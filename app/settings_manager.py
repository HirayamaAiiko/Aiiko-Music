import os
import json
import logging
from config import SETTINGS_FILE, APP_ROOT
class SettingsManager:
    def __init__(self):
        import threading
        self._save_lock = threading.Lock()
        self.data = {
            'folders': [],
            'favorites': [],
            'playlists': {},
            'rpc': False,
            'volume': 80,
            'auto_scan': False,
            'dynamic_bg': False,
            'sort_configs': {'songs': 0, 'albums': 0, 'artists': 0},
            'lastfm_session_key': '',
            'lastfm_username': '',
            'songs_is_grid': False,
            'last_queue_paths': [],
            'last_queue_index': -1,
            'translation_lang': 'es',
            'scroll_positions': {'songs': 0, 'albums': 0, 'artists': 0},
            'smooth_lyrics': True,
            'app_theme': 'Obsidian Fluent',
            'app_accent_name': 'Cian (AIIKO)',
            'advanced_image_cache_size': 200,
            'show_scroll_to_top': True,
            'show_locate_track': False,
            'fetch_artist_info_network': False
        }
        self.load()
    def get(self, key, default=None):
        return self.data.get(key, default)
    def set(self, key, value):
        self.data[key] = value
    def load(self):
        loaded_data = {}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8-sig') as f:
                    loaded_data = json.load(f)
            except Exception as e:
                logging.error(f"Error cargando ajustes JSON: {e}. Intentando usar backup...")
                bak_file = SETTINGS_FILE + '.bak'
                if os.path.exists(bak_file):
                    try:
                        with open(bak_file, 'r', encoding='utf-8-sig') as f:
                            loaded_data = json.load(f)
                        logging.info("Ajustes recuperados exitosamente desde el backup.")
                    except Exception as e2:
                        logging.error(f"Fallo también el backup: {e2}")
                        try:
                            import shutil
                            shutil.copy(SETTINGS_FILE, SETTINGS_FILE + '.corrupted')
                        except: pass
                else:
                    try:
                        import shutil
                        shutil.copy(SETTINGS_FILE, SETTINGS_FILE + '.corrupted')
                    except: pass
        for key, val in loaded_data.items():
            self.data[key] = val
        if loaded_data:
            logging.info("Ajustes cargados exitosamente de forma segura.")
        try:
            from database import init_db, get_favorites_db, set_favorites_db, get_playlists_db, set_playlists_db, get_queue_db, set_queue_db, get_playlist_covers_db, set_playlist_covers_db
            init_db()
            migrated = False
            if 'favorites' in loaded_data and len(loaded_data['favorites']) > 0:
                set_favorites_db(loaded_data['favorites'])
                migrated = True
            if 'playlists' in loaded_data and len(loaded_data['playlists']) > 0:
                set_playlists_db(loaded_data['playlists'])
                migrated = True
            if 'playlist_covers' in loaded_data and len(loaded_data['playlist_covers']) > 0:
                set_playlist_covers_db(loaded_data['playlist_covers'])
                migrated = True
            if 'last_queue_paths' in loaded_data and len(loaded_data['last_queue_paths']) > 0:
                set_queue_db(loaded_data['last_queue_paths'], loaded_data.get('last_queue_index', -1))
                migrated = True
            self.data['favorites'] = get_favorites_db()
            self.data['playlists'] = get_playlists_db()
            self.data['playlist_covers'] = get_playlist_covers_db()
            q_paths, q_idx = get_queue_db()
            self.data['last_queue_paths'] = q_paths
            self.data['last_queue_index'] = q_idx
            if migrated:
                self.save()
        except Exception as e:
            logging.error(f"Error en proxy SQLite-Settings: {e}")
    def save(self, sync=False):
        import threading
        import copy
        def _bg_save(data_snap):
            with self._save_lock:
                try:
                    from database import set_favorites_db, set_playlists_db, set_queue_db, set_playlist_covers_db
                    favs = data_snap.get('favorites', [])
                    if getattr(self, '_last_favs', None) != favs:
                        set_favorites_db(favs)
                        self._last_favs = list(favs)
                    pls = data_snap.get('playlists', {})
                    if getattr(self, '_last_pls', None) != pls:
                        set_playlists_db(pls)
                        self._last_pls = {k: list(v) for k, v in pls.items()}
                    covers = data_snap.get('playlist_covers', {})
                    if getattr(self, '_last_covers', None) != covers:
                        set_playlist_covers_db(covers)
                        self._last_covers = {k: v for k, v in covers.items()}
                    q_tuple = (data_snap.get('last_queue_paths', []), data_snap.get('last_queue_index', -1))
                    if getattr(self, '_last_q', None) != q_tuple:
                        set_queue_db(q_tuple[0], q_tuple[1])
                        self._last_q = (list(q_tuple[0]), q_tuple[1])
                except Exception as e:
                    logging.error(f"Error guardando en proxy SQL asíncrono: {e}")
                json_data = data_snap.copy()
                for key in ['favorites', 'playlists', 'playlist_covers', 'last_queue_paths', 'last_queue_index']:
                    json_data.pop(key, None)
                try:
                    import json
                    import shutil
                    tmp_file = SETTINGS_FILE + '.tmp'
                    with open(tmp_file, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=4)
                        f.flush()
                        os.fsync(f.fileno())                                  
                    os.replace(tmp_file, SETTINGS_FILE)                                     
                    bak_file = SETTINGS_FILE + '.bak'
                    shutil.copy(SETTINGS_FILE, bak_file)
                except Exception as e:
                    logging.error(f"Error guardando ajustes JSON atómico: {e}")
        snap = copy.deepcopy(self.data)
        if sync:
            _bg_save(snap)
        else:
            t = threading.Thread(target=_bg_save, args=(snap,), daemon=False)
            t.start()
settings = SettingsManager()