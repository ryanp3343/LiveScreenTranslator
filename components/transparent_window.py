from mss import mss
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QDesktopWidget,QWidget

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
