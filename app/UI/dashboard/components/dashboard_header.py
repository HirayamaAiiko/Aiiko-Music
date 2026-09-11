from datetime import datetime
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from qfluentwidgets import TitleLabel, BodyLabel, TransparentToolButton
from UI.user_profile_widget import UserProfileButton, is_birthday_today
import theme_manager
from core.language_manager import tr
class DashboardHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setStyleSheet("background: transparent;")
        self._build_ui()
        self._update_greeting()
    def _get_accent(self):
        from settings_manager import settings
        return theme_manager.get_accent_hex(settings.get('app_accent_name', 'Teal (AIIKO)'))
    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 4, 0, 12)
        main_layout.setSpacing(16)
        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(4)
        self.greeting_label = TitleLabel("")
        self.greeting_label.setStyleSheet("font-size: 28px; font-weight: bold; background: transparent;")
        text_col.addWidget(self.greeting_label)
        self.greeting_sub = BodyLabel("")
        self.greeting_sub.setStyleSheet("color: #888888; font-size: 14px; background: transparent;")
        text_col.addWidget(self.greeting_sub)
        main_layout.addLayout(text_col, 1)
        accent = self._get_accent()
        from PyQt6.QtCore import QSize
        self.discord_btn = TransparentToolButton()
        self.discord_btn.setIconSize(QSize(25, 25))
        self.discord_btn.hide()
        self.discord_btn.clicked.connect(self._go_to_services)
        self.discord_btn.setToolTip("Discord RPC Activo")
        self.lastfm_btn = TransparentToolButton()
        self.lastfm_btn.setIconSize(QSize(25, 25))
        self.lastfm_btn.hide()
        self.lastfm_btn.clicked.connect(self._go_to_services)
        self.lastfm_btn.setToolTip("Last.fm Scrobbling Activo")
        main_layout.addWidget(self.discord_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        main_layout.addWidget(self.lastfm_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        self.profile_btn = UserProfileButton(accent=accent, parent=self)
        self.profile_btn.profile_updated.connect(self._update_greeting)
        main_layout.addWidget(self.profile_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        self._update_service_indicators()
    def _go_to_services(self):
        mw = self.window()
        mw._target_settings_tab = 'services'
        if hasattr(mw, 'page_settings') and hasattr(mw.page_settings, 'pivot'):
            if getattr(mw.page_settings, 'current_load_index', 0) >= len(getattr(mw.page_settings, 'tabs_to_load', [])):
                mw.page_settings.pivot.setCurrentItem('services')
                if hasattr(mw.page_settings, 'tab_services'):
                    mw.page_settings.stacked_widget.setCurrentWidget(mw.page_settings.tab_services)
        mw.navigation_controller.switch_page(5)
    def _get_svg_icon(self, icon_name, color):
        from PyQt6.QtGui import QIcon, QPainter, QColor
        from config import APP_ROOT
        path = os.path.join(APP_ROOT, 'resources', 'buttons', 'services', f'{icon_name}.svg')
        if os.path.exists(path):
            pix = QIcon(path).pixmap(25, 25)
            p = QPainter(pix)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(pix.rect(), QColor(color))
            p.end()
            return QIcon(pix)
        return QIcon()
    def _update_service_indicators(self):
        from settings_manager import settings
        from services.lastfm_service import LastfmService
        accent = self._get_accent()
        if getattr(self, '_cached_accent', None) != accent:
            self._cached_lastfm_icon = self._get_svg_icon('lastfm', accent)
            self._cached_discord_icon = self._get_svg_icon('discord', accent)
            self._cached_accent = accent
        if LastfmService.is_connected():
            self.lastfm_btn.setIcon(self._cached_lastfm_icon)
            self.lastfm_btn.show()
        else:
            self.lastfm_btn.hide()
        if settings.get('rpc', False):
            self.discord_btn.setIcon(self._cached_discord_icon)
            self.discord_btn.show()
        else:
            self.discord_btn.hide()
    def refresh_theme(self):
        self._update_greeting()
        self._update_service_indicators()
        if hasattr(self, 'profile_btn') and hasattr(self.profile_btn, 'refresh'):
            self.profile_btn.refresh()
    def _update_greeting(self):
        from settings_manager import settings
        from UI.user_profile_widget import PROFILE_NAME_KEY
        from core.dashboard.greeting_manager import GreetingManager
        name = settings.get(PROFILE_NAME_KEY, "Usuario")
        accent = self._get_accent()
        title, sub, is_special_day = GreetingManager.get_greeting(name, accent)
        self.greeting_label.setTextFormat(Qt.TextFormat.RichText)
        self.greeting_sub.setTextFormat(Qt.TextFormat.RichText)
        self.greeting_label.setText(title)
        if is_special_day:
            self.greeting_sub.setText(sub)
            self._is_special_day_active = True
        else:
            self._is_special_day_active = False
            if not getattr(self, '_has_dynamic_subtitle', False):
                self.greeting_sub.setText(sub)
    def update_data(self, data):
        from core.dashboard.greeting_manager import GreetingManager
        if getattr(self, '_is_special_day_active', False):
            return
        accent = self._get_accent()
        chosen_sub = GreetingManager.get_dynamic_subtitle(data, accent)
        self.greeting_sub.setTextFormat(Qt.TextFormat.RichText)
        self.greeting_sub.setText(chosen_sub)
        self._has_dynamic_subtitle = True