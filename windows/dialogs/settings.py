from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QRadioButton, QLineEdit, QPushButton, QHBoxLayout, \
    QMessageBox, QGroupBox
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.resize(450, 250)
        self.data_manager = data_manager

        # Загружаем текущие настройки
        settings = self.data_manager.get_settings()
        self.current_source = settings.get("api_source", "default")
        self.current_custom_key = settings.get("custom_key", "")

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Группа настроек API
        group = QGroupBox("Ключ нейросети (API Key)")
        group_layout = QVBoxLayout()

        # Радиокнопка: По умолчанию
        self.rb_default = QRadioButton("Использовать встроенный ключ (Бесплатно/Лимит)")
        self.rb_default.toggled.connect(self.toggle_input)
        group_layout.addWidget(self.rb_default)

        # Радиокнопка: Свой ключ
        self.rb_custom = QRadioButton("Использовать свой ключ (OpenRouter)")
        self.rb_custom.toggled.connect(self.toggle_input)
        group_layout.addWidget(self.rb_custom)

        # Поле ввода ключа
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("sk-or-v1-...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)  # Скрываем символы
        group_layout.addWidget(self.key_input)

        group.setLayout(group_layout)
        layout.addWidget(group)

        layout.addStretch()

        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

        # Установка начального состояния
        if self.current_source == "custom":
            self.rb_custom.setChecked(True)
            self.key_input.setText(self.current_custom_key)
            self.key_input.setEnabled(True)
        else:
            self.rb_default.setChecked(True)
            self.key_input.setText(self.current_custom_key)  # Показываем сохраненный, даже если не активен
            self.key_input.setEnabled(False)

    def toggle_input(self):
        """Включает/выключает поле ввода в зависимости от радиокнопки."""
        self.key_input.setEnabled(self.rb_custom.isChecked())
        if self.rb_custom.isChecked():
            self.key_input.setFocus()

    def save_settings(self):
        source = "custom" if self.rb_custom.isChecked() else "default"
        key = self.key_input.text().strip()

        if source == "custom" and not key:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите API ключ.")
            return

        # Сохраняем в файл
        self.data_manager.save_settings(source, key)
        self.accept()