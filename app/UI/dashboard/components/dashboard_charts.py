from datetime import date
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFont, QLinearGradient
from PyQt6.QtWidgets import QWidget
class WeeklyBarChart(QWidget):
    _ALL_DAYS = ["L", "M", "X", "J", "V", "S", "D"]
    def __init__(self, parent=None):
        super().__init__(parent)
        self._values = [0] * 7
        self._accent = "#7C3AED"
        self._hover_idx = -1
        self.setMouseTracking(True)
        self.setStyleSheet("background: transparent;")
    def set_data(self, values, accent="#7C3AED"):
        self._values = values
        self._accent = accent
        self.update()
    def mouseMoveEvent(self, event):
        w = self.width()
        n = len(self._values)
        if n == 0:
            return super().mouseMoveEvent(event)
        slot_w = w / n
        idx = int(event.pos().x() / slot_w)
        if 0 <= idx < n:
            if self._hover_idx != idx:
                self._hover_idx = idx
                self.update()
        else:
            if self._hover_idx != -1:
                self._hover_idx = -1
                self.update()
        super().mouseMoveEvent(event)
    def leaveEvent(self, event):
        if self._hover_idx != -1:
            self._hover_idx = -1
            self.update()
        super().leaveEvent(event)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        n = len(self._values)
        if n == 0:
            return
        max_val = max(self._values) or 1
        bar_w = max(4, int(w / n * 0.55))
        slot_w = w / n
        label_h = 16
        bar_area = h - label_h
        accent = QColor(self._accent)
        today_idx = 6                                                      
        today_wd = date.today().weekday()
        day_labels = [self._ALL_DAYS[(today_wd - (today_idx - i)) % 7] for i in range(n)]
        for i, val in enumerate(self._values):
            x = int(i * slot_w + (slot_w - bar_w) / 2)
            bar_h = max(4, int(val / max_val * (bar_area - 8)))
            y = bar_area - bar_h
            if i == today_idx or i == self._hover_idx:
                grad = QLinearGradient(x, y, x, y + bar_h)
                top_color = QColor(accent)
                if i == self._hover_idx and i != today_idx:
                    top_color = top_color.lighter(130)
                top_color.setAlpha(255)
                bot_color = QColor(accent)
                bot_color.setAlpha(140)
                grad.setColorAt(0, top_color)
                grad.setColorAt(1, bot_color)
                painter.setBrush(grad)
            else:
                dim = QColor(accent)
                dim.setAlpha(55)
                painter.setBrush(dim)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, bar_w, bar_h, 3, 3)
            label_font = self.font()
            label_font.setPixelSize(11)
            if i == today_idx or i == self._hover_idx:
                label_font.setBold(True)
                painter.setPen(accent)
            else:
                label_font.setBold(False)
                painter.setPen(QColor("#888888"))
            painter.setFont(label_font)
            lbl = day_labels[i]
            painter.drawText(int(x + bar_w / 2) - 4, h - 2, lbl)
        if self._hover_idx != -1:
            idx = self._hover_idx
            val = self._values[idx]
            from core.language_manager import tr
            tooltip_txt = tr("1 canción") if val == 1 else tr("{count} canciones").format(count=val)
            tooltip_font = self.font()
            tooltip_font.setPixelSize(12)
            painter.setFont(tooltip_font)
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(tooltip_txt) + 16
            th = fm.height() + 10
            x_center = int(idx * slot_w + slot_w / 2)
            tx = x_center - tw // 2
            tx = max(0, min(tx, w - tw))                   
            bar_h = max(4, int(val / max_val * (bar_area - 8)))
            ty = int(bar_area - bar_h - th - 8)
            if ty < 0: 
                ty = int(bar_area - bar_h + 8)                                     
            painter.setBrush(QColor(25, 25, 30, 245))
            painter.setPen(QColor(60, 60, 70, 200))
            painter.drawRoundedRect(tx, ty, tw, th, 6, 6)
            painter.setPen(QColor(240, 240, 240))
            painter.drawText(tx, ty, tw, th, Qt.AlignmentFlag.AlignCenter, tooltip_txt)
        painter.end()