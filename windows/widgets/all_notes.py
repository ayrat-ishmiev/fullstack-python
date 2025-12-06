from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QTableWidgetItem
from ui.all_notes_table_ui import Ui_Form

class AllNotesTableWindow(QWidget):
    def __init__(self, data_manager, main_window, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.data_manager = data_manager
        self.main_window = main_window

        # Add Import/Export buttons programmatically to layout
        layout = self.ui.verticalLayout
        btn_layout = QVBoxLayout()
        self.btn_export = QPushButton("📤 Экспорт CSV")
        self.btn_import = QPushButton("📥 Импорт CSV")
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_import)
        layout.addLayout(btn_layout)

        self.btn_export.clicked.connect(self.export_csv)
        self.btn_import.clicked.connect(self.import_csv)
        self.ui.tableWidget.cellDoubleClicked.connect(self.on_row_double_clicked)

        self.load_data()

    def load_data(self):
        notes = self.data_manager.get_all_notes()
        self.ui.tableWidget.setRowCount(len(notes))
        for r, n in enumerate(notes):
            self.ui.tableWidget.setItem(r, 0, QTableWidgetItem(n["subject"]))
            self.ui.tableWidget.setItem(r, 1, QTableWidgetItem(n["name"]))
            self.ui.tableWidget.setItem(r, 2, QTableWidgetItem(n["created_date"]))

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт", "notes.csv", "CSV (*.csv)")
        if path:
            ok, msg = self.data_manager.export_to_csv(path)
            if ok: QMessageBox.information(self, "OK", msg)
            else: QMessageBox.warning(self, "Ошибка", msg)

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Импорт", "", "CSV (*.csv)")
        if path:
            ok, msg = self.data_manager.import_from_csv(path)
            if ok: 
                QMessageBox.information(self, "OK", msg)
                self.load_data()
                self.main_window.load_subjects()
            else: 
                QMessageBox.warning(self, "Ошибка", msg)

    def on_row_double_clicked(self, row, col):
        subj = self.ui.tableWidget.item(row, 0).text()
        name = self.ui.tableWidget.item(row, 1).text()
        self.close()
        self.main_window.open_subject_with_note(subj, name)
