# windows/dialogs/add_note_choice.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class AddNoteChoiceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить конспект")
        self.resize(400, 250)
        self.choice = None  # 'file' или 'ai'

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        lbl = QLabel("Как вы хотите создать конспект?", self)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        lbl.setFont(font)
        layout.addWidget(lbl)

        # Кнопка Импорта
        self.btn_file = QPushButton("📁 Загрузить файл\n(PDF, Фото, Аудио, Видео)", self)
        self.btn_file.setMinimumHeight(60)
        self.btn_file.clicked.connect(self.select_file)
        layout.addWidget(self.btn_file)

        # Кнопка Генерации
        self.btn_ai = QPushButton("✨ Сгенерировать нейросетью\n(По теме или запросу)", self)
        self.btn_ai.setMinimumHeight(60)
        self.btn_ai.setStyleSheet("QPushButton { border: 1px solid #cbbbc4; }") # Акцентный цвет
        self.btn_ai.clicked.connect(self.select_ai)
        layout.addWidget(self.btn_ai)

    def select_file(self):
        self.choice = 'file'
        self.accept()

    def select_ai(self):
        self.choice = 'ai'
        self.accept()