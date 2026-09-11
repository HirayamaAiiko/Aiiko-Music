import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor
from core.language_manager import tr
class _ArtistAvatarOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
    @opacity.setter
    def opacity(self, val):
        self._opacity = val
        self.update()
    def paintEvent(self, event):
        if self._opacity <= 0.0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, int(120 * self._opacity)))
        painter.setPen(Qt.PenStyle.NoPen)
        w, h = self.width(), self.height()
        painter.drawEllipse(0, 0, w, h)
        painter.setPen(QColor(255, 255, 255, int(255 * self._opacity)))
        font = painter.font()
        font.setPixelSize(18)
        painter.setFont(font)
        painter.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, "▶")
        painter.end()
class ArtistRow(QWidget):
    clicked = pyqtSignal(str)                               
    def __init__(self, rank, artist_name, total_plays, cover_path=None,
                 cover_pixmap=None, accent="#1DB954", parent=None):
        super().__init__(parent)
        self._artist_name = artist_name
        self._accent = accent
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 12, 4)
        layout.setSpacing(12)
        self.rank_label = QLabel(f"#{rank}")
        self.rank_label.setFixedWidth(28)
        self.rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rank_label.setStyleSheet(
            f"color: {accent}; font-weight: bold; font-size: 14px; background: transparent;"
        )
        layout.addWidget(self.rank_label)
        self.cover_container = QWidget()
        self.cover_container.setFixedSize(40, 40)
        self.cover_container.setStyleSheet("background: transparent;")
        self.cover = QLabel(self.cover_container)
        self.cover.setFixedSize(40, 40)
        self.cover.setStyleSheet("background: transparent;")
        self._apply_circular_cover(cover_path, cover_pixmap)
        self.play_overlay = _ArtistAvatarOverlay(self.cover_container)
        self.play_overlay.setGeometry(0, 0, 40, 40)
        self._anim = QPropertyAnimation(self.play_overlay, b"opacity")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        layout.addWidget(self.cover_container)
        info = QVBoxLayout()
        info.setSpacing(0)
        info.setContentsMargins(0, 0, 0, 0)
        self.name_lbl = QLabel(artist_name)
        self.name_lbl.setStyleSheet(
            "font-weight: 600; font-size: 13px; background: transparent;"
        )
        info.addWidget(self.name_lbl)
        self.plays_lbl = QLabel(f"{total_plays:,} {tr('reproducciones')}")
        self.plays_lbl.setStyleSheet("color: #888888; font-size: 13px; background: transparent;")
        info.addWidget(self.plays_lbl)
        layout.addLayout(info, 1)
    def _apply_circular_cover(self, cover_path=None, cover_pixmap=None):
        self.cover.setPixmap(QPixmap())         
        self.cover.setStyleSheet("background: transparent;")
        if cover_pixmap and not cover_pixmap.isNull():
            self.cover.setPixmap(cover_pixmap)
        elif cover_path and os.path.exists(cover_path):
            pix = QPixmap(cover_path).scaled(
                40, 40,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            circular = QPixmap(40, 40)
            circular.fill(Qt.GlobalColor.transparent)
            painter = QPainter(circular)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addEllipse(QRectF(0, 0, 40, 40))
            painter.setClipPath(path)
            x_off = (pix.width() - 40) // 2
            y_off = (pix.height() - 40) // 2
            painter.drawPixmap(-x_off, -y_off, pix)
            painter.end()
            self.cover.setPixmap(circular)
        else:
            circular = QPixmap(40, 40)
            circular.fill(Qt.GlobalColor.transparent)
            painter = QPainter(circular)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor(255, 255, 255, 20))                         
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, 40, 40)
            painter.end()
            self.cover.setPixmap(circular)
    def update_data(self, rank, artist_name, total_plays, cover_pixmap=None, cover_path=None, accent=None):
        self._artist_name = artist_name
        if accent:
            self._accent = accent
            self.rank_label.setStyleSheet(
                f"color: {accent}; font-weight: bold; font-size: 14px; background: transparent;"
            )
        self.rank_label.setText(f"#{rank}")
        self.name_lbl.setText(artist_name)
        self.plays_lbl.setText(f"{total_plays:,} {tr('reproducciones')}")
        self._apply_circular_cover(cover_path, cover_pixmap)
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._artist_name)
        super().mousePressEvent(e)
    def enterEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self.play_overlay.opacity)
        self._anim.setEndValue(1.0)
        self._anim.start()
        self.name_lbl.setStyleSheet(f"color: {self._accent}; font-weight: 600; font-size: 13px; background: transparent;")
        super().enterEvent(event)
    def leaveEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self.play_overlay.opacity)
        self._anim.setEndValue(0.0)
        self._anim.start()
        self.name_lbl.setStyleSheet("font-weight: 600; font-size: 13px; background: transparent;")
        super().leaveEvent(event)
class MiniProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._accent = "#1DB954"
        self.setFixedHeight(6)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    def setValue(self, val):
        self._value = max(0, min(100, val))
        self.update()
    def setAccent(self, accent):
        self._accent = accent
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.drawRoundedRect(0, 0, w, h, 3.0, 3.0)
        if self._value > 0:
            chunk_w = int(w * (self._value / 100.0))
            if chunk_w > 0:
                painter.setBrush(QColor(self._accent))
                painter.drawRoundedRect(0, 0, chunk_w, h, 3.0, 3.0)
        painter.end()
class GenreRow(QWidget):
    def __init__(self, genre_name, pct, accent="#1DB954", parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.name_lbl = QLabel(genre_name)
        self.name_lbl.setFixedWidth(80)
        self.name_lbl.setStyleSheet("font-size: 13px; background: transparent;")
        layout.addWidget(self.name_lbl)
        self.bar = MiniProgressBar()
        self.bar.setAccent(accent)
        self.bar.setValue(pct)
        layout.addWidget(self.bar, 1)
        self.pct_lbl = QLabel(f"{pct}%")
        self.pct_lbl.setFixedWidth(32)
        self.pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.pct_lbl.setStyleSheet("color: #888888; font-size: 13px; background: transparent;")
        layout.addWidget(self.pct_lbl)
    def update_data(self, genre_name, pct, accent):
        self.name_lbl.setText(genre_name)
        self.bar.setAccent(accent)
        self.bar.setValue(pct)
        self.pct_lbl.setText(f"{pct}%")