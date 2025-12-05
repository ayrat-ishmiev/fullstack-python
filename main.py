import sys
import os
import json
import re
import csv
import base64
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QDialog,
                             QListWidget, QListWidgetItem, QMessageBox, QFileDialog,
                             QMenu, QTableWidgetItem, QVBoxLayout, QLabel,
                             QTextBrowser, QPushButton, QFrame, QHeaderView,
                             QProgressDialog, QProgressBar, QLineEdit)
from PyQt6.QtCore import QDate, Qt, QRect, QTimer
from PyQt6 import QtCore, QtGui
from openai import OpenAI
from main_screen_ui import Ui_Form as MainScreen
# Импорт UI файлов (как в исходном проекте)
# ПРИМЕЧАНИЕ: Предполагается, что эти файлы существуют в проекте.
from add_subject_dialog_ui import Ui_Dialog as AddSubjectDialog
from import_note_dialog_ui import Ui_Dialog as ImportNoteDialog
from notes_list_ui import Ui_Form as NotesList
from ask_ai_dialog_ui import Ui_Form as AskAIDialog
from all_notes_table_ui import Ui_Form as AllNotesTable
from search_results_ui import Ui_SearchResultsDialog as SearchResultsDialog

# Импорт обновленных классов логики
from add_subject_dialog import AddSubjectDialog as AddSubjectDialogClass
from import_note_dialog import ImportNoteDialog as ImportNoteDialogClass
from exceptions import SubjectValidationError, FileImportError

# Ключ OpenRouter
# ПРИМЕЧАНИЕ: Файл openrouter_key.py должен содержать переменную OPENROUTER_KEY

# Импорт стилей
# ПРИМЕЧАНИЕ: Файл styles.py должен содержать переменную STYLESHEET
import styles

# Предполагается, что openrouter_key.py предоставит ключ
# try:
#     import openrouter_key
#
#     OPENROUTER_KEY = openrouter_key.OPENROUTER_KEY
# except ImportError:
#     OPENROUTER_KEY = "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"  # Замените на ваш фактический ключ или убедитесь, что файл openrouter_key.py доступен
from openrouter_key import OPENROUTER_KEY

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)


# =============================================================================
# КЛАССЫ ЛОГИКИ
# =============================================================================
def resource_path(relative_path):
    """
    Получает абсолютный путь к ресурсу, работает и в режиме разработки,
    и после упаковки PyInstaller
    """
    try:
        # Путь к временной папке PyInstaller (если запущен .exe)
        base_path = sys._MEIPASS
    except Exception:
        # Путь в режиме разработки (ваша папка проекта)
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class SearchResultsWindow(QDialog):
    def __init__(self, search_query, search_results, data_manager, main_window, parent=None):
        super().__init__(parent)
        self.ui = SearchResultsDialog()
        self.ui.setupUi(self)

        self.search_query = search_query
        self.search_results = search_results
        self.data_manager = data_manager
        self.main_window = main_window

        self.setWindowTitle("Результаты умного поиска")
        self.resize(900, 600)

        self.ui.label_query.setText(f"Запрос: {search_query}")
        self.ui.label_count.setText(f"Найдено конспектов: {len(search_results)}")

        self.load_search_results()

        self.ui.pushButton_close.clicked.connect(self.close)
        self.ui.pushButton_export.clicked.connect(self.export_results)
        self.ui.tableWidget.cellDoubleClicked.connect(self.open_note)

        self.ui.tableWidget.setSortingEnabled(True)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.ui.tableWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.tableWidget.customContextMenuRequested.connect(self.show_context_menu)

    def load_search_results(self):
        self.ui.tableWidget.setRowCount(len(self.search_results))
        for row, result in enumerate(self.search_results):
            subject_item = QTableWidgetItem(result["subject"])
            subject_item.setData(Qt.ItemDataRole.UserRole, result)
            self.ui.tableWidget.setItem(row, 0, subject_item)
            name_item = QTableWidgetItem(result["note_name"])
            self.ui.tableWidget.setItem(row, 1, name_item)
            date_item = QTableWidgetItem(result["created_date"])
            self.ui.tableWidget.setItem(row, 2, date_item)
            relevance = result.get("relevance_score", 0)
            relevance_item = QTableWidgetItem(f"{relevance:.1f}%")
            if relevance >= 80:
                relevance_item.setForeground(QtGui.QBrush(QtGui.QColor(46, 204, 113)))
            elif relevance >= 60:
                relevance_item.setForeground(QtGui.QBrush(QtGui.QColor(241, 196, 15)))
            else:
                relevance_item.setForeground(QtGui.QBrush(QtGui.QColor(231, 76, 60)))
            self.ui.tableWidget.setItem(row, 3, relevance_item)

    def show_context_menu(self, position):
        item = self.ui.tableWidget.itemAt(position)
        if item:
            row = item.row()
            menu = QMenu(self)
            open_action = menu.addAction("📖 Открыть конспект")
            view_subject_action = menu.addAction("📚 Перейти к предмету")
            copy_info_action = menu.addAction("📋 Копировать информацию")
            action = menu.exec(self.ui.tableWidget.mapToGlobal(position))
            if action == open_action:
                self.open_selected_note(row)
            elif action == view_subject_action:
                self.view_subject(row)
            elif action == copy_info_action:
                self.copy_note_info(row)

    def open_selected_note(self, row=None):
        if row is None: row = self.ui.tableWidget.currentRow()
        if row >= 0: self.open_note(row, 0)

    def view_subject(self, row):
        if row >= 0:
            result_data = self.ui.tableWidget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.close()
            self.main_window.open_subject_notes_by_name(result_data["subject"])

    def copy_note_info(self, row):
        if row >= 0:
            result_data = self.ui.tableWidget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            text = f"Предмет: {result_data['subject']}\nКонспект: {result_data['note_name']}\nДата: {result_data['created_date']}"
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Скопировано", "Информация скопирована!")

    def open_note(self, row, column):
        result_data = self.ui.tableWidget.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.close()
        self.main_window.open_subject_with_note(result_data["subject"], result_data["note_name"])

    def export_results(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Экспорт", f"search_{self.search_query[:20]}.csv",
                                                   "CSV (*.csv)")
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    fieldnames = ['subject', 'note_name', 'content_preview', 'created_date', 'relevance_score',
                                  'search_query']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                    writer.writeheader()
                    for result in self.search_results:
                        writer.writerow({
                            'subject': result["subject"],
                            'note_name': result["note_name"],
                            'content_preview': result["content"][:200],
                            'created_date': result["created_date"],
                            'relevance_score': f"{result.get('relevance_score', 0):.1f}%",
                            'search_query': self.search_query
                        })
                QMessageBox.information(self, "Экспорт", "Успешно экспортировано")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", str(e))


