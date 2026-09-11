import time
import logging
from PyQt6.QtGui import QColor
from config import ICON_TIMER
from settings_manager import settings
from services.discord_service import RPC_AVAILABLE
from PyQt6.QtCore import QRunnable, QThreadPool
from core.language_manager import tr
class RPCWorker(QRunnable):
    def __init__(self, rpc_manager, track, is_playing, length_ms, position_ms):
        super().__init__()
        self.rpc_manager = rpc_manager
        self.track = track
        self.is_playing = is_playing
        self.length_ms = length_ms
        self.position_ms = position_ms
    def run(self):
        try:
            self.rpc_manager.update_presence(self.track, self.is_playing, self.length_ms, self.position_ms)
        except Exception as e:
            logging.debug(f"Error asíncrono en Discord RPC: {e}")
class SystemTrayController:
    def __init__(self, main_window):
        self.mw = main_window
    def toggle_floating_player(self):
        tracks = self.mw.queue.tracks
        idx = self.mw.queue.current_index
        current_track = tracks[idx] if (tracks and 0 <= idx < len(tracks)) else None
        self.mw.system_manager.toggle_floating_player(current_track, self.mw.audio_engine.is_playing())
    def restore_from_floating(self):
        self.mw.system_manager.restore_from_floating()
    def toggle_discord_rpc(self, checked):
        if not RPC_AVAILABLE:
            return
        settings.set('rpc', checked)
        settings.save()
        if checked:
            if self.mw.system_manager.connect_rpc():
                self.update_discord_rpc()
            else:
                self.mw.switch_rpc.blockSignals(True)
                self.mw.switch_rpc.setChecked(False)
                self.mw.switch_rpc.blockSignals(False)
                settings.set('rpc', False)
        else:
            self.mw.system_manager.disconnect_rpc()
    def update_discord_rpc(self):
        if not settings.get('rpc') or not self.mw.system_manager.discord_rpc:
            return
        if 0 <= self.mw.queue.current_index < len(self.mw.queue.tracks):
            track = self.mw.queue.tracks[self.mw.queue.current_index]
            is_playing = self.mw.audio_engine.is_playing()
            length_ms = self.mw.audio_engine.get_length()
            position_ms = self.mw.audio_engine.get_position()
            worker = RPCWorker(self.mw.system_manager.discord_rpc, track, is_playing, length_ms, position_ms)
            QThreadPool.globalInstance().start(worker)
        else:
            worker = RPCWorker(self.mw.system_manager.discord_rpc, None, False, 0, 0)
            QThreadPool.globalInstance().start(worker)
    def perform_shutdown(self):
        logging.info("Ejecutando Guardado Maestro al cerrar...")
        self.mw.settings_sync.sync_ui_to_settings()
        settings.save(sync=True)
        logging.info("Guardado Maestro completado exitosamente.")
        self.mw.audio_engine.stop()
        self.mw.system_manager.shutdown()
        if hasattr(self.mw, 'image_loader'):
            self.mw.image_loader.running = False
        if hasattr(self.mw, 'fetcher') and self.mw.fetcher is not None and self.mw.fetcher.isRunning():
            self.mw.fetcher.running = False
        if hasattr(self.mw, 'library_manager'):
            self.mw.library_manager.stop_all()
        if hasattr(self.mw, 'lyrics_manager') and getattr(self.mw, 'lyrics_manager', None) is not None:
            if hasattr(self.mw.lyrics_manager, 'translation_thread') and getattr(self.mw.lyrics_manager, 'translation_thread', None) is not None and self.mw.lyrics_manager.translation_thread.isRunning():
                self.mw.lyrics_manager.translation_thread.stop()