import os
from PyQt6.QtWidgets import QDialog, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
from ui.import_note_dialog_ui import Ui_Dialog
from core.exceptions import FileImportError

class ImportNoteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.has_unsaved_changes = False
        
        self.file_path = None
        self.file_content = ""
        self.file_type = ""
        self.note_title = ""

        self.ui.pushButton_Add.setEnabled(False)
        self.ui.label.setText("Загрузите файл (txt, pdf, jpg/png, mp3, mp4)")
        
        self.ui.pushButton.clicked.connect(self.select_file)
        self.ui.pushButton_Add.clicked.connect(self.import_note)
        self.ui.pushButton_Cancel.clicked.connect(self.reject)

    def select_file(self):
        try:
            filters = "Все поддерживаемые (*.txt *.pdf *.jpg *.jpeg *.png *.mp3 *.mp4);;Все файлы (*.*)"
            file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", filters)

            if file_path:
                self.file_path = file_path
                self.note_title = os.path.splitext(os.path.basename(file_path))[0]
                
                # Упрощенная логика предпросмотра для примера
                file_size = os.path.getsize(file_path)
                self.ui.label_2.setText(f"{os.path.basename(file_path)}\nРазмер: {file_size/1024:.1f} КБ")
                self.ui.pushButton_Add.setEnabled(True)
                
                self.prepare_content()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def prepare_content(self):
        # Здесь упрощенная логика чтения, полную можно взять из оригинального файла
        ext = os.path.splitext(self.file_path)[1].lower()
        self.file_type = ext
        
        if ext == '.txt':
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.file_content = f.read()
            except:
                self.file_content = f"Ошибка чтения текстового файла {self.file_path}"
        else:
            self.file_content = f"Файл типа {ext}: {os.path.basename(self.file_path)}\n(Медиа-контент для анализа ИИ)"

    def import_note(self):
        if self.file_path:
            self.accept()

    def get_note_name(self):
        return f"{self.note_title} ({self.file_type})" if self.file_type else self.note_title

    def get_note_content(self):
        return self.file_content
