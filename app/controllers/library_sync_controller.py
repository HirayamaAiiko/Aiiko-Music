import logging
import os
from PyQt6.QtCore import QTimer, Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QFont, QPen, QPainterPath, QRadialGradient, QFontMetrics
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect, QApplication
from settings_manager import settings
from core.notification_manager import notify
import theme_manager
from core.language_manager import tr
from UI.dialogs.scan_progress_dialog import ScanProgressDialog
class LibrarySyncController:
    def __init__(self, main_window):
        self.mw = main_window
        self._pending_new_tracks = []
        self._pending_removed_names = []
        self._new_track_timer = QTimer(main_window)
        self._new_track_timer.setSingleShot(True)
        self._new_track_timer.setInterval(3000)
        self._new_track_timer.timeout.connect(self._flush_new_tracks_notification)
        self._removed_track_timer = QTimer(main_window)
        self._removed_track_timer.setSingleShot(True)
        self._removed_track_timer.setInterval(3000)
        self._removed_track_timer.timeout.connect(self._flush_removed_tracks_notification)
    def load_library(self):
        self.mw.library_manager.load_library()
    def on_library_loaded(self, library):
        mw = self.mw
        mw.library = library
        if getattr(mw, 'ext_filepath', None):
            mw.track_model.set_tracks(list(mw.library))
            if hasattr(mw, 'queue_model'):
                mw.queue_model.set_tracks(list(mw.queue.tracks))
                mw.queue_model.update_current_index(mw.queue.current_index)
            mw.library_controller.refresh_library_views()
            return
        last_paths = settings.get('last_queue_paths', [])
        last_idx = settings.get('last_queue_index', -1)
        if last_paths:
            path_to_track = {t.filepath: t for t in mw.library}
            mw.queue.tracks = []
            for p in last_paths:
                if p in path_to_track:
                    mw.queue.tracks.append(path_to_track[p])
            mw.queue.current_index = last_idx if mw.queue.tracks else -1
            if mw.queue.current_index >= len(mw.queue.tracks):
                mw.queue.current_index = 0 if mw.queue.tracks else -1
            mw.queue.is_shuffled = settings.get('is_shuffled', False)
            mw.queue.set_repeat_mode(settings.get('repeat_mode', 0))
            if hasattr(mw, 'playback_ui_controller'):
                mw.playback_ui_controller._update_shuffle_icon()
                mw.playback_ui_controller._update_repeat_icon()
            if mw.queue.current_index >= 0 and mw.queue.tracks:
                t = mw.queue.tracks[mw.queue.current_index]
                if hasattr(mw, 'audio_engine'):
                    mw.audio_engine.initialize()
                last_time = settings.get('last_playback_time', 0)
                if hasattr(mw, 'playback_ui_controller'):
                    mw.playback_ui_controller._update_play_icon(False)
                    mw.playback_ui_controller.update_metadata_ui(t)
                if last_time > 0 and hasattr(mw, 'player_controller'):
                    mw.player_controller.update_audio_time(last_time, t.duration if getattr(t, 'duration', 0) > 0 else 0)
                if getattr(mw, 'lyrics_manager', None):
                    mw.lyrics_manager.load(t)
        else:
            mw.queue.tracks = list(mw.library)
        mw.track_model.set_tracks(list(mw.library))
        if hasattr(mw, 'queue_model'):
            mw.queue_model.set_tracks(list(mw.queue.tracks))
            mw.queue_model.update_current_index(mw.queue.current_index)
        mw.library_controller.refresh_library_views()
    def update_library_cache(self):
        self.mw.library_manager.update_library_cache()
    def start_background_scan(self, force_full=False, show_dialog=True, specific_folders=None):
        if not self.mw.library_manager.start_background_scan(force_full=force_full, specific_folders=specific_folders):
            notify.warning(tr("Escaneo en progreso"), tr("La biblioteca ya se está escaneando."))
            return
        if show_dialog:
            self._scan_dialog = ScanProgressDialog(self.mw)
            self._scan_dialog.show()
            if hasattr(self.mw.library_manager, 'scanner') and self.mw.library_manager.scanner:
                scanner = self.mw.library_manager.scanner
                scanner.current_file.connect(
                    lambda p: self._scan_dialog.update_details(p) if hasattr(self, '_scan_dialog') and self._scan_dialog else None
                )
                scanner.progress_percent.connect(
                    lambda pct: self._scan_dialog.update_progress(pct) if hasattr(self, '_scan_dialog') and self._scan_dialog else None
                )
        self._scan_timeout = QTimer(self.mw)
        self._scan_timeout.setSingleShot(True)
        self._scan_timeout.setInterval(120000)
        self._scan_timeout.timeout.connect(self._force_close_scan_dialog)
        self._scan_timeout.start()
    def on_scan_batch(self, tracks_batch):
        if not tracks_batch:
            return
        if hasattr(self, '_scan_dialog') and self._scan_dialog:
            self._scan_dialog.update_details(tracks_batch[-1].filepath)
        existing_paths = {t.filepath for t in self.mw.library}
        new_tracks = [t for t in tracks_batch if t.filepath not in existing_paths]
        if new_tracks:
            self.mw.library.extend(new_tracks)
            if not getattr(self.mw, 'ext_filepath', None):
                self.mw.queue.tracks = list(self.mw.library)
            self.mw.track_model.add_tracks(new_tracks)
    def on_scan_finished(self):
        if hasattr(self, '_scan_timeout') and self._scan_timeout:
            self._scan_timeout.stop()
            self._scan_timeout = None
        if hasattr(self, '_scan_dialog') and self._scan_dialog:
            self._scan_dialog.accept()
            self._scan_dialog = None
        self.mw.library_controller.refresh_library_views()
        notify.success(tr("Escaneo Completo"), tr("La biblioteca ha sido actualizada exitosamente."))
    def _force_close_scan_dialog(self):
        logging.warning("Scan timeout reached — forcing dialog close.")
        if hasattr(self, '_scan_dialog') and self._scan_dialog:
            self._scan_dialog.accept()
            self._scan_dialog = None
        self._scan_timeout = None
        notify.warning(tr("Escaneo Interrumpido"), tr("El escaneo tardó demasiado o se interrumpió."))
    def on_watcher_new_track(self, track):
        mw = self.mw
        if not any(t.filepath == track.filepath for t in mw.library):
            mw.library.append(track)
            logging.info(f"[LibSync] Track añadido a mw.library: '{track.title}'")
        mw.queue.tracks.append(track)
        mw.library_controller.refresh_library_views()
        if hasattr(mw, 'queue_model'):
            mw.queue_model.set_tracks(list(mw.queue.tracks))
            mw.queue_model.update_current_index(mw.queue.current_index)
        self._pending_new_tracks.append(track)
        self._new_track_timer.start()                           
    def on_watcher_track_removed(self, filepath):
        mw = self.mw
        track = next((t for t in mw.library if t.filepath == filepath), None)
        if not track:
            return
        track_name = f"{track.title} — {track.artist}"
        if track in mw.library:
            mw.library.remove(track)
        if track in mw.queue.tracks:
            idx = mw.queue.tracks.index(track)
            mw.queue.tracks.remove(track)
            if idx < mw.queue.current_index:
                mw.queue.current_index -= 1
            elif idx == mw.queue.current_index:
                mw.queue.current_index = min(mw.queue.current_index, len(mw.queue.tracks) - 1)
        mw.library_controller.refresh_library_views()
        if getattr(mw, 'queue_is_open', False):
            mw.refresh_queue_ui()
        self._pending_removed_names.append(track_name)
        self._removed_track_timer.start()
    def _flush_new_tracks_notification(self):
        count = len(self._pending_new_tracks)
        if count == 0:
            return
        if count == 1:
            t = self._pending_new_tracks[0]
            notify.success(tr("Nueva canción detectada"), f"{t.title} — {t.artist}")
        else:
            notify.success(tr("Canciones nuevas detectadas"), tr("Se añadieron {count} canciones a la biblioteca.").format(count=count))
        self._pending_new_tracks.clear()
    def _flush_removed_tracks_notification(self):
        count = len(self._pending_removed_names)
        if count == 0:
            return
        if count == 1:
            notify.warning(tr("Canción eliminada"), self._pending_removed_names[0])
        else:
            notify.warning(tr("Canciones eliminadas"), tr("Se eliminaron {count} canciones de la biblioteca.").format(count=count))
        self._pending_removed_names.clear()
    def on_diff_scan_new_tracks(self, tracks):
        mw = self.mw
        for track in tracks:
            if not any(t.filepath == track.filepath for t in mw.library):
                mw.library.append(track)
            if track not in mw.queue.tracks:
                mw.queue.tracks.append(track)
    def on_diff_scan_removed_tracks(self, filepaths):
        mw = self.mw
        for fp in filepaths:
            track = next((t for t in mw.library if t.filepath == fp), None)
            if track:
                if track in mw.library:
                    mw.library.remove(track)
                if track in mw.queue.tracks:
                    idx = mw.queue.tracks.index(track)
                    mw.queue.tracks.remove(track)
                    if idx < mw.queue.current_index:
                        mw.queue.current_index -= 1
    def on_diff_scan_finished(self, new_count, removed_count):
        mw = self.mw
        if new_count == 0 and removed_count == 0:
            return                              
        mw.library_controller.refresh_library_views()
        if hasattr(mw, 'queue_model'):
            mw.queue_model.set_tracks(list(mw.queue.tracks))
            mw.queue_model.update_current_index(mw.queue.current_index)
        parts = []
        if new_count > 0:
            parts.append(tr("{count} nuevas").format(count=new_count) if new_count > 1 else tr("1 nueva"))
        if removed_count > 0:
            parts.append(tr("{count} eliminadas").format(count=removed_count) if removed_count > 1 else tr("1 eliminada"))
        msg = ", ".join(parts)
        notify.success(tr("Biblioteca sincronizada"), msg)
    def repair_cover_cache(self):
        if notify.confirm(tr('Confirmar'), tr('¿Deseas limpiar la caché y volver a extraer TODAS las carátulas?\n\nEsto puede tardar unos minutos.')):
            self.mw.btn_repair_cache.setEnabled(False)
            self.mw.btn_repair_cache.setText(tr("Reparando..."))
            self.mw.library_manager.repair_cover_cache()
    def on_repair_progress(self, current, total):
        if hasattr(self.mw, 'btn_repair_cache') and not self.mw.btn_repair_cache.isEnabled():
            self.mw.btn_repair_cache.setText(tr("Reparando... {current}/{total}").format(current=current, total=total))
    def on_repair_finished(self):
        mw = self.mw
        if hasattr(mw, 'btn_repair_cache'):
            mw.btn_repair_cache.setEnabled(True)
            mw.btn_repair_cache.setText(tr("Limpiar y Reparar"))
        if hasattr(mw, 'btn_repair_missing'):
            mw.btn_repair_missing.setEnabled(True)
            mw.btn_repair_missing.setText(tr("Reparar Faltantes"))
        mw.library_controller.refresh_library_views()
        notify.success(tr("Reparación Completa"), tr("El proceso de reparación ha finalizado correctamente."))
        if mw.queue.current_index >= 0 and mw.queue.tracks:
            mw.playback_ui_controller.update_metadata_ui(mw.queue.tracks[mw.queue.current_index])
    def repair_missing_covers(self):
        if notify.confirm(tr('Confirmar'), tr('¿Deseas buscar las canciones que no tienen carátula y extraerlas?\n\nEsto no borrará la caché existente.')):
            self.mw.btn_repair_missing.setEnabled(False)
            self.mw.btn_repair_missing.setText(tr("Buscando..."))
            if hasattr(self.mw, 'btn_repair_cache'):
                self.mw.btn_repair_cache.setEnabled(False)
            self.mw.library_manager.repair_missing_covers()
    def repair_artist_cache(self):
        if notify.confirm(tr('Confirmar'), tr('¿Deseas limpiar la caché de artistas y descargarlos todos de nuevo?')):
            self.mw.btn_repair_artist_cache.setEnabled(False)
            self.mw.btn_repair_artist_cache.setText(tr("Limpiando..."))
            self.mw.library_manager.repair_artist_cache()
    def on_batch_fetcher_progress(self, current, total, name):
        if hasattr(self.mw, 'btn_repair_artist_cache') and not self.mw.btn_repair_artist_cache.isEnabled():
            self.mw.btn_repair_artist_cache.setText(tr("Descargando... {current}/{total}").format(current=current, total=total))
    def on_batch_fetcher_finished(self):
        if hasattr(self.mw, 'btn_repair_artist_cache'):
            self.mw.btn_repair_artist_cache.setEnabled(True)
            self.mw.btn_repair_artist_cache.setText(tr("Recargar Info Artistas"))
        self.mw.library_controller.refresh_library_views()
    def on_audio_error(self, err_msg):
        logging.warning(err_msg)
        notify.error(tr("Error de Reproducción"), err_msg)
        if self.mw.queue.tracks and 0 <= self.mw.queue.current_index < len(self.mw.queue.tracks):
            self.mw.app_controller.remove_invalid_track(self.mw.queue.tracks[self.mw.queue.current_index])
            self.mw.queue.current_index -= 1
            self.mw.playback_controller.next_track()