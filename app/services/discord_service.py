import logging
import time
import urllib.request
import urllib.parse
import json
import threading
from collections import OrderedDict
try:
    from pypresence import Presence
    from pypresence.types import ActivityType
    RPC_AVAILABLE = True
except ImportError:
    RPC_AVAILABLE = False
_MAX_COVER_CACHE = 200
class _CoverCache(OrderedDict):
    def get_val(self, key):
        if key in self:
            self.move_to_end(key)
            return self[key]
        return None
    def set_val(self, key, value):
        if key in self:
            self.move_to_end(key)
        self[key] = value
        if len(self) > _MAX_COVER_CACHE:
            self.popitem(last=False)
class DiscordRPCManager:
    def __init__(self):
        self.rpc = None
        self.enabled = False
        self._last_track = None
        self._current_cover_url = "music_icon"
        self._cover_cache = _CoverCache()
        self._fetch_lock = threading.Lock()
        self._last_kwargs = None
        self._rpc_lock = threading.Lock()
    def connect(self, client_id):
        if not RPC_AVAILABLE or not client_id or len(client_id) < 17:
            return False
        def _worker():
            try:
                rpc = Presence(client_id)
                rpc.connect()
                with self._rpc_lock:
                    self.rpc = rpc
                    self.enabled = True
                logging.info("Conectado a Discord RPC.")
                if self._last_kwargs:
                    self._safe_rpc_update(self._last_kwargs)
            except Exception as e:
                logging.debug(f"Fallo al conectar con Discord RPC: {e}")
                with self._rpc_lock:
                    self.rpc = None
                    self.enabled = False
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return True
    def disconnect(self):
        if self.rpc:
            try:
                self.rpc.clear()
                self.rpc.close()
                logging.info("Desconectado de Discord RPC.")
            except Exception as e:
                logging.warning(f"Aviso al cerrar Discord RPC: {e}")
        self.rpc = None
        self.enabled = False
        self._last_track = None
        self._current_cover_url = "music_icon"
    def _safe_rpc_update(self, kwargs):
        def _worker():
            with self._rpc_lock:
                if not self.enabled or not self.rpc:
                    return
                try:
                    self.rpc.update(**kwargs)
                except Exception as e:
                    logging.warning(f"Error actualizando Discord RPC: {e}")
                    self.enabled = False
                    self.rpc = None
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
    def _fetch_cover_url(self, artist, title):
        track_key = f"{artist}-{title}"
        cached = self._cover_cache.get_val(track_key)
        if cached is not None:
            return cached
        try:
            query = urllib.parse.quote(f"{artist} {title}")
            url = f"https://itunes.apple.com/search?term={query}&limit=1&entity=song"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data['resultCount'] > 0:
                    artwork_url = data['results'][0]['artworkUrl100']
                    hd_url = artwork_url.replace('100x100bb', '512x512bb')
                    self._cover_cache.set_val(track_key, hd_url)
                    return hd_url
        except Exception as e:
            logging.debug(f"No se pudo obtener carátula de internet: {e}")
        self._cover_cache.set_val(track_key, "music_icon")
        return "music_icon"
    def _fetch_cover_async(self, artist, title):
        def _worker():
            cover_url = self._fetch_cover_url(artist, title)
            with self._fetch_lock:
                self._current_cover_url = cover_url
            if self.enabled and self.rpc and self._last_kwargs:
                try:
                    kwargs_copy = dict(self._last_kwargs)
                    kwargs_copy["large_image"] = cover_url
                    self._safe_rpc_update(kwargs_copy)
                except Exception as e:
                    logging.debug(f"Error actualizando carátula en Discord RPC: {e}")
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
    def update_presence(self, track, is_playing, length_ms, position_ms=0):
        if not track:
            if self.enabled and self.rpc:
                self._safe_rpc_update({
                    "state": "Nada en reproducción",
                    "details": "Aiiko Music",
                    "large_image": "music_icon",
                    "large_text": "Aiiko Music",
                    "activity_type": ActivityType.LISTENING
                })
            return
        try:
            track_id = f"{track.artist}-{track.title}"
            from core.language_manager import tr
            artist_name = track.artist or "Desconocido"
            if artist_name in ("Desconocido", "Artista Desconocido", "Álbum Desconocido", "Unknown Artist", "Unknown Album"):
                artist_name = tr(artist_name)
            title_name = track.title or "Desconocido"
            if title_name in ("Desconocido", "Artista Desconocido", "Álbum Desconocido", "Unknown Artist", "Unknown Album"):
                title_name = tr(title_name)
            album_name = track.album
            if album_name and album_name in ("Desconocido", "Artista Desconocido", "Álbum Desconocido", "Unknown Artist", "Unknown Album"):
                album_name = tr(album_name)
            if self._last_track != track_id:
                self._last_track = track_id
                self._current_cover_url = "music_icon"
                self._fetch_cover_async(track.artist, track.title)
            kwargs = {
                "state": f"👤 {artist_name}",
                "details": f"🎵 {title_name}",
                "large_image": self._current_cover_url,
                "large_text": f"💿 {album_name}" if track.album else "Aiiko Music",
                "activity_type": ActivityType.LISTENING
            }
            if is_playing:
                if length_ms > 0:
                    start_time = int(time.time()) - (position_ms // 1000)
                    kwargs["start"] = start_time
                kwargs["small_image"] = "playing_icon"
                kwargs["small_text"] = "Reproduciendo"
            else:
                kwargs["small_image"] = "paused_icon"
                kwargs["small_text"] = "En pausa"
            self._last_kwargs = kwargs
            self._safe_rpc_update(kwargs)
        except Exception as e:
            logging.warning(f"Error preparando Discord RPC: {e}")