import sys
from PyQt6.QtWidgets import QApplication
from config.styles import STYLESHEET
from windows.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()