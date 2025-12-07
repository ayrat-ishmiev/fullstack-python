from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QListWidget, QPushButton, QLineEdit, QMessageBox, QMenu, QListWidgetItem, QProgressDialog, QDialog
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6 import QtGui

from core.utils import resource_path
from data.data_manager import DataManager
from windows.dialogs.add_subject import AddSubjectDialog
from windows.dialogs.import_note import ImportNoteDialog
from windows.dialogs.search_results import SearchResultsWindow
from windows.widgets.notes_list import NotesListWindow
from windows.widgets.all_notes import AllNotesTableWindow
from services.ai_service import AIService
from windows.dialogs.add_note_choice import AddNoteChoiceDialog
from windows.dialogs.generate_note import GenerateNoteDialog
from core.utils import resource_path, get_formatted_date # <--- Добавили get_formatted_date
from config.keys import OPENROUTER_KEY
from windows.dialogs.settings import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Умный агрегатор конспектов")
        self.resize(1000, 700)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.data_manager = DataManager()
        self.apply_api_settings()
        self.notes_windows = {} # Cache for open windows

        # Background
        self.bg_pixmap = QtGui.QPixmap(resource_path("assets/background.jpg"))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Build UI manually (as in original main.py logic for custom layout)
        self.setup_ui()
        self.load_subjects()

    def apply_api_settings(self):
        """Считывает настройки и передает нужный ключ в AIService."""
        settings = self.data_manager.get_settings()
        if settings.get("api_source") == "custom":
            custom_key = settings.get("custom_key", "")
            if custom_key:
                AIService.set_api_key(custom_key)
            else:
                AIService.set_api_key(OPENROUTER_KEY)  # Fallback
        else:
            AIService.set_api_key(OPENROUTER_KEY)

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background: transparent;")  # Важно для прозрачности

        # 1. Заголовки (Важно: setObjectName должен совпадать с CSS в styles.py)
        self.lbl_subjects = QLabel("Список предметов", self.central_widget)
        self.lbl_subjects.setObjectName("subject_title_label")  # ID для CSS

        self.lbl_welcome = QLabel("Добро пожаловать!", self.central_widget)
        self.lbl_welcome.setObjectName("welcome_label")  # ID для CSS
        self.lbl_welcome.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        self.lbl_date = QLabel(self.central_widget)
        self.lbl_date.setObjectName("date_label")  # ID для CSS
        self.lbl_date.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.lbl_date.setText(get_formatted_date())

        # 2. Список
        self.list_widget = QListWidget(self.central_widget)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.itemDoubleClicked.connect(self.open_subject_notes)
        self.list_widget.itemClicked.connect(lambda: self.btn_add_note.setEnabled(True))

        # 3. Кнопки
        self.btn_add_note = QPushButton("➕ Добавить конспект", self.central_widget)
        self.btn_add_note.setEnabled(False)
        self.btn_add_note.clicked.connect(self.add_note)

        self.btn_add_subject = QPushButton("➕ Добавить предмет", self.central_widget)
        self.btn_add_subject.clicked.connect(self.add_subject)

        self.btn_all = QPushButton("📋 Все конспекты", self.central_widget)
        self.btn_all.clicked.connect(self.show_all_notes)

        # Кнопка Инструкция (оставляем)
        self.btn_info = QPushButton("Инструкция", self.central_widget)
        self.btn_info.clicked.connect(self.show_instructions)

        # Кнопка Настройки (НОВАЯ)
        self.btn_settings = QPushButton("⚙ Настройки", self.central_widget)
        self.btn_settings.clicked.connect(self.open_settings)

        # 4. Поиск
        self.search_input = QLineEdit(self.central_widget)
        self.search_input.setPlaceholderText("Умный поиск...")
        self.search_input.returnPressed.connect(self.smart_search)

        self.btn_search = QPushButton("🔍", self.central_widget)
        self.btn_search.clicked.connect(self.smart_search)

    def paintEvent(self, event):
        if not self.bg_pixmap.isNull():
            painter = QtGui.QPainter(self)
            scaled = self.bg_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.setBrush(QtGui.QColor(0, 0, 0, 150)) # Dark overlay
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(self.rect())
        super().paintEvent(event)

    def resizeEvent(self, event):
        """
        Полная логика позиционирования из оригинального main.py.
        Восстанавливает расположение элементов.
        """
        W = self.width()
        H = self.height()
        MARGIN = 20

        # Инструкция (сдвигаем левее)
        self.btn_info.setGeometry(W - 250 - MARGIN, MARGIN, 120, 35)

        # Настройки (в самый правый угол)
        self.btn_settings.setGeometry(W - 120 - MARGIN, MARGIN, 120, 35)

        # Левая колонка (Список)
        LIST_W = 370
        LIST_TOP = 60
        LIST_BOTTOM_MARGIN = 120

        self.lbl_subjects.setGeometry(MARGIN, MARGIN, LIST_W, 30)
        self.list_widget.setGeometry(MARGIN, LIST_TOP, LIST_W, H - LIST_TOP - LIST_BOTTOM_MARGIN)

        # Правая часть (Приветствие и Дата)
        # Центрируем относительно правой свободной области
        CENTER_Y = H // 2 - 80
        WELCOME_W = 500
        WELCOME_H = 60
        DATE_H = 70

        # Приветствие
        self.lbl_welcome.setGeometry(W - WELCOME_W - MARGIN - 20, CENTER_Y, WELCOME_W, WELCOME_H)

        # Дата
        DATE_Y = CENTER_Y + WELCOME_H + 5
        self.lbl_date.setGeometry(W - WELCOME_W - MARGIN - 20, DATE_Y, WELCOME_W, DATE_H)

        # Поиск (Под датой)
        SEARCH_Y = DATE_Y + DATE_H + 30
        SEARCH_W = 400
        BTN_SEARCH_W = 50
        SEARCH_X = W - SEARCH_W - MARGIN - 20

        self.search_input.setGeometry(SEARCH_X, SEARCH_Y, SEARCH_W - BTN_SEARCH_W - 5, 40)
        self.btn_search.setGeometry(SEARCH_X + SEARCH_W - BTN_SEARCH_W, SEARCH_Y, BTN_SEARCH_W, 40)

        # Кнопки слева внизу
        BTN_H = 40
        BTN_Y_1 = H - LIST_BOTTOM_MARGIN + 10
        BTN_Y_2 = BTN_Y_1 + BTN_H + 10

        HALF_W = (LIST_W - 10) // 2
        self.btn_add_note.setGeometry(MARGIN, BTN_Y_1, HALF_W, BTN_H)
        self.btn_all.setGeometry(MARGIN + HALF_W + 10, BTN_Y_1, HALF_W, BTN_H)

        # Большая кнопка "Добавить предмет" в самом низу
        self.btn_add_subject.setGeometry(MARGIN, BTN_Y_2, LIST_W, BTN_H)

        super().resizeEvent(event)

    def load_subjects(self):
        self.list_widget.clear()
        for s in self.data_manager.get_subjects():
            self.list_widget.addItem(QListWidgetItem(s))

    def add_subject(self):
        dlg = AddSubjectDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.data_manager.add_subject(dlg.get_subject_name()):
                self.load_subjects()

    def add_note(self):
        item = self.list_widget.currentItem()
        if not item: return
        subj_name = item.text()

        # 1. Спрашиваем пользователя: Файл или ИИ?
        choice_dlg = AddNoteChoiceDialog(self)
        if choice_dlg.exec() != QDialog.DialogCode.Accepted:
            return

        # 2. Логика в зависимости от выбора
        if choice_dlg.choice == 'file':
            # СТАРЫЙ СПОСОБ (Импорт файла)
            dlg = ImportNoteDialog(self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                if dlg.file_path:
                    # Проверяем уникальность имени
                    if self.data_manager.add_note(subj_name, dlg.get_note_name(), dlg.get_note_content()):
                        QMessageBox.information(self, "Успех", f"Конспект добавлен в {subj_name}!")
                    else:
                        QMessageBox.warning(self, "Ошибка", "Конспект с таким именем уже существует.")

        elif choice_dlg.choice == 'ai':
            # НОВЫЙ СПОСОБ (Генерация)
            gen_dlg = GenerateNoteDialog(subj_name, self)
            if gen_dlg.exec() == QDialog.DialogCode.Accepted:
                name = gen_dlg.get_note_name()
                content = gen_dlg.get_note_content()

                # Пометка, что это AI конспект
                name = f"✨ {name}"

                if self.data_manager.add_note(subj_name, name, content):
                    QMessageBox.information(self, "Успех", f"Сгенерированный конспект добавлен!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Конспект с таким именем уже существует.")

    def show_all_notes(self):
        self.all_notes_win = AllNotesTableWindow(self.data_manager, self)
        self.all_notes_win.setWindowTitle("Все конспекты")
        self.all_notes_win.resize(800, 600)
        self.all_notes_win.show()

    def smart_search(self):
        q = self.search_input.text().strip()
        if not q: return
        
        pd = QProgressDialog(f"Ищу: {q}", "Отмена", 0, 0, self)
        pd.setWindowModality(Qt.WindowModality.WindowModal)
        pd.show()
        QTimer.singleShot(100, lambda: self._execute_search(q, pd))

    def _execute_search(self, q, pd):
        try:
            results = self.data_manager.smart_search(q, AIService.get_client())
            pd.close()
            SearchResultsWindow(q, results, self.data_manager, self, self).exec()
        except Exception as e:
            pd.close()
            QMessageBox.critical(self, "Ошибка поиска", str(e))

    def open_subject_notes(self, item):
        self.open_subject_notes_by_name(item.text())

    def open_subject_notes_by_name(self, name):
        if name in self.notes_windows and self.notes_windows[name].isVisible():
            self.notes_windows[name].activateWindow()
        else:
            w = NotesListWindow(name, self.data_manager)
            self.notes_windows[name] = w
            w.show()

    def open_subject_with_note(self, subj, note_name):
        self.open_subject_notes_by_name(subj)
        if subj in self.notes_windows:
            self.notes_windows[subj].select_note_by_name(note_name)

    def show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if item:
            # 1. СРАЗУ сохраняем имя предмета в обычную переменную
            subject_name = item.text()

            menu = QMenu(self)
            act_del = menu.addAction("Удалить предмет")

            # Добавляем свойство для красного цвета (как в оригинале)
            act_del.setProperty("delete_item", True)

            if menu.exec(self.list_widget.mapToGlobal(pos)) == act_del:
                reply = QMessageBox.question(
                    self,
                    "Удаление",
                    f"Удалить предмет '{subject_name}' и все его конспекты?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    # 2. Используем сохраненную строку subject_name, а не item.text()

                    # Удаляем данные
                    self.data_manager.delete_subject(subject_name)

                    # Закрываем окно конспектов, если оно открыто
                    if subject_name in self.notes_windows:
                        win = self.notes_windows.pop(subject_name)
                        if win.isVisible():
                            win.close()

                    # 3. Обновляем список ТОЛЬКО ПОСЛЕ всех операций с данными
                    # (это уничтожит объект item, но нам он уже не нужен)
                    self.load_subjects()

                    # Если был выбран удаленный предмет, блокируем кнопку добавления
                    self.btn_add_note.setEnabled(False)

    def show_instructions(self):
        QMessageBox.information(self, "Инструкция", "1. Создайте предмет\n2. Добавьте конспект\n3. Используйте поиск!")

    def open_settings(self):
        dlg = SettingsDialog(self.data_manager, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Если нажали "Сохранить", применяем новый ключ немедленно
            self.apply_api_settings()
            QMessageBox.information(self, "Успех", "Настройки сохранены и применены.")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Выход", "Выйти?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            for w in self.notes_windows.values(): w.close()
            event.accept()
        else:
            event.ignore()
