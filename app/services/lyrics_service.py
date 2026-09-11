import os
import re
import html
import logging
import bisect
import hashlib
import json
from PyQt6.QtWidgets import QListWidgetItem, QAbstractItemView, QListWidget
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRunnable, QThreadPool, pyqtSignal, QObject, QThread
from qfluentwidgets import isDarkTheme
import theme_manager
from settings_manager import settings
from core.language_manager import tr
from config import LYRICS_CACHE_DIR
from PyQt6.QtCore import QEvent
class LyricsResizeFilter(QObject):
    def __init__(self, panel, item):
        super().__init__(panel)
        self.panel = panel
        self.item = item
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Resize:
            h = self.panel.viewport().height()
            from PyQt6.QtCore import QSize
            self.item.setSizeHint(QSize(self.panel.viewport().width(), max(h - 20, 100)))
        return False
FONT_SIZE_INACTIVE = 16
FONT_SIZE_ACTIVE = 24
def _parse_timestamp(m_str, s_str, ms_str):
    m = int(m_str)
    s = int(s_str)
    millis = 0
    if ms_str:
        if len(ms_str) == 1:
            millis = int(ms_str) * 100
        elif len(ms_str) == 2:
            millis = int(ms_str) * 10
        else:
            millis = int(ms_str[:3])
    return (m * 60000) + (s * 1000) + millis
