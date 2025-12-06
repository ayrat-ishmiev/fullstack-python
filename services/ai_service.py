import base64
import os
from openai import OpenAI
from config.keys import OPENROUTER_KEY


class AIService:
    _instance = None
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_KEY,
            )
        return cls._client

    @staticmethod
    def _encode_file(file_path):
        with open(file_path, "rb") as file:
            return base64.b64encode(file.read()).decode('utf-8')

    @staticmethod
    def get_mime_type(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        # Аудио
        if ext in ['.mp3']: return 'audio/mpeg'
        if ext in ['.wav']: return 'audio/wav'
        if ext in ['.ogg']: return 'audio/ogg'
        if ext in ['.m4a', '.aac']: return 'audio/mp4'
        # Видео
        if ext in ['.mp4']: return 'video/mp4'
        if ext in ['.avi']: return 'video/x-msvideo'
        if ext in ['.mov']: return 'video/quicktime'
        if ext in ['.webm']: return 'video/webm'
        if ext in ['.mkv']: return 'video/x-matroska'
        # Изображения
        if ext in ['.jpg', '.jpeg']: return 'image/jpeg'
        if ext in ['.png']: return 'image/png'
        if ext in ['.webp']: return 'image/webp'
        return None

    @classmethod
    def recognize_image(cls, image_path):
        client = cls.get_client()
        base64_image = cls._encode_file(image_path)
        mime_type = cls.get_mime_type(image_path) or "image/jpeg"

        prompt = """На изображении рукописный текст на русском языке. Распознай его.
        СТРОГОЕ ТРЕБОВАНИЕ: Верни ТОЛЬКО текст в формате Markdown. Без вступлений.
        1. Определи заголовок текста и поставь его в начале как заголовок первого уровня #.
        2. Сохрани структуру (списки, таблицы).
        3. Исправляй ошибки распознавания."""

        response = client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                    ]
                }
            ]
        )
        return response.choices[0].message.content.strip()

    @classmethod
    def transcribe_audio(cls, audio_path):
        client = cls.get_client()
        base64_audio = cls._encode_file(audio_path)
        mime_type = cls.get_mime_type(audio_path)

        if not mime_type or 'audio' not in mime_type:
            if audio_path.endswith('.m4a'):
                mime_type = 'audio/mp4'
            else:
                raise ValueError(f"Это не аудиофайл: {audio_path}")

        # ОБНОВЛЕННЫЙ ПРОМПТ ДЛЯ АУДИО
        prompt = """Ты — автоматический транскрибатор. Твоя задача — вернуть только конспект.

        СТРОГИЕ ПРАВИЛА ВЫВОДА:
        1. ЗАПРЕЩЕНО писать вводные слова (например: 'Вот конспект', 'Конечно').
        2. ПЕРВАЯ СТРОКА ответа должна быть заголовком: '# Тема лекции'.
        3. Используй Markdown для форматирования.
        4. Язык: Русский."""

        alt_payload = [
            {"type": "text", "text": prompt},
            {"type": "audio_url", "audio_url": {"url": f"data:{mime_type};base64,{base64_audio}"}}
        ]

        response = client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{"role": "user", "content": alt_payload}],
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()

    @classmethod
    def transcribe_video(cls, video_path):
        client = cls.get_client()
        base64_video = cls._encode_file(video_path)
        mime_type = cls.get_mime_type(video_path)

        if not mime_type or 'video' not in mime_type:
            raise ValueError(f"Это не видеофайл: {video_path}")

        # ОБНОВЛЕННЫЙ ПРОМПТ ДЛЯ ВИДЕО
        prompt = """Ты — система компьютерного зрения и анализа речи. Составь конспект.

        КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА ФОРМАТА:
        1. В ответе должен быть ТОЛЬКО Markdown код. 
        2. НИКАКИХ приветствий, вводных фраз ("Вот конспект", "Анализ видео") или заключений.
        3. ПЕРВАЯ строка ответа ОБЯЗАНА быть заголовком первого уровня: '# Название видеоурока'.

        Инструкции по содержанию:
        1. Совмещай аудио (речь) и видео (слайды/доска). Текст с доски имеет приоритет для формул.
        2. Структурируй через '## Разделы'.
        3. Используй списки и жирный шрифт для терминов.
        """

        payload = [
            {"type": "text", "text": prompt},
            {"type": "video_url", "video_url": {"url": f"data:{mime_type};base64,{base64_video}"}}
        ]

        response = client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{"role": "user", "content": payload}],
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()

    @classmethod
    def generate_study_note(cls, topic, subject_context=""):
        """Генерация конспекта с нуля по теме."""
        client = cls.get_client()

        prompt = f"""Напиши подробный учебный конспект на тему: "{topic}".
            Предмет: {subject_context}.

            СТРУКТУРА КОНСПЕКТА (Markdown):
            1. # {topic} (Заголовок)
            2. ## Введение (Краткая суть)
            3. ## Основные понятия (Термины и определения)
            4. ## Подробный разбор (Тезисы, формулы, примеры)
            5. ## Заключение / Выводы

            ТРЕБОВАНИЯ:
            - Язык: Русский.
            - ВЕРНИ ЧИСТЫЙ ТЕКСТ. НЕ оборачивай ответ в тройные кавычки (```markdown).
            - Используй жирный шрифт для важных терминов.
            - Используй списки для перечислений.
            - Стиль: Академический, но понятный."""

        response = client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()