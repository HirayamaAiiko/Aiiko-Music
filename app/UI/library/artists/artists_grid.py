from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QListView, QAbstractItemView
from delegates.grid_delegates import CircularHoverDelegate
from widgets import ResponsiveGridHelper
class ArtistsGridTab(QListView):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self._build_ui()
    def _build_ui(self):
        self.setObjectName("ArtistGridList")
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setUniformItemSizes(True)
        self.setIconSize(QSize(160, 160))
        self.setGridSize(QSize(190, 265))
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.verticalScrollBar().setSingleStep(15)
        self.setViewportMargins(0, 15, 0, 0)
        self.setStyleSheet("QListView::item { background-color: transparent; }")
        self.player.artist_delegate = CircularHoverDelegate(self)
        self.setItemDelegate(self.player.artist_delegate)
        self.setModel(self.player.artist_proxy)
        self.doubleClicked.connect(self.player.navigation_controller.open_artist_detail)
        self.player.artist_grid_helper = ResponsiveGridHelper(self, parent=self.player)
        if hasattr(self.player, 'apply_smooth_scroll'):
            self.player.apply_smooth_scroll(self, step=250)
        self.set_view_mode(self.player.artists_is_grid)
        if hasattr(self.player, 'image_cache'):
            self.player.image_cache.cache_updated.connect(self.viewport().update)
    def set_view_mode(self, is_grid: bool):
        from PyQt6.QtCore import QSize
        from PyQt6.QtWidgets import QListView
        if is_grid:
            self.setViewMode(QListView.ViewMode.IconMode)
            self.setResizeMode(QListView.ResizeMode.Adjust)
            self.setItemDelegate(self.player.artist_delegate)
            if hasattr(self.player, 'artist_grid_helper'):
                self.player.artist_grid_helper.set_active(True)
                self.player.artist_grid_helper.set_list_mode(False)
        else:
            self.setViewMode(QListView.ViewMode.IconMode)
            self.setResizeMode(QListView.ResizeMode.Adjust)
            if not hasattr(self.player, 'artist_list_delegate'):
                from delegates.list_delegates import ArtistListDelegate
                self.player.artist_list_delegate = ArtistListDelegate(self)
            self.setItemDelegate(self.player.artist_list_delegate)
            if hasattr(self.player, 'artist_grid_helper'):
                self.player.artist_grid_helper.set_active(True)
                self.player.artist_grid_helper.set_list_mode(True, columns=3, height=70)