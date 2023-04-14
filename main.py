"""main.py intializes qapplicaiton and runs my main window"""
import sys
from PyQt5.QtWidgets import QApplication
from components.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
