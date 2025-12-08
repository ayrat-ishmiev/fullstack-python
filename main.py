import sys
import os
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt
from config.styles import STYLESHEET
from windows.main_window import MainWindow


def resource_path(relative_path):
    """ Получает абсолютный путь к ресурсу для PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('icon.png')))
    app.setStyleSheet(STYLESHEET)

    # --- РАБОТА С ОКНОМ ЗАГРУЗКИ ---
    original_pixmap = QPixmap(resource_path('Loading.png'))

    # УМЕНЬШАЕМ КАРТИНКУ:
    # 400 - ширина, второй параметр - высота (используется AspectRatioMode для сохранения пропорций)
    scaled_pixmap = original_pixmap.scaled(
        400, 400,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )

    splash = QSplashScreen(scaled_pixmap)
    splash.show()

    # Текст на заставке (опционально)
    splash.showMessage(
        "",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
        Qt.GlobalColor.white
    )

    app.processEvents()

    # Инициализация основного окна
    window = MainWindow()
    window.show()

    # Закрываем заставку
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
