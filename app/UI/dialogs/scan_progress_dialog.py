import os
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QFont, QPen, QPainterPath
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from settings_manager import settings
import theme_manager
from core.language_manager import tr
def _get_dialog_colors():
    theme_name = settings.get('app_theme', 'Oscuro (Dark)')
    theme = theme_manager.get_theme(theme_name)
    accent_hex = theme_manager.get_current_accent_hex()
    main_bg = QColor(theme.get('main_bg', '#202020'))
    bg_dark = main_bg.darker(105)
    bg_mid = main_bg
    bg_bottom = main_bg.darker(108)
    accent = QColor(accent_hex)
    accent_light = QColor(accent_hex)
    accent_light.setAlphaF(0.7)
    lightness = main_bg.lightnessF()
    if lightness < 0.3:
        text_primary = QColor(232, 228, 240)
        text_dim = QColor(122, 116, 144)
    else:
        text_primary = QColor(30, 30, 40)
        text_dim = QColor(90, 85, 110)
    return {
        'bg_dark': bg_dark, 'bg_mid': bg_mid, 'bg_bottom': bg_bottom,
        'accent': accent, 'accent_light': accent_light,
        'text_primary': text_primary, 'text_dim': text_dim,
        'border': QColor(255, 255, 255, 18) if lightness < 0.3 else QColor(0, 0, 0, 25),
    }
class _ProgressBarWidget(QWidget):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self._progress = 0
        self._colors = colors
    def set_progress(self, value):
        self._progress = max(0, min(100, value))
        self.update()
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bar_h = 6
        bar_y = 4
        bar_w = w
        radius = bar_h / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 15))
        p.drawRoundedRect(QRectF(0, bar_y, bar_w, bar_h), radius, radius)
        if self._progress > 0:
            fill_w = max(bar_h, bar_w * self._progress / 100)
            grad = QLinearGradient(0, 0, bar_w, 0)
            grad.setColorAt(0.0, self._colors['accent'])
            grad.setColorAt(1.0, self._colors['accent_light'])
            p.setBrush(grad)
            p.drawRoundedRect(QRectF(0, bar_y, fill_w, bar_h), radius, radius)
        pct_font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        p.setFont(pct_font)
        p.setPen(self._colors['accent'])
        p.drawText(QRectF(0, bar_y + bar_h + 4, bar_w, 24),
                   Qt.AlignmentFlag.AlignCenter, f"{self._progress}%")
        p.end()
class _BackdropOverlay(QWidget):
    def __init__(self, parent, dialog=None):
        super().__init__(parent)
        self._dialog = dialog
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background: transparent;")
        if parent:
            self.setGeometry(0, 0, parent.width(), parent.height())
            parent.installEventFilter(self)
    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Move) and obj == self.parent():
            self.setGeometry(0, 0, obj.width(), obj.height())
            if self._dialog:
                self._dialog._center_on_parent(obj)
        return False
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 190))
        p.end()
class ScanProgressDialog(QWidget):
    _MAX_FILENAME_LEN = 38                                           
    def __init__(self, parent=None):
        super().__init__(parent)
        self._colors = _get_dialog_colors()
        self._parent_ref = parent
        self._backdrop = None
        if parent:
            self._backdrop = _BackdropOverlay(parent, dialog=self)
            self._backdrop.show()
            self._backdrop.raise_()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(380, 160)
        self._build_ui()
        self._center_on_parent(parent)
        self.raise_()
    def _center_on_parent(self, parent):
        if parent:
            x = (parent.width() - self.width()) // 2
            y = (parent.height() - self.height()) // 2
            self.move(x, y)
        else:
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move((geo.width() - self.width()) // 2,
                          (geo.height() - self.height()) // 2)
    def _build_ui(self):
        c = self._colors
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._card = QWidget()
        self._card.setFixedSize(380, 160)
        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(36, 28, 36, 24)
        card_layout.setSpacing(0)
        self._title = QLabel(tr("Analizando archivos..."))
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(
            f"color: {c['text_primary'].name()}; font-size: 18px; font-weight: 600; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        card_layout.addWidget(self._title)
        card_layout.addSpacing(6)
        self._subtitle = QLabel(tr("Buscando e identificando tu música local"))
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle.setFixedWidth(308)                                  
        self._subtitle.setStyleSheet(
            f"color: {c['text_dim'].name()}; font-size: 12px; "
            f"font-family: 'Segoe UI'; background: transparent;"
        )
        card_layout.addWidget(self._subtitle, 0, Qt.AlignmentFlag.AlignHCenter)
        card_layout.addSpacing(20)
        self._progress_bar = _ProgressBarWidget(c)
        card_layout.addWidget(self._progress_bar)
        card_layout.addStretch()
        layout.addWidget(self._card)
    def paintEvent(self, event):
        c = self._colors
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        path = QPainterPath()
        fluent_radius = 8.0                                                 
        path.addRoundedRect(QRectF(0, 0, w, h), fluent_radius, fluent_radius)
        p.setClipPath(path)
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0.0, c['bg_dark'])
        bg.setColorAt(0.5, c['bg_mid'])
        bg.setColorAt(1.0, c['bg_bottom'])
        p.fillPath(path, bg)
        p.setClipping(False)
        p.setPen(QPen(c['border'], 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), fluent_radius, fluent_radius)
        p.end()
    def _truncate(self, text, max_len):
        if len(text) <= max_len:
            return text
        return text[:max_len - 1] + "…"
    def update_details(self, text):
        basename = os.path.basename(text)
        truncated = self._truncate(basename, self._MAX_FILENAME_LEN)
        self._subtitle.setText(tr("Procesando: {file}").format(file=truncated))
    def update_progress(self, value):
        self._progress_bar.set_progress(value)
    def set_title(self, text):
        self._title.setText(text)
    def accept(self):
        if self._backdrop:
            self._backdrop.hide()
            self._backdrop.deleteLater()
            self._backdrop = None
        self.close()
        self.deleteLater()