import time
import math
from PyQt6.QtCore import Qt, QTime, QTimer, QRect, QSize, pyqtSignal
from PyQt6.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem
from PyQt6.QtGui import QColor, QPen, QPainter, QFont, QFontMetrics
from qfluentwidgets import FluentIcon as FIF
from config import ICON_HEART
_cached_accent = None
_last_accent_time = 0
def _get_accent_color():
    global _cached_accent, _last_accent_time
    import time
    now = time.time()
    if _cached_accent and (now - _last_accent_time) < 1.0:
        return _cached_accent
    try:
        import theme_manager
        _cached_accent = QColor(theme_manager.get_current_accent_hex())
    except Exception:
        _cached_accent = QColor('#1DB954')
    _last_accent_time = now
    return _cached_accent
class AnimatedGridDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_view = parent
        self.hovered_row = -1
        self.hover_start_time = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer)
        self.timer.setInterval(30)          
    def _on_timer(self):
        if self.parent_view and self.hovered_row >= 0:
            window = self.parent_view.window()
            if window and (window.isMinimized() or window.isHidden()):
                self.hovered_row = -1
                self.hover_start_time = 0
                self.timer.stop()
                return
            model = self.parent_view.model()
            if model:
                idx = model.index(self.hovered_row, 0)
                if idx.isValid():
                    self.parent_view.update(idx)
                    return
        self.timer.stop()
    def check_hover_state(self, option, index):
        is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        row = index.row()
        if is_hovered:
            if self.hovered_row != row:
                self.hovered_row = row
                self.hover_start_time = QTime.currentTime().msecsSinceStartOfDay()
        else:
            if self.hovered_row == row:
                self.hovered_row = -1
                self.hover_start_time = 0
                if self.timer.isActive():
                    self.timer.stop()
        return is_hovered
    def draw_marquee_text(self, painter, rect, text, font, font_color, is_hovered):
        painter.save()
        painter.setFont(font)
        painter.setPen(font_color)
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(text)
        painter.setClipRect(rect)
        if not is_hovered or text_width <= rect.width():
            elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, rect.width())
            painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, elided)
        else:
            if not self.timer.isActive():
                self.timer.start()
            current_time = QTime.currentTime().msecsSinceStartOfDay()
            hover_duration = current_time - self.hover_start_time
            delay = 800
            if hover_duration < delay:
                elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, rect.width())
                painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, elided)
            else:
                speed = 0.04
                gap = 40
                total_scroll_width = text_width + gap
                active_time = hover_duration - delay
                offset = (active_time * speed) % total_scroll_width
                x = rect.x() - offset
                painter.drawText(int(x), rect.y(), text_width, rect.height(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, text)
                if x + text_width < rect.right():
                    x_trailing = x + total_scroll_width
                    painter.drawText(int(x_trailing), rect.y(), text_width, rect.height(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, text)
        painter.restore()