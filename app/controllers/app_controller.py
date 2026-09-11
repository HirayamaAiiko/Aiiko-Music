import os
import logging
from PyQt6.QtCore import QObject, Qt, QTimer, QRunnable, QThreadPool, pyqtSignal, QThread
from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from settings_manager import settings
from services.metadata_editor import MetadataEditorService
from database import save_batch
class MetadataWriterWorker(QThread):
    finished_write = pyqtSignal(bool, str)
    def __init__(self, track, changed_metadata, new_cover_path, parent=None):
        super().__init__(parent)
        self.track = track
        self.changed_metadata = changed_metadata
        self.new_cover_path = new_cover_path
    def run(self):
        try:
            MetadataEditorService.save_metadata(self.track.filepath, self.changed_metadata, self.new_cover_path)
            if 'title' in self.changed_metadata: self.track.title = self.changed_metadata['title']
            if 'artist' in self.changed_metadata: self.track.artist = self.changed_metadata['artist']
            if 'album' in self.changed_metadata: self.track.album = self.changed_metadata['album']
            if 'year' in self.changed_metadata: self.track.year = self.changed_metadata['year']
            if 'genre' in self.changed_metadata: self.track.genre = self.changed_metadata['genre']
            if os.path.exists(self.track.filepath):
                self.track.mtime = os.path.getmtime(self.track.filepath)
            save_batch([self.track])
            if self.new_cover_path:
                import hashlib
                from config import CACHE_DIR
                with open(self.new_cover_path, 'rb') as f:
                    img_data = f.read()
                new_hash = hashlib.md5(img_data).hexdigest()
                new_cache_path = os.path.join(CACHE_DIR, f"{new_hash}.jpg")
                if not os.path.exists(new_cache_path):
                    with open(new_cache_path, 'wb') as f:
                        f.write(img_data)
                self.track.cover_path = new_cache_path
                save_batch([self.track])
            self.finished_write.emit(True, "")
        except Exception as e:
            logging.error(f"Error asíncrono guardando metadatos: {e}")
            self.finished_write.emit(False, str(e))
