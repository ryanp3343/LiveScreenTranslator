import sys
import time
import threading
from queue import Queue
from mss import mss
from PIL import Image, ImageChops, ImageOps, ImageFilter
import pytesseract
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QWidget, QComboBox,QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from textprocessor import TextProcessor
from PyQt5.QtGui import QPixmap
from io import BytesIO
from languages import LANGUAGES


def ocr_screenshot(image, language_code):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    config = f'-l {language_code} --psm 6'
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

def capture_screenshot(monitor_index):
    with mss() as sct:
        monitor = sct.monitors[monitor_index]
        screenshot = sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.rgb)

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
            screenshot = binarize_image(screenshot)
            text = ocr_screenshot(screenshot, language_code)
            self.ocr_result.emit(text)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create a queue to store screenshots and worker to process them
        self.screenshot_queue = Queue()
        self.initUI()
        self.ocr_worker = OCRWorker(self.screenshot_queue, self.language_from_combo)
        self.ocr_worker.ocr_result.connect(self.update_ocr_result)
        self.ocr_worker.start()
        self.text_processor = TextProcessor()

        self.initUI()
        self.initial_size = self.size()  # Store the initial window size


    def initUI(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        top_layout = QHBoxLayout()

        # Add language-related widgets to the layout
        self.language_from_label = QLabel("Translate From:")
        self.language_from_combo = QComboBox()
        top_layout.addWidget(self.language_from_label)
        top_layout.addWidget(self.language_from_combo)

        # Add new widgets to the layout
        self.language_to_label = QLabel("Translate To:")
        self.language_to_combo = QComboBox()
        top_layout.addWidget(self.language_to_label)
        top_layout.addWidget(self.language_to_combo)

        # Add the QHBoxLayout to the main layout
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

    def populate_monitor_combo(self):
        with mss() as sct:
            for i, monitor in enumerate(sct.monitors[1:], 1):
                self.monitor_combo.addItem(f"Monitor {i}", i)
        self.monitor_combo.setCurrentIndex(0)
        self.update_monitor_preview(0)

    def populate_language_from_combo(self):
        for language, code in LANGUAGES:
            self.language_from_combo.addItem(language, code)

    def populate_language_to_combo(self):
        for language, code in LANGUAGES:
            self.language_to_combo.addItem(language, code)

    def update_monitor_preview(self, index):
        monitor_index = self.monitor_combo.currentData()
        with mss() as sct:
            monitor = sct.monitors[monitor_index]
            monitor_info = f"Monitor {monitor_index}: {monitor['width']}x{monitor['height']}"
            self.monitor_info_label.setText(monitor_info)

            # Capture and show a preview of the selected monitor
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
            self.resize(self.initial_size)  # Set the window size back to the initial size
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
        monitor_index = self.monitor_combo.currentData()
        prev_screenshot = capture_screenshot(monitor_index).convert("L")  # Convert to grayscale
        prev_screenshot = upscale_image(prev_screenshot)   # Downscale image

        while self.capturing:
            time.sleep(5)
            new_screenshot = capture_screenshot(monitor_index).convert("L")  # Convert to grayscale
            new_screenshot = upscale_image(new_screenshot)    # Downscale image

            if has_changed(prev_screenshot, new_screenshot):
                prev_screenshot = new_screenshot
                new_screenshot.save("sample_screenshot.png")
                language_code = self.language_from_combo.currentData()
                self.screenshot_queue.put((new_screenshot, language_code))



    def update_ocr_result(self, text):
        cleaned_text = self.text_processor.process_text(text)
        self.label.setText("OCR Result:\n\n" + cleaned_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())