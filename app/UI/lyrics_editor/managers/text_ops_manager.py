import re
from PyQt6.QtGui import QTextCursor
class TextOpsManager:
    def __init__(self, text_editor):
        self.text_editor = text_editor
    def insert_timestamp(self, audio_engine):
        if not audio_engine: return
        pos_ms = audio_engine.get_position()
        total_seconds = pos_ms / 1000.0
        mm = int(total_seconds // 60)
        ss = total_seconds % 60
        stamp = f"[{mm:02d}:{ss:05.2f}]"
        cursor = self.text_editor.textCursor()
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        line_text = cursor.selectedText()
        clean_text = re.sub(r'^\[\d{2,}:\d{2}(?:\.\d+)?\]\s*', '', line_text).strip()
        cursor.insertText(f"{stamp} {clean_text}")
        moved = cursor.movePosition(QTextCursor.MoveOperation.Down)
        if not moved:
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
            cursor.insertText('\n')
        else:
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        self.text_editor.setTextCursor(cursor)
        self.text_editor.setFocus()
    def batch_adjust_time(self, seconds_delta):
        text = self.text_editor.toPlainText()
        if not text.strip(): return
        def replace_time(match):
            mm = int(match.group(1))
            ss = int(match.group(2))
            ms_str = match.group(3)
            ms = 0.0
            if ms_str:
                ms = int(ms_str.ljust(3, '0')[:3]) / 1000.0
            total_seconds = mm * 60 + ss + ms + seconds_delta
            if total_seconds < 0:
                total_seconds = 0
            new_mm = int(total_seconds // 60)
            new_ss = total_seconds % 60
            return f"[{new_mm:02d}:{new_ss:05.2f}]"
        new_text = re.sub(r'\[(\d{2,}):(\d{2})(?:\.(\d+))?\]', replace_time, text)
        self.text_editor.setPlainText(new_text)