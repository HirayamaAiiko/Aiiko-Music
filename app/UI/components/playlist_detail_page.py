import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListView, QAbstractItemView
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QTimer
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QPixmap
from qfluentwidgets import TransparentToolButton, ToolButton, CaptionLabel, BodyLabel, FluentIcon as FIF, Action, RoundMenu
from delegates.list_delegates import SongListDelegate
from view_models.playlist_models import PlaylistTrackModel
from widgets import AspectRatioLabel
from settings_manager import settings
from config import ICON_PLAY, ICON_SHUFFLE, ICON_DELETE
from UI.components.song_table_header import SongTableHeader
from UI.dialogs.playlist_edit_dialog import PlaylistEditDialog
from core.notification_manager import notify
import theme_manager
from core.language_manager import tr
from UI.library.albums.album_detail import DynamicAccentLabel
from UI.components.draggable_track_list import DraggableTrackListView
import uuid
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QImage
from core.image_processing_worker import ImageCacheTask
class PlaylistListView(DraggableTrackListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dragging = False
        self.dragged_indexes = []
        self.setAutoScroll(True)
        self.setAutoScrollMargin(24)
    def startDrag(self, supportedActions):
        self.is_dragging = True
        self.dragged_indexes = [i.row() for i in self.selectedIndexes()]
        self.viewport().update()
        super().startDrag(supportedActions)
        self.is_dragging = False
        self.dragged_indexes = []
        self.viewport().update()
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QSize, Qt
class ElidedTitleLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full_text = text
    def setText(self, text):
        self._full_text = text
        self.setToolTip(f"<span style='font-size: 14px; font-weight: normal; color: white;'>{text}</span>")
        self._elide_text()
    def text(self):
        return self._full_text
    def minimumSizeHint(self):
        metrics = self.fontMetrics()
        return QSize(metrics.horizontalAdvance("..."), metrics.height())
    def sizeHint(self):
        metrics = self.fontMetrics()
        return QSize(metrics.horizontalAdvance(self._full_text), metrics.height())
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._elide_text()
    def _elide_text(self):
        metrics = self.fontMetrics()
        elided = metrics.elidedText(self._full_text, Qt.TextElideMode.ElideRight, self.width())
        if super().text() != elided:
            super().setText(elided)
class GradientHeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._gradient_color = QColor(0, 0, 0, 0)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    def set_dominant_color(self, color: QColor):
        self._gradient_color = color
        self.update()
    def paintEvent(self, event):
        if self._gradient_color.alpha() == 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r, g, b = self._gradient_color.red(), self._gradient_color.green(), self._gradient_color.blue()
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, QColor(r, g, b, 35))
        grad.setColorAt(0.3, QColor(r, g, b, 18))
        grad.setColorAt(0.6, QColor(r, g, b, 5))
        grad.setColorAt(1.0, QColor(r, g, b, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawRoundedRect(self.rect(), 16, 16)
        p.end()
class PlaylistDetailPage(QWidget):
    go_back = pyqtSignal()
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.current_playlist_name = None
        self.current_tracks = []
        self._build_ui()
    def _build_ui(self):
        detail_layout = QVBoxLayout(self)
        detail_layout.setContentsMargins(30, 10, 30, 0)
        self._header_wrapper = QWidget()
        wrapper_layout = QVBoxLayout(self._header_wrapper)
        wrapper_layout.setContentsMargins(5, 0, 5, 0)
        wrapper_layout.setSpacing(5)
        self._header_container = GradientHeaderWidget()
        self._header_container.setFixedHeight(200)
        header_inner_layout = QVBoxLayout(self._header_container)
        header_inner_layout.setContentsMargins(0, 0, 0, 0)
        header_inner_layout.setSpacing(0)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 20, 10, 20)
        self.detail_cover = AspectRatioLabel()
        self.detail_cover.setObjectName("PlaylistDetailCover")
        self.detail_cover.setFixedSize(160, 160)
        self.detail_cover.setStyleSheet("background: #2D2D32; border: 1px solid rgba(255,255,255,0.06);")
        header_layout.addWidget(self.detail_cover)
        header_layout.addSpacing(24)
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        info_layout.setSpacing(4)
        lbl_type = DynamicAccentLabel(tr("PLAYLIST"), "font-size: 13px; font-weight: bold; letter-spacing: 3px; background: transparent;")
        info_layout.addWidget(lbl_type)
        from PyQt6.QtWidgets import QSizePolicy
        self.lbl_current_playlist = ElidedTitleLabel("")
        self.lbl_current_playlist.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.lbl_current_playlist.setStyleSheet("font-size: 36px; font-weight: 800; color: white; background: transparent;")
        info_layout.addWidget(self.lbl_current_playlist)
        self.lbl_playlist_info = BodyLabel(tr("0 canciones"))
        self.lbl_playlist_info.setStyleSheet("color: #AAAAAA; font-size: 14px; background: transparent;")
        info_layout.addWidget(self.lbl_playlist_info)
        info_layout.addSpacing(16)
        self.actions_container = QWidget()
        actions_layout = QHBoxLayout(self.actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(12)
        from qfluentwidgets import PrimaryPushButton, PushButton
        self.btn_play_all = PrimaryPushButton(self.player.playback_ui_controller._get_icon("play.svg", ICON_PLAY, "#000000"), f" {tr('Reproducir')}")
        self.btn_play_all.setFixedSize(140, 40)
        self.btn_play_all.clicked.connect(self._play_all)
        actions_layout.addWidget(self.btn_play_all)
        self.btn_shuffle = PushButton(self.player.playback_ui_controller._get_icon("shuffle.svg", ICON_SHUFFLE), f" {tr('Aleatorio')}")
        self.btn_shuffle.setFixedSize(120, 40)
        self.btn_shuffle.clicked.connect(self._play_shuffle)
        actions_layout.addWidget(self.btn_shuffle)
        self.btn_shuffle_icon = ToolButton(self.player.playback_ui_controller._get_icon("shuffle.svg", ICON_SHUFFLE))
        self.btn_shuffle_icon.setFixedSize(40, 40)
        self.btn_shuffle_icon.setToolTip(tr("Aleatorio"))
        self.btn_shuffle_icon.clicked.connect(self._play_shuffle)
        self.btn_shuffle_icon.hide()
        actions_layout.addWidget(self.btn_shuffle_icon)
        self.btn_edit_pl = ToolButton(FIF.EDIT)
        self.btn_edit_pl.setFixedSize(40, 40)
        self.btn_edit_pl.clicked.connect(self._rename_playlist)
        self.btn_edit_pl.setToolTip(tr("Editar Playlist"))
        actions_layout.addWidget(self.btn_edit_pl)
        self.btn_del_pl = ToolButton(ICON_DELETE)
        self.btn_del_pl.setFixedSize(40, 40)
        self.btn_del_pl.clicked.connect(self._delete_current_playlist)
        self.btn_del_pl.setToolTip(tr("Eliminar Playlist"))
        actions_layout.addWidget(self.btn_del_pl)
        actions_layout.addStretch()
        info_layout.addWidget(self.actions_container)
        header_layout.addLayout(info_layout, 1)
        from qfluentwidgets import SearchLineEdit
        self.search_bar = SearchLineEdit()
        from PyQt6.QtCore import QSize
        self.search_bar.searchButton.setIconSize(QSize(14, 14))
        self.search_bar.clearButton.setIconSize(QSize(14, 14))
        self.search_bar.setPlaceholderText(tr("Buscar en la playlist..."))
        self.search_bar.setFixedSize(250, 40)
        self.search_bar.textChanged.connect(self._filter_tracks)
        self.btn_search_icon = ToolButton(FIF.SEARCH)
        self.btn_search_icon.setFixedSize(40, 40)
        self.btn_search_icon.setToolTip(tr("Buscar en la playlist"))
        self.btn_search_icon.hide()
        self.btn_search_icon.clicked.connect(self._on_search_icon_clicked)
        header_layout.addWidget(self.btn_search_icon, 0, Qt.AlignmentFlag.AlignBottom)
        header_layout.addWidget(self.search_bar, 0, Qt.AlignmentFlag.AlignBottom)
        header_inner_layout.addLayout(header_layout)
        self.search_bar.installEventFilter(self)
        wrapper_layout.addWidget(self._header_container)
        detail_layout.addWidget(self._header_wrapper)
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        self.table_header = SongTableHeader()
        table_layout.addWidget(self.table_header)
        self._track_model = PlaylistTrackModel(self.player)
        self._track_model.tracks_reordered.connect(self._on_tracks_reordered)
        self.list_playlist_tracks = PlaylistListView()
        self.table_header.list_view = self.list_playlist_tracks
        self.list_playlist_tracks.setObjectName("PlaylistTracksList")
        self.list_playlist_tracks.setModel(self._track_model)
        self.list_playlist_tracks.setItemDelegate(SongListDelegate(self.list_playlist_tracks, player=self.player, is_table_view=True))
        self.list_playlist_tracks.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_playlist_tracks.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list_playlist_tracks.setStyleSheet("QListView { background: transparent; border: none; outline: none; }")
        self.list_playlist_tracks.setUniformItemSizes(True)
        self.list_playlist_tracks.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_playlist_tracks.setDragEnabled(True)
        self.list_playlist_tracks.setAcceptDrops(True)
        self.list_playlist_tracks.setDropIndicatorShown(True)
        self.list_playlist_tracks.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.player.apply_smooth_scroll(self.list_playlist_tracks)
        from core.selection_tracker import SelectionTracker
        self.list_playlist_tracks._selection_tracker = SelectionTracker(self.list_playlist_tracks)
        self.list_playlist_tracks.doubleClicked.connect(self._on_item_double_clicked)
        self.list_playlist_tracks.customContextMenuRequested.connect(self._show_track_context_menu)
        table_layout.addWidget(self.list_playlist_tracks)
        detail_layout.addWidget(table_container, stretch=1)
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        self._header_animation = QPropertyAnimation(self._header_wrapper, b"maximumHeight")
        self._header_animation.setDuration(250)
        self._header_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._header_collapsed = False
        self._header_full_height = 260
        self._header_wrapper.setMaximumHeight(self._header_full_height)
        self.list_playlist_tracks.viewport().installEventFilter(self)
        self.list_playlist_tracks.installEventFilter(self)
        self._cache_update_timer = QTimer(self)
        self._cache_update_timer.setSingleShot(True)
        self._cache_update_timer.setInterval(150)
        self._cache_update_timer.timeout.connect(self._do_update_cover)
        self.player.image_cache.cache_updated.connect(self._on_cache_updated)
        from UI.components.scroll_to_top import ScrollToTopButton
        from UI.components.locate_track_button import LocateTrackButton
        self.btn_scroll_top = ScrollToTopButton(self.list_playlist_tracks, self)
        self.btn_locate_track = LocateTrackButton(self.player, self.list_playlist_tracks, self)
        self.btn_locate_track.set_model(self._track_model)
    def _on_search_icon_clicked(self):
        self.btn_search_icon.hide()
        self.search_bar.show()
        self.search_bar.setFocus()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_floating_positions()
        self._update_responsive_layout()
    def _update_responsive_layout(self):
        w = self.width()
        if w <= 850:
            self.btn_del_pl.hide()
            self.btn_edit_pl.hide()
        elif w <= 930:
            self.btn_del_pl.hide()
            self.btn_edit_pl.show()
        else:
            self.btn_del_pl.show()
            self.btn_edit_pl.show()
        if w <= 850:
            self.btn_shuffle.hide()
            self.btn_shuffle_icon.show()
        else:
            self.btn_shuffle.show()
            self.btn_shuffle_icon.hide()
        is_compact_search = w <= 650
        self.actions_container.show()
        if is_compact_search:
            if not self.search_bar.text() and not self.search_bar.hasFocus():
                self.search_bar.hide()
                self.btn_search_icon.show()
            else:
                self.btn_search_icon.hide()
                self.search_bar.show()
        else:
            self.search_bar.show()
            self.btn_search_icon.hide()
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
    def _on_cache_updated(self):
        if self.isVisible() and not self._cache_update_timer.isActive():
            self._cache_update_timer.start()
    def _do_update_cover(self):
        if self.isVisible():
            self._update_detail_cover()
    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj == self.search_bar and event.type() == QEvent.Type.FocusOut:
            self._update_responsive_layout()
        if obj in (self.list_playlist_tracks, self.list_playlist_tracks.viewport()):
            if event.type() == QEvent.Type.Wheel:
                angle = event.angleDelta().y()
                from PyQt6.QtCore import QPropertyAnimation
                is_animating = (self._header_animation.state() == QPropertyAnimation.State.Running)
                if angle < 0:              
                    needs_scroll = self.list_playlist_tracks.verticalScrollBar().maximum() > 0
                    if (not self._header_collapsed and needs_scroll) or is_animating:
                        self._trigger_collapse(True)
                        return True                                     
                elif angle > 0:               
                    if self._header_collapsed and self.list_playlist_tracks.verticalScrollBar().value() == 0:
                        self._trigger_collapse(False)
                        return True                                     
                    if is_animating:
                        return True
        return super().eventFilter(obj, event)
    def _trigger_collapse(self, collapse):
        from PyQt6.QtCore import QPropertyAnimation
        if collapse:
            if not self._header_collapsed and self._header_animation.state() != QPropertyAnimation.State.Running:
                self._header_collapsed = True
                self._header_animation.setStartValue(self._header_wrapper.height())
                self._header_animation.setEndValue(0)
                self._header_animation.start()
        else:
            if self._header_collapsed and self._header_animation.state() != QPropertyAnimation.State.Running:
                self._header_collapsed = False
                self._header_animation.setStartValue(0)
                self._header_animation.setEndValue(self._header_full_height)
                self._header_animation.start()
    def clear(self):
        self.current_playlist_name = None
        self.lbl_current_playlist.setText("")
        self.lbl_playlist_info.setText(tr("0 canciones"))
        self.detail_cover.clear()
        self._track_model.set_tracks([])
        self.current_tracks = []
    def load_details(self, name, filepaths):
        self.current_playlist_name = name
        self.lbl_current_playlist.setText(name)
        tracks = [t for fp in filepaths for t in self.player.library if t.filepath == fp]
        self.current_tracks = tracks
        import math
        total_ms = sum(t.duration for t in tracks if hasattr(t, 'duration') and t.duration)
        total_seconds = total_ms / 1000.0
        if total_seconds > 0:
            mins = math.floor(total_seconds / 60)
            if mins >= 60:
                hours = mins // 60
                mins = mins % 60
                duration_str = tr(" • {hours} h {mins} min").format(hours=hours, mins=mins)
            else:
                duration_str = tr(" • {mins} min").format(mins=mins)
        else:
            duration_str = ""
        self.lbl_playlist_info.setText(tr("{count} canciones{duration}").format(count=len(tracks), duration=duration_str))
        self._track_model.set_tracks(tracks)
        self.search_bar.clear()
        self._update_detail_cover()
    def _filter_tracks(self, text):
        if not text:
            self._track_model.set_tracks(self.current_tracks)
        else:
            text = text.lower()
            filtered = [
                t for t in self.current_tracks 
                if text in getattr(t, 'title', '').lower() 
                or text in getattr(t, 'artist', '').lower() 
                or text in getattr(t, 'album', '').lower()
            ]
            self._track_model.set_tracks(filtered)
    def _on_tracks_reordered(self):
        if not self.current_playlist_name:
            return
        new_tracks = self._track_model.tracks()
        self.current_tracks = list(new_tracks)
        new_filepaths = [t.filepath for t in new_tracks if hasattr(t, 'filepath')]
        playlists = settings.get('playlists', {})
        if self.current_playlist_name in playlists:
            playlists[self.current_playlist_name] = new_filepaths
            settings.set('playlists', playlists)
            settings.save()
            self._update_detail_cover()
            self.player.library_controller.refresh_playlists_list()
            self.player.library_controller.refresh_artist_related_playlists()
    def _update_detail_cover(self):
        if not self.current_playlist_name: return
        covers_cfg = settings.get('playlist_covers', {})
        custom = covers_cfg.get(self.current_playlist_name)
        if custom and os.path.exists(custom):
            pix = self.player.image_cache.get_cached_pixmap(custom, 160, radius=0)
            self.detail_cover.setPixmap(pix)
            self._apply_cover_gradient(pix)
        else:
            fps = settings.get('playlists', {}).get(self.current_playlist_name, [])
            covers = []
            seen_covers = set()
            for fp in reversed(fps):
                track = next((t for t in self.player.library if t.filepath == fp), None)
                if track and hasattr(track, 'cover_path') and track.cover_path and os.path.exists(track.cover_path):
                    if track.cover_path not in seen_covers:
                        seen_covers.add(track.cover_path)
                        covers.append(track.cover_path)
                    if len(covers) == 4: break
            pix = QPixmap(160, 160)
            pix.fill(QColor(45, 45, 50))
            if covers:
                p = QPainter(pix)
                if len(covers) == 1:
                    cpix = self.player.image_cache.get_cached_pixmap(covers[0], 160, radius=0)
                    p.drawPixmap(0, 0, 160, 160, cpix)
                else:
                    half = 79
                    gap = 2
                    positions = [(0, 0), (half + gap, 0), (0, half + gap), (half + gap, half + gap)]
                    for i, cpath in enumerate(covers):
                        cpix = self.player.image_cache.get_cached_pixmap(cpath, half, radius=0)
                        p.drawPixmap(positions[i][0], positions[i][1], half, half, cpix)
                p.end()
                self.detail_cover.setPixmap(pix)
                self._apply_cover_gradient(pix)
            else:
                svg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "resources", "app", "logo_full.svg")
                if os.path.exists(svg_path):
                    from PyQt6.QtSvg import QSvgRenderer
                    pix.fill(Qt.GlobalColor.transparent)
                    p = QPainter(pix)
                    p.setRenderHint(QPainter.RenderHint.Antialiasing)
                    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                    renderer = QSvgRenderer(svg_path)
                    renderer.render(p)
                    p.end()
                self.detail_cover.setPixmap(pix)
                self._header_container.set_dominant_color(QColor(0,0,0,0))
    def _apply_cover_gradient(self, pixmap: QPixmap):
        img = pixmap.toImage().scaled(1, 1, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        if not img.isNull():
            color = img.pixelColor(0, 0)
            self._header_container.set_dominant_color(color)
        else:
            self._header_container.set_dominant_color(QColor(0,0,0,0))
    def _on_item_double_clicked(self, index):
        track = index.data(Qt.ItemDataRole.UserRole)
        if track:
            self.player.queue_controller.play_specific_track_global(track, self.current_tracks)
    def _show_track_context_menu(self, pos):
        index = self.list_playlist_tracks.indexAt(pos)
        if not index.isValid(): return
        track = index.data(Qt.ItemDataRole.UserRole)
        if not track: return
        global_pos = self.list_playlist_tracks.viewport().mapToGlobal(pos)
        selected_tracks = []
        if hasattr(self.list_playlist_tracks, '_selection_tracker'):
            selected_tracks = self.list_playlist_tracks._selection_tracker.get_selected_tracks()
        if track not in selected_tracks:
            selected_tracks = [track]
        menu = RoundMenu(parent=self.player)
        self.player.context_menu_manager._populate_common_actions(menu, selected_tracks, self.current_tracks)
        if self.current_playlist_name:
            menu.addSeparator()
            menu.addAction(Action(ICON_DELETE, tr("Quitar de esta Playlist"), triggered=lambda: self._remove_tracks_from_playlist(selected_tracks)))
        menu.exec(global_pos)
    def _remove_tracks_from_playlist(self, selected_tracks):
        if not self.current_playlist_name: return
        playlists = settings.get('playlists', {})
        if self.current_playlist_name in playlists:
            current_fps = playlists[self.current_playlist_name]
            removed = False
            for t in selected_tracks:
                if t.filepath in current_fps:
                    current_fps.remove(t.filepath)
                    removed = True
            if removed:
                settings.set('playlists', playlists)
                settings.save()
                self._update_detail_cover()
                self.load_details(self.current_playlist_name, current_fps)
                self.player.library_controller.refresh_playlists_list()
                self.player.library_controller.refresh_artist_related_playlists()
    def _play_all(self):
        if not self.current_tracks: return
        self.player.queue_controller.play_specific_track_global(self.current_tracks[0], self.current_tracks)
    def _play_shuffle(self):
        if not self.current_tracks: return
        import random
        shuffled = list(self.current_tracks)
        random.shuffle(shuffled)
        self.player.queue_controller.play_specific_track_global(shuffled[0], shuffled)
    def _rename_playlist(self):
        if not self.current_playlist_name: return
        dlg = PlaylistEditDialog(self.current_playlist_name, self.player, parent=self.player)
        if dlg.exec():
            new_name = dlg.get_name()
            new_cover_path = dlg.get_cover_path()
            playlists = settings.get('playlists', {})
            covers = settings.get('playlist_covers', {})
            if new_name != self.current_playlist_name:
                if new_name in playlists:
                    notify.warning(tr("Error"), tr("Ya existe una playlist con ese nombre."))
                    return
                playlists[new_name] = playlists.pop(self.current_playlist_name)
                if self.current_playlist_name in covers:
                    covers[new_name] = covers.pop(self.current_playlist_name)
                settings.set('playlists', playlists)
            self.current_playlist_name = new_name
            self.lbl_current_playlist.setText(new_name)
            if new_cover_path or (new_cover_path is None and dlg.cover_reset):
                from config import CACHE_DIR
                playlists_cache_dir = os.path.join(CACHE_DIR, "playlists")
                old_cover = covers.get(new_name)
                self._cover_task = ImageCacheTask(new_name, new_cover_path, playlists_cache_dir, old_cover, max_size=800, parent=self)
                self._cover_task.finished_processing.connect(self._on_cover_processed)
                self._cover_task.start()
            else:
                settings.set('playlist_covers', covers)
                settings.save()
                self._update_detail_cover()
                self.player.library_controller.refresh_playlists_list()
                self.player.library_controller.refresh_artist_related_playlists()
    def _on_cover_processed(self, playlist_name, new_path, old_path):
        covers = settings.get('playlist_covers', {})
        if new_path:
            covers[playlist_name] = new_path
        elif old_path:                                                         
            covers.pop(playlist_name, None)
        settings.set('playlist_covers', covers)
        settings.save()
        if self.current_playlist_name == playlist_name:
            self._update_detail_cover()
        self.player.library_controller.refresh_playlists_list()
        self.player.library_controller.refresh_artist_related_playlists()
    def _delete_current_playlist(self):
        if not self.current_playlist_name: return
        if notify.confirm(tr('Confirmar'), tr('¿Eliminar la playlist "{name}"?').format(name=self.current_playlist_name)):
            playlists = settings.get('playlists', {})
            if self.current_playlist_name in playlists:
                del playlists[self.current_playlist_name]
                settings.set('playlists', playlists)
                covers = settings.get('playlist_covers', {})
                if self.current_playlist_name in covers:
                    old_cover = covers[self.current_playlist_name]
                    del covers[self.current_playlist_name]
                    settings.set('playlist_covers', covers)
                    from config import CACHE_DIR
                    playlists_cache_dir = os.path.join(CACHE_DIR, "playlists")
                    self._del_task = ImageCacheTask(self.current_playlist_name, None, playlists_cache_dir, old_cover, max_size=800, parent=self)
                    self._del_task.start()
                settings.save()
                self.current_playlist_name = None
                self.go_back.emit()
                self.player.library_controller.refresh_playlists_list()
                self.player.library_controller.refresh_artist_related_playlists()