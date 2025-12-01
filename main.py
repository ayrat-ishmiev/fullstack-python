# [file name]: main.py
# [file content begin]
import sys
import os
import json
import re
import csv
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QDialog,
                             QListWidget, QListWidgetItem, QMessageBox, QFileDialog,
                             QMenu, QTableWidgetItem, QVBoxLayout, QLabel,
                             QTextBrowser, QPushButton, QFrame, QHeaderView)
from PyQt6.QtCore import QDate, Qt, QRect
from PyQt6 import QtCore, QtGui
from openai import OpenAI

# Импорт UI файлов
from add_subject_dialog_ui import Ui_Dialog as AddSubjectDialog
from import_note_dialog_ui import Ui_Dialog as ImportNoteDialog
from main_screen_ui import Ui_Form as MainScreen
from notes_list_ui import Ui_Form as NotesList
from ask_ai_dialog_ui import Ui_Form as AskAIDialog
from all_notes_table_ui import Ui_Form as AllNotesTable

# Импорт обновленных классов
from add_subject_dialog import AddSubjectDialog as AddSubjectDialogClass
from import_note_dialog import ImportNoteDialog as ImportNoteDialogClass
from exceptions import SubjectValidationError, FileImportError

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)


class DataManager:
    """Класс для управления данными приложения"""

    def __init__(self):
        self.data_file = "app_data.json"
        self.csv_file = "notes_export.csv"
        self.data = self.load_data()

    def load_data(self):
        """Загрузка данных из файла"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"subjects": [], "notes": {}}
        return {"subjects": [], "notes": {}}

    def save_data(self):
        """Сохранение данных в файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def add_subject(self, subject_name):
        """Добавление нового предмета"""
        if subject_name and subject_name not in self.data["subjects"]:
            self.data["subjects"].append(subject_name)
            self.data["notes"][subject_name] = []
            return self.save_data()
        return False

    def get_subjects(self):
        """Получение списка предметов"""
        return self.data["subjects"]

    def add_note(self, subject_name, note_name, content=""):
        """Добавление конспекта к предмету"""
        if subject_name in self.data["notes"]:
            note_data = {
                "name": note_name,
                "content": content,
                "created_date": QDate.currentDate().toString("dd.MM.yyyy")
            }
            self.data["notes"][subject_name].append(note_data)
            return self.save_data()
        return False

    def get_notes(self, subject_name):
        """Получение конспектов предмета"""
        return self.data["notes"].get(subject_name, [])

    def get_note_data(self, subject_name, note_name):
        """Получение данных конкретного конспекта"""
        notes = self.data["notes"].get(subject_name, [])
        for note in notes:
            if note["name"] == note_name:
                return note
        return None

    def delete_note(self, subject_name, note_name):
        """Удаление конспекта"""
        if subject_name in self.data["notes"]:
            self.data["notes"][subject_name] = [
                note for note in self.data["notes"][subject_name]
                if note["name"] != note_name
            ]
            return self.save_data()
        return False

    def delete_subject(self, subject_name):
        """Удаление предмета"""
        if subject_name in self.data["subjects"]:
            self.data["subjects"].remove(subject_name)
            if subject_name in self.data["notes"]:
                del self.data["notes"][subject_name]
            return self.save_data()
        return False

    def get_all_notes(self):
        """Получение всех конспектов из всех предметов"""
        all_notes = []
        for subject in self.data["subjects"]:
            for note in self.data["notes"].get(subject, []):
                all_notes.append({
                    "subject": subject,
                    "name": note["name"],
                    "content": note["content"],
                    "created_date": note.get("created_date", "Не указана")
                })
        return all_notes

    def export_to_csv(self, filename=None):
        """Экспорт всех конспектов в CSV файл с правильной кодировкой"""
        if filename is None:
            filename = self.csv_file

        all_notes = self.get_all_notes()

        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:  # Исправлена кодировка
                fieldnames = ['subject', 'name', 'content', 'created_date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')  # Используем разделитель ;

                writer.writeheader()
                for note in all_notes:
                    # Очищаем данные от лишних пробелов
                    cleaned_note = {
                        'subject': note['subject'].strip(),
                        'name': note['name'].strip(),
                        'content': note['content'].strip()[:500] + '...' if len(note['content']) > 500 else note[
                            'content'].strip(),  # Обрезаем длинный контент
                        'created_date': note['created_date'].strip()
                    }
                    writer.writerow(cleaned_note)

            return True, f"Данные успешно экспортированы в {filename}"
        except Exception as e:
            return False, f"Ошибка при экспорте в CSV: {str(e)}"

    def import_from_csv(self, filename):
        """Импорт конспектов из CSV файла с правильной кодировкой"""
        try:
            with open(filename, 'r', encoding='utf-8-sig') as csvfile:  # Исправлена кодировка
                reader = csv.DictReader(csvfile, delimiter=';')  # Используем разделитель ;
                imported_count = 0
                skipped_count = 0

                for row_num, row in enumerate(reader, 1):
                    try:
                        subject = row.get('subject', '').strip()
                        note_name = row.get('name', '').strip()
                        content = row.get('content', '').strip()
                        created_date = row.get('created_date', QDate.currentDate().toString("dd.MM.yyyy")).strip()

                        # Проверяем обязательные поля
                        if not subject or not note_name:
                            skipped_count += 1
                            continue

                        # Добавляем предмет, если его нет
                        if subject not in self.data["subjects"]:
                            self.data["subjects"].append(subject)
                            self.data["notes"][subject] = []

                        # Проверяем, нет ли уже такого конспекта
                        note_exists = any(note["name"] == note_name for note in self.data["notes"][subject])

                        if not note_exists:
                            note_data = {
                                "name": note_name,
                                "content": content,
                                "created_date": created_date
                            }
                            self.data["notes"][subject].append(note_data)
                            imported_count += 1
                        else:
                            skipped_count += 1

                    except Exception as e:
                        print(f"Ошибка в строке {row_num}: {e}")
                        skipped_count += 1
                        continue

                if self.save_data():
                    message = f"Успешно импортировано {imported_count} конспектов"
                    if skipped_count > 0:
                        message += f", пропущено {skipped_count} (дубликаты или ошибки)"
                    return True, message
                else:
                    return False, "Ошибка при сохранении данных после импорта"

        except Exception as e:
            return False, f"Ошибка при импорте из CSV: {str(e)}"


