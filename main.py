# [file name]: main.py
# [file content begin]
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
                             QProgressDialog, QProgressBar)
from PyQt6.QtCore import QDate, Qt, QRect, QTimer
from PyQt6 import QtCore, QtGui
from openai import OpenAI

# Импорт UI файлов
from add_subject_dialog_ui import Ui_Dialog as AddSubjectDialog
from import_note_dialog_ui import Ui_Dialog as ImportNoteDialog
from main_screen_ui import Ui_Form as MainScreen
from notes_list_ui import Ui_Form as NotesList
from ask_ai_dialog_ui import Ui_Form as AskAIDialog
from all_notes_table_ui import Ui_Form as AllNotesTable
from search_results_ui import Ui_SearchResultsDialog as SearchResultsDialog

# Импорт обновленных классов
from add_subject_dialog import AddSubjectDialog as AddSubjectDialogClass
from import_note_dialog import ImportNoteDialog as ImportNoteDialogClass
from exceptions import SubjectValidationError, FileImportError

# Ключ OpenRouter
from openrouter_key import OPENROUTER_KEY

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)


class SearchResultsWindow(QDialog):
    def __init__(self, search_query, search_results, data_manager, main_window, parent=None):
        super().__init__(parent)
        self.ui = SearchResultsDialog()
        self.ui.setupUi(self)

        self.search_query = search_query
        self.search_results = search_results
        self.data_manager = data_manager
        self.main_window = main_window

        # Настройка окна
        self.setWindowTitle("Результаты умного поиска")
        self.resize(900, 600)

        # Отображение информации о запросе
        self.ui.label_query.setText(f"Запрос: {search_query}")
        self.ui.label_count.setText(f"Найдено конспектов: {len(search_results)}")

        # Загрузка результатов в таблицу
        self.load_search_results()

        # Подключение сигналов
        self.ui.pushButton_close.clicked.connect(self.close)
        self.ui.pushButton_export.clicked.connect(self.export_results)
        self.ui.tableWidget.cellDoubleClicked.connect(self.open_note)

        # Настройка таблицы
        self.ui.tableWidget.setSortingEnabled(True)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        # Добавляем контекстное меню для таблицы
        self.ui.tableWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.tableWidget.customContextMenuRequested.connect(self.show_context_menu)

    def load_search_results(self):
        """Загрузка результатов поиска в таблицу"""
        self.ui.tableWidget.setRowCount(len(self.search_results))

        for row, result in enumerate(self.search_results):
            # Предмет
            subject_item = QTableWidgetItem(result["subject"])
            subject_item.setData(Qt.ItemDataRole.UserRole, result)  # Сохраняем полные данные
            self.ui.tableWidget.setItem(row, 0, subject_item)

            # Название конспекта
            name_item = QTableWidgetItem(result["note_name"])
            self.ui.tableWidget.setItem(row, 1, name_item)

            # Дата добавления
            date_item = QTableWidgetItem(result["created_date"])
            self.ui.tableWidget.setItem(row, 2, date_item)

            # Релевантность (в процентах)
            relevance = result.get("relevance_score", 0)
            relevance_item = QTableWidgetItem(f"{relevance:.1f}%")

            # Настройка цвета в зависимости от релевантности
            if relevance >= 80:
                relevance_item.setForeground(QtGui.QBrush(QtGui.QColor(46, 204, 113)))  # Зеленый
            elif relevance >= 60:
                relevance_item.setForeground(QtGui.QBrush(QtGui.QColor(241, 196, 15)))  # Желтый
            else:
                relevance_item.setForeground(QtGui.QBrush(QtGui.QColor(231, 76, 60)))  # Красный

            self.ui.tableWidget.setItem(row, 3, relevance_item)

    def show_context_menu(self, position):
        """Показ контекстного меню для таблицы результатов"""
        item = self.ui.tableWidget.itemAt(position)
        if item:
            row = item.row()
            result_data = self.ui.tableWidget.item(row, 0).data(Qt.ItemDataRole.UserRole)

            menu = QMenu(self)

            # Добавляем пункты меню
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
        """Открытие выбранного конспекта"""
        if row is None:
            row = self.ui.tableWidget.currentRow()

        if row >= 0:
            self.open_note(row, 0)

    def view_subject(self, row):
        """Открытие окна предмета"""
        if row >= 0:
            result_data = self.ui.tableWidget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            subject_name = result_data["subject"]

            # Закрываем окно результатов
            self.close()

            # Открываем окно предмета
            self.main_window.open_subject_notes_by_name(subject_name)

    def copy_note_info(self, row):
        """Копирование информации о конспекте"""
        if row >= 0:
            result_data = self.ui.tableWidget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            subject = result_data["subject"]
            note_name = result_data["note_name"]
            date = result_data["created_date"]
            relevance = result_data.get("relevance_score", 0)

            text_to_copy = f"Предмет: {subject}\nКонспект: {note_name}\nДата: {date}\nРелевантность: {relevance:.1f}%"

            clipboard = QApplication.clipboard()
            clipboard.setText(text_to_copy)

            QMessageBox.information(self, "Скопировано", "Информация о конспекте скопирована в буфер обмена!")

    def open_note(self, row, column):
        """Открытие конспекта при двойном клике"""
        result_data = self.ui.tableWidget.item(row, 0).data(Qt.ItemDataRole.UserRole)
        subject = result_data["subject"]
        note_name = result_data["note_name"]

        # Закрываем окно результатов
        self.close()

        # Открываем конспект через главное окно
        self.main_window.open_subject_with_note(subject, note_name)

    def export_results(self):
        """Экспорт результатов поиска в CSV файл"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт результатов поиска",
            f"search_results_{self.search_query[:20]}.csv",
            "CSV Files (*.csv)"
        )

        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    fieldnames = ['subject', 'note_name', 'content_preview', 'created_date', 'relevance_score',
                                  'search_query']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')

                    writer.writeheader()
                    for result in self.search_results:
                        # Обрезаем контент для предпросмотра
                        content_preview = result["content"][:200] + "..." if len(result["content"]) > 200 else result[
                            "content"]

                        writer.writerow({
                            'subject': result["subject"],
                            'note_name': result["note_name"],
                            'content_preview': content_preview,
                            'created_date': result["created_date"],
                            'relevance_score': f"{result.get('relevance_score', 0):.1f}%",
                            'search_query': self.search_query
                        })

                QMessageBox.information(self, "Экспорт завершен",
                                        f"Результаты поиска успешно экспортированы в:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка экспорта", f"Не удалось экспортировать результаты: {str(e)}")


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

    def smart_search(self, query, ai_client=None):
        """Умный поиск конспектов с использованием нейросети"""
        all_notes = self.get_all_notes()

        if not all_notes:
            return []

        if not query.strip():
            # Если запрос пустой, возвращаем все конспекты
            return [{
                "subject": note["subject"],
                "note_name": note["name"],
                "content": note["content"],
                "created_date": note["created_date"],
                "relevance_score": 100  # Все конспекты релевантны при пустом запросе
            } for note in all_notes]

        # Если нет доступа к нейросети, используем простой текстовый поиск
        if ai_client is None:
            return self.simple_text_search(query)

        try:
            # Формируем промпт для нейросети
            notes_text = ""
            for i, note in enumerate(all_notes):
                notes_text += f"--- Конспект {i + 1} ---\n"
                notes_text += f"Предмет: {note['subject']}\n"
                notes_text += f"Название: {note['name']}\n"
                notes_text += f"Содержимое: {note['content'][:1000]}...\n\n"  # Ограничиваем длину

            prompt = f"""Пользователь ищет конспекты по запросу: "{query}"

