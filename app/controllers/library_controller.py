import os
import logging
from PyQt6.QtCore import QObject, Qt, QSize, QTimer
from PyQt6.QtWidgets import QListView, QAbstractItemView, QDialog
from qfluentwidgets import RoundMenu, Action, FluentIcon as FIF
from database import get_all_artists_info_db
from workers import ArtistInfoFetcherThread
from settings_manager import settings
from core.notification_manager import notify
from widgets import ResponsiveGridHelper
from utils import sanitize_text, get_artists_from_string, normalize_artist_name
from core.language_manager import tr
class LibraryController(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
    def filter_library(self, text):
        self.mw._search_query = text.lower()
        if hasattr(self.mw, 'search_timer'):
            self.mw.search_timer.start(250)
        else:
            self.apply_filter()
    def update_library_count(self):
        if not hasattr(self.mw, 'pivot') or not hasattr(self.mw.pivot, 'lbl_count'): return
        tab = getattr(self.mw, 'current_lib_tab', 'songs')
        if tab == 'songs' and hasattr(self.mw, 'proxy_model'):
            count = self.mw.proxy_model.rowCount()
            text = f"{count} {tr('canciones')}"
        elif tab == 'albums' and hasattr(self.mw, 'album_proxy'):
            count = self.mw.album_proxy.rowCount()
            text = f"{count} {tr('álbumes')}"
        elif tab == 'artists' and hasattr(self.mw, 'artist_proxy'):
            count = self.mw.artist_proxy.rowCount()
            text = f"{count} {tr('artistas')}"
        elif tab == 'folders' and hasattr(self.mw, 'page_library') and hasattr(self.mw.page_library, 'folders_tab') and hasattr(self.mw.page_library.folders_tab, 'folders_list'):
            count = self.mw.page_library.folders_tab.folders_list.count()
            text = f"{count} {tr('carpetas')}"
        else:
            text = "0 items"
        self.mw.pivot.lbl_count.setText(text)
    def apply_filter(self):
        query = getattr(self.mw, '_search_query', "")
        if not hasattr(self.mw, 'proxy_model'):
            return
        self.mw.proxy_model.setFilterRegularExpression(query)
        if hasattr(self.mw, 'album_proxy'):
            self.mw.album_proxy.setFilterRegularExpression(query)
        if hasattr(self.mw, 'artist_proxy'):
            self.mw.artist_proxy.setFilterRegularExpression(query)
        if hasattr(self.mw, 'page_library') and hasattr(self.mw.page_library, 'folders_tab') and not getattr(self.mw.page_library.folders_tab, 'is_placeholder', False):
            self.mw.page_library.folders_tab.local_proxy_model.setFilterRegularExpression(query)
            self.mw.page_library.folders_tab.filter_folders(query)
        if hasattr(self.mw, 'album_grid_helper'): self.mw.album_grid_helper.force_recalculate()
        if hasattr(self.mw, 'artist_grid_helper'): self.mw.artist_grid_helper.force_recalculate()
        self.update_library_count()
        if not getattr(self.mw, '_initial_scroll_restored', False):
            self.mw._initial_scroll_restored = True
            saved_pos = settings.get('scroll_positions', {})
            def restore():
                if 'songs' in saved_pos and hasattr(self.mw, 'list_songs'):
                    self.mw.list_songs.verticalScrollBar().setValue(saved_pos['songs'])
            QTimer.singleShot(50, restore)
    def sort_current_tab(self, index):
        tab = getattr(self.mw, 'current_lib_tab', 'songs')
        sort_configs = settings.get('sort_configs', {})
        sort_configs[tab] = index
        settings.set('sort_configs', sort_configs)
        if tab == 'songs':
            self.sort_tracks_model(index)
        elif tab == 'albums':
            self.sort_albums_model(index)
        elif tab == 'artists':
            self.sort_artists_model(index)
        elif tab == 'folders':
            self.sort_folders_model(index)
    def sort_folders_model(self, index):
        mw = self.mw
        if hasattr(mw, 'page_library') and hasattr(mw.page_library, 'folders_tab') and not getattr(mw.page_library.folders_tab, 'is_placeholder', False):
            from settings_manager import settings
            ftab = mw.page_library.folders_tab
            tracks = list(ftab.local_track_model.tracks)
            if index == 0: tracks.sort(key=lambda t: t.title.lower())
            elif index == 1: tracks.sort(key=lambda t: t.title.lower(), reverse=True)
            elif index == 2: tracks.sort(key=lambda t: t.artist.lower() + t.title.lower())
            elif index == 3: tracks.sort(key=lambda t: t.album.lower() + t.title.lower())
            elif index == 4: tracks.sort(key=lambda t: str(getattr(t, 'year', '')) + t.title.lower(), reverse=True)
            elif index == 5: tracks.sort(key=lambda t: getattr(t, 'mtime', 0), reverse=True)
            elif index == 6: tracks.sort(key=lambda t: getattr(t, 'ctime', 0), reverse=True)
            elif index == 7: tracks.sort(key=lambda t: getattr(t, 'ctime', 0))
            elif index == 8: 
                fav_set = set(settings.get('favorites', []))
                tracks.sort(key=lambda t: (0 if t.filepath in fav_set else 1, t.title.lower()))
            elif index == 9: tracks.sort(key=lambda t: getattr(t, 'duration', 0), reverse=True)
            elif index == 10: tracks.sort(key=lambda t: getattr(t, 'duration', 0))
            ftab.local_track_model.layoutAboutToBeChanged.emit()
            ftab.local_track_model.set_tracks(tracks)
            ftab.local_track_model.layoutChanged.emit()
    def sort_tracks_model(self, index):
        mw = self.mw
        mw.track_model.layoutAboutToBeChanged.emit()
        if index == 0: mw.library.sort(key=lambda t: t.title.lower())
        elif index == 1: mw.library.sort(key=lambda t: t.title.lower(), reverse=True)
        elif index == 2: mw.library.sort(key=lambda t: t.artist.lower() + t.title.lower())
        elif index == 3: mw.library.sort(key=lambda t: t.album.lower() + t.title.lower())
        elif index == 4: mw.library.sort(key=lambda t: str(getattr(t, 'year', '')) + t.title.lower(), reverse=True)
        elif index == 5: mw.library.sort(key=lambda t: getattr(t, 'mtime', 0), reverse=True)
        elif index == 6: mw.library.sort(key=lambda t: getattr(t, 'ctime', 0), reverse=True)
        elif index == 7: mw.library.sort(key=lambda t: getattr(t, 'ctime', 0))
        elif index == 8: 
            fav_set = set(settings.get('favorites', []))
            mw.library.sort(key=lambda t: (0 if t.filepath in fav_set else 1, t.title.lower()))
        elif index == 9: mw.library.sort(key=lambda t: getattr(t, 'duration', 0), reverse=True)
        elif index == 10: mw.library.sort(key=lambda t: getattr(t, 'duration', 0))
        elif index == 11: mw.library.sort(key=lambda t: getattr(t, 'replaygain_track', 0.0))
        mw.track_model.layoutChanged.emit()
        mw.track_model.set_tracks(list(mw.library))
    def sort_albums_model(self, index):
        mw = self.mw
        if not hasattr(mw, 'album_model'): return
        mw.album_model.layoutAboutToBeChanged.emit()
        if index == 1: mw.album_model.items.sort(key=lambda x: x[0].lower(), reverse=True)
        elif index == 6: mw.album_model.items.sort(key=lambda x: getattr(x[1], 'ctime', 0), reverse=True)
        elif index == 7: mw.album_model.items.sort(key=lambda x: getattr(x[1], 'ctime', 0))
        else: mw.album_model.items.sort(key=lambda x: x[0].lower())
        mw.album_model.layoutChanged.emit()
    def sort_artists_model(self, index):
        mw = self.mw
        if not hasattr(mw, 'artist_model'): return
        mw.artist_model.layoutAboutToBeChanged.emit()
        if index == 1: mw.artist_model.items.sort(key=lambda x: x[0].lower(), reverse=True)
        elif index == 6: mw.artist_model.items.sort(key=lambda x: getattr(x[1], 'ctime', 0), reverse=True)
        elif index == 7: mw.artist_model.items.sort(key=lambda x: getattr(x[1], 'ctime', 0))
        else: mw.artist_model.items.sort(key=lambda x: x[0].lower())
        mw.artist_model.layoutChanged.emit()
    def locate_in_library(self, track):
        mw = self.mw
        mw.navigation_controller.switch_page(1)
        mw.pivot.setCurrentItem('songs')
        for row in range(mw.proxy_model.rowCount()):
            idx = mw.proxy_model.index(row, 0)
            if idx.data(Qt.ItemDataRole.UserRole) == track:
                mw.list_songs.setCurrentIndex(idx)
                mw.list_songs.scrollTo(idx, QAbstractItemView.ScrollHint.PositionAtCenter)
                break
    def delete_selected_queue_items(self):
        mw = self.mw
        selected_indexes = mw.list_queue_ui.selectionModel().selectedIndexes()
        if not selected_indexes:
            if notify.confirm('Limpiar Cola', '¿Vaciar toda la cola de reproducción?'):
                mw.queue_controller.clear_queue()
            return
        rows = sorted([idx.row() for idx in selected_indexes], reverse=True)
        for row in rows:
            if row != mw.queue.current_index:
                mw.queue.tracks.pop(row)
                if row < mw.queue.current_index:
                    mw.queue.current_index -= 1
        mw.queue_controller.refresh_queue_ui()
    def toggle_current_tab_view(self):
        from config import ICON_LIST, ICON_GRID
        from PyQt6.QtWidgets import QListView
        from PyQt6.QtCore import QSize
        from settings_manager import settings
        mw = self.mw
        if not hasattr(mw, 'pivot'): return
        current_tab = mw.pivot.currentRouteKey()
        mw.image_cache.pending_icons.clear()
        if current_tab == 'songs':
            from delegates.grid_delegates import SongGridDelegate
            if hasattr(mw, 'track_model') and mw.track_model is not None:
                mw.track_model.layoutAboutToBeChanged.emit()
            mw.songs_is_grid = not mw.songs_is_grid
            settings.set('songs_is_grid', mw.songs_is_grid)
            if hasattr(mw, 'track_model') and mw.track_model is not None:
                mw.track_model.is_grid = mw.songs_is_grid
            if hasattr(mw, 'btn_view_mode'):
                mw.btn_view_mode.setIcon(mw.playback_ui_controller._get_icon("list.svg" if mw.songs_is_grid else "grid.svg", ICON_LIST if mw.songs_is_grid else ICON_GRID))
            if not hasattr(mw, 'list_songs'): return
            if mw.songs_is_grid:
                if not getattr(mw.page_library, 'is_placeholder', False) and hasattr(mw.page_library, 'songs_tab') and hasattr(mw.page_library.songs_tab, 'table_header'):
                    mw.page_library.songs_tab.table_header.hide()
                mw.list_songs.setViewMode(QListView.ViewMode.IconMode)
                mw.list_songs.setResizeMode(QListView.ResizeMode.Adjust)
                mw.list_songs.setIconSize(QSize(160, 160))
                mw.list_songs.setGridSize(QSize(190, 265))
                mw.list_songs.setUniformItemSizes(True)
                mw.list_songs.setSpacing(15)
                mw.btn_view_mode.setIcon(mw.playback_ui_controller._get_icon("list.svg", ICON_LIST))
                if not hasattr(mw, 'song_grid_delegate'):
                    mw.song_grid_delegate = SongGridDelegate(mw.list_songs)
                mw.list_songs.setItemDelegate(mw.song_grid_delegate)
                if not hasattr(mw, 'songs_grid_helper'):
                    from widgets import ResponsiveGridHelper
                    mw.songs_grid_helper = ResponsiveGridHelper(mw.list_songs, parent=mw)
                else:
                    mw.songs_grid_helper.force_recalculate()
            else:
                if not getattr(mw.page_library, 'is_placeholder', False) and hasattr(mw.page_library, 'songs_tab') and hasattr(mw.page_library.songs_tab, 'table_header'):
                    mw.page_library.songs_tab.table_header.show()
                mw.list_songs.setViewMode(QListView.ViewMode.ListMode)
                mw.list_songs.setIconSize(QSize(50, 50))
                mw.list_songs.setGridSize(QSize())
                mw.list_songs.setSpacing(0)
                mw.list_songs.setViewportMargins(0, 5, 0, 0)
                mw.btn_view_mode.setIcon(mw.playback_ui_controller._get_icon("grid.svg", ICON_GRID))
                if not hasattr(mw, 'song_list_delegate'):
                    from delegates.list_delegates import SongListDelegate
                    mw.song_list_delegate = SongListDelegate(mw.list_songs, mw, is_artist_view=False, is_table_view=True, show_cover_in_table=True)
                else:
                    mw.song_list_delegate.is_table_view = True
                    mw.song_list_delegate.show_cover_in_table = True
                mw.list_songs.setItemDelegate(mw.song_list_delegate)
            mw.track_model.layoutChanged.emit()
        elif current_tab == 'albums':
            mw.albums_is_grid = not mw.albums_is_grid
            settings.set('albums_is_grid', mw.albums_is_grid)
            if hasattr(mw, 'btn_view_mode'):
                mw.btn_view_mode.setIcon(mw.playback_ui_controller._get_icon("list.svg" if mw.albums_is_grid else "grid.svg", ICON_LIST if mw.albums_is_grid else ICON_GRID))
            if hasattr(mw, 'page_library') and hasattr(mw.page_library, 'albums_tab') and hasattr(mw.page_library.albums_tab, 'grid_tab'):
                mw.page_library.albums_tab.grid_tab.set_view_mode(mw.albums_is_grid)
                if hasattr(mw.page_library.albums_tab, 'table_header'):
                    mw.page_library.albums_tab.table_header.setVisible(not mw.albums_is_grid)
        elif current_tab == 'artists':
            mw.artists_is_grid = not mw.artists_is_grid
            settings.set('artists_is_grid', mw.artists_is_grid)
            if hasattr(mw, 'btn_view_mode'):
                mw.btn_view_mode.setIcon(mw.playback_ui_controller._get_icon("list.svg" if mw.artists_is_grid else "grid.svg", ICON_LIST if mw.artists_is_grid else ICON_GRID))
            if hasattr(mw, 'page_library') and hasattr(mw.page_library, 'artists_tab') and hasattr(mw.page_library.artists_tab, 'grid_tab'):
                mw.page_library.artists_tab.grid_tab.set_view_mode(mw.artists_is_grid)
        elif current_tab == 'folders':
            mw.folders_is_grid = not getattr(mw, 'folders_is_grid', False)
            settings.set('folders_is_grid', mw.folders_is_grid)
            if hasattr(mw, 'btn_view_mode'):
                mw.btn_view_mode.setIcon(mw.playback_ui_controller._get_icon("list.svg" if mw.folders_is_grid else "grid.svg", ICON_LIST if mw.folders_is_grid else ICON_GRID))
            if hasattr(mw, 'page_library') and hasattr(mw.page_library, 'folders_tab') and not getattr(mw.page_library.folders_tab, 'is_placeholder', False):
                mw.page_library.folders_tab.set_view_mode(mw.folders_is_grid)
    def refresh_library_views(self, only_songs=False, skip_dashboard=False):
        mw = self.mw
        mw.image_cache.pending_icons.clear()
        mw.track_model.set_tracks(list(mw.library))
        if only_songs: return
        if hasattr(mw, '_library_parser_worker') and mw._library_parser_worker:
            try: mw._library_parser_worker.result_ready.disconnect()
            except TypeError: pass
            old_worker = mw._library_parser_worker
            if old_worker.isRunning():
                if not hasattr(mw, '_orphaned_workers'):
                    mw._orphaned_workers = []
                mw._orphaned_workers.append(old_worker)
                def _cleanup(w=old_worker):
                    w.deleteLater()
                    if hasattr(mw, '_orphaned_workers') and w in mw._orphaned_workers:
                        mw._orphaned_workers.remove(w)
                old_worker.finished.connect(_cleanup)
            else:
                old_worker.deleteLater()
        from workers import LibraryParserWorker
        merge_albums = settings.get('merge_collaborative_albums', True)
        mw._library_parser_worker = LibraryParserWorker(list(mw.library), merge_albums=merge_albums, parent=mw)
        mw._library_parser_worker.result_ready.connect(lambda a, ar: self._apply_library_data(a, ar, skip_dashboard))
        mw._library_parser_worker.start()
    def _apply_library_data(self, album_items, artist_items, skip_dashboard=False):
        mw = self.mw
        mw.album_model.set_items(album_items)
        mw.artist_model.set_items(artist_items)
        if hasattr(mw, 'album_proxy'): mw.album_proxy.invalidate()
        if hasattr(mw, 'artist_proxy'): mw.artist_proxy.invalidate()
        if hasattr(mw, 'page_library') and hasattr(mw.page_library, 'folders_tab') and not getattr(mw.page_library.folders_tab, 'is_placeholder', False):
            mw.page_library.folders_tab.refresh()
        search_text = mw.search_bar.text() if hasattr(mw, 'search_bar') else ""
        mw.library_controller.filter_library(search_text)
        sort_configs = settings.get('sort_configs', {'songs':0, 'albums':0, 'artists':0})
        if hasattr(mw, 'sort_combo'):
            self.sort_tracks_model(sort_configs.get('songs', 0))
            self.sort_albums_model(sort_configs.get('albums', 0))
            self.sort_artists_model(sort_configs.get('artists', 0))
        self.update_library_count()
        self.refresh_playlists_list()
        if hasattr(mw, 'page_dashboard') and not skip_dashboard:
            mw.page_dashboard.refresh(force=True)
        if hasattr(mw, 'stacked_lib'):
            current = mw.stacked_lib.currentWidget()
            if current:
                if hasattr(mw, 'artist_detail_widget') and current == mw.artist_detail_widget:
                    if hasattr(mw, 'current_viewing_artist') and mw.current_viewing_artist:
                        from workers import ArtistDataWorker
                        if hasattr(mw, '_artist_data_worker') and mw._artist_data_worker:
                            try: mw._artist_data_worker.result_ready.disconnect()
                            except TypeError: pass
                            old = mw._artist_data_worker
                            if old.isRunning():
                                if not hasattr(mw, '_orphaned_workers'): mw._orphaned_workers = []
                                mw._orphaned_workers.append(old)
                                old.finished.connect(lambda w=old: (w.deleteLater(), mw._orphaned_workers.remove(w) if w in mw._orphaned_workers else None))
                            else:
                                old.deleteLater()
                        mw._artist_data_worker = ArtistDataWorker(mw.current_viewing_artist, mw.library)
                        mw._artist_data_worker.result_ready.connect(mw.navigation_controller._apply_artist_data)
                        mw._artist_data_worker.start()
                elif hasattr(mw, 'album_detail_widget') and current == mw.album_detail_widget:
                    if hasattr(mw, 'sidebar_title') and hasattr(mw, 'sidebar_artist'):
                        album_name = mw.sidebar_title.text()
                        artist_name = mw.sidebar_artist.text()
                        if album_name:
                            mw.navigation_controller.open_album_detail(target_album_name=album_name, target_artist_name=artist_name)
    def on_artist_info_fetched(self, artist_name, local_path, bio):
        mw = self.mw
        if bio or local_path:
            if local_path and os.path.exists(local_path):
                for i, (name, track, cover) in enumerate(mw.artist_model.items):
                    if name == artist_name:
                        mw.artist_model.items[i] = (name, track, local_path)
                        mw.artist_model.dataChanged.emit(mw.artist_model.index(i, 0), mw.artist_model.index(i, 0))
                        break
            if hasattr(mw, 'current_viewing_artist') and mw.current_viewing_artist == artist_name:
                if bio:
                    import json
                    try:
                        data = json.loads(bio)
                        summary = data.get("bio_summary", "")
                        content = data.get("bio_content", "")
                        tags = data.get("tags", [])
                        import theme_manager
                        accent = theme_manager.get_current_accent_hex()
                        final_text = ""
                        if summary:
                            final_text = summary
                            if len(summary) > 250:
                                final_text = summary[:250] + "... "
                            if content and len(content) > len(summary[:250]):
                                mw.current_artist_full_bio = content
                                final_text += f'<a href="read_more" style="color: {accent}; text-decoration: none;">Leer Más</a>'
                        if tags:
                            valid_tags = [t for t in tags if len(t) <= 20][:4]
                            tags_html = " • ".join(valid_tags)
                            mw.sidebar_artist_tags.setText(tags_html)
                        else:
                            mw.sidebar_artist_tags.setText("Aiiko Music")
                        if not final_text:
                            final_text = tr("Información no disponible.")
                        mw.sidebar_artist_bio_right.setTextFormat(Qt.TextFormat.RichText)
                        mw.sidebar_artist_bio_right.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
                        mw.sidebar_artist_bio_right.setOpenExternalLinks(False)
                        try: mw.sidebar_artist_bio_right.linkActivated.disconnect()
                        except: pass
                        def handle_link(link):
                            if link == "read_more":
                                from qfluentwidgets import MessageBoxBase, SubtitleLabel, BodyLabel
                                from qfluentwidgets import SmoothScrollArea as ScrollArea
                                from PyQt6.QtCore import Qt
                                class BioDialog(MessageBoxBase):
                                    def __init__(self, parent=None):
                                        super().__init__(parent)
                                        self.titleLabel = SubtitleLabel(tr("Biografía completa"), self)
                                        self.scrollArea = ScrollArea(self)
                                        self.scrollArea.setWidgetResizable(True)
                                        self.scrollArea.setStyleSheet("QScrollArea { border: none; background: transparent; }")
                                        self.contentLabel = BodyLabel(mw.current_artist_full_bio)
                                        self.contentLabel.setWordWrap(True)
                                        self.contentLabel.setStyleSheet("line-height: 1.5; font-size: 14px;")
                                        self.scrollArea.setWidget(self.contentLabel)
                                        self.viewLayout.addWidget(self.titleLabel)
                                        self.viewLayout.addWidget(self.scrollArea)
                                        self.widget.setMinimumWidth(500)
                                        self.widget.setMinimumHeight(450)
                                msg = BioDialog(mw)
                                msg.yesButton.setText(tr("Cerrar"))
                                msg.cancelButton.hide()
                                msg.exec()
                        mw.sidebar_artist_bio_right.linkActivated.connect(handle_link)
                        mw.sidebar_artist_bio_right.setText(final_text)
                    except json.JSONDecodeError:
                        mw.sidebar_artist_bio_right.setText(bio)
                        mw.sidebar_artist_tags.setText("Aiiko Music")
                else:
                    mw.sidebar_artist_bio_right.setText(tr("Información no disponible."))
                    mw.sidebar_artist_tags.setText("Aiiko Music")
                if local_path and os.path.exists(local_path):
                    class FakeTrack: pass
                    ft = FakeTrack()
                    ft.cover_path = local_path
                    mw.image_cache.assign_async_pixmap(mw.sidebar_artist_cover, ft, 200, 100)
        else:
            if hasattr(mw, 'current_viewing_artist') and mw.current_viewing_artist == artist_name:
                if hasattr(mw, 'sidebar_artist_bio_right'):
                    mw.sidebar_artist_bio_right.setText(tr("Información no disponible en la red."))
                    mw.sidebar_artist_tags.setText("Aiiko Music")
    def refresh_favorites_view(self):
        mw = self.mw
        fav_filepaths = settings.get('favorites', [])
        fav_tracks = []
        for filepath in fav_filepaths:
            track = next((t for t in mw.library if t.filepath == filepath), None)
            if track:
                fav_tracks.append(track)
        if hasattr(mw, 'page_favorites') and not getattr(mw.page_favorites, 'is_placeholder', False):
            mw.page_favorites.load_favorites(fav_tracks)
    def refresh_playlists_list(self):
        if hasattr(self.mw, 'page_playlists') and hasattr(self.mw.page_playlists, 'load_playlists'):
            self.mw.page_playlists.load_playlists(settings.get('playlists', {}))
    def refresh_playlists_view_details(self):
        mw = self.mw
        if hasattr(mw, 'page_playlists') and hasattr(mw.page_playlists, 'current_playlist_name') and mw.page_playlists.current_playlist_name:
            playlists = settings.get('playlists', {})
            p_name = mw.page_playlists.current_playlist_name
            if p_name in playlists:
                mw.page_playlists.load_playlist_details(p_name, playlists[p_name])
    def refresh_artist_related_playlists(self):
        mw = self.mw
        if not hasattr(mw, 'current_viewing_artist') or not mw.current_viewing_artist: return
        if not hasattr(mw, 'artist_stack') or mw.artist_stack.currentIndex() != 1: return
        artist_name = mw.current_viewing_artist
        artist_name_lower = artist_name.lower()
        tracks_in_artist = []
        for t in mw.library:
            artists = [a.lower() for a in get_artists_from_string(t.artist)]
            if artist_name_lower in artists:
                tracks_in_artist.append(t)
        all_playlists = settings.get('playlists', {})
        playlist_covers = settings.get('playlist_covers', {})
        related_playlists_data = {}
        if all_playlists:
            track_paths = {t.filepath for t in tracks_in_artist}
            lib_dict = {t.filepath: t for t in mw.library}
            for p_name, filepaths in all_playlists.items():
                if any(fp in track_paths for fp in filepaths):
                    cover = playlist_covers.get(p_name)
                    if not cover or not os.path.exists(cover):
                        cover = None
                        for fp in filepaths:
                            track = lib_dict.get(fp)
                            if track and getattr(track, 'cover_path', None) and os.path.exists(track.cover_path):
                                cover = track.cover_path
                                break
                    related_playlists_data[p_name] = {'filepaths': filepaths, 'cover': cover}
        if hasattr(mw, 'page_library') and hasattr(mw.page_library.artists_tab, 'populate_related_playlists'):
            mw.page_library.artists_tab.populate_related_playlists(related_playlists_data)