from PyQt6.QtCore import Qt, QRect
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListView, QAbstractItemView, QLabel
from PyQt6.QtGui import QPainter, QColor
from qfluentwidgets import (SubtitleLabel, BodyLabel, PrimaryPushButton, PushButton, 
                            ToolButton, FluentIcon as FIF, FluentIcon, SmoothScrollArea, CaptionLabel, themeColor)
from config import ICON_PLAY, ICON_SHUFFLE, ICON_HEART
from delegates.list_delegates import SongListDelegate
from view_models.library_models import TrackListModel
from widgets import BannerLabel, SquareCoverLabel
from core.language_manager import tr
from UI.library.shared_widgets import ArtistHoverCard, _FakeTrack, PanelCardWidget, HeroOverlayWidget
from database import get_artists_info_batch_db
from utils import normalize_artist_name
from UI.components.song_table_header import SongTableHeader
class DynamicAccentLabel(QLabel):
    def __init__(self, text, base_style, parent=None):
        super().__init__(text, parent)
        self.base_style = base_style
        from qfluentwidgets import qconfig
        qconfig.themeChanged.connect(self._update_color)
        qconfig.themeColorChanged.connect(self._update_color)
        self._update_color()
    def _update_color(self):
        from qfluentwidgets import themeColor
        self.setStyleSheet(f"color: {themeColor().name()}; {self.base_style}")
