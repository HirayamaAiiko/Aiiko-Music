import urllib.request
import urllib.parse
import json
import logging
import sqlite3
import os
import threading
from collections import OrderedDict
from PyQt6.QtCore import QThread, pyqtSignal
from config import INSTALL_ROOT
DB_DIR = os.path.join(INSTALL_ROOT, 'database')
DB_PATH = os.path.join(DB_DIR, 'translations.db')
_local = threading.local()
_db_initialized = False
_db_lock = threading.Lock()
def _get_conn():
    global _db_initialized
    if not _db_initialized:
        with _db_lock:
            if not _db_initialized:
                os.makedirs(DB_DIR, exist_ok=True)
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute('''
                        CREATE TABLE IF NOT EXISTS translations (
                            hash_key TEXT PRIMARY KEY,
                            translated_text TEXT
                        )
                    ''')
                _db_initialized = True
    conn = getattr(_local, 'conn', None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn = conn
    return conn
_MAX_CACHE = 500
class _LRUCache(OrderedDict):
    def get_val(self, key):
        if key in self:
            self.move_to_end(key)
            return self[key]
        return None
    def set_val(self, key, value):
        if key in self:
            self.move_to_end(key)
        self[key] = value
        if len(self) > _MAX_CACHE:
            self.popitem(last=False)
memory_cache = _LRUCache()
def _make_key(text, lang):
    return f"{lang}:{text}"
def get_cached_translation(text, lang):
    key = _make_key(text, lang)
    cached = memory_cache.get_val(key)
    if cached is not None:
        return cached
    try:
        conn = _get_conn()
        row = conn.execute(
            'SELECT translated_text FROM translations WHERE hash_key=?', (key,)
        ).fetchone()
        if row:
            memory_cache.set_val(key, row[0])
            return row[0]
    except Exception as e:
        logging.error(f"Translation DB read error: {e}")
    return None
def preload_cached_translations(texts, lang):
    keys = [_make_key(t, lang) for t in texts if t.strip()]
    keys_to_fetch = [k for k in keys if memory_cache.get_val(k) is None]
    if not keys_to_fetch:
        return
    try:
        conn = _get_conn()
        chunk_size = 500
        for i in range(0, len(keys_to_fetch), chunk_size):
            chunk = keys_to_fetch[i:i + chunk_size]
            placeholders = ','.join(['?'] * len(chunk))
            cursor = conn.execute(
                f"SELECT hash_key, translated_text FROM translations WHERE hash_key IN ({placeholders})", 
                chunk
            )
            for key, translated_text in cursor.fetchall():
                memory_cache.set_val(key, translated_text)
    except Exception as e:
        logging.error(f"Translation DB bulk read error: {e}")
def save_cached_translation(text, lang, translated_text):
    key = _make_key(text, lang)
    memory_cache.set_val(key, translated_text)
    try:
        conn = _get_conn()
        conn.execute(
            'INSERT OR REPLACE INTO translations (hash_key, translated_text) VALUES (?, ?)',
            (key, translated_text)
        )
        conn.commit()
    except Exception as e:
        logging.error(f"Translation DB write error: {e}")
class TranslationThread(QThread):
    finished_translation = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    def __init__(self, lyrics_data, target_lang='es', is_synced=True):
        super().__init__()
        self.lyrics_data = lyrics_data
        self.target_lang = target_lang
        self.is_synced = is_synced
        self.running = True
    def stop(self):
        self.running = False
    def _translate_api(self, block_text):
        encoded_text = urllib.parse.quote(block_text)
        url = (
            f"https://translate.googleapis.com/translate_a/single"
            f"?client=dict-chrome-ex&sl=auto&tl={self.target_lang}&dt=t&q={encoded_text}"
        )
        import logging
        logging.info(f"[Translator] Calling API with URL length: {len(url)}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                raw_data = response.read().decode('utf-8')
                logging.info(f"[Translator] API Response received, length: {len(raw_data)}")
                res_json = json.loads(raw_data)
                if not res_json or not isinstance(res_json, list) or len(res_json) == 0:
                    logging.warning(f"[Translator] Unexpected JSON format: {raw_data[:200]}")
                    return ""
                translated_str = ""
                if isinstance(res_json[0], list):
                    for part in res_json[0]:
                        if part and part[0]:
                            translated_str += part[0]
                logging.info(f"[Translator] Translation successful, length: {len(translated_str)}")
                return translated_str
        except urllib.error.HTTPError as e:
            logging.error(f"[Translator] HTTPError {e.code}: {e.reason} for URL")
            if hasattr(self, 'error_occurred'): self.error_occurred.emit(f"Error 429: Límite excedido de API." if e.code == 429 else f"Fallo en la conexión HTTP ({e.code})")
            raise
        except Exception as e:
            logging.error(f"[Translator] Exception: {e}")
            if hasattr(self, 'error_occurred'): self.error_occurred.emit("Error de red al contactar Google Translate.")
            raise
    def run(self):
        translated_lines = []
        total = len(self.lyrics_data)
        if total == 0:
            self.finished_translation.emit([])
            return
        texts_to_preload = [item[1] for item in self.lyrics_data]
        preload_cached_translations(texts_to_preload, self.target_lang)
        if not self.is_synced:
            self._run_unsynced(translated_lines)
        else:
            self._run_synced(translated_lines)
        if self.running:
            self.finished_translation.emit(translated_lines)
    def _run_unsynced(self, translated_lines):
        to_translate = [item[1] for item in self.lyrics_data if item[1].strip()]
        combined_text = "\n".join(to_translate)
        try:
            if to_translate:
                cached = get_cached_translation(combined_text, self.target_lang)
                if cached:
                    translated_combined = cached
                else:
                    translated_combined = self._translate_api(combined_text)
                    save_cached_translation(combined_text, self.target_lang, translated_combined)
            else:
                translated_combined = ""
            translated_parts = [p.strip() for p in translated_combined.split('\n')]
            part_idx = 0
            for idx, orig_text in self.lyrics_data:
                if orig_text.strip():
                    t_text = translated_parts[part_idx] if part_idx < len(translated_parts) else orig_text
                    part_idx += 1
                else:
                    t_text = ""
                translated_lines.append((idx, orig_text, t_text))
        except Exception as e:
            logging.debug(f"Error translating unsynced block: {e}")
            for idx, orig_text in self.lyrics_data:
                translated_lines.append((idx, orig_text, ""))
    def _run_synced(self, translated_lines):
        batch_size = 20
        batches = [self.lyrics_data[i:i + batch_size] for i in range(0, len(self.lyrics_data), batch_size)]
        for batch in batches:
            if not self.running:
                break
            batch_results = [None] * len(batch)
            to_translate_texts = []
            mapping_to_batch = []
            for i, (time_ms, orig_text) in enumerate(batch):
                if not self.running:
                    break
                if not orig_text.strip():
                    batch_results[i] = (time_ms, orig_text, "")
                    continue
                cached = get_cached_translation(orig_text, self.target_lang)
                if cached is not None:
                    batch_results[i] = (time_ms, orig_text, cached)
                else:
                    mapping_to_batch.append(i)
                    to_translate_texts.append(orig_text)
            if to_translate_texts and self.running:
                combined_text = " \n ".join(to_translate_texts)
                try:
                    translated_combined = self._translate_api(combined_text)
                    translated_parts = [p.strip() for p in translated_combined.split('\n')]
                    for i, orig_text in enumerate(to_translate_texts):
                        t_text = translated_parts[i] if i < len(translated_parts) else orig_text
                        batch_idx = mapping_to_batch[i]
                        time_ms = batch[batch_idx][0]
                        batch_results[batch_idx] = (time_ms, orig_text, t_text)
                        if t_text and t_text != orig_text:
                            save_cached_translation(orig_text, self.target_lang, t_text)
                except Exception as e:
                    logging.debug(f"Error translating batch: {e}")
                    for i, orig_text in enumerate(to_translate_texts):
                        batch_idx = mapping_to_batch[i]
                        time_ms = batch[batch_idx][0]
                        batch_results[batch_idx] = (time_ms, orig_text, "")
                QThread.msleep(200)
            translated_lines.extend(batch_results)