class AllNotesTableWindow(QWidget):
    def __init__(self, data_manager, main_window, parent=None):
        super().__init__(parent)
        self.ui = AllNotesTable()
        self.ui.setupUi(self)

        self.data_manager = data_manager
        self.main_window = main_window

        # Добавляем кнопки для экспорта/импорта
        self.add_export_import_buttons()

        # Загрузка данных в таблицу
        self.load_table_data()

        # Подключение сигналов
        self.ui.tableWidget.cellDoubleClicked.connect(self.open_note_in_subject_window)

    def add_export_import_buttons(self):
        """Добавление кнопок экспорта и импорта"""
        button_layout = QVBoxLayout()

        # Кнопка экспорта
        self.export_button = QPushButton("📤 Экспорт в CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.export_button)

        # Кнопка импорта
        self.import_button = QPushButton("📥 Импорт из CSV")
        self.import_button.clicked.connect(self.import_from_csv)
        button_layout.addWidget(self.import_button)

        # Добавляем layout с кнопками к основному layout
        self.ui.verticalLayout.addLayout(button_layout)

    def load_table_data(self):
        """Загрузка всех конспектов в таблицу"""
        all_notes = self.data_manager.get_all_notes()
        self.ui.tableWidget.setRowCount(len(all_notes))

        for row, note in enumerate(all_notes):
            # Предмет
            subject_item = QTableWidgetItem(note["subject"])
            self.ui.tableWidget.setItem(row, 0, subject_item)

            # Название конспекта
            name_item = QTableWidgetItem(note["name"])
            self.ui.tableWidget.setItem(row, 1, name_item)

            # Дата добавления
            date_item = QTableWidgetItem(note["created_date"])
            self.ui.tableWidget.setItem(row, 2, date_item)

        # Настройка таблицы
        self.ui.tableWidget.setSortingEnabled(True)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

    def export_to_csv(self):
        """Экспорт данных в CSV файл"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт в CSV",
            "notes_export.csv",
            "CSV Files (*.csv)"
        )

        if file_path:
            success, message = self.data_manager.export_to_csv(file_path)
            if success:
                QMessageBox.information(self, "Экспорт завершен", message)
            else:
                QMessageBox.warning(self, "Ошибка экспорта", message)

    def import_from_csv(self):
        """Импорт данных из CSV файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт из CSV",
            "",
            "CSV Files (*.csv)"
        )

        if file_path:
            reply = QMessageBox.question(
                self,
                "Подтверждение импорта",
                "Вы уверены, что хотите импортировать данные из CSV файла?\nСуществующие конспекты не будут удалены.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.data_manager.import_from_csv(file_path)
                if success:
                    QMessageBox.information(self, "Импорт завершен", message)
                    # Обновляем таблицу после импорта
                    self.load_table_data()
                else:
                    QMessageBox.warning(self, "Ошибка импорта", message)

    def open_note_in_subject_window(self, row, column):
        """Открытие конспекта в окне предмета при двойном клике"""
        subject = self.ui.tableWidget.item(row, 0).text()
        note_name = self.ui.tableWidget.item(row, 1).text()

        # Закрываем окно таблицы
        self.close()

        # Открываем окно предмета с выбранным конспектом
        self.main_window.open_subject_with_note(subject, note_name)


class AddSubjectDialogWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = AddSubjectDialogClass(parent)

    def exec(self):
        """Выполнение диалога с обработкой результата"""
        result = self.dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return QDialog.DialogCode.Accepted
        return QDialog.DialogCode.Rejected

    def get_subject_name(self):
        """Получение названия предмета"""
        return self.dialog.lineEdit.text().strip()


class ImportNoteDialogWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = ImportNoteDialogClass(parent)
        self.selected_file = ""
        self.note_content = ""

    def exec(self):
        """Выполнение диалога с обработкой результата"""
        result = self.dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            # Получаем данные из диалога
            self.selected_file = getattr(self.dialog, 'file_path', '')
            if self.selected_file:
                # Чтение содержимого файла (для текстовых файлов)
                if self.selected_file.lower().endswith('.txt'):
                    try:
                        with open(self.selected_file, 'r', encoding='utf-8') as f:
                            self.note_content = f.read()
                    except:
                        file_name = os.path.basename(self.selected_file)
                        self.note_content = f"Содержимое файла: {file_name}"
                else:
                    file_name = os.path.basename(self.selected_file)
                    self.note_content = f"Файл: {file_name}"
            return QDialog.DialogCode.Accepted
        return QDialog.DialogCode.Rejected

    def get_file_path(self):
        return self.selected_file

    def get_note_name(self):
        """Получение имени конспекта из имени файла"""
        if self.selected_file:
            return os.path.splitext(os.path.basename(self.selected_file))[0]
        return ""

    def get_note_content(self):
        return self.note_content


class AskAIDialogWindow(QDialog):
    def __init__(self, note_name, note_content, parent=None):
        super().__init__(parent)
        self.ui = AskAIDialog()
        self.ui.setupUi(self)

        self.note_name = note_name
        self.note_content = note_content

        self.setWindowTitle(f"Вопрос по конспекту: {note_name}")
        self.ui.pushButton.clicked.connect(self.ask_question)
        self.ui.lineEdit.setPlaceholderText("Введите ваш вопрос...")

        self.display_note_info()

    def display_note_info(self):
        """Отображение информации о конспекте"""
        info_text = f"<h3>Конспект: {self.note_name}</h3>"
        info_text += f"<p>Содержимое конспекта доступно для вопросов.</p>"
        info_text += "<hr>"
        self.ui.textBrowser.setHtml(info_text)

    def ask_question(self):
        """Обработка вопроса к нейросети"""
        question = self.ui.lineEdit.text().strip()

        if not question:
            QMessageBox.warning(self, "Ошибка", "Введите вопрос!")
            return

        # Сразу обновляем UI до начала запроса
        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton.setText("⏳")
        self.display_waiting_message(question)

        # Даем интерфейсу обновиться перед началом долгой операции
        QApplication.processEvents()

        # Теперь выполняем запрос (UI уже обновлен)
        self.process_question(question)

    def display_waiting_message(self, question):
        """Отображение сообщения об ожидании ответа"""
        waiting_text = f"""
        <div style="margin-bottom: 15px;">
            <h4 style="color: #2c3e50;">Ваш вопрос:</h4>
            <p style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid #3498db;">
                {question}
            </p>
        </div>
        <div>
            <h4 style="color: #f39c12;">Статус:</h4>
            <p style="background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 4px solid #ffc107;">
                <strong>Ожидайте ответа нейросети...</strong><br>
                <em>Идет обработка запроса</em>
            </p>
        </div>
        """
        self.ui.textBrowser.setHtml(waiting_text)

    def process_question(self, question):
        """Выполнение запроса к нейросети"""
        try:
            response = self.generate_response(question)
            self.display_response(question, response)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
        finally:
            # Восстанавливаем кнопку
            self.ui.pushButton.setEnabled(True)
            self.ui.pushButton.setText("✨")

    def generate_response(self, question):
        """Генерация ответа с обработкой ошибок"""
        try:
            # Проверяем наличие клиента
            if 'client' not in globals():
                return "Ошибка: API клиент не инициализирован"

            # Формируем промпт
            prompt = f"""Вот конспект "{self.note_name}":
{self.note_content}

Ответь на вопрос по этому конспекту:
{question}"""

            response = client.chat.completions.create(
                model="google/gemma-3-27b-it:free",
                messages=[{"role": "user", "content": prompt}],
                timeout=30  # Таймаут на случай долгого ответа
            )

            # Правильное обращение к ответу
            return response.choices[0].message.content

        except Exception as e:
            return f"Ошибка при обращении к нейросети: {str(e)}"

    def markdown_to_html(self, markdown_text):
        """Конвертация Markdown в HTML"""
        try:
            # Базовые преобразования Markdown в HTML
            html_text = markdown_text

            # Заголовки
            html_text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html_text, flags=re.MULTILINE)
            html_text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html_text, flags=re.MULTILINE)
            html_text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html_text, flags=re.MULTILINE)

            # Жирный текст
            html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
            html_text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html_text)

            # Курсив
            html_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_text)
            html_text = re.sub(r'_(.*?)_', r'<em>\1</em>', html_text)

            # Списки
            html_text = re.sub(r'^\s*[-*+]\s+(.*?)$', r'<li>\1</li>', html_text, flags=re.MULTILINE)

            # Обрамляем списки в ul теги
            lines = html_text.split('\n')
            in_list = False
            formatted_lines = []

            for line in lines:
                if line.startswith('<li>'):
                    if not in_list:
                        formatted_lines.append('<ul>')
                        in_list = True
                    formatted_lines.append(line)
                else:
                    if in_list:
                        formatted_lines.append('</ul>')
                        in_list = False
                    formatted_lines.append(line)

            if in_list:
                formatted_lines.append('</ul>')

            html_text = '\n'.join(formatted_lines)

            # Код (inline)
            html_text = re.sub(r'`([^`]+)`', r'<code>\1</code>', html_text)

            # Блоки кода
            html_text = re.sub(r'```(\w+)?\n(.*?)\n```', r'<pre><code class="\1">\2</code></pre>', html_text,
                               flags=re.DOTALL)

            # Ссылки
            html_text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" style="color: #3498db;">\1</a>', html_text)

            # Цитаты
            html_text = re.sub(r'^>\s*(.*?)$',
                               r'<blockquote style="border-left: 3px solid #3498db; padding-left: 10px; margin-left: 0; color: #666;">\1</blockquote>',
                               html_text, flags=re.MULTILINE)

            # Разделители
            html_text = re.sub(r'^\s*---\s*$',
                               r'<hr style="border: none; border-top: 1px solid #ddd; margin: 10px 0;">', html_text,
                               flags=re.MULTILINE)

            # Переносы строк
            html_text = html_text.replace('\n', '<br>')

            return html_text

        except Exception as e:
            # В случае ошибки возвращаем оригинальный текст
            return markdown_text

    def display_response(self, question, response):
        """Отображение вопроса и ответа с поддержкой Markdown"""
        # Конвертируем Markdown в HTML
        formatted_response = self.markdown_to_html(response)

        formatted_text = f"""
        <div style="margin-bottom: 15px;">
            <h4 style="color: #2c3e50;">Ваш вопрос:</h4>
            <p style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid #3498db;">
                {question}
            </p>
        </div>
        <div>
            <h4 style="color: #27ae60;">Ответ нейросети:</h4>
            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; border-left: 4px solid #2ecc71; line-height: 1.5;">
                {formatted_response}
            </div>
        </div>
        <hr>
        """
        self.ui.textBrowser.setHtml(formatted_text)


