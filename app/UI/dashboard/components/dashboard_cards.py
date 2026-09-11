import os
import hashlib
from PyQt6.QtCore import Qt, QSize, QRectF, QPropertyAnimation, QEasingCurve, pyqtSignal, pyqtProperty
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSizePolicy, QFrame
)
from qfluentwidgets import (
    CaptionLabel, CardWidget, TransparentToolButton, SubtitleLabel
)
from config import CACHE_DIR
import functools
from core.language_manager import tr
class _ClippedCoverLabel(QLabel):
    def __init__(self, radius: int = 8, parent=None):
        super().__init__(parent)
        self._radius = radius
        self._pixmap_src: QPixmap | None = None
        self._cached_scaled: QPixmap | None = None
        self._fade_opacity = 1.0
        self.setStyleSheet("background: transparent;")
    @pyqtProperty(float)
    def fade_opacity(self):
        return self._fade_opacity
    @fade_opacity.setter
    def fade_opacity(self, val):
        self._fade_opacity = val
        self.update()
    def setPixmap(self, pix: QPixmap, animate: bool = True):
        if pix is not None and pix.isNull():
            pix = None
        self._pixmap_src = pix
        self._cached_scaled = None
        if animate and pix is not None:
            self._fade_opacity = 0.0
            self._anim = QPropertyAnimation(self, b"fade_opacity", self)
            self._anim.setDuration(300)                       
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.start()
        else:
            self._fade_opacity = 1.0
        self.update()
    def resizeEvent(self, event):
        self._cached_scaled = None
        super().resizeEvent(event)
    _fallback_cache = {}
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.setBrush(QColor(255, 255, 255, 13))
        painter.setPen(Qt.PenStyle.NoPen)
        if self._radius:
            painter.drawRoundedRect(0, 0, w, h, self._radius, self._radius)
        else:
            painter.drawRect(0, 0, w, h)
        if self._pixmap_src:
            if not self._cached_scaled or self._cached_scaled.size() != QSize(w, h):
                raw_scaled = self._pixmap_src.scaled(
                    w, h,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                clipped_pixmap = QPixmap(w, h)
                clipped_pixmap.fill(Qt.GlobalColor.transparent)
                p = QPainter(clipped_pixmap)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                if self._radius:
                    clip = QPainterPath()
                    clip.addRoundedRect(QRectF(0, 0, w, h), self._radius, self._radius)
                    p.setClipPath(clip)
                x = (raw_scaled.width()  - w) // 2
                y = (raw_scaled.height() - h) // 2
                p.drawPixmap(-x, -y, raw_scaled)
                p.end()
                self._cached_scaled = clipped_pixmap
            painter.setOpacity(self._fade_opacity)
            painter.drawPixmap(0, 0, self._cached_scaled)
            painter.setOpacity(1.0)
        else:
            size_key = (w // 2, h // 2)
            if size_key not in self._fallback_cache:
                from qfluentwidgets import FluentIcon as _FIF
                c = QColor(136, 136, 136)              
                self._fallback_cache[size_key] = _FIF.MUSIC.icon(color=c).pixmap(QSize(*size_key))
            icon_pix = self._fallback_cache[size_key]
            if not icon_pix.isNull():
                ix = (w - icon_pix.width())  // 2
                iy = (h - icon_pix.height()) // 2
                painter.setOpacity(0.35)
                painter.drawPixmap(ix, iy, icon_pix)
                painter.setOpacity(1.0)
        painter.end()
class _ClippedOverlayLabel(QWidget):
    def __init__(self, radius: int = 8, parent=None):
        super().__init__(parent)
        self._radius = radius
        self._opacity = 0.0
        self.setStyleSheet("background: transparent;")
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
        painter.setBrush(QColor(0, 0, 0, int(102 * self._opacity)))                         
        painter.setPen(Qt.PenStyle.NoPen)
        w, h = self.width(), self.height()
        if self._radius:
            painter.drawRoundedRect(0, 0, w, h, self._radius, self._radius)
        else:
            painter.drawRect(0, 0, w, h)
        painter.setPen(QColor(255, 255, 255, int(255 * self._opacity)))
        font = painter.font()
        font.setPixelSize(32)
        painter.setFont(font)
        painter.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, "▶")
        painter.end()
@functools.lru_cache(maxsize=100)
def _load_cover_thumbnail(cover_path, size=140):
    if not cover_path or not os.path.exists(cover_path):
        return None
    file_hash = hashlib.md5(cover_path.encode('utf-8')).hexdigest()
    thumb_path = os.path.join(CACHE_DIR, "thumbnails", f"{file_hash}_{size}.jpg")
    if os.path.exists(thumb_path):
        pix = QPixmap(thumb_path)
    else:
        pix = QPixmap(cover_path).scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
    return pix
class CoverCard(QFrame):
    clicked = pyqtSignal()
    def __init__(self, title="", subtitle="", cover_path=None, filepath=None, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.setFixedSize(160, 210)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        self.setObjectName("CoverCard")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self._is_hover = False
        from settings_manager import settings
        square = settings.get('square_covers', False)
        radius = 0 if square else 8
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        self.cover_label = _ClippedCoverLabel(radius=radius)
        self.cover_label.setFixedSize(140, 140)
        cover_container = QWidget()
        cover_container.setFixedSize(140, 140)
        cover_container.setStyleSheet("background: transparent;")
        self.cover_label.setParent(cover_container)
        self.cover_label.setGeometry(0, 0, 140, 140)
        self.play_overlay = _ClippedOverlayLabel(radius=radius, parent=cover_container)
        self.play_overlay.setGeometry(0, 0, 140, 140)
        self.play_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._overlay_anim = QPropertyAnimation(self.play_overlay, b"opacity")
        self._overlay_anim.setDuration(150)
        self._overlay_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        layout.addWidget(cover_container, 0, Qt.AlignmentFlag.AlignCenter)
        self.title_label = QLabel("")
        self.title_label.setWordWrap(False)
        self.title_label.setFixedWidth(140)
        self.title_label.setStyleSheet("font-weight: 600; font-size: 14px; background: transparent;")
        layout.addWidget(self.title_label)
        self.subtitle_label = QLabel("")
        self.subtitle_label.setWordWrap(False)
        self.subtitle_label.setFixedWidth(140)
        self.subtitle_label.setStyleSheet("color: #888888; font-size: 13px; background: transparent;")
        layout.addWidget(self.subtitle_label)
        self.update_data(title, subtitle, cover_path, filepath)
    def update_data(self, title, subtitle, cover_path, filepath):
        self.filepath = filepath
        full_title = title if title else tr("Desconocido")
        full_subtitle = subtitle if subtitle else tr("Desconocido")
        self.title_label.setToolTip(full_title)
        self.subtitle_label.setToolTip(full_subtitle)
        fm_title = self.title_label.fontMetrics()
        self.title_label.setText(fm_title.elidedText(full_title, Qt.TextElideMode.ElideRight, 138))
        fm_sub = self.subtitle_label.fontMetrics()
        if " • " in full_subtitle:
            left_part, right_part = full_subtitle.rsplit(" • ", 1)
            right_part_with_bullet = " • " + right_part
            right_width = fm_sub.horizontalAdvance(right_part_with_bullet)
            left_width = max(0, 138 - right_width)
            elided_left = fm_sub.elidedText(left_part, Qt.TextElideMode.ElideRight, left_width)
            self.subtitle_label.setText(elided_left + right_part_with_bullet)
        else:
            self.subtitle_label.setText(fm_sub.elidedText(full_subtitle, Qt.TextElideMode.ElideRight, 138))
        main_win = self.window()
        image_cache = getattr(main_win, 'image_cache', None)
        if image_cache:
            import types
            from settings_manager import settings
            square = settings.get('square_covers', False)
            radius = 0 if square else 8
            dummy_track = types.SimpleNamespace(cover_path=cover_path)
            image_cache.assign_async_pixmap(self.cover_label, dummy_track, 140, radius)
        else:
            pix = _load_cover_thumbnail(cover_path, 140)
            self.cover_label.setPixmap(pix if pix else None)
    def enterEvent(self, event):
        self._is_hover = True
        self.update()
        self._overlay_anim.stop()
        self._overlay_anim.setStartValue(self.play_overlay.opacity)
        self._overlay_anim.setEndValue(1.0)
        self._overlay_anim.start()
        super().enterEvent(event)
    def leaveEvent(self, event):
        self._is_hover = False
        self.update()
        self._overlay_anim.stop()
        self._overlay_anim.setStartValue(self.play_overlay.opacity)
        self._overlay_anim.setEndValue(0.0)
        self._overlay_anim.start()
        super().leaveEvent(event)
    def paintEvent(self, event):
        if not getattr(self, '_is_hover', False):
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 10))                               
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 8.0, 8.0)
        painter.end()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self._press_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and getattr(self, '_pressed', False):
            self._pressed = False
            drag_dist = (event.globalPosition().toPoint() - self._press_pos).manhattanLength()
            if drag_dist < 12 and self.rect().contains(event.pos()) and hasattr(self, 'clicked'):
                self.clicked.emit()
        super().mouseReleaseEvent(event)