class DataManager:
    def __init__(self):
        # 1. Определение пути для постоянного хранения данных (НЕ resource_path)
        self.app_dir = self.get_app_data_path()
        os.makedirs(self.app_dir, exist_ok=True)  # Создаем папку, если ее нет
        self.data_file = os.path.join(self.app_dir, "app_data.json")
        self.data = self.load_data()

    def get_app_data_path(self):
        """Возвращает постоянный путь для хранения данных приложения."""
        app_name = "Aggregator"  # Используйте имя вашего приложения
        if sys.platform.startswith('win'):
            # Windows: C:\Users\User\AppData\Local\Aggregator
            return os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), app_name)
        elif sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
            # Linux/macOS: ~/.local/share/Aggregator
            return os.path.join(os.path.expanduser('~'), '.local', 'share', app_name)
        return os.path.abspath(".")  # Fallback

    def load_data(self):
        # 2. Логика первого запуска: если постоянного файла нет, возвращаем пустые данные.
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Проверка на пустые/невалидные данные после загрузки
                    if not isinstance(data, dict) or "subjects" not in data or "notes" not in data:
                        raise ValueError("Invalid data structure")
                    return data
            except Exception as e:
                print(f"Error loading {self.data_file}: {e}")
                QMessageBox.warning(None, "Ошибка данных", "Файл данных поврежден. Начнется с чистого листа.")
                return {"subjects": [], "notes": {}}

        # Если файл НЕ существует (ПЕРВЫЙ ЗАПУСК)
        return {"subjects": [], "notes": {}}

    def save_data(self):
        try:
            # Убеждаемся, что папка существует перед сохранением
            os.makedirs(self.app_dir, exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def add_subject(self, subject_name):
        if subject_name and subject_name not in self.data["subjects"]:
            self.data["subjects"].append(subject_name)
            self.data["notes"][subject_name] = []
            return self.save_data()
        return False

    def get_subjects(self):
        return self.data["subjects"]

    def add_note(self, subject_name, note_name, content=""):
        if subject_name in self.data["notes"]:
            self.data["notes"][subject_name].append({
                "name": note_name, "content": content,
                "created_date": QDate.currentDate().toString("dd.MM.yyyy")
            })
            return self.save_data()
        return False

    def update_note_content(self, subject_name, note_name, new_content):
        """Обновление содержимого существующего конспекта."""
        if subject_name in self.data["notes"]:
            for note in self.data["notes"][subject_name]:
                if note["name"] == note_name:
                    note["content"] = new_content
                    return self.save_data()
        return False

    def get_notes(self, subject_name):
        return self.data["notes"].get(subject_name, [])

    def get_note_data(self, subject_name, note_name):
        for note in self.data["notes"].get(subject_name, []):
            if note["name"] == note_name: return note
        return None

    def delete_note(self, subject_name, note_name):
        if subject_name in self.data["notes"]:
            self.data["notes"][subject_name] = [n for n in self.data["notes"][subject_name] if n["name"] != note_name]
            return self.save_data()
        return False

    def delete_subject(self, subject_name):
        if subject_name in self.data["subjects"]:
            self.data["subjects"].remove(subject_name)
            if subject_name in self.data["notes"]: del self.data["notes"][subject_name]
            return self.save_data()
        return False

    def get_all_notes(self):
        all_notes = []
        for subject in self.data["subjects"]:
            for note in self.data["notes"].get(subject, []):
                all_notes.append({"subject": subject, "name": note["name"], "content": note["content"],
                                  "created_date": note.get("created_date", "Не указана")})
        return all_notes

    def smart_search(self, query, ai_client=None):
        all_notes = self.get_all_notes()
        if not all_notes: return []
        if not query.strip():
            return [{"subject": n["subject"], "note_name": n["name"], "content": n["content"],
                     "created_date": n["created_date"], "relevance_score": 100} for n in all_notes]

        if ai_client is None: return self.simple_text_search(query)

        try:
            notes_text = ""
            for i, note in enumerate(all_notes):
                notes_text += f"--- {i} ---\nSubj: {note['subject']}\nName: {note['name']}\nCont: {note['content'][:1000]}...\n"

            prompt = f"Пользователь ищет: '{query}'. Оцени релевантность конспектов (0-100). Верни JSON массив: [{{'index': 0, 'relevance_score': 85}}, ...]. Конспекты:\n{notes_text}"

            response = ai_client.chat.completions.create(
                model="google/gemini-2.5-flash-lite",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            response_text = response.choices[0].message.content.strip()

            try:
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                relevance_data = json.loads(json_match.group() if json_match else response_text)
            except:
                return self.simple_text_search(query)

            results = []
            for item in relevance_data:
                idx = item.get("index", 0)
                if 0 <= idx < len(all_notes):
                    n = all_notes[idx]
                    results.append({"subject": n["subject"], "note_name": n["name"], "content": n["content"],
                                    "created_date": n["created_date"],
                                    "relevance_score": item.get("relevance_score", 0)})
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return [r for r in results if r["relevance_score"] >= 30]
        except:
            return self.simple_text_search(query)

    def simple_text_search(self, query):
        all_notes = self.get_all_notes()
        q_low = query.lower()
        results = []
        for n in all_notes:
            rel = 0
            if q_low in n["name"].lower(): rel += 40
            if q_low in n["subject"].lower(): rel += 30
            if q_low in n["content"].lower(): rel += 20
            if rel > 0:
                results.append({"subject": n["subject"], "note_name": n["name"], "content": n["content"],
                                "created_date": n["created_date"], "relevance_score": min(rel, 100)})
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results

    def export_to_csv(self, filename=None):
        if filename is None: filename = resource_path("notes_export.csv")
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['subject', 'name', 'content', 'created_date'], delimiter=';')
                writer.writeheader()
                for n in self.get_all_notes():
                    writer.writerow({'subject': n['subject'], 'name': n['name'], 'content': n['content'],
                                     'created_date': n['created_date']})
            return True, f"Экспорт в {filename}"
        except Exception as e:
            return False, str(e)

    def import_from_csv(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                cnt = 0
                for row in reader:
                    subj = row.get('subject', '').strip()
                    name = row.get('name', '').strip()
                    # Проверяем наличие всех ключевых полей
                    if not subj or not name or 'content' not in row or 'created_date' not in row:
                        continue

                    # Добавляем предмет, если его нет
                    if subj not in self.data["subjects"]:
                        self.data["subjects"].append(subj)
                        self.data["notes"][subj] = []

                    # Добавляем конспект, если его нет
                    if not any(n["name"] == name for n in self.data["notes"][subj]):
                        self.data["notes"][subj].append({"name": name, "content": row.get('content', ''),
                                                         "created_date": row.get('created_date', '')})
                        cnt += 1
                self.save_data()
                return True, f"Импортировано {cnt} новых конспектов. Предметы обновлены."
        except Exception as e:
            return False, str(e)


class AllNotesTableWindow(QWidget):
    def __init__(self, data_manager, main_window, parent=None):
        super().__init__(parent)
        self.ui = AllNotesTable()
        self.ui.setupUi(self)
        self.data_manager = data_manager
        self.main_window = main_window  # Ссылка на главное окно

        layout = self.ui.verticalLayout
        btn_layout = QVBoxLayout()
        self.export_btn = QPushButton("📤 Экспорт в CSV")
        self.export_btn.clicked.connect(self.export_to_csv)
        self.import_btn = QPushButton("📥 Импорт из CSV")
        self.import_btn.clicked.connect(self.import_from_csv)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.import_btn)
        layout.addLayout(btn_layout)

        self.load_table_data()
        self.ui.tableWidget.cellDoubleClicked.connect(self.open_note_in_subject_window)

    def load_table_data(self):
        all_notes = self.data_manager.get_all_notes()
        self.ui.tableWidget.setRowCount(len(all_notes))
        for row, note in enumerate(all_notes):
            self.ui.tableWidget.setItem(row, 0, QTableWidgetItem(note["subject"]))
            self.ui.tableWidget.setItem(row, 1, QTableWidgetItem(note["name"]))
            self.ui.tableWidget.setItem(row, 2, QTableWidgetItem(note["created_date"]))
        self.ui.tableWidget.setSortingEnabled(True)
        # Гарантируем немедленное обновление отрисовки
        self.ui.tableWidget.viewport().update()

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт", "notes_export.csv", "CSV (*.csv)")
        if path:
            s, m = self.data_manager.export_to_csv(path)
            if s:
                QMessageBox.information(self, "OK", m)
            else:
                QMessageBox.warning(self, "Err", m)

    def import_from_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Импорт", "", "CSV (*.csv)")
        if path and QMessageBox.question(self, "Подтверждение импорта",
                                         "Импортировать? Это добавит новые предметы и конспекты в вашу базу данных.",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:

            s, m = self.data_manager.import_from_csv(path)
            if s:
                QMessageBox.information(self, "Успех", m)
                self.load_table_data()  # Обновляем таблицу в текущем окне (для отображения конспектов)

                # Обновляем список предметов в главном окне (для отображения новых предметов)
                self.main_window.load_subjects()

            else:
                QMessageBox.warning(self, "Ошибка", m)

    def open_note_in_subject_window(self, row, column):
        subj = self.ui.tableWidget.item(row, 0).text()
        name = self.ui.tableWidget.item(row, 1).text()
        self.close()
        self.main_window.open_subject_with_note(subj, name)


class AddSubjectDialogWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = AddSubjectDialogClass(parent)

    def exec(self): return self.dialog.exec()

    def get_subject_name(self): return self.dialog.lineEdit.text().strip()


class ImportNoteDialogWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = ImportNoteDialogClass(parent)
        self.selected_file = ""
        self.note_content = ""
        self.note_title = ""
        self.parent_window = parent
        self.progress_dialog = None

    def exec(self):
        result = self.dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.selected_file = getattr(self.dialog, 'file_path', '')

            if hasattr(self.dialog, 'note_title'): self.note_title = self.dialog.note_title
            if hasattr(self.dialog, 'note_content'): self.note_content = self.dialog.note_content

            if not self.note_content and self.selected_file:
                self.process_file_manually()

        return result

    def process_file_manually(self):
        try:
            with open(self.selected_file, 'r', encoding='utf-8') as f:
                self.note_content = f.read()
                self.note_title = os.path.splitext(os.path.basename(self.selected_file))[0]
        except:
            pass

    def get_file_path(self):
        return self.selected_file

    def get_note_name(self):
        if hasattr(self.dialog, 'get_note_name'): return self.dialog.get_note_name()
        return self.note_title

    def get_note_content(self):
        if hasattr(self.dialog, 'get_note_content'): return self.dialog.get_note_content()
        return self.note_content


class AskAIDialogWindow(QDialog):
    def __init__(self, note_name, note_content, parent=None):
        super().__init__(parent)
        self.note_name = note_name
        self.note_content = note_content
        self.setWindowTitle(f"Вопрос: {note_name}")
        self.resize(800, 600)

        # 1. Заголовок (Название конспекта)
        self.title_label = QLabel(note_name, self)
        self.title_label.setObjectName("note_title_label")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 2. Текстовый виджет-приветствие
        self.greeting_browser = QTextBrowser(self)
        self.greeting_browser.setHtml(
            "<p>Нейросеть готова ответить на вопросы по содержанию этого конспекта. Задайте вопрос ниже.</p>")
        self.greeting_browser.setMaximumHeight(80)

        # 3. Поле ввода вопроса
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setPlaceholderText("Введите ваш вопрос здесь...")
        self.lineEdit.setMinimumHeight(40)

        # 4. Кнопка "Задать вопрос нейросети"
        self.pushButton = QPushButton("✨ Задать вопрос нейросети", self)
        self.pushButton.setObjectName("ai_action_button")
        self.pushButton.clicked.connect(self.ask_question)

        # 5. Виджет для вывода ответа (основное окно)
        self.textBrowser = QTextBrowser(self)
        self.textBrowser.setMinimumHeight(150)
        self.textBrowser.setHtml("<h4>Ответ нейросети будет здесь.</h4>")

        # Размещение виджетов через QVBoxLayout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.greeting_browser)
        self.layout.addWidget(self.lineEdit)
        self.layout.addWidget(self.pushButton)
        self.layout.addWidget(self.textBrowser)

        self.setLayout(self.layout)

    def ask_question(self):
        q = self.lineEdit.text().strip()
        if not q:
            self.textBrowser.setHtml("<h4>Введите вопрос, чтобы получить ответ.</h4>")
            return

        self.pushButton.setEnabled(False)
        self.pushButton.setText("⏳ Идет поиск ответа...")
        QApplication.processEvents()

        # Очищаем и выводим вопрос в окно ответа перед началом процесса
        self.textBrowser.setHtml(f"<b>В: {q}</b><br><br><i>Нейросеть ищет ответ...</i>")
        QApplication.processEvents()

        try:
            resp = client.chat.completions.create(
                model="google/gemini-2.5-flash",
                messages=[{"role": "user", "content": f"Конспект:\n{self.note_content}\n\nВопрос: {q}"}]
            )
            self.display_response(q, resp.choices[0].message.content)
        except Exception as e:
            self.textBrowser.setHtml(f"<b>В: {q}</b><br><br><b>Ошибка:</b> {e}")
        finally:
            self.pushButton.setEnabled(True)
            self.pushButton.setText("✨ Задать вопрос нейросети")
            self.lineEdit.clear()

    def display_response(self, q, r):
        html = f"<b>В: {q}</b><br><br><b>О:</b><br>{r.replace(chr(10), '<br>')}<hr>"
        self.textBrowser.setHtml(html)
        self.textBrowser.verticalScrollBar().setValue(self.textBrowser.verticalScrollBar().maximum())


class NotesListWindow(QWidget):
    def __init__(self, subject_name, data_manager, parent=None):
        super().__init__(parent)
        self.ui = NotesList()
        self.ui.setupUi(self)
        self.subject_name = subject_name
        self.data_manager = data_manager
        self.current_note = None
        self.setWindowTitle(f"Конспекты - {subject_name}")

        self.resize(1000, 650)

        # Устанавливаем текст и режим
        self.ui.pushButton.setText("➕ Добавить конспект")
        self.ui.pushButton_2.setText("📝 Редактировать")
        self.ui.pushButton_3.setText("💾 Сохранить")
        self.ui.pushButton_4.setText("➖ Удалить")
        self.ui.pushButton_5.setText("✨ Задать вопрос нейросети")
        self.ui.textBrowser.setReadOnly(True)

        # Изначально деактивируем кнопки действий с конспектом
        self.ui.pushButton_2.setEnabled(False)
        self.ui.pushButton_3.setEnabled(False)
        self.ui.pushButton_4.setEnabled(False)
        self.ui.pushButton_5.setEnabled(False)

        self.load_notes()
        self.ui.listWidget.itemClicked.connect(self.on_note_selected)

        # Подключение функционала
        self.ui.pushButton.clicked.connect(self.add_note)
        self.ui.pushButton_4.clicked.connect(self.delete_note)
        self.ui.pushButton_5.clicked.connect(self.ask_ai)

        # ПОДКЛЮЧЕНИЕ ФУНКЦИОНАЛА РЕДАКТИРОВАНИЯ И СОХРАНЕНИЯ
        self.ui.pushButton_2.clicked.connect(self.edit_note)
        self.ui.pushButton_3.clicked.connect(self.save_note)

        self.ui.pushButton_5.setObjectName("ai_action_button")

        self.resizeEvent(None)

    def edit_note(self):
        """Переключает textBrowser в режим редактирования и обновляет состояние кнопок."""
        if not self.current_note: return

        self.ui.textBrowser.setReadOnly(False)
        self.ui.textBrowser.setFocus()

        # Состояния кнопок
        self.ui.pushButton_2.setEnabled(False)  # Редактировать - ВЫКЛ
        self.ui.pushButton_3.setEnabled(True)  # Сохранить - ВКЛ
        self.ui.pushButton_4.setEnabled(False)  # Удалить - ВЫКЛ
        self.ui.pushButton_5.setEnabled(False)  # ИИ - ВЫКЛ

        QMessageBox.information(self, "Редактирование",
                                "Конспект открыт для редактирования. Не забудьте нажать 'Сохранить'.")

    def save_note(self):
        """Сохраняет измененный контент и возвращает textBrowser в режим только для чтения."""
        if not self.current_note: return

        new_content = self.ui.textBrowser.toPlainText()

        if self.data_manager.update_note_content(self.subject_name, self.current_note, new_content):
            self.ui.textBrowser.setReadOnly(True)

            # Состояния кнопок
            self.ui.pushButton_2.setEnabled(True)  # Редактировать - ВКЛ
            self.ui.pushButton_3.setEnabled(False)  # Сохранить - ВЫКЛ
            self.ui.pushButton_4.setEnabled(True)  # Удалить - ВКЛ
            self.ui.pushButton_5.setEnabled(True)  # ИИ - ВКЛ

            QMessageBox.information(self, "Сохранение", "Конспект успешно сохранен!")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить конспект.")

    def load_notes(self):
        self.ui.listWidget.clear()
        for n in self.data_manager.get_notes(self.subject_name):
            self.ui.listWidget.addItem(QListWidgetItem(n["name"]))

    def on_note_selected(self, item):
        # Если находились в режиме редактирования, пытаемся сохранить или предупреждаем
        if not self.ui.textBrowser.isReadOnly():
            reply = QMessageBox.question(self, "Несохраненные изменения",
                                         "У вас есть несохраненные изменения. Сохранить их перед переключением?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)

            if reply == QMessageBox.StandardButton.Yes:
                self.save_note()
            elif reply == QMessageBox.StandardButton.Cancel:
                self.ui.listWidget.setCurrentItem(
                    self.ui.listWidget.findItems(self.current_note, Qt.MatchFlag.MatchExactly)[0])
                return

        # Устанавливаем режим только для чтения перед отображением
        self.ui.textBrowser.setReadOnly(True)

        self.current_note = item.text()
        self.ui.label_3.setText(self.current_note)
        data = self.data_manager.get_note_data(self.subject_name, self.current_note)
        if data:
            self.ui.label_2.setText(data.get("created_date", ""))
            self.ui.textBrowser.setText(data["content"])

            # Активируем кнопки (кроме Сохранить)
            self.ui.pushButton_2.setEnabled(True)
            self.ui.pushButton_3.setEnabled(False)
            self.ui.pushButton_4.setEnabled(True)
            self.ui.pushButton_5.setEnabled(True)
        else:
            # Деактивируем, если по какой-то причине данные не найдены
            self.ui.pushButton_2.setEnabled(False)
            self.ui.pushButton_3.setEnabled(False)
            self.ui.pushButton_4.setEnabled(False)
            self.ui.pushButton_5.setEnabled(False)

    def add_note(self):
        d = ImportNoteDialogWindow(self)
        if d.exec() == QDialog.DialogCode.Accepted and d.get_file_path():
            if self.data_manager.add_note(self.subject_name, d.get_note_name(), d.get_note_content()):
                self.load_notes()
                QMessageBox.information(self, "OK", "Конспект добавлен")

    def delete_note(self):
        if self.current_note and QMessageBox.question(self, "Удалить?", "Удалить?",
                                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.data_manager.delete_note(self.subject_name, self.current_note)
            self.load_notes()
            self.ui.textBrowser.clear()
            self.current_note = None
            self.ui.pushButton_2.setEnabled(False)
            self.ui.pushButton_3.setEnabled(False)
            self.ui.pushButton_4.setEnabled(False)
            self.ui.pushButton_5.setEnabled(False)

    def ask_ai(self):
        if self.current_note:
            data = self.data_manager.get_note_data(self.subject_name, self.current_note)
            if data and data.get("content"):
                AskAIDialogWindow(self.current_note, data["content"], self).exec()
            else:
                QMessageBox.warning(self, "Ошибка", "Невозможно задать вопрос: контент конспекта пуст.")

    def select_note_by_name(self, name):
        items = self.ui.listWidget.findItems(name, Qt.MatchFlag.MatchExactly)
        if items:
            self.ui.listWidget.setCurrentItem(items[0])
            self.on_note_selected(items[0])

    def resizeEvent(self, event):
        W = self.width()
        H = self.height()
        MARGIN = 20
        BTN_H = 40
        BTN_SPACE = 10
        LIST_W = 300

        ACTION_BTN_COUNT = 3
        ACTION_BTN_W = (W - (MARGIN * 3) - LIST_W - (BTN_SPACE * (ACTION_BTN_COUNT - 1))) // ACTION_BTN_COUNT

        BUTTON_BLOCK_H = (BTN_H * 2) + BTN_SPACE * 2

        # 1. Кнопка "Добавить конспект" (pushButton)
        BTN_ADD_Y = H - MARGIN - BTN_H
        self.ui.pushButton.setGeometry(MARGIN, BTN_ADD_Y, LIST_W, BTN_H)

        # 2. Список конспектов (QListWidget)
        LIST_Y = MARGIN
        LIST_H_ADJUSTED = H - LIST_Y - MARGIN - BTN_H - BTN_SPACE
        self.ui.listWidget.setGeometry(MARGIN, LIST_Y, LIST_W, LIST_H_ADJUSTED)

        # 3. Основное информационное поле (правая колонка)
        RIGHT_X = MARGIN + LIST_W + MARGIN
        RIGHT_W = W - RIGHT_X - MARGIN

        # Заголовок (label_3: Имя конспекта)
        self.ui.label_3.setGeometry(RIGHT_X, MARGIN, RIGHT_W, 30)

        # Дата (label_2: Дата создания)
        self.ui.label_2.setGeometry(RIGHT_X, MARGIN + 30, RIGHT_W, 20)

        # Текстовый браузер (textBrowser: Содержимое конспекта)
        TEXT_Y = MARGIN + 60
        TEXT_H = H - TEXT_Y - MARGIN - BUTTON_BLOCK_H
        self.ui.textBrowser.setGeometry(RIGHT_X, TEXT_Y, RIGHT_W, TEXT_H)

        # 4. Кнопки в правом нижнем углу (Два ряда)

        # --- Ряд 1: Редактировать, Сохранить, Удалить ---
        BTN_ROW1_Y = H - MARGIN - (BTN_H * 2) - BTN_SPACE

        # Редактировать (pushButton_2)
        self.ui.pushButton_2.setGeometry(RIGHT_X, BTN_ROW1_Y, ACTION_BTN_W, BTN_H)

        # Сохранить (pushButton_3)
        BTN_SAVE_X = RIGHT_X + ACTION_BTN_W + BTN_SPACE
        self.ui.pushButton_3.setGeometry(BTN_SAVE_X, BTN_ROW1_Y, ACTION_BTN_W, BTN_H)

        # Удалить (pushButton_4)
        BTN_DEL_X = BTN_SAVE_X + ACTION_BTN_W + BTN_SPACE
        self.ui.pushButton_4.setGeometry(BTN_DEL_X, BTN_ROW1_Y, ACTION_BTN_W, BTN_H)

        # --- Ряд 2: Задать вопрос нейросети (на всю ширину) ---
        AI_BTN_Y = H - MARGIN - BTN_H
        self.ui.pushButton_5.setGeometry(RIGHT_X, AI_BTN_Y, RIGHT_W, BTN_H)

        super().resizeEvent(event)


# =============================================================================
# ГЛАВНОЕ ОКНО
# =============================================================================

class MainWindow(QMainWindow):
    INSTRUCTIONS_TEXT = """
    Основные функции: 
    Это приложение помогает вам организовать учебные материалы и работать с ними с помощью нейросети. 
    Вы можете создавать предметы (например, "Математика", "Программирование") и добавлять к ним конспекты в виде файлов, а также удалять предметы нажатием правой кнопки мыши по соответствующему предмету. 
    В загрузке конспекта поддерживаются текстовые файлы (.txt), документы (.pdf, .docx), изображения (.jpg, .png), аудио (.mp3) и видео (.mp4). 
    Нейросеть поможет вам анализировать содержимое этих файлов - задавайте вопросы по материалам, и она будет искать ответы в ваших конспектах, а также найдёт нужные с помощью умного поиска.

    💡 Контроль данных: Вы можете загружать и выгружать все конспекты с помощью CSV-файлов для удобства переноса.

    Как работать:
    1) На главном экране создайте предметы через кнопку "Добавить предмет"; 
    2) Выберите предмет и добавьте к нему файлы-конспекты через "Добавить конспект"; 
    3) Чтобы задать вопрос нейросети, откройте предмет, выберите конспект и нажмите "Задать вопрос нейросети" или используйте умный поиск для поиска конспекта; 
    4) Все данные автоматически сохраняются. Для выхода можно использовать клавишу Escape - программа спросит, нужно ли сохранить изменения.
    """

    def __init__(self):
        super().__init__()
        # Настройка окна
        self.setWindowTitle("Умный агрегатор конспектов")
        self.resize(1000, 700)

        # --- ДОБАВЛЕНО ---
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # --- /ДОБАВЛЕНО ---

        # Менеджер данных
        self.data_manager = DataManager()
        self.notes_windows = {}

        # Переменные для поиска
        self._search_in_progress = False
        self.search_progress_dialog = None

        # Фон
        self.background_image = QtGui.QPixmap(resource_path("background.jpg"))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # === СОЗДАНИЕ UI ВРУЧНУЮ (ДЛЯ НОВОГО ДИЗАЙНА) ===
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background: transparent;")

        # 1. Заголовки
        self.subject_title_label = QLabel("Список предметов", self.central_widget)
        self.subject_title_label.setObjectName("subject_title_label")

        self.welcome_label = QLabel("Добро пожаловать!", self.central_widget)
        self.welcome_label.setObjectName("welcome_label")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        self.date_label = QLabel(self.central_widget)
        self.date_label.setObjectName("date_label")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # 2. Список предметов
        self.listWidget = QListWidget(self.central_widget)
        self.listWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # 3. Кнопки
        self.btn_add_note = QPushButton("➕ Добавить конспект", self.central_widget)
        self.btn_add_subject = QPushButton("➕ Добавить предмет", self.central_widget)
        self.btn_all_notes = QPushButton("📋 Все конспекты", self.central_widget)

        # 4. Поиск
        self.search_input = QLineEdit(self.central_widget)
        self.search_input.setPlaceholderText("Умный поиск...")
        self.btn_search = QPushButton("🔍", self.central_widget)

        # 5. Инструкция
        self.btn_settings = QPushButton("Инструкция", self.central_widget)
        self.btn_settings.setObjectName("btn_instructions")

        # === ПОДКЛЮЧЕНИЕ ФУНКЦИОНАЛА ===
        # Обновление даты
        current_date = QDate.currentDate()
        day_of_week = self.get_russian_day_of_week(current_date.dayOfWeek())
        self.date_label.setText(f"Сегодня {day_of_week}, {current_date.toString('dd MMMM yyyy')}")

        # Загрузка
        self.load_subjects()
        self.btn_add_note.setEnabled(False)

        # Сигналы
        self.btn_add_subject.clicked.connect(self.add_subject)
        self.btn_add_note.clicked.connect(self.add_note)
        self.btn_all_notes.clicked.connect(self.show_all_notes)
        self.btn_settings.clicked.connect(self.show_instructions)

        self.btn_search.clicked.connect(self.smart_search)
        self.search_input.returnPressed.connect(self.smart_search)

        self.listWidget.itemDoubleClicked.connect(self.open_subject_notes)
        self.listWidget.itemClicked.connect(self.on_subject_selected)
        self.listWidget.customContextMenuRequested.connect(self.show_context_menu)

    def paintEvent(self, event):
        """Отрисовка фона"""
        if not self.background_image.isNull():
            painter = QtGui.QPainter(self)
            scaled = self.background_image.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                                  Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.setBrush(QtGui.QColor(0, 0, 0, 150))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(self.rect())
        super().paintEvent(event)

    def resizeEvent(self, event):
        """РАСПОЛОЖЕНИЕ ЭЛЕМЕНТОВ"""
        W = self.width()
        H = self.height()
        MARGIN = 20
        # BTN_H = 40 # Не используется явно в resizeEvent, но определено в другом месте

        # Инструкция
        self.btn_settings.setGeometry(W - 140 - MARGIN, MARGIN, 140, 35)

        # Левая колонка (Список)
        LIST_W = 370
        LIST_TOP = 60
        LIST_BOTTOM_MARGIN = 120
        self.subject_title_label.setGeometry(MARGIN, MARGIN, LIST_W, 30)
        self.listWidget.setGeometry(MARGIN, LIST_TOP, LIST_W, H - LIST_TOP - LIST_BOTTOM_MARGIN)

        # Правая часть (Приветствие и Дата)
        CENTER_Y = H // 2 - 80
        WELCOME_W = 500
        WELCOME_H = 60
        DATE_H = 70

        # Приветствие
        self.welcome_label.setGeometry(W - WELCOME_W - MARGIN - 20, CENTER_Y, WELCOME_W, WELCOME_H)

        # Дата
        DATE_Y = CENTER_Y + WELCOME_H + 5
        self.date_label.setGeometry(W - WELCOME_W - MARGIN - 20, DATE_Y, WELCOME_W, DATE_H)

        # Поиск
        SEARCH_Y = DATE_Y + DATE_H + 30
        SEARCH_W = 400
        BTN_SEARCH_W = 50
        SEARCH_X = W - SEARCH_W - MARGIN - 20

        self.search_input.setGeometry(SEARCH_X, SEARCH_Y, SEARCH_W - BTN_SEARCH_W - 5, 40)
        self.btn_search.setGeometry(SEARCH_X + SEARCH_W - BTN_SEARCH_W, SEARCH_Y, BTN_SEARCH_W, 40)

        # Кнопки слева внизу
        BTN_H = 40  # Используем здесь
        BTN_Y_1 = H - LIST_BOTTOM_MARGIN + 10
        BTN_Y_2 = BTN_Y_1 + BTN_H + 10

        HALF_W = (LIST_W - 10) // 2
        self.btn_add_note.setGeometry(MARGIN, BTN_Y_1, HALF_W, BTN_H)
        self.btn_all_notes.setGeometry(MARGIN + HALF_W + 10, BTN_Y_1, HALF_W, BTN_H)

        # Большая кнопка "Добавить предмет" в самом низу
        self.btn_add_subject.setGeometry(MARGIN, BTN_Y_2, LIST_W, BTN_H)

        super().resizeEvent(event)

    # === ЛОГИКА ВЫХОДА ИЗ ПРОГРАММЫ (Восстановлено) ===

    def keyPressEvent(self, event):
        """Обработка нажатия ESC для вызова подтверждения выхода."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """Обработка события закрытия окна с подтверждением."""
        reply = QMessageBox.question(self, "Подтверждение выхода",
                                     "Вы действительно хотите выйти из программы?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # Закрываем все открытые окна конспектов перед выходом
            for subject_name, notes_window in list(self.notes_windows.items()):
                if notes_window is not None and notes_window.isVisible():
                    notes_window.close()
            event.accept()
        else:
            event.ignore()

            # === /ЛОГИКА ВЫХОДА ИЗ ПРОГРАММЫ ===

    # === ОСНОВНАЯ ЛОГИКА ПРИЛОЖЕНИЯ ===

    def get_russian_day_of_week(self, day):
        return {1: "понедельник", 2: "вторник", 3: "среда", 4: "четверг", 5: "пятница", 6: "суббота",
                7: "воскресенье"}.get(day, "")

    def load_subjects(self):
        """Загружает и отображает предметы из DataManager."""
        self.listWidget.clear()
        for s in self.data_manager.get_subjects():
            self.listWidget.addItem(QListWidgetItem(s))

    def on_subject_selected(self, item):
        self.btn_add_note.setEnabled(True)

    def add_subject(self):
        dialog = AddSubjectDialogWindow(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if self.data_manager.add_subject(dialog.get_subject_name()):
                self.load_subjects()
            else:
                QMessageBox.warning(self, "Ошибка", "Предмет уже существует!")

    def add_note(self):
        current_item = self.listWidget.currentItem()
        if not current_item: return

        subj = current_item.text()
        dialog = ImportNoteDialogWindow(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            path = dialog.get_file_path()
            if path:
                if self.data_manager.add_note(subj, dialog.get_note_name(), dialog.get_note_content()):
                    QMessageBox.information(self, "Успех", f"Конспект добавлен в {subj}!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось добавить!")

    def show_all_notes(self):
        # Передаем ссылку на себя, чтобы можно было обновить список предметов после импорта
        self.all_notes_window = AllNotesTableWindow(self.data_manager, self)
        self.all_notes_window.setWindowTitle("Все конспекты - Таблица")
        self.all_notes_window.resize(800, 600)
        self.all_notes_window.show()

    def smart_search(self):
        text = self.search_input.text().strip()
        if not text: return

        self.show_search_progress(text)
        QtCore.QTimer.singleShot(100, lambda: self.perform_smart_search(text))

    def show_search_progress(self, text):
        self.search_progress_dialog = QProgressDialog(f"Поиск: {text}", "Отмена", 0, 0, self)
        self.search_progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.search_progress_dialog.show()

    def perform_smart_search(self, text):
        try:
            res = self.data_manager.smart_search(text, client)
            if self.search_progress_dialog: self.search_progress_dialog.close()

            if res:
                self.show_search_results(text, res)
            else:
                QMessageBox.information(self, "Поиск", "Ничего не найдено")
        except Exception as e:
            if self.search_progress_dialog: self.search_progress_dialog.close()
            QMessageBox.warning(self, "Ошибка", str(e))

    def show_search_results(self, text, res):
        self.search_input.clear()
        SearchResultsWindow(text, res, self.data_manager, self, self).exec()

    def show_instructions(self):
        msg = QMessageBox()
        msg.setWindowTitle("Инструкция")
        msg.setText(self.INSTRUCTIONS_TEXT)
        msg.exec()

    def show_context_menu(self, pos):
        item = self.listWidget.itemAt(pos)
        if item:
            menu = QMenu(self)

            delt = menu.addAction("Удалить предмет")
            delt.setProperty("delete_item", True)

            if menu.exec(self.listWidget.mapToGlobal(pos)) == delt:
                if QMessageBox.question(self, "Удалить?", "Уверены?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:

                    subject_to_delete = item.text()

                    # 1. Удаляем данные и обновляем список
                    self.data_manager.delete_subject(subject_to_delete)
                    self.load_subjects()
                    self.btn_add_note.setEnabled(False)

                    # 2. Безопасно закрываем окно конспектов и удаляем ссылку из словаря
                    if subject_to_delete in self.notes_windows:
                        win = self.notes_windows.pop(subject_to_delete)
                        if win.isVisible():
                            win.close()

    def open_subject_notes(self, item):
        self.open_subject_notes_by_name(item.text())

    def open_subject_notes_by_name(self, name):
        if name in self.notes_windows and self.notes_windows[name].isVisible():
            self.notes_windows[name].activateWindow()
        else:
            w = NotesListWindow(name, self.data_manager)
            self.notes_windows[name] = w
            w.show()

    def open_subject_with_note(self, subj, note):
        self.open_subject_notes_by_name(subj)
        if subj in self.notes_windows:
            self.notes_windows[subj].select_note_by_name(note)


def main():
    app = QApplication(sys.argv)
    # ПРИМЕЧАНИЕ: Предполагается, что файл styles.py существует и содержит STYLESHEET
    app.setStyleSheet(styles.STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
