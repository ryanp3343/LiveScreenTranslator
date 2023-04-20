from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor, QFontMetrics, QPen, QPainterPath
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
                255,
            )
        )
        painter.drawRect(self.rect())

        font = painter.font()
        font.setPointSize(20)
        font.setBold(True)
        painter.setFont(font)

        padding_top = 10
        padding_left_right = 10
        bounding_rect = QRect(0, 0, self.width() - 2 * padding_left_right, self.height())

        # Calculates the horizontal center
        font_metrics = QFontMetrics(font)
        text_rect = font_metrics.boundingRect(bounding_rect, Qt.TextWordWrap, self.text)
        x_center = padding_left_right + (bounding_rect.width() - text_rect.width()) // 2

        # Wrap the text into lines based on the available width
        text_lines = []
        words = self.text.split(' ')
        line = words[0]
        for word in words[1:]:
            new_line = line + ' ' + word
            if font_metrics.width(new_line) > bounding_rect.width():
                text_lines.append(line)
                line = word
            else:
                line = new_line
        text_lines.append(line)

        text_path = QPainterPath()
        current_y = font_metrics.capHeight() + padding_top
        for line in text_lines:
            text_path.addText(x_center, current_y, font, line)
            current_y += font_metrics.lineSpacing()

        # Draw outline
        painter.setPen(QPen(QColor(0, 0, 0), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(text_path)

        # Draw text with the fill color
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawPath(text_path)

        # Resize the window based on text and capture area width and height
        min_width, min_height = 50, 20
        new_width = max(text_rect.width() + 2 * padding_left_right, min_width)
        new_height = max(text_rect.height() + padding_top, min_height)
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
