from PyQt6.QtWidgets import QWidget, QListWidgetItem, QMessageBox, QDialog
from PyQt6.QtCore import Qt
from ui.notes_list_ui import Ui_Form
from windows.dialogs.import_note import ImportNoteDialog
from windows.dialogs.ask_ai import AskAIDialog

class NotesListWindow(QWidget):
    def __init__(self, subject_name, data_manager, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.subject_name = subject_name
        self.data_manager = data_manager
        self.current_note = None
        
        self.setWindowTitle(f"Конспекты - {subject_name}")
        self.resize(1000, 650)
        
        # Init UI state
        self.ui.textBrowser.setReadOnly(True)
        self.toggle_buttons(False)

        self.load_notes()
        
        # Connections
        self.ui.listWidget.itemClicked.connect(self.on_note_selected)
        self.ui.pushButton.clicked.connect(self.add_note)          # Add
        self.ui.pushButton_2.clicked.connect(self.edit_note)         # Edit
        self.ui.pushButton_3.clicked.connect(self.save_note)         # Save
        self.ui.pushButton_4.clicked.connect(self.delete_note)       # Delete
        self.ui.pushButton_5.clicked.connect(self.ask_ai)            # AI

    def resizeEvent(self, event):
        W = self.width()
        H = self.height()
        MARGIN = 20
        BTN_H = 40
        BTN_SPACE = 10
        LIST_W = 300

        # Кнопки действий
        ACTION_BTN_COUNT = 3
        # Вычисляем ширину кнопок динамически
        ACTION_BTN_W = (W - (MARGIN * 3) - LIST_W - (BTN_SPACE * (ACTION_BTN_COUNT - 1))) // ACTION_BTN_COUNT
        BUTTON_BLOCK_H = (BTN_H * 2) + BTN_SPACE * 2

        # 1. Кнопка "Добавить конспект" (слева)
        BTN_ADD_Y = H - MARGIN - BTN_H
        self.ui.pushButton.setGeometry(MARGIN, BTN_ADD_Y, LIST_W, BTN_H)

        # 2. Список конспектов
        LIST_Y = MARGIN
        LIST_H_ADJUSTED = H - LIST_Y - MARGIN - BTN_H - BTN_SPACE
        self.ui.listWidget.setGeometry(MARGIN, LIST_Y, LIST_W, LIST_H_ADJUSTED)

        # 3. Правая колонка
        RIGHT_X = MARGIN + LIST_W + MARGIN
        RIGHT_W = W - RIGHT_X - MARGIN

        # Заголовок и дата
        self.ui.label_3.setGeometry(RIGHT_X, MARGIN, RIGHT_W, 30)
        self.ui.label_2.setGeometry(RIGHT_X, MARGIN + 30, RIGHT_W, 20)

        # Текстовое поле
        TEXT_Y = MARGIN + 60
        TEXT_H = H - TEXT_Y - MARGIN - BUTTON_BLOCK_H
        self.ui.textBrowser.setGeometry(RIGHT_X, TEXT_Y, RIGHT_W, TEXT_H)

        # 4. Кнопки управления (Два ряда)
        BTN_ROW1_Y = H - MARGIN - (BTN_H * 2) - BTN_SPACE

        # Редактировать / Сохранить / Удалить
        self.ui.pushButton_2.setGeometry(RIGHT_X, BTN_ROW1_Y, ACTION_BTN_W, BTN_H)

        BTN_SAVE_X = RIGHT_X + ACTION_BTN_W + BTN_SPACE
        self.ui.pushButton_3.setGeometry(BTN_SAVE_X, BTN_ROW1_Y, ACTION_BTN_W, BTN_H)

        BTN_DEL_X = BTN_SAVE_X + ACTION_BTN_W + BTN_SPACE
        self.ui.pushButton_4.setGeometry(BTN_DEL_X, BTN_ROW1_Y, ACTION_BTN_W, BTN_H)

        # Кнопка ИИ (на всю ширину справа)
        AI_BTN_Y = H - MARGIN - BTN_H
        self.ui.pushButton_5.setGeometry(RIGHT_X, AI_BTN_Y, RIGHT_W, BTN_H)

        super().resizeEvent(event)

    def toggle_buttons(self, enabled):
        self.ui.pushButton_2.setEnabled(enabled)
        self.ui.pushButton_3.setEnabled(False) # Save is mostly disabled unless editing
        self.ui.pushButton_4.setEnabled(enabled)
        self.ui.pushButton_5.setEnabled(enabled)

    def load_notes(self):
        self.ui.listWidget.clear()
        for n in self.data_manager.get_notes(self.subject_name):
            self.ui.listWidget.addItem(QListWidgetItem(n["name"]))

    def on_note_selected(self, item):
        # Check unsaved changes logic here if needed
        self.ui.textBrowser.setReadOnly(True)
        self.current_note = item.text()
        
        self.ui.label_3.setText(self.current_note)
        data = self.data_manager.get_note_data(self.subject_name, self.current_note)
        if data:
            self.ui.label_2.setText(data.get("created_date", ""))
            self.ui.textBrowser.setText(data["content"])
            self.toggle_buttons(True)

    def add_note(self):
        dlg = ImportNoteDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.get_note_name()
            content = dlg.get_note_content()
            if self.data_manager.add_note(self.subject_name, name, content):
                self.load_notes()
                QMessageBox.information(self, "OK", "Добавлено")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить (возможно, имя занято)")

    def edit_note(self):
        if not self.current_note: return
        self.ui.textBrowser.setReadOnly(False)
        self.ui.textBrowser.setFocus()
        self.ui.pushButton_2.setEnabled(False)
        self.ui.pushButton_3.setEnabled(True)

    def save_note(self):
        if not self.current_note: return
        new_content = self.ui.textBrowser.toPlainText()
        if self.data_manager.update_note_content(self.subject_name, self.current_note, new_content):
            self.ui.textBrowser.setReadOnly(True)
            self.ui.pushButton_2.setEnabled(True)
            self.ui.pushButton_3.setEnabled(False)
            QMessageBox.information(self, "OK", "Сохранено")

    def delete_note(self):
        if not self.current_note: return
        if QMessageBox.question(self, "Удаление", "Удалить конспект?", 
                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.data_manager.delete_note(self.subject_name, self.current_note)
            self.load_notes()
            self.ui.textBrowser.clear()
            self.current_note = None
            self.toggle_buttons(False)

    def ask_ai(self):
        if not self.current_note: return
        data = self.data_manager.get_note_data(self.subject_name, self.current_note)
        if data:
            AskAIDialog(self.current_note, data["content"], self).exec()
            
    def select_note_by_name(self, name):
        items = self.ui.listWidget.findItems(name, Qt.MatchFlag.MatchExactly)
        if items:
            self.ui.listWidget.setCurrentItem(items[0])
            self.on_note_selected(items[0])
