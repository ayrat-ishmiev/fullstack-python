import os
import re
from PyQt6.QtWidgets import QDialog, QMessageBox, QFileDialog, QProgressDialog, QApplication
from PyQt6.QtCore import Qt, QTimer
from ui.import_note_dialog_ui import Ui_Dialog
from services.ai_service import AIService


class ImportNoteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.file_path = None
        self.note_content = ""
        self.note_title = ""
        self.file_type = ""

        self.progress_dialog = None
        self.progress_timer = None
        self.dots = 0

        self.ui.pushButton_Add.setEnabled(False)
        self.ui.label.setText("Поддерживается: TXT, PDF, изображения, аудио, видео")

        self.ui.pushButton.clicked.connect(self.select_file)
        self.ui.pushButton_Add.clicked.connect(self.process_and_accept)
        self.ui.pushButton_Cancel.clicked.connect(self.reject)

    def select_file(self):
        filters = "Все форматы (*.txt *.md *.pdf *.jpg *.jpeg *.png *.webp *.mp3 *.wav *.ogg *.m4a *.aac *.amr *.mp4 *.avi *.mov *.webm *.mkv);;Текст (*.txt *.md *.pdf);;Изображения (*.jpg *.jpeg *.png *.webp);;Аудио (*.mp3 *.wav *.ogg *.m4a *.aac *.amr);;Видео (*.mp4 *.mov *.avi *.webm *.mkv)"
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", filters)

        if path:
            self.file_path = path
            self.file_type = self._detect_type(path)

            size_mb = os.path.getsize(path) / (1024 * 1024)
            type_rus = {
                'text': 'Текстовый документ',
                'pdf': 'Документ PDF',
                'image': 'Изображение',
                'audio': 'Аудио',
                'video': 'Видео',
                'unknown': 'Неизвестный формат'
            }.get(self.file_type, 'Файл')

            self.ui.label_2.setText(f"{os.path.basename(path)}\nТип: {type_rus}\nРазмер: {size_mb:.2f} МБ")
            self.ui.pushButton_Add.setEnabled(True)

            # Меняем текст кнопки в зависимости от типа
            if self.file_type == 'text':
                self.ui.pushButton_Add.setText("Добавить")
            else:
                self.ui.pushButton_Add.setText("Обработать нейросетью")

    def _detect_type(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.txt', '.md']: return 'text'
        if ext in ['.pdf']: return 'pdf'
        if ext in ['.jpg', '.jpeg', '.png', '.webp']: return 'image'
        if ext in ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.amr']: return 'audio'
        if ext in ['.mp4', '.avi', '.mov', '.webm', '.mkv']: return 'video'
        return 'unknown'

    def process_and_accept(self):
        if not self.file_path: return

        try:
            if self.file_type == 'text':
                self._read_text_file()
            elif self.file_type in ['image', 'audio', 'video', 'pdf']:
                self._process_media_with_ai()
            else:
                self.note_title = os.path.basename(self.file_path)
                self.note_content = f"Файл: {self.note_title}\n(Формат не поддерживается для анализа)"

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка обработки", f"Не удалось обработать файл:\n{str(e)}")

    def _read_text_file(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.note_content = f.read()
            self._extract_title_from_content()
        except UnicodeDecodeError:
            self.note_content = "Ошибка кодировки файла. Попробуйте UTF-8."
            self.note_title = os.path.basename(self.file_path)

    def _process_media_with_ai(self):
        """Вызов соответствующего метода AI Service."""
        op_map = {
            'image': ('Распознавание текста', AIService.recognize_image),
            'audio': ('Транскрибация аудио', AIService.transcribe_audio),
            'video': ('Анализ видеоурока', AIService.transcribe_video),
            'pdf': ('Обработка PDF', AIService.analyze_pdf)
        }

        op_name, ai_method = op_map[self.file_type]

        self._show_progress(op_name)

        try:
            QApplication.processEvents()

            # Вызов конкретного метода (audio vs video теперь разделены)
            result_text = ai_method(self.file_path)

            self.note_content = result_text
            self._extract_title_from_content()

        finally:
            self._hide_progress()

    def _extract_title_from_content(self):
        match = re.search(r'^#\s+(.+)$', self.note_content, re.MULTILINE)
        if match:
            self.note_title = match.group(1).strip()
        else:
            self.note_title = os.path.splitext(os.path.basename(self.file_path))[0]
            if self.note_content and not self.note_content.startswith("#"):
                self.note_content = f"# {self.note_title}\n\n{self.note_content}"

    def get_note_name(self):
        return self.note_title

    def get_note_content(self):
        return self.note_content

    # --- Progress UI ---
    def _show_progress(self, operation_text):
        self.progress_dialog = QProgressDialog(
            f"{operation_text}...\nАнализ больших файлов может занять до 1-2 минут.",
            None, 0, 0, self
        )
        self.progress_dialog.setWindowTitle("Обработка нейросетью")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setRange(0, 0)
        self.progress_dialog.show()

        self.dots = 0
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(lambda: self._update_progress_label(operation_text))
        self.progress_timer.start(500)

    def _update_progress_label(self, base_text):
        if self.progress_dialog:
            self.dots = (self.dots + 1) % 4
            self.progress_dialog.setLabelText(f"{base_text}{'.' * self.dots}\nПожалуйста, подождите.")

    def _hide_progress(self):
        if self.progress_timer: self.progress_timer.stop()
        if self.progress_dialog: self.progress_dialog.close()