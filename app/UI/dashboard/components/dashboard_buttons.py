from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF, QSize
from PyQt6.QtGui import QPainter, QColor, QFont, QLinearGradient
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect, QHBoxLayout, QLabel
class _CarouselArrowBtn(QWidget):
    clicked = pyqtSignal()
    def __init__(self, direction: str = "right", parent=None):
        super().__init__(parent)
        self._direction = direction                     
        self._hovered = False
        self._is_active = True
        self.setFixedSize(38, 230)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setStyleSheet("background: transparent;")
        self._bg_alpha = 0
        self._anim = QPropertyAnimation(self, b"_bg_opacity", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._op_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._op_effect)
        self._fade_anim = QPropertyAnimation(self._op_effect, b"opacity", self)
        self._fade_anim.setDuration(200)
    def _get_bg_opacity(self): return self._bg_alpha
    def _set_bg_opacity(self, v): self._bg_alpha = v; self.update()
    _bg_opacity = pyqtProperty(int, _get_bg_opacity, _set_bg_opacity)
    def set_active(self, active: bool):
        if self._is_active == active:
            return
        self._is_active = active
        self.setCursor(Qt.CursorShape.PointingHandCursor if active else Qt.CursorShape.ArrowCursor)
        self._fade_anim.stop()
        self._fade_anim.setEndValue(1.0 if active else 0.3)
        self._fade_anim.start()
        if not active and self._hovered:
            self.leaveEvent(None)
    def enterEvent(self, e):
        if not self._is_active: return
        self._hovered = True
        self._anim.stop()
        self._anim.setStartValue(self._bg_alpha)
        self._anim.setEndValue(45)
        self._anim.start()
        if e: super().enterEvent(e)
    def leaveEvent(self, e):
        self._hovered = False
        self._anim.stop()
        self._anim.setStartValue(self._bg_alpha)
        self._anim.setEndValue(0)
        self._anim.start()
        if e: super().leaveEvent(e)
    def mousePressEvent(self, e):
        if not self._is_active: return
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        r = 10                      
        pill_y = 20
        pill_h = 140
        if self._bg_alpha > 0:
            p.setBrush(QColor(255, 255, 255, self._bg_alpha))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(0, pill_y, w, pill_h, r, r)
        chev = "‹" if self._direction == "left" else "›"
        font = QFont("Segoe UI", 28)
        font.setBold(True)
        p.setFont(font)
        alpha = 200 if self._hovered else 130
        p.setPen(QColor(255, 255, 255, alpha))
        p.drawText(QRectF(0, pill_y, w, pill_h), Qt.AlignmentFlag.AlignCenter, chev)
        p.end()
class QuickActionCard(QWidget):
    clicked = pyqtSignal()
    def __init__(self, label: str, icon, accent_color: str, is_active: bool = False, parent=None):
        super().__init__(parent)
        self._label  = label
        self._icon   = icon
        self._accent = accent_color
        self._is_active = is_active
        self._hovered = False
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setToolTip(label)
        self.setObjectName("QuickActionCard")
        self._update_style()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 16, 0)
        layout.setSpacing(8)
        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(16, 16)
        self._icon_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._icon_lbl)
        self._text_lbl = QLabel(label)
        layout.addWidget(self._text_lbl)
        self._render_icon()
    def _update_style(self):
        hex_c = self._accent.lstrip('#')
        if len(hex_c) == 6:
            r, g, b = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
        else:
            r, g, b = 29, 185, 84
        if self._is_active:
            self._current_bg = QColor(r, g, b, 30)             
            self._current_border = QColor(self._accent)
            text_color = self._accent
        else:
            self._current_bg = QColor(255, 255, 255, 0)
            self._current_border = QColor(255, 255, 255, 38)             
            text_color = "#E0E0E0"
        self._hover_bg = QColor(r, g, b, 46) if self._is_active else QColor(255, 255, 255, 20)
        self._hover_border_color = QColor(self._accent) if self._is_active else QColor(255, 255, 255, 76)
        self._normal_text_color = text_color
        self._hover_text_color = self._accent
        self.setStyleSheet("QuickActionCard { background: transparent; }")
        if hasattr(self, '_text_lbl'):
            if self._hovered:
                c = self._hover_text_color
            else:
                c = self._normal_text_color
            self._text_lbl.setStyleSheet(
                f"color: {c}; font-size: 13px; font-weight: 500; background: transparent; border: none;"
            )
            self._render_icon()
        self.update()
    def _render_icon(self):
        try:
            if self._is_active or self._hovered:
                color = QColor(self._accent)
            else:
                color = QColor(224, 224, 224)
            if hasattr(self._icon, 'icon'):
                pix = self._icon.icon(color=color).pixmap(QSize(16, 16))
            else:
                pix = self._icon.pixmap(QSize(16, 16))
            self._icon_lbl.setPixmap(pix)
        except Exception as e:
            pass
    def set_accent(self, accent_color: str):
        self._accent = accent_color
        self._update_style()
    def enterEvent(self, event):
        self._hovered = True
        if hasattr(self, '_text_lbl'):
            self._text_lbl.setStyleSheet(
                f"color: {self._hover_text_color}; font-size: 13px; font-weight: 500; background: transparent; border: none;"
            )
        self._render_icon()
        super().enterEvent(event)
    def leaveEvent(self, event):
        self._hovered = False
        if hasattr(self, '_text_lbl'):
            self._text_lbl.setStyleSheet(
                f"color: {self._normal_text_color}; font-size: 13px; font-weight: 500; background: transparent; border: none;"
            )
        self._render_icon()
        super().leaveEvent(event)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = self._hover_bg if self._hovered else self._current_bg
        border = self._hover_border_color if self._hovered else self._current_border
        if bg.alpha() > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(0, 0, self.width(), self.height(), 8.0, 8.0)
        pen = painter.pen()
        pen.setColor(border)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        painter.drawRoundedRect(rect, 7.5, 7.5)
        painter.end()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)