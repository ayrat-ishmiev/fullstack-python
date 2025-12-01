import sys
import os
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import Qt
from exceptions import SubjectValidationError
from PyQt6.uic import loadUi

# Добавляем путь к ui файлам
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class AddSubjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.has_unsaved_changes = False  # Флаг для отслеживания изменений

        try:
            # Загружаем UI файл (ИСПРАВЛЕН ПУТЬ - убрано '..')
            ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'add_subject_dialog.ui')
            if not os.path.exists(ui_path):
                # Попробуем альтернативный путь
                ui_path = os.path.join('ui', 'add_subject_dialog.ui')
                if not os.path.exists(ui_path):
                    raise FileNotFoundError(f"UI файл не найден: {ui_path}")

            loadUi(ui_path, self)

            # Настройки
            self.lineEdit.textChanged.connect(self.on_text_changed)
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

    def on_text_changed(self):
        """Обработка изменения текста"""
        try:
            has_text = bool(self.lineEdit.text().strip())
            self.pushButton_Add.setEnabled(has_text)
            self.has_unsaved_changes = has_text  # Если есть текст - есть изменения
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
            self.has_unsaved_changes = False  # Изменения сохранены
            self.accept()

        except SubjectValidationError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Неизвестная ошибка", f"Произошла непредвиденная ошибка: {str(e)}")

    def cancel(self):
        """Отмена добавления предмета"""
        try:
            if self.has_unsaved_changes:
                reply = QMessageBox.question(self, "Подтверждение",
                                             "У вас есть несохраненные изменения.\nВы уверены, что хотите отменить добавление предмета?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    self.reject()
            else:
                self.reject()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отмене: {str(e)}")
            self.reject()

    def keyPressEvent(self, event):
        """Обработка нажатия клавиши Escape для диалога добавления предмета"""
        if event.key() == Qt.Key.Key_Escape:
            self.handle_escape_press()
        else:
            super().keyPressEvent(event)

    def handle_escape_press(self):
        """Обработка нажатия клавиши Escape"""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                'Несохраненные изменения',
                'У вас есть несохраненные изменения.\nЗакрыть диалог без сохранения?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.reject()
        else:
            self.reject()

    def closeEvent(self, event):
        """Обработка закрытия окна через крестик"""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                'Несохраненные изменения',
                'У вас есть несохраненные изменения.\nЗакрыть диалог без сохранения?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()  # Закрыть окно
            else:
                event.ignore()  # Не закрывать окно
        else:
            event.accept()  # Закрыть окно
