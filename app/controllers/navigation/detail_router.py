import os
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PyQt6.QtWidgets import QListWidgetItem
from qfluentwidgets import RoundMenu, Action, FluentIcon as FIF
from settings_manager import settings
from utils import sanitize_text, get_artists_from_string
from workers import ArtistInfoFetcherThread
from core.language_manager import tr
class DetailRouterMixin:
    def open_album_detail(self, index=None, target_album_name=None, target_artist_name=None):
        if hasattr(index, 'data'):
            album_name = index.data(Qt.ItemDataRole.UserRole)
            track_ref = index.data(Qt.ItemDataRole.UserRole + 1)
            if track_ref:
                target_artist_name = getattr(track_ref, 'album_artist', None) or track_ref.artist
        elif isinstance(index, str):
            album_name = index
        else:
            album_name = target_album_name
        if not album_name:
            return
        if getattr(self.mw.page_library, 'is_placeholder', False):
            self.preload_view(1)
        if getattr(self.mw, 'album_detail_widget', None) is None:
            from UI.library.albums.album_detail import AlbumDetailView
            self.mw.album_detail_widget = AlbumDetailView(self.mw, parent=self.mw.stacked_lib)
            self.mw.stacked_lib.addWidget(self.mw.album_detail_widget)
            if hasattr(self.mw, 'theme_controller'):
                from PyQt6.QtCore import QTimer as _QTimer
                from qfluentwidgets.common.style_sheet import updateStyleSheet as _updateStyleSheet
                _QTimer.singleShot(0, _updateStyleSheet)
                _QTimer.singleShot(0, lambda: self.mw.theme_controller.apply_theme(full_refresh=False))
        if not getattr(self, '_restoring', False):
            current_page = self.mw.stacked_widget.currentIndex() if hasattr(self.mw, 'stacked_widget') else 0
            if current_page == 1:
                self._push_nav_state(self._get_current_state(), target_category=1)
            else:
                self._push_nav_state({'page_index': 1, 'lib_tab_index': 1, 'lib_tab_name': 'albums'}, target_category=1)
            self.update_return_button()
        tracks_in_album = []
        safe_target = sanitize_text(album_name)
        safe_artist = sanitize_text(target_artist_name) if target_artist_name else None
        merge_albums = settings.get('merge_collaborative_albums', True)
        from utils import match_track_to_album
        for t in self.mw.library:
            if match_track_to_album(t, safe_target, safe_artist, merge_albums):
                tracks_in_album.append(t)
        tracks_in_album.sort(key=lambda t: getattr(t, 'track_number', 9999))
        if hasattr(self.mw, 'album_tracks_model') and self.mw.album_tracks_model:
            self.mw.album_tracks_model.set_tracks(tracks_in_album)
        first_track = tracks_in_album[0] if tracks_in_album else None
        if first_track:
            self.mw.sidebar_title.setText(album_name)
            self.mw.sidebar_artist.setText(sanitize_text(first_track.artist))
            total_duration = 0
            for t in tracks_in_album:
                if getattr(t, 'duration', 0) > 0:
                    total_duration += t.duration
            total_duration_sec = int(total_duration // 1000)
            mins = total_duration_sec // 60
            secs = total_duration_sec % 60
            if mins >= 60:
                hrs = mins // 60
                mins = mins % 60
                dur_text = f"{hrs} h {mins} min {secs} s"
            else:
                dur_text = f"{mins} min {secs:02d} s"
            self.mw.sidebar_year.setText(f"{len(tracks_in_album)} canciones • {dur_text}")            
            self.mw.image_cache.assign_async_pixmap(self.mw.sidebar_cover, first_track, 220, 15, fallback_icon=FIF.ALBUM)
            if hasattr(self.mw, 'album_hero_banner_bg'):
                self.mw.image_cache.assign_async_pixmap(self.mw.album_hero_banner_bg, first_track, 400, 40, fallback_icon=FIF.ALBUM)
            total_duration = 0
            genres = set()
            for t in tracks_in_album:
                if getattr(t, 'duration', 0) > 0:
                    total_duration += t.duration
                if getattr(t, 'genre', None):
                    import re
                    g_list = re.split(r'[/,;]', t.genre)
                    for g in g_list:
                        g_clean = g.strip()
                        if g_clean:
                            genres.add(g_clean.title())
            total_duration_sec = int(total_duration // 1000)
            mins = total_duration_sec // 60
            secs = total_duration_sec % 60
            if mins >= 60:
                hrs = mins // 60
                mins = mins % 60
                duration_str = f"{hrs} h {mins} min {secs} s"
            else:
                duration_str = f"{mins} min {secs:02d} s"
            genre_str = " / ".join(list(genres)[:3]) if genres else tr("Desconocido")
            import theme_manager
            accent = theme_manager.get_current_accent_hex()
            owner_str = tr("Desconocido")
            if first_track and first_track.artist:
                owner_artists = get_artists_from_string(first_track.artist)
                if owner_artists:
                    owner_str = owner_artists[0]
            if hasattr(self.mw, 'lbl_album_info_artist'):
                year_val = getattr(first_track, 'year', tr('Desconocido')) if first_track else tr('Desconocido')
                self.mw.lbl_album_info_artist.set_value(owner_str)
                self.mw.lbl_album_info_year.set_value(str(year_val))
                self.mw.lbl_album_info_genre.set_value(genre_str)
                self.mw.lbl_album_info_duration.set_value(duration_str)
            unique_artists = []
            if first_track and first_track.artist:
                for a in get_artists_from_string(first_track.artist):
                    if a not in unique_artists:
                        unique_artists.append(a)
            for t in tracks_in_album:
                if t.artist:
                    extracted = get_artists_from_string(t.artist)
                    for a in extracted:
                        a_clean = a.strip()
                        if a_clean and a_clean not in unique_artists:
                            unique_artists.append(a_clean)
            if hasattr(self.mw, 'album_detail_widget'):
                self.mw.album_detail_widget.populate_album_artists(unique_artists)
        if hasattr(self.mw, 'stacked_lib'):
            self.mw.stacked_lib.setCurrentWidget(self.mw.album_detail_widget)
        if hasattr(self.mw, 'pivot'):
            self.mw.pivot.setCurrentItem('albums')
        self.switch_page(1)
        if hasattr(self.mw, 'page_library') and hasattr(self.mw.page_library, 'header_widget'):
            self.mw.page_library.header_widget.hide()
    def open_artist_detail(self, index=None, artist_name_str=None):
        if artist_name_str:
            artist_name = artist_name_str
        elif index:
            artist_name = index.data(Qt.ItemDataRole.UserRole)
        else:
            return
        if getattr(self.mw.page_library, 'is_placeholder', False):
            self.preload_view(1)
        if getattr(self.mw, 'artist_detail_widget', None) is None:
            from UI.library.artists.artist_detail import ArtistDetailView
            self.mw.artist_detail_widget = ArtistDetailView(self.mw, parent=self.mw.stacked_lib)
            self.mw.stacked_lib.addWidget(self.mw.artist_detail_widget)
            if hasattr(self.mw, 'theme_controller'):
                from PyQt6.QtCore import QTimer as _QTimer
                from qfluentwidgets.common.style_sheet import updateStyleSheet as _updateStyleSheet
                _QTimer.singleShot(0, _updateStyleSheet)
                _QTimer.singleShot(0, lambda: self.mw.theme_controller.apply_theme(full_refresh=False))
        if not getattr(self, '_restoring', False):
            current_page = self.mw.stacked_widget.currentIndex() if hasattr(self.mw, 'stacked_widget') else 0
            if current_page == 1:
                self._push_nav_state(self._get_current_state(), target_category=1)
            else:
                self._push_nav_state({'page_index': 1, 'lib_tab_index': 2, 'lib_tab_name': 'artists'}, target_category=1)
            self.update_return_button()
        self.mw.current_viewing_artist = artist_name
        if hasattr(self.mw, 'artist_detail_widget') and self.mw.artist_detail_widget:
            try:
                artist_detail = self.mw.artist_detail_widget
                artist_detail.artist_tabs.setCurrentItem('overview', trigger=True)
                artist_detail.left_scroll.verticalScrollBar().setValue(0)
                artist_detail.right_scroll.verticalScrollBar().setValue(0)
                artist_detail.disco_scroll.horizontalScrollBar().setValue(0)
            except Exception:
                pass
        self.mw.sidebar_artist_title.setText(artist_name)
        self.mw.sidebar_artist_stats.setText(tr("Cargando..."))
        if hasattr(self.mw, 'sidebar_artist_bio_right'):
            self.mw.sidebar_artist_bio_right.setText(tr("Buscando información en internet..."))
            self.mw.sidebar_artist_tags.setText("")
        if hasattr(self.mw, 'page_library') and hasattr(self.mw.page_library, 'header_widget'):
            self.mw.page_library.header_widget.hide()
        if hasattr(self.mw, 'stacked_lib'):
            self.mw.stacked_lib.setCurrentWidget(self.mw.artist_detail_widget)
        if hasattr(self.mw, 'pivot'):
            self.mw.pivot.setCurrentItem('artists')
        self.switch_page(1)
        if hasattr(self.mw, '_artist_data_worker') and self.mw._artist_data_worker is not None:
            try:
                self.mw._artist_data_worker.result_ready.disconnect()
            except TypeError:
                pass
            old_worker = self.mw._artist_data_worker
            if old_worker.isRunning():
                if not hasattr(self.mw, '_orphaned_workers'):
                    self.mw._orphaned_workers = []
                self.mw._orphaned_workers.append(old_worker)
                def _cleanup(w=old_worker):
                    w.deleteLater()
                    if hasattr(self.mw, '_orphaned_workers') and w in self.mw._orphaned_workers:
                        self.mw._orphaned_workers.remove(w)
                old_worker.finished.connect(_cleanup)
            else:
                old_worker.deleteLater()
        from workers import ArtistDataWorker
        self.mw._artist_data_worker = ArtistDataWorker(artist_name, self.mw.library)
        self.mw._artist_data_worker.result_ready.connect(self._apply_artist_data)
        self.mw._artist_data_worker.start()
    def _apply_artist_data(self, data):
        artist_name = data['artist_name']
        if getattr(self.mw, 'current_viewing_artist', None) != artist_name:
            return
        first_track = data['first_track']
        tracks_in_artist = data['tracks_in_artist']
        top_tracks = data['top_tracks']
        album_items = data['album_items']
        ep_items = data['ep_items']
        all_disco_items = data['all_disco_items']
        rec_list = data['rec_list']
        count = data['count']
        total_plays = data['total_plays']
        if self.mw.artist_tracks_model:
            self.mw.artist_tracks_model.set_tracks(tracks_in_artist)
            if hasattr(self.mw, 'list_artist_tracks'):
                self.mw.list_artist_tracks.setFixedHeight(len(tracks_in_artist) * 50 + 10)
        if hasattr(self.mw, 'top_tracks_model'):
            self.mw.top_tracks_model.set_tracks(top_tracks)
            if hasattr(self.mw, 'top_tracks_list'):
                self.mw.top_tracks_list.setFixedHeight(max(51, len(top_tracks) * 51))
        related_playlists = data.get('related_playlists', {})
        if hasattr(self.mw, 'artist_detail_widget') and hasattr(self.mw.artist_detail_widget, 'populate_related_playlists'):
            self.mw.artist_detail_widget.populate_related_playlists(related_playlists)
        if hasattr(self.mw, 'populate_artist_discography'):
            self.mw.populate_artist_discography(all_disco_items)
        if hasattr(self.mw, 'populate_full_discography'):
            self.mw.populate_full_discography(album_items, ep_items)
        if hasattr(self.mw, 'populate_recommended_artists'):
            self.mw.populate_recommended_artists(rec_list)
        self.mw.sidebar_artist_title.setText(artist_name)
        self.mw.sidebar_artist_stats.setText(f"{count} Canciones • {total_plays} Reproducciones")
        from database import get_artist_info_db
        from utils import normalize_artist_name
        artist_data = get_artist_info_db(normalize_artist_name(artist_name)) or {}
        custom_cover = artist_data.get('cover_path')
        class FakeTrack: pass
        if custom_cover and isinstance(custom_cover, str) and os.path.exists(custom_cover):
            ft = FakeTrack()
            ft.cover_path = custom_cover
            self.mw.image_cache.assign_async_pixmap(self.mw.sidebar_artist_cover, ft, 200, 100, fallback_icon=FIF.PEOPLE)
            if hasattr(self.mw, 'hero_banner_bg'):
                self.mw.image_cache.assign_async_pixmap(self.mw.hero_banner_bg, ft, 400, 0, fallback_icon=FIF.PEOPLE)
        elif first_track:
            self.mw.image_cache.assign_async_pixmap(self.mw.sidebar_artist_cover, first_track, 200, 100, fallback_icon=FIF.PEOPLE)
            if hasattr(self.mw, 'hero_banner_bg'):
                self.mw.image_cache.assign_async_pixmap(self.mw.hero_banner_bg, first_track, 400, 0, fallback_icon=FIF.PEOPLE)
        else:
            ft = FakeTrack()
            ft.cover_path = None
            self.mw.image_cache.assign_async_pixmap(self.mw.sidebar_artist_cover, ft, 200, 100, fallback_icon=FIF.PEOPLE)
            if hasattr(self.mw, 'hero_banner_bg'):
                self.mw.hero_banner_bg.clear()
        if hasattr(self.mw, 'fetcher') and self.mw.fetcher is not None:
            try: self.mw.fetcher.result_ready.disconnect()
            except TypeError: pass
            old_fetcher = self.mw.fetcher
            if old_fetcher.isRunning():
                if not hasattr(self.mw, '_orphaned_workers'):
                    self.mw._orphaned_workers = []
                self.mw._orphaned_workers.append(old_fetcher)
                def _cleanup_fetcher(w=old_fetcher):
                    w.deleteLater()
                    if hasattr(self.mw, '_orphaned_workers') and w in self.mw._orphaned_workers:
                        self.mw._orphaned_workers.remove(w)
                old_fetcher.finished.connect(_cleanup_fetcher)
            else:
                old_fetcher.deleteLater()
        self.mw.fetcher = ArtistInfoFetcherThread(artist_name)
        self.mw.fetcher.result_ready.connect(self.mw.library_controller.on_artist_info_fetched)
        self.mw.fetcher.start()
    def _navigate_to_artist(self, target_artist):
        is_lazy = getattr(self.mw.stacked_widget.widget(1), 'is_placeholder', False)
        self.switch_page(1)
        def _do_nav():
            if hasattr(self.mw, 'pivot'):
                self.mw.pivot.setCurrentItem('artists')
            self.open_artist_detail(artist_name_str=target_artist)
        self._execute_when_page_ready(1, _do_nav)
    def _show_artist_picker(self, artists):
        menu = RoundMenu(parent=self.mw)
        menu.setTitle(tr("Seleccionar Artista"))
        for artist in artists:
            menu.addAction(Action(FIF.PEOPLE, artist, triggered=lambda checked=False, a=artist: self._navigate_to_artist(a)))
        if hasattr(self.mw, 'full_artist') and self.mw.full_artist.isVisible():
            pos = self.mw.full_artist.mapToGlobal(self.mw.full_artist.rect().bottomLeft())
        else:
            pos = self.mw.cursor().pos()
        menu.exec(pos)
    def handle_now_playing_link(self, link):
        if self.mw.queue.current_index < 0 or not self.mw.queue.tracks: return
        track = self.mw.queue.tracks[self.mw.queue.current_index]
        if link == "artist":
            artists = get_artists_from_string(track.artist) if track.artist else ["Desconocido"]
            if len(artists) > 1:
                self._show_artist_picker(artists)
                return
            else:
                self._navigate_to_artist(artists[0])
        elif link == "album":
            is_lazy = getattr(self.mw.stacked_widget.widget(1), 'is_placeholder', False)
            self.switch_page(1)
            def _do_nav_album():
                if hasattr(self.mw, 'pivot'):
                    self.mw.pivot.setCurrentItem('albums')
                target_album = track.album if track.album else "Desconocido"
                target_artist = getattr(track, 'album_artist', None) or track.artist
                self.open_album_detail(target_album_name=target_album, target_artist_name=target_artist)
            self._execute_when_page_ready(1, _do_nav_album)