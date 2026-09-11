from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QVariantAnimation, QRectF, QPointF, QTimer
from PyQt6.QtWidgets import QWidget, QGraphicsDropShadowEffect
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QPen
from settings_manager import settings
import theme_manager
class ScrollToTopButton(QWidget):
    def __init__(self, target_scrollable, parent=None):
        super().__init__(parent)
        self.target_scrollable = target_scrollable
        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hide()
        self.is_hovered = False
        self.is_pressed = False
        self._scale = 1.0
        self._opacity = 0.0
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(6)
        self.shadow.setColor(QColor(0, 0, 0, 0))                     
        self.setGraphicsEffect(self.shadow)
        self._scale_anim = QVariantAnimation(self)
        self._scale_anim.setDuration(120)
        self._scale_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._scale_anim.valueChanged.connect(self._on_scale_changed)
        self._fade_anim = QVariantAnimation(self)
        self._fade_anim.setDuration(250)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._fade_anim.valueChanged.connect(self._on_opacity_changed)
        self._fade_anim.finished.connect(self._on_fade_finished)
        self.vbar = getattr(self.target_scrollable, 'verticalScrollBar', lambda: None)()
        if self.vbar:
            self.vbar.valueChanged.connect(self._on_scroll)
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setInterval(2500)                              
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self._on_auto_hide_timeout)
    def _on_scale_changed(self, value):
        self._scale = float(value)
        self.update()
    def _on_opacity_changed(self, value):
        self._opacity = float(value)
        self.shadow.setColor(QColor(0, 0, 0, int(80 * self._opacity)))
        self.update()
    def refresh_visibility(self):
        from settings_manager import settings
        if not settings.get('show_scroll_to_top', True):
            self._fade_anim.stop()
            self._opacity = 0.0
            self.hide()
        elif self.vbar:
            self._on_scroll(self.vbar.value())
    def _on_fade_finished(self):
        if self._opacity == 0.0:
            self.hide()
    def _on_auto_hide_timeout(self):
        if not self.is_hovered and self._opacity > 0.0:
            self._fade_anim.stop()
            self._fade_anim.setStartValue(self._opacity)
            self._fade_anim.setEndValue(0.0)
            self._fade_anim.start()
    def _on_scroll(self, value):
        if not settings.get('show_scroll_to_top', True):
            self.hide()
            return
        if value > 300:
            if self.isHidden() or (self._fade_anim.endValue() == 0.0 and self._fade_anim.state() == QVariantAnimation.State.Running) or self._opacity == 0.0:
                self.show()
                self._fade_anim.stop()
                self._fade_anim.setStartValue(self._opacity)
                self._fade_anim.setEndValue(1.0)
                self._fade_anim.start()
            self._auto_hide_timer.start()
        else:
            if not self.isHidden() and self._fade_anim.endValue() != 0.0:
                self._fade_anim.stop()
                self._fade_anim.setStartValue(self._opacity)
                self._fade_anim.setEndValue(0.0)
                self._fade_anim.start()
                self._auto_hide_timer.stop()
    def enterEvent(self, event):
        self.is_hovered = True
        self._auto_hide_timer.stop()                                           
        super().enterEvent(event)
    def leaveEvent(self, event):
        self.is_hovered = False
        self.is_pressed = False
        self._animate_scale(1.0)
        try:
            if self.vbar and self.vbar.value() > 300:
                self._auto_hide_timer.start()
        except RuntimeError:
            pass
        super().leaveEvent(event)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressed = True
            self._animate_scale(0.90)                              
        super().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_pressed:
            self.is_pressed = False
            self._animate_scale(1.0)
            self._scroll_to_top()
        super().mouseReleaseEvent(event)
    def _animate_scale(self, target):
        self._scale_anim.stop()
        self._scale_anim.setStartValue(self._scale)
        self._scale_anim.setEndValue(target)
        self._scale_anim.start()
    def _scroll_to_top(self):
        if not self.vbar: return
        try:
            current_val = self.vbar.value()
        except RuntimeError:
            return
        if not hasattr(self, '_top_anim'):
            self._top_anim = QPropertyAnimation(self.vbar, b"value", self)
            self._top_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._top_anim.stop()
        self._top_anim.setDuration(600)
        self._top_anim.setStartValue(current_val)
        self._top_anim.setEndValue(0)
        self._top_anim.start()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)
        accent_name = settings.get('app_accent_name', 'Teal (AIIKO)')
        base_hex = theme_manager.get_accent_hex(accent_name)
        bg_color = QColor(base_hex)
        if self.is_pressed:
            bg_color = bg_color.darker(115)
        elif self.is_hovered:
            bg_color = bg_color.lighter(115)
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        radius = (min(w, h) / 2.0) * self._scale
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2.0, radius * 2.0))
        pen = QPen(QColor(255, 255, 255))
        pen.setWidthF(3.5 * self._scale)                                 
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        arrow_w = 6.0 * self._scale
        arrow_h = 3.5 * self._scale
        offset_y = -1.5 * self._scale 
        p1 = QPointF(cx - arrow_w, cy + arrow_h + offset_y)
        p2 = QPointF(cx, cy - arrow_h + offset_y)
        p3 = QPointF(cx + arrow_w, cy + arrow_h + offset_y)
        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)
        path.lineTo(p3)
        painter.drawPath(path)
    def update_position(self, parent_width, parent_height, offset_x=0):
        self.move(int(parent_width / 2 - self.width() / 2) + offset_x, parent_height - 70)