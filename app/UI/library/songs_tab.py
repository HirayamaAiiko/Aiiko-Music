from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListView, QAbstractItemView
from delegates.list_delegates import SongListDelegate
from view_models.library_models import TrackListModel, TrackProxyModel
class SongsTab(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self._build_ui()
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.player.proxy_model = TrackProxyModel(self.player)
        self.player.proxy_model.setSourceModel(self.player.track_model)
        from UI.components.song_table_header import SongTableHeader
        self.table_header = SongTableHeader(self)
        self.table_header.has_covers = True
        layout.addWidget(self.table_header)
        from UI.components.draggable_track_list import DraggableTrackListView
        self.list_songs = DraggableTrackListView()
        self.list_songs.setObjectName("SongsList")
        self.table_header.list_view = self.list_songs
        self.list_songs.setModel(self.player.proxy_model)
        self.list_songs.setUniformItemSizes(True)
        self.list_songs.setIconSize(QSize(50, 50))
        self.list_songs.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list_songs.verticalScrollBar().setSingleStep(15)
        self.list_songs.setViewportMargins(0, 5, 0, 0)
        self.list_songs.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_songs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_songs.customContextMenuRequested.connect(self.player.context_menu_manager.show_song_context_menu_listview)
        from core.selection_tracker import SelectionTracker
        self.list_songs._selection_tracker = SelectionTracker(self.list_songs)
        self.list_songs.doubleClicked.connect(self.player.queue_controller.play_specific_track_from_listview)
        self.list_songs.setStyleSheet("""
            QListView::item { background-color: transparent; border: none; }
            QListView::item:selected { background-color: transparent; border: none; }
            QListView::item:hover { background-color: transparent; border: none; }
        """)
        self.player.song_list_delegate = SongListDelegate(self.list_songs, self.player, is_artist_view=False, is_table_view=True, show_cover_in_table=True)
        self.list_songs.setItemDelegate(self.player.song_list_delegate)
        self.player.apply_smooth_scroll(self.list_songs)
        self.player.list_songs = self.list_songs
        layout.addWidget(self.list_songs)
        from UI.components.scroll_to_top import ScrollToTopButton
        from UI.components.locate_track_button import LocateTrackButton
        self.btn_scroll_top = ScrollToTopButton(self.list_songs, self)
        self.btn_locate_track = LocateTrackButton(self.player, self.list_songs, self)
        self.btn_locate_track.set_model(self.player.proxy_model)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_floating_positions()
    def refresh_floating_buttons(self):
        if hasattr(self, 'btn_scroll_top'):
            self.btn_scroll_top.refresh_visibility()
        if hasattr(self, 'btn_locate_track'):
            self.btn_locate_track.refresh_visibility()
        self._update_floating_positions()
    def _update_floating_positions(self):
        from settings_manager import settings
        stt_enabled = settings.get('show_scroll_to_top', True)
        loc_enabled = settings.get('show_locate_track', False)
        loc_present = self.btn_locate_track._is_track_present if hasattr(self, 'btn_locate_track') else False
        show_stt = stt_enabled
        show_loc = loc_enabled and loc_present
        w, h = self.width(), self.height()
        if show_stt and show_loc:
            if hasattr(self, 'btn_scroll_top'): self.btn_scroll_top.update_position(w, h, offset_x=25)
            if hasattr(self, 'btn_locate_track'): self.btn_locate_track.update_position(w, h, offset_x=-25)
        elif show_stt:
            if hasattr(self, 'btn_scroll_top'): self.btn_scroll_top.update_position(w, h, offset_x=0)
        elif show_loc:
            if hasattr(self, 'btn_locate_track'): self.btn_locate_track.update_position(w, h, offset_x=0)