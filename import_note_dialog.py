import sys
import os
import mimetypes
from PyQt6.QtWidgets import QDialog, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
from exceptions import FileImportError
from PyQt6.uic import loadUi


class ImportNoteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.has_unsaved_changes = False

        # ТОЛЬКО указанные форматы файлов
        self.supported_formats = {
            'Текстовые файлы': ['*.txt'],
            'PDF документы': ['*.pdf'],
            'Изображения': ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif'],
            'Аудио файлы': ['*.mp3'],
            'Видео файлы': ['*.mp4']
        }

        try:
            ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'import_note_dialog.ui')
            if not os.path.exists(ui_path):
                ui_path = os.path.join('ui', 'import_note_dialog.ui')
                if not os.path.exists(ui_path):
                    raise FileNotFoundError(f"UI файл не найден: {ui_path}")

            loadUi(ui_path, self)

            # Настройки
            self.file_path = None
            self.file_content = ""
            self.file_type = ""
            self.pushButton_Add.setEnabled(False)

            # Обновляем текст метки с указанием поддерживаемых форматов
            self.label.setText("Загрузите файл (txt, pdf, jpg/png, mp3, mp4)")

            # Подключаем кнопки
            self.pushButton.clicked.connect(self.select_file)
            self.pushButton_Add.clicked.connect(self.import_note)
            self.pushButton_Cancel.clicked.connect(self.cancel)

        except FileNotFoundError as e:
            QMessageBox.critical(None, "Ошибка", f"Файл интерфейса не найден: {str(e)}")
            raise
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка при загрузке диалога: {str(e)}")
            raise

    def select_file(self):
        """Выбор файла для импорта"""
        try:
            # Создаем строку фильтров
            filters = []
            filters.append("Все файлы (*.*)")

            for category, extensions in self.supported_formats.items():
                filter_str = f"{category} ({' '.join(extensions)})"
                filters.append(filter_str)

            filter_string = ";;".join(filters)

            file_path, selected_filter = QFileDialog.getOpenFileName(
                self,
                "Выберите файл для конспекта (поддерживаются: txt, pdf, jpg/png, mp3, mp4)",
                "",
                filter_string,
                "Все файлы (*.*)"
            )

            if file_path:
                # Определяем тип файла
                file_ext = os.path.splitext(file_path)[1].lower()
                self.file_type = self.determine_file_type(file_ext)

                # Проверка существования файла
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Выбранный файл не существует: {file_path}")

                # Проверка размера файла
                file_size = os.path.getsize(file_path)
                max_size = 100 * 1024 * 1024  # 100 МБ

                if file_size > max_size:
                    raise FileImportError(
                        f"Размер файла превышает 100 МБ.\n"
                        f"Текущий размер: {file_size / (1024 * 1024):.2f} МБ"
                    )

                self.file_path = file_path
                file_name = os.path.basename(file_path)

                # Обновляем отображение информации о файле
                info_text = f"{file_name}\nТип: {self.file_type}\nРазмер: {file_size / 1024:.1f} КБ"
                self.label_2.setText(info_text)
                self.pushButton_Add.setEnabled(True)
                self.has_unsaved_changes = True

                # Подготовка предпросмотра
                self.prepare_file_preview(file_path, file_ext)

        except FileNotFoundError as e:
            QMessageBox.warning(self, "Файл не найден", str(e))
        except FileImportError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при выборе файла: {str(e)}")

    def determine_file_type(self, file_ext):
        """Определение типа файла по расширению"""
        file_ext = file_ext.lower()

        # Только указанные форматы
        if file_ext == '.txt':
            return "Текстовый файл"
        elif file_ext == '.pdf':
            return "PDF документ"
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            return "Изображение"
        elif file_ext == '.mp3':
            return "Аудио файл MP3"
        elif file_ext == '.mp4':
            return "Видео файл MP4"
        else:
            return "Неизвестный тип"

    def prepare_file_preview(self, file_path, file_ext):
        """Подготовка предварительного просмотра файла"""
        try:
            file_ext = file_ext.lower()
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            # Для текстовых файлов
            if file_ext == '.txt':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(1000)
                        if len(content) == 1000:
                            content += "..."
                        self.file_content = content
                except:
                    self.file_content = f"Текстовый файл: {file_name}"

            # Для PDF
            elif file_ext == '.pdf':
                self.file_content = (
                    f"PDF документ: {file_name}\n"
                    f"Размер: {file_size / 1024:.1f} КБ\n"
                    f"Нейросеть будет анализировать текстовое содержимое PDF"
                )

            # Для изображений
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                self.file_content = (
                    f"Изображение: {file_name}\n"
                    f"Размер: {file_size / 1024:.1f} КБ\n"
                    f"Нейросеть будет анализировать изображение"
                )

            # Для MP3
            elif file_ext == '.mp3':
                self.file_content = (
                    f"Аудио файл MP3: {file_name}\n"
                    f"Размер: {file_size / (1024 * 1024):.2f} МБ\n"
                    f"Нейросеть будет анализировать аудиофайл"
                )

            # Для MP4
            elif file_ext == '.mp4':
                self.file_content = (
                    f"Видео файл MP4: {file_name}\n"
                    f"Размер: {file_size / (1024 * 1024):.2f} МБ\n"
                    f"Нейросеть будет анализировать видеофайл"
                )

        except Exception as e:
            self.file_content = f"Файл: {file_name}"

    def import_note(self):
        """Импорт выбранного файла"""
        try:
            if not self.file_path:
                raise FileImportError("Файл не выбран")

            if not os.path.exists(self.file_path):
                raise FileNotFoundError("Выбранный файл больше не существует")

            # Проверка на опасные расширения
            dangerous_extensions = ['.exe', '.bat', '.cmd', '.vbs', '.ps1', '.sh']
            file_ext = os.path.splitext(self.file_path)[1].lower()
            if file_ext in dangerous_extensions:
                reply = QMessageBox.warning(
                    self,
                    "Предупреждение",
                    f"Выбранный файл имеет расширение {file_ext}.\n"
                    f"Вы уверены, что хотите продолжить?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Подготовка финального содержимого
            final_content = self.prepare_final_content()
            self.file_content = final_content

            QMessageBox.information(
                self,
                "Успешно",
                f"Файл '{os.path.basename(self.file_path)}' успешно добавлен!\n"
                f"Тип: {self.file_type}"
            )

            self.has_unsaved_changes = False
            self.accept()

        except FileNotFoundError as e:
            QMessageBox.warning(self, "Файл не найден", str(e))
        except FileImportError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить файл:\n{str(e)}")

    def prepare_final_content(self):
        """Подготовка финального содержимого файла для сохранения"""
        file_ext = os.path.splitext(self.file_path)[1].lower()
        file_name = os.path.basename(self.file_path)
        file_size = os.path.getsize(self.file_path)

        # Для текстовых файлов
        if file_ext == '.txt':
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) > 50000:
                        content = content[:50000] + "\n...[файл обрезан]"
                    return f"Текстовый файл: {file_name}\n\n{content}"
            except:
                return f"Текстовый файл: {file_name}\n(ошибка чтения)"

        # Для PDF
        elif file_ext == '.pdf':
            return (
                f"PDF документ: {file_name}\n"
                f"Размер: {file_size / 1024:.1f} КБ\n\n"
                f"Нейросеть будет анализировать текстовое содержимое PDF документа."
            )

        # Для изображений
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            image_type = "JPG" if file_ext in ['.jpg',
                                               '.jpeg'] else "PNG" if file_ext == '.png' else "GIF" if file_ext == '.gif' else "BMP"
            return (
                f"Изображение: {file_name}\n"
                f"Тип: {image_type}\n"
                f"Размер: {file_size / 1024:.1f} КБ\n\n"
                f"Нейросеть будет анализировать изображение."
            )

        # Для MP3
        elif file_ext == '.mp3':
            return (
                f"Аудио файл: {file_name}\n"
                f"Формат: MP3\n"
                f"Размер: {file_size / (1024 * 1024):.2f} МБ\n\n"
                f"Нейросеть будет анализировать аудиофайл."
            )

        # Для MP4
        elif file_ext == '.mp4':
            return (
                f"Видео файл: {file_name}\n"
                f"Формат: MP4\n"
                f"Размер: {file_size / (1024 * 1024):.2f} МБ\n\n"
                f"Нейросеть будет анализировать видеофайл."
            )

        # Для других файлов (если пользователь выбрал "Все файлы")
        else:
            return (
                f"Файл: {file_name}\n"
                f"Тип: {self.file_type}\n"
                f"Размер: {file_size} байт\n\n"
                f"Нейросеть попытается проанализировать файл."
            )

    def cancel(self):
        """Отмена импорта"""
        try:
            if self.has_unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    "Подтверждение",
                    "У вас есть несохраненные изменения.\nВы уверены, что хотите отменить?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.reject()
            else:
                self.reject()
        except Exception as e:
            self.reject()

    def keyPressEvent(self, event):
        """Обработка нажатия клавиши Escape"""
        if event.key() == Qt.Key.Key_Escape:
            if self.has_unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    'Несохраненные изменения',
                    'У вас есть несохраненные изменения.\nЗакрыть без сохранения?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.reject()
            else:
                self.reject()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Обработка закрытия окна через крестик"""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                'Несохраненные изменения',
                'У вас есть несохраненные изменения.\nЗакрыть без сохранения?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def get_note_content(self):
        """Получение содержимого конспекта"""
        return self.file_content if hasattr(self, 'file_content') and self.file_content else ""

    def get_note_name(self):
        """Получение имени конспекта"""
        if self.file_path:
            base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            return f"{base_name} ({self.file_type})"
        return ""
