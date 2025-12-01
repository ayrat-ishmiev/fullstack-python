import sys
import os
from PyQt6.QtWidgets import QDialog, QMessageBox
from exceptions import SubjectValidationError
from PyQt6.uic import loadUi

# Добавляем путь к ui файлам
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class AddSubjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        try:
            # Загружаем UI файл
            ui_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'add_subject_dialog.ui')
            if not os.path.exists(ui_path):
                raise FileNotFoundError(f"UI файл не найден: {ui_path}")

            loadUi(ui_path, self)

            # Настройки
            self.lineEdit.textChanged.connect(self.check_input)
            self.pushButton_Add.setEnabled(False)

            # Подключаем кнопки
            self.pushButton_Add.clicked.connect(self.add_subject)
            self.pushButton_Cancel.clicked.connect(self.cancel)

        except FileNotFoundError as e:
            QMessageBox.critical(None, "Ошибка инициализации", f"Файл интерфейса не найден: {str(e)}")
            raise
        except Exception as e:
            QMessageBox.critical(None, "Ошибка инициализации", f"Ошибка при загрузке диалога: {str(e)}")
            raise

    def check_input(self):
        """Проверка ввода названия предмета"""
        try:
            has_text = bool(self.lineEdit.text().strip())
            self.pushButton_Add.setEnabled(has_text)
        except Exception as e:
            print(f"Ошибка при проверке ввода: {e}")

    def add_subject(self):
        """Добавление нового предмета"""
        try:
            subject_name = self.lineEdit.text().strip()

            # Проверка на пустое название
            if not subject_name:
                raise SubjectValidationError("Название предмета не может быть пустым")

            # Проверка на минимальную длину
            if len(subject_name) < 2:
                raise SubjectValidationError("Название предмета должно содержать минимум 2 символа")

            # Проверка на максимальную длину
            if len(subject_name) > 50:
                raise SubjectValidationError("Название предмета не должно превышать 50 символов")

            # Проверка на запрещённые символы
            forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            for char in forbidden_chars:
                if char in subject_name:
                    raise SubjectValidationError(f"Название содержит запрещённый символ: '{char}'")

            QMessageBox.information(self, "Успех", f"Предмет '{subject_name}' добавлен!")
            self.accept()

        except SubjectValidationError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Неизвестная ошибка", f"Произошла непредвиденная ошибка: {str(e)}")

    def cancel(self):
        """Отмена добавления предмета"""
        try:
            reply = QMessageBox.question(self, "Подтверждение",
                                         "Вы уверены, что хотите отменить?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.reject()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отмене: {str(e)}")
            self.reject()