class StatCard(QWidget):
    def __init__(self, icon, value, label, color="#1DB954", parent=None):
        super().__init__(parent)
        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._color = color
        self._icon_def = icon
        self._hovered = False
        self.setStyleSheet("""
            StatCard { background: transparent; }
            StatCard * {
                background: transparent;
                border: none;
            }
        """)
        self.setObjectName("StatCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)
        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(24, 24)
        self._icon_lbl.setStyleSheet("background: transparent; border: none;")
        self._update_icon()
        icon_layout = QHBoxLayout()
        icon_layout.setContentsMargins(0,0,0,0)
        icon_layout.addWidget(self._icon_lbl)
        icon_layout.addStretch()
        layout.addLayout(icon_layout)
        layout.addStretch()
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(
            "font-weight: 800; font-size: 28px; color: white;"
            "background: transparent; padding: 0px; margin: 0px;"
        )
        layout.addWidget(self.value_label)
        desc_label = QLabel(label)
        desc_label.setStyleSheet(
            "color: #999999; font-weight: 500; font-size: 13px;"
            "background: transparent; padding: 0px; margin: 0px;"
        )
        layout.addWidget(desc_label)
        layout.addSpacing(6)
        self._line = QFrame()
        self._line.setFixedSize(32, 3)
        self._line.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
        layout.addWidget(self._line)
    def _update_icon(self):
        try:
            icon_obj = self._icon_def.icon(color=QColor(self._color)) if hasattr(self._icon_def, 'icon') else self._icon_def
            pix = icon_obj.pixmap(QSize(24, 24))
            self._icon_lbl.setPixmap(pix)
        except Exception:
            pass
    def set_accent(self, color):
        self._color = color
        self._update_icon()
        self._line.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)
    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor(255, 255, 255, 15) if self._hovered else QColor(255, 255, 255, 7)               
        border = QColor(255, 255, 255, 25) if self._hovered else QColor(255, 255, 255, 12)              
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12.0, 12.0)
        pen = painter.pen()
        pen.setColor(border)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        painter.drawRoundedRect(rect, 11.5, 11.5)
        painter.end()