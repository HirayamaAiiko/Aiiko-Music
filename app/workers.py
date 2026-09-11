import os
import queue
import logging
import re
import html
import json
import hashlib
import requests
import urllib.parse
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPainter, QPainterPath
from models import Track
from config import CACHE_DIR
from database import get_artist_info_db, save_artist_info_db, clear_artist_cache_db, get_all_artists_info_db
from utils import normalize_artist_name, sanitize_text, get_artists_from_string
from settings_manager import settings
class AsyncImageLoader(QThread):
    image_ready = pyqtSignal(str, int, int, QImage)
    def __init__(self):
        super().__init__()
        self.task_queue = queue.Queue()
        self.seen = set()
        self.running = True
    def add_task(self, filepath, size, radius):
        if filepath:
            task_id = f"{filepath}_{size}_{radius}"
            if task_id not in self.seen:
                self.seen.add(task_id)
                self.task_queue.put((filepath, size, radius))
    def run(self):
        TYPICAL_SIZES = [65, 160, 220, 450]
        while self.running:
            try:
                filepath, size, radius = self.task_queue.get(timeout=0.5)
                if filepath:
                    is_artist = "artist_profiles" in filepath or radius >= 80
                    thumb_dir = os.path.join(CACHE_DIR, "artist_profiles", "thumbnails") if is_artist else os.path.join(CACHE_DIR, "thumbnails")
                    os.makedirs(thumb_dir, exist_ok=True)
                    file_hash = hashlib.md5(filepath.encode('utf-8')).hexdigest()
                    thumb_jpg_path = os.path.join(thumb_dir, f"{file_hash}_{size}.jpg")
                    def apply_radius_and_emit(src_img, target_size, target_radius):
                        out_img = QImage(target_size, target_size, QImage.Format.Format_ARGB32_Premultiplied)
                        out_img.fill(Qt.GlobalColor.transparent)
                        painter = QPainter(out_img)
                        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                        path_obj = QPainterPath()
                        path_obj.addRoundedRect(0, 0, target_size, target_size, target_radius, target_radius)
                        painter.setClipPath(path_obj)
                        x = (target_size - src_img.width()) // 2
                        y = (target_size - src_img.height()) // 2
                        painter.drawImage(x, y, src_img)
                        painter.end()
                        self.image_ready.emit(filepath, target_size, target_radius, out_img)
                    if os.path.exists(thumb_jpg_path):
                        sq_img = QImage(thumb_jpg_path)
                        if not sq_img.isNull():
                            apply_radius_and_emit(sq_img, size, radius)
                            continue
                    legacy_png_path = os.path.join(thumb_dir, f"{file_hash}_{size}_{radius}.png")
                    if os.path.exists(legacy_png_path):
                        legacy_img = QImage(legacy_png_path)
                        if not legacy_img.isNull():
                            self.image_ready.emit(filepath, size, radius, legacy_img.copy())
                            continue
                    if os.path.exists(filepath):
                        sizes_to_gen = set(TYPICAL_SIZES)
                        sizes_to_gen.add(size)
                        max_target = max(sizes_to_gen)
                        from PyQt6.QtGui import QImageReader
                        from PyQt6.QtCore import QSize
                        reader = QImageReader(filepath)
                        orig_size = reader.size()
                        if orig_size.width() > 0 and orig_size.height() > 0:
                            orig_w, orig_h = orig_size.width(), orig_size.height()
                            if orig_w > max_target or orig_h > max_target:
                                if orig_w < orig_h:
                                    target_w = max_target
                                    target_h = int((orig_h / orig_w) * max_target)
                                else:
                                    target_h = max_target
                                    target_w = int((orig_w / orig_h) * max_target)
                                reader.setScaledSize(QSize(target_w, target_h))
                        img = reader.read()
                        if not img.isNull() and size > 0:
                            min_dim = min(img.width(), img.height())
                            x_offset = (img.width() - min_dim) // 2
                            y_offset = (img.height() - min_dim) // 2
                            square_img = img.copy(x_offset, y_offset, min_dim, min_dim)
                            generated_requested_img = None
                            for s in sizes_to_gen:
                                scaled_sq = square_img.scaled(s, s, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                                if scaled_sq.format() != QImage.Format.Format_RGB32:
                                    scaled_sq = scaled_sq.convertToFormat(QImage.Format.Format_RGB32)
                                out_jpg_path = os.path.join(thumb_dir, f"{file_hash}_{s}.jpg")
                                scaled_sq.save(out_jpg_path, "JPEG", 85)                             
                                if s == size:
                                    generated_requested_img = scaled_sq
                            if generated_requested_img:
                                apply_radius_and_emit(generated_requested_img, size, radius)
            except queue.Empty:
                continue 
            except Exception as e:
                logging.debug(f"Error procesando imagen asíncrona: {e}")
class ScannerThread(QThread):
    batch_scanned = pyqtSignal(list)
    finished_scan = pyqtSignal()
    current_file = pyqtSignal(str)
    progress_percent = pyqtSignal(int)         
    progress_count = pyqtSignal(int, int)                   
    def __init__(self, folders, existing_tracks_dict, force_full=False, ignored_tracks=None):
        super().__init__()
        self.folders = folders
        self.existing_tracks = existing_tracks_dict
        self.force_full = force_full
        self.ignored_tracks = ignored_tracks or set()
        self.running = True
    def _count_files(self):
        valid_extensions = ('.mp3', '.flac', '.wav', '.ogg', '.m4a')
        total = 0
        for directory in self.folders:
            if not os.path.exists(directory):
                continue
            try:
                for root, _dirs, files in os.walk(directory):
                    if not self.running:
                        return total
                    for f in files:
                        if f.lower().endswith(valid_extensions):
                            total += 1
            except PermissionError:
                pass
        return total
    def run(self):
        valid_extensions = ('.mp3', '.flac', '.wav', '.ogg', '.m4a')
        current_batch = []
        batch_size = 100 
        total_files = self._count_files()
        if total_files == 0:
            total_files = 1                            
        processed_count = 0
        import time
        last_emit_time = time.time()
        processed_paths = set(self.existing_tracks)
        def scan_dir(directory):
            if not self.running: return
            try:
                with os.scandir(directory) as it:
                    for entry in it:
                        if not self.running: return
                        if entry.is_dir(follow_symlinks=False):
                            yield from scan_dir(entry.path)
                        elif entry.is_file() and entry.name.lower().endswith(valid_extensions):
                            yield entry.path
            except PermissionError:
                pass
        for directory in self.folders:
            if not self.running: break
            if not os.path.exists(directory): continue
            for path in scan_dir(directory):
                if not self.running: break
                processed_count += 1
                if processed_count % 100 == 0:
                    QThread.msleep(1)
                current_time = time.time()
                if current_time - last_emit_time >= 0.033 or processed_count == total_files:
                    self.current_file.emit(os.path.basename(path))
                    pct = min(100, int(processed_count * 100 / total_files))
                    self.progress_percent.emit(pct)
                    self.progress_count.emit(processed_count, total_files)
                    last_emit_time = current_time
                norm_path = os.path.normpath(path)
                if norm_path in self.ignored_tracks:
                    continue
                if norm_path not in processed_paths:
                    processed_paths.add(norm_path)
                    track = Track(path, lazy=False)
                    current_batch.append(track)
                    if len(current_batch) >= batch_size:
                        self.batch_scanned.emit(current_batch)
                        current_batch = []
                        QThread.msleep(2)
                else:
                    track = self.existing_tracks.get(norm_path) or self.existing_tracks.get(path)
                    if track is None:
                        continue
                    if self.force_full or getattr(track, 'duration', 0) == 0 or getattr(track, 'bitrate', 0) == 0:
                        track.extract_metadata()
                        current_batch.append(track)
                        if len(current_batch) >= batch_size:
                            self.batch_scanned.emit(current_batch)
                            current_batch = []
                            QThread.msleep(2)
        if current_batch:
            self.batch_scanned.emit(current_batch)
        self.progress_percent.emit(100)
        self.finished_scan.emit()
class ArtistDataWorker(QThread):
    result_ready = pyqtSignal(dict)                                      
    def __init__(self, artist_name, library, parent=None):
        super().__init__(parent)
        self.artist_name = artist_name
        self._library = library
    def run(self):
        from utils import get_artists_from_string
        artist_name = self.artist_name
        artist_name_lower = artist_name.lower()
        first_track = None
        tracks_in_artist = []
        for t in self._library:
            if artist_name_lower not in t.artist.lower():
                continue
            artists = get_artists_from_string(t.artist)
            if any(a.lower() == artist_name_lower for a in artists):
                if not first_track and t.cover_path:
                    first_track = t
                elif not first_track:
                    first_track = t
                tracks_in_artist.append(t)
        top_tracks = sorted(tracks_in_artist, key=lambda x: getattr(x, 'play_count', 0), reverse=True)[:5]
        unique_albums = {}
        for t in tracks_in_artist:
            if t.album:
                if t.album not in unique_albums:
                    unique_albums[t.album] = []
                unique_albums[t.album].append(t)
        album_counts = {}
        if unique_albums:
            for tr in self._library:
                if tr.album in unique_albums:
                    album_counts[tr.album] = album_counts.get(tr.album, 0) + 1
        album_items = []
        ep_items = []
        for alb_name, tracks in unique_albums.items():
            alb_track = tracks[0]
            total = album_counts.get(alb_name, len(tracks))
            total_duration = sum(getattr(t, 'duration', 0) for t in tracks)
            if total >= 7 or total_duration >= 1800000:
                album_items.append((alb_name, alb_track, total))
            else:
                ep_items.append((alb_name, alb_track, total))
        def _get_year(item):
            y = getattr(item[1], 'year', '0')
            try: return int(y)
            except: return 0
        album_items.sort(key=lambda x: (-_get_year(x), x[0]))
        ep_items.sort(key=lambda x: (-_get_year(x), x[0]))
        all_disco_items = sorted(album_items + ep_items, key=lambda x: (-_get_year(x), x[0]))
        recommended_artists = set()
        for t in tracks_in_artist:
            for a in get_artists_from_string(t.artist):
                if a.lower() != artist_name_lower:
                    recommended_artists.add(a)
        rec_list = list(recommended_artists)
        if len(rec_list) < 5:
            genres = [t.genre for t in tracks_in_artist if t.genre and t.genre != "Desconocido"]
            if genres:
                from collections import Counter
                most_common_genre = Counter(genres).most_common(1)[0][0]
                for t in self._library:
                    if t.genre == most_common_genre:
                        for a in get_artists_from_string(t.artist):
                            if a.lower() != artist_name_lower and a not in rec_list:
                                rec_list.append(a)
                                if len(rec_list) >= 5:
                                    break
                    if len(rec_list) >= 5:
                        break
        from settings_manager import settings
        all_playlists = settings.get('playlists', {})
        playlist_covers = settings.get('playlist_covers', {})
        related_playlists_data = {}
        if all_playlists:
            track_paths = {t.filepath for t in tracks_in_artist}
            lib_dict = {t.filepath: t for t in self._library}
            for p_name, filepaths in all_playlists.items():
                if any(fp in track_paths for fp in filepaths):
                    cover = playlist_covers.get(p_name)
                    if not cover or not os.path.exists(cover):
                        cover = None
                        for fp in filepaths:
                            track = lib_dict.get(fp)
                            if track and getattr(track, 'cover_path', None) and os.path.exists(track.cover_path):
                                cover = track.cover_path
                                break
                    related_playlists_data[p_name] = {
                        'filepaths': filepaths,
                        'cover': cover
                    }
        total_plays = sum(getattr(t, 'play_count', 0) for t in tracks_in_artist)
        self.result_ready.emit({
            'artist_name': artist_name,
            'first_track': first_track,
            'tracks_in_artist': tracks_in_artist,
            'top_tracks': top_tracks,
            'album_items': album_items,
            'ep_items': ep_items,
            'all_disco_items': all_disco_items,
            'rec_list': rec_list[:5],
            'related_playlists': related_playlists_data,
            'count': len(tracks_in_artist),
            'total_plays': total_plays,
        })
class ArtistInfoFetcherThread(QThread):
    result_ready = pyqtSignal(str, str, str)                                     
    def __init__(self, artist_name):
        super().__init__()
        self.artist_name = artist_name
    def run(self):
        original_name = self.artist_name.strip()
        norm_name = normalize_artist_name(self.artist_name)
        if not norm_name or norm_name.lower() == "desconocido":
            self.result_ready.emit(self.artist_name, "", "")
            return
        cached = get_artist_info_db(norm_name)
        cached_bio = cached.get("bio", "") if cached else ""
        cached_cover = cached.get("cover_path", "") if cached else ""
        needs_bio = not cached_bio or not cached_bio.startswith("{")
        needs_cover = not cached_cover or not os.path.exists(cached_cover)
        if not needs_bio and not needs_cover:
            self.result_ready.emit(self.artist_name, cached_cover, cached_bio)
            return
        bio = cached_bio
        local_path = cached_cover
        if needs_bio:
            if settings.get('fetch_artist_info_network', True):
                from services.lastfm_client import LastFMClient
                lastfm = LastFMClient()
                lastfm_data = lastfm.get_artist_info(original_name)
                if lastfm_data:
                    bio = json.dumps(lastfm_data)
        if needs_cover:
            if settings.get('fetch_artist_info_network', True):
                profiles_dir = os.path.join(CACHE_DIR, "artist_profiles")
            os.makedirs(profiles_dir, exist_ok=True)
            headers = {"User-Agent": "AIIKOMusicPro/1.0"}
            session = requests.Session()
            session.headers.update(headers)
            try:
                dz_url = f"https://api.deezer.com/search/artist?q={urllib.parse.quote(norm_name)}"
                dz_resp = session.get(dz_url, timeout=5)
                if dz_resp.status_code == 200:
                    dz_data = dz_resp.json()
                    if dz_data.get("data") and len(dz_data["data"]) > 0:
                        artist_item = dz_data["data"][0]
                        img_url = artist_item.get("picture_xl") or artist_item.get("picture_big")
                        if img_url and "/artist//" not in img_url:
                            local_path = self._download_image(session, img_url, norm_name, profiles_dir)
            except Exception as e:
                logging.debug(f"Error Deezer API: {e}")
            session.close()
        if bio or local_path:
            save_artist_info_db(norm_name, bio, local_path)
        self.result_ready.emit(self.artist_name, local_path, bio)
    def _download_image(self, session, img_url, norm_name, profiles_dir):
        try:
            img_resp = session.get(img_url, timeout=10)
            if img_resp.status_code == 200:
                img_data = img_resp.content
                if len(img_data) > 100:
                    cover_hash = hashlib.md5((norm_name + img_url).encode('utf-8')).hexdigest()
                    local_path = os.path.join(profiles_dir, f"artist_cover_{cover_hash}.jpg")
                    try:
                        img = QImage()
                        img.loadFromData(img_data)
                        if not img.isNull() and (img.width() > 500 or img.height() > 500):
                            from PyQt6.QtCore import Qt as QtConst
                            img = img.scaled(500, 500, QtConst.AspectRatioMode.KeepAspectRatio, QtConst.TransformationMode.SmoothTransformation)
                        img.save(local_path, "JPEG", 85)
                    except Exception:
                        with open(local_path, 'wb') as f:
                            f.write(img_data)
                    return local_path
        except Exception as img_err:
            logging.debug(f"Error descargando imagen: {img_err}")
        return ""
class ArtistBatchFetcherThread(QThread):
    progress = pyqtSignal(int, int, str)
    finished_batch = pyqtSignal()
    def __init__(self, artists_list):
        super().__init__()
        self.artists_list = artists_list
        self.running = True
    def run(self):
        total = len(self.artists_list)
        profiles_dir = os.path.join(CACHE_DIR, "artist_profiles")
        os.makedirs(profiles_dir, exist_ok=True)
        headers = {"User-Agent": "AIIKOMusicPro/1.0"}
        session = requests.Session()
        session.headers.update(headers)
        network_enabled = settings.get('fetch_artist_info_network', True)
        for i, artist_name in enumerate(self.artists_list):
            if not self.running: break
            self.progress.emit(i, total, artist_name)
            norm_name = normalize_artist_name(artist_name)
            if not norm_name or norm_name.lower() == "desconocido":
                continue
            cached = get_artist_info_db(norm_name)
            if cached and cached.get("cover_path") and cached.get("bio"):
                continue 
            bio = ""
            local_path = ""
            if network_enabled:
                try:
                    dz_url = f"https://api.deezer.com/search/artist?q={urllib.parse.quote(norm_name)}"
                    dz_resp = session.get(dz_url, timeout=5)
                    if dz_resp.status_code == 200:
                        dz_data = dz_resp.json()
                        if dz_data.get("data") and len(dz_data["data"]) > 0:
                            artist_item = dz_data["data"][0]
                            img_url = artist_item.get("picture_xl") or artist_item.get("picture_big")
                            if img_url and "/artist//" not in img_url:
                                local_path = self._download_image(session, img_url, norm_name, profiles_dir)
                except Exception as e:
                    logging.debug(f"Error Deezer API: {e}")
            if bio or local_path:
                save_artist_info_db(norm_name, bio, local_path)
        session.close()
        self.finished_batch.emit()
    def _download_image(self, session, img_url, norm_name, profiles_dir):
        try:
            img_resp = session.get(img_url, timeout=10)
            if img_resp.status_code == 200:
                img_data = img_resp.content
                if len(img_data) > 100:
                    import hashlib
                    cover_hash = hashlib.md5((norm_name + img_url).encode('utf-8')).hexdigest()
                    local_path = os.path.join(profiles_dir, f"artist_cover_{cover_hash}.jpg")
                    with open(local_path, 'wb') as f:
                        f.write(img_data)
                    return local_path
        except Exception: pass
        return ""
class CacheRepairThread(QThread):
    progress = pyqtSignal(int, int)
    def __init__(self, library, only_missing=False):
        super().__init__()
        self.library = library
        self.only_missing = only_missing
        self.running = True
    def run(self):
        if not self.only_missing:
            import shutil
            try:
                for item in os.listdir(CACHE_DIR):
                    if not self.running: break
                    item_path = os.path.join(CACHE_DIR, item)
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
            except Exception as e:
                logging.error(f"Error limpiando caché física: {e}")
        total = len(self.library)
        import time
        last_emit_time = time.time()
        for i, track in enumerate(self.library):
            if not self.running: break
            if i % 100 == 0:
                QThread.msleep(1)
            needs_repair = True
            if self.only_missing:
                if track.cover_path and os.path.exists(track.cover_path):
                    needs_repair = False
            if needs_repair:
                track.cover_path = None 
                track.extract_metadata()
            current_time = time.time()
            if current_time - last_emit_time >= 0.033 or i == total - 1:
                self.progress.emit(i + 1, total)
                last_emit_time = current_time
        self.progress.emit(total, total)
class LibraryParserWorker(QThread):
    result_ready = pyqtSignal(list, list)                            
    def __init__(self, library, merge_albums=True, parent=None):
        super().__init__(parent)
        self.library = library
        self.merge_albums = merge_albums
    def run(self):
        from core.language_manager import tr
        albums_dict, artists_dict = {}, {}
        _artist_name_counts = {}
        _artist_tracks = {}
        from utils import sanitize_text, get_artists_from_string, get_album_group_key
        for track in self.library:
            album_key = get_album_group_key(track, self.merge_albums)
            if album_key not in albums_dict: 
                albums_dict[album_key] = track
            artists = get_artists_from_string(track.artist)
            for clean_artist in artists:
                key = clean_artist.lower()
                if key not in _artist_name_counts:
                    _artist_name_counts[key] = {}
                _artist_name_counts[key][clean_artist] = _artist_name_counts[key].get(clean_artist, 0) + 1
                if key not in _artist_tracks:
                    _artist_tracks[key] = track
                elif not _artist_tracks[key].cover_path and track.cover_path:
                    _artist_tracks[key] = track
        for key, variants in _artist_name_counts.items():
            canonical_name = max(variants, key=variants.get)
            artists_dict[canonical_name] = _artist_tracks[key]
        all_artists_db = get_all_artists_info_db()
        album_items = [(track.album if track.album else tr("Desconocido"), track, None) for key, track in albums_dict.items()]
        artist_items = []
        for name, track in artists_dict.items():
            norm_name = normalize_artist_name(name)
            cached = all_artists_db.get(norm_name)
            custom_cover = cached.get('cover_path') if cached else None
            artist_items.append((name, track, custom_cover))
        self.result_ready.emit(album_items, artist_items)