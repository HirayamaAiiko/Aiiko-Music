from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from qfluentwidgets import BodyLabel, CaptionLabel, SmoothScrollArea
from settings_manager import settings
class BaseSettingsTab(QWidget):
    CARD_STYLE = """
        QWidget#SettingsCard {
            background-color: rgba(255, 255, 255, 0.04);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.06);
        }
    """
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self._accent = player.ACCENT_COLORS.get(
            settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954'
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        self.scroll_area, self.main_layout = self._create_scroll_page(player)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.scroll_area)
    def _create_scroll_page(self, player):
        scroll_area = SmoothScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("SmoothScrollArea { background: transparent; border: none; }")
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 30)
        layout.setSpacing(0)
        scroll_area.setWidget(content)
        player.apply_smooth_scroll(scroll_area)
        return scroll_area, layout
    _ICON_CACHE = {}
    def _get_custom_icon(self, icon_name, default_fif, color=None):
        cache_key = (icon_name, color)
        if cache_key in BaseSettingsTab._ICON_CACHE:
            return BaseSettingsTab._ICON_CACHE[cache_key]
        import os
        from PyQt6.QtGui import QIcon, QPainter, QColor
        from config import APP_ROOT
        path = os.path.join(APP_ROOT, 'resources', 'buttons', f'{icon_name}.svg')
        result_icon = None
        if os.path.exists(path):
            if color:
                pix = QIcon(path).pixmap(24, 24)
                p = QPainter(pix)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                p.fillRect(pix.rect(), QColor(color))
                p.end()
                result_icon = QIcon(pix)
            else:
                result_icon = QIcon(path)
        else:
            if color:
                result_icon = default_fif.icon(color=QColor(color))
            else:
                result_icon = default_fif if not hasattr(default_fif, 'icon') else default_fif.icon()
        BaseSettingsTab._ICON_CACHE[cache_key] = result_icon
        return result_icon
    def _register_dynamic_icon(self, widget, icon_name, default_fif):
        if not hasattr(self, '_dynamic_icons'): self._dynamic_icons = []
        self._dynamic_icons.append((widget, icon_name, default_fif))
        qicon = self._get_custom_icon(icon_name, default_fif, self._accent)
        if hasattr(widget, 'setIcon'):
            widget.setIcon(qicon)
        elif hasattr(widget, 'setPixmap'):
            widget.setPixmap(qicon.pixmap(widget.width(), widget.height()))
    def refresh_theme(self):
        self._accent = self.player.ACCENT_COLORS.get(
            settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954'
        )
        if hasattr(self, '_dynamic_icons'):
            for widget, icon_name, default_fif in self._dynamic_icons:
                qicon = self._get_custom_icon(icon_name, default_fif, self._accent)
                if hasattr(widget, 'setIcon'):
                    widget.setIcon(qicon)
                elif hasattr(widget, 'setPixmap'):
                    widget.setPixmap(qicon.pixmap(widget.width(), widget.height()))
        if hasattr(self, '_dynamic_fifs'):
            for widget, fif in self._dynamic_fifs:
                from PyQt6.QtGui import QColor
                if hasattr(widget, 'setPixmap'):
                    widget.setPixmap(fif.icon(color=QColor(self._accent)).pixmap(widget.width(), widget.height()))
                elif hasattr(widget, 'setIcon'):
                    widget.setIcon(fif.icon(color=QColor(self._accent)))
        if hasattr(self, '_accent_labels'):
            for lbl in self._accent_labels:
                lbl.setStyleSheet(f"color: {self._accent}; background: transparent; border: none;")
    def _create_card(self, title, icon=None):
        card = QWidget()
        card.setObjectName("SettingsCard")
        card.setStyleSheet(self.CARD_STYLE)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(24, 20, 24, 20)
        inner.setSpacing(0)
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        if icon:
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(18, 18)
            from PyQt6.QtGui import QIcon
            if isinstance(icon, tuple) and len(icon) == 2:
                icon_name, default_fif = icon
                self._register_dynamic_icon(icon_lbl, icon_name, default_fif)
            elif isinstance(icon, QIcon):
                icon_lbl.setPixmap(icon.pixmap(18, 18))
            else:
                from PyQt6.QtGui import QColor
                icon_lbl.setPixmap(icon.icon(color=QColor(self._accent)).pixmap(18, 18))
                if not hasattr(self, '_dynamic_fifs'): self._dynamic_fifs = []
                self._dynamic_fifs.append((icon_lbl, icon))
            icon_lbl.setStyleSheet("background: transparent; border: none;")
            header_row.addWidget(icon_lbl)
        header = QLabel(title)
        from PyQt6.QtWidgets import QApplication
        font = QApplication.font()
        font.setWeight(700)       
        font.setPixelSize(15)
        header.setFont(font)
        header.setStyleSheet(
            f"color: {self._accent}; "
            "background: transparent; border: none;"
        )
        if not hasattr(self, '_accent_labels'): self._accent_labels = []
        self._accent_labels.append(header)
        header_row.addWidget(header)
        header_row.addStretch()
        inner.addLayout(header_row)
        inner.addSpacing(14)
        return card, inner
    def _setting_row(self, layout, title, description, control_widget, add_separator=True):
        row = QHBoxLayout()
        row.setContentsMargins(0, 8, 0, 8)
        info = QVBoxLayout()
        info.setSpacing(2)
        from qfluentwidgets import StrongBodyLabel
        from PyQt6.QtWidgets import QApplication
        global_family = QApplication.font().family()
        t = StrongBodyLabel(title)
        font = t.font()
        font.setFamily(global_family)
        font.setPixelSize(14)
        t.setFont(font)
        info.addWidget(t)
        d = QLabel(description)
        d_font = d.font()
        d_font.setFamily(global_family)
        d_font.setPixelSize(13)
        d.setFont(d_font)
        d.setStyleSheet("QLabel { color: #A0A0A0; background: transparent; border: none; }")
        d.setWordWrap(True)
        info.addWidget(d)
        row.addLayout(info, 1)
        row.addSpacing(20)
        row.addWidget(control_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(row)
        if add_separator:
            self._separator(layout)
    def _setting_row_layout(self, layout, title, description, control_layout, add_separator=True):
        row = QHBoxLayout()
        row.setContentsMargins(0, 8, 0, 8)
        info = QVBoxLayout()
        info.setSpacing(2)
        from qfluentwidgets import StrongBodyLabel
        from PyQt6.QtWidgets import QApplication
        global_family = QApplication.font().family()
        t = StrongBodyLabel(title)
        font = t.font()
        font.setFamily(global_family)
        font.setPixelSize(14)
        t.setFont(font)
        info.addWidget(t)
        d = QLabel(description)
        d_font = d.font()
        d_font.setFamily(global_family)
        d_font.setPixelSize(13)
        d.setFont(d_font)
        d.setStyleSheet("QLabel { color: #A0A0A0; background: transparent; border: none; }")
        d.setWordWrap(True)
        info.addWidget(d)
        row.addLayout(info, 1)
        row.addSpacing(20)
        row.addLayout(control_layout)
        layout.addLayout(row)
        if add_separator:
            self._separator(layout)
    def _separator(self, layout):
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: rgba(255,255,255,0.05);")
        layout.addWidget(sep)