Вот все доступные конспекты:
{notes_text}

Проанализируй релевантность каждого конспекта запросу пользователя и оцени от 0 до 100, где:
- 100: идеально соответствует запросу
- 80-99: очень релевантен
- 60-79: умеренно релевантен  
- 40-59: слабо релевантен
- 0-39: не релевантен

Верни ответ в формате JSON массива, где каждый элемент содержит:
- "index": номер конспекта (начиная с 0)
- "relevance_score": оценка релевантности (0-100)
- "reason": краткое объяснение (1-2 предложения)

Пример ответа:
[
  {{"index": 0, "relevance_score": 85, "reason": "Конспект содержит подробное объяснение баз данных, что соответствует запросу"}},
  {{"index": 1, "relevance_score": 45, "reason": "Только кратко упоминает базы данных"}}
]

ВАЖНО: Верни ТОЛЬКО JSON массив, без дополнительного текста."""

            response = ai_client.chat.completions.create(
                model="google/gemini-2.5-flash-lite",  # Используем более легкую модель для поиска
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1  # Низкая температура для более детерминированных результатов
            )

            response_text = response.choices[0].message.content.strip()

            # Извлекаем JSON из ответа
            try:
                # Попробуем найти JSON в ответе
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    relevance_data = json.loads(json_match.group())
                else:
                    relevance_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Если не удалось распарсить JSON, используем простой поиск
                print(f"Ошибка парсинга JSON от нейросети: {response_text}")
                return self.simple_text_search(query)

            # Формируем результаты с оценками релевантности
            results = []
            for item in relevance_data:
                index = item.get("index", 0)
                if 0 <= index < len(all_notes):
                    note = all_notes[index]
                    results.append({
                        "subject": note["subject"],
                        "note_name": note["name"],
                        "content": note["content"],
                        "created_date": note["created_date"],
                        "relevance_score": item.get("relevance_score", 0),
                        "reason": item.get("reason", "")
                    })

            # Сортируем по релевантности (по убыванию)
            results.sort(key=lambda x: x["relevance_score"], reverse=True)

            # Фильтруем только достаточно релевантные результаты (более 30%)
            filtered_results = [r for r in results if r["relevance_score"] >= 30]

            return filtered_results

        except Exception as e:
            print(f"Ошибка при умном поиске: {e}")
            # В случае ошибки используем простой текстовый поиск
            return self.simple_text_search(query)

    def simple_text_search(self, query):
        """Простой текстовый поиск (используется как fallback)"""
        all_notes = self.get_all_notes()
        query_lower = query.lower()

        results = []
        for note in all_notes:
            relevance = 0

            # Проверяем совпадения в названии
            if query_lower in note["name"].lower():
                relevance += 40

            # Проверяем совпадения в предмете
            if query_lower in note["subject"].lower():
                relevance += 30

            # Проверяем совпадения в содержимом
            if query_lower in note["content"].lower():
                relevance += 20
            else:
                # Проверяем отдельные слова
                query_words = query_lower.split()
                content_lower = note["content"].lower()
                for word in query_words:
                    if len(word) > 2 and word in content_lower:
                        relevance += 5

            if relevance > 0:
                results.append({
                    "subject": note["subject"],
                    "note_name": note["name"],
                    "content": note["content"],
                    "created_date": note["created_date"],
                    "relevance_score": min(relevance, 100)
                })

        # Сортируем по релевантности
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results

    def export_to_csv(self, filename=None):
        """Экспорт всех конспектов в CSV файл с правильной кодировкой"""
        if filename is None:
            filename = self.csv_file

        all_notes = self.get_all_notes()

        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['subject', 'name', 'content', 'created_date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')

                writer.writeheader()
                for note in all_notes:
                    cleaned_note = {
                        'subject': note['subject'].strip(),
                        'name': note['name'].strip(),
                        'content': note['content'].strip()[:500] + '...' if len(note['content']) > 500 else note[
                            'content'].strip(),
                        'created_date': note['created_date'].strip()
                    }
                    writer.writerow(cleaned_note)

            return True, f"Данные успешно экспортированы в {filename}"
        except Exception as e:
            return False, f"Ошибка при экспорте в CSV: {str(e)}"

    def import_from_csv(self, filename):
        """Импорт конспектов из CSV файла с правильной кодировкой"""
        try:
            with open(filename, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=';')
                imported_count = 0
                skipped_count = 0

                for row_num, row in enumerate(reader, 1):
                    try:
                        subject = row.get('subject', '').strip()
                        note_name = row.get('name', '').strip()
                        content = row.get('content', '').strip()
                        created_date = row.get('created_date', QDate.currentDate().toString("dd.MM.yyyy")).strip()

                        if not subject or not note_name:
                            skipped_count += 1
                            continue

                        if subject not in self.data["subjects"]:
                            self.data["subjects"].append(subject)
                            self.data["notes"][subject] = []

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
        self.note_title = ""  # Новое поле для хранения заголовка
        self.parent_window = parent  # Сохраняем ссылку на родительское окно
        self.progress_dialog = None  # Диалог прогресса

    def show_progress_dialog(self, filename):
        """Показ диалога прогресса с анимацией"""
        self.progress_dialog = QProgressDialog(
            f"Распознавание текста из изображения...\n{os.path.basename(filename)}",
            None,  # Без кнопки отмены
            0, 0,  # Неопределенное время выполнения
            self.parent_window
        )

        # Настройка диалога
        self.progress_dialog.setWindowTitle("Распознавание текста")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)  # Показываем сразу
        self.progress_dialog.setCancelButton(None)  # Убираем кнопку отмены

        # Устанавливаем индикатор в режим "занято"
        self.progress_dialog.setRange(0, 0)

        # Создаем таймер для анимации точек
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_progress_text)
        self.animation_timer.start(500)  # Обновляем каждые 500 мс

        self.dot_count = 0
        self.progress_dialog.show()
        QApplication.processEvents()  # Обрабатываем события для отображения диалога

    def update_progress_text(self):
        """Обновление текста с анимацией точек"""
        if self.progress_dialog:
            self.dot_count = (self.dot_count + 1) % 4
            dots = "." * self.dot_count
            base_text = f"Распознавание текста из изображения{dots}\n{os.path.basename(self.selected_file) if self.selected_file else ''}"
            self.progress_dialog.setLabelText(base_text)

    def close_progress_dialog(self):
        """Закрытие диалога прогресса"""
        if self.progress_dialog:
            if self.animation_timer:
                self.animation_timer.stop()
            self.progress_dialog.close()
            self.progress_dialog = None
            QApplication.processEvents()  # Обрабатываем события для обновления UI

    def recognize_image_text(self, image_path):
        """Отправка изображения в Gemini для распознавания текста с форматированием Markdown"""
        try:
            # Показываем индикатор загрузки
            self.show_progress_dialog(image_path)

            # Читаем изображение как base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # Определяем MIME тип по расширению файла
            mime_type = "image/jpeg"  # по умолчанию
            if image_path.lower().endswith('.png'):
                mime_type = "image/png"
            elif image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
                mime_type = "image/jpeg"
            elif image_path.lower().endswith('.gif'):
                mime_type = "image/gif"
            elif image_path.lower().endswith('.bmp'):
                mime_type = "image/bmp"
            elif image_path.lower().endswith('.webp'):
                mime_type = "image/webp"

            # Обновляем текст диалога
            if self.progress_dialog:
                self.progress_dialog.setLabelText(f"Отправка запроса к нейросети...\n{os.path.basename(image_path)}")
                QApplication.processEvents()

            response = client.chat.completions.create(
                model="google/gemini-2.5-flash",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """На картинке рукописный текст на русском языке. Распознай, что там написано. Исправляй ошибки распознавания.

