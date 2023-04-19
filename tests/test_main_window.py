import sys
import pytest
from PyQt5.QtWidgets import QApplication,QComboBox, QCheckBox, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QToolButton
from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QMouseEvent
from components.main_window import MainWindow,has_changed,capture_screenshot
from components.text_processor import TextProcessor
from components.translated_window import TranslatedTextWindow
from PIL import Image
from constants.languages_google import LANGUAGES_GOOGLE
from constants.languages_ocr import LANGUAGES_OCR
import unittest
from unittest.mock import MagicMock, patch, call
import threading
import time 
from queue import Queue
from contextlib import contextmanager

@pytest.fixture
def red_image():
    return Image.new('RGB', (100, 100), color='red')

@pytest.fixture
def green_image():
    return Image.new('RGB', (100, 100), color='green')

def test_has_changed_identical_images(red_image):
    assert not has_changed(red_image, red_image)

def test_has_changed_different_images(red_image, green_image):
    assert has_changed(red_image, green_image)

def test_capture_screenshot(monkeypatch):
    test_image = Image.new('RGB', (200, 200), color='blue')

    class MockScreenshot:
        def __init__(self, image):
            self.width = image.width
            self.height = image.height
            self.rgb = image.tobytes()

    class MockSCT:
        monitors = [
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
        ]

        def grab(self, bbox):
            return MockScreenshot(test_image)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("components.main_window.mss", MockSCT)
    monkeypatch.setattr("components.main_window.Image.frombytes", lambda *args, **kwargs: test_image)

    monitor = {"left": 100, "top": 100, "width": 200, "height": 200}
    monitor_index = 0

    screenshot = capture_screenshot(monitor, monitor_index)

    assert screenshot.size == (200, 200)

@contextmanager
def main_window_scope(qapp):
    main_window = MainWindow()
    yield main_window
    main_window.close()

@pytest.fixture(scope="module")
def main_window(qapp):
    with main_window_scope(qapp) as main_window:
        yield main_window


def test_main_window_init(main_window):
    assert main_window.capture_area is None
    assert main_window.correct_capture_area is None
    assert main_window.monitor_index is None
    assert main_window.translated_text_window is None
    assert main_window.save_translated_text is False
    assert main_window.save_destination == ""
    assert main_window.previous_translated_text is None
    assert main_window.update_translation_window is True

