import math
from PyQt6.QtCore import Qt, QSize, QAbstractListModel, QModelIndex, QTime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListView,
                             QAbstractItemView, QStackedWidget)
from qfluentwidgets import (TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
                            PushButton, SearchLineEdit, TransparentToolButton, FluentIcon as FIF,
                            ComboBox)
from widgets import AspectRatioLabel
from config import ICON_PLAY, ICON_SHUFFLE, ICON_HEART
from settings_manager import settings
import theme_manager
from core.language_manager import tr
class FavoritesTrackModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks = []
    def rowCount(self, parent=QModelIndex()):
        return len(self._tracks)
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._tracks):
            return None
        if role == Qt.ItemDataRole.UserRole:
            return self._tracks[index.row()]
        return None
    def set_tracks(self, tracks):
        self.beginResetModel()
        self._tracks = list(tracks)
        self.endResetModel()
    def tracks(self):
        return self._tracks
class FavoritesView(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.setObjectName("PageContent")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.all_favorite_tracks = []
        self._build_ui()
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 10, 30, 0)
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.addWidget(TitleLabel(tr("Mis Favoritos")))
        self.lbl_stats = CaptionLabel(tr("0 canciones • 00:00"))
        from PyQt6.QtGui import QColor
        self.lbl_stats.setTextColor(QColor('#888888'), QColor('#888888'))
        font = self.lbl_stats.font()
        font.setPixelSize(14)
        self.lbl_stats.setFont(font)
        title_layout.addWidget(self.lbl_stats)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)
        actions_layout = QHBoxLayout()
        from qfluentwidgets import PrimaryPushButton
        self.btn_play_all = PrimaryPushButton(self.player.playback_ui_controller._get_icon("play.svg", ICON_PLAY, "#000000"), tr("Reproducir Todo"))
        self.btn_play_all.clicked.connect(self._play_all)
        self.btn_shuffle = PushButton(self.player.playback_ui_controller._get_icon("shuffle.svg", ICON_SHUFFLE), tr("Aleatorio"))
        self.btn_shuffle.clicked.connect(self._play_shuffle)
        actions_layout.addWidget(self.btn_play_all)
        actions_layout.addWidget(self.btn_shuffle)
        actions_layout.addStretch()
        self.search_bar = SearchLineEdit()
        from PyQt6.QtCore import QSize
        self.search_bar.searchButton.setIconSize(QSize(14, 14))
        self.search_bar.clearButton.setIconSize(QSize(14, 14))
        self.search_bar.setPlaceholderText(tr("Buscar en favoritos..."))
        self.search_bar.setFixedWidth(250)
        self.search_bar.textChanged.connect(self._filter_favorites)
        actions_layout.addWidget(self.search_bar)
        from UI.components.sort_filter_button import SortFilterButton
        self.sort_combo = SortFilterButton([
            tr("A-Z"), tr("Z-A"), tr("Artista"), tr("Álbum"), 
            tr("Agregado recientemente"), tr("Agregado (Antiguos)"),
            tr("Duración (Mayor)"), tr("Duración (Menor)"),
            tr("ReplayGain")
        ])
        sort_configs = settings.get('sort_configs', {})
        saved_idx = sort_configs.get('favorites', 0)
        if 0 <= saved_idx < self.sort_combo.count():
            self.sort_combo.setCurrentIndex(saved_idx)
        self.sort_combo.currentIndexChanged.connect(self._sort_favorites)
        actions_layout.addWidget(self.sort_combo)
        main_layout.addLayout(actions_layout)
        main_layout.addSpacing(10)
        from UI.components.song_table_header import SongTableHeader
        self.table_header = SongTableHeader(self)
        self.table_header.has_covers = True
        self.table_header.hide()
        main_layout.addWidget(self.table_header)
        self.stacked = QStackedWidget()
        self._fav_model = FavoritesTrackModel(self)
        from UI.components.draggable_track_list import DraggableTrackListView
        self.list_favorites = DraggableTrackListView()
        self.list_favorites.setObjectName("FavoritesList")
        self.table_header.list_view = self.list_favorites
        self.list_favorites.setModel(self._fav_model)
        self.list_favorites.setUniformItemSizes(True)
        self.list_favorites.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list_favorites.verticalScrollBar().setSingleStep(15)
        self.list_favorites.setViewportMargins(0, 5, 0, 0)
        self.list_favorites.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_favorites.setStyleSheet(
            "QListView { border: none; background: transparent; }"
            "QListView::item { background-color: transparent; border: none; }"
            "QListView::item:selected { background: transparent; border: none; }"
        )
        self.list_favorites.doubleClicked.connect(self._on_item_double_clicked)
        self.list_favorites.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_favorites.customContextMenuRequested.connect(self._show_context_menu)
        from core.selection_tracker import SelectionTracker
        self.list_favorites._selection_tracker = SelectionTracker(self.list_favorites)
        from delegates.list_delegates import SongListDelegate
        self._delegate = SongListDelegate(self.list_favorites, self.player, is_artist_view=False, is_table_view=True, show_cover_in_table=True)
        self.list_favorites.setItemDelegate(self._delegate)
        self.player.apply_smooth_scroll(self.list_favorites)
        self.stacked.addWidget(self.list_favorites)
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.addStretch()                     
        empty_icon = AspectRatioLabel()
        empty_icon.setFixedSize(120, 120)
        empty_icon.setPixmap(self.player.playback_ui_controller._get_icon("heart.svg", ICON_HEART, "#444444").pixmap(120, 120))
        empty_layout.addWidget(empty_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        empty_title = SubtitleLabel(tr("Aún no tienes favoritos"))
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)
        empty_desc = BodyLabel(tr("Toca el icono del corazón en cualquier canción\npara agregarla a esta lista."))
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        from PyQt6.QtGui import QColor
        empty_desc.setTextColor(QColor('#888888'), QColor('#888888'))
        empty_layout.addWidget(empty_desc)
        empty_layout.addStretch()
        self.stacked.addWidget(self.empty_widget)
        main_layout.addWidget(self.stacked)
        from UI.components.scroll_to_top import ScrollToTopButton
        from UI.components.locate_track_button import LocateTrackButton
        self.btn_scroll_top = ScrollToTopButton(self.list_favorites, self)
        self.btn_locate_track = LocateTrackButton(self.player, self.list_favorites, self)
        self.btn_locate_track.set_model(self._fav_model)
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
    def load_favorites(self, tracks):
        self.all_favorite_tracks = tracks
        self._update_stats()
        self._sort_favorites(self.sort_combo.currentIndex())
    def _render_list(self, tracks):
        if not self.all_favorite_tracks:
            self.stacked.setCurrentWidget(self.empty_widget)
            self.table_header.hide()
            self.btn_play_all.setDisabled(True)
            self.btn_shuffle.setDisabled(True)
            return
        self.stacked.setCurrentWidget(self.list_favorites)
        self.table_header.show()
        self.btn_play_all.setDisabled(False)
        self.btn_shuffle.setDisabled(False)
        self._fav_model.set_tracks(tracks)
    def _update_stats(self):
        count = len(self.all_favorite_tracks)
        if count == 0:
            self.lbl_stats.setText(tr("0 canciones"))
            return
        total_ms = sum(t.duration for t in self.all_favorite_tracks if hasattr(t, 'duration') and t.duration)
        total_s = total_ms / 1000
        if total_s < 3600:
            dur_str = QTime(0, 0, 0).addSecs(math.floor(total_s)).toString("mm:ss")
        else:
            h = math.floor(total_s / 3600)
            m = math.floor((total_s % 3600) / 60)
            dur_str = f"{h}h {m}m"
        self.lbl_stats.setText(tr("{count} canciones • {duration}").format(count=count, duration=dur_str))
    def _filter_favorites(self, text):
        if not text:
            self._render_list(self.all_favorite_tracks)
            return
        text = text.lower()
        filtered = [t for t in self.all_favorite_tracks if text in t.title.lower() or text in t.artist.lower()]
        self._render_list(filtered)
    def _sort_favorites(self, index):
        sort_configs = settings.get('sort_configs', {})
        sort_configs['favorites'] = index
        settings.set('sort_configs', sort_configs)
        settings.save()
        if index == 0:
            self.all_favorite_tracks.sort(key=lambda t: getattr(t, 'title', '').lower())
        elif index == 1:
            self.all_favorite_tracks.sort(key=lambda t: getattr(t, 'title', '').lower(), reverse=True)
        elif index == 2:
            self.all_favorite_tracks.sort(key=lambda t: getattr(t, 'artist', '').lower() + getattr(t, 'title', '').lower())
        elif index == 3:
            self.all_favorite_tracks.sort(key=lambda t: getattr(t, 'album', '').lower() + getattr(t, 'title', '').lower())
        elif index in (4, 5):
            fav_list = settings.get('favorites', [])
            fav_map = {fp: i for i, fp in enumerate(fav_list)}
            self.all_favorite_tracks.sort(key=lambda t: fav_map.get(t.filepath, -1), reverse=(index == 4))
        elif index == 6:
            self.all_favorite_tracks.sort(key=lambda t: getattr(t, 'duration', 0), reverse=True)
        elif index == 7:
            self.all_favorite_tracks.sort(key=lambda t: getattr(t, 'duration', 0))
        elif index == 8:
            self.all_favorite_tracks.sort(key=lambda t: getattr(t, 'replaygain_track', 0.0))
        self._filter_favorites(self.search_bar.text())
    def _on_item_double_clicked(self, index):
        track = index.data(Qt.ItemDataRole.UserRole)
        if track:
            self.player.queue_controller.play_specific_track_global(track, self._fav_model.tracks())
    def _show_context_menu(self, pos):
        index = self.list_favorites.indexAt(pos)
        if not index.isValid():
            return
        track = index.data(Qt.ItemDataRole.UserRole)
        if track:
            global_pos = self.list_favorites.viewport().mapToGlobal(pos)
            selected_tracks = []
            if hasattr(self.list_favorites, '_selection_tracker'):
                selected_tracks = self.list_favorites._selection_tracker.get_selected_tracks()
            if track not in selected_tracks:
                selected_tracks = [track]
            self.player.context_menu_manager.show_song_context_menu_multiple_at(selected_tracks, global_pos, self.all_favorite_tracks)
    def _play_all(self):
        if not self.all_favorite_tracks: return
        self.player.queue_controller.play_specific_track_global(self.all_favorite_tracks[0], self.all_favorite_tracks)
    def _play_shuffle(self):
        if not self.all_favorite_tracks: return
        import random
        shuffled = list(self.all_favorite_tracks)
        random.shuffle(shuffled)
        self.player.queue_controller.play_specific_track_global(shuffled[0], shuffled)