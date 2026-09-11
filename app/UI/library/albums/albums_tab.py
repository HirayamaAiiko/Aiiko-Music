from PyQt6.QtWidgets import QWidget, QVBoxLayout
from UI.library.albums.albums_grid import AlbumsGridTab
from UI.components.song_table_header import SongTableHeader
class AlbumsTab(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self._build_ui()
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.table_header = SongTableHeader(self, solid_bg=False, is_album_list=True)
        self.table_header.has_covers = True
        self.table_header.setVisible(not self.player.albums_is_grid)
        layout.addWidget(self.table_header)
        self.grid_tab = AlbumsGridTab(self.player, parent=self)
        self.table_header.list_view = self.grid_tab
        self.player.list_albums = self.grid_tab
        layout.addWidget(self.grid_tab)
        from UI.components.scroll_to_top import ScrollToTopButton
        self.btn_scroll_top = ScrollToTopButton(self.grid_tab, self)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'btn_scroll_top'):
            self.btn_scroll_top.update_position(self.width(), self.height())