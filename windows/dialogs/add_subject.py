from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import Qt
from ui.add_subject_dialog_ui import Ui_Dialog
from core.exceptions import SubjectValidationError

class AddSubjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.has_unsaved_changes = False

        self.ui.lineEdit.textChanged.connect(self.on_text_changed)
        self.ui.pushButton_Add.setEnabled(False)
        self.ui.pushButton_Add.clicked.connect(self.add_subject)
        self.ui.pushButton_Cancel.clicked.connect(self.cancel)

    def on_text_changed(self):
        has_text = bool(self.ui.lineEdit.text().strip())
        self.ui.pushButton_Add.setEnabled(has_text)
        self.has_unsaved_changes = has_text

    def get_subject_name(self):
        return self.ui.lineEdit.text().strip()

    def add_subject(self):
        try:
            subject_name = self.get_subject_name()
            if not subject_name:
                raise SubjectValidationError("Название не может быть пустым")
            if len(subject_name) < 2:
                raise SubjectValidationError("Минимум 2 символа")
            if len(subject_name) > 50:
                raise SubjectValidationError("Максимум 50 символов")
            
            forbidden = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            if any(char in subject_name for char in forbidden):
                raise SubjectValidationError("Содержит запрещенные символы")

            self.has_unsaved_changes = False
            self.accept()

        except SubjectValidationError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def cancel(self):
        if self.has_unsaved_changes:
            reply = QMessageBox.question(self, "Подтверждение", "Несохраненные изменения. Закрыть?", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.reject()
        else:
            self.reject()
