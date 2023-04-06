import sys
import time
import threading
from queue import Queue
from mss import mss
from PIL import Image, ImageChops, ImageOps, ImageFilter
import pytesseract
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QWidget, QComboBox,QHBoxLayout, QDesktopWidget
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QPoint, QRect
from textprocessor import TextProcessor
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from io import BytesIO
from languages_ocr import LANGUAGES_OCR
from languages_google import LANGUAGES_GOOGLE
import cv2
import numpy as np
from skimage.transform import rotate
from skimage import io

def adaptive_thresholding(image):
    gray_image = image.convert("L")
    return gray_image.point(lambda x: 0 if x < 128 else 255, '1')

def increase_contrast(image, alpha=1.5, beta=20):
    new_image = np.zeros(image.shape, image.dtype)
    new_image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    return new_image

def apply_gaussian_blur(image, kernel_size=(5, 5)):
    blurred_image = cv2.GaussianBlur(image, kernel_size, 0)
    return blurred_image

def deskew_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    deskewed_image = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return deskewed_image

def ocr_screenshot(image, language_code):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    config = f'-l {language_code} --psm 3 --oem 1'
    return pytesseract.image_to_string(image, config=config)

def has_changed(prev_screenshot, new_screenshot, threshold=5):
    diff = ImageChops.difference(prev_screenshot, new_screenshot)
    extrema = diff.getextrema()
    max_diff = extrema[1] if isinstance(extrema[0], int) else extrema[0][1]
    return diff.getbbox() is not None and max_diff > threshold

def upscale_image(image, scale_factor=2.0):
    width, height = image.size
    new_width, new_height = int(width * scale_factor), int(height * scale_factor)
    return image.resize((new_width, new_height), Image.ANTIALIAS)

def binarize_image(image, block_size=15, offset=5):
    return image.filter(ImageFilter.UnsharpMask).convert('1', dither=Image.NONE)

def capture_screenshot(monitor, monitor_index):
    with mss() as sct:
        monitor_geometry = sct.monitors[monitor_index]
        left = monitor["left"] + monitor_geometry["left"]
        top = monitor["top"] + monitor_geometry["top"]
        width = monitor["width"]
        height = monitor["height"]

        left = max(left, monitor_geometry["left"])
        top = max(top, monitor_geometry["top"])
        right = min(left + width, monitor_geometry["left"] + monitor_geometry["width"])
        bottom = min(top + height, monitor_geometry["top"] + monitor_geometry["height"])

        bbox = (left, top, right, bottom)
        screenshot = sct.grab(bbox)
        img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)
        return img




def downscale_image(image, scale_factor=0.5):
    width, height = image.size
    new_width, new_height = int(width * scale_factor), int(height * scale_factor)
    return image.resize((new_width, new_height), Image.ANTIALIAS)

class OCRWorker(QThread):
    ocr_result = pyqtSignal(str)

    def __init__(self, screenshot_queue,language_combo):
        super(OCRWorker, self).__init__()
        self.screenshot_queue = screenshot_queue
        self.language_combo = language_combo

    def run(self):
        while True:
            screenshot, language_code = self.screenshot_queue.get()
            screenshot = upscale_image(screenshot)
            screenshot = adaptive_thresholding(screenshot)
            text = ocr_screenshot(screenshot, language_code)
            self.ocr_result.emit(text)

