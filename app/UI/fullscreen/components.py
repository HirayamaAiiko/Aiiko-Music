import os
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPainterPath, QColor
from PyQt6.QtWidgets import QLabel, QSizePolicy, QWidget
from qfluentwidgets import Slider
from settings_manager import settings
class FullScreenSlider(Slider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.setSliderDown(True)
            val = self.minimum() + ((self.maximum() - self.minimum()) * e.position().x()) / self.width()
            self.setValue(int(val))
            self.sliderPressed.emit()
            self.sliderMoved.emit(int(val))
        super().mousePressEvent(e)
    def mouseMoveEvent(self, e):
        if self.isSliderDown():
            val = self.minimum() + ((self.maximum() - self.minimum()) * e.position().x()) / self.width()
            val = max(self.minimum(), min(self.maximum(), val))
            self.setValue(int(val))
            self.sliderMoved.emit(int(val))
        super().mouseMoveEvent(e)
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.isSliderDown():
            self.setSliderDown(False)
            self.sliderReleased.emit()
        super().mouseReleaseEvent(e)
class FullScreenCover(QLabel):
    pixmapChanged = pyqtSignal(object)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.setMaximumSize(550, 550)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._original_pixmap = None
        self._scale_factor = 1.0
        self._radius = 0 if settings.get('square_covers', False) else 20
    def update_cover_style(self):
        self._radius = 0 if settings.get('square_covers', False) else 20
        self.update()
    def set_scale_factor(self, scale):
        self._scale_factor = scale
        if self._original_pixmap:
            self._cached_scaled_pixmap = None
            self.update()
    def setPixmap(self, pixmap):
        self._original_pixmap = pixmap
        self._cached_scaled_pixmap = None
        self.update()
        self.pixmapChanged.emit(pixmap)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._cached_scaled_pixmap = None
    def paintEvent(self, event):
        if not self._original_pixmap or self._original_pixmap.isNull():
            return
        w = self.width()
        h = self.height()
        side = min(w, h) - 20 
        x = (w - side) // 2
        y = (h - side) // 2 - 5
        if not hasattr(self, '_cached_scaled_pixmap') or self._cached_scaled_pixmap is None or self._cached_scaled_pixmap.width() != int(side * self._scale_factor):
            scaled = self._original_pixmap.scaled(side, side,
                                                   Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                                   Qt.TransformationMode.SmoothTransformation)
            new_w = int(side * self._scale_factor)
            new_h = int(side * self._scale_factor)
            if self._scale_factor != 1.0:
                self._cached_scaled_pixmap = scaled.scaled(new_w, new_h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            else:
                self._cached_scaled_pixmap = scaled
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(x, y + 10, side, side, self._radius, self._radius)
        painter.fillPath(shadow_path, QColor(0, 0, 0, 100))
        path = QPainterPath()
        path.addRoundedRect(x, y, side, side, self._radius, self._radius)
        painter.setClipPath(path)
        new_w = self._cached_scaled_pixmap.width()
        new_h = self._cached_scaled_pixmap.height()
        img_x = x + (side - new_w) // 2
        img_y = y + (side - new_h) // 2
        painter.drawPixmap(img_x, img_y, self._cached_scaled_pixmap)
        painter.end()
class ShortcutsOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QVBoxLayout
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setVisible(False)
        self.setFixedSize(320, 320)
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(20, 20, 20, 20)
        self.lay.setSpacing(10)
        self.refresh_shortcuts()
    def refresh_shortcuts(self):
        while self.lay.count():
            item = self.lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        from PyQt6.QtWidgets import QLabel, QHBoxLayout
        from PyQt6.QtCore import Qt
        title = QLabel("<b>Atajos de Teclado</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 15px; background: transparent;")
        self.lay.addWidget(title)
        self.lay.addSpacing(10)
        from settings_manager import settings
        custom_shortcuts = settings.get('custom_shortcuts', {})
        key_esc = custom_shortcuts.get("esc", "Esc / F11")
        key_space = custom_shortcuts.get("play_pause", "Espacio")
        key_next = custom_shortcuts.get("next_track", "Ctrl+Right")
        key_prev = custom_shortcuts.get("prev_track", "Ctrl+Left")
        key_volup = custom_shortcuts.get("vol_up", "Ctrl+Up")
        key_voldown = custom_shortcuts.get("vol_down", "Ctrl+Down")
        key_l = custom_shortcuts.get("fs_lyrics", "L")
        key_t = custom_shortcuts.get("fs_translation", "T")
        key_p = custom_shortcuts.get("fs_visualizer", "P")
        key_c = custom_shortcuts.get("fs_cover", "C")
        shortcuts = [
            (key_esc, "Salir de pantalla completa"),
            (key_space, "Reproducir / Pausa"),
            (f"{key_prev} / {key_next}", "Saltar pista"),
            (f"{key_volup} / {key_voldown}", "Subir / Bajar volumen"),
            (key_l, "Mostrar / Ocultar letras"),
            (key_t, "Traducir letras"),
            (key_p, "Activar visualizador"),
            (key_c, "Mostrar / Ocultar carátula")
        ]
        for key, desc in shortcuts:
            row = QHBoxLayout()
            lbl_key = QLabel(key)
            lbl_key.setStyleSheet("color: #14B8A6; font-weight: bold; font-size: 13px; background: transparent;")
            lbl_desc = QLabel(desc)
            lbl_desc.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 13px; background: transparent;")
            row.addWidget(lbl_key)
            row.addStretch()
            row.addWidget(lbl_desc)
            self.lay.addLayout(row)
    def paintEvent(self, e):
        from PyQt6.QtGui import QPainter, QColor
        from PyQt6.QtCore import Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 200))
        p.drawRoundedRect(self.rect(), 12, 12)