class NotesListWindow(QWidget):
    def __init__(self, subject_name, data_manager, parent=None):
        super().__init__(parent)
        self.ui = NotesList()
        self.ui.setupUi(self)

        self.subject_name = subject_name
        self.data_manager = data_manager
        self.current_note = None

        # Установка заголовка окна
        self.setWindowTitle(f"Конспекты - {subject_name}")

        # Установка начального состояния
        self.reset_view()

        # Загрузка конспектов для выбранного предмета
        self.load_notes()

        # Подключение сигналов
        self.ui.listWidget.itemClicked.connect(self.on_note_selected)
        self.ui.pushButton.clicked.connect(self.add_note)
        self.ui.pushButton_2.clicked.connect(self.edit_note)
        self.ui.pushButton_3.clicked.connect(self.save_note)
        self.ui.pushButton_4.clicked.connect(self.delete_note)
        self.ui.pushButton_5.clicked.connect(self.ask_ai)

    def reset_view(self):
        """Сброс вида к начальному состоянию (когда конспект не выбран)"""
        self.ui.label_3.setText("")
        self.ui.label_2.setText("")
        self.ui.textBrowser.setHtml("""
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
        <html><head><meta name="qrichtext" content="1" /><style type="text/css">
        p, li { white-space: pre-wrap; }
        </style></head><body style=" font-family:'MS Shell Dlg 2'; font-size:11pt; font-weight:400; font-style:normal;">
        <p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
        <p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
        <span style=" font-size:12pt; color:#666666;">Выберите конспект из списка слева</span></p>
        <p align="center" style=" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
        <span style=" font-size:10pt; color:#999999;">для просмотра его содержимого</span></p></body></html>
        """)

        # Деактивируем кнопки управления
        self.ui.pushButton_2.setEnabled(False)
        self.ui.pushButton_3.setEnabled(False)
        self.ui.pushButton_4.setEnabled(False)
        self.ui.pushButton_5.setEnabled(False)

    def load_notes(self):
        """Загрузка конспектов из базы данных"""
        self.ui.listWidget.clear()
        notes = self.data_manager.get_notes(self.subject_name)

        for note in notes:
            item = QListWidgetItem(note["name"])
            self.ui.listWidget.addItem(item)

    def on_note_selected(self, item):
        """Обработка выбора конспекта из списка"""
        note_name = item.text()
        self.current_note = note_name
        self.ui.label_3.setText(note_name)

        # Получаем данные конспекта
        note_data = self.data_manager.get_note_data(self.subject_name, note_name)
        if note_data:
            # Отображаем дату добавления конспекта
            created_date = note_data.get("created_date", "Дата не указана")
            self.ui.label_2.setText(created_date)

            # Загрузка содержимого конспекта
            self.ui.textBrowser.setHtml(self.format_note_content(note_data["content"]))

        # Активируем кнопки управления
        self.ui.pushButton_2.setEnabled(True)
        self.ui.pushButton_3.setEnabled(True)
        self.ui.pushButton_4.setEnabled(True)
        self.ui.pushButton_5.setEnabled(True)

    def format_note_content(self, content):
        """Форматирование содержимого конспекта для отображения"""
        if content.startswith("Файл:") or content.startswith("Содержимое файла:"):
            return f"""
            <html>
            <body>
            <p style="font-size: 14px; color: #666;">
            {content}
            </p>
            </body>
            </html>
            """
        else:
            return content

    def add_note(self):
        """Добавление нового конспекта"""
        dialog = ImportNoteDialogWindow(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            file_path = dialog.get_file_path()
            if file_path:
                note_name = dialog.get_note_name()
                note_content = dialog.get_note_content()

                if self.data_manager.add_note(self.subject_name, note_name, note_content):
                    self.load_notes()
                    QMessageBox.information(self, "Успех", f"Конспект '{note_name}' успешно добавлен!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось добавить конспект!")

    def edit_note(self):
        """Редактирование конспекта"""
        if not self.current_note:
            QMessageBox.warning(self, "Ошибка", "Выберите конспект для редактирования!")
            return

        QMessageBox.information(self, "Редактирование",
                                f"Редактирование конспекта: {self.current_note}\n\nЭта функция будет реализована в будущем!")

    def save_note(self):
        """Сохранение конспекта"""
        if not self.current_note:
            QMessageBox.warning(self, "Ошибка", "Выберите конспект для сохранения!")
            return

        QMessageBox.information(self, "Сохранение", "Все изменения автоматически сохраняются!")

    def delete_note(self):
        """Удаление конспекта"""
        if not self.current_note:
            QMessageBox.warning(self, "Ошибка", "Выберите конспект для удаления!")
            return

        reply = QMessageBox.question(self, "Подтверждение",
                                     f"Вы уверены, что хотите удалить конспект '{self.current_note}'?")
        if reply == QMessageBox.StandardButton.Yes:
            if self.data_manager.delete_note(self.subject_name, self.current_note):
                self.load_notes()
                self.reset_view()
                self.current_note = None
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить конспект!")

    def ask_ai(self):
        """Запрос к нейросети"""
        if not self.current_note:
            QMessageBox.warning(self, "Ошибка", "Выберите конспект для вопроса к нейросети!")
            return

        # Получаем данные текущего конспекта
        note_data = self.data_manager.get_note_data(self.subject_name, self.current_note)
        if note_data:
            # Создаем и показываем диалоговое окно для вопроса к нейросети
            dialog = AskAIDialogWindow(self.current_note, note_data["content"], self)
            dialog.exec()

    def select_note_by_name(self, note_name):
        """Выбор конспекта по имени (для открытия из таблицы)"""
        # Ищем конспект в списке
        items = self.ui.listWidget.findItems(note_name, Qt.MatchFlag.MatchExactly)
        if items:
            # Выбираем найденный конспект
            item = items[0]
            self.ui.listWidget.setCurrentItem(item)
            self.on_note_selected(item)
            return True
        return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = MainScreen()
        self.ui.setupUi(self)

        self.data_manager = DataManager()
        self.notes_windows = {}  # Словарь для хранения открытых окон предметов

        # Установка текущей даты
        current_date = QDate.currentDate()
        day_of_week = self.get_russian_day_of_week(current_date.dayOfWeek())
        formatted_date = current_date.toString("dd MMMM yyyy")
        self.ui.label_3.setText(f"Сегодня {day_of_week}, {formatted_date}")

        # Загрузка предметов
        self.load_subjects()

        # Подключение сигналов
        self.ui.pushButton.clicked.connect(self.add_note)
        self.ui.pushButton_2.clicked.connect(self.add_subject)
        self.ui.pushButton_3.clicked.connect(self.show_settings)
        self.ui.pushButton_4.clicked.connect(self.search)
        self.ui.listWidget.itemDoubleClicked.connect(self.open_subject_notes)
        self.ui.listWidget.itemClicked.connect(self.on_subject_selected)

        # Включаем контекстное меню для списка предметов
        self.ui.listWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.listWidget.customContextMenuRequested.connect(self.show_context_menu)

        # Изначально кнопка добавления конспекта неактивна
        self.ui.pushButton.setEnabled(False)

        # Добавляем кнопку для просмотра всех конспектов
        self.add_all_notes_button()

    def add_all_notes_button(self):
        """Добавление кнопки для просмотра всех конспектов"""
        self.all_notes_button = QPushButton("📋 Все конспекты", self)
        self.all_notes_button.setGeometry(QRect(200, 390, 141, 23))
        self.all_notes_button.clicked.connect(self.show_all_notes)

    def show_all_notes(self):
        """Показ таблицы со всеми конспектами"""
        self.all_notes_window = AllNotesTableWindow(self.data_manager, self)
        self.all_notes_window.setWindowTitle("Все конспекты - Таблица")
        self.all_notes_window.resize(700, 500)
        self.all_notes_window.show()

    def open_subject_with_note(self, subject_name, note_name):
        """Открытие окна предмета с выбранным конспектом"""
        # Открываем окно предмета как отдельное окно
        self.open_subject_notes_by_name(subject_name)

        # Затем выбираем нужный конспект в открытом окне
        if subject_name in self.notes_windows:
            notes_window = self.notes_windows[subject_name]
            notes_window.select_note_by_name(note_name)
            # Активируем окно, чтобы оно было поверх других
            notes_window.raise_()
            notes_window.activateWindow()

    def open_subject_notes_by_name(self, subject_name):
        """Открытие окна предмета по имени как отдельного окна"""
        # Проверяем, не открыто ли уже окно для этого предмета
        if subject_name in self.notes_windows:
            # Если окно уже открыто, активируем его
            notes_window = self.notes_windows[subject_name]
            # Проверяем, не было ли окно уничтожено
            if notes_window and hasattr(notes_window, 'isVisible') and notes_window.isVisible():
                notes_window.raise_()
                notes_window.activateWindow()
                return
            else:
                # Если окно было закрыто, удаляем его из словаря
                del self.notes_windows[subject_name]

        # Создаем новое окно как отдельное окно
        new_notes_window = NotesListWindow(subject_name, self.data_manager)
        new_notes_window.setWindowTitle(f"Конспекты - {subject_name}")

        # Устанавливаем флаги окна для отдельного отображения
        new_notes_window.setWindowFlags(Qt.WindowType.Window)

        self.notes_windows[subject_name] = new_notes_window

        # Подключаем сигнал закрытия окна для удаления из словаря
        new_notes_window.destroyed.connect(
            lambda: self.on_notes_window_closed(subject_name)
        )

        new_notes_window.show()

    def on_notes_window_closed(self, subject_name):
        """Обработка закрытия окна предмета"""
        if subject_name in self.notes_windows:
            # Устанавливаем значение в None вместо удаления, чтобы избежать KeyError
            self.notes_windows[subject_name] = None

    def get_russian_day_of_week(self, day_number):
        """Получение русского названия дня недели"""
        days = {
            1: "понедельник",
            2: "вторник",
            3: "среда",
            4: "четверг",
            5: "пятница",
            6: "суббота",
            7: "воскресенье"
        }
        return days.get(day_number, "")

    def load_subjects(self):
        """Загрузка предметов из базы данных"""
        self.ui.listWidget.clear()
        subjects = self.data_manager.get_subjects()

        for subject in subjects:
            item = QListWidgetItem(subject)
            self.ui.listWidget.addItem(item)

    def show_context_menu(self, position):
        """Показ контекстного меню для удаления предмета"""
        item = self.ui.listWidget.itemAt(position)
        if item:
            menu = QMenu(self)
            delete_action = menu.addAction("Удалить предмет")

            action = menu.exec(self.ui.listWidget.mapToGlobal(position))

            if action == delete_action:
                self.delete_subject(item)

    def delete_subject(self, item):
        """Удаление выбранного предмета"""
        subject_name = item.text()

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить предмет '{subject_name}'?\n\nВсе конспекты этого предмета также будут удалены!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.data_manager.delete_subject(subject_name):
                self.load_subjects()
                # Деактивируем кнопку добавления конспекта, так как предмет удален
                self.ui.pushButton.setEnabled(False)

                # Закрываем окно предмета, если оно было открыто
                if subject_name in self.notes_windows and self.notes_windows[subject_name] is not None:
                    notes_window = self.notes_windows[subject_name]
                    if hasattr(notes_window, 'close'):
                        notes_window.close()
                    # Удаляем из словаря
                    del self.notes_windows[subject_name]

                QMessageBox.information(self, "Успех", f"Предмет '{subject_name}' успешно удален!")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить предмет!")

    def on_subject_selected(self, item):
        """Активация кнопки добавления конспекта при выборе предмета"""
        self.ui.pushButton.setEnabled(True)

    def add_note(self):
        """Добавление нового конспекта"""
        current_item = self.ui.listWidget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите предмет!")
            return

        subject_name = current_item.text()
        dialog = ImportNoteDialogWindow(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            file_path = dialog.get_file_path()
            if file_path:
                note_name = dialog.get_note_name()
                note_content = dialog.get_note_content()

                if self.data_manager.add_note(subject_name, note_name, note_content):
                    QMessageBox.information(self, "Успех",
                                            f"Конспект '{note_name}' успешно добавлен к предмету '{subject_name}'!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось добавить конспект!")

    def add_subject(self):
        """Добавление нового предмета"""
        dialog = AddSubjectDialogWindow(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            subject_name = dialog.get_subject_name()
            if subject_name:
                if self.data_manager.add_subject(subject_name):
                    self.load_subjects()
                    QMessageBox.information(self, "Успех", f"Предмет '{subject_name}' успешно добавлен!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось добавить предмет или предмет уже существует!")

    def show_settings(self):
        """Показ настроек"""
        QMessageBox.information(self, "Настройки", "Раздел настроек будет реализован позже!")

    def search(self):
        """Поиск конспектов"""
        search_text = self.ui.lineEdit.text().strip()
        if search_text:
            QMessageBox.information(self, "Поиск",
                                    f"Поиск по запросу: '{search_text}'\n\nФункция поиска будет полностью реализована в будущем!")
        else:
            QMessageBox.warning(self, "Поиск", "Введите текст для поиска!")

    def open_subject_notes(self, item):
        """Открытие списка конспектов для выбранного предмета как отдельного окна"""
        subject_name = item.text()
        self.open_subject_notes_by_name(subject_name)


def main():
    app = QApplication(sys.argv)

    # Создание и отображение главного окна
    window = MainWindow()
    window.setWindowTitle("Умный агрегатор конспектов")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
# [file content end]