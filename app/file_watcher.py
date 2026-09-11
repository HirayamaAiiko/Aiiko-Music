import os
import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logging.warning("watchdog no instalado. El vigilante de archivos en tiempo real no estará disponible.")
from models import Track
from database import save_batch, get_db_connection
VALID_EXTENSIONS = ('.mp3', '.flac', '.wav', '.ogg', '.m4a')
class _MusicFileHandler(FileSystemEventHandler):
    def __init__(self, callback_new, callback_delete, existing_paths):
        super().__init__()
        self.callback_new = callback_new
        self.callback_delete = callback_delete
        self.existing_paths = existing_paths
        self._recent = {}                                    
    def on_created(self, event):
        if event.is_directory:
            return
        self._handle(event.src_path)
    def on_moved(self, event):
        if event.is_directory:
            return
        self._handle(event.dest_path)
    def ignore_next(self, filepath):
        self._recent[filepath] = time.time() + 10.0                        
    def _handle(self, filepath):
        if not filepath.lower().endswith(VALID_EXTENSIONS):
            return
        now = time.time()
        if filepath in self._recent:
            last = self._recent[filepath]
            if last > now:
                return
            if (now - last) < 3.0:
                return
        self._recent[filepath] = now
        if filepath in self.existing_paths:
            return
        from database import get_ignored_tracks
        if filepath in get_ignored_tracks():
            return
        self._wait_for_file_ready(filepath)
        if os.path.exists(filepath):
            self.existing_paths.add(filepath)
            self.callback_new(filepath)
    def on_deleted(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        if not filepath.lower().endswith(VALID_EXTENSIONS):
            return
        now = time.time()
        key = f"del:{filepath}"
        if key in self._recent and (now - self._recent[key]) < 3.0:
            return
        self._recent[key] = now
        if filepath in self.existing_paths:
            self.existing_paths.discard(filepath)
            self.callback_delete(filepath)
    def _wait_for_file_ready(self, filepath, timeout=5.0):
        prev_size = -1
        elapsed = 0.0
        interval = 0.3
        while elapsed < timeout:
            try:
                curr_size = os.path.getsize(filepath)
                if curr_size == prev_size and curr_size > 0:
                    return                   
                prev_size = curr_size
            except OSError:
                pass
            time.sleep(interval)
            elapsed += interval
class FileWatcherThread(QThread):
    new_track_found = pyqtSignal(object)                  
    track_removed = pyqtSignal(str)                                           
    def __init__(self, folders, existing_paths):
        super().__init__()
        self.folders = list(folders)
        self.existing_paths = set(existing_paths)
        self.running = True
        self._observer = None
    def run(self):
        if not WATCHDOG_AVAILABLE:
            logging.warning("FileWatcher: watchdog no disponible, el hilo no arrancará.")
            return
        self._observer = Observer()
        self._handler = _MusicFileHandler(self._on_new_file, self._on_file_deleted, self.existing_paths)
        for folder in self.folders:
            if os.path.isdir(folder):
                self._observer.schedule(self._handler, folder, recursive=True)
                logging.info(f"FileWatcher: Vigilando '{folder}'")
        self._observer.start()
        while self.running:
            self.msleep(500)
        self._observer.stop()
        self._observer.join(timeout=3)
        logging.info("FileWatcher: Detenido limpiamente.")
    def ignore_next(self, filepath):
        if hasattr(self, '_handler'):
            self._handler.ignore_next(filepath)
    def _on_new_file(self, filepath):
        try:
            track = Track(filepath, lazy=False)
            save_batch([track])                                      
            self.new_track_found.emit(track)
            logging.info(f"FileWatcher: Nueva canción detectada → {track.title} - {track.artist}")
        except Exception as e:
            logging.error(f"FileWatcher: Error procesando '{filepath}': {e}")
    def _on_file_deleted(self, filepath):
        try:
            _delete_track_db(filepath)
            self.track_removed.emit(filepath)
            logging.info(f"FileWatcher: Canción eliminada → {filepath}")
        except Exception as e:
            logging.error(f"FileWatcher: Error al eliminar '{filepath}': {e}")
    def update_folders(self, new_folders, existing_paths):
        self.existing_paths = set(existing_paths)
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=3)
        self.folders = list(new_folders)
        if not WATCHDOG_AVAILABLE:
            return
        self._observer = Observer()
        handler = _MusicFileHandler(self._on_new_file, self._on_file_deleted, self.existing_paths)
        for folder in self.folders:
            if os.path.isdir(folder):
                self._observer.schedule(handler, folder, recursive=True)
                logging.info(f"FileWatcher: Re-vigilando '{folder}'")
        self._observer.start()
    def stop(self):
        self.running = False
def _delete_tracks_db_batch(filepaths):
    if not filepaths: return
    try:
        from contextlib import closing
        conn = get_db_connection()
        with closing(conn):
            with conn:
                conn.executemany("DELETE FROM tracks WHERE filepath = ?", [(fp,) for fp in filepaths])
    except Exception as e:
        logging.error(f"Error eliminando tracks en lote de SQLite: {e}")
def _delete_track_db(filepath):
    _delete_tracks_db_batch([filepath])
class DiffScanThread(QThread):
    new_tracks_found = pyqtSignal(list)                           
    tracks_removed = pyqtSignal(list)                                     
    diff_finished = pyqtSignal(int, int)                         
    def __init__(self, folders, existing_paths):
        super().__init__()
        self.folders = list(folders)
        self.existing_paths = set(existing_paths)
        self.running = True
    def run(self):
        logging.info("DiffScan: Iniciando escaneo diferencial...")
        disk_files = set()
        def scan_dir_recursive(directory):
            try:
                with os.scandir(directory) as it:
                    for entry in it:
                        if not self.running: return
                        if entry.is_dir(follow_symlinks=False):
                            yield from scan_dir_recursive(entry.path)
                        elif entry.is_file() and entry.name.lower().endswith(VALID_EXTENSIONS):
                            yield entry.path
            except PermissionError:
                pass
        for folder in self.folders:
            if not os.path.isdir(folder):
                continue
            for path in scan_dir_recursive(folder):
                disk_files.add(path)
        from database import get_ignored_tracks
        new_files = disk_files - self.existing_paths - get_ignored_tracks()
        missing_files = []
        for path in self.existing_paths:
            if path not in disk_files:
                missing_files.append(path)
        new_tracks = []
        for filepath in new_files:
            if not self.running: break
            try:
                track = Track(filepath, lazy=False)
                new_tracks.append(track)
            except Exception as e:
                logging.error(f"DiffScan: Error procesando '{filepath}': {e}")
        if new_tracks:
            save_batch(new_tracks)
            self.new_tracks_found.emit(new_tracks)
        if missing_files:
            _delete_tracks_db_batch(missing_files)
            self.tracks_removed.emit(missing_files)
        logging.info(f"DiffScan: Completado — {len(new_tracks)} nuevos, {len(missing_files)} eliminados.")
        self.diff_finished.emit(len(new_tracks), len(missing_files))