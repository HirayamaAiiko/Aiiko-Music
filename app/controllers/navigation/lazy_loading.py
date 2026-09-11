import os
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PyQt6.QtWidgets import QListWidgetItem
from qfluentwidgets import RoundMenu, Action, FluentIcon as FIF
from settings_manager import settings
from utils import sanitize_text, get_artists_from_string
from workers import ArtistInfoFetcherThread
from core.language_manager import tr
class LazyLoadingMixin:
    def _execute_when_page_ready(self, page_index, callback):
        widget = self.mw.stacked_widget.widget(page_index)
        if not getattr(widget, 'is_placeholder', False):
            callback()
        else:
            if page_index not in self._page_ready_callbacks:
                self._page_ready_callbacks[page_index] = []
            self._page_ready_callbacks[page_index].append(callback)
    def _notify_page_ready(self, page_index):
        callbacks = self._page_ready_callbacks.get(page_index, [])
        self._page_ready_callbacks[page_index] = []
        for cb in callbacks:
            try:
                cb()
            except Exception as e:
                import logging
                logging.error(f"Error executing page callback for {page_index}: {e}")
    def _execute_when_tab_ready(self, tab_name, callback):
        if tab_name == 'albums' and hasattr(self.mw, 'album_tracks_model'):
            callback()
        elif tab_name == 'artists' and hasattr(self.mw, 'artist_tracks_model'):
            callback()
        else:
            self._tab_ready_callbacks[tab_name].append(callback)
    def _notify_tab_ready(self, tab_name):
        callbacks = self._tab_ready_callbacks.get(tab_name, [])
        self._tab_ready_callbacks[tab_name] = []
        for cb in callbacks:
            try:
                cb()
            except Exception as e:
                import logging
                logging.error(f"Error executing callback for {tab_name}: {e}")
    def preload_view(self, index):
        try:
            old_widget = self.mw.stacked_widget.widget(index)
            if not getattr(old_widget, 'is_placeholder', False):
                return
            import logging
            logging.info(f"Pre-cargando vista silenciosamente en índice {index}...")
            new_widget = None
            if index == 1:
                from UI.library_view import LibraryView
                self.mw.page_library = LibraryView(self.mw)
                new_widget = self.mw.page_library
                if hasattr(self.mw, 'library_controller'):
                    self.mw.library_controller.refresh_library_views(skip_dashboard=True)
            elif index == 2:
                from UI.favorites_view import FavoritesView
                self.mw.page_favorites = FavoritesView(self.mw)
                new_widget = self.mw.page_favorites
                if hasattr(self.mw, 'library_controller'):
                    self.mw.library_controller.refresh_favorites_view()
            elif index == 3:
                from UI.playlists_view import PlaylistsView
                self.mw.page_playlists = PlaylistsView(self.mw)
                new_widget = self.mw.page_playlists
                if hasattr(self.mw, 'library_controller'):
                    self.mw.library_controller.refresh_playlists_list()
            elif index == 5:
                from UI.settings_view import SettingsView
                self.mw.page_settings = SettingsView(self.mw)
                new_widget = self.mw.page_settings
            if new_widget:
                self.mw.stacked_widget.addWidget(new_widget)
                was_visible = (self.mw.stacked_widget.currentWidget() == old_widget)
                if was_visible:
                    self.mw.stacked_widget.setCurrentWidget(new_widget)
                self.mw.stacked_widget.removeWidget(old_widget)
                old_widget.deleteLater()
                self.mw.stacked_widget.removeWidget(new_widget)
                self.mw.stacked_widget.insertWidget(index, new_widget)
                if was_visible:
                    self.mw.stacked_widget.setCurrentWidget(new_widget)
            if new_widget and hasattr(self.mw, 'theme_controller'):
                self.mw.theme_controller.apply_theme(full_refresh=False)
            if index == 5 and hasattr(self.mw, 'page_settings') and hasattr(self.mw.page_settings, 'refresh_theme'):
                self.mw.page_settings.refresh_theme()
        except Exception as e:
            import logging
            logging.error(f"Error fatal en preload de index {index}: {e}", exc_info=True)
    def preload_library_tabs(self):
        if not hasattr(self.mw, 'stacked_lib'):
            return
        import logging
        from PyQt6.QtCore import QTimer
        def _preload_artists():
            try:
                old_artists = self.mw.stacked_lib.widget(2)
                if getattr(old_artists, 'is_placeholder', False):
                    logging.info("Precargando vista de Artistas en segundo plano...")
                    from UI.library.artists.artists_tab import ArtistsTab
                    new_artists = ArtistsTab(self.mw, parent=self.mw.stacked_lib)
                    self.mw.page_library.artists_tab = new_artists
                    self.mw.stacked_lib.removeWidget(old_artists)
                    self.mw.stacked_lib.insertWidget(2, new_artists)
                    old_artists.deleteLater()
                    if hasattr(self.mw, 'library') and hasattr(self.mw.library_controller, 'refresh_library_views'):
                        pass                                      
                if hasattr(self.mw, 'theme_controller') and getattr(old_artists, 'is_placeholder', False):
                    from qfluentwidgets.common.style_sheet import updateStyleSheet as _updateStyleSheet
                    QTimer.singleShot(0, _updateStyleSheet)
                    QTimer.singleShot(0, lambda: self.mw.theme_controller.apply_theme(full_refresh=False))
            except Exception as e:
                logging.error(f"Error pre-cargando pestaña Artistas: {e}")
        try:
            old_albums = self.mw.stacked_lib.widget(1)
            if getattr(old_albums, 'is_placeholder', False):
                logging.info("Precargando vista de Álbumes en segundo plano...")
                from UI.library.albums.albums_tab import AlbumsTab
                new_albums = AlbumsTab(self.mw, parent=self.mw.stacked_lib)
                self.mw.page_library.albums_tab = new_albums
                self.mw.stacked_lib.removeWidget(old_albums)
                self.mw.stacked_lib.insertWidget(1, new_albums)
                old_albums.deleteLater()
                if hasattr(self.mw, 'library') and hasattr(self.mw.library_controller, 'refresh_library_views'):
                    pass                                      
                if hasattr(self.mw, 'theme_controller'):
                    from qfluentwidgets.common.style_sheet import updateStyleSheet as _updateStyleSheet
                    QTimer.singleShot(0, _updateStyleSheet)
                    QTimer.singleShot(0, lambda: self.mw.theme_controller.apply_theme(full_refresh=False))
            QTimer.singleShot(100, _preload_artists)
        except Exception as e:
            logging.error(f"Error pre-cargando pestaña Álbumes: {e}")