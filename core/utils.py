import sys
import os

def resource_path(relative_path):
    """
    Получает абсолютный путь к ресурсу, работает и в режиме разработки,
    и после упаковки PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
