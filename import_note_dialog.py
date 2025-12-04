import sys
import os
import mimetypes
from PyQt6.QtWidgets import QDialog, QMessageBox, QFileDialog, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QIcon
from exceptions import FileImportError
from PyQt6.uic import loadUi


class ImportNoteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.has_unsaved_changes = False  # Флаг для отслеживания изменений

        # Поддерживаемые форматы файлов для нейросети
        self.supported_formats = {
            '📄 Текстовые файлы': ['*.txt', '*.md', '*.rtf'],
            '📝 Документы Word': ['*.doc', '*.docx', '*.odt'],
            '📋 PDF документы': ['*.pdf'],
            '📊 Электронные таблицы': ['*.xls', '*.xlsx', '*.ods', '*.csv'],
            '📽️ Презентации': ['*.ppt', '*.pptx', '*.odp'],
            '🖼️ Изображения': ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.tiff', '*.webp'],
            '🌐 Веб-страницы': ['*.html', '*.htm'],
            '💻 Исходный код': ['*.py', '*.java', '*.cpp', '*.c', '*.js', '*.css', '*.sql', '*.php', '*.rb'],
            '📊 Файлы данных': ['*.json', '*.xml', '*.yaml', '*.yml']
        }

        try:
            # Загружаем UI файл
            ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'import_note_dialog.ui')
            if not os.path.exists(ui_path):
                # Попробуем альтернативный путь
                ui_path = os.path.join('ui', 'import_note_dialog.ui')
                if not os.path.exists(ui_path):
                    raise FileNotFoundError(f"UI файл не найден: {ui_path}")

            loadUi(ui_path, self)

            # Настройки
            self.file_path = None
            self.file_content = ""  # Будет хранить содержимое файла или описание
            self.file_type = ""  # Тип файла для обработки нейросетью
            self.pushButton_Add.setEnabled(False)  # Кнопка "Добавить" изначально неактивна

            # Устанавливаем иконку для окна
            self.setWindowIcon(self.create_icon())

            # Обновляем стили
            self.apply_styles()

            # Создаем информационную кнопку и добавляем ее в layout
            self.add_info_button()

            # Обновляем текст и стили кнопок
            self.pushButton.setText("📁 Выбрать файл")
            self.pushButton_Add.setText("✅ Добавить")
            self.pushButton_Cancel.setText("❌ Отмена")

            # Добавляем ToolTip
            self.pushButton.setToolTip("Нажмите для выбора файла")
            self.label_2.setToolTip("Здесь будет отображаться информация о выбранном файле")

            # Подключаем кнопки
            self.pushButton.clicked.connect(self.select_file)  # Кнопка "Выбрать файл"
            self.pushButton_Add.clicked.connect(self.import_note)  # Кнопка "Добавить"
            self.pushButton_Cancel.clicked.connect(self.cancel)  # Кнопка "Отмена"

        except FileNotFoundError as e:
            QMessageBox.critical(None, "Ошибка инициализации", f"Файл интерфейса не найден: {str(e)}")
            raise
        except Exception as e:
            QMessageBox.critical(None, "Ошибка инициализации", f"Ошибка при загрузке диалога: {str(e)}")
            raise

    def create_icon(self):
        """Создание иконки для окна"""
        # Создаем простую иконку с символом документа
        from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
        from PyQt6.QtCore import QRect

        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Рисуем документ
        painter.setBrush(QBrush(QColor("#4a90e2")))
        painter.setPen(QPen(QColor("#357abd"), 2))
        painter.drawRoundedRect(4, 4, 24, 28, 4, 4)

        # Рисуем линии текста
        painter.setPen(QPen(QColor("white"), 2))
        painter.drawLine(8, 12, 20, 12)
        painter.drawLine(8, 16, 20, 16)
        painter.drawLine(8, 20, 16, 20)

        painter.end()
        return QIcon(pixmap)

    def apply_styles(self):
        """Применение стилей ко всему диалогу"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            QLabel {
                color: #333333;
                font-size: 10pt;
            }

            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10pt;
                min-height: 30px;
            }

            QPushButton:hover {
                background-color: #357abd;
            }

            QPushButton:pressed {
                background-color: #2c5fa3;
            }

            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }

            QLineEdit, QTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 6px;
                background-color: white;
                font-size: 10pt;
            }

            QLineEdit:focus, QTextEdit:focus {
                border-color: #4a90e2;
            }
        """)

        # Стили для метки с информацией о файле
        self.label_2.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                font-size: 10pt;
                padding: 12px;
                background-color: white;
                border-radius: 8px;
                border: 2px solid #e0e0e0;
                min-height: 60px;
            }
        """)

    def add_info_button(self):
        """Добавление информационной кнопки рядом с заголовком"""
        # Создаем горизонтальный layout для заголовка
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)

        # Создаем иконку для заголовка
        icon_label = QLabel("📄")
        icon_label.setStyleSheet("font-size: 14pt;")

        # Создаем заголовок
        title_label = QLabel("Загрузка файла для конспекта")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_font.setFamily('Segoe UI')
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50;")

        # Создаем информационную кнопку
        self.info_button = QPushButton("ℹ️")
        self.info_button.setFixedSize(30, 30)
        self.info_button.setToolTip("Информация о поддерживаемых форматах")
        self.info_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:pressed {
                background-color: #d35400;
            }
        """)
        self.info_button.clicked.connect(self.show_formats_info)

        # Добавляем элементы в layout
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.info_button)

        # Вставляем layout в вертикальный layout
        original_index = self.verticalLayout.indexOf(self.label)
        if original_index != -1:
            # Создаем контейнер для заголовка
            title_widget = QWidget()
            title_widget.setLayout(title_layout)
            title_widget.setStyleSheet("background-color: #e8f4fc; border-radius: 8px; padding: 10px;")

            # Заменяем оригинальный label на наш виджет
            self.verticalLayout.insertWidget(original_index, title_widget)

            # Удаляем оригинальный label
            self.label.setParent(None)

            # Сохраняем ссылку на новый виджет заголовка
            self.title_widget = title_widget

    def show_formats_info(self):
        """Показ информации о поддерживаемых форматах"""
        # Создаем красивое информационное сообщение
        info_text = """
        <div style="font-family: 'Segoe UI', Arial, sans-serif;">
            <h3 style="color: #2c3e50; margin-top: 0;">📚 Поддерживаемые форматы файлов</h3>

            <div style="background-color: #e8f4fc; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <p style="color: #2c3e50; margin: 0;">
                    <b>✨ Приложение поддерживает широкий спектр форматов файлов!</b><br>
                    Нейросеть лучше всего работает с текстовыми данными.
                </p>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
        """

        # Добавляем форматы в две колонки
        formats_html = []
        for category, extensions in self.supported_formats.items():
            ext_list = [ext.replace('*.', '').upper() for ext in extensions[:4]]
            ext_str = ', '.join(ext_list)
            if len(extensions) > 4:
                ext_str += f" +{len(extensions) - 4}"

            formats_html.append(f"""
                <div style="background-color: white; padding: 10px; border-radius: 6px; border-left: 4px solid #4a90e2;">
                    <div style="font-weight: bold; color: #2c3e50;">{category}</div>
                    <div style="color: #7f8c8d; font-size: 9pt;">{ext_str}</div>
                </div>
            """)

        info_text += ''.join(formats_html)
        info_text += """
            </div>

            <div style="margin-top: 20px; padding: 15px; background-color: #fff8e1; border-radius: 8px; border-left: 4px solid #f39c12;">
                <h4 style="color: #e67e22; margin-top: 0;">💡 Рекомендации:</h4>
                <ul style="color: #2c3e50; margin: 0; padding-left: 20px;">
                    <li><b>Текстовые файлы (.txt, .md)</b> - дают наилучшие результаты</li>
                    <li><b>Документы (.docx, .pdf)</b> - текст будет извлечен автоматически</li>
                    <li><b>Изображения</b> - нейросеть попытается распознать текст на картинке</li>
                    <li><b>Файлы кода</b> - будут проанализированы как текстовые данные</li>
                </ul>
            </div>

            <div style="margin-top: 15px; color: #7f8c8d; font-size: 9pt; text-align: center;">
                🚀 Выберите любой файл - приложение попытается обработать его содержимое
            </div>
        </div>
        """

        # Создаем кастомное диалоговое окно с информацией
        info_dialog = QDialog(self)
        info_dialog.setWindowTitle("📋 Информация о форматах файлов")
        info_dialog.setFixedSize(550, 450)
        info_dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10pt;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)

        layout = QVBoxLayout(info_dialog)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 15)

        # Верхняя панель с заголовком
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #2c3e50; padding: 15px;")
        header_layout = QHBoxLayout(header_widget)
        header_label = QLabel("📋 Информация о форматах")
        header_label.setStyleSheet("color: white; font-size: 12pt; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Основной контент
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Добавляем HTML текст
        text_label = QLabel()
        text_label.setText(info_text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("background-color: transparent;")

        # Добавляем кнопку закрытия
        close_button = QPushButton("✅ Понятно, спасибо!")
        close_button.clicked.connect(info_dialog.accept)

        content_layout.addWidget(text_label)
        content_layout.addStretch()
        content_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(header_widget)
        layout.addWidget(content_widget)

        info_dialog.exec()

    def select_file(self):
        """Выбор файла для импорта с поддержкой всех форматов"""
        try:
            # Создаем строку фильтров для диалога выбора файла
            filters = []

            # 1. Сначала добавляем "Все файлы" - это ОСНОВНОЙ фильтр
            filters.append("Все файлы (*.*)")

            # 2. Затем добавляем остальные фильтры по категориям
            for category, extensions in self.supported_formats.items():
                # Убираем эмодзи из названия категории для фильтра
                clean_category = category.split(' ', 1)[1] if ' ' in category else category
                filter_str = f"{clean_category} ({' '.join(extensions)})"
                filters.append(filter_str)

            filter_string = ";;".join(filters)

            # Открываем диалог выбора файла
            file_path, selected_filter = QFileDialog.getOpenFileName(
                self,
                "Выберите файл для конспекта",
                "",
                filter_string,
                "Все файлы (*.*)"  # Фильтр по умолчанию
            )

            if file_path:
                # Определяем тип файла по расширению
                file_ext = os.path.splitext(file_path)[1].lower()
                self.file_type = self.determine_file_type(file_ext)

                # Проверка существования файла
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Выбранный файл не существует: {file_path}")

                # Проверка размера файла
                file_size = os.path.getsize(file_path)
                max_size = 50 * 1024 * 1024  # 50 МБ

                # Для документов и изображений увеличиваем лимит
                if file_ext in ['.pdf', '.docx', '.xlsx', '.pptx']:
                    max_size = 100 * 1024 * 1024  # 100 МБ

                if file_size > max_size:
                    raise FileImportError(
                        f"Размер файла превышает допустимый лимит.\n"
                        f"Текущий размер: {file_size / (1024 * 1024):.2f} МБ\n"
                        f"Максимальный размер: {max_size / (1024 * 1024):.2f} МБ"
                    )

                # Проверка на пустой файл
                if file_size == 0 and file_ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                    raise FileImportError("Выбранный файл пуст")

                self.file_path = file_path
                file_name = os.path.basename(file_path)

                # Определяем MIME-тип файла
                mime_type, _ = mimetypes.guess_type(file_path)

                # Обновляем отображение информации о файле
                icon = self.get_file_icon(file_ext)
                info_text = f"{icon} <b>{file_name}</b><br>"
                info_text += f"📋 <i>{self.file_type}</i><br>"
                info_text += f"📊 Размер: {file_size / 1024:.1f} КБ"

                self.label_2.setText(info_text)
                self.label_2.setStyleSheet("""
                    QLabel {
                        color: #2c3e50;
                        font-size: 10pt;
                        padding: 15px;
                        background-color: white;
                        border-radius: 10px;
                        border: 2px solid #e0e0e0;
                        min-height: 80px;
                    }
                """)

                # Анимируем кнопку добавления
                self.pushButton_Add.setEnabled(True)
                self.pushButton_Add.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 11pt;
                    }
                    QPushButton:hover {
                        background-color: #219653;
                    }
                """)

                self.has_unsaved_changes = True

                # Обновляем ToolTip
                detailed_tooltip = f"Файл готов к добавлению в конспекты"
                self.label_2.setToolTip(detailed_tooltip)

                # Предварительная обработка файла
                self.prepare_file_preview(file_path, file_ext)

        except FileNotFoundError as e:
            QMessageBox.warning(self, "Файл не найден", str(e))
        except FileImportError as e:
            QMessageBox.warning(self, "Ошибка выбора файла", str(e))
        except PermissionError as e:
            QMessageBox.warning(self, "Ошибка доступа", f"Нет прав доступа к файлу: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Неизвестная ошибка", f"Ошибка при выборе файла: {str(e)}")

    def get_file_icon(self, file_ext):
        """Получение иконки для типа файла"""
        file_ext = file_ext.lower()

        if file_ext in ['.txt', '.md', '.rtf']:
            return "📄"
        elif file_ext in ['.doc', '.docx', '.odt']:
            return "📝"
        elif file_ext == '.pdf':
            return "📋"
        elif file_ext in ['.xls', '.xlsx', '.ods', '.csv']:
            return "📊"
        elif file_ext in ['.ppt', '.pptx', '.odp']:
            return "📽️"
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']:
            return "🖼️"
        elif file_ext in ['.html', '.htm']:
            return "🌐"
        elif file_ext in ['.py', '.java', '.cpp', '.c', '.js', '.css', '.sql', '.php', '.rb']:
            return "💻"
        elif file_ext in ['.json', '.xml', '.yaml', '.yml']:
            return "📊"
        else:
            return "📁"

    def determine_file_type(self, file_ext):
        """Определение типа файла по расширению"""
        file_ext = file_ext.lower()

        if file_ext in ['.txt', '.md', '.rtf']:
            return "Текстовый документ"
        elif file_ext in ['.doc', '.docx', '.odt']:
            return "Документ Word"
        elif file_ext == '.pdf':
            return "PDF документ"
        elif file_ext in ['.xls', '.xlsx', '.ods', '.csv']:
            return "Электронная таблица"
        elif file_ext in ['.ppt', '.pptx', '.odp']:
            return "Презентация"
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']:
            return "Изображение"
        elif file_ext in ['.html', '.htm']:
            return "Веб-страница"
        elif file_ext in ['.py', '.java', '.cpp', '.c', '.js', '.css', '.sql', '.php', '.rb']:
            return "Исходный код"
        elif file_ext in ['.json', '.xml', '.yaml', '.yml']:
            return "Файл данных"
        else:
            return "Неизвестный тип"

    def prepare_file_preview(self, file_path, file_ext):
        """Подготовка предварительного просмотра файла"""
        try:
            file_ext = file_ext.lower()

            # Для текстовых файлов
            if file_ext in ['.txt', '.md', '.rtf', '.py', '.java', '.cpp', '.c', '.js', '.html', '.css', '.sql', '.php',
                            '.rb']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        preview = f.read(500)
                        if len(preview) == 500:
                            preview += "..."
                        self.file_content = f"📄 Текстовое содержимое:\n\n{preview}"
                except UnicodeDecodeError:
                    self.file_content = f"📦 Файл: {os.path.basename(file_path)}\n🔤 Требуется специальная обработка"

            # Для документов
            elif file_ext in ['.doc', '.docx', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp']:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                self.file_content = (
                    f"📋 Документ: {file_name}\n"
                    f"🔤 Тип: {self.file_type}\n"
                    f"📊 Размер: {file_size / 1024:.1f} КБ\n"
                    f"✨ Содержимое будет извлечено нейросетью"
                )

            # Для изображений
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']:
                file_name = os.path.basename(file_path)
                self.file_content = (
                    f"🖼️ Изображение: {file_name}\n"
                    f"🎨 Нейросеть попытается распознать текст на изображении"
                )

            # Для CSV файлов
            elif file_ext == '.csv':
                try:
                    import csv
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        headers = next(reader, [])

                    self.file_content = (
                        f"📊 CSV файл: {os.path.basename(file_path)}\n"
                        f"📋 Столбцы: {', '.join(headers[:5])}{'...' if len(headers) > 5 else ''}"
                    )
                except:
                    self.file_content = f"📊 CSV файл: {os.path.basename(file_path)}"

            else:
                file_name = os.path.basename(file_path)
                self.file_content = f"📁 Файл: {file_name}\n🔤 Тип: {self.file_type}"

        except Exception as e:
            self.file_content = f"📁 Файл: {os.path.basename(file_path)}"

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
                    "Предупреждение безопасности",
                    f"Выбранный файл имеет расширение {file_ext}, которое может быть опасным.\n"
                    f"Вы уверены, что хотите продолжить?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Подготовка финального содержимого
            final_content = self.prepare_final_content()
            self.file_content = final_content

            self.has_unsaved_changes = False
            self.accept()

        except FileNotFoundError as e:
            QMessageBox.warning(self, "Файл не найден", str(e))
        except FileImportError as e:
            QMessageBox.warning(self, "Ошибка импорта", str(e))
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось добавить файл:\n{str(e)}"
            )

    def prepare_final_content(self):
        """Подготовка финального содержимого файла для сохранения"""
        file_ext = os.path.splitext(self.file_path)[1].lower()
        file_name = os.path.basename(self.file_path)

        # Для текстовых файлов
        if file_ext in ['.txt', '.md', '.rtf', '.py', '.java', '.cpp', '.c', '.js', '.html', '.css', '.sql', '.php',
                        '.rb']:
            try:
                encodings = ['utf-8', 'cp1251', 'iso-8859-1', 'windows-1252']
                for encoding in encodings:
                    try:
                        with open(self.file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                            if len(content) > 100000:
                                content = content[:100000] + "\n...[файл обрезан]"
                            return f"📄 Файл: {file_name}\n🔤 Тип: {self.file_type}\n\n{content}"
                    except UnicodeDecodeError:
                        continue

                return f"📦 Файл: {file_name}\n🔤 Тип: {self.file_type}\n✨ Требуется специальная обработка"

            except Exception as e:
                return f"📁 Файл: {file_name}\n🔤 Тип: {self.file_type}\n❌ Ошибка чтения"

        # Для других типов файлов
        else:
            file_size = os.path.getsize(self.file_path)
            return (
                f"📁 Файл: {file_name}\n"
                f"🔤 Тип: {self.file_type}\n"
                f"📊 Размер: {file_size} байт\n"
                f"📍 Путь: {self.file_path}\n\n"
                f"✨ Нейросеть будет работать с этим файлом как с конспектом.\n"
                f"💡 Для лучших результатов используйте текстовые файлы."
            )

    def _simulate_file_import(self):
        """Симуляция процесса импорта файла"""
        try:
            with open(self.file_path, 'rb') as f:
                f.read(10)
        except IOError as e:
            raise IOError(f"Файл недоступен для чтения: {str(e)}")

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
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отмене: {str(e)}")
            self.reject()

    def keyPressEvent(self, event):
        """Обработка нажатия клавиши Escape"""
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
                'У вас есть несохраненные изменения.\nЗакрыть форму без сохранения?',
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
                'У вас есть несохраненные изменения.\nЗакрыть форму без сохранения?',
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
