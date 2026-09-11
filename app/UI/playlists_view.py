from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt
from UI.components.playlist_grid_page import PlaylistGridPage
from UI.components.playlist_detail_page import PlaylistDetailPage
class PlaylistsView(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.setObjectName("PageContent")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.main_stack = QStackedWidget(self)
        layout.addWidget(self.main_stack)
        self.grid_page = PlaylistGridPage(self.player, self)
        self.detail_page = PlaylistDetailPage(self.player, self)
        self.main_stack.addWidget(self.grid_page)             
        self.main_stack.addWidget(self.detail_page)           
        self.grid_page.open_playlist.connect(self._open_playlist)
        self.detail_page.go_back.connect(self._back_to_grid)
    @property
    def current_playlist_name(self):
        return self.detail_page.current_playlist_name
    @property
    def grid_search(self):
        return self.grid_page.grid_search
    def refresh_theme(self):
        if hasattr(self, 'grid_page') and hasattr(self.grid_page, 'grid_view'):
            self.grid_page.grid_view.viewport().update()
        if hasattr(self, 'detail_page') and hasattr(self.detail_page, 'btn_play_all'):
            self.detail_page.btn_play_all.update()
    def load_playlists(self, playlists_dict):
        self.grid_page.load_playlists(playlists_dict)
        if self.current_playlist_name and self.current_playlist_name in playlists_dict:
            self.load_playlist_details(self.current_playlist_name, playlists_dict[self.current_playlist_name])
        elif self.current_playlist_name and self.current_playlist_name not in playlists_dict:
            self._back_to_grid()
    def load_playlist_details(self, name, filepaths):
        self.detail_page.load_details(name, filepaths)
        self.main_stack.setCurrentWidget(self.detail_page)
    def _open_playlist(self, name, filepaths):
        if hasattr(self.player, 'navigation_controller'):
            nc = self.player.navigation_controller
            if not getattr(nc, '_restoring', False):
                nc._push_nav_state(nc._get_current_state())
                nc.update_return_button()
        self.load_playlist_details(name, filepaths)
    def _back_to_grid(self):
        self.main_stack.setCurrentWidget(self.grid_page)
        self.detail_page.clear()