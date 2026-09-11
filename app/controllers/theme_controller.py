from PyQt6.QtGui import QColor, QPainter, QRadialGradient, QPixmap
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QEvent
from qfluentwidgets import setTheme, Theme, setThemeColor, FluentIcon as FIF
from settings_manager import settings
from config import get_custom_styles
import theme_manager
class GradientOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setStyleSheet("background: transparent;")
        self._gradient_config = None
        self._accent_color = None
        self._base_bg = None
        self._cached_pixmap = None
        self._cached_size = None
        self.lower()
        if parent:
            parent.installEventFilter(self)
    def eventFilter(self, obj, event):
        if obj == self.parent() and event.type() == QEvent.Type.Resize:
            self.setGeometry(obj.rect())
        return False
    def set_config(self, config, accent_color, base_bg):
        self._gradient_config = config
        self._accent_color = accent_color
        self._base_bg = base_bg
        self._cached_pixmap = None                                      
        self.update()
    def paintEvent(self, event):
        if self._cached_pixmap is None or self.size() != self._cached_size:
            self._cached_size = self.size()
            self._cached_pixmap = QPixmap(self.size())
            self._cached_pixmap.fill(Qt.GlobalColor.transparent)
            p = QPainter(self._cached_pixmap)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            if self._base_bg:
                p.fillRect(self.rect(), QColor(self._base_bg))
            if self._gradient_config and self._gradient_config.get('enabled'):
                cfg = self._gradient_config
                raw_color = cfg.get('color', 'accent')
                if raw_color == 'accent' and self._accent_color:
                    color = QColor(self._accent_color)
                else:
                    color = QColor(raw_color)
                opacity = cfg.get('opacity', 0.15)
                radius = cfg.get('radius', 800)
                cx = self.width() * cfg.get('x', 0.95)
                cy = self.height() * cfg.get('y', 0.0)
                gradient = QRadialGradient(cx, cy, radius)
                color.setAlphaF(opacity)
                gradient.setColorAt(0.0, color)
                color_transparent = QColor(color)
                color_transparent.setAlphaF(0.0)
                gradient.setColorAt(1.0, color_transparent)
                p.setBrush(gradient)
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRect(self.rect())
            p.end()
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._cached_pixmap)
        painter.end()
