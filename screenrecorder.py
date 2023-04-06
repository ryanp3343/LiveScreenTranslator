import sys
import time
import threading
from io import BytesIO
from queue import Queue
from mss import mss
from PIL import Image, ImageChops
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QWidget, QComboBox,QHBoxLayout
from ocr_worker import OCRWorker, upscale_image
from languages_ocr import LANGUAGES_OCR
from languages_google import LANGUAGES_GOOGLE
from textprocessor import TextProcessor
from transparent_window import TransparentWindow

def has_changed(prev_screenshot, new_screenshot, threshold=5):
    diff = ImageChops.difference(prev_screenshot, new_screenshot)
    extrema = diff.getextrema()
    max_diff = extrema[1] if isinstance(extrema[0], int) else extrema[0][1]
    return diff.getbbox() is not None and max_diff > threshold

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon('icon.ico'))
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
        self.setWindowIcon(QIcon('icon.ico'))

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
    app.setWindowIcon(QIcon('icon.ico'))
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())