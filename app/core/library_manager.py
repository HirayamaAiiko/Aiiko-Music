import os
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from database import load_library_cache, save_library_cache, save_batch, clear_artist_cache_db
from workers import ScannerThread, ArtistBatchFetcherThread, CacheRepairThread
from file_watcher import FileWatcherThread, DiffScanThread, WATCHDOG_AVAILABLE
from settings_manager import settings
class LibraryManager(QObject):
    library_loaded = pyqtSignal(list)
    scan_batch_ready = pyqtSignal(list)
    scan_finished = pyqtSignal()
    watcher_new_track = pyqtSignal(object)
    watcher_track_removed = pyqtSignal(str)                                
    batch_fetcher_progress = pyqtSignal(int, int, str)
    batch_fetcher_finished = pyqtSignal()
    repair_progress = pyqtSignal(int, int)
    repair_finished = pyqtSignal()
    diff_scan_new_tracks = pyqtSignal(list)                                          
    diff_scan_removed_tracks = pyqtSignal(list)                                 
    diff_scan_finished = pyqtSignal(int, int)                           
    def __init__(self, parent=None):
        super().__init__(parent)
        self.library = []
        self.scanner = None
        self.file_watcher = None
        self.batch_fetcher = None
        self.repair_thread = None
        self.diff_scan_thread = None
        self.image_cache = None 
    def set_image_cache(self, image_cache):
        self.image_cache = image_cache
    def load_library(self):
        self.library = load_library_cache()
        self.library_loaded.emit(self.library)
        return self.library
    def update_library_cache(self):
        save_library_cache(self.library)
    def start_background_scan(self, force_full=False, specific_folders=None):
        if self.scanner and self.scanner.isRunning():
            return False 
        logging.info(f"Iniciando escaneo en segundo plano (force_full={force_full})...")
        existing_tracks = {t.filepath: t for t in self.library}
        folders = specific_folders if specific_folders is not None else settings.get('folders', [])
        from database import get_ignored_tracks
        ignored_tracks = get_ignored_tracks()
        self.scanner = ScannerThread(folders, existing_tracks, force_full, ignored_tracks)
        self.scanner.batch_scanned.connect(self._on_scan_batch)
        self.scanner.finished_scan.connect(self._on_scan_finished)
        self.scanner.start()
        return True
    def _on_scan_batch(self, tracks_batch):
        if not tracks_batch: return
        existing_paths = {t.filepath for t in self.library}
        new_tracks = [t for t in tracks_batch if t.filepath not in existing_paths]
        self.library.extend(new_tracks)
        save_batch(tracks_batch)
        self.scan_batch_ready.emit(tracks_batch)
    def _on_scan_finished(self):
        logging.info("Escaneo finalizado.")
        self.scan_finished.emit()
        self.start_artist_batch_fetcher()
        self.start_file_watcher()
    def start_file_watcher(self):
        if not WATCHDOG_AVAILABLE: return
        folders = settings.get('folders', [])
        if not folders: return
        existing_paths = [t.filepath for t in self.library]
        if self.file_watcher and self.file_watcher.isRunning():
            self.file_watcher.update_folders(folders, existing_paths)
        else:
            self.file_watcher = FileWatcherThread(folders, existing_paths)
            self.file_watcher.new_track_found.connect(self._on_watcher_new_track)
            self.file_watcher.track_removed.connect(self._on_watcher_track_removed)
            self.file_watcher.start()
    def _on_watcher_new_track(self, track):
        if any(t.filepath == track.filepath for t in self.library):
            return
        self.library.append(track)
        self.watcher_new_track.emit(track)
    def _on_watcher_track_removed(self, filepath):
        removed = [t for t in self.library if t.filepath == filepath]
        if removed:
            for t in removed:
                self.library.remove(t)
            self.watcher_track_removed.emit(filepath)
    def start_diff_scan(self):
        folders = settings.get('folders', [])
        if not folders:
            return
        existing_paths = [t.filepath for t in self.library]
        self.diff_scan_thread = DiffScanThread(folders, existing_paths)
        self.diff_scan_thread.new_tracks_found.connect(self._on_diff_new_tracks)
        self.diff_scan_thread.tracks_removed.connect(self._on_diff_removed_tracks)
        self.diff_scan_thread.diff_finished.connect(self._on_diff_finished)
        self.diff_scan_thread.start()
    def _on_diff_new_tracks(self, tracks):
        existing_paths = {t.filepath for t in self.library}
        new_tracks = [t for t in tracks if t.filepath not in existing_paths]
        self.library.extend(new_tracks)
        self.diff_scan_new_tracks.emit(tracks)
    def _on_diff_removed_tracks(self, filepaths):
        filepaths_set = set(filepaths)
        self.library[:] = [t for t in self.library if t.filepath not in filepaths_set]
        self.diff_scan_removed_tracks.emit(filepaths)
    def _on_diff_finished(self, new_count, removed_count):
        self.diff_scan_finished.emit(new_count, removed_count)
    def start_artist_batch_fetcher(self):
        artists = set()
        for t in self.library:
            if t.artist:
                for a in t.artist.split(", "):
                    if a.strip(): artists.add(a.strip())
        if not self.batch_fetcher or not self.batch_fetcher.isRunning():
            self.batch_fetcher = ArtistBatchFetcherThread(list(artists))
            self.batch_fetcher.progress.connect(self.batch_fetcher_progress.emit)
            self.batch_fetcher.finished_batch.connect(self.batch_fetcher_finished.emit)
            self.batch_fetcher.start()
    def repair_cover_cache(self):
        if self.image_cache:
            self.image_cache.pixmap_cache.clear()
            self.image_cache.pending_icons.clear()
            self.image_cache.pending_labels.clear()
        self.repair_thread = CacheRepairThread(self.library)
        self.repair_thread.progress.connect(self.repair_progress.emit)
        self.repair_thread.finished.connect(self._on_repair_finished)
        self.repair_thread.start()
    def repair_missing_covers(self):
        self.repair_thread = CacheRepairThread(self.library, only_missing=True)
        self.repair_thread.progress.connect(self.repair_progress.emit)
        self.repair_thread.finished.connect(self._on_repair_finished)
        self.repair_thread.start()
    def _on_repair_finished(self):
        self.update_library_cache()
        self.repair_finished.emit()
    def repair_artist_cache(self):
        clear_artist_cache_db()
        self.start_artist_batch_fetcher()
    def stop_all(self):
        if self.scanner and self.scanner.isRunning():
            self.scanner.running = False
            self.scanner.wait(1000)
        if self.batch_fetcher and self.batch_fetcher.isRunning():
            self.batch_fetcher.running = False
            self.batch_fetcher.wait(1000)
        if self.repair_thread and self.repair_thread.isRunning():
            self.repair_thread.running = False
            self.repair_thread.wait(1000)
        if self.file_watcher and self.file_watcher.isRunning():
            self.file_watcher.stop()
            self.file_watcher.wait(1000)
        if self.diff_scan_thread and self.diff_scan_thread.isRunning():
            self.diff_scan_thread.running = False
            self.diff_scan_thread.wait(500)