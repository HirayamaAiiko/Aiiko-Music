from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QSizePolicy, QGraphicsDropShadowEffect, QLabel
from PyQt6.QtGui import QColor, QPainter, QLinearGradient
from PyQt6.QtCore import Qt
from qfluentwidgets import NavigationInterface, NavigationItemPosition, FluentIcon as FIF
from UI.library_view import LibraryView
from UI.favorites_view import FavoritesView
from UI.playlists_view import PlaylistsView
from UI.settings_view import SettingsView
from UI.now_playing_view import NowPlayingView
from UI.mini_player_view import MiniPlayerView
from UI.queue_panel import QueuePanel
from UI.dashboard import DashboardView
from config import ICON_HEART, ICON_PLAY
from settings_manager import settings
from core.language_manager import tr
class MainWindowBuilder:
    @staticmethod
    def build(player):
        player.central_widget = QWidget()
        player.central_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        player.central_widget.setObjectName("MainWindow")
        player.central_widget.setStyleSheet("QWidget#MainWindow { background-color: transparent; }")
        player.setObjectName("MainWindow")
        if player.layout():
            window_layout = player.layout()
        else:
            window_layout = QVBoxLayout(player)
            title_bar_h = player.titleBar.height() if hasattr(player, 'titleBar') else 32
            window_layout.setContentsMargins(0, title_bar_h, 0, 0)
            window_layout.setSpacing(0)
        window_layout.addWidget(player.central_widget)
        main_layout = QVBoxLayout(player.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        top_area = QWidget()
        top_layout = QHBoxLayout(top_area)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        class SolidSidebarContainer(QWidget):
            def __init__(self):
                super().__init__()
                self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            def paintEvent(self, event):
                import theme_manager
                from settings_manager import settings
                theme_name = settings.get('app_theme', 'Oscuro (Dark)')
                td = theme_manager.get_theme(theme_name)
                base_hex = td.get('mini_player_bg', '#23232D')
                base_color = QColor(base_hex)
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                gradient = QLinearGradient(0, 0, 0, self.height())
                gradient.setColorAt(0.0, base_color.lighter(115))
                gradient.setColorAt(1.0, base_color.darker(110))
                painter.fillRect(self.rect(), gradient)
                painter.end()
        player.sidebar_container = SolidSidebarContainer()
        player.sidebar_container.setObjectName("SidebarContainer")
        sidebar_layout = QVBoxLayout(player.sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        player.nav_interface = NavigationInterface(player, showMenuButton=True, showReturnButton=True)
        player.nav_interface.setReturnButtonVisible(False)
        player.nav_interface.setExpandWidth(175)                                            
        sidebar_layout.addWidget(player.nav_interface)
        top_layout.addWidget(player.sidebar_container)
        player.stacked_widget = QStackedWidget()
        player.stacked_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        player.page_dashboard = DashboardView(player)
        player.page_now_playing = NowPlayingView(player)
        startup_tab = settings.get('startup_tab', 'dashboard')
        if startup_tab in ['Inicio', 'Home']: startup_tab = 'dashboard'
        elif startup_tab in ['Biblioteca', 'Library']: startup_tab = 'library'
        elif startup_tab in ['Favoritos', 'Favorites']: startup_tab = 'favorites'
        elif startup_tab == 'Playlists': startup_tab = 'playlists'
        index_map = {'dashboard': 0, 'library': 1, 'favorites': 2, 'playlists': 3}
        startup_idx = index_map.get(startup_tab, 0)
        from UI.components.loading_placeholder import LoadingPlaceholder
        if startup_idx == 1:
            player.page_library = LibraryView(player)
        else:
            player.page_library = LoadingPlaceholder(tr("Cargando Biblioteca..."))
        if startup_idx == 2:
            player.page_favorites = FavoritesView(player)
        else:
            player.page_favorites = LoadingPlaceholder(tr("Cargando Favoritos..."))
        if startup_idx == 3:
            player.page_playlists = PlaylistsView(player)
        else:
            player.page_playlists = LoadingPlaceholder(tr("Cargando Playlists..."))
        player.page_settings = LoadingPlaceholder(tr("Cargando Ajustes..."), use_glitch=False)
        player.stacked_widget.addWidget(player.page_dashboard)
        player.stacked_widget.addWidget(player.page_library)
        player.stacked_widget.addWidget(player.page_favorites)
        player.stacked_widget.addWidget(player.page_playlists)
        player.stacked_widget.addWidget(player.page_now_playing)
        player.stacked_widget.addWidget(player.page_settings)
        player.nav_interface.addItem('dashboard', FIF.HOME, tr('Inicio'), onClick=lambda: player.navigation_controller.switch_page(0, force_reset=True))
        player.nav_interface.addItem('library', player.playback_ui_controller._get_icon('library.svg', FIF.MUSIC), tr('Biblioteca'), onClick=lambda: player.navigation_controller.switch_page(1, force_reset=True))
        player.nav_interface.addItem('favorites', player.playback_ui_controller._get_icon('favorites_nav.svg', ICON_HEART), tr('Favoritos'), onClick=lambda: player.navigation_controller.switch_page(2, force_reset=True))
        player.nav_interface.addItem('playlists', player.playback_ui_controller._get_icon('playlists.svg', FIF.MUSIC_FOLDER), tr('Playlists'), onClick=lambda: player.navigation_controller.switch_page(3, force_reset=True))
        player.nav_interface.addItem('now_playing', player.playback_ui_controller._get_icon('playing.svg', ICON_PLAY), tr('Reproduciendo'), onClick=lambda: player.navigation_controller.switch_page(4, force_reset=True))
        player.nav_interface.addItem('settings', player.playback_ui_controller._get_icon('settings.svg', FIF.SETTING), tr('Ajustes'), position=NavigationItemPosition.BOTTOM, onClick=lambda: player.navigation_controller.switch_page(5, force_reset=True))
        startup_tab = settings.get('startup_tab', 'dashboard')
        if startup_tab in ['Inicio', 'Home']: startup_tab = 'dashboard'
        elif startup_tab in ['Biblioteca', 'Library']: startup_tab = 'library'
        elif startup_tab in ['Favoritos', 'Favorites']: startup_tab = 'favorites'
        elif startup_tab == 'Playlists': startup_tab = 'playlists'
        index_map = {'dashboard': 0, 'library': 1, 'favorites': 2, 'playlists': 3}
        player.nav_interface.setCurrentItem(startup_tab)
        player.stacked_widget.setCurrentIndex(index_map.get(startup_tab, 0))
        if hasattr(player.nav_interface, 'widget'):
            if player.nav_interface.widget('dashboard'): player.nav_interface.widget('dashboard').setToolTip(tr('Inicio'))
            if player.nav_interface.widget('library'): player.nav_interface.widget('library').setToolTip(tr('Biblioteca'))
            if player.nav_interface.widget('favorites'): player.nav_interface.widget('favorites').setToolTip(tr('Favoritos'))
            if player.nav_interface.widget('playlists'): player.nav_interface.widget('playlists').setToolTip(tr('Playlists'))
            if player.nav_interface.widget('now_playing'): player.nav_interface.widget('now_playing').setToolTip(tr('Reproduciendo'))
            if player.nav_interface.widget('settings'): player.nav_interface.widget('settings').setToolTip(tr('Ajustes'))
        top_layout.addWidget(player.stacked_widget, 1)
        player.mini_player = MiniPlayerView(player)
        from PyQt6.QtCore import QAbstractAnimation
        if hasattr(player.nav_interface, 'panel') and hasattr(player.nav_interface.panel, 'expandAnimation'):
            def on_nav_anim_state(state):
                is_stopped = (state == QAbstractAnimation.State.Stopped)
                if hasattr(player, 'page_dashboard') and hasattr(player.page_dashboard, '_left_scroll'):
                    player.page_dashboard._left_scroll.setWidgetResizable(is_stopped)
            player.nav_interface.panel.expandAnimation.stateChanged.connect(on_nav_anim_state)
        main_layout.addWidget(top_area, 1)
        main_layout.addWidget(player.mini_player, 0)
        player.queue_panel = QueuePanel(player, player.central_widget)
        player.queue_panel.setFixedWidth(375)
