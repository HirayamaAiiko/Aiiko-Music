import logging
import time
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, Qt, QRunnable, QThreadPool
from database import record_listen
class DBWorker(QRunnable):
    def __init__(self, filepath, listen_type, listened_ms, total_ms):
        super().__init__()
        self.filepath = filepath
        self.listen_type = listen_type
        self.listened_ms = listened_ms
        self.total_ms = total_ms
    def run(self):
        try:
            record_listen(self.filepath, self.listen_type, self.listened_ms, self.total_ms)
        except Exception as e:
            logging.debug(f"Error asíncrono en DB: {e}")
class LastfmWorker(QRunnable):
    def __init__(self, action, artist, title, album="", timestamp=None):
        super().__init__()
        self.action = action
        self.artist = artist
        self.title = title
        self.album = album
        self.timestamp = timestamp
    def run(self):
        try:
            from services.lastfm_service import LastfmService
            if self.action == 'now_playing':
                LastfmService.update_now_playing(self.artist, self.title, self.album)
            elif self.action == 'scrobble':
                LastfmService.scrobble(self.artist, self.title, self.album, self.timestamp)
        except Exception as e:
            logging.debug(f"Error en Last.fm Worker: {e}")
class PlaybackController(QObject):
    track_loaded = pyqtSignal(object)
    def __init__(self, main_window, audio_engine, queue):
        super().__init__()
        self.main_window = main_window
        self.audio_engine = audio_engine
        self.queue = queue
        self.audio_engine.gapless_transition_occurred.connect(
            self._handle_gapless_transition, 
            Qt.ConnectionType.QueuedConnection
        )
        self.audio_engine.track_load_failed.connect(
            self._handle_track_load_failed,
            Qt.ConnectionType.QueuedConnection
        )
        self.audio_engine.crossfade_advance.connect(
            self._handle_crossfade_advance,
            Qt.ConnectionType.QueuedConnection
        )
        self._current_filepath = None
        self._listen_start_time = 0                                   
        self._listen_start_pos_ms = 0                                    
        self._current_total_ms = 0                                    
    def _evaluate_previous_listen(self, was_natural_end=False):
        if not self._current_filepath:
            return
        try:
            current_pos = self.audio_engine.get_position() if not was_natural_end else self._current_total_ms
            listened_ms = max(0, current_pos - self._listen_start_pos_ms)
            total_ms = self._current_total_ms
            if total_ms > 0:
                listened_ms = min(listened_ms, total_ms)
            if listened_ms < 10_000 and not was_natural_end:
                self._current_filepath = None
                return
            if was_natural_end:
                listen_type = 'completed'
            elif total_ms > 0 and (listened_ms >= 30_000 or (listened_ms / total_ms) >= 0.5):
                listen_type = 'listened'
            else:
                listen_type = 'partial'
            filepath = self._current_filepath
            if listen_type in ('listened', 'completed'):
                track = self.queue.get_current()
                if track and track.filepath == filepath:
                    track.play_count = getattr(track, 'play_count', 0) + 1
                    track.last_played = time.time()
                if hasattr(self.main_window, 'page_dashboard'):
                    QTimer.singleShot(500, lambda: self.main_window.page_dashboard.refresh_after_playback())
            worker = DBWorker(filepath, listen_type, listened_ms, total_ms)
            QThreadPool.globalInstance().start(worker)
            if listen_type in ('listened', 'completed'):
                if hasattr(self, '_current_artist') and hasattr(self, '_current_title'):
                    scrobble_worker = LastfmWorker(
                        action='scrobble',
                        artist=getattr(self, '_current_artist', ''),
                        title=getattr(self, '_current_title', ''),
                        album=getattr(self, '_current_album', ''),
                        timestamp=int(self._listen_start_time)
                    )
                    QThreadPool.globalInstance().start(scrobble_worker)
        except Exception as e:
            logging.debug(f"Error evaluando escucha anterior: {e}")
        finally:
            self._current_filepath = None
    def _start_tracking(self, track):
        self._current_filepath = track.filepath
        self._current_artist = track.artist
        self._current_title = track.title
        self._current_album = track.album
        self._listen_start_time = time.time()
        self._listen_start_pos_ms = 0
        self._current_total_ms = self.audio_engine.get_length() or getattr(track, 'duration', 0)
        if hasattr(self, '_lastfm_np_timer'):
            self._lastfm_np_timer.stop()
            self._lastfm_np_timer.deleteLater()
        self._lastfm_np_timer = QTimer(self)
        self._lastfm_np_timer.setSingleShot(True)
        artist = track.artist
        title = track.title
        album = track.album
        def _send_now_playing():
            now_playing_worker = LastfmWorker(
                action='now_playing',
                artist=artist,
                title=title,
                album=album
            )
            QThreadPool.globalInstance().start(now_playing_worker)
        self._lastfm_np_timer.timeout.connect(_send_now_playing)
        self._lastfm_np_timer.start(2000)
        if hasattr(self.main_window, 'sleep_timer_controller'):
            pass
    def _handle_gapless_transition(self, new_filepath):
        self._evaluate_previous_listen(was_natural_end=True)
        if hasattr(self.main_window, 'sleep_timer_controller'):
            self.main_window.sleep_timer_controller.evaluate_song_transition(was_natural_end=True)
        track = None
        search_start = self.queue.current_index
        if search_start < 0: 
            search_start = 0
        num_tracks = len(self.queue.tracks)
        if num_tracks > 0:
            for offset in range(num_tracks):
                idx = (search_start + offset) % num_tracks
                if offset == 0 and getattr(self.queue, 'repeat_mode', 0) != 2:
                    continue                                                          
                t = self.queue.tracks[idx]
                if t.filepath == new_filepath:
                    self.queue.current_index = idx
                    track = t
                    break
            if not track and self.queue.tracks[search_start].filepath == new_filepath:
                self.queue.current_index = search_start
                track = self.queue.tracks[search_start]
        if not track:
            return
        logging.info(f"Reproduciendo (Gapless): {track.title} - {track.artist}")
        self._listen_start_pos_ms = 0
        self._start_tracking(track)
        self.track_loaded.emit(track)
        self.main_window.playback_ui_controller.update_metadata_ui(track)
        is_playing = True
        if hasattr(self.main_window, 'sleep_timer_controller'):
            is_playing = not self.main_window.sleep_timer_controller.did_just_pause_playback()
        self.main_window.playback_ui_controller._update_play_icon(is_playing)
        duration_ms = getattr(track, 'duration', 0)
        def _update_smtc():
            try:
                self.main_window.smtc_controller.update_metadata(track)
                self.main_window.smtc_controller.update_timeline(0, duration_ms)
            except Exception as e:
                logging.debug(f"Error asíncrono SMTC: {e}")
        QTimer.singleShot(250, _update_smtc)
        if hasattr(self.main_window, 'lyrics_manager') and self.main_window.lyrics_manager:
            QTimer.singleShot(500, lambda: self.main_window.lyrics_manager.load(track))
        self.main_window.playback_ui_controller.update_favorite_icon_ui()
        self.main_window.system_tray_controller.update_discord_rpc() 
        QTimer.singleShot(20, self._refresh_views)
        if hasattr(self.main_window, 'queue_controller') and self.main_window.queue_controller:
            QTimer.singleShot(1500, self.main_window.queue_controller.update_gapless_preload)
        if getattr(self.main_window, 'remote_server', None):
            self.main_window.remote_server.broadcast_state()
    def _handle_crossfade_advance(self):
        if not self.queue.tracks:
            return
        if hasattr(self.main_window, 'sleep_timer_controller') and self.main_window.sleep_timer_controller.is_last_song():
            self.audio_engine._unlock_track_change()
            return
        self._evaluate_previous_listen(was_natural_end=True)
        if hasattr(self.main_window, 'sleep_timer_controller'):
            self.main_window.sleep_timer_controller.evaluate_song_transition(was_natural_end=True)
        self._current_filepath = None
        track = self.queue.get_next(manual=False)
        if not track:
            self.audio_engine.stop()
            return
        self.audio_engine.play_file(track.filepath, use_crossfade=True)
        crossfade_ms = self.audio_engine._crossfade_ms
        logging.info(f"Crossfade: Audio de '{track.title}' iniciado. UI se actualizará en {crossfade_ms}ms.")
        self._listen_start_pos_ms = 0
        self._start_tracking(track)
        QTimer.singleShot(crossfade_ms, lambda t=track: self._crossfade_ui_update(t))
    def _crossfade_ui_update(self, track):
        self.track_loaded.emit(track)
        self.main_window.playback_ui_controller.update_metadata_ui(track)
        is_playing = True
        if hasattr(self.main_window, 'sleep_timer_controller'):
            is_playing = not self.main_window.sleep_timer_controller.did_just_pause_playback()
        self.main_window.playback_ui_controller._update_play_icon(is_playing)
        duration_ms = getattr(track, 'duration', 0)
        def _update_smtc():
            try:
                self.main_window.smtc_controller.update_metadata(track)
                self.main_window.smtc_controller.update_timeline(0, duration_ms)
            except Exception as e:
                logging.debug(f"Error asíncrono SMTC: {e}")
        QTimer.singleShot(250, _update_smtc)
        if hasattr(self.main_window, 'lyrics_manager') and self.main_window.lyrics_manager:
            QTimer.singleShot(500, lambda: self.main_window.lyrics_manager.load(track))
        self.main_window.playback_ui_controller.update_favorite_icon_ui()
        self.main_window.system_tray_controller.update_discord_rpc()
        QTimer.singleShot(20, self._refresh_views)
        if hasattr(self.main_window, 'queue_controller') and self.main_window.queue_controller:
            QTimer.singleShot(1500, self.main_window.queue_controller.update_gapless_preload)
        if getattr(self.main_window, 'remote_server', None):
            self.main_window.remote_server.broadcast_state()
    def play_track(self, track, start_time=0):
        if not track:
            return False
        self._evaluate_previous_listen(was_natural_end=False)
        if not self.audio_engine.play_file(track.filepath, start_time=start_time, use_crossfade=False):
            return False
        self.audio_engine.restore_volume_after_crossfade()
        logging.info(f"Reproduciendo: {track.title} - {track.artist}")
        self._listen_start_pos_ms = start_time
        self._start_tracking(track)
        self.track_loaded.emit(track)
        self.main_window.playback_ui_controller.update_metadata_ui(track)
        is_playing = True
        if hasattr(self.main_window, 'sleep_timer_controller'):
            if self.main_window.sleep_timer_controller.did_just_pause_playback():
                is_playing = False
                self.audio_engine.pause()
        self.main_window.playback_ui_controller._update_play_icon(is_playing)
        duration_ms = getattr(track, 'duration', 0)
        def _update_smtc():
            try:
                self.main_window.smtc_controller.update_metadata(track)
                self.main_window.smtc_controller.update_timeline(start_time, duration_ms)
            except Exception as e:
                logging.debug(f"Error asíncrono SMTC: {e}")
        QTimer.singleShot(250, _update_smtc)
        if hasattr(self.main_window, 'lyrics_manager') and self.main_window.lyrics_manager:
            QTimer.singleShot(500, lambda: self.main_window.lyrics_manager.load(track))
        self.main_window.playback_ui_controller.update_favorite_icon_ui()
        self.main_window.system_tray_controller.update_discord_rpc() 
        QTimer.singleShot(20, self._refresh_views)
        if hasattr(self.main_window, 'queue_controller') and self.main_window.queue_controller:
            QTimer.singleShot(1500, self.main_window.queue_controller.update_gapless_preload)
        return True
    def _refresh_views(self):
        try:
            self.main_window.queue_controller.refresh_queue_ui()
            for view_name in ('list_album_tracks', 'list_artist_tracks', 'list_songs'):
                view = getattr(self.main_window, view_name, None)
                if view and view.isVisible():
                    view.viewport().update()
            if hasattr(self.main_window, 'page_playlists'):
                if hasattr(self.main_window.page_playlists, 'detail_page') and hasattr(self.main_window.page_playlists.detail_page, 'list_playlist_tracks') and getattr(self.main_window.page_playlists.detail_page.list_playlist_tracks, 'isVisible', lambda: False)():
                    self.main_window.page_playlists.detail_page.list_playlist_tracks.viewport().update()
                if hasattr(self.main_window.page_playlists, 'grid_page') and hasattr(self.main_window.page_playlists.grid_page, 'grid_view') and getattr(self.main_window.page_playlists.grid_page.grid_view, 'isVisible', lambda: False)():
                    self.main_window.page_playlists.grid_page.grid_view.viewport().update()
        except Exception as e:
            logging.debug(f"Error repintando vistas asíncronas: {e}")
    def toggle_play(self):
        if not self.queue.tracks: return
        if self.queue.current_index < 0:
            track = self.queue.get_next()
            if track:
                self.play_track(track)
            return
        state = self.audio_engine.get_state()
        if getattr(self.audio_engine, '_ghost_paused', False):
            self.audio_engine.resume()
            self.main_window.playback_ui_controller._update_play_icon(True)
        elif state == "Playing":
            self.audio_engine.pause()
            self.main_window.playback_ui_controller._update_play_icon(False)
        elif state == "Paused":
            self.audio_engine.resume()
            self.main_window.playback_ui_controller._update_play_icon(True)
        else:
            from settings_manager import settings
            last_time = settings.get('last_playback_time', 0)
            track = self.queue.get_current()
            if track:
                self.play_track(track, start_time=last_time)
            settings.set('last_playback_time', 0)
        self.main_window.system_tray_controller.update_discord_rpc()
    def set_volume(self, value):
        from settings_manager import settings
        self.volume = value
        self.audio_engine.set_volume(value)
        settings.set('volume', value)
        if hasattr(self.main_window, 'mini_volume_inline'):
            self.main_window.mini_volume_inline.setValue(value)
        if hasattr(self.main_window, 'mini_volume_popup'):
            self.main_window.mini_volume_popup.setValue(value)
        if getattr(self.main_window, 'remote_server', None):
            self.main_window.remote_server.broadcast_state()
    def next_track(self, manual=False):
        if not self.queue.tracks: return
        timer_paused = False
        if not manual:
            self._evaluate_previous_listen(was_natural_end=True)
            if hasattr(self.main_window, 'sleep_timer_controller'):
                timer_paused = self.main_window.sleep_timer_controller.evaluate_song_transition(was_natural_end=True)
            self._current_filepath = None                                       
        else:
            if hasattr(self.main_window, 'sleep_timer_controller'):
                self.main_window.sleep_timer_controller.evaluate_song_transition(was_natural_end=False)
        track = self.queue.get_next(manual=manual)
        if timer_paused:
            if hasattr(self.main_window, 'sleep_timer_controller'):
                self.main_window.sleep_timer_controller.did_just_pause_playback()               
            self.audio_engine.unload()                                                                      
            if track:
                self.track_loaded.emit(track)
                self.main_window.playback_ui_controller.update_metadata_ui(track)
                self.main_window.playback_ui_controller._update_play_icon(False)
                if hasattr(self.main_window, 'player_controller'):
                    self.main_window.player_controller.update_audio_time(0, getattr(track, 'duration', 0))
                duration_ms = getattr(track, 'duration', 0)
                from PyQt6.QtCore import QTimer
                def _update_smtc():
                    try:
                        self.main_window.smtc_controller.update_metadata(track)
                        self.main_window.smtc_controller.update_timeline(0, duration_ms)
                    except Exception as e:
                        import logging
                        logging.debug(f"Error asíncrono SMTC: {e}")
                QTimer.singleShot(250, _update_smtc)
                if hasattr(self.main_window, 'lyrics_manager') and self.main_window.lyrics_manager:
                    QTimer.singleShot(500, lambda: self.main_window.lyrics_manager.load(track))
                self.main_window.playback_ui_controller.update_favorite_icon_ui()
                self.main_window.system_tray_controller.update_discord_rpc() 
                QTimer.singleShot(20, self._refresh_views)
            return
        if track:
            self.play_track(track)
        else:
            self._evaluate_previous_listen(was_natural_end=not manual)
            self.audio_engine.stop()
            from settings_manager import settings
            if settings.get('rpc') and getattr(self.main_window, 'system_manager', None) and self.main_window.system_manager.discord_rpc:
                self.main_window.system_manager.discord_rpc.update_presence(None, False, 0)
            self.main_window.queue_controller.refresh_queue_ui()
    def prev_track(self, manual=False):
        if not self.queue.tracks: return
        position = 0
        if getattr(self.main_window, 'mini_slider', None):
            position = self.main_window.mini_slider.value()
        if manual and position > 30:
            self.audio_engine.set_position(0)
            return
        track = self.queue.get_prev()
        if track:
            self.play_track(track)
    def _handle_track_load_failed(self, filepath):
        for track in self.queue.tracks:
            if track.filepath == filepath:
                self.main_window.app_controller.remove_invalid_track(track)
                self.queue.remove_track(track)
                break
        self.next_track()