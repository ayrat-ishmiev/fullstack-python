from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextBrowser, QLineEdit, QPushButton, QApplication
from PyQt6.QtCore import Qt
from ui.ask_ai_dialog_ui import Ui_Form
from services.ai_service import AIService
from core.utils import render_markdown # <--- Импорт

class AskAIDialog(QDialog): # Наследуем QDialog, а не QWidget, чтобы работал exec()
    def __init__(self, note_name, note_content, parent=None):
        super().__init__(parent)
        # Мы можем использовать ui файл, но в оригинале он был QWidget, 
        # а в коде main.py переопределялся вручную. 
        # Используем логику ручной сборки из main.py для надежности,
        # так как ui файл AskAiDialog был прост.
        
        self.note_name = note_name
        self.note_content = note_content
        self.setWindowTitle(f"Вопрос: {note_name}")
        self.resize(800, 600)

        # UI Elements (Manual reconstruction per original code logic)
        self.title_label = QLabel(note_name, self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.greeting_browser = QTextBrowser(self)
        self.greeting_browser.setHtml("<p>Задайте вопрос по этому конспекту.</p>")
        self.greeting_browser.setMaximumHeight(80)
        
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setPlaceholderText("Ваш вопрос...")
        
        self.pushButton = QPushButton("✨ Спросить ИИ", self)
        self.pushButton.clicked.connect(self.ask_question)
        
        self.textBrowser = QTextBrowser(self)
        self.textBrowser.setHtml("<h4>Ответ будет здесь.</h4>")

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.greeting_browser)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.pushButton)
        layout.addWidget(self.textBrowser)

    def ask_question(self):
        q = self.lineEdit.text().strip()
        if not q: return

        self.pushButton.setEnabled(False)
        self.pushButton.setText("⏳ Думаю...")

        # Показываем вопрос
        self.textBrowser.setHtml(f"<b>В: {q}</b><br><i>Ожидание ответа...</i>")
        QApplication.processEvents()

        try:
            client = AIService.get_client()
            resp = client.chat.completions.create(
                model="google/gemini-2.5-flash",
                messages=[{"role": "user", "content": f"Context:\n{self.note_content}\n\nQuestion: {q}"}]
            )
            ans = resp.choices[0].message.content

            # Рендерим Markdown ответа
            formatted_ans = render_markdown(ans)

            # Собираем HTML для чата
            final_html = f"""
            <div style="color: #ccc; margin-bottom: 10px;"><b>Вопрос:</b> {q}</div>
            <hr>
            <div>{formatted_ans}</div>
            """
            self.textBrowser.setHtml(final_html)

        except Exception as e:
            self.textBrowser.setHtml(f"Ошибка: {e}")
        finally:
            self.pushButton.setEnabled(True)
            self.pushButton.setText("✨ Спросить ИИ")
            self.lineEdit.clear()