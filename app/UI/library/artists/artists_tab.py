from PyQt6.QtWidgets import QWidget, QVBoxLayout
from UI.library.artists.artists_grid import ArtistsGridTab
class ArtistsTab(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self._build_ui()
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.grid_tab = ArtistsGridTab(self.player, parent=self)
        self.player.list_artists = self.grid_tab
        layout.addWidget(self.grid_tab)