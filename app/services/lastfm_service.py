import hashlib
import time
import logging
import threading
import requests
from settings_manager import settings
from config import LASTFM_API_KEY, LASTFM_API_SECRET
LASTFM_WS = "http://ws.audioscrobbler.com/2.0/"
_session = requests.Session()
class LastfmService:
    @staticmethod
    def is_configured():
        return bool(LASTFM_API_KEY and LASTFM_API_SECRET)
    @staticmethod
    def is_connected():
        return bool(settings.get('lastfm_session_key'))
    @staticmethod
    def _generate_signature(params):
        keys = sorted(params.keys())
        sig_str = ""
        for k in keys:
            if k not in ['format', 'callback']:
                sig_str += f"{k}{params[k]}"
        sig_str += LASTFM_API_SECRET
        return hashlib.md5(sig_str.encode('utf-8')).hexdigest()
    @staticmethod
    def fetch_user_info(username):
        if not LastfmService.is_configured() or not username: return None
        try:
            import time
            url = f"{LASTFM_WS}?method=user.getinfo&user={username}&api_key={LASTFM_API_KEY}&format=json&t={int(time.time())}"
            response = _session.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json().get('user', {})
                avatar = ""
                if 'image' in data:
                    images = data['image']
                    if images and isinstance(images, list):
                        avatar = images[-1].get('#text', '')
                return {
                    'name': data.get('name', username),
                    'realname': data.get('realname', ''),
                    'playcount': data.get('playcount', '0'),
                    'avatar_url': avatar
                }
        except Exception as e:
            logging.error(f"[Last.fm] Error obteniendo info del usuario: {e}")
        return None
    @staticmethod
    def get_token():
        if not LastfmService.is_configured(): return None
        try:
            params = {
                'method': 'auth.gettoken',
                'api_key': LASTFM_API_KEY,
            }
            params['api_sig'] = LastfmService._generate_signature(params)
            params['format'] = 'json'
            r = _session.get(LASTFM_WS, params=params, timeout=5)
            data = r.json()
            if 'error' in data:
                logging.error(f"Last.fm API Error {data['error']}: {data.get('message')}")
                return f"ERROR_{data['error']}"
            return data.get('token')
        except Exception as e:
            logging.error(f"Last.fm get_token error: {e}")
            return None
    @staticmethod
    def get_auth_url(token):
        return f"http://www.last.fm/api/auth/?api_key={LASTFM_API_KEY}&token={token}"
    @staticmethod
    def get_session(token):
        if not LastfmService.is_configured(): return False
        try:
            params = {
                'method': 'auth.getSession',
                'api_key': LASTFM_API_KEY,
                'token': token
            }
            params['api_sig'] = LastfmService._generate_signature(params)
            params['format'] = 'json'
            r = _session.get(LASTFM_WS, params=params, timeout=5)
            data = r.json()
            if 'session' in data:
                settings.set('lastfm_session_key', data['session']['key'])
                settings.set('lastfm_username', data['session']['name'])
                settings.save()
                return True
            else:
                logging.error(f"Last.fm get_session error: {data}")
                return False
        except Exception as e:
            logging.error(f"Last.fm get_session error: {e}")
            return False
    @staticmethod
    def disconnect():
        settings.set('lastfm_session_key', "")
        settings.set('lastfm_username', "")
        settings.save()
    @staticmethod
    def update_now_playing(artist, title, album=""):
        sk = settings.get('lastfm_session_key')
        if not sk or not LastfmService.is_configured(): return
        if not artist or not title or artist == "Desconocido" or title == "Desconocido": return
        try:
            params = {
                'method': 'track.updateNowPlaying',
                'api_key': LASTFM_API_KEY,
                'sk': sk,
                'artist': artist,
                'track': title,
            }
            if album and album != "Desconocido":
                params['album'] = album
            params['api_sig'] = LastfmService._generate_signature(params)
            params['format'] = 'json'
            r = _session.post(LASTFM_WS, data=params, timeout=5)
            if r.status_code == 200:
                logging.info(f"Last.fm: Now Playing actualizado -> {artist} - {title}")
            else:
                logging.error(f"Last.fm Now Playing falló: {r.text}")
        except requests.exceptions.Timeout:
            logging.warning(f"Last.fm Now Playing timeout (el servidor tardó mucho en responder).")
        except Exception as e:
            logging.error(f"Last.fm Now Playing request error: {e}")
    @staticmethod
    def scrobble(artist, title, album="", timestamp=None):
        sk = settings.get('lastfm_session_key')
        if not sk or not LastfmService.is_configured(): return
        if not artist or not title or artist == "Desconocido" or title == "Desconocido": return
        if timestamp is None:
            timestamp = int(time.time())
        try:
            params = {
                'method': 'track.scrobble',
                'api_key': LASTFM_API_KEY,
                'sk': sk,
                'artist': artist,
                'track': title,
                'timestamp': str(timestamp)
            }
            if album and album != "Desconocido":
                params['album'] = album
            params['api_sig'] = LastfmService._generate_signature(params)
            params['format'] = 'json'
            r = _session.post(LASTFM_WS, data=params, timeout=15)
            if r.status_code == 200:
                logging.info(f"Last.fm: Scrobble exitoso -> {artist} - {title}")
                threading.Thread(target=LastfmService.flush_offline_cache, daemon=True).start()
            elif r.status_code >= 500:
                from database import save_offline_scrobble
                save_offline_scrobble(artist, title, album, timestamp)
                logging.warning(f"Last.fm Scrobble guardado offline por error de servidor ({r.status_code})")
            else:
                logging.error(f"Last.fm Scrobble falló: {r.text}")
        except requests.exceptions.Timeout:
            logging.warning(f"Last.fm Scrobble timeout. Guardando offline...")
            from database import save_offline_scrobble
            save_offline_scrobble(artist, title, album, timestamp)
        except requests.exceptions.RequestException as e:
            logging.warning(f"Last.fm Scrobble offline (sin red): {e}")
            from database import save_offline_scrobble
            save_offline_scrobble(artist, title, album, timestamp)
        except Exception as e:
            logging.error(f"Last.fm Scrobble request error: {e}")
    @staticmethod
    def flush_offline_cache():
        sk = settings.get('lastfm_session_key')
        if not sk or not LastfmService.is_configured(): return
        from database import get_offline_scrobbles, delete_offline_scrobbles
        pending = get_offline_scrobbles()
        if not pending: return
        for i in range(0, len(pending), 50):
            batch = pending[i:i+50]
            params = {
                'method': 'track.scrobble',
                'api_key': LASTFM_API_KEY,
                'sk': sk,
            }
            for idx, track in enumerate(batch):
                params[f'artist[{idx}]'] = track['artist']
                params[f'track[{idx}]'] = track['title']
                params[f'timestamp[{idx}]'] = str(track['timestamp'])
                if track['album']:
                    params[f'album[{idx}]'] = track['album']
            try:
                params['api_sig'] = LastfmService._generate_signature(params)
                params['format'] = 'json'
                r = _session.post(LASTFM_WS, data=params, timeout=20)
                if r.status_code == 200:
                    logging.info(f"Last.fm: Sincronizados {len(batch)} scrobbles offline.")
                    delete_offline_scrobbles([t['id'] for t in batch])
                else:
                    logging.error(f"Last.fm Scrobble Batch falló: {r.text}")
                    break                                          
            except requests.exceptions.Timeout:
                logging.warning(f"Last.fm Scrobble Batch timeout. Se reintentará en el futuro.")
                break
            except Exception as e:
                logging.error(f"Last.fm Scrobble Batch request error: {e}")
                break