import os
import sys
import json
import logging
from PyQt6.QtCore import QObject, pyqtSignal
class _LanguageManager(QObject):
    language_changed = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.current_lang = "es"                                                
        self.translations = {}
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            self.languages_dir = os.path.join(os.path.dirname(sys.executable), "languages")
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.languages_dir = os.path.join(base_dir, "languages")
        if not os.path.exists(self.languages_dir):
            try:
                os.makedirs(self.languages_dir, exist_ok=True)
            except Exception:
                pass
        if is_frozen:
            internal_langs = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)), "languages")
            if not os.path.exists(internal_langs):
                internal_langs = os.path.join(os.path.dirname(sys.executable), "appdata", "languages")
            if os.path.exists(internal_langs) and self.languages_dir != internal_langs:
                try:
                    import shutil
                    if not os.listdir(self.languages_dir):
                        for item in os.listdir(internal_langs):
                            s = os.path.join(internal_langs, item)
                            d = os.path.join(self.languages_dir, item)
                            if os.path.isfile(s):
                                shutil.copy2(s, d)
                except Exception as e:
                    logging.error(f"Error copiando idiomas internos: {e}")
    def load_language(self, lang_code: str):
        self.current_lang = lang_code
        self.translations.clear()
        if lang_code == "es":
            logging.info("LanguageManager: Idioma base (es) cargado.")
            self.language_changed.emit(lang_code)
            return True
        file_path = os.path.join(self.languages_dir, f"{lang_code}.json")
        if not os.path.exists(file_path):
            logging.warning(f"LanguageManager: No se encontró el archivo de idioma '{file_path}'. Usando español por defecto.")
            self.language_changed.emit(lang_code)
            return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            logging.info(f"LanguageManager: Idioma '{lang_code}' cargado exitosamente con {len(self.translations)} traducciones.")
            self.language_changed.emit(lang_code)
            return True
        except Exception as e:
            logging.error(f"LanguageManager: Error cargando el idioma '{lang_code}': {e}")
            self.language_changed.emit(lang_code)
            return False
    def get_available_languages(self):
        langs = {"es": "Español"}                                     
        if os.path.exists(self.languages_dir):
            for file in os.listdir(self.languages_dir):
                if file.endswith('.json') and file not in ('base.json', 'es.json'):
                    code = file.replace('.json', '')
                    try:
                        with open(os.path.join(self.languages_dir, file), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if "_meta" in data and "language_name" in data["_meta"]:
                                langs[code] = data["_meta"]["language_name"]
                            else:
                                langs[code] = code.upper()
                    except Exception:
                        langs[code] = code.upper()
        return langs
    def translate(self, text: str) -> str:
        if not text:
            return text
        translated = self.translations.get(text)
        if translated is not None:
            return translated
        return text
lang_manager = _LanguageManager()
def tr(text: str) -> str:
    return lang_manager.translate(text)