def test_mouse_events(main_window):
    QTest.mousePress(main_window, Qt.LeftButton, Qt.NoModifier, QPoint(10, 10))
    assert main_window.mousePressed is True

    initial_position = main_window.pos()
    move_event = QMouseEvent(QEvent.MouseMove, QPoint(10, 10), QPoint(30, 30), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    main_window.mouseMoveEvent(move_event)
    assert main_window.pos() != initial_position

    QTest.mouseRelease(main_window, Qt.LeftButton, Qt.NoModifier, QPoint(20, 20))
    assert main_window.mousePressed is False

def test_comboboxes(main_window):
    assert isinstance(main_window.language_from_combo, QComboBox)
    assert isinstance(main_window.language_to_combo, QComboBox)

    assert main_window.language_from_combo.count() > 0
    assert main_window.language_to_combo.count() > 0

def test_checkboxes(main_window):
    assert isinstance(main_window.voice_checkbox, QCheckBox)
    assert isinstance(main_window.save_checkbox, QCheckBox)

def test_pushbuttons(main_window):
    assert isinstance(main_window.select_area_button, QPushButton)
    assert isinstance(main_window.capture_button, QPushButton)

    assert main_window.capture_button.isEnabled() is False

def test_labels(main_window):
    assert isinstance(main_window.language_from_label, QLabel)
    assert isinstance(main_window.language_to_label, QLabel)
    assert isinstance(main_window.monitor_label, QLabel)
    assert isinstance(main_window.monitor_info_label, QLabel)
    assert isinstance(main_window.voice_label, QLabel)
    assert isinstance(main_window.save_text_label, QLabel)
    assert isinstance(main_window.preview_label, QLabel)

def test_layouts(main_window):
    central_widget = main_window.centralWidget()
    layout = central_widget.layout()

    assert isinstance(layout, QVBoxLayout)

    for index in range(layout.count()):
        item = layout.itemAt(index)
        if isinstance(item, QHBoxLayout) or isinstance(item, QVBoxLayout):
            assert item is not None

def test_signal_slot_connections(main_window):

    min_button = main_window.findChild(QToolButton, "min_button")
    close_button = main_window.findChild(QToolButton, "close_button")
    voice_checkbox = main_window.findChild(QCheckBox, "voice_checkbox")
    save_checkbox = main_window.findChild(QCheckBox, "save_checkbox")
    select_area_button = main_window.findChild(QPushButton, "select_area_button")
    capture_button = main_window.findChild(QPushButton, "capture_button")

    assert min_button is not None
    assert close_button is not None
    assert voice_checkbox is not None
    assert save_checkbox is not None
    assert select_area_button is not None
    assert capture_button is not None

    assert min_button.clicked is not None
    assert close_button.clicked is not None
    assert voice_checkbox.stateChanged is not None
    assert save_checkbox.stateChanged is not None
    assert select_area_button.clicked is not None
    assert capture_button.clicked is not None

def test_toggleMaximizeRestore(main_window):
    main_window.showMaximized()
    main_window.toggleMaximizeRestore()
    assert main_window.isMaximized() is False
    main_window.toggleMaximizeRestore()
    assert main_window.isMaximized() is True

def test_toggle_save_translated_text(main_window):
    main_window.toggle_save_translated_text(Qt.Checked)
    assert main_window.save_translated_text is True
    main_window.toggle_save_translated_text(Qt.Unchecked)
    assert main_window.save_translated_text is False

def test_select_save_destination(main_window):
    with unittest.mock.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName", return_value=("test.txt", None)):
        main_window.select_save_destination(Qt.Checked)
        assert main_window.save_path == "test.txt"
    main_window.select_save_destination(Qt.Unchecked)
    assert main_window.save_path is None

def test_enable_capture_button(main_window):
    main_window.capture_button.setDisabled(True)
    main_window.enable_capture_button()
    assert main_window.capture_button.isEnabled()

def test_toggle_voice_output(main_window):
    main_window.toggle_voice_output(Qt.Checked)
    assert main_window.voice_output_enabled is True

    with unittest.mock.patch.object(main_window.text_to_speech, "stop_voice") as mocked_stop:
        main_window.toggle_voice_output(Qt.Unchecked)
        assert main_window.voice_output_enabled is False
        mocked_stop.assert_called_once()



def test_populate_language_from_combo(main_window):
    main_window.populate_language_from_combo()
    print([main_window.language_from_combo.itemText(i) for i in range(main_window.language_from_combo.count())])
    assert main_window.language_from_combo.count() == len(LANGUAGES_OCR)


def test_populate_language_to_combo(main_window):
    main_window.populate_language_to_combo()
    print([main_window.language_to_combo.itemText(i) for i in range(main_window.language_to_combo.count())])
    assert main_window.language_to_combo.count() == len(LANGUAGES_GOOGLE)

def test_update_capture_area(main_window):
    start = MagicMock(x=MagicMock(return_value=10), y=MagicMock(return_value=20))
    end = MagicMock(x=MagicMock(return_value=110), y=MagicMock(return_value=120))
    geometry = MagicMock()

    main_window.update_capture_area(start, end, geometry)

    assert main_window.correct_capture_area == (10, 20, 100, 100)
    assert main_window.capture_area == (10, 20, 100, 100)
    with patch.object(main_window, "enable_capture_button") as mock_enable_capture_button:
        main_window.update_capture_area(start, end, geometry)
        mock_enable_capture_button.assert_called_once()

def test_show_transparent_window(main_window):
    main_window.transparent_window = None
    monitor_index = 1

    with patch("components.main_window.TransparentWindow") as MockTransparentWindow:
        main_window.show_transparent_window()

        MockTransparentWindow.assert_called_with(main_window, monitor_index)
        main_window.transparent_window.show.assert_called_once()

def test_populate_monitor_combo(main_window):
    monitors = [
        {"left": 0, "top": 0, "width": 1920, "height": 1080, "size": (1920, 1080)},
        {"left": 1920, "top": 0, "width": 1920, "height": 1080, "size": (1920, 1080)},
    ]

    with patch("components.main_window.mss") as MockMSS, \
            patch.object(main_window.monitor_combo, "addItem") as mock_add_item, \
            patch.object(main_window.monitor_combo, "setCurrentIndex") as mock_set_current_index, \
            patch.object(main_window, "update_monitor_preview") as mock_update_monitor_preview:
        MockMSS.return_value.__enter__.return_value.monitors = monitors

        screenshot = MagicMock(size=(1920, 1080), rgb=b"\x00" * 1920 * 1080 * 3)
        MockMSS.return_value.__enter__.return_value.grab.return_value = screenshot

        main_window.populate_monitor_combo()

        mock_add_item.assert_any_call("Monitor 1", 1)
        mock_set_current_index.assert_called_once_with(0)
        mock_update_monitor_preview.assert_called_once_with(0)

def test_update_monitor_preview(main_window):
    monitor_index = 1
    main_window.monitor_combo.currentData = MagicMock(return_value=monitor_index)

    with patch("components.main_window.mss") as MockMSS, \
            patch.object(main_window.monitor_info_label, "setText") as mock_set_text, \
            patch.object(main_window.preview_label, "setPixmap") as mock_set_pixmap:
        
        monitor = {"width": 1920, "height": 1080}
        MockMSS.return_value.__enter__.return_value.monitors = {monitor_index: monitor}
        screenshot = MagicMock(size=(1920, 1080), rgb=b"\x00" * 1920 * 1080 * 3)
        MockMSS.return_value.__enter__.return_value.grab.return_value = screenshot

        main_window.update_monitor_preview(monitor_index)

        mock_set_text.assert_called_once_with(f"Monitor {monitor_index}: {monitor['width']}x{monitor['height']}")

        mock_set_pixmap.assert_called_once()


def test_toggle_capturing_when_capturing_is_true(main_window):
    main_window.capturing = True
    main_window.translated_text_window = MagicMock()

    with patch.object(main_window.capture_button, "setText") as mock_set_text, \
            patch.object(main_window.capture_button, "setDisabled") as mock_set_disabled:
        main_window.toggle_capturing()

        mock_set_text.assert_called_once_with("Start Capturing")

        mock_set_disabled.assert_called_once_with(True)


def test_toggle_capturing_when_capturing_is_false(main_window):
    main_window.capturing = False

    with patch.object(main_window.capture_button, "setText") as mock_set_text, \
            patch.object(threading, "Thread") as mock_thread, \
            patch.object(main_window.text_to_speech, "stop_voice") as mock_stop_voice:
        main_window.toggle_capturing()
        mock_set_text.assert_called_once_with("Stop Capturing")
        mock_thread.assert_called_once_with(target=main_window.capture_loop)

        main_window.capture_thread.start.assert_called_once()

        mock_stop_voice.assert_called_once()


def mock_capture_screenshot(monitor, monitor_index):
    global counter
    counter += 1
    return Image.new("RGB", (100, 100), (counter % 256, counter % 256, counter % 256))


def test_capture_loop_no_capture_area(main_window):
    main_window.capture_area = None

    with patch("components.main_window.print") as mock_print:
        main_window.capture_loop()
        mock_print.assert_called_once_with("Please select an area first.")


def test_capture_loop_capturing_true(main_window, monkeypatch):
    global counter
    counter = 0 

    main_window.capture_area = (0, 0, 100, 100)
    main_window.capturing = True
    monkeypatch.setattr("components.main_window.time.sleep", lambda *args, **kwargs: None)
    monkeypatch.setattr("components.main_window.capture_screenshot", mock_capture_screenshot)

    loop_thread = threading.Thread(target=main_window.capture_loop)
    loop_thread.start()
    time.sleep(10) 
    main_window.capturing = False  
    loop_thread.join()

    expected_number_of_screenshots = counter - 1  
    assert main_window.screenshot_queue.qsize() == expected_number_of_screenshots

def test_capture_loop_capturing_false(main_window):
    main_window.capture_area = (0, 0, 100, 100)
    main_window.capturing = False

    with patch("components.main_window.time.sleep") as mock_sleep:
        main_window.capture_loop()
        mock_sleep.assert_not_called()