class LyricsLoaderWorker(QThread):
    finished_load = pyqtSignal(list, list, object, object, dict)
    def __init__(self, track, base_path, clean_text_func, fix_mojibake_func, parent=None):
        super().__init__(parent)
        self.track = track
        self.base_path = base_path
        self._clean_text = clean_text_func
        self._fix_mojibake = fix_mojibake_func
        unique_string = f"{self.track.filepath}_{getattr(self.track, 'mtime', 0)}"
        self.track_hash = hashlib.md5(unique_string.encode('utf-8')).hexdigest()
        self.cache_file = os.path.join(LYRICS_CACHE_DIR, f"{self.track_hash}.json")
    def run(self):
        lyrics_sync = []
        unsynced_lyrics = []
        lines = []
        has_sylt = False
        lyrics_source = None
        cached_translations = {}
        valid_exts = ['.lrc', '.srt', '.txt']
        found_file = None
        for ext in valid_exts:
            if os.path.exists(self.base_path + ext):
                found_file = self.base_path + ext
                break
        if found_file:
            try:
                with open(found_file, 'r', encoding='utf-8') as f:
                    raw_text = self._clean_text(f.read())
                    lines = raw_text.split('\n')
                lyrics_source = found_file.split('.')[-1].upper()
            except Exception as e:
                logging.debug(f"Error leyendo archivo de letras: {e}")
        else:
            if os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        lyrics_sync = data.get('lyrics_sync', [])
                        unsynced_lyrics = data.get('unsynced_lyrics', [])
                        lyrics_source = data.get('lyrics_source', 'CACHE')
                        cached_translations = data.get('translations', {})
                    self.finished_load.emit(lyrics_sync, unsynced_lyrics, None, lyrics_source, cached_translations)
                    return
                except Exception as e:
                    logging.debug(f"Error leyendo caché de letras: {e}")
            try:
                import mutagen
                audio = mutagen.File(self.track.filepath)
                if audio and hasattr(audio, 'tags') and audio.tags:
                    for key, val in audio.tags.items():
                        if key.startswith('SYLT'):
                            if hasattr(val, 'text') and isinstance(val.text, list) and len(val.text) > 0 and isinstance(val.text[0], tuple):
                                for item in val.text:
                                    if len(item) == 2:
                                        time_ms = item[1] if isinstance(item[1], int) else item[0]
                                        text_str = item[0] if isinstance(item[1], int) else item[1]
                                        clean_txt = self._clean_text(str(text_str))
                                        lyrics_sync.append((time_ms, self._fix_mojibake(clean_txt)))
                                if lyrics_sync:
                                    lyrics_sync.sort(key=lambda x: x[0])
                                    has_sylt = True
                                    break
                    if not has_sylt:
                        best_text = ""
                        possible_texts = []
                        for key, val in audio.tags.items():
                            ku = key.upper()
                            is_id3_text = ku.startswith('USLT') or ku.startswith('TXXX') or ku.startswith('SYLT')
                            is_apple = ku == '©LYR'
                            is_flac_or_custom = 'LYRIC' in ku
                            if is_id3_text or is_apple or is_flac_or_custom:
                                if ku.startswith('TXXX'):
                                    desc = getattr(val, 'desc', '').upper()
                                    if 'LYRIC' not in desc and 'LYRIC' not in ku:
                                        continue
                                if hasattr(val, 'text') and val.text:
                                    if isinstance(val.text, list) and not (len(val.text) > 0 and isinstance(val.text[0], tuple)):
                                        possible_texts.append("\n".join([str(t) for t in val.text]))
                                    elif isinstance(val.text, str):
                                        possible_texts.append(val.text)
                                elif isinstance(val, (list, tuple)):
                                    possible_texts.append("\n".join([str(t) for t in val]))
                                else:
                                    possible_texts.append(str(val))
                        for pt in possible_texts:
                            pt_clean = str(pt).replace('\x00', '').replace('\ufeff', '')
                            if '[' in pt_clean and ']' in pt_clean and bool(re.search(r'\[\d+:\d+', pt_clean)):
                                best_text = pt_clean
                                break
                            elif not best_text and len(pt_clean) > 20:
                                best_text = pt_clean
                        if best_text:
                            best_text = self._fix_mojibake(best_text)
                            best_text = self._clean_text(best_text)
                            lines = best_text.split('\n')
                    if not has_sylt and not lines:
                        raw_dump = str(audio.tags)
                        raw_dump = html.unescape(raw_dump).replace('\\x00', '').replace('\x00', '').replace('\ufeff', '')
                        raw_dump = raw_dump.replace('\\n', '\n').replace('\\r', '\n')
                        brute_matches = re.findall(
                            r'\[\s*(\d{1,3})\s*[:：]\s*(\d{1,2})(?:\s*[\.:,]\s*(\d+))?\s*\]([^\n\[]+)',
                            raw_dump
                        )
                        if brute_matches:
                            for m_str, s_str, ms_str, txt in brute_matches:
                                txt = self._fix_mojibake(txt.strip())
                                if txt and not txt.isdigit():
                                    total_ms = _parse_timestamp(m_str, s_str, ms_str)
                                    lyrics_sync.append((total_ms, txt))
                            if lyrics_sync:
                                lyrics_sync.sort(key=lambda x: x[0])
                                has_sylt = True
            except Exception as e:
                logging.debug(f"Error extrayendo letras integradas asíncronamente: {e}")
        if lines and not has_sylt:
            if found_file and found_file.endswith('.srt'):
                for i in range(len(lines)):
                    if '-->' in lines[i]:
                        time_str = lines[i].split('-->')[0].strip()
                        try:
                            h, m, s_ms = time_str.split(':')
                            s, ms = s_ms.split(',')
                            total_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
                            txt = lines[i + 1].strip() if i + 1 < len(lines) else ""
                            if txt:
                                txt = self._clean_text(txt)
                                lyrics_sync.append((total_ms, txt))
                        except Exception:
                            continue
            else:
                pattern_lrc = re.compile(r'\[\s*(\d+)\s*[:：]\s*(\d{1,2})(?:\s*[\.:,]\s*(\d+))?\s*\]')
                garbage_pattern = re.compile(r'^\s*\[(-\d+|\d+:\d+:\d+)')
                for line in lines:
                    line = line.strip()
                    if not line or line.isdigit() or garbage_pattern.match(line):
                        continue
                    timestamps = pattern_lrc.findall(line)
                    if timestamps:
                        txt = pattern_lrc.sub('', line).strip()
                        for m_str, s_str, ms_str in timestamps:
                            try:
                                total_ms = _parse_timestamp(m_str, s_str, ms_str)
                                lyrics_sync.append((total_ms, txt))
                            except Exception:
                                continue
                    else:
                        if not re.match(r'^\[\w+:', line):
                            unsynced_lyrics.append(line)
                lyrics_sync.sort(key=lambda x: x[0])
        if not found_file and (lyrics_sync or unsynced_lyrics):
            try:
                data = {
                    'lyrics_sync': lyrics_sync,
                    'unsynced_lyrics': unsynced_lyrics,
                    'lyrics_source': lyrics_source or 'ID3'
                }
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
            except Exception as e:
                logging.debug(f"Error guardando caché de letras: {e}")
        self.finished_load.emit(lyrics_sync, unsynced_lyrics, found_file, lyrics_source, {})
