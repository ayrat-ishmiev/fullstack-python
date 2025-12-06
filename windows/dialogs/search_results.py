import csv
from PyQt6.QtWidgets import QDialog, QTableWidgetItem, QHeaderView, QMenu, QMessageBox, QApplication, QFileDialog
from PyQt6.QtCore import Qt, QDate
from PyQt6 import QtGui
from ui.search_results_ui import Ui_SearchResultsDialog

class SearchResultsWindow(QDialog):
    def __init__(self, search_query, search_results, data_manager, main_window, parent=None):
        super().__init__(parent)
        self.ui = Ui_SearchResultsDialog()
        self.ui.setupUi(self)

        self.search_query = search_query
        self.results = search_results
        self.data_manager = data_manager
        self.main_window = main_window

        self.ui.label_query.setText(f"Запрос: {search_query}")
        self.ui.label_count.setText(f"Найдено: {len(search_results)}")
        
        self.load_results()
        
        self.ui.pushButton_close.clicked.connect(self.close)
        self.ui.pushButton_export.clicked.connect(self.export_results)
        self.ui.tableWidget.cellDoubleClicked.connect(self.open_note)
        
        # Context Menu setup
        self.ui.tableWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.tableWidget.customContextMenuRequested.connect(self.show_context_menu)

    def load_results(self):
        self.ui.tableWidget.setRowCount(len(self.results))
        for row, res in enumerate(self.results):
            # 0: Subject
            item_sub = QTableWidgetItem(res["subject"])
            item_sub.setData(Qt.ItemDataRole.UserRole, res) # Store full data
            self.ui.tableWidget.setItem(row, 0, item_sub)
            
            # 1: Name
            self.ui.tableWidget.setItem(row, 1, QTableWidgetItem(res["note_name"]))
            
            # 2: Date
            self.ui.tableWidget.setItem(row, 2, QTableWidgetItem(res["created_date"]))
            
            # 3: Relevance
            score = res.get("relevance_score", 0)
            item_rel = QTableWidgetItem(f"{score:.1f}%")
            if score >= 80: color = QtGui.QColor(46, 204, 113)
            elif score >= 60: color = QtGui.QColor(241, 196, 15)
            else: color = QtGui.QColor(231, 76, 60)
            item_rel.setForeground(QtGui.QBrush(color))
            self.ui.tableWidget.setItem(row, 3, item_rel)

    def show_context_menu(self, pos):
        item = self.ui.tableWidget.itemAt(pos)
        if item:
            menu = QMenu(self)
            act_open = menu.addAction("📖 Открыть")
            act_copy = menu.addAction("📋 Копировать инфо")
            
            action = menu.exec(self.ui.tableWidget.mapToGlobal(pos))
            if action == act_open:
                self.open_note(item.row(), 0)
            elif action == act_copy:
                data = self.ui.tableWidget.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
                QApplication.clipboard().setText(f"{data['subject']} - {data['note_name']}")

    def open_note(self, row, col):
        data = self.ui.tableWidget.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.close()
        self.main_window.open_subject_with_note(data["subject"], data["note_name"])

    def export_results(self):
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт", "search_results.csv", "CSV (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=['subject', 'note_name', 'score'], delimiter=';')
                    writer.writeheader()
                    for r in self.results:
                        writer.writerow({'subject': r['subject'], 'note_name': r['note_name'], 'score': r.get('relevance_score')})
                QMessageBox.information(self, "OK", "Экспорт выполнен")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", str(e))
