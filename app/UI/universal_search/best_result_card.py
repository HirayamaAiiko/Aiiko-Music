from PyQt6.QtCore import Qt, QSize, QRect, QEvent, pyqtProperty, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QFontMetrics, QFont
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QListWidget, QListWidgetItem, QApplication, QGraphicsOpacityEffect,
                             QStyledItemDelegate, QStyle, QFrame, QLineEdit)
from qfluentwidgets import FluentIcon as FIF
from utils import get_artists_from_string
from settings_manager import settings
from core.language_manager import tr
from UI.universal_search.components import ElidedLabel
class BestResultCard(QWidget):
    play_clicked = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._is_hover = False
        self._accent = "#A064FF"
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 16, 24, 16)
        lay.setSpacing(24)
        self.cover_lbl = QLabel()
        self.cover_lbl.setFixedSize(108, 108)
        self.cover_lbl.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 8px;")
        self.cover_lbl.setScaledContents(True)
        lay.addWidget(self.cover_lbl)
        info_lay = QVBoxLayout()
        info_lay.setSpacing(6)
        info_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.title_lbl = ElidedLabel("Título")
        self.title_lbl.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background: transparent;")
        info_lay.addWidget(self.title_lbl)
        self.artist_lbl = ElidedLabel("ARTISTA")
        self.artist_lbl.setStyleSheet("color: #10b981; font-size: 14px; font-weight: bold; background: transparent; text-transform: uppercase;")
        info_lay.addWidget(self.artist_lbl)
        self.album_lbl = ElidedLabel("Álbum Desconocido • 2023")
        self.album_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 13px; background: transparent;")
        info_lay.addWidget(self.album_lbl)
        lay.addLayout(info_lay, 1)
        from qfluentwidgets import PrimaryPushButton
        self.play_btn = PrimaryPushButton(FIF.PLAY_SOLID, " Reproducir")
        self.play_btn.setFixedSize(140, 42)
        font = self.play_btn.font()
        font.setBold(True)
        font.setPixelSize(14)
        self.play_btn.setFont(font)
        self.play_btn.clicked.connect(self.play_clicked.emit)
        lay.addWidget(self.play_btn, 0, Qt.AlignmentFlag.AlignVCenter)
    def update_accent(self, accent_hex):
        self._accent = accent_hex
        accent_qcolor = QColor(accent_hex)
        r, g, b = accent_qcolor.red(), accent_qcolor.green(), accent_qcolor.blue()
        self.artist_lbl.setStyleSheet(f"color: {accent_hex}; font-size: 14px; font-weight: bold; background: transparent; text-transform: uppercase;")
        self.update()
    def enterEvent(self, e):
        self._is_hover = True
        self.update()
        super().enterEvent(e)
    def leaveEvent(self, e):
        self._is_hover = False
        self.update()
        super().leaveEvent(e)
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.play_clicked.emit()
        super().mousePressEvent(e)
    def paintEvent(self, e):
        from PyQt6.QtGui import QPainter, QColor, QPen
        from PyQt6.QtCore import QRectF, Qt
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        accent_qcolor = QColor(self._accent)
        r, g, b = accent_qcolor.red(), accent_qcolor.green(), accent_qcolor.blue()
        bg_color = QColor(0, 0, 0, 40)
        border_color = QColor(r, g, b, 60)
        if self._is_hover:
            bg_color = QColor(r, g, b, 15)
            border_color = QColor(r, g, b, 100)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()).adjusted(0.5, 0.5, -0.5, -0.5), 12.0, 12.0)
        pen = QPen()
        pen.setColor(border_color)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        painter.drawRoundedRect(rect, 11.5, 11.5)
        painter.end()