class TransparentWindow(QWidget):
    def __init__(self, main_window, monitor_index):
        super().__init__()
        self.main_window = main_window
        self.monitor_index = monitor_index
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        desktop = QDesktopWidget()
        monitor_geometry = desktop.screenGeometry(monitor_index)
        self.setGeometry(monitor_geometry)

        with mss() as sct:
            monitor = sct.monitors[self.monitor_index]
            x, y, width, height = monitor["left"], monitor["top"], monitor["width"] - 1, monitor["height"] - 1
            self.setGeometry(x, y, width, height)

        self.start_point = None
        self.end_point = None
        self.selection_rect = None
        self.pen = QPen(Qt.red)
        self.pen.setWidth(2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 100))
        painter.drawRect(self.rect())

        if self.start_point and self.end_point:
            rect = QRect(self.start_point, self.end_point)
            rect = rect.normalized()

            painter.setPen(self.pen)
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        self.start_point = event.pos()
        self.end_point = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        self.end_point = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.end_point = event.pos()
        self.main_window.update_capture_area(self.start_point, self.end_point, self.geometry())
        self.close()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.capture_area = None
        self.monitor_index = None
        self.initUI()

        self.screenshot_queue = Queue()
        self.ocr_worker = OCRWorker(self.screenshot_queue, self.language_from_combo)
        self.ocr_worker.ocr_result.connect(self.update_ocr_result)
        self.ocr_worker.start()
        self.text_processor = TextProcessor()

    def initUI(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.select_area_button = QPushButton("Select Area")
        self.select_area_button.clicked.connect(self.show_transparent_window)
        layout.addWidget(self.select_area_button)


        top_layout = QHBoxLayout()

        self.language_from_label = QLabel("Translate From:")
        self.language_from_combo = QComboBox()
        top_layout.addWidget(self.language_from_label)
        top_layout.addWidget(self.language_from_combo)

        self.language_to_label = QLabel("Translate To:")
        self.language_to_combo = QComboBox()
        top_layout.addWidget(self.language_to_label)
        top_layout.addWidget(self.language_to_combo)

        layout.addLayout(top_layout)

        self.populate_language_from_combo()
        self.populate_language_to_combo()

        self.label = QLabel("OCR Result:")
        layout.addWidget(self.label)

        monitor_selection_layout = QHBoxLayout()
        self.monitor_label = QLabel("Select monitor:")
        self.monitor_combo = QComboBox()
        monitor_selection_layout.addWidget(self.monitor_label)
        monitor_selection_layout.addWidget(self.monitor_combo)
        layout.addLayout(monitor_selection_layout)

        self.monitor_info_label = QLabel("Monitor info:")
        layout.addWidget(self.monitor_info_label)

        self.preview_label = QLabel("Monitor Preview:")
        layout.addWidget(self.preview_label)

        self.capture_button = QPushButton("Start Capturing")
        self.capture_button.clicked.connect(self.toggle_capturing)
        layout.addWidget(self.capture_button)

        self.setWindowTitle("LiveScreen Translator")
        self.setGeometry(100, 100, 600, 400)
        self.show()

        self.populate_monitor_combo()
        self.monitor_combo.currentIndexChanged.connect(self.update_monitor_preview)

        self.capturing = False
        self.capture_thread = None

    def update_capture_area(self, start, end, geometry):
        monitor_geometry = self.monitor_combo.currentData()
        with mss() as sct:
            monitor = sct.monitors[monitor_geometry]
            left_offset, top_offset = monitor['left'], monitor['top']

        self.capture_area = (start.x() - left_offset, start.y() - top_offset, end.x() - start.x(), end.y() - start.y())
        self.capture_geometry = geometry


    def show_transparent_window(self):
        monitor_index = self.monitor_combo.currentData()
        self.transparent_window = TransparentWindow(self, monitor_index)
        self.transparent_window.show()

    def populate_monitor_combo(self):
        with mss() as sct:
            for i, monitor in enumerate(sct.monitors[1:], 1):
                self.monitor_combo.addItem(f"Monitor {i}", i)
        self.monitor_combo.setCurrentIndex(0)
        self.update_monitor_preview(0)

    def populate_language_from_combo(self):
        for language, code in LANGUAGES_OCR:
            self.language_from_combo.addItem(language, code)

    def populate_language_to_combo(self):
        for language, code in LANGUAGES_GOOGLE:
            self.language_to_combo.addItem(language, code)

    def update_monitor_preview(self, index):
        monitor_index = self.monitor_combo.currentData()
        with mss() as sct:
            monitor = sct.monitors[monitor_index]
            monitor_info = f"Monitor {monitor_index}: {monitor['width']}x{monitor['height']}"
            self.monitor_info_label.setText(monitor_info)

            screenshot = sct.grab(monitor)
            image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            image = image.resize((640, 400), Image.ANTIALIAS)
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            self.preview_label.setPixmap(pixmap)

    def toggle_capturing(self):
        if self.capturing:
            self.capture_button.setText("Start Capturing")
            self.capturing = False
            self.preview_label.show()
            self.monitor_label.show()
            self.monitor_combo.show()
            self.monitor_info_label.show()
            self.language_from_label.show()
            self.language_from_combo.show()
            self.language_to_label.show()
            self.language_to_combo.show()
            self.label.setText("OCR Result:")
            self.monitor_label.setText("Select monitor:")
        else:
            self.capture_button.setText("Stop Capturing")
            self.capturing = True
            self.capture_thread = threading.Thread(target=self.capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            self.preview_label.hide()
            self.monitor_label.clear()
            self.monitor_combo.hide()
            self.monitor_info_label.hide()
            self.language_from_label.hide()
            self.language_from_combo.hide()
            self.language_to_label.hide()
            self.language_to_combo.hide()


    def capture_loop(self):
        if not self.capture_area:
            print("Please select an area first.")
            return

        left, top, width, height = self.capture_area
        monitor_index = self.monitor_combo.currentData()
        with mss() as sct:
            monitor_geometry = sct.monitors[monitor_index]
            left_offset, top_offset = monitor_geometry['left'], monitor_geometry['top']
        monitor = {'left': left + left_offset, 'top': top + top_offset, 'width': width, 'height': height}

        prev_screenshot = capture_screenshot(monitor,monitor_index).convert("L") 
        prev_screenshot = upscale_image(prev_screenshot)

        while self.capturing:
            time.sleep(3)
            new_screenshot = capture_screenshot(monitor,monitor_index).convert("L") 
            new_screenshot = upscale_image(new_screenshot)  

            if has_changed(prev_screenshot, new_screenshot):
                prev_screenshot = new_screenshot
                new_screenshot.save("sample_screenshot.png")
                language_code = self.language_from_combo.currentData()
                self.screenshot_queue.put((new_screenshot, language_code))


    def update_ocr_result(self, text):
        cleaned_text = self.text_processor.process_text(text)
        language_to = self.language_to_combo.currentData()
        translated_text = self.text_processor.translate_text(cleaned_text, target_language=language_to)
        self.label.setText("OCR Result:\n\n" + translated_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())