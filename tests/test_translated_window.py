import pytest
from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication, QWidget
from components.translated_window import TranslatedTextWindow
from unittest.mock import MagicMock

app = QApplication([])

@pytest.fixture
def text_window():
    parent = None
    monitor_index = 0
    capture_area = (0, 0, 300, 200)
    text = "Test text"
    window = TranslatedTextWindow(parent, monitor_index, capture_area, text)
    return window

def test_init(text_window):
    assert text_window.monitor_index == 0
    assert text_window.capture_area == (0, 0, 300, 200)
    assert text_window.text == "Test text"

def test_paint_event(text_window, qtbot):
    with qtbot.waitExposed(text_window):
        text_window.show()

    qtbot.wait(500)
    assert isinstance(text_window, QWidget)

def test_update_position(text_window):
    text_window.move = MagicMock()
    text_window.resize(100, 50)
    text_window.update_position()
    expected_x = text_window.capture_area[0] + (text_window.capture_area[2] - 100) // 2
    expected_y = text_window.capture_area[1] + (text_window.capture_area[3] - 50) // 2
    text_window.move.assert_called_once_with(expected_x, expected_y)

def test_update_text(text_window):
    new_text = "New test text"
    text_window.update_text(new_text)
    assert text_window.text == new_text



