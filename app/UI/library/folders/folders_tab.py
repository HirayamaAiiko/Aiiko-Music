import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QListView, QAbstractItemView, QListWidgetItem
from qfluentwidgets import ListWidget, FluentIcon as FIF, TitleLabel, BodyLabel
from delegates.list_delegates import SongListDelegate
from view_models.library_models import TrackListModel, TrackProxyModel
from core.language_manager import tr
class FoldersTab(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.folder_map = {}
        self._build_ui()
        self._populate_folders()
    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self.folders_list = ListWidget(self)
        self.folders_list.setFixedWidth(280)
        self.folders_list.setUniformItemSizes(True)
        self.folders_list.setStyleSheet("""
            QListWidget { background: transparent; border: none; outline: none; }
        """)
        self.folders_list.currentItemChanged.connect(self._on_folder_selected)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        self.empty_state_lbl = BodyLabel(tr("Selecciona una carpeta para ver su contenido"), self)
        self.empty_state_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state_lbl.setStyleSheet("color: rgba(255,255,255,0.5);")
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        from qfluentwidgets import TitleLabel
        self.folder_title = TitleLabel("", self)
        self.folder_title.setContentsMargins(0, 0, 0, 16)
        content_layout.addWidget(self.folder_title)
        self.local_track_model = TrackListModel(self.player)
        self.local_proxy_model = TrackProxyModel(self.player)
        self.local_proxy_model.setSourceModel(self.local_track_model)
        from UI.components.song_table_header import SongTableHeader
        self.table_header = SongTableHeader(self)
        self.table_header.has_covers = True
        content_layout.addWidget(self.table_header)
        from UI.components.draggable_track_list import DraggableTrackListView
        self.list_songs = DraggableTrackListView()
        self.list_songs.setObjectName("SongsList")
        self.table_header.list_view = self.list_songs
        self.list_songs.setModel(self.local_proxy_model)
        self.list_songs.setUniformItemSizes(True)
        self.list_songs.setIconSize(QSize(50, 50))
        self.list_songs.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list_songs.verticalScrollBar().setSingleStep(15)
        self.list_songs.setViewportMargins(0, 5, 0, 0)
        self.list_songs.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_songs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_songs.customContextMenuRequested.connect(lambda pos: self.player.context_menu_manager.show_song_context_menu_listview(pos, list_view=self.list_songs))
        from core.selection_tracker import SelectionTracker
        self.list_songs._selection_tracker = SelectionTracker(self.list_songs)
        self.list_songs.doubleClicked.connect(self.player.queue_controller.play_specific_track_from_listview)
        self.list_songs.setStyleSheet("""
            QListView::item { background-color: transparent; border: none; }
            QListView::item:selected { background-color: transparent; border: none; }
            QListView::item:hover { background-color: transparent; border: none; }
        """)
        from settings_manager import settings
        self.player.folders_is_grid = settings.get('folders_is_grid', False)
        self.set_view_mode(self.player.folders_is_grid)
        self.player.apply_smooth_scroll(self.list_songs)
        self.player.apply_smooth_scroll(self.folders_list)
        content_layout.addWidget(self.list_songs)
        right_layout.addWidget(self.empty_state_lbl)
        right_layout.addWidget(self.content_widget)
        self.content_widget.hide()                           
        layout.addWidget(self.folders_list)
        layout.addWidget(right_panel)
        layout.setStretch(0, 0)                                    
        layout.setStretch(1, 1)                                                      
    def refresh(self):
        self.folders_list.clear()
        self._populate_folders()
    def _populate_folders(self):
        if not hasattr(self.player, 'library'): return
        self.folder_map = {}
        for track in self.player.library:
            if hasattr(track, 'filepath') and track.filepath:
                folder = os.path.dirname(track.filepath)
                if folder not in self.folder_map:
                    self.folder_map[folder] = []
                self.folder_map[folder].append(track)
        sorted_folders = sorted(self.folder_map.keys(), key=lambda f: os.path.basename(f).lower())
        for folder in sorted_folders:
            count = len(self.folder_map[folder])
            display_text = f"{os.path.basename(folder)}  ({count})"
            item = QListWidgetItem(display_text)
            item.setIcon(FIF.FOLDER.icon())
            item.setData(Qt.ItemDataRole.UserRole, folder)
            self.folders_list.addItem(item)
        from settings_manager import settings
        last_folder = settings.get('last_folder', None)
        if last_folder and last_folder in self.folder_map:
            for i in range(self.folders_list.count()):
                item = self.folders_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == last_folder:
                    self.folders_list.setCurrentItem(item)
                    return
        if self.folders_list.count() > 0:
            self.folders_list.setCurrentRow(0)
    def _on_folder_selected(self, current, previous):
        if not current: 
            self.content_widget.hide()
            self.empty_state_lbl.show()
            return
        folder = current.data(Qt.ItemDataRole.UserRole)
        tracks = self.folder_map.get(folder, [])
        self.folder_title.setText(f"{os.path.basename(folder)} ({len(tracks)})")
        from settings_manager import settings
        settings.set('last_folder', folder)
        settings.save()
        self.local_track_model.set_tracks(tracks)
        idx = settings.get('sort_configs', {}).get('folders', 0)
        if idx > 0:
            self.player.library_controller.sort_folders_model(idx)
        self.empty_state_lbl.hide()
        self.content_widget.show()
    def filter_folders(self, query: str):
        query = query.lower()
        first_visible_item = None
        for i in range(self.folders_list.count()):
            item = self.folders_list.item(i)
            folder_path = item.data(Qt.ItemDataRole.UserRole)
            folder_name = os.path.basename(folder_path).lower()
            matches = not query or query in folder_name
            if not matches and query:
                tracks = self.folder_map.get(folder_path, [])
                for t in tracks:
                    if query in t.title.lower() or query in t.artist.lower() or query in getattr(t, 'album', '').lower():
                        matches = True
                        break
            item.setHidden(not matches)
            if matches and first_visible_item is None:
                first_visible_item = item
        current = self.folders_list.currentItem()
        if current and current.isHidden() and first_visible_item:
            self.folders_list.setCurrentItem(first_visible_item)
        elif first_visible_item is None:
            self.content_widget.hide()
            self.empty_state_lbl.setText(tr("No se encontraron carpetas o canciones"))
            self.empty_state_lbl.show()
        elif current and not current.isHidden():
            pass               
        elif first_visible_item:
            self.folders_list.setCurrentItem(first_visible_item)
    def set_view_mode(self, is_grid: bool):
        from PyQt6.QtWidgets import QListView
        from PyQt6.QtCore import QSize
        self.local_track_model.is_grid = is_grid
        if is_grid:
            self.table_header.hide()
            self.list_songs.setViewMode(QListView.ViewMode.IconMode)
            self.list_songs.setResizeMode(QListView.ResizeMode.Adjust)
            self.list_songs.setIconSize(QSize(160, 160))
            self.list_songs.setGridSize(QSize(190, 265))
            self.list_songs.setUniformItemSizes(True)
            self.list_songs.setSpacing(15)
            if not hasattr(self, 'song_grid_delegate'):
                from delegates.grid_delegates import SongGridDelegate
                self.song_grid_delegate = SongGridDelegate(self.list_songs)
            self.list_songs.setItemDelegate(self.song_grid_delegate)
            if not hasattr(self, 'songs_grid_helper'):
                from widgets import ResponsiveGridHelper
                self.songs_grid_helper = ResponsiveGridHelper(self.list_songs, parent=self.player)
            else:
                self.songs_grid_helper.force_recalculate()
        else:
            self.table_header.show()
            self.list_songs.setViewMode(QListView.ViewMode.ListMode)
            self.list_songs.setIconSize(QSize(50, 50))
            self.list_songs.setGridSize(QSize())
            self.list_songs.setSpacing(0)
            self.list_songs.setViewportMargins(0, 5, 0, 0)
            if not hasattr(self, 'song_list_delegate'):
                from delegates.list_delegates import SongListDelegate
                self.song_list_delegate = SongListDelegate(self.list_songs, self.player, is_artist_view=False, is_table_view=True, show_cover_in_table=True)
            self.list_songs.setItemDelegate(self.song_list_delegate)
        self.local_track_model.layoutChanged.emit()