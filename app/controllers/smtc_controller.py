import logging
import os
from PyQt6.QtCore import QObject, pyqtSignal
class SMTCController(QObject):
    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    next_requested = pyqtSignal()
    prev_requested = pyqtSignal()
    def __init__(self, playback_controller):
        super().__init__()
        self.playback_controller = playback_controller
        self.smtc = None
        self._button_pressed_token = None
        self._init_winrt_smtc()
        if self.smtc:
            self.play_requested.connect(self._do_play)
            self.pause_requested.connect(self._do_pause)
            self.next_requested.connect(lambda: self.playback_controller.next_track(manual=True))
            self.prev_requested.connect(lambda: self.playback_controller.prev_track(manual=True))
    def _do_play(self):
        state = self.playback_controller.audio_engine.get_state()
        if state in ["Paused", "Stopped"]:
            self.playback_controller.toggle_play()
    def _do_pause(self):
        state = self.playback_controller.audio_engine.get_state()
        if state == "Playing":
            self.playback_controller.toggle_play()
    def _init_winrt_smtc(self):
        try:
            from winrt.windows.media.playback import MediaPlayer
            from winrt.windows.media import SystemMediaTransportControlsButton
            self.media_player = MediaPlayer()
            self.smtc = self.media_player.system_media_transport_controls
            self.smtc.is_play_enabled = True
            self.smtc.is_pause_enabled = True
            self.smtc.is_next_enabled = True
            self.smtc.is_previous_enabled = True
            self.smtc.display_updater.app_media_id = "Aiiko Music"
            self.smtc.display_updater.update()
            self._button_pressed_token = self.smtc.add_button_pressed(self._on_button_pressed)
            logging.info("SMTC Controller inicializado con exito (Integracion Windows nativa).")
        except Exception as e:
            logging.warning(f"No se pudo inicializar SMTC (¿SO no compatible?): {e}")
            self.smtc = None
    def _on_button_pressed(self, sender, args):
        try:
            from winrt.windows.media import SystemMediaTransportControlsButton
            btn = args.button
            if btn == SystemMediaTransportControlsButton.PLAY:
                self.play_requested.emit()
            elif btn == SystemMediaTransportControlsButton.PAUSE:
                self.pause_requested.emit()
            elif btn == SystemMediaTransportControlsButton.NEXT:
                self.next_requested.emit()
            elif btn == SystemMediaTransportControlsButton.PREVIOUS:
                self.prev_requested.emit()
        except Exception as e:
            logging.error(f"Error procesando boton SMTC: {e}")
    def update_metadata(self, track):
        if not self.smtc or not track: return
        try:
            from winrt.windows.media import MediaPlaybackType
            import os
            updater = self.smtc.display_updater
            updater.type = MediaPlaybackType.MUSIC
            from core.language_manager import tr
            title = track.title or "Desconocido"
            if title in ("Desconocido", "Artista Desconocido", "Álbum Desconocido"):
                title = tr(title)
            artist = track.artist or "Desconocido"
            if artist in ("Desconocido", "Artista Desconocido", "Álbum Desconocido"):
                artist = tr(artist)
            updater.music_properties.title = title
            updater.music_properties.artist = artist
            updater.update()
            if track.cover_path and os.path.exists(track.cover_path):
                thumbnail_path = os.path.abspath(track.cover_path)
            else:
                from config import ICON_FILE
                thumbnail_path = ICON_FILE if os.path.exists(ICON_FILE) else None
            if thumbnail_path:
                import threading
                import asyncio
                def _async_thumbnail_update():
                    import pythoncom
                    pythoncom.CoInitialize() 
                    async def run():
                        try:
                            from winrt.windows.storage.streams import InMemoryRandomAccessStream, DataWriter, RandomAccessStreamReference
                            with open(thumbnail_path, 'rb') as f:
                                data = f.read()
                            stream = InMemoryRandomAccessStream()
                            writer = DataWriter(stream)
                            writer.write_bytes(data)
                            await writer.store_async()
                            writer.detach_stream()
                            stream.seek(0)
                            updater.thumbnail = RandomAccessStreamReference.create_from_stream(stream)
                            updater.update()
                        except Exception as e:
                            logging.error(f"Error cargando thumbnail en memoria SMTC: {e}")
                    asyncio.run(run())
                    pythoncom.CoUninitialize()
                threading.Thread(target=_async_thumbnail_update, daemon=True).start()
            else:
                updater.thumbnail = None
                updater.update()
        except Exception as e:
            logging.error(f"Error actualizando metadatos SMTC: {e}")
    def update_playback_status(self, is_playing):
        if not self.smtc: return
        try:
            from winrt.windows.media import MediaPlaybackStatus
            if is_playing:
                self.smtc.playback_status = MediaPlaybackStatus.PLAYING
            else:
                self.smtc.playback_status = MediaPlaybackStatus.PAUSED
        except Exception as e:
            logging.error(f"Error actualizando estado SMTC: {e}")
    def update_timeline(self, current_ms, total_ms):
        if not self.smtc: return
        try:
            from winrt.windows.media import SystemMediaTransportControlsTimelineProperties
            from datetime import timedelta
            timeline = SystemMediaTransportControlsTimelineProperties()
            timeline.start_time = timedelta(0)
            timeline.end_time = timedelta(milliseconds=total_ms)
            timeline.position = timedelta(milliseconds=current_ms)
            timeline.min_seek_time = timedelta(0)
            timeline.max_seek_time = timedelta(milliseconds=total_ms)
            self.smtc.update_timeline_properties(timeline)
        except Exception as e:
            logging.error(f"Error actualizando timeline SMTC: {e}")
    def cleanup(self):
        if self.smtc and self._button_pressed_token:
            try:
                self.smtc.remove_button_pressed(self._button_pressed_token)
            except: pass
        if hasattr(self, 'media_player') and hasattr(self.media_player, 'close'):
            try:
                self.media_player.close()
            except: pass