class AppController(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
    def toggle_favorite(self):
        if self.mw.queue.current_index < 0 or not self.mw.queue.tracks:
            return
        track = self.mw.queue.tracks[self.mw.queue.current_index]
        favs = settings.get('favorites', [])
        if track.filepath in favs:
            favs.remove(track.filepath)
        else:
            favs.append(track.filepath)
        settings.set('favorites', favs)
        settings.save()
        self.mw.playback_ui_controller.update_favorite_icon_ui()
        self.mw.library_controller.refresh_favorites_view()
    def create_new_playlist(self):
        from UI.dialogs.playlist_create_dialog import PlaylistCreateDialog
        from core.notification_manager import notify
        dlg = PlaylistCreateDialog(parent=self.mw)
        if dlg.exec():
            text = dlg.get_name()
            playlists = settings.get('playlists', {})
            if text in playlists:
                notify.warning("Error", "Ya existe una playlist con ese nombre.")
                return
            playlists[text] = []
            settings.set('playlists', playlists)
            settings.save()
            self.mw.library_controller.refresh_playlists_list()
            self.mw.library_controller.refresh_artist_related_playlists()
    def add_to_playlist(self, playlist_name, track_or_tracks, batch_mode=False):
        playlists = settings.get('playlists', {})
        added = False
        tracks = track_or_tracks if isinstance(track_or_tracks, list) else [track_or_tracks]
        if playlist_name in playlists:
            for track in tracks:
                if track.filepath not in playlists[playlist_name]:
                    playlists[playlist_name].append(track.filepath)
                    added = True
        if added:
            settings.set('playlists', playlists)
            if not batch_mode:
                settings.save()
                self.mw.library_controller.refresh_playlists_list()
                self.mw.library_controller.refresh_artist_related_playlists()
    def remove_from_playlist(self, playlist_name, filepath):
        playlists = settings.get('playlists', {})
        if playlist_name in playlists and filepath in playlists[playlist_name]:
            playlists[playlist_name].remove(filepath)
            settings.set('playlists', playlists)
            settings.save()
            self.mw.library_controller.refresh_playlists_list()
            self.mw.library_controller.refresh_artist_related_playlists()
    def add_folder(self):
        from core.language_manager import tr
        from core.notification_manager import notify
        import os
        directory = QFileDialog.getExistingDirectory(self.mw, tr("Seleccionar Carpeta"))
        if not directory:
            return
        folders = settings.get('folders', [])
        dir_norm = os.path.normpath(os.path.abspath(directory))
        if os.name == 'nt':
            dir_norm = dir_norm.lower()
        for existing in folders:
            exist_norm = os.path.normpath(os.path.abspath(existing))
            if os.name == 'nt':
                exist_norm = exist_norm.lower()
            if dir_norm == exist_norm:
                notify.warning(tr("Carpeta duplicada"), tr("Esta carpeta ya está en tu biblioteca."))
                return
            if dir_norm.startswith(exist_norm + os.sep):
                notify.warning(tr("Subcarpeta detectada"), tr("Esta ruta ya está incluida dentro de una carpeta existente."))
                return
            if exist_norm.startswith(dir_norm + os.sep):
                notify.warning(tr("Conflicto"), tr("Ya tienes una subcarpeta de esta ruta en la biblioteca. Elimínala primero."))
                return
        folders.append(directory)
        settings.set('folders', folders)
        self.mw.list_folders.addItem(directory)
        settings.save()
        self.mw.library_sync_controller.start_background_scan(specific_folders=[directory])
        self.mw.library_manager.start_file_watcher()
    def remove_folder(self):
        selected = self.mw.list_folders.currentItem()
        if selected:
            folder = selected.text()
            folders = settings.get('folders', [])
            if folder in folders:
                folders.remove(folder)
                settings.set('folders', folders)
            self.mw.list_folders.takeItem(self.mw.list_folders.row(selected))
            settings.save()
            current_track = None
            if self.mw.queue.tracks and 0 <= self.mw.queue.current_index < len(self.mw.queue.tracks):
                current_track = self.mw.queue.tracks[self.mw.queue.current_index]
                if current_track.filepath.startswith(folder):
                    self.mw.audio_engine.stop()
                    current_track = None
            self.mw.library = [t for t in self.mw.library if not t.filepath.startswith(folder)]
            self.mw.queue.tracks = list(self.mw.library)
            if current_track in self.mw.queue.tracks:
                self.mw.queue.current_index = self.mw.queue.tracks.index(current_track)
            else:
                self.mw.queue.current_index = -1
                self.mw.audio_engine.stop()
            self.mw.library_sync_controller.update_library_cache()
            self.mw.library_controller.refresh_library_views()
            self.mw.library_manager.start_file_watcher()
    def toggle_favorite_track(self, track=None):
        if not track or isinstance(track, bool):
            if self.mw.queue.current_index < 0 or not self.mw.queue.tracks:
                return
            track = self.mw.queue.tracks[self.mw.queue.current_index]
        self.toggle_favorite_tracks([track])
    def toggle_favorite_tracks(self, tracks, force_state=None):
        if not tracks: return
        favs = settings.get('favorites', [])
        changed = False
        for track in tracks:
            is_fav = track.filepath in favs
            if force_state is True and not is_fav:
                favs.append(track.filepath)
                changed = True
            elif force_state is False and is_fav:
                favs.remove(track.filepath)
                changed = True
            elif force_state is None:
                if is_fav: favs.remove(track.filepath)
                else: favs.append(track.filepath)
                changed = True
        if changed:
            settings.set('favorites', favs)
            settings.save()
            self.mw.playback_ui_controller.update_favorite_icon_ui()
            self.mw.library_controller.refresh_favorites_view()
    def remove_invalid_track(self, track, add_to_blacklist=False):
        self.remove_invalid_tracks([track], add_to_blacklist)
    def remove_invalid_tracks(self, tracks, add_to_blacklist=False):
        for track in tracks:
            if track in self.mw.library:
                self.mw.library.remove(track)
            while track in self.mw.queue.tracks:
                self.mw.queue.remove_track(track)
            for model_name in ['artist_tracks_model', 'album_tracks_model', 'top_tracks_model']:
                if hasattr(self.mw, model_name):
                    model = getattr(self.mw, model_name)
                    if hasattr(model, 'tracks') and track in model.tracks:
                        model.tracks.remove(track)
                        model.layoutChanged.emit()
        from PyQt6.QtCore import QThread
        class RemovalThread(QThread):
            def __init__(self, filepaths, blacklist, parent=None):
                super().__init__(parent)
                self.filepaths = filepaths
                self.blacklist = blacklist
            def run(self):
                from database import get_db_connection, add_ignored_track
                from contextlib import closing
                try:
                    with closing(get_db_connection()) as conn:
                        with conn:
                            c = conn.cursor()
                            for fp in self.filepaths:
                                if self.blacklist:
                                    c.execute("INSERT OR IGNORE INTO ignored_tracks (filepath) VALUES (?)", (fp,))
                                c.execute("DELETE FROM tracks WHERE filepath = ?", (fp,))
                except Exception as e:
                    import logging
                    logging.error(f"Error de base de datos al eliminar lote: {e}")
        filepaths = [t.filepath for t in tracks]
        removal_thread = RemovalThread(filepaths, add_to_blacklist, parent=self.mw)
        if not hasattr(self.mw, '_removal_threads'):
            self.mw._removal_threads = []
        self.mw._removal_threads.append(removal_thread)
        def _on_removal_finished(t=removal_thread):
            self.mw.library_controller.refresh_library_views()
            t.deleteLater()
            if t in self.mw._removal_threads:
                self.mw._removal_threads.remove(t)
        removal_thread.finished.connect(_on_removal_finished)
        removal_thread.start()
    def edit_track_metadata(self, track):
        from UI.dialogs.metadata_editor_dialog import MetadataEditorDialog
        from core.notification_manager import notify
        def _show_dialog():
            dialog = MetadataEditorDialog(track, self.mw)
            def on_saved(changed_metadata, new_cover_path):
                if not changed_metadata and not new_cover_path:
                    return
                was_playing = False
                position = 0
                is_current = False
                if self.mw.queue.tracks and 0 <= self.mw.queue.current_index < len(self.mw.queue.tracks):
                    current_track = self.mw.queue.tracks[self.mw.queue.current_index]
                    if current_track.filepath == track.filepath:
                        is_current = True
                        was_playing = self.mw.audio_engine.is_playing()
                        position = self.mw.audio_engine.get_position()
                        self.mw.audio_engine.unload()
                def _start_worker():
                    old_cover = track.cover_path
                    worker = MetadataWriterWorker(track, changed_metadata, new_cover_path, parent=self.mw)
                    def on_writer_finished(success, error_msg):
                        if success:
                            if new_cover_path and old_cover:
                                keys_to_purge = [k for k in self.mw.image_cache.pixmap_cache if old_cover in k]
                                for k in keys_to_purge:
                                    del self.mw.image_cache.pixmap_cache[k]
                                if self.mw.image_cache.image_loader and hasattr(self.mw.image_cache.image_loader, 'seen'):
                                    tasks_to_clear = [t for t in self.mw.image_cache.image_loader.seen if old_cover in t]
                                    for t in tasks_to_clear:
                                        self.mw.image_cache.image_loader.seen.discard(t)
                            self.mw.library_controller.refresh_library_views()
                            notify.success("Guardado", f"Metadatos actualizados: {track.title}")
                        else:
                            logging.error(f"Error editando metadatos: {error_msg}")
                            notify.error("Error", "No se pudieron guardar los metadatos. ¿El archivo es de solo lectura?")
                        if is_current:
                            current = self.mw.queue.get_current()
                            if current:
                                self.mw.playback_controller.play_track(current)
                                def restore_playback_state():
                                    if position > 0:
                                        self.mw.audio_engine.set_position(position)
                                    if not was_playing:
                                        self.mw.audio_engine.pause()
                                QTimer.singleShot(250, restore_playback_state)
                        if hasattr(self, '_metadata_workers') and worker in self._metadata_workers:
                            self._metadata_workers.remove(worker)
                    if not hasattr(self, '_metadata_workers'):
                        self._metadata_workers = []
                    worker.finished_write.connect(on_writer_finished)
                    self._metadata_workers.append(worker)
                    worker.start()
                if self.mw.library_manager.file_watcher:
                    self.mw.library_manager.file_watcher.ignore_next(track.filepath)
                if is_current:
                    QTimer.singleShot(150, _start_worker)
                else:
                    _start_worker()
            dialog.metadata_saved.connect(on_saved)
            dialog.exec()
        QTimer.singleShot(10, _show_dialog)