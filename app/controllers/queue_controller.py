from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QObject, pyqtSignal
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import QAbstractItemView
from qfluentwidgets import Action, RoundMenu
from qfluentwidgets import FluentIcon as FIF
from config import ICON_PLAY, ICON_DELETE
from core.language_manager import tr
class QueueController(QObject):
    queue_changed = pyqtSignal()
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
    def play_specific_track_from_list(self, track, list_widget):
        queue = [list_widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(list_widget.count()) if list_widget.item(i).data(Qt.ItemDataRole.UserRole)]
        self.play_specific_track_global(track, queue)
    def _get_tracks_from_model(self, model):
        if hasattr(model, 'tracks'):
            return list(model.tracks)
        elif hasattr(model, 'sourceModel'):
            source = model.sourceModel()
            from PyQt6.QtCore import QSortFilterProxyModel
            if isinstance(model, QSortFilterProxyModel):
                if hasattr(source, 'tracks'):
                    return [source.tracks[model.mapToSource(model.index(i, 0)).row()] for i in range(model.rowCount())]
            from PyQt6.QtCore import Qt
            return [model.index(i, 0).data(Qt.ItemDataRole.UserRole) for i in range(model.rowCount())]
        return list(self.main_window.track_model.tracks)
    def play_specific_track_from_listview(self, index):
        track = index.data(Qt.ItemDataRole.UserRole)
        if track: 
            source_queue = self._get_tracks_from_model(index.model())
            self.play_specific_track_global(track, source_queue)
    def play_album_shuffled(self, track_model):
        if not hasattr(track_model, 'tracks') or not track_model.tracks: return
        import random
        shuffled_tracks = list(track_model.tracks)
        random.shuffle(shuffled_tracks)
        self.play_specific_track_global(shuffled_tracks[0], shuffled_tracks)
    def play_album_direct(self, album_name, artist_name=None):
        from utils import sanitize_text
        target_album = sanitize_text(album_name)
        target_artist = sanitize_text(artist_name) if artist_name else None
        album_tracks = []
        from settings_manager import settings
        from utils import get_artists_from_string, match_track_to_album
        merge_albums = settings.get('merge_collaborative_albums', True)
        for t in self.main_window.library:
            if match_track_to_album(t, target_album, target_artist, merge_albums):
                album_tracks.append(t)
        if not album_tracks:
            return
        def get_track_num(t):
            try:
                import mutagen
                audio = mutagen.File(t.filepath)
                if audio is not None:
                    tags = getattr(audio, 'tags', audio)
                    if tags:
                        lower_keys = {k.lower(): k for k in tags.keys()} if hasattr(tags, 'keys') else {}
                        for t_name in ['trck', 'tracknumber', 'trkn']:
                            if t_name in lower_keys:
                                val = tags[lower_keys[t_name]]
                                if isinstance(val, list): val = val[0]
                                return int(str(val).split('/')[0])
            except Exception:
                pass
            return 9999
        album_tracks.sort(key=get_track_num)
        self.play_specific_track_global(album_tracks[0], album_tracks)
    def play_specific_track_global(self, track, source_queue):
        self.main_window.queue.tracks = list(source_queue)
        if track in self.main_window.queue.tracks:
            self.main_window.queue.current_index = self.main_window.queue.tracks.index(track)
            if self.main_window.queue.is_shuffled:
                self.main_window.queue.shuffle(state=True)
            track = self.main_window.queue.get_current()
            if track:
                self.main_window.playback_controller.play_track(track)
    def add_to_queue(self, track_or_tracks, show_notification=True, custom_notify_text=None):
        tracks = track_or_tracks if isinstance(track_or_tracks, list) else [track_or_tracks]
        self.main_window.queue.tracks.extend(tracks)
        if show_notification:
            from core.notification_manager import notify
            if custom_notify_text:
                notify.success(tr("Añadido"), custom_notify_text)
            else:
                title_str = tracks[0].title if len(tracks) == 1 else f"{len(tracks)} canciones"
                notify.success(tr("Añadido"), f"{title_str} se añadió al final de la cola.")
        self.refresh_queue_ui()
        self.update_gapless_preload()
    def add_to_queue_next(self, track_or_tracks, show_notification=True, custom_notify_text=None):
        tracks = track_or_tracks if isinstance(track_or_tracks, list) else [track_or_tracks]
        if self.main_window.queue.current_index >= 0:
            insert_idx = self.main_window.queue.current_index + 1
            for track in reversed(tracks):
                self.main_window.queue.tracks.insert(insert_idx, track)
        else:
            self.main_window.queue.tracks.extend(tracks)
        if show_notification:
            from core.notification_manager import notify
            if custom_notify_text:
                notify.success(tr("Añadido a continuación"), custom_notify_text)
            else:
                title_str = tracks[0].title if len(tracks) == 1 else f"{len(tracks)} canciones"
                notify.success(tr("Añadido a continuación"), f"{title_str} se reproducirá a continuación.")
        self.refresh_queue_ui()
        self.update_gapless_preload()
    def toggle_queue_panel(self):
        panel_width = self.main_window.queue_panel.width()
        panel_height = self.main_window.central_widget.height() - self.main_window.mini_player.height()
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        self.main_window.queue_animation = QPropertyAnimation(self.main_window.queue_panel, b"geometry")
        self.main_window.queue_animation.setDuration(350)
        self.main_window.queue_animation.setEasingCurve(QEasingCurve.Type.OutExpo)
        if self.main_window.queue_is_open:
            self.main_window.queue_animation.setStartValue(QRect(self.main_window.width() - panel_width, 0, panel_width, panel_height))
            self.main_window.queue_animation.setEndValue(QRect(self.main_window.width(), 0, panel_width, panel_height))
            self.main_window.queue_is_open = False
        else:
            self.main_window.queue_panel.raise_()
            self.main_window.queue_animation.setStartValue(QRect(self.main_window.width(), 0, panel_width, panel_height))
            self.main_window.queue_animation.setEndValue(QRect(self.main_window.width() - panel_width, 0, panel_width, panel_height))
            self.main_window.queue_is_open = True
            if 0 <= self.main_window.queue.current_index < len(self.main_window.queue.tracks):
                target_row = self.main_window.queue.current_index
                if target_row + 1 < len(self.main_window.queue.tracks): target_row += 1
                idx = self.main_window.queue_model.index(target_row, 0)
                self.main_window.list_queue_ui.scrollTo(idx, QAbstractItemView.ScrollHint.PositionAtTop)
        if hasattr(self.main_window, 'playback_ui_controller'):
            self.main_window.playback_ui_controller._update_queue_icon()
        self.main_window.queue_animation.start()
    def scroll_to_current(self):
        if 0 <= self.main_window.queue.current_index < len(self.main_window.queue.tracks):
            from PyQt6.QtWidgets import QAbstractItemView
            target_row = self.main_window.queue.current_index
            if target_row + 1 < len(self.main_window.queue.tracks): target_row += 1
            idx = self.main_window.queue_model.index(target_row, 0)
            self.main_window.list_queue_ui.scrollTo(idx, QAbstractItemView.ScrollHint.PositionAtTop)
    def show_queue_context_menu(self, pos):
        idx = self.main_window.list_queue_ui.indexAt(pos)
        if not idx.isValid(): return
        track = self.main_window.queue_model.tracks[idx.row()]
        global_pos = self.main_window.list_queue_ui.mapToGlobal(pos)
        self._build_queue_context_menu(track, idx.row(), global_pos)
    def show_pinned_track_context_menu(self, global_pos):
        current_idx = self.main_window.queue.current_index
        if 0 <= current_idx < len(self.main_window.queue.tracks):
            track = self.main_window.queue.tracks[current_idx]
            self._build_queue_context_menu(track, current_idx, global_pos)
    def _build_queue_context_menu(self, track, index_row, global_pos):
        menu = RoundMenu(parent=self.main_window)
        from core.language_manager import tr
        menu.addAction(Action(ICON_PLAY, tr("Reproducir"), triggered=lambda: self.play_from_queue_ui(index_row)))
        menu.addAction(Action(ICON_DELETE, tr("Quitar de la cola"), triggered=lambda: self.remove_track_from_queue_by_index(index_row)))
        menu.addAction(Action(FIF.SEARCH, tr("Localizar en la biblioteca"), triggered=lambda: self.main_window.library_controller.locate_in_library(track)))
        menu.addSeparator()
        if track.album and track.album not in ["Desconocido", "Unknown", "", tr("Álbum Desconocido")]:
            t_artist = getattr(track, 'album_artist', None) or track.artist
            menu.addAction(Action(FIF.ALBUM, tr("Ir al álbum"), triggered=lambda: self.main_window.navigation_controller.open_album_detail(target_album_name=track.album, target_artist_name=t_artist)))
        from utils import get_artists_from_string
        artists = get_artists_from_string(track.artist)
        if len(artists) == 1:
            menu.addAction(Action(FIF.PEOPLE, tr("Ir al artista"), triggered=lambda _, a=artists[0]: self.main_window.navigation_controller.open_artist_detail(artist_name_str=a)))
        elif len(artists) > 1:
            artist_menu = RoundMenu(tr("Ir al artista"), parent=menu)
            artist_menu.setIcon(FIF.PEOPLE)
            for a in artists:
                artist_menu.addAction(Action(FIF.CONNECT, a, triggered=lambda _, artist=a: self.main_window.navigation_controller.open_artist_detail(artist_name_str=artist)))
            menu.addMenu(artist_menu)
        from settings_manager import settings
        from config import ICON_HEART
        favs = settings.get('favorites', [])
        is_fav = track.filepath in favs
        fav_text, fav_icon = (tr("Quitar de Favoritos"), ICON_DELETE) if is_fav else (tr("Añadir a Favoritos"), ICON_HEART)
        menu.addAction(Action(fav_icon, fav_text, triggered=lambda _, t=track: self.main_window.app_controller.toggle_favorite_track(t)))
        menu.addSeparator()
        menu.addAction(Action(FIF.EDIT, tr("Propiedades"), triggered=lambda: self.main_window.app_controller.edit_track_metadata(track)))
        menu.exec(global_pos)
    def refresh_queue_ui(self):
        self.main_window.queue_model.set_tracks(self.main_window.queue.tracks)
        self.main_window.queue_model.update_current_index(self.main_window.queue.current_index)
        total = len(self.main_window.queue.tracks)
        current_idx = self.main_window.queue.current_index
        current = current_idx + 1 if current_idx >= 0 else 0
        remaining_count = total - (current_idx + 1) if current_idx >= 0 else total
        if remaining_count < 0: remaining_count = 0
        if 0 <= current_idx < total:
            remaining_tracks = self.main_window.queue.tracks[current_idx:]
        else:
            remaining_tracks = self.main_window.queue.tracks
        total_ms = sum(getattr(t, 'duration', 0) or 0 for t in remaining_tracks)
        total_sec = total_ms / 1000.0
        if total_sec >= 3600:
            h = int(total_sec // 3600)
            m = int((total_sec % 3600) // 60)
            dur_str = f"{h} h {m} min"
        else:
            m = int(total_sec // 60)
            dur_str = f"{m} min"
        import theme_manager
        accent = theme_manager.get_current_accent_hex()
        self.main_window.lbl_queue_subtitle.setText(
            f'<span style="color:{accent}; font-weight:600;">{current}</span>'
            f' de '
            f'<span style="color:{accent}; font-weight:600;">{total}</span>'
            f' <span style="font-size:18px;">·</span> '
            f'<span style="color:{accent}; font-weight:600;">{dur_str}</span>'
            f' restantes'
        )
        self._last_remaining_count = remaining_count
        self.update_queue_theme()
        if self.main_window.queue_is_open and 0 <= self.main_window.queue.current_index < len(self.main_window.queue.tracks):
            target_row = self.main_window.queue.current_index
            if target_row + 1 < len(self.main_window.queue.tracks): target_row += 1
            idx = self.main_window.queue_model.index(target_row, 0)
            self.main_window.list_queue_ui.scrollTo(idx, QAbstractItemView.ScrollHint.PositionAtTop)
        if hasattr(self.main_window, 'remote_server') and self.main_window.remote_server:
            self.main_window.remote_server.broadcast_queue()
        self.queue_changed.emit()
    def update_queue_theme(self):
        import theme_manager
        from PyQt6.QtGui import QPixmap, QPainter, QColor
        from PyQt6.QtCore import Qt
        from core.language_manager import tr
        accent = theme_manager.get_current_accent_hex()
        if hasattr(self.main_window, 'icon_en_reproduccion'):
            eq_pix = QPixmap(14, 14)
            eq_pix.fill(Qt.GlobalColor.transparent)
            p = QPainter(eq_pix)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(accent))
            p.drawRoundedRect(1, 6, 3, 8, 1, 1)
            p.drawRoundedRect(5, 2, 3, 12, 1, 1)
            p.drawRoundedRect(9, 8, 3, 6, 1, 1)
            p.end()
            self.main_window.icon_en_reproduccion.setPixmap(eq_pix)
            self.main_window.lbl_en_reproduccion.setStyleSheet(f"color: {accent}; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        if hasattr(self.main_window, 'icon_proximas'):
            menu_pix = QPixmap(14, 14)
            menu_pix.fill(Qt.GlobalColor.transparent)
            p = QPainter(menu_pix)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(accent))
            p.drawRoundedRect(0, 2, 14, 2, 1, 1)
            p.drawRoundedRect(0, 6, 14, 2, 1, 1)
            p.drawRoundedRect(0, 10, 14, 2, 1, 1)
            p.end()
            self.main_window.icon_proximas.setPixmap(menu_pix)
            rem_count = getattr(self, '_last_remaining_count', 0)
            self.main_window.lbl_proximas.setText(f"{tr('PRÓXIMAS CANCIONES')} ({rem_count})")
            self.main_window.lbl_proximas.setStyleSheet(f"color: {accent}; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        total = len(self.main_window.queue.tracks)
        if total > 0:
            current_idx = self.main_window.queue.current_index
            current = current_idx + 1 if current_idx >= 0 else 0
            if 0 <= current_idx < total:
                remaining_tracks = self.main_window.queue.tracks[current_idx:]
            else:
                remaining_tracks = self.main_window.queue.tracks
            total_ms = sum(getattr(t, 'duration', 0) or 0 for t in remaining_tracks)
            total_sec = total_ms / 1000.0
            if total_sec >= 3600:
                h = int(total_sec // 3600)
                m = int((total_sec % 3600) // 60)
                dur_str = f"{h} h {m} min"
            else:
                m = int(total_sec // 60)
                dur_str = f"{m} min"
            self.main_window.lbl_queue_subtitle.setText(
                f'<span style="color:{accent}; font-weight:600;">{current}</span>'
                f' de '
                f'<span style="color:{accent}; font-weight:600;">{total}</span>'
                f' <span style="font-size:18px;">·</span> '
                f'<span style="color:{accent}; font-weight:600;">{dur_str}</span>'
                f' restantes'
            )
        if hasattr(self.main_window, 'pinned_track_widget'):
            self.main_window.pinned_track_widget.update_theme()
    def sync_queue_from_ui(self):
        new_queue = list(self.main_window.queue_model.tracks)
        self.main_window.queue.tracks = new_queue
        self.main_window.queue.current_index = self.main_window.queue_model.current_index
        self.refresh_queue_ui()
        self.update_gapless_preload()
    def clear_queue(self):
        if not self.main_window.queue.tracks: return
        if 0 <= self.main_window.queue.current_index < len(self.main_window.queue.tracks):
            current = self.main_window.queue.tracks[self.main_window.queue.current_index]
            self.main_window.queue.tracks = [current]
            self.main_window.queue.current_index = 0
        else:
            self.main_window.queue.tracks = []
            self.main_window.queue.current_index = -1
        self.refresh_queue_ui()
        self.update_gapless_preload()
    def play_from_queue_ui(self, index_or_row):
        from PyQt6.QtCore import QModelIndex
        row = index_or_row.row() if isinstance(index_or_row, QModelIndex) else index_or_row
        if 0 <= row < len(self.main_window.queue.tracks):
            self.main_window.queue.current_index = row
            current = self.main_window.queue.get_current()
            if current:
                self.main_window.playback_controller.play_track(current)
    def remove_track_from_queue_by_index(self, index_row):
        if 0 <= index_row < len(self.main_window.queue.tracks):
            track_to_remove = self.main_window.queue.tracks[index_row]
            if index_row == self.main_window.queue.current_index:
                del self.main_window.queue.tracks[index_row]
                if self.main_window.queue.tracks:
                    if self.main_window.queue.current_index >= len(self.main_window.queue.tracks):
                        self.main_window.queue.current_index = 0
                    current = self.main_window.queue.get_current()
                    if current:
                        self.main_window.playback_controller.play_track(current)
                else:
                    self.main_window.queue.current_index = -1
                    self.main_window.audio_engine.stop()
            else:
                del self.main_window.queue.tracks[index_row]
                if index_row < self.main_window.queue.current_index:
                    self.main_window.queue.current_index -= 1
            self.refresh_queue_ui()
            self.update_gapless_preload()
    def toggle_shuffle(self):
        from settings_manager import settings
        self.main_window.queue.shuffle()
        settings.set('is_shuffled', getattr(self.main_window.queue, 'is_shuffled', False))
        self.main_window.playback_ui_controller._update_shuffle_icon()
        self.refresh_queue_ui()
        self.update_gapless_preload()
        if getattr(self.main_window, 'remote_server', None):
            self.main_window.remote_server.broadcast_state()
            self.main_window.remote_server.broadcast_queue()
    def toggle_repeat(self):
        from settings_manager import settings
        self.main_window.queue.set_repeat_mode(self.main_window.queue.repeat_mode + 1)
        settings.set('repeat_mode', getattr(self.main_window.queue, 'repeat_mode', 0))
        self.main_window.playback_ui_controller._update_repeat_icon()
        self.update_gapless_preload()
        if getattr(self.main_window, 'remote_server', None):
            self.main_window.remote_server.broadcast_state()
    def update_gapless_preload(self):
        from settings_manager import settings
        if not hasattr(self.main_window, 'audio_engine') or not getattr(self.main_window, 'queue', None):
            return
        if not settings.get('gapless_enabled', True):
            self.main_window.audio_engine._release_preload()
            return
        if hasattr(self.main_window, 'sleep_timer_controller') and self.main_window.sleep_timer_controller.is_last_song():
            self.main_window.audio_engine._release_preload()
            return
        queue = self.main_window.queue
        if not queue.tracks:
            return
        if queue.repeat_mode == 2:
            current = queue.get_current()
            if current:
                self.main_window.audio_engine.preload_track(current.filepath)
            return
        next_idx = queue.current_index + 1
        if next_idx >= len(queue.tracks):
            if queue.repeat_mode == 1:
                next_idx = 0
            else:
                self.main_window.audio_engine._release_preload()
                return                  
        if 0 <= next_idx < len(queue.tracks):
            next_track = queue.tracks[next_idx]
            self.main_window.audio_engine.preload_track(next_track.filepath)