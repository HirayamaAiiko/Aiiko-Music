import logging
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QObject
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QWidget
from qfluentwidgets import InfoBarPosition, MessageBox, PushButton, TitleLabel, BodyLabel, FluentIcon as FIF, IconWidget, TransparentToolButton, MessageBoxBase
from settings_manager import settings
import theme_manager
from core.language_manager import tr
_TOAST_TYPES = {
    'success': (None, FIF.COMPLETED),                                
    'warning': ("#f59e0b", FIF.INFO),
    'error':   ("#ef4444", FIF.CLOSE),
    'info':    ("#3b82f6", FIF.INFO),
}
class AiikoToast(QFrame):
    closed = pyqtSignal()
    W = 340
    H = 68
    __slots__ = ('_timer',)
    def __init__(self, title, content, icon_type, parent=None, duration=3500):
        super().__init__(parent)
        accent = theme_manager.get_accent_hex(settings.get('app_accent_name', 'Teal (AIIKO)'))
        border_color, icon_name = _TOAST_TYPES.get(icon_type, _TOAST_TYPES['info'])
        if border_color is None:
            border_color = accent                                  
        is_dark = settings.get('themeMode', 'Dark') == 'Dark'
        bg     = "#1E1E20" if is_dark else "#F5F5F5"
        fg_sub = "#DDDDDD" if is_dark else "#333333"
        bd     = "rgba(255,255,255,0.06)" if is_dark else "rgba(0,0,0,0.08)"
        self.setFixedSize(self.W, self.H)
        self.setStyleSheet(
            f"AiikoToast{{"
            f"background-color:{bg};"
            f"border-top-left-radius:0px;border-bottom-left-radius:0px;"
            f"border-top-right-radius:8px;border-bottom-right-radius:8px;"
            f"border:1px solid {bd};border-left:4px solid {border_color};}}"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 8, 0)
        lay.setSpacing(10)
        from PyQt6.QtGui import QColor
        icon_w = IconWidget(icon_name.icon(color=QColor(border_color)))
        icon_w.setFixedSize(20, 20)
        txt_lay = QVBoxLayout()
        txt_lay.setSpacing(2)
        txt_lay.setContentsMargins(0, 0, 0, 0)
        if title:
            lt = QLabel(title)
            lt.setStyleSheet(f"font-weight:bold;font-size:14px;color:{border_color};background:transparent;border:none;")
            txt_lay.addWidget(lt)
        if content:
            lc = QLabel(content)
            lc.setStyleSheet(f"font-size:12px;color:{fg_sub};background:transparent;border:none;")
            lc.setWordWrap(True)
            txt_lay.addWidget(lc)
        close_btn = TransparentToolButton(FIF.CLOSE)
        close_btn.setFixedSize(22, 22)
        close_btn.setIconSize(close_btn.size() * 0.5)
        close_btn.setStyleSheet("border:none;background:transparent;")
        close_btn.clicked.connect(self._dismiss)
        lay.addWidget(icon_w, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addLayout(txt_lay, 1)
        lay.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(duration)
        self._timer.timeout.connect(self._dismiss)
    def show_toast(self):
        self.raise_()
        self.show()
        self._timer.start()
    def _dismiss(self):
        self._timer.stop()
        self.hide()
        self.closed.emit()
        self.deleteLater()
class ToastManager(QObject):
    _MARGIN_R = 20
    _MARGIN_T = 48
    _GAP = 8
    __slots__ = ('_toasts',)
    def __init__(self):
        super().__init__()
        self._toasts = []
    def _get_valid_toasts(self):
        valid = []
        for t in self._toasts:
            try:
                if not t.isHidden():
                    valid.append(t)
            except RuntimeError:
                pass
        return valid
    def show_toast(self, toast, pw):
        toast.setParent(pw)
        valid_toasts = self._get_valid_toasts()
        self._toasts = valid_toasts + [toast]
        x = pw.width() - AiikoToast.W - self._MARGIN_R
        y = self._MARGIN_T + len(valid_toasts) * (AiikoToast.H + self._GAP)
        toast.move(x, y)
        toast.closed.connect(self._on_closed)
        toast.show_toast()
    def _on_closed(self):
        toast = self.sender()
        if not toast:
            return
        try:
            pw = toast.parent()
        except RuntimeError:
            pw = None
        if toast in self._toasts:
            self._toasts.remove(toast)
        self._toasts = self._get_valid_toasts()
        if pw:
            x = pw.width() - AiikoToast.W - self._MARGIN_R
            y = self._MARGIN_T
            for t in self._toasts:
                try:
                    t.move(x, y)
                    y += AiikoToast.H + self._GAP
                except RuntimeError:
                    pass
_toast_mgr = ToastManager()
class NotificationManager:
    def __init__(self):
        self.main_window = None
    def initialize(self, main_window):
        self.main_window = main_window
    def _get_parent(self, parent):
        return parent if parent else self.main_window
    def success(self, title, content, parent=None):
        p = self._get_parent(parent)
        if p:
            t = AiikoToast(title, content, 'success', duration=3000)
            _toast_mgr.show_toast(t, p)
    def info(self, title, content, parent=None):
        p = self._get_parent(parent)
        if p:
            t = AiikoToast(title, content, 'info', duration=3000)
            _toast_mgr.show_toast(t, p)
    def warning(self, title, content, parent=None):
        p = self._get_parent(parent)
        if p:
            t = AiikoToast(title, content, 'warning', duration=4500)
            _toast_mgr.show_toast(t, p)
    def error(self, title, content, parent=None):
        p = self._get_parent(parent)
        if p:
            t = AiikoToast(title, content, 'error', duration=5500)
            _toast_mgr.show_toast(t, p)
            logging.error(f"[Notificación] {title}: {content}")
    def confirm(self, title, content, parent=None):
        p = self._get_parent(parent)
        if not p: return False
        dialog = MessageBox(title, content, p)
        dialog.yesButton.setText("Sí")
        dialog.cancelButton.setText("Cancelar")
        return dialog.exec()
    def confirm_destructive(self, title, content, btn_soft_text, btn_hard_text, parent=None):
        p = self._get_parent(parent)
        if not p: return 0
        from UI.dialogs.confirm_destructive_dialog import ConfirmDestructiveDialog
        dialog = ConfirmDestructiveDialog(title, content, btn_soft_text, btn_hard_text, p)
        dialog.exec()
        return dialog.result_code
notify = NotificationManager()