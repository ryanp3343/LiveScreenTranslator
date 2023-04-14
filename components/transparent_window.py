"""transparent window class"""
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QDesktopWidget, QWidget
from mss import mss


class TransparentWindow(QWidget):
    """
    Transparent Window Component for MainWindow, creates a black semi-transparent window over
    the users selected screen. Uses Mouse Events for user to click and drag on the semi-transparent window
    """

    def __init__(self, main_window, monitor_index):
        """Basic init set values,attr,flags, and geometry"""
        super().__init__()
        self.main_window = main_window
        self.monitor_index = monitor_index

        # Qt flags and attributes that make the transparent background stay ontop of the screen
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        # Get specific desktop geometry
        desktop = QDesktopWidget()
        monitor_geometry = desktop.screenGeometry(monitor_index)
        self.setGeometry(monitor_geometry)

        # set geometry for mss
        with mss() as sct:
            monitor = sct.monitors[self.monitor_index]
            x, y, width, height = (
                monitor["left"],
                monitor["top"],
                monitor["width"] - 1,
                monitor["height"] - 1,
            )
            self.setGeometry(x, y, width, height)

        self.start_point = None
        self.end_point = None
        self.selection_rect = None
        self.pen = QPen(Qt.red)
        self.pen.setWidth(2)

    def paintEvent(self, event):
        """Draw Rect over dragged mouse events"""
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
        """Get start and end points when mouse is clicked on screen"""
        self.start_point = event.pos()
        self.end_point = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        """Get positions when mouse is held down and dragged across the screen"""
        self.end_point = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        """Get point where mouse is release send start and end values to update capture area"""
        self.end_point = event.pos()
        self.main_window.update_capture_area(
            self.start_point, self.end_point, self.geometry()
        )
        self.close()
