import time
import threading
from io import BytesIO
from queue import Queue
from mss import mss
from PIL import Image, ImageChops
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QWidget,
    QComboBox,
    QHBoxLayout,
    QToolButton,
    QCheckBox,
    QFileDialog,
)
from constants.languages_ocr import LANGUAGES_OCR
from constants.languages_google import LANGUAGES_GOOGLE
from components.ocr_worker import OCRWorker
from components.text_processor import TextProcessor
from components.transparent_window import TransparentWindow
from components.translated_window import TranslatedTextWindow
from components.text_to_speech import TextToSpeech


def has_changed(prev_screenshot, new_screenshot, threshold=5):
    """takes two screennshots and compares if there different"""
    diff = ImageChops.difference(prev_screenshot, new_screenshot)
    extrema = diff.getextrema()
    max_diff = extrema[1] if isinstance(extrema[0], int) else extrema[0][1]
    return diff.getbbox() is not None and max_diff > threshold


def capture_screenshot(monitor, monitor_index, exclude_hwnd=None):
    """gets geometry of montior area and takes a screenshot of the bbox"""
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

        img = Image.frombytes(
            "RGB", (screenshot.width, screenshot.height), screenshot.rgb
        )

        return img


class MainWindow(QMainWindow):
    """
    MainWindow class all other components get used here
    Creates a small desktop application window that lets
    user choose translation languages,select caputre area,
    save to file, use tts
    """

    def __init__(self):
        """inits the main window and all values, creates referecense to other classes"""
        super().__init__()

        self.setWindowIcon(QIcon("resources/img/icon.ico"))
        self.capture_area = None
        self.correct_capture_area = None
        self.monitor_index = None
        self.translated_text_window = None
        self.save_translated_text = False
        self.save_destination = ""
        self.previous_translated_text = None
        self.update_translation_window = True
        self.initUI()

        self.screenshot_queue = Queue()
        self.ocr_worker = OCRWorker(self.screenshot_queue, self.language_from_combo)
        self.ocr_worker.ocr_result.connect(self.update_ocr_result)
        self.ocr_worker.start()
        self.text_processor = TextProcessor()
        self.text_to_speech = TextToSpeech(self)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.mousePressed = False
        self.mousePos = QPoint()
        with open("resources/styles/styles.qss", "r") as f:
            stylesheet = f.read()
        self.setStyleSheet(stylesheet)

    def mousePressEvent(self, event):
        """for the custon title bar dragging across screen"""
        if event.button() == Qt.LeftButton:
            self.mousePressed = True
            self.mousePos = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        """for the custon title bar dragging across screen"""
        if event.buttons() == Qt.LeftButton and self.mousePressed:
            self.move(event.globalPos() - self.mousePos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """for the custon title bar dragging across screen"""
        if event.button() == Qt.LeftButton:
            self.mousePressed = False
            event.accept()

    def initUI(self):
        """creates all the user interface for the main window"""
        central_widget = QWidget()
        central_widget.setObjectName("central_widget")
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        title_bar = QWidget()
        title_bar_layout = QHBoxLayout()
        title_bar.setLayout(title_bar_layout)

        icon = QLabel()
        icon.setPixmap(QIcon("resources/img/icon.ico").pixmap(36, 36))

        centered_label = QLabel("LiveScreen Translator")
        centered_label.setObjectName("center_label")
        centered_label.setAlignment(Qt.AlignCenter)

        min_button = QToolButton()
        min_button.setObjectName("min_button")
        min_button.setIcon(QIcon("resources/img/minimize-sign.ico"))
        min_button.clicked.connect(self.showMinimized)

        close_button = QToolButton()
        close_button.setObjectName("close_button")
        close_button.setIcon(QIcon("resources/img/close.ico"))
        close_button.clicked.connect(self.close)

        title_bar_layout.addWidget(icon)
        title_bar_layout.addStretch(1)
        title_bar_layout.addWidget(centered_label)
        title_bar_layout.addStretch(1)
        title_bar_layout.addWidget(min_button)
        title_bar_layout.addWidget(close_button)

        layout.addWidget(title_bar)
        layout.addStretch(100)

        top_layout = QHBoxLayout()

        self.language_from_label = QLabel("Translate From:")
        self.language_from_label.setObjectName("language_from_label")
        self.language_from_combo = QComboBox()
        self.language_from_combo.setObjectName("language_from_combo")
        top_layout.addWidget(self.language_from_label)
        top_layout.addWidget(self.language_from_combo)

        self.language_to_label = QLabel("Translate To:")
        self.language_to_label.setObjectName("language_to_label")
        self.language_to_combo = QComboBox()
        self.language_to_combo.setObjectName("language_to_combo")
        top_layout.addWidget(self.language_to_label)
        top_layout.addWidget(self.language_to_combo)

        layout.addLayout(top_layout)

        self.populate_language_from_combo()
        self.populate_language_to_combo()

        monitor_selection_layout = QHBoxLayout()
        self.monitor_label = QLabel("Select monitor:")
        self.monitor_label.setObjectName("monitor_label")
        self.monitor_combo = QComboBox()
        self.monitor_combo.setObjectName("monitor_combo")
        monitor_selection_layout.addWidget(self.monitor_label)
        monitor_selection_layout.addWidget(self.monitor_combo)
        layout.addLayout(monitor_selection_layout)

        monitor_info_layout = QHBoxLayout()
        self.monitor_info_label = QLabel("Monitor info:")
        self.monitor_info_label.setObjectName("monitor_info_label")
        monitor_info_layout.addWidget(self.monitor_info_label)

        voice_layout = QHBoxLayout()
        self.voice_label = QLabel("TTS")
        self.voice_label.setObjectName("voice_label")
        voice_layout.addWidget(self.voice_label)

        self.voice_checkbox = QCheckBox("Voice Output")
        self.voice_checkbox.stateChanged.connect(self.toggle_voice_output)
        voice_layout.addWidget(self.voice_checkbox)

        monitor_info_layout.addLayout(voice_layout)

        save_text_layout = QHBoxLayout()
        self.save_text_label = QLabel("Save text to file:")
        self.save_text_label.setObjectName("save_to_file")
        save_text_layout.addWidget(self.save_text_label)

        self.save_checkbox = QCheckBox("Select Destination")
        self.save_checkbox.stateChanged.connect(self.select_save_destination)
        save_text_layout.addWidget(self.save_checkbox)

        monitor_info_layout.addLayout(save_text_layout)

        monitor_info_layout.setStretch(0, 2)
        monitor_info_layout.setStretch(2, 1)

        layout.addLayout(monitor_info_layout)

        self.preview_label = QLabel("Monitor Preview:")
        self.preview_label.setObjectName("preview_label")
        layout.addWidget(self.preview_label)

        buttons_layout = QHBoxLayout()

        self.select_area_button = QPushButton("Select Area")
        self.select_area_button.setObjectName("select_area_button")
        self.select_area_button.clicked.connect(self.show_transparent_window)
        buttons_layout.addWidget(self.select_area_button)

        self.capture_button = QPushButton("Start Capturing")
        self.capture_button.setObjectName("capture_button")
        self.capture_button.setDisabled(True)
        self.capture_button.clicked.connect(self.toggle_capturing)
        buttons_layout.addWidget(self.capture_button)

        layout.addLayout(buttons_layout)
        layout.addStretch(1)

        self.setWindowTitle("LiveScreen Translator")
        self.setGeometry(100, 100, 600, 400)
        self.show()
        self.setWindowIcon(QIcon("resources/img/icon.ico"))

        self.populate_monitor_combo()
        self.monitor_combo.currentIndexChanged.connect(self.update_monitor_preview)

        self.capturing = False
        self.capture_thread = None

    def toggleMaximizeRestore(self):
        """minimize main window"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def toggle_save_translated_text(self, state):
        """boolean if user selects save text to file"""
        if state == Qt.Checked:
            self.save_translated_text = True
        else:
            self.save_translated_text = False

    def select_save_destination(self, state):
        """let user pick where they want the saved file to go"""
        if state == Qt.Checked:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Save Translated Text",
                "",
                "Text Files (*.txt);;All Files (*)",
                options=options,
            )
            if file_name:
                if not file_name.endswith(".txt"):
                    file_name += ".txt"
                self.save_path = file_name
        else:
            self.save_path = None

    def save_translated_text_to_file(self):
        """open file and save the translated text"""
        if self.save_path and self.translated_text_window:
            with open(self.save_path, "a", encoding="utf-8") as f:
                f.write(self.translated_text_window.translated_text + "\n")

    def enable_capture_button(self):
        """disable the button from being pressed"""
        self.capture_button.setDisabled(False)

    def toggle_voice_output(self, state):
        """boolean if user selects the tts checkbox"""
        if state == Qt.Checked:
            self.voice_output_enabled = True
        else:
            self.voice_output_enabled = False
            self.text_to_speech.media_player.stop()

    def update_capture_area(self, start, end, geometry):
        """updates the capture area from user dragging mouse"""
        monitor_geometry = self.monitor_combo.currentData()
        with mss() as sct:
            monitor = sct.monitors[monitor_geometry]
            left_offset, top_offset = monitor["left"], monitor["top"]
        self.correct_capture_area = (
            start.x() + left_offset,
            start.y() + top_offset,
            end.x() - start.x(),
            end.y() - start.y(),
        )
        self.capture_area = (
            start.x() - left_offset,
            start.y() - top_offset,
            end.x() - start.x(),
            end.y() - start.y(),
        )
        self.capture_geometry = (
            left_offset,
            top_offset,
            monitor["width"],
            monitor["height"],
        )
        self.enable_capture_button()

    def show_transparent_window(self):
        """shows the transparent window when user is selecting area"""
        monitor_index = self.monitor_combo.currentData()
        self.transparent_window = TransparentWindow(self, monitor_index)
        self.transparent_window.show()

    def populate_monitor_combo(self):
        """populate the monitors box with the users monitor if not multiple"""
        with mss() as sct:
            for i, monitor in enumerate(sct.monitors[1:], 1):
                self.monitor_combo.addItem(f"Monitor {i}", i)
        self.monitor_combo.setCurrentIndex(0)
        self.update_monitor_preview(0)

    def populate_language_from_combo(self):
        """populate the language from combo with list of languages available"""
        for language, code in LANGUAGES_OCR:
            self.language_from_combo.addItem(language, code)

    def populate_language_to_combo(self):
        """populate the language to combo with list of languages available"""
        for language, code in LANGUAGES_GOOGLE:
            self.language_to_combo.addItem(language, code)

    def update_monitor_preview(self, index):
        """creats a preview of the users monitors"""
        monitor_index = self.monitor_combo.currentData()
        with mss() as sct:
            monitor = sct.monitors[monitor_index]
            monitor_info = (
                f"Monitor {monitor_index}: {monitor['width']}x{monitor['height']}"
            )
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
        """toggle what shows up ui is shown when capturing and not capturing"""
        if self.capturing:
            self.capture_button.setText("Start Capturing")
            self.capturing = False
            self.capture_button.setDisabled(True)
            self.preview_label.show()
            self.monitor_label.show()
            self.monitor_combo.show()
            self.monitor_info_label.show()
            self.language_from_label.show()
            self.language_from_combo.show()
            self.language_to_label.show()
            self.language_to_combo.show()
            self.save_text_label.show()
            self.save_checkbox.show()
            self.select_area_button.show()
            self.voice_checkbox.show()
            self.voice_label.show()
            self.monitor_label.setText("Select monitor:")
            self.update_translation_window = False
            if self.translated_text_window:
                self.translated_text_window.close()
                self.translated_text_window = None

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
            self.save_text_label.hide()
            self.save_checkbox.hide()
            self.voice_checkbox.hide()
            self.voice_label.hide()
            self.select_area_button.hide()
            self.update_translation_window = True
            self.text_to_speech.stop_voice()

    def capture_loop(self):
        """
        main loop of capturing gets geometry takes caputures screenshot
        hides the translated text window to prevent it from being captured in the screenshot
        """
        if not self.capture_area:
            print("Please select an area first.")
            return

        left, top, width, height = self.capture_area
        monitor_index = self.monitor_combo.currentData()
        with mss() as sct:
            monitor_geometry = sct.monitors[monitor_index]
            left_offset, top_offset = monitor_geometry["left"], monitor_geometry["top"]
        monitor = {
            "left": left + left_offset,
            "top": top + top_offset,
            "width": width,
            "height": height,
        }

        prev_screenshot = capture_screenshot(monitor, monitor_index).convert("L")

        while self.capturing:
            time.sleep(3)
            if self.translated_text_window:
                self.translated_text_window.setWindowOpacity(0)  # Hide the translated text window
                time.sleep(0.3)
            new_screenshot = capture_screenshot(monitor, monitor_index).convert("L")
            if self.translated_text_window:
                self.translated_text_window.setWindowOpacity(1)  # Show the translated text window again
                time.sleep(0.3)
            if has_changed(prev_screenshot, new_screenshot):
                prev_screenshot = new_screenshot
                new_screenshot.save("sample_screenshot.png")
                language_code = self.language_from_combo.currentData()
                self.screenshot_queue.put((new_screenshot, language_code))



    def update_ocr_result(self, text):
        """
        sends text to text processor, cleans, translates, preforms cosine similarity
        saves the text to file if true and displays the translated text window
        """
        cleaned_text = self.text_processor.process_text(text)
        language_to = self.language_to_combo.currentData()
        monitor_index = self.monitor_combo.currentData()
        translated_text = self.text_processor.translate_text(
            cleaned_text, target_language=language_to
        )

        if self.previous_translated_text is not None:
            similarity = self.text_processor.calculate_similarity(
                self.previous_translated_text, translated_text, language_to
            )
            if similarity > 0.8:
                return

        self.previous_translated_text = translated_text

        if self.save_checkbox.isChecked() and self.save_path:
            if translated_text.strip():
                with open(self.save_path, "a", encoding="utf-8") as output_file:
                    output_file.write(translated_text + "\n")

        if self.update_translation_window:
            if (
                hasattr(self, "translated_text_window")
                and self.translated_text_window is not None
            ):
                self.translated_text_window.close()

            if self.voice_checkbox.isChecked() and translated_text.strip():
                self.text_to_speech.play_text_voice(translated_text, language_to)

            self.translated_text_window = TranslatedTextWindow(
                self, monitor_index, self.correct_capture_area, translated_text
            )
            self.translated_text_window.show()
