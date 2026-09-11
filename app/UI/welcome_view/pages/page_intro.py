import os
import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF, QSequentialAnimationGroup, QParallelAnimationGroup
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer
from UI.welcome_view.components import TEXT_WHITE
APP_ROOT = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
LOGO_PATH = os.path.join(APP_ROOT, "resources", "app", "logo_full.svg")
class SplashWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 300)
        self._svg = QSvgRenderer(LOGO_PATH)
        self._logo_opacity = 0.0
        self._text_opacity = 0.0
        self._logo_y_offset = 20.0
        self._logo_scale = 0.9
        import theme_manager
        self.update_dynamic_colors(theme_manager.get_current_accent_hex())
    def update_dynamic_colors(self, hex_c):
        from PyQt6.QtGui import QPixmap, QColor
        self._accent = QColor(hex_c)
        self._cached_logo = None
        if self._svg.isValid():
            logo_size = 130
            pix = QPixmap(logo_size, logo_size)
            pix.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self._svg.render(painter)
            painter.end()
            self._cached_logo = pix
        self.update()
    @pyqtProperty(float)
    def logo_opacity(self): return self._logo_opacity
    @logo_opacity.setter
    def logo_opacity(self, v): self._logo_opacity = v; self.update()
    @pyqtProperty(float)
    def text_opacity(self): return self._text_opacity
    @text_opacity.setter
    def text_opacity(self, v): self._text_opacity = v; self.update()
    @pyqtProperty(float)
    def logo_y_offset(self): return self._logo_y_offset
    @logo_y_offset.setter
    def logo_y_offset(self, v): self._logo_y_offset = v; self.update()
    @pyqtProperty(float)
    def logo_scale(self): return self._logo_scale
    @logo_scale.setter
    def logo_scale(self, v): self._logo_scale = v; self.update()
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        cx = self.width() / 2
        cy = self.height() / 2
        logo_size = 130
        if self._logo_opacity > 0.01:
            p.save()
            p.setOpacity(self._logo_opacity)
            p.translate(cx, cy - 40 + self._logo_y_offset)
            p.scale(self._logo_scale, self._logo_scale)
            if getattr(self, '_cached_logo', None):
                p.drawPixmap(int(-logo_size/2), int(-logo_size/2), self._cached_logo)
            else:
                self._svg.render(p, QRectF(-logo_size/2, -logo_size/2, logo_size, logo_size))
            p.restore()
        if self._text_opacity > 0.01:
            p.save()
            p.setOpacity(self._text_opacity)
            font = p.font()
            font.setPixelSize(48)
            font.setBold(True)
            p.setFont(font)
            fm = p.fontMetrics()
            text1 = "Aiiko "
            text2 = "Music"
            w1 = fm.horizontalAdvance(text1)
            w2 = fm.horizontalAdvance(text2)
            total_w = w1 + w2
            start_x = (self.width() - total_w) / 2
            text_y = cy + 40
            p.setPen(QColor("#14B8A6"))
            p.drawText(QRectF(start_x, text_y, w1, 60), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text1)
            p.setPen(TEXT_WHITE)
            p.drawText(QRectF(start_x + w1, text_y, w2, 60), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text2)
            p.restore()
class PageIntro(QWidget):
    def __init__(self, overlay, parent=None):
        super().__init__(parent)
        self.overlay = overlay
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.splash = SplashWidget(self)
        layout.addWidget(self.splash)
    def start_intro(self):
        anim_logo_op = QPropertyAnimation(self.splash, b"logo_opacity")
        anim_logo_op.setDuration(800)
        anim_logo_op.setStartValue(0.0)
        anim_logo_op.setEndValue(1.0)
        anim_logo_op.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_logo_y = QPropertyAnimation(self.splash, b"logo_y_offset")
        anim_logo_y.setDuration(800)
        anim_logo_y.setStartValue(20.0)
        anim_logo_y.setEndValue(0.0)
        anim_logo_y.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_logo_scale = QPropertyAnimation(self.splash, b"logo_scale")
        anim_logo_scale.setDuration(800)
        anim_logo_scale.setStartValue(0.8)
        anim_logo_scale.setEndValue(1.0)
        anim_logo_scale.setEasingCurve(QEasingCurve.Type.OutBack)
        group_in = QParallelAnimationGroup(self)
        group_in.addAnimation(anim_logo_op)
        group_in.addAnimation(anim_logo_y)
        group_in.addAnimation(anim_logo_scale)
        anim_text = QPropertyAnimation(self.splash, b"text_opacity")
        anim_text.setDuration(800)
        anim_text.setStartValue(0.0)
        anim_text.setEndValue(1.0)
        anim_text.setEasingCurve(QEasingCurve.Type.InOutCubic)
        seq_text = QSequentialAnimationGroup(self)
        seq_text.addPause(400)                
        seq_text.addAnimation(anim_text)
        group_in.addAnimation(seq_text)
        self.main_seq = QSequentialAnimationGroup(self)
        self.main_seq.addAnimation(group_in)
        self.main_seq.addPause(1500)                
        group_out = QParallelAnimationGroup(self)
        anim_logo_out = QPropertyAnimation(self.splash, b"logo_opacity")
        anim_logo_out.setDuration(600)
        anim_logo_out.setStartValue(1.0)
        anim_logo_out.setEndValue(0.0)
        anim_text_out = QPropertyAnimation(self.splash, b"text_opacity")
        anim_text_out.setDuration(600)
        anim_text_out.setStartValue(1.0)
        anim_text_out.setEndValue(0.0)
        group_out.addAnimation(anim_logo_out)
        group_out.addAnimation(anim_text_out)
        self.main_seq.addAnimation(group_out)
        self.main_seq.finished.connect(self._on_finished)
        self.main_seq.start()
    def _on_finished(self):
        self.overlay._animate_to_page(1)
    def update_dynamic_colors(self, hex_c):
        self.splash.update_dynamic_colors(hex_c)
