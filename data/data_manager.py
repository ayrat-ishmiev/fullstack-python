import os
import json
import csv
import re
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QMessageBox
from core.utils import resource_path

class DataManager:
    def __init__(self):
        self.app_dir = self.get_app_data_path()
        os.makedirs(self.app_dir, exist_ok=True)
        self.data_file = os.path.join(self.app_dir, "app_data.json")
        self.data = self.load_data()

    def get_app_data_path(self):
        app_name = "Aggregator"
        if os.name == 'nt': # Windows
            return os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), app_name)
        # Linux/Mac
        return os.path.join(os.path.expanduser('~'), '.local', 'share', app_name)

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, dict) or "subjects" not in data or "notes" not in data:
                        return {"subjects": [], "notes": {}}
                    return data
            except Exception as e:
                print(f"Error loading data: {e}")
                return {"subjects": [], "notes": {}}
        return {"subjects": [], "notes": {}}

    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def add_subject(self, subject_name):
        if subject_name and subject_name not in self.data["subjects"]:
            self.data["subjects"].append(subject_name)
            self.data["notes"][subject_name] = []
            return self.save_data()
        return False

    def get_subjects(self):
        return self.data["subjects"]

    def add_note(self, subject_name, note_name, content=""):
        if subject_name in self.data["notes"]:
            # Проверка дубликатов имен
            for note in self.data["notes"][subject_name]:
                if note["name"] == note_name:
                    return False
            
            self.data["notes"][subject_name].append({
                "name": note_name, 
                "content": content,
                "created_date": QDate.currentDate().toString("dd.MM.yyyy")
            })
            return self.save_data()
        return False

    def update_note_content(self, subject_name, note_name, new_content):
        if subject_name in self.data["notes"]:
            for note in self.data["notes"][subject_name]:
                if note["name"] == note_name:
                    note["content"] = new_content
                    return self.save_data()
        return False

    def get_notes(self, subject_name):
        return self.data["notes"].get(subject_name, [])

    def get_note_data(self, subject_name, note_name):
        for note in self.data["notes"].get(subject_name, []):
            if note["name"] == note_name: return note
        return None

    def delete_note(self, subject_name, note_name):
        if subject_name in self.data["notes"]:
            self.data["notes"][subject_name] = [n for n in self.data["notes"][subject_name] if n["name"] != note_name]
            return self.save_data()
        return False

    def delete_subject(self, subject_name):
        if subject_name in self.data["subjects"]:
            self.data["subjects"].remove(subject_name)
            if subject_name in self.data["notes"]: del self.data["notes"][subject_name]
            return self.save_data()
        return False

    def get_all_notes(self):
        all_notes = []
        for subject in self.data["subjects"]:
            for note in self.data["notes"].get(subject, []):
                all_notes.append({
                    "subject": subject, 
                    "name": note["name"], 
                    "content": note["content"],
                    "created_date": note.get("created_date", "Не указана")
                })
        return all_notes

    def smart_search(self, query, ai_client=None):
        all_notes = self.get_all_notes()
        if not all_notes: return []
        if not query.strip():
            return [{"subject": n["subject"], "note_name": n["name"], "content": n["content"],
                     "created_date": n["created_date"], "relevance_score": 100} for n in all_notes]

        if ai_client is None: return self.simple_text_search(query)

        try:
            notes_text = ""
            for i, note in enumerate(all_notes):
                # Ограничиваем длину контента для токенов
                preview = note['content'][:500].replace('\n', ' ')
                notes_text += f"ID:{i} | Subj:{note['subject']} | Name:{note['name']} | Content:{preview}...\n"

            prompt = (f"Query: '{query}'. Rate relevance (0-100) for these notes. "
                      f"Return ONLY raw JSON list: [{{'index': 0, 'relevance_score': 85}}, ...].\nData:\n{notes_text}")

            response = ai_client.chat.completions.create(
                model="google/gemini-2.5-flash-lite", # Или другой дешевый модель
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            response_text = response.choices[0].message.content.strip()

            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match: raise ValueError("No JSON found")
            
            relevance_data = json.loads(json_match.group())

            results = []
            for item in relevance_data:
                idx = item.get("index")
                if idx is not None and 0 <= idx < len(all_notes):
                    n = all_notes[idx]
                    score = item.get("relevance_score", 0)
                    if score >= 10: # Фильтр мусора
                        results.append({
                            "subject": n["subject"], 
                            "note_name": n["name"], 
                            "content": n["content"],
                            "created_date": n["created_date"],
                            "relevance_score": score
                        })
            
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            if not results: return self.simple_text_search(query)
            return results

        except Exception as e:
            print(f"AI Search failed: {e}")
            return self.simple_text_search(query)

    def simple_text_search(self, query):
        all_notes = self.get_all_notes()
        q_low = query.lower()
        results = []
        for n in all_notes:
            rel = 0
            if q_low in n["name"].lower(): rel += 40
            if q_low in n["subject"].lower(): rel += 30
            if q_low in n["content"].lower(): rel += 20
            if rel > 0:
                results.append({
                    "subject": n["subject"], 
                    "note_name": n["name"], 
                    "content": n["content"],
                    "created_date": n["created_date"], 
                    "relevance_score": min(rel, 100)
                })
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results

    def export_to_csv(self, filename=None):
        if filename is None: filename = resource_path("notes_export.csv")
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['subject', 'name', 'content', 'created_date'], delimiter=';')
                writer.writeheader()
                for n in self.get_all_notes():
                    writer.writerow(n)
            return True, f"Экспорт в {filename}"
        except Exception as e:
            return False, str(e)

    def import_from_csv(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                cnt = 0
                for row in reader:
                    subj = row.get('subject', '').strip()
                    name = row.get('name', '').strip()
                    if not subj or not name: continue

                    if subj not in self.data["subjects"]:
                        self.data["subjects"].append(subj)
                        self.data["notes"][subj] = []

                    # Простая проверка на дубликаты
                    exists = any(n["name"] == name for n in self.data["notes"][subj])
                    if not exists:
                        self.data["notes"][subj].append({
                            "name": name, 
                            "content": row.get('content', ''),
                            "created_date": row.get('created_date', '')
                        })
                        cnt += 1
                self.save_data()
                return True, f"Импортировано {cnt} новых конспектов."
        except Exception as e:
            return False, str(e)

    def get_settings(self):
        """Возвращает словарь настроек. Если их нет, возвращает дефолтные."""
        return self.data.get("settings", {
            "api_source": "default",  # 'default' или 'custom'
            "custom_key": ""
        })

    def save_settings(self, api_source, custom_key):
        """Сохраняет настройки API ключа."""
        self.data["settings"] = {
            "api_source": api_source,
            "custom_key": custom_key
        }
        return self.save_data()
