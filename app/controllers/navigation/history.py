import os
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PyQt6.QtWidgets import QListWidgetItem
from qfluentwidgets import RoundMenu, Action, FluentIcon as FIF
from settings_manager import settings
from utils import sanitize_text, get_artists_from_string
from workers import ArtistInfoFetcherThread
from core.language_manager import tr
class HistoryManagerMixin:
    def _push_nav_state(self, state, target_category=None):
        if not hasattr(self, '_nav_history_map'):
            self._nav_history_map = {}
        current_page = target_category if target_category is not None else (self.mw.stacked_widget.currentIndex() if hasattr(self.mw, 'stacked_widget') else 0)
        if current_page not in self._nav_history_map:
            self._nav_history_map[current_page] = []
        self._nav_history_map[current_page].append(state)
    def _get_current_state(self):
        state = {
            'page_index': self.mw.stacked_widget.currentIndex() if hasattr(self.mw, 'stacked_widget') else 0,
        }
        if hasattr(self.mw, 'stacked_lib'):
            state['lib_tab_index'] = self.mw.stacked_lib.currentIndex()
            state['lib_tab_name'] = getattr(self.mw, 'current_lib_tab', 'songs')
            if self.mw.stacked_lib.currentWidget() == getattr(self.mw, 'artist_detail_widget', None):
                state['viewing_artist'] = getattr(self.mw, 'current_viewing_artist', None)
        if hasattr(self.mw, 'page_playlists') and hasattr(self.mw.page_playlists, 'main_stack'):
            state['playlist_stack_index'] = self.mw.page_playlists.main_stack.currentIndex()
        return state
    def _restore_nav_state(self, state):
        self._restoring = True
        try:
            self._do_restore(state)
        finally:
            self._restoring = False
    def _do_restore(self, state):
        page_index = state.get('page_index', 0)
        if page_index == 1:
            lib_tab_name = state.get('lib_tab_name', 'songs')
            lib_tab_index = state.get('lib_tab_index', 0)
            is_detail_view = False
            if hasattr(self.mw, 'album_detail_widget') and hasattr(self.mw, 'stacked_lib'):
                idx = self.mw.stacked_lib.indexOf(self.mw.album_detail_widget)
                if idx != -1 and lib_tab_index == idx:
                    is_detail_view = True
            if hasattr(self.mw, 'artist_detail_widget') and hasattr(self.mw, 'stacked_lib'):
                idx = self.mw.stacked_lib.indexOf(self.mw.artist_detail_widget)
                if idx != -1 and lib_tab_index == idx:
                    is_detail_view = True
            if is_detail_view:
                if hasattr(self.mw, 'stacked_lib'):
                    self.mw.stacked_lib.setCurrentIndex(lib_tab_index)
            else:
                self.switch_library_tab(lib_tab_name, lib_tab_index)
            if hasattr(self.mw, 'page_library') and hasattr(self.mw.page_library, 'header_widget'):
                if is_detail_view:
                    self.mw.page_library.header_widget.hide()
                else:
                    self.mw.page_library.header_widget.show()
            if state.get('viewing_artist') and is_detail_view:
                self.open_artist_detail(artist_name_str=state['viewing_artist'])
        elif page_index == 3:
            playlist_idx = state.get('playlist_stack_index', 0)
            if hasattr(self.mw, 'page_playlists') and hasattr(self.mw.page_playlists, 'main_stack'):
                if playlist_idx == 0:
                    if hasattr(self.mw.page_playlists, '_back_to_grid'):
                        self.mw.page_playlists._back_to_grid()
                    else:
                        self.mw.page_playlists.main_stack.setCurrentIndex(0)
    def update_return_button(self, *args):
        if not hasattr(self, '_nav_history_map'):
            self._nav_history_map = {}
        current_page = self.mw.stacked_widget.currentIndex() if hasattr(self.mw, 'stacked_widget') else 0
        history_stack = self._nav_history_map.get(current_page, [])
        can_go_back = len(history_stack) > 0
        if current_page == 3 and hasattr(self.mw, 'page_playlists') and hasattr(self.mw.page_playlists, 'main_stack'):
             if self.mw.page_playlists.main_stack.currentIndex() != 0:
                 can_go_back = True
        if current_page == 1 and hasattr(self.mw, 'stacked_lib'):
             cw = self.mw.stacked_lib.currentWidget()
             if cw == getattr(self.mw, 'album_detail_widget', None) or cw == getattr(self.mw, 'artist_detail_widget', None):
                 can_go_back = True
        if hasattr(self.mw, 'nav_interface'):
            self.mw.nav_interface.setReturnButtonVisible(True)
            if hasattr(self.mw.nav_interface, 'returnBtn'):
                btn = self.mw.nav_interface.returnBtn
                btn.setEnabled(can_go_back)
                btn.setToolTip(tr("Volver atrás" if can_go_back else ""))
            if hasattr(self.mw.nav_interface, 'panel') and hasattr(self.mw.nav_interface.panel, 'returnButton'):
                btn = self.mw.nav_interface.panel.returnButton
                btn.setEnabled(can_go_back)
                btn.setToolTip(tr("Volver atrás" if can_go_back else ""))
    def go_back(self):
        if not hasattr(self, '_nav_history_map'):
            self._nav_history_map = {}
        if not hasattr(self.mw, 'stacked_widget'):
            return
        current_page = self.mw.stacked_widget.currentIndex()
        if current_page == 3 and hasattr(self.mw, 'page_playlists') and hasattr(self.mw.page_playlists, 'main_stack'):
            if self.mw.page_playlists.main_stack.currentIndex() != 0:
                if hasattr(self.mw.page_playlists, '_back_to_grid'):
                    self.mw.page_playlists._back_to_grid()
                else:
                    self.mw.page_playlists.main_stack.setCurrentIndex(0)
                if self._nav_history_map.get(3, []):
                    self._nav_history_map[3].pop()
                self.update_return_button()
                return
        history_stack = self._nav_history_map.get(current_page, [])
        if not history_stack:
            if current_page == 1 and hasattr(self.mw, 'stacked_lib'):
                cw = self.mw.stacked_lib.currentWidget()
                if cw == getattr(self.mw, 'album_detail_widget', None):
                    self.switch_library_tab('albums', 1)
                    self.update_return_button()
                    return
                elif cw == getattr(self.mw, 'artist_detail_widget', None):
                    self.switch_library_tab('artists', 2)
                    self.update_return_button()
                    return
            return
        state = history_stack.pop()
        self._restore_nav_state(state)
        self.update_return_button()