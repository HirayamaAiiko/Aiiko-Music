import os, sys
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QCursor, QConicalGradient, QPen
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtSvg import QSvgRenderer
TEXT_WHITE = QColor("#FFFFFF")
TEXT_DIM   = QColor("#8A85A0")
class SvgLogoWidget(QWidget):
    def __init__(self, path, size=120, parent=None):
        super().__init__(parent)
        self._svg = QSvgRenderer(path) if os.path.exists(path) else None
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    def paintEvent(self, e):
        if not self._svg or not self._svg.isValid(): return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self._svg.render(p, QRectF(0, 0, self._size, self._size))
        p.end()
def make_label(text, style, align=Qt.AlignmentFlag.AlignLeft):
    l = QLabel(text)
    l.setAlignment(align)
    l.setWordWrap(True)
    l.setStyleSheet(style + " background: transparent;")
    return l
class LangCard(QWidget):
    clicked = pyqtSignal(str)
    def __init__(self, code, name_str, parent=None):
        super().__init__(parent)
        self.code = code
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(56)                  
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._selected = False
        self._hover = False
        self._accent = "#00D1B2"          
        self.lbl = QLabel(name_str, self)
        lo = QHBoxLayout(self)
        lo.setContentsMargins(24, 0, 24, 0)
        lo.addWidget(self.lbl)
        self._update_label_style()
    def _update_label_style(self):
        color = TEXT_WHITE.name()
        self.lbl.setStyleSheet(f"font-size: 15px; color: {color}; background: transparent;")
    def set_selected(self, s, accent):
        self._selected = s
        self._accent = accent
        self._update_label_style()
        self.update()
    def enterEvent(self, e): self._hover = True; self.update()
    def leaveEvent(self, e): self._hover = False; self.update()
    def mousePressEvent(self, e): self.clicked.emit(self.code)
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg_color = QColor(self._accent) if self._selected else (QColor(255, 255, 255, 15) if self._hover else QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg_color)
        p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0), 6.0, 6.0)
        p.end()
class ColorCircle(QWidget):
    clicked = pyqtSignal(str, str)
    custom_clicked = pyqtSignal()
    def __init__(self, name, hex_color, is_multicolor=False, parent=None):
        super().__init__(parent)
        self._name = name; self._hex = hex_color; self._is_multicolor = is_multicolor
        self._selected = False; self._hover = False
        self.setFixedSize(50, 50); self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip(name)
    def set_selected(self, s): self._selected = s; self.update()
    def enterEvent(self, e): self._hover = True; self.update()
    def leaveEvent(self, e): self._hover = False; self.update()
    def mousePressEvent(self, e):
        if self._is_multicolor: self.custom_clicked.emit()
        else: self.clicked.emit(self._name, self._hex)
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = 42 if (self._selected or self._hover) else 32
        off = (50 - size) // 2
        if self._is_multicolor:
            grad = QConicalGradient(25, 25, 0)
            grad.setColorAt(0.0, QColor(255, 0, 0))
            grad.setColorAt(0.16, QColor(255, 255, 0))
            grad.setColorAt(0.33, QColor(0, 255, 0))
            grad.setColorAt(0.5, QColor(0, 255, 255))
            grad.setColorAt(0.66, QColor(0, 0, 255))
            grad.setColorAt(0.83, QColor(255, 0, 255))
            grad.setColorAt(1.0, QColor(255, 0, 0))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(grad)
        else:
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(self._hex))
        p.drawEllipse(off, off, size, size)
        if self._selected:
            p.setPen(QPen(QColor(255,255,255,200), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(off-3, off-3, size+6, size+6)
        p.end()
