from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QListView, QAbstractItemView
from delegates.grid_delegates import AlbumGridDelegate
from widgets import ResponsiveGridHelper
class AlbumsGridTab(QListView):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self._build_ui()
    def _build_ui(self):
        self.setObjectName("GridList")
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setUniformItemSizes(True)
        self.setIconSize(QSize(160, 160))
        self.setGridSize(QSize(190, 265))
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.verticalScrollBar().setSingleStep(15)
        self.setViewportMargins(0, 15, 0, 0)
        self.setStyleSheet("QListView::item { background-color: transparent; border: none; }")
        from PyQt6.QtCore import Qt
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.doubleClicked.connect(self.player.navigation_controller.open_album_detail)
        self.player.album_delegate = AlbumGridDelegate(self)
        self.setItemDelegate(self.player.album_delegate)
        self.setModel(self.player.album_proxy)
        self.player.album_grid_helper = ResponsiveGridHelper(self, parent=self.player)
        if hasattr(self.player, 'apply_smooth_scroll'):
            self.player.apply_smooth_scroll(self, step=250)
        self.set_view_mode(self.player.albums_is_grid)
    def set_view_mode(self, is_grid: bool):
        from PyQt6.QtCore import QSize
        from PyQt6.QtWidgets import QListView
        if is_grid:
            self.setUniformItemSizes(False)
            self.setViewMode(QListView.ViewMode.IconMode)
            self.setGridSize(QSize(190, 265))
            self.setResizeMode(QListView.ResizeMode.Adjust)
            self.setUniformItemSizes(True)
            self.setItemDelegate(self.player.album_delegate)
            self.setViewportMargins(0, 15, 0, 0)
            if hasattr(self.player, 'album_grid_helper'):
                self.player.album_grid_helper.set_active(True)
                self.player.album_grid_helper.set_list_mode(False)
        else:
            self.setUniformItemSizes(False)
            self.setViewMode(QListView.ViewMode.IconMode)
            self.setResizeMode(QListView.ResizeMode.Adjust)
            self.setUniformItemSizes(True)
            if not hasattr(self.player, 'album_list_delegate'):
                from delegates.list_delegates import AlbumListDelegate
                self.player.album_list_delegate = AlbumListDelegate(self)
            self.setItemDelegate(self.player.album_list_delegate)
            if hasattr(self.player, 'album_grid_helper'):
                self.player.album_grid_helper.set_active(True)
                self.player.album_grid_helper.set_list_mode(True, columns=1, height=50)
            self.setViewportMargins(0, 5, 0, 0)
    def _show_context_menu(self, pos):
        from PyQt6.QtCore import Qt
        index = self.indexAt(pos)
        if not index.isValid():
            return
        album_name = index.data(Qt.ItemDataRole.UserRole)
        representative_track = index.data(Qt.ItemDataRole.UserRole + 1)
        if not album_name or not representative_track:
            return
        global_pos = self.viewport().mapToGlobal(pos)
        if hasattr(self.player, 'context_menu_manager'):
            self.player.context_menu_manager.show_album_context_menu_at(album_name, representative_track, global_pos)