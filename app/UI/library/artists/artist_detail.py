from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListView, QAbstractItemView, QSizePolicy, QLabel
from qfluentwidgets import TitleLabel, SubtitleLabel, BodyLabel, SmoothScrollArea
from qfluentwidgets import PrimaryPushButton, PushButton, ToolButton, FluentIcon
from delegates.list_delegates import SongListDelegate
from view_models.library_models import TrackListModel
from widgets import AspectRatioLabel
from UI.library.shared_widgets import CircularAvatar, PanelCardWidget, HeroOverlayWidget, AccentIconWidget
import theme_manager
from core.language_manager import tr
class ArtistDetailView(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self._build_ui()
    def _build_ui(self):
        self.setObjectName("ArtistDetailWidget")
        self.setStyleSheet("#ArtistDetailWidget { background: transparent; }")
        artist_detail_layout = QHBoxLayout(self)
        artist_detail_layout.setContentsMargins(0, 0, 0, 0)
        artist_detail_layout.setSpacing(10)
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
        from widgets import BannerLabel
        self.hero_container = BannerLabel()
        self.hero_container.setFixedHeight(280)
        self.hero_container.setObjectName("HeroContainer")
        self.hero_container.setStyleSheet("#HeroContainer { background: transparent; }")
        self.player.hero_banner_bg = self.hero_container
        self.hero_overlay = HeroOverlayWidget()
        hero_main_layout = QVBoxLayout(self.hero_container)
        hero_main_layout.setContentsMargins(0, 0, 0, 0)
        hero_main_layout.addWidget(self.hero_overlay)
        hero_layout = QHBoxLayout(self.hero_overlay)
        hero_layout.setContentsMargins(30, 20, 30, 20)
        hero_layout.setSpacing(25)
        self.player.sidebar_artist_cover = CircularAvatar(200)
        hero_info_layout = QVBoxLayout()
        hero_info_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        hero_info_layout.setSpacing(4)
        self.player.sidebar_artist_title = QLabel(tr("Nombre del Artista"))
        self.player.sidebar_artist_title.setStyleSheet("font-size: 38px; font-weight: 900; color: white; background: transparent;")
        self.player.sidebar_artist_title.setWordWrap(True)
        accent = theme_manager.get_current_accent_hex()
        self.player.sidebar_artist_stats = BodyLabel(tr("0 Canciones • 0 Reproducciones"))
        self.player.sidebar_artist_stats.setStyleSheet(f"color: {accent}; font-size: 14px; background: transparent;")
        self.player.sidebar_artist_desc = BodyLabel("")
        self.player.sidebar_artist_desc.setWordWrap(True)
        self.player.sidebar_artist_desc.setStyleSheet("color: #CCCCCC; font-size: 13px; line-height: 1.5;")
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        from config import ICON_PLAY, ICON_SHUFFLE
        self.player.btn_play_artist = PrimaryPushButton(self.player.playback_ui_controller._get_icon("play.svg", ICON_PLAY, "#000000"), f" {tr('Reproducir')}")
        self.player.btn_play_artist.setFixedSize(130, 36)
        self.player.btn_shuffle_artist = PushButton(self.player.playback_ui_controller._get_icon("shuffle.svg", ICON_SHUFFLE), f" {tr('Aleatorio')}")
        self.player.btn_shuffle_artist.setFixedSize(110, 36)
        self.player.btn_more_artist = ToolButton(FluentIcon.MORE)
        self.player.btn_more_artist.setFixedSize(36, 36)
        action_layout.addWidget(self.player.btn_play_artist)
        action_layout.addWidget(self.player.btn_shuffle_artist)
        action_layout.addWidget(self.player.btn_more_artist)
        action_layout.addStretch()
        self.player.btn_play_artist.clicked.connect(self._play_artist_tracks)
        self.player.btn_shuffle_artist.clicked.connect(self._shuffle_artist_tracks)
        self.player.btn_more_artist.clicked.connect(self._show_artist_more_menu)
        hero_info_layout.addWidget(self.player.sidebar_artist_title)
        hero_info_layout.addWidget(self.player.sidebar_artist_stats)
        self.player.sidebar_artist_desc.hide()
        hero_info_layout.addLayout(action_layout)
        hero_layout.addWidget(self.player.sidebar_artist_cover)
        hero_layout.addLayout(hero_info_layout)
        hero_layout.addStretch()
        hero_wrapper = QWidget()
        hero_wrapper.setStyleSheet("background: transparent;")
        hero_wrapper_layout = QVBoxLayout(hero_wrapper)
        hero_wrapper_layout.setContentsMargins(5, 0, 5, 0)
        hero_wrapper_layout.addWidget(self.hero_container)
        self.left_main_layout.addWidget(hero_wrapper)
        from widgets import CustomLibraryTabs
        self.artist_tabs = CustomLibraryTabs(self.player)
        self.artist_tabs.addItem('overview', tr('Resumen'), callback=lambda: self.switch_artist_tab('overview'))
        self.artist_tabs.addItem('songs', tr('Canciones'), callback=lambda: self.switch_artist_tab('songs'))
        self.artist_tabs.addItem('albums', tr('Discografía'), callback=lambda: self.switch_artist_tab('albums'))
        self.artist_tabs.addItem('playlists', tr('Playlists relacionadas'), callback=lambda: self.switch_artist_tab('playlists'))
        self.artist_tabs.setCurrentItem('overview')
        self.artist_tabs.lbl_count.setVisible(False)
        self.left_main_layout.addWidget(self.artist_tabs)
        self.artist_content_stack = QStackedWidget()
        self.overview_tab = QWidget()
        overview_layout = QVBoxLayout(self.overview_tab)
        overview_layout.setContentsMargins(10, 10, 10, 10)
        overview_layout.setSpacing(20)
        top_tracks_header_layout = QHBoxLayout()
        top_tracks_header_layout.setContentsMargins(0, 0, 0, 0)
        top_tracks_title = SubtitleLabel(tr("Más Escuchados"))
        top_tracks_title.setStyleSheet("font-weight: bold; font-size: 20px;")
        top_tracks_header_layout.addWidget(top_tracks_title)
        top_tracks_header_layout.addStretch()
        from UI.components.draggable_track_list import DraggableTrackListView
        self.player.top_tracks_list = DraggableTrackListView()
        self.player.top_tracks_list.setObjectName("TopTracksList")
        self.player.top_tracks_list.setFixedHeight(255)
        self.player.top_tracks_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.player.top_tracks_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.player.top_tracks_list.setUniformItemSizes(True)
        self.player.top_tracks_list.setStyleSheet("QListView { background: transparent; border: none; } QListView::item { background: transparent; border: none; }")
        self.player.top_tracks_model = TrackListModel(self.player)
        self.player.top_tracks_list.setModel(self.player.top_tracks_model)
        from core.selection_tracker import SelectionTracker
        self.player.top_tracks_list._selection_tracker = SelectionTracker(self.player.top_tracks_list)
        self.player.top_tracks_list.setItemDelegate(SongListDelegate(self.player.top_tracks_list, self.player, is_artist_view=True))
        self.player.top_tracks_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.player.top_tracks_list.customContextMenuRequested.connect(lambda pos: self.player.context_menu_manager.show_song_context_menu_listview(pos, self.player.top_tracks_list))
        self.player.top_tracks_list.doubleClicked.connect(lambda idx: self.player.queue_controller.play_specific_track_from_listview(idx))
        if hasattr(self.player, 'image_cache'):
            self.player.image_cache.cache_updated.connect(self.player.top_tracks_list.viewport().update)
        overview_layout.addLayout(top_tracks_header_layout)
        overview_layout.addWidget(self.player.top_tracks_list)
        disco_title = SubtitleLabel(tr("Lanzamientos más recientes"))
        disco_title.setStyleSheet("font-weight: bold; font-size: 20px;")
        from UI.dashboard.components.dashboard_buttons import _CarouselArrowBtn
        from UI.dashboard.components.dashboard_main_panel import _HorizontalDragFilter
        self.disco_container_layout = QHBoxLayout()
        self.disco_container_layout.setContentsMargins(0, 0, 0, 0)
        self.disco_container_layout.setSpacing(12)
        self.disco_inner_widget = QWidget()
        self.disco_inner_widget.setStyleSheet("background: transparent;")
        self.disco_inner_widget.setLayout(self.disco_container_layout)
        self.disco_scroll = SmoothScrollArea()
        self.disco_scroll.setWidgetResizable(True)
        self.disco_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.disco_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.disco_scroll.setFixedHeight(230)
        self.disco_scroll.setStyleSheet("SmoothScrollArea { border: none; background: transparent; }")
        self.disco_scroll.setWidget(self.disco_inner_widget)
        self.disco_scroll.viewport().installEventFilter(_HorizontalDragFilter(self.disco_scroll))
        btn_left  = _CarouselArrowBtn("left")
        btn_right = _CarouselArrowBtn("right")
        def _update_arrows():
            hbar = self.disco_scroll.horizontalScrollBar()
            btn_left.set_active(hbar.value() > 0)
            btn_right.set_active(hbar.value() < hbar.maximum())
        self.disco_scroll.horizontalScrollBar().valueChanged.connect(lambda _: _update_arrows())
        self.disco_scroll.horizontalScrollBar().rangeChanged.connect(lambda *_: _update_arrows())
        _update_arrows()
        def _smooth_scroll(target_val):
            hbar = self.disco_scroll.horizontalScrollBar()
            if not hasattr(self.disco_scroll, "_scroll_anim"):
                from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
                self.disco_scroll._scroll_anim = QPropertyAnimation(hbar, b"value", self.disco_scroll)
                self.disco_scroll._scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                self.disco_scroll._scroll_anim.setDuration(350)
            self.disco_scroll._scroll_anim.stop()
            self.disco_scroll._scroll_anim.setStartValue(hbar.value())
            self.disco_scroll._scroll_anim.setEndValue(target_val)
            self.disco_scroll._scroll_anim.start()
        _STEP = 172 * 2
        btn_left.clicked.connect(lambda: _smooth_scroll(max(0, self.disco_scroll.horizontalScrollBar().value() - _STEP)))
        btn_right.clicked.connect(lambda: _smooth_scroll(min(self.disco_scroll.horizontalScrollBar().maximum(), self.disco_scroll.horizontalScrollBar().value() + _STEP)))
        carousel_row = QHBoxLayout()
        carousel_row.setContentsMargins(0, 0, 0, 0)
        carousel_row.setSpacing(0)
        carousel_row.addWidget(btn_left)
        carousel_row.addWidget(self.disco_scroll, 1)
        carousel_row.addWidget(btn_right)
        self.player.populate_artist_discography = self.populate_discography
        overview_layout.addWidget(disco_title)
        overview_layout.addLayout(carousel_row)
        overview_layout.addStretch()
        self.artist_content_stack.addWidget(self.overview_tab)
        self.songs_tab = QWidget()
        songs_layout = QVBoxLayout(self.songs_tab)
        songs_layout.setContentsMargins(0, 0, 0, 0)
        songs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.player.list_artist_tracks = DraggableTrackListView()
        from UI.components.song_table_header import SongTableHeader
        self.songs_header = SongTableHeader(is_artist_view=True)
        self.songs_header.has_covers = True
        self.songs_header.list_view = self.player.list_artist_tracks
        songs_layout.addWidget(self.songs_header)
        self.sticky_header = SongTableHeader(solid_bg=True, is_artist_view=True)
        self.sticky_header.has_covers = True
        self.sticky_header.list_view = self.player.list_artist_tracks
        self.sticky_header.setParent(self)
        self.sticky_header.hide()
        songs_layout.addWidget(self.player.list_artist_tracks)
        self.player.list_artist_tracks.setObjectName("SongsList")
        self.player.list_artist_tracks.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.player.list_artist_tracks.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.player.list_artist_tracks.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.player.list_artist_tracks.setUniformItemSizes(True)
        self.player.list_artist_tracks.setStyleSheet("QListView { background: transparent; border: none; } QListView::item { background: transparent; border: none; }")
        self.player.list_artist_tracks.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.player.list_artist_tracks.customContextMenuRequested.connect(lambda pos: self.player.context_menu_manager.show_song_context_menu_listview(pos, self.player.list_artist_tracks))
        self.player.list_artist_tracks.doubleClicked.connect(lambda idx: self.player.queue_controller.play_specific_track_from_listview(idx))
        if hasattr(self.player, 'image_cache'):
            self.player.image_cache.cache_updated.connect(self.player.list_artist_tracks.viewport().update)
        self.player.artist_tracks_model = TrackListModel(self.player)
        self.player.list_artist_tracks.setModel(self.player.artist_tracks_model)
        from core.selection_tracker import SelectionTracker
        self.player.list_artist_tracks._selection_tracker = SelectionTracker(self.player.list_artist_tracks)
        self.player.list_artist_tracks.setItemDelegate(SongListDelegate(
            self.player.list_artist_tracks, 
            self.player, 
            is_artist_view=True,
            is_table_view=True,
            show_cover_in_table=True
        ))
        def _adjust_artist_list_height():
            count = self.player.artist_tracks_model.rowCount()
            self.player.list_artist_tracks.setMinimumHeight(count * 50 + 20)
        self.player.artist_tracks_model.layoutChanged.connect(_adjust_artist_list_height)
        self.player.artist_tracks_model.modelReset.connect(_adjust_artist_list_height)
        self.player.list_artist_tracks.wheelEvent = lambda e: e.ignore()
        self.player.list_artist_tracks.viewport().wheelEvent = lambda e: e.ignore()
        songs_layout.addWidget(self.player.list_artist_tracks)
        self.artist_content_stack.addWidget(self.songs_tab)
        self.albums_tab = QWidget()
        albums_layout = QVBoxLayout(self.albums_tab)
        albums_layout.setContentsMargins(0, 10, 0, 0)
        albums_layout.setSpacing(25)
        from qfluentwidgets import FlowLayout
        self.lbl_full_albums = SubtitleLabel(tr("Álbumes"))
        self.lbl_full_albums.setStyleSheet("font-size: 20px; font-weight: bold;")
        albums_layout.addWidget(self.lbl_full_albums)
        self.albums_flow = FlowLayout()
        self.albums_flow.setContentsMargins(0, 0, 0, 0)
        self.albums_flow.setSpacing(12)
        albums_layout.addLayout(self.albums_flow)
        self.lbl_full_eps = SubtitleLabel(tr("Sencillos y EP"))
        self.lbl_full_eps.setStyleSheet("font-size: 20px; font-weight: bold;")
        albums_layout.addWidget(self.lbl_full_eps)
        self.eps_flow = FlowLayout()
        self.eps_flow.setContentsMargins(0, 0, 0, 0)
        self.eps_flow.setSpacing(12)
        albums_layout.addLayout(self.eps_flow)
        albums_layout.addStretch()
        self.player.populate_full_discography = self.populate_full_discography
        self.artist_content_stack.addWidget(self.albums_tab)
        self.playlists_tab = QWidget()
        playlists_layout = QVBoxLayout(self.playlists_tab)
        playlists_layout.setContentsMargins(10, 10, 10, 10)
        self.playlists_stack = QStackedWidget()
        self.playlists_grid_widget = QWidget()
        pg_layout = QVBoxLayout(self.playlists_grid_widget)
        pg_layout.setContentsMargins(0, 10, 0, 0)
        self.playlists_flow = FlowLayout()
        self.playlists_flow.setContentsMargins(0, 0, 0, 0)
        self.playlists_flow.setSpacing(12)
        pg_layout.addLayout(self.playlists_flow)
        pg_layout.addStretch()
        self.playlists_empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.playlists_empty_widget)
        empty_layout.addStretch()
        empty_title = SubtitleLabel(tr("Sin playlists relacionadas"))
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)
        empty_desc = BodyLabel(tr("Ninguna canción de este artista está en tus playlists."))
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_desc.setStyleSheet("color: #888888;")
        empty_layout.addWidget(empty_desc)
        empty_layout.addStretch()
        self.playlists_stack.addWidget(self.playlists_grid_widget)
        self.playlists_stack.addWidget(self.playlists_empty_widget)
        playlists_layout.addWidget(self.playlists_stack)
        self.artist_content_stack.addWidget(self.playlists_tab)
        self.left_main_layout.addWidget(self.artist_content_stack)
        self.right_main_col = QWidget()
        self.right_main_col.setObjectName("RightMainCol")
        self.right_main_col.setStyleSheet("#RightMainCol { background: transparent; }")
        self.right_main_col.setFixedWidth(320)
        self.right_main_layout = QVBoxLayout(self.right_main_col)
        self.right_main_layout.setContentsMargins(0, 0, 20, 0) 
        self.right_main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.right_main_layout.setSpacing(20)
        info_card = PanelCardWidget()
        info_card.setFixedHeight(280)
        info_card_layout = QVBoxLayout(info_card)
        info_card_layout.setContentsMargins(20, 20, 20, 20)
        info_card_layout.setSpacing(15)
        info_title = SubtitleLabel(tr("Información del artista"))
        info_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_pts_layout = QVBoxLayout()
        info_pts_layout.setSpacing(15)
        bio_row = QHBoxLayout()
        bio_row.setSpacing(12)
        bio_icon = AccentIconWidget(FluentIcon.INFO, size=20)
        self.player.sidebar_artist_bio_right = BodyLabel("")
        self.player.sidebar_artist_bio_right.setWordWrap(True)
        self.player.sidebar_artist_bio_right.setStyleSheet("color: #CCCCCC; font-size: 13px; line-height: 1.5;")
        bio_row.addWidget(bio_icon, alignment=Qt.AlignmentFlag.AlignTop)
        bio_row.addWidget(self.player.sidebar_artist_bio_right, 1)
        tags_row = QHBoxLayout()
        tags_row.setSpacing(12)
        tags_icon = AccentIconWidget(FluentIcon.TAG, size=20)
        self.player.sidebar_artist_tags = BodyLabel("")
        self.player.sidebar_artist_tags.setWordWrap(True)
        self.player.sidebar_artist_tags.setStyleSheet("color: #CCCCCC; font-size: 13px; font-weight: 500;")
        tags_row.addWidget(tags_icon, alignment=Qt.AlignmentFlag.AlignTop)
        tags_row.addWidget(self.player.sidebar_artist_tags, 1)
        info_pts_layout.addLayout(bio_row)
        info_pts_layout.addStretch()
        info_pts_layout.addLayout(tags_row)
        info_card_layout.addWidget(info_title)
        info_card_layout.addLayout(info_pts_layout)
        self.right_main_layout.addWidget(info_card)
        self.recommended_card = PanelCardWidget()
        self.recommended_layout = QVBoxLayout(self.recommended_card)
        self.recommended_layout.setContentsMargins(20, 20, 20, 20)
        self.recommended_layout.setSpacing(15)
        rec_title = SubtitleLabel(tr("Otros artistas"))
        rec_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.recommended_layout.addWidget(rec_title)
        self.recommended_list_layout = QVBoxLayout()
        self.recommended_list_layout.setSpacing(4)
        self.recommended_layout.addLayout(self.recommended_list_layout)
        self.right_main_layout.addWidget(self.recommended_card)
        self.player.populate_recommended_artists = self.populate_recommended_artists
        self.right_main_layout.addStretch()
        self.right_scroll = SmoothScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setStyleSheet("SmoothScrollArea { background: transparent; border: none; }")
        self.right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.right_scroll.setFixedWidth(330)
        self.right_scroll.setWidget(self.right_main_col)
        self._scroll_hide_timer = QTimer(self)
        self._scroll_hide_timer.setSingleShot(True)
        self._scroll_hide_timer.setInterval(1500)
        def _show_left_vbar():
            self.left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.left_scroll.verticalScrollBar().show()
            self._scroll_hide_timer.start()
        def _hide_vbars():
            self.left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.left_scroll.verticalScrollBar().hide()
        self._scroll_hide_timer.timeout.connect(_hide_vbars)
        self.left_scroll.verticalScrollBar().valueChanged.connect(lambda _: _show_left_vbar())
        self.left_scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self.artist_content_stack.currentChanged.connect(lambda _: self._on_scroll(self.left_scroll.verticalScrollBar().value()))
        _hide_vbars()
        artist_detail_layout.addWidget(self.left_scroll, stretch=7)
        artist_detail_layout.addWidget(self.right_scroll, stretch=3)
    def _on_scroll(self, val):
        if hasattr(self, 'songs_header') and hasattr(self, 'sticky_header'):
            if self.artist_content_stack.currentWidget() == self.songs_tab:
                from PyQt6.QtCore import QPoint
                pos = self.songs_header.mapTo(self.left_scroll.viewport(), QPoint(0, 0))
                if pos.y() < 0:
                    self.sticky_header.show()
                    self.sticky_header.raise_()
                    self._update_sticky_header_geometry()
                else:
                    self.sticky_header.hide()
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
    def switch_artist_tab(self, route):
        for i in range(self.artist_content_stack.count()):
            widget = self.artist_content_stack.widget(i)
            widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        if route == 'overview':
            self.artist_content_stack.setCurrentIndex(0)
        elif route == 'songs':
            self.artist_content_stack.setCurrentIndex(1)
        elif route == 'albums':
            self.artist_content_stack.setCurrentIndex(2)
        elif route == 'playlists':
            self.artist_content_stack.setCurrentIndex(3)
        current_widget = self.artist_content_stack.currentWidget()
        current_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.artist_content_stack.adjustSize()
    def populate_related_playlists(self, playlists_dict):
        if not hasattr(self, 'playlists_stack'):
            return
        if not playlists_dict:
            self.playlists_stack.setCurrentWidget(self.playlists_empty_widget)
            self.artist_tabs.lbl_count.setVisible(False)
        else:
            self.playlists_stack.setCurrentWidget(self.playlists_grid_widget)
            self.artist_tabs.lbl_count.setText(str(len(playlists_dict)))
            self.artist_tabs.lbl_count.setVisible(True)
        while self.playlists_flow.count():
            item = self.playlists_flow.takeAt(0)
            if item:
                w = item.widget() if hasattr(item, 'widget') else item
                if w: w.deleteLater()
        from UI.dashboard.components.dashboard_cards import CoverCard
        from core.language_manager import tr
        for name, data in playlists_dict.items():
            filepaths = data.get('filepaths', [])
            cover_path = data.get('cover')
            count_str = tr("{count} canciones").format(count=len(filepaths))
            card = CoverCard(
                title=name,
                subtitle=count_str,
                cover_path=cover_path,
                filepath=None,
                parent=self.playlists_tab
            )
            def make_handler(n, fps):
                def handler():
                    self.player.navigation_controller.switch_page(3)
                    if hasattr(self.player, 'page_playlists'):
                        self.player.page_playlists._open_playlist(n, fps)
                return handler
            card.clicked.connect(make_handler(name, filepaths))
            self.playlists_flow.addWidget(card)
    def _show_artist_more_menu(self):
        from qfluentwidgets import RoundMenu, Action, FluentIcon as FIF
        from core.language_manager import tr
        from config import ICON_HEART
        menu = RoundMenu(parent=self.player)
        menu.addAction(Action(FIF.ADD, tr("Agregar a la cola"), triggered=self._add_artist_to_queue))
        from settings_manager import settings
        playlists = settings.get('playlists', {})
        if playlists:
            playlist_menu = RoundMenu(tr("Agregar a la playlist"), parent=menu)
            playlist_menu.setIcon(FIF.ALBUM)
            for p_name in playlists.keys():
                playlist_menu.addAction(Action(p_name, triggered=lambda _, p=p_name: self._add_artist_to_playlist(p)))
            menu.addMenu(playlist_menu)
        menu.addAction(Action(ICON_HEART, tr("Agregar a favoritos"), triggered=self._add_artist_to_favorites))
        pos = self.player.btn_more_artist.mapToGlobal(self.player.btn_more_artist.rect().bottomLeft())
        menu.exec(pos)
    def _add_artist_to_queue(self):
        if hasattr(self.player, 'artist_tracks_model') and self.player.artist_tracks_model:
            tracks = list(self.player.artist_tracks_model.tracks)
            if tracks:
                artist_name = self.player.sidebar_artist_title.text()
                msg = tr("Se agregaron {count} canciones de {artist}").format(count=len(tracks), artist=artist_name)
                self.player.queue_controller.add_to_queue(tracks, show_notification=True, custom_notify_text=msg)
    def _add_artist_to_playlist(self, playlist_name):
        if hasattr(self.player, 'artist_tracks_model') and self.player.artist_tracks_model:
            tracks = list(self.player.artist_tracks_model.tracks)
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
                artist_name = self.player.sidebar_artist_title.text()
                notify.success(tr("Añadido a playlist"), tr("Se agregaron {count} canciones de {artist} a {playlist}").format(count=count, artist=artist_name, playlist=playlist_name))
    def _add_artist_to_favorites(self):
        if hasattr(self.player, 'artist_tracks_model') and self.player.artist_tracks_model:
            tracks = list(self.player.artist_tracks_model.tracks)
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
                artist_name = self.player.sidebar_artist_title.text()
                notify.success(tr("Añadido a favoritos"), tr("Se agregaron {count} canciones nuevas de {artist}").format(count=count, artist=artist_name))
    def _play_artist_tracks(self):
        if hasattr(self.player, 'artist_tracks_model') and self.player.artist_tracks_model:
            tracks = list(self.player.artist_tracks_model.tracks)
            if tracks:
                self.player.queue_controller.play_specific_track_global(tracks[0], tracks)
    def _shuffle_artist_tracks(self):
        import random
        if hasattr(self.player, 'artist_tracks_model') and self.player.artist_tracks_model:
            tracks = list(self.player.artist_tracks_model.tracks)
            if tracks:
                random.shuffle(tracks)
                self.player.queue_controller.play_specific_track_global(tracks[0], tracks)
    def populate_discography(self, album_items):
        while self.disco_container_layout.count():
            child = self.disco_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        from UI.dashboard.components.dashboard_cards import CoverCard
        for alb_name, alb_track, count in album_items[:8]:
            card = CoverCard(
                title=alb_name if alb_name else tr("Desconocido"),
                subtitle=tr("Álbum"),
                cover_path=alb_track.cover_path,
                filepath=alb_track.filepath,
                parent=self.disco_inner_widget
            )
            if count == 1:
                card.clicked.connect(lambda name=alb_name, artist=self.player.current_viewing_artist: self.player.queue_controller.play_album_direct(name, artist_name=artist))
            else:
                card.clicked.connect(lambda name=alb_name, artist=self.player.current_viewing_artist: self.player.navigation_controller.open_album_detail(target_album_name=name, target_artist_name=artist))
            self.disco_container_layout.addWidget(card)
        self.disco_container_layout.addStretch()
    def populate_full_discography(self, album_items, ep_items):
        from UI.dashboard.components.dashboard_cards import CoverCard
        while self.albums_flow.count():
            item = self.albums_flow.takeAt(0)
            if item:
                w = item.widget() if hasattr(item, 'widget') else item
                if w: w.deleteLater()
        while self.eps_flow.count():
            item = self.eps_flow.takeAt(0)
            if item:
                w = item.widget() if hasattr(item, 'widget') else item
                if w: w.deleteLater()
        self.lbl_full_albums.setVisible(len(album_items) > 0)
        for alb_name, alb_track, count in album_items:
            card = CoverCard(
                title=alb_name if alb_name else tr("Desconocido"),
                subtitle=str(getattr(alb_track, 'year', '')),
                cover_path=alb_track.cover_path,
                filepath=alb_track.filepath,
                parent=self.albums_tab
            )
            if count == 1:
                card.clicked.connect(lambda name=alb_name, artist=self.player.current_viewing_artist: self.player.queue_controller.play_album_direct(name, artist_name=artist))
            else:
                card.clicked.connect(lambda name=alb_name, artist=self.player.current_viewing_artist: self.player.navigation_controller.open_album_detail(target_album_name=name, target_artist_name=artist))
            self.albums_flow.addWidget(card)
        self.lbl_full_eps.setVisible(len(ep_items) > 0)
        for alb_name, alb_track, count in ep_items:
            card = CoverCard(
                title=alb_name if alb_name else tr("Desconocido"),
                subtitle=str(getattr(alb_track, 'year', '')),
                cover_path=alb_track.cover_path,
                filepath=alb_track.filepath,
                parent=self.albums_tab
            )
            if count == 1:
                card.clicked.connect(lambda name=alb_name, artist=self.player.current_viewing_artist: self.player.queue_controller.play_album_direct(name, artist_name=artist))
            else:
                card.clicked.connect(lambda name=alb_name, artist=self.player.current_viewing_artist: self.player.navigation_controller.open_album_detail(target_album_name=name, target_artist_name=artist))
            self.eps_flow.addWidget(card)
    def populate_recommended_artists(self, artists_list):
        while self.recommended_list_layout.count():
            child = self.recommended_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        if not artists_list:
            lbl = BodyLabel(tr("No hay recomendaciones similares."))
            lbl.setStyleSheet("color: #888888; font-size: 13px;")
            self.recommended_list_layout.addWidget(lbl)
            return
        from UI.library.shared_widgets import ArtistHoverCard, _FakeTrack
        from database import get_artists_info_batch_db
        from utils import normalize_artist_name
        normalized_names = [normalize_artist_name(name) for name in artists_list]
        artists_data = get_artists_info_batch_db(normalized_names)
        for artist_name in artists_list:
            card = ArtistHoverCard(artist_name, self.player)
            norm_name = normalize_artist_name(artist_name)
            artist_data = artists_data.get(norm_name) or {}
            cover_path = artist_data.get('cover_path')
            ft = _FakeTrack(cover_path)
            self.player.image_cache.assign_async_pixmap(card.avatar, ft, 42, 42, fallback_icon=FluentIcon.PEOPLE)
            self.recommended_list_layout.addWidget(card)