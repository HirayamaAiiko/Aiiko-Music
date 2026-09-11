import re
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextFormat, QColor
class SyncPreviewManager:
    def __init__(self, audio_engine, text_editor, accent_color, queue=None):
        self.audio_engine = audio_engine
        self.queue = queue
        self.text_editor = text_editor
        self.accent_color = accent_color
        self.preview_active = False
        self.preview_timer = QTimer()
        self.preview_timer.setInterval(100)
        self.preview_timer.timeout.connect(self._on_preview_timer)
    def toggle_preview(self):
        self.preview_active = not self.preview_active
        if self.preview_active:
            self.preview_timer.start()
            return True
        else:
            self.preview_timer.stop()
            self.text_editor.setExtraSelections([])
            return False
    def _on_preview_timer(self):
        if not self.preview_active: return
        if not self.audio_engine or not self.queue: return
        if getattr(self.queue, 'current_index', -1) < 0:
            if self.preview_timer.isActive():
                self.preview_timer.stop()
                self.text_editor.setExtraSelections([])
            return
        pos_ms = self.audio_engine.get_position()
        self._highlight_line(pos_ms)
    def _highlight_line(self, pos_ms):
        text = self.text_editor.toPlainText()
        lines = text.split('\n')
        active_line_idx = -1
        last_time_ms = -1
        for i, line in enumerate(lines):
            match = re.search(r'\[(\d{2,}):(\d{2})(?:\.(\d+))?\]', line)
            if match:
                mm = int(match.group(1))
                ss = int(match.group(2))
                ms_str = match.group(3)
                ms = int(ms_str.ljust(3, '0')[:3]) if ms_str else 0
                time_ms = mm * 60000 + ss * 1000 + ms
                if time_ms <= pos_ms:
                    if time_ms >= last_time_ms:
                        active_line_idx = i
                        last_time_ms = time_ms
                else:
                    break
        if active_line_idx >= 0:
            selection = QTextEdit.ExtraSelection()
            bg_color = QColor(self.accent_color)
            bg_color.setAlpha(60)
            selection.format.setBackground(bg_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            cursor = self.text_editor.textCursor()
            cursor.setPosition(0)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.MoveAnchor, active_line_idx)
            selection.cursor = cursor
            self.text_editor.setExtraSelections([selection])
        else:
            self.text_editor.setExtraSelections([])
    def stop(self):
        if self.preview_timer.isActive():
            self.preview_timer.stop()