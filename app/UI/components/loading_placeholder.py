from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtGui import QPainter, QColor, QFontMetrics, QFont
from PyQt6.QtCore import Qt, QTimer, QSize
from qfluentwidgets import CaptionLabel, themeColor, isDarkTheme
import math
import time
class AiikoLoadingLogo(QWidget):
    def __init__(self, parent=None, use_glitch=True):
        super().__init__(parent)
        self.use_glitch = use_glitch
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.full_text = "Aiiko Music"
        self.chars = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()-_=+{}|[]\\;:\'\"<>?,./`~')
        self.cycle_count = 4                                      
        self.frame_counter = 0
        self._cached_x_positions = []
        self._total_width = 0
        self._accent_color = None
        self._text_color = None
        self._is_metrics_cached = False
        self._reset_state()
    def _reset_state(self):
        self.letter_current = 0
        self.cycle_current = 0
        self.done = False
        self.letter_states = []
        for c in self.full_text:
            if c == ' ' or not self.use_glitch:
                self.letter_states.append((c, 1.0, True))
            else:
                self.letter_states.append(('-', 0.0, False))
    def update_animation(self):
        self.frame_counter += 1
        if self.use_glitch and self.frame_counter % 3 == 0 and not self.done:
            self._update_glitch()
        self.update()                                          
    def _update_glitch(self):
        import random
        while self.letter_current < len(self.full_text) and self.full_text[self.letter_current] == ' ':
            self.letter_current += 1
        if self.letter_current >= len(self.full_text):
            self.done = True
            QTimer.singleShot(2500, self._reset_state)                                           
            return
        for i in range(self.letter_current, len(self.full_text)):
            if self.full_text[i] != ' ':
                random_char = random.choice(self.chars)
                random_opacity = random.uniform(0.2, 0.8)
                self.letter_states[i] = (random_char, random_opacity, False)
        if self.cycle_current < self.cycle_count:
            self.cycle_current += 1
        else:
            self.letter_states[self.letter_current] = (self.full_text[self.letter_current], 1.0, True)
            self.cycle_current = 0
            self.letter_current += 1
    def showEvent(self, e):
        super().showEvent(e)
        self._reset_state()
        from qfluentwidgets import themeColor, isDarkTheme
        self._accent_color = themeColor()
        from PyQt6.QtGui import QColor
        self._text_color = QColor(255, 255, 255) if isDarkTheme() else QColor(0, 0, 0)
        self.timer.start(16)         
    def hideEvent(self, e):
        super().hideEvent(e)
        self.timer.stop()
    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(280, 80)
    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QFont, QFontMetrics
        from PyQt6.QtCore import QRectF
        import time
        import math
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = self.font()
        font.setPixelSize(36)
        font.setWeight(QFont.Weight.Bold)
        painter.setFont(font)
        if not self._is_metrics_cached:
            fm = QFontMetrics(font)
            current_x = 0
            for char in self.full_text:
                self._cached_x_positions.append(current_x)
                current_x += fm.horizontalAdvance(char)
            self._total_width = current_x
            self._is_metrics_cached = True
        x_start = (self.width() - self._total_width) / 2.0
        y_text = self.height() / 2.0 + 12 
        for i, (char, opacity, is_resolved) in enumerate(self.letter_states):
            x = x_start + self._cached_x_positions[i]
            if is_resolved:
                if i < 5:          
                    color = self._accent_color
                else:          
                    color = self._text_color
            else:
                color = QColor(self._accent_color)
                color.setAlphaF(opacity)
            painter.setPen(color)
            painter.drawText(int(x), int(y_text), char)
            if is_resolved and i < 5:
                glow = QColor(color)
                glow.setAlphaF(0.3)
                painter.setPen(glow)
                painter.drawText(int(x - 1), int(y_text), char)
                painter.drawText(int(x + 1), int(y_text), char)
        line_y = y_text + 12
        t = time.time() * 1.5                         
        cycle = int(t)
        tau = t - cycle                  
        eased_progress = 1.0 - (1.0 - tau)**3
        stretch = math.sin(math.pi * tau)
        MAX_TAIL = 50                         
        current_tail = MAX_TAIL * stretch
        if cycle % 2 == 0:
            head_x = x_start + (self._total_width * eased_progress)
            tail_x = head_x - current_tail              
        else:
            head_x = (x_start + self._total_width) - (self._total_width * eased_progress)
            tail_x = head_x + current_tail              
        left_edge = min(head_x, tail_x)
        right_edge = max(head_x, tail_x)
        if right_edge - left_edge < 5:
            if cycle % 2 == 0 and tau < 0.5:
                right_edge = left_edge + 5
            elif cycle % 2 == 0 and tau >= 0.5:
                left_edge = right_edge - 5
            elif cycle % 2 == 1 and tau < 0.5:
                left_edge = right_edge - 5
            else:
                right_edge = left_edge + 5
        left_edge = max(x_start, left_edge)
        right_edge = min(x_start + self._total_width, right_edge)
        if right_edge - left_edge < 5:
            if left_edge == x_start:
                right_edge = left_edge + 5
            else:
                left_edge = right_edge - 5
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._accent_color)
        painter.drawRect(QRectF(left_edge, line_y, right_edge - left_edge, 5.0))
        painter.end()
class LoadingPlaceholder(QWidget):
    def __init__(self, title_suffix="", use_glitch=True):
        super().__init__()
        self.is_placeholder = True
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo = AiikoLoadingLogo(self, use_glitch=use_glitch)
        layout.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignCenter)
        if title_suffix:
            self.sub_label = CaptionLabel(title_suffix)
            self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sub_label.setStyleSheet("color: rgba(255, 255, 255, 0.4);")
            layout.addWidget(self.sub_label)