class ThemeController:
    def __init__(self, main_window):
        self.mw = main_window
    def apply_theme(self, full_refresh=True):
        app_accent_name = settings.get('app_accent_name', 'Teal (AIIKO)')
        app_accent_hex = theme_manager.get_accent_hex(app_accent_name)
        self.mw.ACCENT_COLORS = {name: theme_manager.get_accent_hex(name)
                                  for name in theme_manager.get_accent_names()}
        if full_refresh:
            from qfluentwidgets import qconfig
            from qfluentwidgets.common.style_sheet import updateStyleSheet
            if qconfig.theme != Theme.DARK:
                setTheme(Theme.DARK)
            current_color_obj = qconfig.get(qconfig.themeColor)
            current_color = current_color_obj.name().upper() if hasattr(current_color_obj, 'name') else ""
            if current_color != app_accent_hex.upper():
                setThemeColor(app_accent_hex)
            else:
                updateStyleSheet(self.mw)
        base_css = get_custom_styles(app_accent_hex)
        base_css += "\nQWidget#QueuePanel { border-top-left-radius: 0px; }"
        app_theme_name = settings.get('app_theme', 'Oscuro (Dark)')
        td = theme_manager.get_theme(app_theme_name)
        theme_css = ""
        if td.get('main_bg'):
            theme_css += f"MusicPlayer {{ background-color: {td['main_bg']}; border: none; }}\n"
        if td.get('mini_player_bg'):
            border = td.get('mini_player_border', '#383838')
            theme_css += f"QWidget#MiniPlayer {{ background-color: {td['mini_player_bg']}; border-top: 1px solid {border}; border-bottom: none; border-left: none; border-right: none; }}\n"
        if td.get('now_playing_bg'):
            theme_css += f"QWidget#NowPlayingPage {{ background-color: {td['now_playing_bg']}; }}\n"
        gradient_cfg = td.get('gradient')
        user_wants_gradient = settings.get('gradient_enabled', True)
        if gradient_cfg and gradient_cfg.get('enabled') and user_wants_gradient:
            if td.get('page_content_bg'):
                theme_css += f"QWidget#PageContent {{ background-color: transparent; }}\n"
            theme_css += "MSFluentTitleBar { background-color: transparent; }\n"
        else:
            if td.get('page_content_bg'):
                theme_css += f"QWidget#PageContent {{ background-color: {td['page_content_bg']}; }}\n"
        if td.get('queue_bg'):
            theme_css += f"QWidget#QueueContent {{ background-color: {td['queue_bg']} !important; border: none !important; }}\n"
        if td.get('mini_player_bg'):
            theme_css += f"QWidget#SidebarContainer {{ background-color: {td['mini_player_bg']}; }}\n"
            theme_css += f"NavigationInterface, NavigationPanel {{ background-color: {td['mini_player_bg']} !important; border: none !important; }}\n"
        base_css += theme_css
        if settings.get('square_covers', False):
            base_css += """
            QLabel#MiniPlayerCover { border-radius: 0px !important; }
            QLabel#FullScreenCover { border-radius: 0px !important; }
            QLabel#PlaylistDetailCover { border-radius: 0px !important; }
            QWidget#PlaylistCover { border-radius: 0px !important; }
            QWidget#NowPlayingCover { border-radius: 0px !important; }
            """
        else:
            base_css += """
            QLabel#PlaylistDetailCover { border-radius: 12px !important; }
            """
        self.mw.search_controller.apply_spotlight_theme(td.get('spotlight_bg'), td.get('spotlight_border'))
        base_css += """
        QListView::item { 
            background-color: transparent !important; 
            border: none !important;
        }
        """
        if self.mw.styleSheet() != base_css:
            self.mw.setStyleSheet(base_css)
        self._apply_gradient(td, app_accent_hex)
        if hasattr(self.mw, 'sidebar_artist'):
            self.mw.sidebar_artist.setStyleSheet(f"color: {app_accent_hex}; font-size: 16px;")
        if hasattr(self.mw, 'sidebar_artist_stats'):
            self.mw.sidebar_artist_stats.setStyleSheet(f"color: {app_accent_hex}; font-size: 14px;")
        if hasattr(self.mw, 'btn_mini_shuffle'):
            self.mw.playback_ui_controller._update_shuffle_icon()
        if hasattr(self.mw, 'btn_mini_repeat'):
            self.mw.playback_ui_controller._update_repeat_icon()
        if hasattr(self.mw, 'btn_mini_eq'):
            self.mw.playback_ui_controller._update_eq_icons()
        if hasattr(self.mw, 'btn_mini_queue'):
            self.mw.playback_ui_controller._update_queue_icon()
        if hasattr(self.mw, 'btn_fullscreen'):
            self.mw.playback_ui_controller._update_fullscreen_icon()
        if hasattr(self.mw, 'btn_favorite_np'):
            self.mw.playback_ui_controller.update_favorite_icon_ui()
        if hasattr(self.mw, 'full_artist'):
            self.mw.playback_ui_controller.refresh_full_artist_html()
        if hasattr(self.mw, 'btn_mini_play'):
            from UI.mini_player_view import MiniPlayerView
            MiniPlayerView._apply_play_btn_accent(self.mw)
        if full_refresh:
            if hasattr(self.mw, 'page_playlists') and hasattr(self.mw.page_playlists, 'refresh_theme'):
                self.mw.page_playlists.refresh_theme()
            if hasattr(self.mw, 'page_dashboard') and hasattr(self.mw.page_dashboard, 'refresh_theme'):
                self.mw.page_dashboard.refresh_theme()
            if hasattr(self.mw, 'page_settings') and hasattr(self.mw.page_settings, 'refresh_theme'):
                self.mw.page_settings.refresh_theme()
        if hasattr(self.mw, 'btn_translate_lyrics') and hasattr(self.mw, 'lyrics_manager'):
            mode = getattr(self.mw.lyrics_manager, 'display_mode', 'original')
            if mode == 'dual':
                self.mw.playback_ui_controller.update_tool_btn_state(self.mw.btn_translate_lyrics, "translate_lyrics.svg", FIF.LANGUAGE, app_accent_hex)
            elif mode == 'translated':
                self.mw.playback_ui_controller.update_tool_btn_state(self.mw.btn_translate_lyrics, "translate_lyrics.svg", FIF.LANGUAGE, '#FFB900')
            else:
                self.mw.playback_ui_controller.update_tool_btn_state(self.mw.btn_translate_lyrics, "translate_lyrics.svg", FIF.LANGUAGE, '#FFFFFF')
        if hasattr(self.mw, 'btn_lyrics_toggle'):
            if not getattr(self.mw, 'show_lyrics', True):
                self.mw.playback_ui_controller.update_tool_btn_state(self.mw.btn_lyrics_toggle, "hide_lyrics.svg", FIF.ALIGNMENT, '#FFFFFF')
            else:
                self.mw.playback_ui_controller.update_tool_btn_state(self.mw.btn_lyrics_toggle, "hide_lyrics.svg", FIF.ALIGNMENT, app_accent_hex)
        if hasattr(self.mw, 'btn_timer'):
            from config import ICON_TIMER
            is_timer_active = hasattr(self.mw, 'sleep_timer_controller') and self.mw.sleep_timer_controller.is_active()
            if is_timer_active:
                self.mw.playback_ui_controller.update_tool_btn_state(self.mw.btn_timer, "timer.svg", ICON_TIMER, app_accent_hex)
            else:
                self.mw.playback_ui_controller.update_tool_btn_state(self.mw.btn_timer, "timer.svg", ICON_TIMER, '#FFFFFF')
        if hasattr(self.mw, 'lbl_hq'):
            c = QColor(app_accent_hex)
            if hasattr(self.mw.lbl_hq, 'set_bg_color'):
                self.mw.lbl_hq.set_bg_color(QColor(c.red(), c.green(), c.blue(), 51))
            self.mw.lbl_hq.setStyleSheet(f"""
                QLabel {{
                    background: transparent;
                    padding: 4px 8px;
                    font-size: 11px;
                    color: {app_accent_hex};
                    font-weight: bold;
                }}
            """)
        if getattr(self.mw, 'system_manager', None) and getattr(self.mw.system_manager, 'floating_player', None):
            self.mw.system_manager.floating_player.set_accent_color(app_accent_hex)
        if hasattr(self.mw, 'queue_controller') and hasattr(self.mw.queue_controller, 'update_queue_theme'):
            self.mw.queue_controller.update_queue_theme()
        if hasattr(self.mw, 'lyrics_manager') and getattr(self.mw, 'lyrics_manager', None) is not None:
            if self.mw.lyrics_manager.track:
                self.mw.lyrics_manager.sync(self.mw.audio_engine.get_position(), self.mw.lyrics_manager.track)
    def change_theme(self, text):
        settings.set('app_theme', text)
        settings.save()
        self.apply_theme()
    def change_accent(self, text):
        settings.set('app_accent_name', text)
        settings.save()
        self.apply_theme()
    def change_gradient_state(self, state):
        settings.set('gradient_enabled', state)
        settings.save()
        self.apply_theme(full_refresh=False)
    def _apply_gradient(self, theme_data, app_accent_hex):
        gradient_cfg = theme_data.get('gradient')
        user_wants_gradient = settings.get('gradient_enabled', True)
        base_bg = theme_data.get('page_content_bg')
        if not gradient_cfg or not gradient_cfg.get('enabled') or not user_wants_gradient:
            if hasattr(self.mw, '_gradient_overlay'):
                self.mw._gradient_overlay.hide()
            return
        if not hasattr(self.mw, '_gradient_overlay'):
            self.mw._gradient_overlay = GradientOverlay(self.mw)
        overlay = self.mw._gradient_overlay
        overlay.set_config(gradient_cfg, app_accent_hex, base_bg)
        overlay.setGeometry(self.mw.rect())
        overlay.show()
        overlay.lower()                                            