import sys
import os
import markdown
from datetime import datetime

def resource_path(relative_path):
    """Получает абсолютный путь к ресурсу."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_formatted_date():
    """
    Возвращает текущую дату в формате: 'Суббота, 6 декабря 2025'.
    Использует словари для гарантии правильного падежа и регистра.
    """
    now = datetime.now()

    days = {
        0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг",
        4: "Пятница", 5: "Суббота", 6: "Воскресенье"
    }

    months = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
        7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }

    # Формируем строку
    return f"{days[now.weekday()]}, {now.day} {months[now.month]} {now.year}"

def render_markdown(text):
    """
    Конвертирует Markdown в HTML с CSS стилями для темной темы.
    Использует расширения для таблиц и блоков кода.
    """
    if not text:
        return ""

    # Конвертация MD -> HTML
    # extra включает: tables, fenced_code (блоки кода ```), footnotes и др.
    html_content = markdown.markdown(text, extensions=['extra', 'nl2br'])

    # CSS стили для QTextBrowser (он поддерживает ограниченный набор CSS 2.1)
    # Цвета подобраны под вашу тему из styles.py
    style = """
    <style>
        body { 
            font-family: 'Segoe UI', sans-serif; 
            font-size: 14px; 
            color: #e0e0e0; 
        }
        h1 { 
            color: #cbbbc4; 
            font-size: 22px; 
            font-weight: bold;
            margin-top: 20px; 
            margin-bottom: 10px;
            border-bottom: 1px solid #555;
            padding-bottom: 5px;
        }
        h2 { 
            color: #dcdcdc; 
            font-size: 18px; 
            font-weight: bold; 
            margin-top: 15px; 
            margin-bottom: 8px; 
        }
        h3 { 
            color: #a0a0a0; 
            font-size: 16px; 
            font-weight: bold; 
            margin-top: 10px; 
        }
        p { 
            margin-bottom: 10px; 
            line-height: 1.4; 
        }
        strong { 
            color: #ffffff; 
            font-weight: bold; 
        }
        em { 
            color: #cbbbc4; 
            font-style: italic; 
        }
        code { 
            background-color: #2d3436; 
            color: #fab1a0; 
            padding: 2px 4px; 
            border-radius: 3px; 
            font-family: Consolas, monospace;
        }
        pre { 
            background-color: #252525; 
            color: #dfe6e9; 
            padding: 10px; 
            border: 1px solid #444;
            border-radius: 5px;
            margin: 10px 0;
        }
        ul, ol { 
            margin-left: 20px; 
            margin-bottom: 10px; 
        }
        li { 
            margin-bottom: 4px; 
        }
        a { 
            color: #74b9ff; 
            text-decoration: none; 
        }
        blockquote {
            border-left: 4px solid #cbbbc4;
            padding-left: 10px;
            color: #999;
            margin: 10px 0;
        }
    </style>
    """

    return f"<html><head>{style}</head><body>{html_content}</body></html>"