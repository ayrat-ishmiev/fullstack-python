# [file name]: styles.py

# Цвета
COLOR_BG_DARK = "#181b21"
COLOR_ACCENT = "#cbbbc4"            # Лаванда
COLOR_TEXT_MAIN = "#ffffff"         # Белый
COLOR_TEXT_DARK = "#181b21"         # Темный (для текста на светлых кнопках)
COLOR_TEXT_DIM = "#bccce0"          # Серо-голубой
COLOR_GLASS_LIGHT = "rgba(180, 160, 200, 0.25)" # Прозрачная подложка
COLOR_BORDER_LIGHT = "rgba(255, 255, 255, 0.2)"

STYLESHEET = f"""
/* === ГЛОБАЛЬНЫЕ НАСТРОЙКИ === */
QWidget {{
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    font-size: 14px;
    color: {COLOR_TEXT_MAIN};
    background: transparent;
}}

QMainWindow {{
    background: transparent;
}}

/* === ГЛАВНОЕ ПРИВЕТСТВИЕ === */
QLabel#welcome_label {{
    font-size: 38px;  /* Уменьшила, чтобы влезало */
    font-weight: 800;
    color: {COLOR_ACCENT};
    background: transparent;
    margin-bottom: 5px;
}}

QLabel#date_label {{
    font-size: 20px; 
    font-weight: 500;
    color: {COLOR_TEXT_DIM};
    background: transparent;
    margin-bottom: 20px;
}}

/* === ЗАГОЛОВОК СПИСКА ПРЕДМЕТОВ === */
QLabel#subject_title_label {{
    font-size: 16px;
    font-weight: bold;
    color: {COLOR_TEXT_MAIN};
    padding: 5px 10px;
    border: 1px solid {COLOR_BORDER_LIGHT}; 
    border-radius: 8px;
    background-color: rgba(35, 30, 45, 0.6); 
}}

/* === ГЛАВНЫЕ ОКНА И ДИАЛОГИ (Исправляет черный фон в NotesListWindow и других) === */
QDialog, QWidget[windowTitle], QWidget[class="NotesListWindow"] {{ 
    background-color: rgba(30, 30, 40, 0.9); /* Более плотный темный фон для окон */
    border: 1px solid {COLOR_BORDER_LIGHT}; 
    border-radius: 12px;
}}
/* === ОКНО "ВСЕ КОНСПЕКТЫ" (Прозрачный фон) === */
QWidget[class="AllNotesTableWindow"] {{ 
    background-color: transparent; /* Прозрачный фон для соответствия запросу */
    border: 1px solid {COLOR_BORDER_LIGHT}; 
    border-radius: 12px;
}}
/* === КОНТЕЙНЕРЫ (Списки, Таблицы, Текстовые поля внутри окон) === */
QListWidget, QTableWidget, QTextBrowser {{ 
    background-color: rgba(30, 30, 40, 0.6); /* Чуть темнее фон для читаемости */
    border: 1px solid {COLOR_BORDER_LIGHT}; 
    border-radius: 12px;
    padding: 10px;
    outline: none;
}}

/* === СПИСОК ПРЕДМЕТОВ === */
QListWidget::item {{
    padding: 8px 12px;
    margin: 3px 0; 
    border-radius: 6px;
    color: {COLOR_TEXT_MAIN}; /* БЕЛЫЙ ТЕКСТ */
    background: transparent;
}}

QListWidget::item:hover {{
    background-color: rgba(255, 255, 255, 0.15); 
    color: {COLOR_TEXT_MAIN};
}}

QListWidget::item:selected {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_TEXT_DARK}; /* Темный текст на выбранном */
    font-weight: bold;
}}

/* === КНОПКИ === */
QPushButton {{
    background-color: rgba(255, 255, 255, 0.1); /* Полупрозрачный фон */
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: {COLOR_TEXT_MAIN};
    border-radius: 6px; 
    min-height: 30px;
    padding: 6px 12px;
    font-weight: 600;
}}

/* ПРИ НАВЕДЕНИИ: Светлый фон, темный текст */
QPushButton:hover {{
    background-color: rgba(20, 20, 30, 0.9); 
    color: {COLOR_TEXT_DIM}; 
    border-color: white;
}}

QPushButton:pressed {{
    background-color: rgba(200, 200, 200, 0.9);
}}

/* НЕАКТИВНАЯ КНОПКА (Disabled) - Тусклая */
QPushButton:disabled {{
    background-color: rgba(50, 50, 50, 0.3);
    color: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(100, 100, 100, 0.2);
}}

/* === ПОЛЕ ПОИСКА / ПОЛЯ ВВОДА В ДИАЛОГАХ (темно-фиолетовый фон) === */
QLineEdit {{
    background-color: rgba(50, 40, 60, 0.7); /* Темно-фиолетовый */
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 8px;
    padding: 8px 12px;
    color: white;
    font-size: 14px;
}}

QLineEdit:focus {{
    border: 1px solid {COLOR_ACCENT};
    background-color: rgba(50, 40, 60, 0.9); /* Чуть темнее при фокусе */
}}

/* === ТАБЛИЦА === */
QHeaderView::section {{
    background-color: rgba(20, 20, 30, 0.9);
    color: {COLOR_ACCENT};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {COLOR_ACCENT};
}}

/* === МЕНЮ КОНТЕКСТА (ВОССТАНОВЛЕНО) === */
QMenu {{
    background-color: rgba(30, 30, 40, 1.0); /* Сплошной темный фон */
    border: 1px solid {COLOR_BORDER_LIGHT};
    border-radius: 8px;
    padding: 5px;
}}

QMenu::item {{
    padding: 5px 15px 5px 15px;
    margin: 2px;
    border-radius: 4px;
    color: {COLOR_TEXT_MAIN};
    min-width: 100px; 
}}

QMenu::item:selected {{
    background-color: rgba(255, 255, 255, 0.15); 
    color: {COLOR_TEXT_MAIN};
}}

QMenu::separator {{
    height: 1px;
    background: rgba(255, 255, 255, 0.2);
    margin: 4px 10px;
}}

/* === СТИЛЬ ДЕЙСТВИЯ "УДАЛИТЬ ПРЕДМЕТ" (ПО ДИНАМИЧЕСКОМУ СВОЙСТВУ) === */
/* Красный цвет текста для этого пункта */
QMenu::item[delete_item="true"] {{
    color: #e74c3c; 
}}

/* Глубокий красный фон при выборе */
QMenu::item[delete_item="true"]:selected {{
    background-color: #c0392b; 
    color: white; 
}}
"""