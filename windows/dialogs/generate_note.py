# windows/dialogs/generate_note.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QProgressDialog, \
    QMessageBox, QApplication
from PyQt6.QtCore import Qt, QTimer
from services.ai_service import AIService


class GenerateNoteDialog(QDialog):
    def __init__(self, subject_name, parent=None):
        super().__init__(parent)
        self.subject_name = subject_name
        self.note_title = ""
        self.note_content = ""

        self.setWindowTitle("Генерация конспекта")
        self.resize(500, 300)

        layout = QVBoxLayout(self)

        # Инструкция
        layout.addWidget(QLabel(f"Предмет: <b>{subject_name}</b>"))
        layout.addWidget(QLabel("Введите тему конспекта:"))

        # Поле ввода темы
        self.topic_input = QLineEdit(self)
        self.topic_input.setPlaceholderText("Например: Основы ООП, История Древнего Рима...")
        self.topic_input.setMinimumHeight(40)
        layout.addWidget(self.topic_input)

        # Кнопка генерации
        self.btn_generate = QPushButton("✨ Сгенерировать конспект", self)
        self.btn_generate.setMinimumHeight(45)
        self.btn_generate.clicked.connect(self.generate)
        layout.addWidget(self.btn_generate)

        # Отмена
        self.btn_cancel = QPushButton("Отмена", self)
        self.btn_cancel.clicked.connect(self.reject)
        layout.addWidget(self.btn_cancel)

    def generate(self):
        topic = self.topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "Ошибка", "Введите тему конспекта")
            return

        self.note_title = topic

        # Показываем прогресс
        progress = QProgressDialog("Нейросеть пишет конспект...\nЭто займет около 10-20 секунд.", None, 0, 0, self)
        progress.setWindowTitle("Генерация")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setCancelButton(None)
        progress.show()

        # Анимация точек
        dots = 0

        def update_dots():
            nonlocal dots
            dots = (dots + 1) % 4
            progress.setLabelText(f"Нейросеть пишет конспект{'.' * dots}\nФормирование структуры...")

        timer = QTimer()
        timer.timeout.connect(update_dots)
        timer.start(500)

        try:
            QApplication.processEvents()

            # Вызов AI
            content = AIService.generate_study_note(topic, self.subject_name)
            self.note_content = content

            timer.stop()
            progress.close()

            QMessageBox.information(self, "Готово", "Конспект успешно сгенерирован!")
            self.accept()

        except Exception as e:
            timer.stop()
            progress.close()
            QMessageBox.critical(self, "Ошибка", f"Ошибка генерации: {e}")

    def get_note_name(self):
        return self.note_title

    def get_note_content(self):
        return self.note_content