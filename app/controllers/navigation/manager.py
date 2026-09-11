import os
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PyQt6.QtWidgets import QListWidgetItem
from qfluentwidgets import RoundMenu, Action, FluentIcon as FIF
from settings_manager import settings
from utils import sanitize_text, get_artists_from_string
from workers import ArtistInfoFetcherThread
from core.language_manager import tr
from .history import HistoryManagerMixin
from .lazy_loading import LazyLoadingMixin
from .router import PageRouterMixin
from .detail_router import DetailRouterMixin
class NavigationController(
    HistoryManagerMixin,
    LazyLoadingMixin,
    PageRouterMixin,
    DetailRouterMixin
):
    def __init__(self, main_window):
        self.mw = main_window
        self._nav_history_map = {}                                                                           
        self._tab_ready_callbacks = {'albums': [], 'artists': []}
        self._page_ready_callbacks = {}
    def setup_connections(self):
        if hasattr(self.mw, 'nav_interface'):
            if hasattr(self.mw.nav_interface, 'returnBtn'):
                try: self.mw.nav_interface.returnBtn.clicked.connect(self.go_back)
                except Exception: pass
            if hasattr(self.mw.nav_interface, 'panel') and hasattr(self.mw.nav_interface.panel, 'returnButton'):
                try: self.mw.nav_interface.panel.returnButton.clicked.connect(self.go_back)
                except Exception: pass
        if hasattr(self.mw, 'stacked_widget'):
            self.mw.stacked_widget.currentChanged.connect(self.update_return_button)
        if hasattr(self.mw, 'page_playlists') and hasattr(self.mw.page_playlists, 'main_stack'):
            self.mw.page_playlists.main_stack.currentChanged.connect(self.update_return_button)
        if hasattr(self.mw, 'album_stack'):
            self.mw.album_stack.currentChanged.connect(self.update_return_button)
        if hasattr(self.mw, 'artist_stack'):
            self.mw.artist_stack.currentChanged.connect(self.update_return_button)
        self.update_return_button()
    def handle_esc_key(self):
        if hasattr(self.mw, 'search_controller') and self.mw.search_controller.spotlight_dialog.isVisible():
            self.mw.search_controller.spotlight_dialog.fade_out_and_hide()
            return
        self.go_back()