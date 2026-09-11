from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QPainter, QPainterPath, QColor
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from qfluentwidgets import BodyLabel, themeColor
import theme_manager
class AccentIconWidget(QWidget):
    def __init__(self, icon, size=24, parent=None):
        super().__init__(parent)
        self._icon = icon
        self.setFixedSize(size, size)
        from qfluentwidgets import qconfig
        qconfig.themeChanged.connect(self.update)
        qconfig.themeColorChanged.connect(self.update)
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self._icon.render(p, self.rect(), fill=themeColor().name())
class PanelCardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QPen
        from PyQt6.QtCore import QRectF
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 10)) 
        painter.drawRoundedRect(rect, 12, 12)
        pen = QPen(QColor(255, 255, 255, 13), 1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 12, 12)
        painter.end()
class HeroOverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QPainterPath
        from PyQt6.QtCore import QRectF
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height()).adjusted(0.5, 0.5, -0.5, -0.5)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor(18, 18, 24, 240))
        gradient.setColorAt(0.5, QColor(18, 18, 24, 160))
        gradient.setColorAt(1.0, QColor(18, 18, 24, 40))
        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill)
        path.addRoundedRect(rect, 10, 10)
        path.addRect(0.5, 0.5, 10, rect.height())                       
        painter.setPen(Qt.PenStyle.NoPen)
        painter.fillPath(path, gradient)
        painter.end()
class CircularAvatar(QLabel):
    def __init__(self, size=40):
        super().__init__()
        self.setFixedSize(size, size)
        self._pixmap = None
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    def setPixmap(self, pix):
        self._pixmap = pix
        self.update()
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setBrush(QColor(255, 255, 255, 15))
        painter.setPen(Qt.PenStyle.NoPen)
        from PyQt6.QtCore import QRectF
        rect = QRectF(0, 0, self.width(), self.height()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.drawEllipse(rect)
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            path = QPainterPath()
            path.addEllipse(rect)
            painter.setClipPath(path)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        painter.end()
class ArtistHoverCard(QWidget):
    def __init__(self, artist_name, player, avatar_size=42):
        super().__init__()
        self.artist_name = artist_name
        self.player = player
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._hovered = False
        self._accent_color = theme_manager.get_current_accent_hex()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)
        self.avatar = CircularAvatar(avatar_size)
        layout.addWidget(self.avatar)
        self.name_lbl = BodyLabel(artist_name)
        self.name_lbl.setStyleSheet("font-weight: 500; font-size: 15px; background: transparent; color: white;")
        layout.addWidget(self.name_lbl)
        layout.addStretch()
    def enterEvent(self, e):
        self._hovered = True
        self.name_lbl.setStyleSheet(f"font-weight: 500; font-size: 15px; background: transparent; color: {self._accent_color};")
        self.update()
        super().enterEvent(e)
    def leaveEvent(self, e):
        self._hovered = False
        self.name_lbl.setStyleSheet("font-weight: 500; font-size: 15px; background: transparent; color: white;")
        self.update()
        super().leaveEvent(e)
    def paintEvent(self, e):
        if self._hovered:
            from PyQt6.QtCore import QRectF
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 12))
            painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()).adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)
            painter.end()
        super().paintEvent(e)
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            e.accept()
        super().mousePressEvent(e)
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.player.navigation_controller.open_artist_detail(None, self.artist_name)
        super().mouseReleaseEvent(e)
class _FakeTrack:
    __slots__ = ['cover_path']
    def __init__(self, cover_path=None):
        self.cover_path = cover_path