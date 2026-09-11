import os
import sys
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QRectF
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QLinearGradient, QRadialGradient,
    QFont, QFontDatabase, QPen, QIcon, QPainterPath
)
from PyQt6.QtWidgets import QWidget, QApplication, QGraphicsOpacityEffect
from PyQt6.QtSvg import QSvgRenderer
from qframelesswindow import AcrylicWindow
from core.language_manager import tr
APP_ROOT = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGO_PATH = os.path.join(APP_ROOT, "resources", "app", "logo_splash_screen.svg")
import theme_manager
BG_DARK   = QColor("#0A0A0F")
BG_MID    = QColor("#12101C")
TEXT_DIM   = QColor("#7A7490")
class SplashScreen(AcrylicWindow):
    def __init__(self):
        super().__init__()
        self.titleBar.hide()
        self.setWindowFlags(
            Qt.WindowType.SplashScreen 
            | Qt.WindowType.FramelessWindowHint 
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(300, 360)
        self._center_on_screen()
        self.windowEffect.setAcrylicEffect(self.winId(), "180D32A0", enableShadow=False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._progress = 0
        self._status_text = tr("Preparando tu biblioteca...")
        self._text_opacity = 1.0
        self._svg = QSvgRenderer(LOGO_PATH) if os.path.exists(LOGO_PATH) else None
        self._accent = QColor("#14B8A6")
        self._primary = self._accent.darker(120)
        self._cached_logo = None
        if self._svg and self._svg.isValid():
            logo_size = 110
            pix = QPixmap(logo_size, logo_size)
            pix.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self._svg.render(painter)
            painter.end()
            self._cached_logo = pix
    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)
    def set_progress(self, value, status=""):
        self._progress = max(0, min(100, value))
        self.update()
    def finish(self, main_window):
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(400)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        fade_out.finished.connect(lambda: self._on_fade_out_done(main_window))
        self._fade_out_anim = fade_out              
        fade_out.start()
    def _on_fade_out_done(self, main_window):
        if getattr(main_window, '_start_maximized', False):
            main_window.showMaximized()
        else:
            main_window.show()
        self.close()
        self.deleteLater()
    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        p.fillRect(self.rect(), Qt.GlobalColor.transparent)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        w, h = self.width(), self.height()
        logo_size = 110
        logo_x = (w - logo_size) // 2
        logo_y = int(h * 0.12)
        if getattr(self, '_cached_logo', None):
            p.drawPixmap(logo_x, logo_y, self._cached_logo)
        elif self._svg and self._svg.isValid():
            self._svg.render(p, QRectF(logo_x, logo_y, logo_size, logo_size))
        else:
            icon_size = 70
            icon_cx = w / 2
            icon_cy = logo_y + logo_size / 2
            icon_r = icon_size / 2 - 2
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 20))
            p.drawEllipse(QRectF(icon_cx - icon_r, icon_cy - icon_r, icon_r * 2, icon_r * 2))
            pen = QPen(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 100), 2)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(icon_cx - icon_r, icon_cy - icon_r, icon_r * 2, icon_r * 2))
            font_family = self.font().family()
            note_font = QFont(font_family, 26)
            p.setFont(note_font)
            p.setPen(self._accent)
            p.drawText(QRectF(icon_cx - icon_r, icon_cy - icon_r, icon_r * 2, icon_r * 2),
                       Qt.AlignmentFlag.AlignCenter, "♪")
        p.setOpacity(self._text_opacity)
        font_family = self.font().family()
        title_font = QFont(font_family, 20, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        p.setFont(title_font)
        fm = p.fontMetrics()
        text1 = "Aiiko "
        text2 = "Music"
        w1 = fm.horizontalAdvance(text1)
        w2 = fm.horizontalAdvance(text2)
        total_w = w1 + w2
        start_x = (w - total_w) // 2
        title_y = logo_y + logo_size + 15
        p.setPen(QColor("#14B8A6"))
        p.drawText(QRectF(start_x, title_y, w1, 30), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text1)
        p.setPen(QColor(255, 255, 255, 240))
        p.drawText(QRectF(start_x + w1, title_y, w2, 30), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text2)
        bar_w = int(w * 0.6)
        bar_h = 2
        bar_x = (w - bar_w) // 2
        bar_y = title_y + 40
        radius = bar_h / 2
        p.setOpacity(self._text_opacity * 0.6)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 20))
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), radius, radius)
        if self._progress > 0:
            p.setOpacity(self._text_opacity)
            fill_w = max(bar_h, int(bar_w * self._progress / 100))
            bar_grad = QLinearGradient(bar_x, 0, bar_x + bar_w, 0)
            bar_grad.setColorAt(0.0, self._primary)
            bar_grad.setColorAt(1.0, self._accent)
            p.setBrush(bar_grad)
            p.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), radius, radius)
        status_font = QFont(font_family, 9)
        p.setFont(status_font)
        p.setPen(QColor(200, 200, 210, int(200 * self._text_opacity)))
        p.drawText(0, bar_y + bar_h + 20, w, 20, Qt.AlignmentFlag.AlignCenter, self._status_text)
        version_font = QFont(font_family, 9)
        p.setFont(version_font)
        p.setPen(QColor(150, 150, 160, int(150 * self._text_opacity)))
        from config import APP_VERSION
        version_str = f"v{APP_VERSION}"
        p.drawText(0, h - 30, w, 20, Qt.AlignmentFlag.AlignCenter, version_str)
        p.setOpacity(1.0)
        p.end()