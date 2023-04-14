from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor, QFontMetrics
from PyQt5.QtWidgets import QWidget, QDesktopWidget
import random


class TranslatedTextWindow(QWidget):
    """
    Translated Text Window Component for MainWindow, creates a window relative to size
    of text recieved, that is drawn in the middle of the users captured area
    """

    def __init__(self, parent, monitor_index, capture_area, text):
        """Basic init set values,attr,flags, and geometry"""
        super().__init__(parent)
        self.monitor_index = monitor_index
        self.capture_area = capture_area
        self.text = text

        # Qt flags to make sure the window stays on top of the screen
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        # Get specific desktop geometry
        desktop = QDesktopWidget()
        self.monitor_geometry = desktop.screenGeometry(monitor_index)
        x, y, width, height = capture_area
        self.setGeometry(x, y, width, height)

    def paintEvent(self, event):
        """Paints the translated window relative to amount of text and size of capture area"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor(255, 255, 255))
        painter.setBrush(
            QColor(
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
                230,
            )
        )
        painter.drawRect(self.rect())

        font = painter.font()
        font.setPointSize(20)
        painter.setFont(font)
        bounding_rect = QRect(0, 0, self.width(), self.height())

        # Caluclates the horizontal center
        font_metrics = QFontMetrics(font)
        text_rect = font_metrics.boundingRect(bounding_rect, Qt.TextWordWrap, self.text)
        x_center = (self.width() - text_rect.width()) // 2

        painter.drawText(
            x_center, 0, text_rect.width(), self.height(), Qt.TextWordWrap, self.text
        )

        # Resize the window bases on text and capture area width and height
        min_width, min_height = 50, 20
        new_width = max(text_rect.width(), min_width)
        new_height = max(text_rect.height(), min_height)
        self.resize(new_width, new_height)
        self.update_position()

    def update_position(self):
        """Calculate the x and y coordinates relative to capture area"""
        x = self.capture_area[0] + (self.capture_area[2] - self.width()) // 2
        y = self.capture_area[1] + (self.capture_area[3] - self.height()) // 2
        self.move(x, y)

    def update_text(self, new_text):
        """update the text to the window and draw it"""
        self.text = new_text
        self.update()
