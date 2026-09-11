from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QVariantAnimation, QRectF, QPointF, QTimer
from PyQt6.QtWidgets import QWidget, QGraphicsDropShadowEffect
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QPen
from settings_manager import settings
import theme_manager
class LocateTrackButton(QWidget):
    def __init__(self, mw, target_listview, parent=None):
        super().__init__(parent)
        self.mw = mw
        self.target_listview = target_listview
        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hide()
        self.is_hovered = False
        self.is_pressed = False
        self._is_track_present = False
        self._target_index = -1
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
        self.vbar = getattr(self.target_listview, 'verticalScrollBar', lambda: None)()
        if self.vbar:
            self.vbar.valueChanged.connect(self._on_scroll)
        if hasattr(self.mw, 'playback_controller'):
            self.mw.playback_controller.track_loaded.connect(self.check_track_presence)
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setInterval(2500)                              
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self._on_auto_hide_timeout)
    def set_model(self, model):
        try:
            model.layoutChanged.connect(self.check_track_presence)
            model.modelReset.connect(self.check_track_presence)
        except Exception:
            pass
        self.check_track_presence()
    def check_track_presence(self, *args):
        from settings_manager import settings
        if not settings.get('show_locate_track', False) or not self.mw or not self.target_listview or not hasattr(self.mw, 'queue'):
            self._is_track_present = False
            self._target_index = -1
            self._force_hide()
            return
        current_track = self.mw.queue.get_current()
        if not current_track:
            self._is_track_present = False
            self._target_index = -1
            self._force_hide()
            return
        model = self.target_listview.model()
        tracks = getattr(model, 'tracks', None)
        if tracks is None and hasattr(model, 'sourceModel'):
            tracks = getattr(model.sourceModel(), 'tracks', None)
        if tracks is not None:
            if callable(tracks):
                try:
                    tracks = tracks()
                except Exception:
                    pass
            try:
                curr_fp = current_track.filepath
                for i, t in enumerate(tracks):
                    if t.filepath == curr_fp:
                        was_present = self._is_track_present
                        self._is_track_present = True
                        self._target_index = i
                        self._show_button()
                        if not was_present and hasattr(self.parent(), '_update_floating_positions'):
                            self.parent()._update_floating_positions()
                        return
            except Exception:
                pass
        was_present = self._is_track_present
        self._is_track_present = False
        self._target_index = -1
        self._force_hide()
        if was_present and hasattr(self.parent(), '_update_floating_positions'):
            self.parent()._update_floating_positions()
    def refresh_visibility(self):
        self.check_track_presence()
    def _show_button(self):
        if not self._is_track_present: return
        if self.isHidden() or (self._fade_anim.endValue() == 0.0 and self._fade_anim.state() == QVariantAnimation.State.Running) or self._opacity == 0.0:
            self.show()
            self._fade_anim.stop()
            self._fade_anim.setStartValue(self._opacity)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.start()
        self._auto_hide_timer.start()
    def _force_hide(self):
        if not self.isHidden() and self._fade_anim.endValue() != 0.0:
            self._fade_anim.stop()
            self._fade_anim.setStartValue(self._opacity)
            self._fade_anim.setEndValue(0.0)
            self._fade_anim.start()
            self._auto_hide_timer.stop()
    def _on_scale_changed(self, value):
        self._scale = float(value)
        self.update()
    def _on_opacity_changed(self, value):
        self._opacity = float(value)
        self.shadow.setColor(QColor(0, 0, 0, int(80 * self._opacity)))
        self.update()
    def _on_fade_finished(self):
        if self._opacity == 0.0:
            self.hide()
    def _on_auto_hide_timeout(self):
        if not self.is_hovered and self._opacity > 0.0:
            self._force_hide()
    def _on_scroll(self, value):
        if self._is_track_present:
            self._show_button()
        else:
            self._force_hide()
    def enterEvent(self, event):
        self.is_hovered = True
        self._auto_hide_timer.stop()                                           
        super().enterEvent(event)
    def leaveEvent(self, event):
        self.is_hovered = False
        self.is_pressed = False
        self._animate_scale(1.0)
        self._auto_hide_timer.start()
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
            self._locate_track()
        super().mouseReleaseEvent(event)
    def _animate_scale(self, target):
        self._scale_anim.stop()
        self._scale_anim.setStartValue(self._scale)
        self._scale_anim.setEndValue(target)
        self._scale_anim.start()
    def _locate_track(self):
        if not self.target_listview or self._target_index < 0: return
        try:
            model = self.target_listview.model()
            index = model.index(self._target_index, 0)
            from PyQt6.QtWidgets import QAbstractItemView
            self.target_listview.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)
        except Exception as e:
            pass
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
        pen.setWidthF(2.5 * self._scale)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        gap = 3 * self._scale
        length = 6 * self._scale
        painter.drawLine(QPointF(cx, cy - gap - length), QPointF(cx, cy - gap))
        painter.drawLine(QPointF(cx, cy + gap), QPointF(cx, cy + gap + length))
        painter.drawLine(QPointF(cx - gap - length, cy), QPointF(cx - gap, cy))
        painter.drawLine(QPointF(cx + gap, cy), QPointF(cx + gap + length, cy))
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        dot_radius = 1.5 * self._scale
        painter.drawEllipse(QRectF(cx - dot_radius, cy - dot_radius, dot_radius * 2, dot_radius * 2))
    def update_position(self, parent_width, parent_height, offset_x=0):
        self.move(int(parent_width / 2 - self.width() / 2) + offset_x, parent_height - 70)