class LyricsManager:
    def __init__(self, panel_widget: QListWidget):
        self.panel = panel_widget
        self.is_fullscreen = self.panel.objectName() == "FullscreenLyrics"
        self.font_active = 42 if self.is_fullscreen else FONT_SIZE_ACTIVE
        self.font_inactive = 22 if self.is_fullscreen else FONT_SIZE_INACTIVE
        self.panel.setWordWrap(True)
        self.panel.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.items_data = []                                                
        self._sync_times = []                                         
        self.current_idx = -1
        self.display_mode = 'original'
        self.translations = {}
        self.translation_thread = None
        self.track = None
        self._smooth_lyrics = settings.get('smooth_lyrics', True)
        self._scroll_anim = None
        self._inactive_color = self._compute_inactive_color()
    @staticmethod
    def _compute_inactive_color():
        if isDarkTheme():
            return QColor(255, 255, 255, 80)
        else:
            return QColor(0, 0, 0, 80)
    def refresh_theme_colors(self):
        self._inactive_color = self._compute_inactive_color()
    def set_smooth_lyrics(self, enabled):
        self._smooth_lyrics = enabled
    def clear(self):
        if hasattr(self, '_resize_filter') and self._resize_filter:
            self.panel.viewport().removeEventFilter(self._resize_filter)
            self._resize_filter = None
        self.panel.clear()
        self.items_data = []
        self._sync_times = []
        self.current_idx = -1
    @property
    def items(self):
        return [item for item, _, _ in self.items_data]
    def _fix_mojibake(self, text):
        if not text:
            return text
        try:
            chars = []
            for c in text:
                if ord(c) >= 256:
                    hi = ord(c) >> 8
                    lo = ord(c) & 0xFF
                    swapped = (lo << 8) | hi
                    chars.append(chr(swapped))
                else:
                    chars.append(c)
            fixed_mixed = "".join(chars)
            valid_orig = sum(1 for c in text if 32 <= ord(c) < 127)
            valid_fixed = sum(1 for c in fixed_mixed if 32 <= ord(c) < 127)
            if valid_fixed > valid_orig + 5:
                return fixed_mixed
        except Exception as e:
            logging.debug(f"Error al reparar texto corrupto: {e}")
        return text
    def _clean_text(self, text):
        text = html.unescape(text).replace('\ufeff', '').replace('\x00', '')
        return text.replace('\r\n', '\n').replace('\r', '\n')
    def load(self, track):
        if self.translation_thread and self.translation_thread.isRunning():
            self.translation_thread.stop()
            try:
                self.translation_thread.finished_translation.disconnect()
            except Exception:
                pass
            self.translation_thread.finished.connect(self.translation_thread.deleteLater)
        self.translation_thread = None
        self.clear()
        self.track = track
        self.translations = {}
        self._inactive_color = self._compute_inactive_color()
        self.lyrics_source = None
        base_path = os.path.splitext(track.filepath)[0]
        if not hasattr(self, '_active_workers'):
            self._active_workers = []
        worker = LyricsLoaderWorker(track, base_path, self._clean_text, self._fix_mojibake)
        worker.finished_load.connect(lambda sync, unsync, f_file, l_src, trans, t=track: self._on_lyrics_loaded(t, sync, unsync, f_file, l_src, trans))
        worker.finished.connect(lambda w=worker: self._active_workers.remove(w) if w in self._active_workers else None)
        self._active_workers.append(worker)
        worker.start()
    def _on_lyrics_loaded(self, track, lyrics_sync, unsynced_lyrics, found_file, lyrics_source, cached_translations):
        if not self.track or self.track.filepath != track.filepath:
            return
        track.lyrics_sync = lyrics_sync
        self.lyrics_source = lyrics_source
        self._cached_translations = cached_translations                               
        if not self.lyrics_source and (track.lyrics_sync or unsynced_lyrics):
            self.lyrics_source = "ID3"
        if track.lyrics_sync:
            for time_ms, txt in track.lyrics_sync:
                item = QListWidgetItem(txt)
                item.setForeground(self._inactive_color)
                font = item.font()
                font.setPixelSize(self.font_inactive)
                item.setFont(font)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.panel.addItem(item)
                self.items_data.append((item, txt, time_ms))
            self._sync_times = [t for _, _, t in self.items_data]
            if self.display_mode != 'original':
                self.update_display()
        elif unsynced_lyrics:
            static_color = QColor(255, 255, 255, 240) if isDarkTheme() else QColor(0, 0, 0, 240)
            for i, txt in enumerate(unsynced_lyrics):
                item = QListWidgetItem(txt)
                item.setForeground(static_color)
                font = item.font()
                font.setPixelSize(18)
                item.setFont(font)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.panel.addItem(item)
                self.items_data.append((item, txt, f"unsynced_{i}"))
            if self.display_mode != 'original':
                self.update_display()
        else:
            from PyQt6.QtWidgets import QLabel
            from PyQt6.QtCore import QSize
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setOpenExternalLinks(False)
            font = lbl.font()
            font.setPixelSize(18)
            lbl.setFont(font)
            accent = theme_manager.get_current_accent_hex()
            msg = tr("No hay letras disponibles.")
            sug = tr("Haz clic aquí para buscar o editar la letra")
            if self.is_fullscreen:
                html_text = f"""
                <div style='text-align: center; color: #A0A0A0;'>
                    <span>{msg}</span>
                </div>
                """
            else:
                html_text = f"""
                <div style='text-align: center; color: #A0A0A0;'>
                    <span>{msg}</span><br><br>
                    <a href='edit' style='color:{accent}; text-decoration:underline; font-weight:bold;'>{sug}</a>
                </div>
                """
            lbl.setText(html_text)
            def handle_link(url):
                if url == 'edit':
                    mw = self.panel.window()
                    if hasattr(mw, 'lyrics_ui_controller'):
                        mw.lyrics_ui_controller.open_lyrics_editor()
            lbl.linkActivated.connect(handle_link)
            item = QListWidgetItem()
            h = self.panel.viewport().height()
            item.setSizeHint(QSize(self.panel.viewport().width(), max(h - 20, 100)))
            self.panel.addItem(item)
            self.panel.setItemWidget(item, lbl)
            self._resize_filter = LyricsResizeFilter(self.panel, item)
            self.panel.viewport().installEventFilter(self._resize_filter)
    def set_target_lang(self, lang):
        if self.translation_thread and self.translation_thread.isRunning():
            self.translation_thread.stop()
            try:
                self.translation_thread.finished_translation.disconnect()
            except Exception:
                pass
            self.translation_thread.finished.connect(self.translation_thread.deleteLater)
        self.translation_thread = None
        self.translations = {}
        if self.display_mode != 'original':
            self.update_display()
    def translate_current(self):
        if not self.track:
            return
        if not self.track.lyrics_sync and not self.items_data:
            return
        if self.translations:
            return
        is_synced = bool(self.track.lyrics_sync)
        lyrics_data = self.track.lyrics_sync if is_synced else [(time_ms, orig) for _, orig, time_ms in self.items_data]
        from settings_manager import settings
        target_lang = settings.get('translation_lang', 'es')
        if hasattr(self, '_cached_translations') and target_lang in self._cached_translations:
            self.translations = {int(k) if str(k).isdigit() else k: v for k, v in self._cached_translations[target_lang].items()}
            self.update_display()
            return
        from services.translator import TranslationThread
        self.translation_thread = TranslationThread(lyrics_data, target_lang=target_lang, is_synced=is_synced)
        self.translation_thread.finished_translation.connect(lambda t_lines, lang=target_lang: self._on_translation_finished(t_lines, lang))
        self.translation_thread.error_occurred.connect(self._show_translation_error)
        self.translation_thread.start()
    def _on_translation_finished(self, translated_lines, lang):
        for time_ms, orig, t_text in translated_lines:
            self.translations[time_ms] = t_text
        if self.track:
            try:
                unique_string = f"{self.track.filepath}_{getattr(self.track, 'mtime', 0)}"
                track_hash = hashlib.md5(unique_string.encode('utf-8')).hexdigest()
                cache_file = os.path.join(LYRICS_CACHE_DIR, f"{track_hash}.json")
                data = {}
                if os.path.exists(cache_file):
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = {
                        'lyrics_sync': self.track.lyrics_sync if bool(self.track.lyrics_sync) else [],
                        'unsynced_lyrics': [item[1] for item in self.items_data] if not bool(self.track.lyrics_sync) else [],
                        'lyrics_source': self.lyrics_source or 'EXTERNAL'
                    }
                if 'translations' not in data:
                    data['translations'] = {}
                data['translations'][lang] = self.translations
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
                if not hasattr(self, '_cached_translations'):
                    self._cached_translations = {}
                self._cached_translations[lang] = self.translations
            except Exception as e:
                logging.debug(f"Error guardando traducción en caché JSON: {e}")
        if self.translation_thread:
            self.translation_thread.deleteLater()
            self.translation_thread = None
        self.update_display()
    def _show_translation_error(self, msg):
        from core.notification_manager import notify
        mw = self.panel.window()
        if mw:
            notify.error(tr("Error de traducción"), msg, parent=mw)
    def update_display(self):
        if not self.items_data:
            return
        if self.display_mode != 'original' and not self.translations:
            if not self.translation_thread or not self.translation_thread.isRunning():
                self.translate_current()
        for i, (item, orig_text, time_ms) in enumerate(self.items_data):
            if self.display_mode == 'original':
                item.setText(orig_text)
            else:
                t_text = self.translations.get(time_ms, "")
                if self.display_mode == 'dual':
                    item.setText(f"{orig_text}\n{t_text}" if t_text else orig_text)
                elif self.display_mode == 'translated':
                    item.setText(t_text if t_text else orig_text)
    def sync(self, current_time, track):
        if current_time < 0 or not self.items_data or not track.lyrics_sync:
            return
        adjusted_time = current_time + 150
        idx = bisect.bisect_right(self._sync_times, adjusted_time) - 1
        if idx < 0 or idx == self.current_idx or idx >= len(self.items_data):
            return
        if 0 <= self.current_idx < len(self.items_data):
            old_item = self.items_data[self.current_idx][0]
            old_item.setForeground(self._inactive_color)
            font = old_item.font()
            font.setPixelSize(self.font_inactive)
            font.setBold(False)
            old_item.setFont(font)
        self.current_idx = idx
        new_item = self.items_data[idx][0]
        accent_hex = theme_manager.get_current_accent_hex()
        new_item.setForeground(QColor(accent_hex))
        font = new_item.font()
        font.setPixelSize(self.font_active)
        font.setBold(True)
        new_item.setFont(font)
        if self._smooth_lyrics:
            self._smooth_scroll_to(new_item)
        else:
            self.panel.scrollToItem(new_item, QAbstractItemView.ScrollHint.PositionAtCenter)
    def _smooth_scroll_to(self, item):
        rect = self.panel.visualItemRect(item)
        viewport_h = self.panel.viewport().height()
        scrollbar = self.panel.verticalScrollBar()
        target_value = scrollbar.value() + rect.top() - (viewport_h // 2) + (rect.height() // 2)
        target_value = max(scrollbar.minimum(), min(target_value, scrollbar.maximum()))
        if self._scroll_anim is None:
            self._scroll_anim = QPropertyAnimation(scrollbar, b"value")
        self._scroll_anim.stop()
        self._scroll_anim.setDuration(350)
        self._scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._scroll_anim.setStartValue(scrollbar.value())
        self._scroll_anim.setEndValue(target_value)
        self._scroll_anim.start()