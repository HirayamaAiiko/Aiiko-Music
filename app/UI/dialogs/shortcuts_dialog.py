from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QWidget
from qfluentwidgets import MessageBoxBase
import theme_manager
class KeyBadgeWidget(QWidget):
    def __init__(self, text, accent_hex, parent=None):
        super().__init__(parent)
        self.text = text
        self.accent = QColor(accent_hex)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 3, 6, 3)
        self.lbl = QLabel(text)
        self.lbl.setStyleSheet(f"color: {accent_hex}; font-family: Consolas, 'Courier New', monospace; font-weight: bold; font-size: 12px; background: transparent; border: none;")
        lay.addWidget(self.lbl)
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r, g, b = self.accent.red(), self.accent.green(), self.accent.blue()
        bg_color = QColor(r, g, b, 38)                 
        border_color = QColor(r, g, b, 76)                 
        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 1))
        rect = self.rect().adjusted(1, 1, -2, -2)
        painter.drawRoundedRect(rect, 4, 4)
class ShortcutsDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.yesButton.setText('Entendido')
        self.cancelButton.hide()
        self.viewLayout.setSpacing(12)
        self.widget.setMinimumWidth(800)
        from qfluentwidgets import SubtitleLabel
        title_label = SubtitleLabel("Atajos de Teclado", self)
        self.viewLayout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)
        accent = theme_manager.get_current_accent_hex()
        from controllers.shortcut_controller import ShortcutController
        from settings_manager import settings
        custom_shortcuts = settings.get('custom_shortcuts', {})
        defs = ShortcutController.DEFAULT_SHORTCUTS
        def get_key(action_id):
            return custom_shortcuts.get(action_id, defs.get(action_id, {}).get("default", ""))
        shortcuts = {
            "Reproducción": [
                (defs["play_pause"]["name"], get_key("play_pause")),
                (defs["next_track"]["name"], get_key("next_track")),
                (defs["prev_track"]["name"], get_key("prev_track")),
            ],
            "Volumen": [
                (defs["vol_up"]["name"], get_key("vol_up")),
                (defs["vol_down"]["name"], get_key("vol_down")),
                (defs["mute"]["name"], get_key("mute")),
            ],
            "Modos": [
                (defs["shuffle"]["name"], get_key("shuffle")),
                (defs["repeat"]["name"], get_key("repeat")),
            ],
            "Interfaz": [
                (defs["queue"]["name"], get_key("queue")),
                (defs["spotlight"]["name"], get_key("spotlight")),
                (defs["search"]["name"], get_key("search")),
                (defs["fullscreen"]["name"], get_key("fullscreen")),
                (defs["help"]["name"], get_key("help")),
            ],
            "Pantalla Completa": [
                (defs["esc"]["name"], get_key("esc")),
                (defs["fs_lyrics"]["name"], get_key("fs_lyrics")),
                (defs["fs_translation"]["name"], get_key("fs_translation")),
                (defs["fs_visualizer"]["name"], get_key("fs_visualizer")),
                (defs["fs_cover"]["name"], get_key("fs_cover")),
            ]
        }
        columns_lay = QHBoxLayout()
        columns_lay.setSpacing(20)
        left_col = QWidget()
        left_lay = QVBoxLayout(left_col)
        left_lay.setContentsMargins(10, 10, 10, 10)
        left_lay.setSpacing(16)
        right_col = QWidget()
        right_lay = QVBoxLayout(right_col)
        right_lay.setContentsMargins(10, 10, 10, 10)
        right_lay.setSpacing(16)
        left_sections = ["Reproducción", "Volumen", "Modos"]
        for section, items in shortcuts.items():
            lay = left_lay if section in left_sections else right_lay
            section_lbl = QLabel(section)
            section_lbl.setStyleSheet(f"color: {accent}; font-size: 15px; font-weight: bold; letter-spacing: 1px;")
            lay.addWidget(section_lbl)
            for desc, key in items:
                row = QHBoxLayout()
                row.setContentsMargins(10, 0, 0, 0)
                desc_lbl = QLabel(desc)
                desc_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.85); font-size: 13px;")
                row.addWidget(desc_lbl)
                row.addStretch(1)
                keys = key.split(" + ")
                keys_lay = QHBoxLayout()
                keys_lay.setSpacing(4)
                for k in keys:
                    key_badge = KeyBadgeWidget(k, accent)
                    keys_lay.addWidget(key_badge)
                row.addLayout(keys_lay)
                lay.addLayout(row)
        left_lay.addStretch(1)
        right_lay.addStretch(1)
        from PyQt6.QtWidgets import QFrame
        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setFrameShadow(QFrame.Shadow.Plain)
        vline.setStyleSheet("color: rgba(255,255,255,0.1);")
        columns_lay.addWidget(left_col)
        columns_lay.addWidget(vline)
        columns_lay.addWidget(right_col)
        container = QWidget()
        container.setLayout(columns_lay)
        self.viewLayout.addWidget(container)
def show_shortcuts_help(parent):
    dlg = ShortcutsDialog(parent)
    dlg.exec()