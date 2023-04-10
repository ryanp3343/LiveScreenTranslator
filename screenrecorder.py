import sys
import time
import win32gui
import threading
from io import BytesIO
from queue import Queue
from mss import mss
from PIL import Image, ImageChops
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QWidget, QComboBox,QHBoxLayout, QToolButton
from ocr_worker import OCRWorker, upscale_image
from languages_ocr import LANGUAGES_OCR
from languages_google import LANGUAGES_GOOGLE
from text_processor import TextProcessor
from transparent_window import TransparentWindow
from translated_window import TranslatedTextWindow

def has_changed(prev_screenshot, new_screenshot, threshold=5):
    diff = ImageChops.difference(prev_screenshot, new_screenshot)
    extrema = diff.getextrema()
    max_diff = extrema[1] if isinstance(extrema[0], int) else extrema[0][1]
    return diff.getbbox() is not None and max_diff > threshold

def capture_screenshot(monitor, monitor_index, exclude_hwnd=None):
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

        if exclude_hwnd:
            hwnd_left, hwnd_top, hwnd_right, hwnd_bottom = win32gui.GetWindowRect(exclude_hwnd)
            hwnd_width = hwnd_right - hwnd_left
            hwnd_height = hwnd_bottom - hwnd_top

            if hwnd_left < right and hwnd_right > left and hwnd_top < bottom and hwnd_bottom > top:
                hwnd_img = img.crop((hwnd_left - left, hwnd_top - top, hwnd_left - left + hwnd_width, hwnd_top - top + hwnd_height))
                transparent_hwnd_img = hwnd_img.copy()
                transparent_hwnd_img.putalpha(0)
                img.paste(transparent_hwnd_img, (hwnd_left - left, hwnd_top - top))

        return img

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon('img/icon.ico'))
        self.capture_area = None
        self.monitor_index = None
        self.translated_text_window = None
        self.initUI()

        self.screenshot_queue = Queue()
        self.ocr_worker = OCRWorker(self.screenshot_queue, self.language_from_combo)
        self.ocr_worker.ocr_result.connect(self.update_ocr_result)
        self.ocr_worker.start()
        self.text_processor = TextProcessor()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.mousePressed = False
        self.mousePos = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mousePressed = True
            self.mousePos = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.mousePressed:
            self.move(event.globalPos() - self.mousePos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mousePressed = False
            event.accept()

    def initUI(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        title_bar = QWidget()
        title_bar_layout = QHBoxLayout()
        title_bar.setLayout(title_bar_layout)

        icon = QLabel()
        icon.setPixmap(QIcon('img/icon.ico').pixmap(36,36))
        
        centered_label = QLabel("LiveScreen Translator")
        centered_label.setAlignment(Qt.AlignCenter)
        centered_label.setStyleSheet("font-size: 16px; font-family: Tahoma; color: white;")

        min_button = QToolButton()
        min_button.setIcon(QIcon('img/minimize-sign.ico'))
        min_button.clicked.connect(self.showMinimized)
        min_button.setStyleSheet("background-color: rgb(64, 64, 64);")

        close_button = QToolButton()
        close_button.setIcon(QIcon('img/close.ico'))
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("background-color: rgb(64, 64, 64);")

        title_bar_layout.addWidget(icon)
        title_bar_layout.addStretch(1)
        title_bar_layout.addWidget(centered_label)
        title_bar_layout.addStretch(1)
        title_bar_layout.addWidget(min_button)
        title_bar_layout.addWidget(close_button)

        layout.addWidget(title_bar)


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

        buttons_layout = QHBoxLayout()

        self.select_area_button = QPushButton("Select Area")
        self.select_area_button.clicked.connect(self.show_transparent_window)
        buttons_layout.addWidget(self.select_area_button)

        self.capture_button = QPushButton("Start Capturing")
        self.capture_button.clicked.connect(self.toggle_capturing)
        buttons_layout.addWidget(self.capture_button)

        layout.addLayout(buttons_layout)

        self.setWindowTitle("LiveScreen Translator")
        self.setGeometry(100, 100, 600, 400)
        self.show()
        self.setWindowIcon(QIcon('img/icon.ico'))

        self.populate_monitor_combo()
        self.monitor_combo.currentIndexChanged.connect(self.update_monitor_preview)

        self.capturing = False
        self.capture_thread = None
        central_widget.setStyleSheet("background-color: rgb(0,0,0);")
        self.select_area_button.setStyleSheet("background-color: rgb(64, 64, 64); color: white;font-size: 16px; ")
        self.language_from_label.setStyleSheet("font-size: 16px; color: rgb(64, 64, 64); color: white")
        self.language_to_label.setStyleSheet("font-size: 16px; color: rgb(64, 64, 64); color: white")
        self.language_from_combo.setStyleSheet("background-color: rgb(64, 64, 64); font-size: 16px; color: white;")
        self.language_to_combo.setStyleSheet("background-color: rgb(64, 64, 64);font-size: 16px;  color: white;")
        self.preview_label.setStyleSheet("background-color: rgb(64, 64, 64);font-size: 16px; color: white;")
        self.preview_label.setStyleSheet("background-color: rgb(64, 64, 64);font-size: 16px;  color: white;")
        self.monitor_info_label.setStyleSheet("color: white;font-size: 16px; ")
        self.monitor_label.setStyleSheet("color: white;font-size: 16px; ")
        self.monitor_combo.setStyleSheet("background-color: rgb(64, 64, 64);font-size: 16px;  color: white;")
        self.capture_button.setStyleSheet("background-color: rgb(64, 64, 64);font-size: 16px;  color: white;")

    def toggleMaximizeRestore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        

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
            image = image.resize((640, 400), Image.Resampling.LANCZOS)
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

        prev_screenshot = capture_screenshot(monitor, monitor_index).convert("L")
        prev_screenshot = upscale_image(prev_screenshot)
        HWND_BOTTOM = 1
        HWND_TOPMOST = -1
        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_NOACTIVATE = 0x0010

        hwnd = None
        while self.capturing:
            time.sleep(3)

            if self.translated_text_window:
                hwnd = self.translated_text_window.winId()

                if hwnd:
                    # Lower the Z-order of the translated text window
                    win32gui.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
                    time.sleep(0.2)  # Give some time for the window to be placed at the bottom

            new_screenshot = capture_screenshot(monitor, monitor_index, exclude_hwnd=hwnd).convert("L")
            new_screenshot = upscale_image(new_screenshot)

            if hwnd:
                # Restore the Z-order of the translated text window
                win32gui.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
                time.sleep(0.2)  # Give some time for the window to be placed at the top
            if has_changed(prev_screenshot, new_screenshot):
                prev_screenshot = new_screenshot
                new_screenshot.save("sample_screenshot.png")
                language_code = self.language_from_combo.currentData()
                self.screenshot_queue.put((new_screenshot, language_code))
        

    def update_ocr_result(self, text):
        cleaned_text = self.text_processor.process_text(text)
        language_to = self.language_to_combo.currentData()
        translated_text = self.text_processor.translate_text(cleaned_text, target_language=language_to)

        if hasattr(self, 'translated_text_window') and self.translated_text_window is not None:
            self.translated_text_window.close()

        monitor_index = self.monitor_combo.currentData()
        with mss() as sct:
            monitor_geometry = sct.monitors[monitor_index]

        self.translated_text_window = TranslatedTextWindow(self, monitor_geometry, self.capture_area, translated_text)
        self.translated_text_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('img/icon.ico'))
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())