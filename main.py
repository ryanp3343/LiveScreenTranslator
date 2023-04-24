"""main.py intializes qapplicaiton and runs my main window"""
import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from components.main_window import MainWindow

def check_tesseract_installation():
    tesseract_path = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    if not os.path.exists(tesseract_path):
        return False
    return True

def show_error_message():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText("Tesseract-OCR not found")
    msg.setInformativeText("Please make sure Tesseract-OCR is installed and the file path is \nC:\Program Files\Tesseract-OCR\\tesseract.exe")
    msg.setWindowTitle("Error")
    msg.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    if check_tesseract_installation():
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec_())
    else:
        show_error_message()
