from PyQt6.QtCore import Qt, QSize, QRect, QEvent, pyqtProperty, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QFontMetrics, QFont
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QListWidget, QListWidgetItem, QApplication, QGraphicsOpacityEffect,
                             QStyledItemDelegate, QStyle, QFrame, QLineEdit)
from qfluentwidgets import FluentIcon as FIF
from utils import get_artists_from_string
from settings_manager import settings
from core.language_manager import tr
class DarkOverlayWidget(QWidget):
    @pyqtProperty(int)
    def bg_alpha(self):
        return getattr(self, '_bg_alpha', 0)
    @bg_alpha.setter
    def bg_alpha(self, value):
        self._bg_alpha = value
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, getattr(self, '_bg_alpha', 0)))
        painter.end()
class FilterChip(QWidget):
    clicked = pyqtSignal(str)
    def __init__(self, name, icon_enum, parent=None):
        super().__init__(parent)
        self.name = name
        self.icon_enum = icon_enum
        self.is_active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(8)
        self.icn = QLabel()
        self.icn.setStyleSheet("background: transparent; border: none;")
        self.txt = QLabel(name)
        self.txt.setStyleSheet("background: transparent; border: none;")
        self.badge = QLabel("0")
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setFixedSize(24, 20)
        lay.addWidget(self.icn)
        lay.addWidget(self.txt)
        lay.addWidget(self.badge)
    def set_active(self, is_active, accent_hex):
        self.is_active = is_active
        accent_qcolor = QColor(accent_hex)
        r, g, b = accent_qcolor.red(), accent_qcolor.green(), accent_qcolor.blue()
        icon_color = accent_qcolor if is_active else QColor(255, 255, 255, 180)
        self.icn.setPixmap(self.icon_enum.icon(color=icon_color).pixmap(14, 14))
        text_color = accent_hex if is_active else "rgba(255, 255, 255, 0.85)"
        font_weight = 'bold' if is_active else 'normal'
        self.txt.setStyleSheet(f"color: {text_color}; font-size: 14px; font-weight: {font_weight}; background: transparent; border: none;")
        count_bg = f"rgba({r}, {g}, {b}, 0.15)" if is_active else "rgba(255, 255, 255, 0.05)"
        count_color = accent_hex if is_active else "rgba(255, 255, 255, 0.6)"
        self.badge.setStyleSheet(f"QLabel {{ background-color: {count_bg}; color: {count_color}; border-radius: 10px; border: none; font-size: 12px; }}")
        self.update()
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.name)
        super().mousePressEvent(e)
    def paintEvent(self, e):
        from PyQt6.QtGui import QPainter, QColor, QPen
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        import theme_manager
        accent = QColor(theme_manager.get_current_accent_hex())
        if self.is_active:
            bg_color = QColor(accent.red(), accent.green(), accent.blue(), 20)
            border_color = QColor(accent.red(), accent.green(), accent.blue(), 102)
        else:
            bg_color = QColor(0, 0, 0, 0)
            border_color = QColor(255, 255, 255, 20)
        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 1))
        rect = self.rect().adjusted(1, 1, -2, -2)
        painter.drawRoundedRect(rect, 8, 8)
class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full_text = text
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(10)
    def setText(self, text):
        self._full_text = text
        self.setToolTip(text)
        self._elide_text()
    def resizeEvent(self, event):
        self._elide_text()
        super().resizeEvent(event)
    def minimumSizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(10, super().minimumSizeHint().height())
    def sizeHint(self):
        from PyQt6.QtCore import QSize
        from PyQt6.QtGui import QFontMetrics
        fm = QFontMetrics(self.font())
        return QSize(150, fm.height())
    def _elide_text(self):
        if not self._full_text:
            super().setText("")
            return
        from PyQt6.QtGui import QFontMetrics
        fm = QFontMetrics(self.font())
        elided = fm.elidedText(self._full_text, Qt.TextElideMode.ElideRight, self.width() - 2)
        if elided != self.text():
            super().setText(elided)