class AccentIconWidget(QWidget):
    def __init__(self, icon, size=24, parent=None):
        super().__init__(parent)
        self._icon = icon
        self.setFixedSize(size, size)
        from qfluentwidgets import qconfig
        qconfig.themeChanged.connect(self.update)
        qconfig.themeColorChanged.connect(self.update)
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self._icon.render(p, self.rect(), fill=themeColor().name())
class AlbumInfoRow(QWidget):
    def __init__(self, icon, title, value="-", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(15)
        self.icon_widget = AccentIconWidget(icon, size=22)
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        self.lbl_title = CaptionLabel(title.upper())
        self.lbl_title.setStyleSheet("color: #888888; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        self.lbl_value = BodyLabel(value)
        self.lbl_value.setStyleSheet("color: white; font-size: 14px;")
        self.lbl_value.setWordWrap(True)
        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_value)
        layout.addWidget(self.icon_widget, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(text_layout)
    def set_value(self, text):
        self.lbl_value.setText(text)
class AlbumDetailView(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self._build_ui()
    def _build_ui(self):
        self.setObjectName("AlbumDetailWidget")
        self.setStyleSheet("#AlbumDetailWidget { background: transparent; }")
        album_detail_layout = QHBoxLayout(self)
        album_detail_layout.setContentsMargins(0, 0, 0, 0)
        album_detail_layout.setSpacing(10)
        self.left_scroll = SmoothScrollArea()
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setStyleSheet("SmoothScrollArea { background: transparent; border: none; }")
        self.left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.left_main_col = QWidget()
        self.left_main_col.setObjectName("LeftMainCol")
        self.left_main_col.setStyleSheet("#LeftMainCol { background: transparent; }")
        self.left_main_layout = QVBoxLayout(self.left_main_col)
        self.left_main_layout.setContentsMargins(0, 0, 20, 30)
        self.left_main_layout.setSpacing(20)
        self.left_scroll.setWidget(self.left_main_col)
        self.hero_container = BannerLabel()
        self.hero_container.setFixedHeight(280)
        self.hero_container.setObjectName("HeroContainer")
        self.hero_container.setStyleSheet("#HeroContainer { background: transparent; }")
        self.player.album_hero_banner_bg = self.hero_container
        self.hero_overlay = HeroOverlayWidget()
        hero_main_layout = QVBoxLayout(self.hero_container)
        hero_main_layout.setContentsMargins(0, 0, 0, 0)
        hero_main_layout.addWidget(self.hero_overlay)
        hero_layout = QHBoxLayout(self.hero_overlay)
        hero_layout.setContentsMargins(30, 20, 30, 20)
        hero_layout.setSpacing(25)
        self.player.sidebar_cover = SquareCoverLabel(radius=0)
        self.player.sidebar_cover.setFixedSize(220, 220)
        self.player.sidebar_cover.setStyleSheet("background-color: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);")
        hero_info_layout = QVBoxLayout()
        hero_info_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        hero_info_layout.setSpacing(4)
        self.player.lbl_album_type = DynamicAccentLabel(tr("ÁLBUM"), "font-size: 13px; font-weight: bold; letter-spacing: 3px; background: transparent;")
        self.player.sidebar_title = QLabel(tr("Nombre del Álbum"))
        self.player.sidebar_title.setStyleSheet("font-size: 42px; font-weight: 900; color: white; background: transparent;")
        self.player.sidebar_title.setWordWrap(True)
        self.player.sidebar_artist = DynamicAccentLabel(tr("Artista"), "font-size: 18px; font-weight: bold; background: transparent;")
        self.player.sidebar_year = BodyLabel(tr("Año: -"))
        self.player.sidebar_year.setStyleSheet("color: #AAAAAA; font-size: 14px; background: transparent;")
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        self.player.btn_play_album = PrimaryPushButton(self.player.playback_ui_controller._get_icon("play.svg", ICON_PLAY, "#000000"), f" {tr('Reproducir')}")
        self.player.btn_play_album.setFixedSize(140, 40)
        self.player.btn_play_album.clicked.connect(lambda: self.player.queue_controller.play_specific_track_from_listview(self.player.album_tracks_model.index(0, 0)) if self.player.album_tracks_model.rowCount() > 0 else None)
        self.player.btn_shuffle_album = PushButton(self.player.playback_ui_controller._get_icon("shuffle.svg", ICON_SHUFFLE), f" {tr('Aleatorio')}")
        self.player.btn_shuffle_album.setFixedSize(120, 40)
        self.player.btn_shuffle_album.clicked.connect(lambda: self.player.queue_controller.play_album_shuffled(self.player.album_tracks_model))
        self.player.btn_more_album = ToolButton(FluentIcon.MORE)
        self.player.btn_more_album.setFixedSize(40, 40)
        self.player.btn_more_album.clicked.connect(self._show_album_more_menu)
        action_layout.addWidget(self.player.btn_play_album)
        action_layout.addWidget(self.player.btn_shuffle_album)
        action_layout.addWidget(self.player.btn_more_album)
        action_layout.addStretch()
        hero_info_layout.addWidget(self.player.lbl_album_type)
        hero_info_layout.addWidget(self.player.sidebar_title)
        hero_info_layout.addWidget(self.player.sidebar_artist)
        hero_info_layout.addWidget(self.player.sidebar_year)
        hero_info_layout.addSpacing(15)
        hero_info_layout.addLayout(action_layout)
        hero_info_container = QWidget()
        hero_info_container.setStyleSheet("background: transparent;")
        hero_info_container.setLayout(hero_info_layout)
        hero_layout.addWidget(self.player.sidebar_cover)
        hero_layout.addWidget(hero_info_container)
        hero_layout.addStretch()
        hero_wrapper = QWidget()
        hero_wrapper.setStyleSheet("background: transparent;")
        hero_wrapper_layout = QVBoxLayout(hero_wrapper)
        hero_wrapper_layout.setContentsMargins(5, 0, 5, 0)
        hero_wrapper_layout.addWidget(self.hero_container)
        self.left_main_layout.addWidget(hero_wrapper)
        songs_container = QWidget()
        songs_container.setObjectName("SongsContainer")
        songs_container.setStyleSheet("#SongsContainer { background: transparent; }")
        songs_layout = QVBoxLayout(songs_container)
        songs_layout.setContentsMargins(0, 0, 0, 0)
        songs_layout.setSpacing(5)
        self.normal_header = SongTableHeader(is_album_view=True)
        songs_layout.addWidget(self.normal_header)
        from UI.components.draggable_track_list import DraggableTrackListView
        self.player.list_album_tracks = DraggableTrackListView()
        self.normal_header.list_view = self.player.list_album_tracks
        self.player.list_album_tracks.setObjectName("SongsList")
        self.player.list_album_tracks.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.player.list_album_tracks.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.player.list_album_tracks.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.player.list_album_tracks.setStyleSheet("QListView { background: transparent; border: none; outline: none; } QListView::item { background: transparent; border: none; outline: none; }")
        self.player.list_album_tracks.setUniformItemSizes(True)
        self.player.list_album_tracks.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.player.list_album_tracks.customContextMenuRequested.connect(lambda pos: self.player.context_menu_manager.show_song_context_menu_listview(pos, self.player.list_album_tracks))
        self.player.list_album_tracks.doubleClicked.connect(lambda idx: self.player.queue_controller.play_specific_track_from_listview(idx))
        self.player.album_tracks_model = TrackListModel(self.player)
        self.player.list_album_tracks.setModel(self.player.album_tracks_model)
        from core.selection_tracker import SelectionTracker
        self.player.list_album_tracks._selection_tracker = SelectionTracker(self.player.list_album_tracks)
        self.player.list_album_tracks.setItemDelegate(SongListDelegate(self.player.list_album_tracks, self.player, is_table_view=True, is_album_view=True))
        def _adjust_album_list_height():
            count = self.player.album_tracks_model.rowCount()
            self.player.list_album_tracks.setMinimumHeight(count * 50 + 20)
        self.player.album_tracks_model.layoutChanged.connect(_adjust_album_list_height)
        self.player.album_tracks_model.modelReset.connect(_adjust_album_list_height)
        self.player.list_album_tracks.wheelEvent = lambda e: e.ignore()
        self.player.list_album_tracks.viewport().wheelEvent = lambda e: e.ignore()
        songs_layout.addWidget(self.player.list_album_tracks)
        self.left_main_layout.addWidget(songs_container)
        self.left_main_layout.addStretch()
        self.right_scroll = SmoothScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setFixedWidth(320)
        self.right_scroll.setStyleSheet("SmoothScrollArea { background: transparent; border: none; border-left: 1px solid rgba(255,255,255,0.05); }")
        self.right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.right_main_col = QWidget()
        self.right_main_col.setStyleSheet("background: transparent;")
        self.right_main_layout = QVBoxLayout(self.right_main_col)
        self.right_main_layout.setContentsMargins(20, 0, 0, 30)
        self.right_main_layout.setSpacing(15)
        info_group = PanelCardWidget()
        info_group.setFixedHeight(280)
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(10)
        lbl_info_title = SubtitleLabel(tr("Información del Álbum"))
        lbl_info_title.setStyleSheet("font-weight: 900; font-size: 18px; color: white;")
        self.player.lbl_album_info_artist = AlbumInfoRow(FIF.PEOPLE, tr("Artista"))
        self.player.lbl_album_info_year = AlbumInfoRow(FIF.CALENDAR, tr("Año"))
        self.player.lbl_album_info_genre = AlbumInfoRow(FIF.TAG, tr("Género"))
        self.player.lbl_album_info_duration = AlbumInfoRow(FIF.HISTORY, tr("Duración total"))
        info_layout.addWidget(lbl_info_title)
        info_layout.addSpacing(10)
        info_layout.addWidget(self.player.lbl_album_info_artist)
        info_layout.addWidget(self.player.lbl_album_info_year)
        info_layout.addWidget(self.player.lbl_album_info_genre)
        info_layout.addWidget(self.player.lbl_album_info_duration)
        self.right_main_layout.addWidget(info_group)
        self.player.album_artists_container = PanelCardWidget()
        self.player.album_artists_layout = QVBoxLayout(self.player.album_artists_container)
        self.player.album_artists_layout.setContentsMargins(20, 20, 20, 20)
        self.player.album_artists_layout.setSpacing(4)
        lbl_artists_title = SubtitleLabel(tr("Colaboradores"))
        lbl_artists_title.setStyleSheet("font-weight: 900; font-size: 18px; color: white;")
        self.player.album_artists_layout.addWidget(lbl_artists_title)
        self.right_main_layout.addWidget(self.player.album_artists_container)
        self.right_main_layout.addStretch()
        self.right_scroll.setWidget(self.right_main_col)
        album_detail_layout.addWidget(self.left_scroll, 1)
        album_detail_layout.addWidget(self.right_scroll)
        self.sticky_header = SongTableHeader(self, solid_bg=True, is_album_view=True)
        self.sticky_header.list_view = self.player.list_album_tracks
        self.sticky_header.hide()
        self.left_scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)
    def _on_scroll(self, val):
        if hasattr(self, 'normal_header') and hasattr(self, 'sticky_header'):
            from PyQt6.QtCore import QPoint
            pos = self.normal_header.mapTo(self.left_scroll.viewport(), QPoint(0, 0))
            if pos.y() < 0:
                self.sticky_header.show()
                self.sticky_header.raise_()
                self._update_sticky_header_geometry()
            else:
                self.sticky_header.hide()
    def _update_sticky_header_geometry(self):
        w = self.left_scroll.width()
        if self.left_scroll.verticalScrollBar().isVisible():
            w -= self.left_scroll.verticalScrollBar().width()
        w -= 20                                                      
        self.sticky_header.setGeometry(self.left_scroll.x(), self.left_scroll.y(), w, 32)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'sticky_header') and self.sticky_header.isVisible():
            self._update_sticky_header_geometry()
        if hasattr(self, 'right_scroll'):
            if self.width() <= 1050:
                self.right_scroll.hide()
            else:
                self.right_scroll.show()
    def _show_album_more_menu(self):
        from qfluentwidgets import RoundMenu, Action, FluentIcon as FIF
        menu = RoundMenu(parent=self.player)
        menu.addAction(Action(FIF.ADD, tr("Agregar a la cola"), triggered=self._add_album_to_queue))
        from settings_manager import settings
        playlists = settings.get('playlists', {})
        if playlists:
            playlist_menu = RoundMenu(tr("Agregar a la playlist"), parent=menu)
            playlist_menu.setIcon(FIF.ALBUM)
            for p_name in playlists.keys():
                playlist_menu.addAction(Action(p_name, triggered=lambda _, p=p_name: self._add_album_to_playlist(p)))
            menu.addMenu(playlist_menu)
        menu.addAction(Action(ICON_HEART, tr("Agregar a favoritos"), triggered=self._add_album_to_favorites))
        pos = self.player.btn_more_album.mapToGlobal(self.player.btn_more_album.rect().bottomLeft())
        menu.exec(pos)
    def _add_album_to_queue(self):
        if hasattr(self.player, 'album_tracks_model') and self.player.album_tracks_model:
            tracks = list(self.player.album_tracks_model.tracks)
            if tracks:
                album_name = self.player.sidebar_title.text()
                msg = tr("Se agregaron {count} canciones del álbum {album}").format(count=len(tracks), album=album_name)
                self.player.queue_controller.add_to_queue(tracks, show_notification=True, custom_notify_text=msg)
    def _add_album_to_playlist(self, playlist_name):
        if hasattr(self.player, 'album_tracks_model') and self.player.album_tracks_model:
            tracks = list(self.player.album_tracks_model.tracks)
            if tracks:
                count = 0
                for t in tracks:
                    self.player.app_controller.add_to_playlist(playlist_name, t, batch_mode=True)
                    count += 1
                from settings_manager import settings
                settings.save()
                if hasattr(self.player, 'page_playlists') and getattr(self.player.page_playlists, 'current_playlist_name', None) == playlist_name:
                    self.player.library_controller.refresh_playlists_view_details()
                self.player.library_controller.refresh_artist_related_playlists()
                from core.notification_manager import notify
                album_name = self.player.sidebar_title.text()
                notify.success(tr("Añadido a playlist"), tr("Se agregaron {count} canciones de {album} a {playlist}").format(count=count, album=album_name, playlist=playlist_name))
    def _add_album_to_favorites(self):
        if hasattr(self.player, 'album_tracks_model') and self.player.album_tracks_model:
            tracks = list(self.player.album_tracks_model.tracks)
            if tracks:
                from settings_manager import settings
                favs = settings.get('favorites', [])
                count = 0
                for t in tracks:
                    if t.filepath not in favs:
                        favs.append(t.filepath)
                        count += 1
                if count > 0:
                    settings.set('favorites', favs)
                    settings.save()
                    self.player.playback_ui_controller.update_favorite_icon_ui()
                    self.player.library_controller.refresh_favorites_view()
                from core.notification_manager import notify
                album_name = self.player.sidebar_title.text()
                notify.success(tr("Añadido a favoritos"), tr("Se agregaron {count} canciones nuevas de {album}").format(count=count, album=album_name))
    def populate_album_artists(self, artists_list):
        while self.player.album_artists_layout.count() > 1:
            child = self.player.album_artists_layout.takeAt(1)
            if child.widget():
                child.widget().deleteLater()
        if not artists_list:
            return
        normalized_names = [normalize_artist_name(name) for name in artists_list]
        artists_data_batch = get_artists_info_batch_db(normalized_names)
        for i, artist_name in enumerate(artists_list):
            card = ArtistHoverCard(artist_name, self.player)
            artist_data = artists_data_batch.get(normalized_names[i], {})
            cover_path = artist_data.get('cover_path')
            ft = _FakeTrack(cover_path)
            self.player.image_cache.assign_async_pixmap(card.avatar, ft, 42, 42, fallback_icon=FIF.PEOPLE)
            self.player.album_artists_layout.addWidget(card)