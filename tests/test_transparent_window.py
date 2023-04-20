import pytest
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtWidgets import QApplication, QWidget
from components.transparent_window import TransparentWindow
from PyQt5.QtTest import QTest
from unittest.mock import Mock


app = QApplication([])

@pytest.fixture
def transparent_window():
    main_window = Mock()  
    monitor_index = 0
    window = TransparentWindow(main_window, monitor_index)
    return window


def test_init(transparent_window):
    assert transparent_window.monitor_index == 0

def test_paint_event(transparent_window, qtbot):
    with qtbot.waitExposed(transparent_window):
        transparent_window.show()

    qtbot.wait(500)
    assert isinstance(transparent_window, QWidget)

def test_mouse_events(transparent_window, qtbot):
    with qtbot.waitExposed(transparent_window):
        transparent_window.show()

    start_point = QPoint(100, 100)
    end_point = QPoint(200, 200)

    QTest.mousePress(transparent_window, Qt.LeftButton, pos=start_point)
    assert transparent_window.start_point == start_point

    transparent_window.end_point = end_point
    assert transparent_window.end_point == end_point
    QTest.mouseRelease(transparent_window, Qt.LeftButton, pos=end_point)
    assert transparent_window.end_point == end_point



