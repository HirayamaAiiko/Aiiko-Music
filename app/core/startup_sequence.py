import time
import logging
from PyQt6.QtCore import QObject, QTimer
from settings_manager import settings
class StartupSequence(QObject):
    def __init__(self, main_window, app_start_time):
        super().__init__(main_window)
        self.main_window = main_window
        self.app_start_time = app_start_time
    def execute_delayed_startup(self):
        try:
            logging.info("Ejecutando startup diferido (Fase 1)...")
            self.main_window.settings_sync.apply_settings_to_ui()
            if not getattr(self.main_window.page_settings, 'is_placeholder', False):
                self.main_window.settings_ui_controller.init_audio_settings_ui()
            self.main_window.library_sync_controller.load_library()
            if settings.get('crossfade_enabled', False):
                self.main_window.audio_engine.set_crossfade(settings.get('crossfade_seconds', 3))
            if hasattr(self.main_window, 'theme_controller'):
                self.main_window.theme_controller.apply_theme(full_refresh=True)
            if hasattr(self.main_window, 'playback_ui_controller'):
                self.main_window.playback_ui_controller._update_eq_icons()
            elapsed = time.time() - self.app_start_time
            logging.info(f"ARRANQUE FASE 1 COMPLETADO EN {elapsed:.2f} segundos")
            print(f"\nAiiko Music arrancó en {elapsed:.2f} segundos \n")
            def phase_2():
                try:
                    logging.info("Ejecutando startup Fase 2 (Tareas de fondo)...")
                    if not settings.get('file_associations_registered', False):
                        import threading
                        def _do_register():
                            from core.file_association import register_file_associations
                            if register_file_associations():
                                settings.set('file_associations_registered', True)
                        threading.Thread(target=_do_register, daemon=True).start()
                    if settings.get('auto_scan'):
                        self.main_window.library_sync_controller.start_background_scan()
                    else:
                        self.main_window.library_manager.start_file_watcher()
                        self.main_window.library_manager.start_diff_scan()
                    self.main_window.system_manager.init_global_hotkeys()
                    if hasattr(self.main_window, 'page_dashboard'):
                        self.main_window.page_dashboard.refresh()
                except Exception as e2:
                    logging.error(f"Error en phase_2: {e2}")
            QTimer.singleShot(1500, phase_2)
            def phase_3():
                try:
                    logging.info("Ejecutando startup Fase 3 (Servicios externos)...")
                    import threading
                    from services.lastfm_service import LastfmService
                    threading.Thread(target=LastfmService.flush_offline_cache, daemon=True).start()
                    if settings.get('remote_enabled', False):
                        from core.remote_server import RemoteServer
                        name = settings.get('remote_name', 'Aiiko Server')
                        self.main_window.remote_server = RemoteServer(self.main_window, port=8080, server_name=name)
                        self.main_window.remote_server.start()
                except Exception as e3:
                    logging.error(f"Error en phase_3: {e3}")
            QTimer.singleShot(3500, phase_3)
        except Exception as e:
            logging.error(f"Error in delayed_startup pt 1: {e}", exc_info=True)
        try:
            if self.main_window.ext_filepath:
                if hasattr(self.main_window, 'queue') and self.main_window.queue.tracks:
                    t = self.main_window.queue.tracks[0]
                    self.main_window.playback_controller._listen_start_pos_ms = 0
                    self.main_window.playback_controller._start_tracking(t)
                    self.main_window.playback_ui_controller.update_metadata_ui(t)
                    self.main_window.playback_ui_controller._update_play_icon(True)
                    if getattr(self.main_window, 'lyrics_manager', None):
                        self.main_window.lyrics_manager.load(t)
                    self.main_window.playback_ui_controller.update_favorite_icon_ui()
                    self.main_window.system_tray_controller.update_discord_rpc()
                    QTimer.singleShot(20, self.main_window.playback_controller._refresh_views)
                    if hasattr(self.main_window, 'queue_controller') and self.main_window.queue_controller:
                        QTimer.singleShot(1500, self.main_window.queue_controller.update_gapless_preload)
                    if getattr(self.main_window, 'remote_server', None):
                        self.main_window.remote_server.broadcast_state()
        except Exception as e:
            logging.error(f"Error in delayed_startup pt 2: {e}", exc_info=True)