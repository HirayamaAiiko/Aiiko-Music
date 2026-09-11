import os, sys
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QRadialGradient
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton, QGraphicsOpacityEffect
from settings_manager import settings
import theme_manager
from core.language_manager import tr
from qfluentwidgets import ProgressBar, PrimaryPushButton, PushButton
from UI.welcome_view.components import SvgLogoWidget, make_label, TEXT_WHITE, TEXT_DIM
from UI.welcome_view.pages.page_intro import PageIntro
from UI.welcome_view.pages.page_lang import PageLang
from UI.welcome_view.pages.page_library import PageLibrary
from UI.welcome_view.pages.page_user import PageUser
from UI.welcome_view.pages.page_accent import PageAccent
from UI.welcome_view.pages.page_ready import PageReady
APP_ROOT = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LOGO_PATH = os.path.join(APP_ROOT, "resources", "app", "logo.svg")
BG_DARK = QColor("#050508")
class WelcomeOverlay(QWidget):
    finished = pyqtSignal()
    def __init__(self, main_window, parent=None):
        super().__init__(parent or main_window)
        self.main_window = main_window
        self._current_page = 0
        self._animating = False
        self._language_changed = False
        self._original_language = settings.get('language', 'es')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        self._current_accent = theme_manager.get_accent_hex(settings.get('app_accent_name', 'Cian (AIIKO)'))
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 60, 40, 60)
        self.main_layout.setSpacing(24)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setFixedWidth(600)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar, 0, Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.addSpacing(16)
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")
        self.pages = [
            PageIntro(self),
            PageLang(self),
            PageLibrary(self),
            PageUser(self),
            PageAccent(self),
            PageReady(self)
        ]
        for p in self.pages: 
            self.stack.addWidget(p)
        self.main_layout.addWidget(self.stack, 1)
        nav_lo = QHBoxLayout()
        nav_lo.setContentsMargins(0, 20, 0, 0)
        nav_lo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_lo.setSpacing(24)
        self.btn_back = PushButton(tr("← Atrás"))
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self._on_back)
        self.btn_back.setVisible(False)
        self.btn_skip = PushButton(tr("Omitir"))
        self.btn_skip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_skip.clicked.connect(self._on_finish)
        self.btn_skip.setVisible(False)
        self.btn_next = PrimaryPushButton(tr("Continuar →"))
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.clicked.connect(self._on_next)
        self.bottom_container = QWidget()
        self.bottom_container.setFixedWidth(600)
        self.bottom_container.setVisible(False)
        bottom_layout = QHBoxLayout(self.bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.addWidget(self.btn_back)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_skip)
        bottom_layout.addWidget(self.btn_next)
        self.main_layout.addWidget(self.bottom_container, 0, Qt.AlignmentFlag.AlignHCenter)
        self.update_dynamic_colors(self._current_accent)
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        import theme_manager
        from settings_manager import settings
        theme_name = settings.get('app_theme', 'Oscuro (Dark)')
        td = theme_manager.get_theme(theme_name)
        bg_hex = td.get('main_bg', '#202020')
        p.fillRect(self.rect(), QColor(bg_hex))
        p.end()
    def update_dynamic_colors(self, hex_c):
        self._current_accent = hex_c
        self.update()
        for p in self.pages:
            if hasattr(p, 'update_dynamic_colors'):
                p.update_dynamic_colors(hex_c)
    def show_animated(self, instant=False):
        self.show()
        self.raise_()
        if instant:
            self._opacity.setOpacity(1.0)
            if self._current_page == 0 and hasattr(self.pages[0], 'start_intro'):
                QTimer.singleShot(150, self.pages[0].start_intro)
        else:
            f = QPropertyAnimation(self._opacity, b"opacity")
            f.setDuration(800)
            f.setStartValue(0.0)
            f.setEndValue(1.0)
            f.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._fade_in_anim = f
            if self._current_page == 0 and hasattr(self.pages[0], 'start_intro'):
                f.finished.connect(self.pages[0].start_intro)
            f.start()
    def _on_next(self):
        if self._animating: return
        if self._current_page < len(self.pages) - 1:
            self._animate_to_page(self._current_page + 1)
        else:
            self._on_finish()
    def _on_back(self):
        if self._animating: return
        if self._current_page > 0:
            self._animate_to_page(self._current_page - 1)
    def _animate_to_page(self, target):
        if self._animating: return
        self._animating = True
        self.stack.setCurrentIndex(target)
        self._current_page = target
        total_steps = len(self.pages) - 1
        val = int((target / total_steps) * 100) if target > 0 else 0
        self.progress_bar.setValue(val)
        self.progress_bar.setVisible(target > 0)
        self.bottom_container.setVisible(target > 0)
        self.btn_back.setVisible(target > 1)
        if target == len(self.pages) - 1:
            self.btn_next.setVisible(False)                                         
            self.btn_skip.setVisible(False)
            if hasattr(self.pages[target], 'start_scan'):
                self.pages[target].start_scan()
        else:
            self.btn_next.setVisible(True)
            self.btn_next.setText(tr("Continuar →"))
            self.btn_skip.setVisible(target > 1)
        self._animating = False
    def retranslate_ui(self):
        for p in self.pages:
            if hasattr(p, 'retranslate_ui'):
                p.retranslate_ui()
        if hasattr(self, 'btn_next'):
            if self._current_page != len(self.pages) - 1:
                self.btn_next.setText(tr("Continuar →"))
        if hasattr(self, 'btn_back'):
            self.btn_back.setText(tr("← Atrás"))
        if hasattr(self, 'btn_skip'):
            self.btn_skip.setText(tr("Omitir"))
    def _on_finish(self):
        if getattr(self, '_animating', False): return
        self._animating = True
        settings.set('welcome_completed', True)
        settings.save()
        needs_restart = getattr(self, '_language_changed', False)
        if needs_restart:
            self._restart_pending = True
            QTimer.singleShot(1000, self._do_restart)
        self._close_welcome()
    def _close_welcome(self):
        f = QPropertyAnimation(self._opacity, b"opacity")
        f.setDuration(500)
        f.setStartValue(1.0)
        f.setEndValue(0.0)
        f.setEasingCurve(QEasingCurve.Type.InCubic)
        f.finished.connect(self._cleanup)
        self._fade_out_anim = f
        f.start()
    def _cleanup(self):
        self.finished.emit()
        self.hide()
        if not getattr(self, '_restart_pending', False):
            self.deleteLater()
    def _do_restart(self):
        import sys, subprocess
        from PyQt6.QtWidgets import QApplication
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable, '--restart'])
        else:
            subprocess.Popen([sys.executable] + sys.argv + ['--restart'])
        QApplication.quit()
