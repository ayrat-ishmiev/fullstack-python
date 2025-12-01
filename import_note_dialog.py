import sys
import os
from PyQt6.QtWidgets import QDialog, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
from exceptions import FileImportError
from PyQt6.uic import loadUi


class ImportNoteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.has_unsaved_changes = False  # Флаг для отслеживания изменений

        try:
            # Загружаем UI файл (ИСПРАВЛЕН ПУТЬ - убрано '..')
            ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'import_note_dialog.ui')
            if not os.path.exists(ui_path):
                # Попробуем альтернативный путь
                ui_path = os.path.join('ui', 'import_note_dialog.ui')
                if not os.path.exists(ui_path):
                    raise FileNotFoundError(f"UI файл не найден: {ui_path}")

            loadUi(ui_path, self)

            # Настройки
            self.file_path = None
            self.pushButton_Add.setEnabled(False)  # Кнопка "Добавить" изначально неактивна

            # Подключаем кнопки с ПРАВИЛЬНЫМИ именами
            self.pushButton.clicked.connect(self.select_file)  # Кнопка "Выбрать файл"
            self.pushButton_Add.clicked.connect(self.import_note)  # Кнопка "Добавить"
            self.pushButton_Cancel.clicked.connect(self.cancel)  # Кнопка "Отмена"

        except FileNotFoundError as e:
            QMessageBox.critical(None, "Ошибка инициализации", f"Файл интерфейса не найден: {str(e)}")
            raise
        except Exception as e:
            QMessageBox.critical(None, "Ошибка инициализации", f"Ошибка при загрузке диалога: {str(e)}")
            raise

    def select_file(self):
        """Выбор файла для импорта"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Выберите файл конспекта",
                "",
                "Текстовые файлы (*.txt);;Документы (*.doc *.docx);;Изображения (*.jpg *.jpeg *.png);;Все файлы (*.*)"
            )

            if file_path:
                # Проверка существования файла
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Выбранный файл не существует: {file_path}")

                # Проверка размера файла (максимум 10 МБ)
                file_size = os.path.getsize(file_path)
                max_size = 10 * 1024 * 1024  # 10 МБ в байтах
                if file_size > max_size:
                    raise FileImportError(
                        f"Размер файла превышает допустимый лимит 10 МБ. Текущий размер: {file_size / (1024 * 1024):.2f} МБ")

                # Проверка на пустой файл
                if file_size == 0:
                    raise FileImportError("Выбранный файл пуст")

                self.file_path = file_path
                file_name = os.path.basename(file_path)

                # ДИНАМИЧЕСКОЕ ИЗМЕНЕНИЕ
                self.label_2.setText(file_name)  # label_2 - это метка для имени файла
                self.label_2.setStyleSheet("color: green; font-weight: bold;")
                self.pushButton_Add.setEnabled(True)
                self.has_unsaved_changes = True  # Файл выбран - есть изменения

        except FileNotFoundError as e:
            QMessageBox.warning(self, "Файл не найден", str(e))
        except FileImportError as e:
            QMessageBox.warning(self, "Ошибка выбора файла", str(e))
        except PermissionError as e:
            QMessageBox.warning(self, "Ошибка доступа", f"Нет прав доступа к файлу: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Неизвестная ошибка", f"Ошибка при выборе файла: {str(e)}")

    def import_note(self):
        """Импорт выбранного файла"""
        try:
            if not self.file_path:
                raise FileImportError("Файл не выбран")

            # Дополнительные проверки перед импортом
            if not os.path.exists(self.file_path):
                raise FileNotFoundError("Выбранный файл больше не существует")

            # Проверка расширения файла
            allowed_extensions = ['.txt', '.doc', '.docx', '.jpg', '.jpeg', '.png']
            file_extension = os.path.splitext(self.file_path)[1].lower()
            if file_extension not in allowed_extensions:
                raise FileImportError(
                    f"Неподдерживаемый формат файла: {file_extension}. Допустимые форматы: {', '.join(allowed_extensions)}")

            # Симуляция импорта файла
            self._simulate_file_import()

            file_name = os.path.basename(self.file_path)
            QMessageBox.information(
                self,
                "Успех",
                f"Конспект из файла '{file_name}' успешно импортирован!"
            )
            self.has_unsaved_changes = False  # Изменения сохранены
            self.accept()

        except FileNotFoundError as e:
            QMessageBox.warning(self, "Файл не найден", str(e))
        except FileImportError as e:
            QMessageBox.warning(self, "Ошибка импорта", str(e))
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка импорта",
                f"Не удалось импортировать файл:\n{str(e)}"
            )

    def _simulate_file_import(self):
        """Симуляция процесса импорта файла с возможными ошибками"""
        # Проверка, доступен ли файл для чтения
        try:
            with open(self.file_path, 'rb') as f:
                # Читаем первые несколько байт для проверки доступности
                f.read(10)
        except IOError as e:
            raise IOError(f"Файл недоступен для чтения: {str(e)}")

    def cancel(self):
        """Отмена импорта"""
        try:
            if self.has_unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    "Подтверждение отмены",
                    "У вас есть несохраненные изменения.\nВы уверены, что хотите отменить импорт файла?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.reject()
            else:
                self.reject()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отмене: {str(e)}")
            self.reject()

    def keyPressEvent(self, event):
        """Обработка нажатия клавиши Escape для диалога импорта файла"""
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