ТРЕБОВАНИЯ К ФОРМАТИРОВАНИЮ:
1. Сначала определи заголовок конспекта - обычно это самая крупная или выделенная надпись в начале.
2. Отформатируй текст в Markdown с такими элементами:
   - Заголовок первого уровня для названия конспекта: # Заголовок
   - Заголовки второго уровня для основных разделов: ## Раздел
   - Заголовки третьего уровня для подразделов: ### Подраздел
   - Используй **жирный текст** для ключевых терминов
   - Используй *курсив* для важных определений
   - Используй маркированные списки (-) для перечислений
   - Используй нумерованные списки (1., 2., 3.) для шагов или последовательностей
   - Используй `код` для формул или специальных терминов

3. Разделяй текст на логические блоки с пустыми строками между ними.
4. Сохрани всю смысловую структуру оригинала.
5. В ответе должен быть только отформатированный текст в Markdown, ничего лишнего."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            )

            if self.progress_dialog:
                self.progress_dialog.setLabelText(f"Обработка ответа нейросети...\n{os.path.basename(image_path)}")
                QApplication.processEvents()

            recognized_text = response.choices[0].message.content.strip()

            # Извлекаем заголовок из распознанного текста (первая строка с #)
            lines = recognized_text.split('\n')
            for line in lines:
                if line.startswith('# '):
                    # Убираем символы # и пробелы для получения чистого заголовка
                    self.note_title = line.replace('# ', '').strip()
                    break

            # Закрываем диалог прогресса
            self.close_progress_dialog()

            return recognized_text

        except Exception as e:
            print(f"Ошибка распознавания изображения: {e}")
            file_name = os.path.basename(image_path)
            self.note_title = file_name

            # Закрываем диалог прогресса в случае ошибки
            self.close_progress_dialog()

            return f"# Ошибка при распознавании\n\nНе удалось распознать текст из изображения: {str(e)}"

    def exec(self):
        """Выполнение диалога с обработкой результата"""
        result = self.dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            # Получаем данные из диалога
            self.selected_file = getattr(self.dialog, 'file_path', '')
            if self.selected_file:
                # Определяем расширение файла
                file_ext = os.path.splitext(self.selected_file)[1].lower()

                # Список поддерживаемых изображений для распознавания
                image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

                if self.selected_file.lower().endswith('.txt'):
                    # Чтение текстового файла и сохранение как обычный текст
                    try:
                        with open(self.selected_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                            # Проверяем, есть ли в тексте Markdown-заголовок
                            lines = content.split('\n')
                            for line in lines:
                                if line.startswith('# '):
                                    self.note_title = line.replace('# ', '').strip()
                                    break
                            else:
                                # Если заголовка нет, используем первую строку или имя файла
                                if lines and lines[0].strip():
                                    self.note_title = lines[0].strip()[:50]  # Ограничиваем длину
                                else:
                                    self.note_title = self.get_note_name()

                            self.note_content = content
                    except:
                        file_name = os.path.basename(self.selected_file)
                        self.note_title = file_name
                        self.note_content = f"# {file_name}\n\nНе удалось прочитать содержимое файла."

                elif file_ext in image_extensions:
                    # Распознавание текста из изображения с форматированием Markdown
                    file_name = os.path.basename(self.selected_file)
                    self.note_content = self.recognize_image_text(self.selected_file)

                    # Если заголовок не был извлечен из текста, используем имя файла
                    if not self.note_title:
                        self.note_title = self.get_note_name()

                else:
                    # Для других типов файлов создаем простую текстовую заметку
                    file_name = os.path.basename(self.selected_file)
                    self.note_title = file_name
                    self.note_content = f"# {file_name}\n\nФайл импортирован: {file_name}"

            return QDialog.DialogCode.Accepted
        return QDialog.DialogCode.Rejected

    def get_file_path(self):
        return self.selected_file

    def get_note_name(self):
        """Получение имени конспекта из имени файла или распознанного заголовка"""
        if self.note_title:
            # Если есть распознанный заголовок, используем его
            # Ограничиваем длину и убираем запрещенные символы для имени файла
            clean_title = re.sub(r'[\\/*?:"<>|]', '', self.note_title)
            return clean_title[:100]  # Ограничиваем длину
        elif self.selected_file:
            # Иначе используем имя файла без расширения
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
        # Используем функцию markdown_to_html из AskAIDialogWindow для конвертации Markdown
        try:
            # Создаем временный экземпляр для использования метода markdown_to_html
            temp_dialog = AskAIDialogWindow("temp", "", None)
            return temp_dialog.markdown_to_html(content)
        except:
            # Если произошла ошибка, отображаем как обычный текст
            return f"""
            <html>
            <body>
            <p style="font-size: 14px; color: #666; white-space: pre-wrap;">
            {content}
            </p>
            </body>
            </html>
            """

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
        self.search_progress_dialog = None  # Диалог прогресса для поиска
        self._search_in_progress = False
        self._last_search_time = QtCore.QTime.currentTime()
        self._line_edit_signals_blocked = False

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
        self.ui.pushButton_4.clicked.connect(self.smart_search)
        self.ui.listWidget.itemDoubleClicked.connect(self.open_subject_notes)
        self.ui.listWidget.itemClicked.connect(self.on_subject_selected)

        # Добавляем обработку нажатия Enter в поле поиска
        self.ui.lineEdit.returnPressed.connect(self.smart_search)

        # Включаем контекстное меню для списка предметов
        self.ui.listWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.listWidget.customContextMenuRequested.connect(self.show_context_menu)

        # Изначально кнопка добавления конспекта неактивна
        self.ui.pushButton.setEnabled(False)

        # Добавляем кнопку для просмотра всех конспектов
        self.add_all_notes_button()

        # Устанавливаем фокус на виджет для получения событий клавиатуры
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def smart_search(self, from_key_press=False):
        """Умный поиск конспектов с использованием нейросети"""
        search_text = self.ui.lineEdit.text().strip()

        if not search_text:
            QMessageBox.warning(self, "Поиск", "Введите текст для поиска!")
            return

        # Защита от повторного вызова (debounce)
        current_time = QtCore.QTime.currentTime()
        if hasattr(self, '_last_search_time') and not from_key_press:
            time_diff = self._last_search_time.msecsTo(current_time)
            if time_diff < 1000:  # Защита от быстрых повторных вызовов (1 секунда)
                return

        self._last_search_time = current_time

        # Если поиск уже выполняется, не запускаем новый
        if hasattr(self, '_search_in_progress') and self._search_in_progress:
            return

        self._search_in_progress = True

        # Показываем диалог прогресса
        self.show_search_progress(search_text)

        # Используем QTimer для асинхронного выполнения поиска
        QtCore.QTimer.singleShot(100, lambda: self.perform_smart_search(search_text))

    def show_search_progress(self, search_text):
        """Показ диалога прогресса поиска"""
        self.search_progress_dialog = QProgressDialog(
            f"Выполняется умный поиск по запросу:\n\"{search_text}\"",
            "Отмена",
            0, 0,
            self
        )

        # Настройка диалога
        self.search_progress_dialog.setWindowTitle("Умный поиск")
        self.search_progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.search_progress_dialog.setMinimumDuration(0)

        # Устанавливаем индикатор в режим "занято"
        self.search_progress_dialog.setRange(0, 0)

        # Подключаем кнопку отмены
        self.search_progress_dialog.canceled.connect(self.cancel_search)

        # Создаем таймер для анимации
        self.search_animation_timer = QTimer()
        self.search_animation_timer.timeout.connect(self.update_search_progress_text)
        self.search_animation_timer.start(500)

        self.search_dot_count = 0
        self.search_progress_dialog.show()
        QApplication.processEvents()

    def update_search_progress_text(self):
        """Обновление текста с анимацией точек"""
        if self.search_progress_dialog:
            self.search_dot_count = (self.search_dot_count + 1) % 4
            dots = "." * self.search_dot_count
            base_text = self.search_progress_dialog.labelText().split('\n')[0]
            self.search_progress_dialog.setLabelText(f"{base_text}{dots}")

    def cancel_search(self):
        """Отмена поиска"""
        if self.search_progress_dialog:
            if hasattr(self, 'search_animation_timer'):
                self.search_animation_timer.stop()
            self.search_progress_dialog.close()
            self.search_progress_dialog = None

    def close_search_progress(self):
        """Закрытие диалога прогресса поиска"""
        if self.search_progress_dialog:
            if hasattr(self, 'search_animation_timer'):
                self.search_animation_timer.stop()
            self.search_progress_dialog.close()
            self.search_progress_dialog = None
            QApplication.processEvents()

        # Восстанавливаем обработку сигналов в поле поиска
        if hasattr(self, '_line_edit_signals_blocked') and self._line_edit_signals_blocked:
            self.ui.lineEdit.blockSignals(False)
            self._line_edit_signals_blocked = False

    def perform_smart_search(self, search_text):
        """Выполнение умного поиска"""
        try:
            # Выполняем поиск через DataManager
            search_results = self.data_manager.smart_search(search_text, client)

            # Закрываем диалог прогресса
            self.close_search_progress()

            # Сбрасываем флаг выполнения поиска
            self._search_in_progress = False

            # Показываем результаты
            if search_results:
                self.show_search_results(search_text, search_results)
            else:
                QMessageBox.information(self, "Результаты поиска",
                                        "По вашему запросу ничего не найдено.\n\nПопробуйте изменить формулировку запроса.")

                # Восстанавливаем фокус на поле поиска после закрытия сообщения
                QtCore.QTimer.singleShot(100, self.ui.lineEdit.setFocus)

        except Exception as e:
            # Закрываем диалог прогресса в случае ошибки
            self.close_search_progress()

            # Сбрасываем флаг выполнения поиска
            self._search_in_progress = False

            QMessageBox.warning(self, "Ошибка поиска",
                                f"Произошла ошибка при выполнении поиска:\n\n{str(e)}\n\nПопробуйте еще раз.")

            # Восстанавливаем фокус на поле поиска после ошибки
            QtCore.QTimer.singleShot(100, self.ui.lineEdit.setFocus)

    def show_search_results(self, search_text, search_results):
        """Показ результатов поиска в отдельном окне"""
        # Очищаем поле поиска перед показом результатов
        # Это предотвращает случайное повторное нажатие Enter
        self.ui.lineEdit.blockSignals(True)
        self.ui.lineEdit.clear()
        self.ui.lineEdit.blockSignals(False)

        # Создаем и показываем окно результатов
        results_window = SearchResultsWindow(search_text, search_results,
                                             self.data_manager, self, self)

        # Подключаем сигнал закрытия окна результатов
        results_window.finished.connect(self.on_search_results_closed)

        results_window.exec()

    def on_search_results_closed(self):
        """Обработчик закрытия окна результатов поиска"""
        # Устанавливаем фокус на главное окно, а не на поле поиска
        self.activateWindow()
        self.setFocus()

        # Очищаем флаг поиска
        if hasattr(self, '_search_in_progress'):
            self._search_in_progress = False

        # Очищаем поле поиска для предотвращения случайного повторного поиска
        QtCore.QTimer.singleShot(50, self.ui.lineEdit.clear)

    def keyPressEvent(self, event):
        """Обработка нажатия клавиш"""
        if event.key() == Qt.Key.Key_Escape:
            self.close_application()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Проверяем, находится ли фокус в поле поиска
            if self.ui.lineEdit.hasFocus():
                # Запускаем поиск с флагом, что он вызван из keyPressEvent
                self.smart_search(from_key_press=True)
                # Блокируем дальнейшую обработку Enter
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def close_application(self):
        """Закрытие приложения с подтверждением"""
        reply = QMessageBox.question(
            self,
            "Подтверждение выхода",
            "Вы уверены, что хотите выйти из приложения?\n\nВсе несохраненные изменения будут потеряны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.close()

    def closeEvent(self, event):
        """Обработка события закрытия окна (через крестик)"""
        reply = QMessageBox.question(
            self,
            "Подтверждение выхода",
            "Вы уверены, что хотите выйти из приложения?\n\nВсе несохраненные изменения будут потеряны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Закрываем все открытые окна предметов перед закрытием главного окна
            for subject_name, notes_window in list(self.notes_windows.items()):
                if notes_window and hasattr(notes_window, 'close'):
                    notes_window.close()
            event.accept()
        else:
            event.ignore()

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
            # Проверяем, что окно существует и активно
            if notes_window is not None and hasattr(notes_window, 'select_note_by_name'):
                notes_window.select_note_by_name(note_name)
                # Активируем окно, чтобы оно было поверх других
                notes_window.raise_()
                notes_window.activateWindow()

    def open_subject_notes_by_name(self, subject_name):
        """Открытие окна предмета по имени как отдельного окна"""
        # Проверяем, не открыто ли уже окно для этого предмета
        if subject_name in self.notes_windows:
            notes_window = self.notes_windows[subject_name]
            # Проверяем, существует ли еще объект окна и видимо ли оно
            if notes_window is not None and hasattr(notes_window, 'isVisible') and notes_window.isVisible():
                notes_window.raise_()
                notes_window.activateWindow()
                return
            else:
                # Если окно было закрыто или уничтожено, удаляем его из словаря
                if subject_name in self.notes_windows:
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
        # Полностью удаляем запись из словаря при закрытии окна
        if subject_name in self.notes_windows:
            # Проверяем, существует ли еще объект окна
            notes_window = self.notes_windows[subject_name]
            if notes_window is None or not hasattr(notes_window, 'isVisible') or not notes_window.isVisible():
                del self.notes_windows[subject_name]

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
                if subject_name in self.notes_windows:
                    notes_window = self.notes_windows[subject_name]
                    if notes_window is not None and hasattr(notes_window, 'close'):
                        notes_window.close()
                    # Удаляем из словаря
                    if subject_name in self.notes_windows:
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