import os
import mutagen
import hashlib
import time
import logging
from config import CACHE_DIR
def fix_mojibake(text):
    if not text: return text
    text = str(text).replace('\ufeff', '').strip('\x00').replace('\x00', ', ').strip()
    import re
    text = re.sub(r'[\ud800-\udfff]', '', text)
    return text
class Track:
    def __init__(self, filepath, lazy=False):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.title = os.path.splitext(self.filename)[0]
        self.artist = "Artista Desconocido"
        self.album = "Álbum Desconocido"
        self.genre = "Desconocido"
        self.year = "Desconocido"
        self.duration = 0
        self.cover_path = None
        self.lyrics_sync = []
        self.play_count = 0
        self.last_played = 0
        self.file_type = os.path.splitext(self.filename)[1][1:].upper()
        self.bitrate = 0
        self.sample_rate = 0
        self.track_number = 0
        self.replaygain_track = 0.0
        self.replaygain_album = 0.0
        if not lazy:
            try:
                stat = os.stat(filepath)
                self.mtime = stat.st_mtime
                self.ctime = stat.st_ctime
            except Exception:
                self.mtime = 0
                self.ctime = 0
            self.extract_metadata()
        else:
            self.mtime = 0
            self.ctime = 0
    def extract_metadata(self):
        try:
            audio = mutagen.File(self.filepath)
            if audio is None: return
            if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                self.duration = audio.info.length * 1000
                self.bitrate = getattr(audio.info, 'bitrate', 0)
                self.sample_rate = getattr(audio.info, 'sample_rate', 0)
            tags = getattr(audio, 'tags', audio)
            if tags:
                lower_keys = {k.lower(): k for k in tags.keys()} if hasattr(tags, 'keys') else {}
                def get_tag(tag_list):
                    for t in tag_list:
                        t_lower = t.lower()
                        if t_lower in lower_keys:
                            val = tags[lower_keys[t_lower]]
                            if hasattr(val, 'text') and isinstance(val.text, list):
                                joined = ', '.join(str(v) for v in val.text if str(v).strip())
                                return fix_mojibake(joined) if joined else None
                            if isinstance(val, list) and len(val) > 0:
                                return fix_mojibake(val[0])
                            return fix_mojibake(val)
                    return None
                title = get_tag(['TIT2', 'title', '©nam', 'TITLE'])
                if title: self.title = title
                artist = get_tag(['TPE1', 'artist', '©ART', 'ARTIST'])
                if artist: self.artist = artist
                album = get_tag(['TALB', 'album', '©alb', 'ALBUM'])
                if album: self.album = album
                year = get_tag(['TDRC', 'TYER', 'date', 'year', '©day', 'DATE', 'YEAR'])
                if year: 
                    import re
                    match = re.search(r'\b(19\d{2}|20\d{2})\b', str(year))
                    self.year = match.group(1) if match else str(year)[:4]
                genre = get_tag(['TCON', 'genre', '©gen', 'GENRE'])
                if genre: self.genre = genre
            art_data = None
            if hasattr(audio, 'pictures') and audio.pictures:
                for pic in audio.pictures:
                    if pic.type == 3:              
                        art_data = pic.data
                        break
                if not art_data:                                                     
                    art_data = audio.pictures[0].data
            elif tags and 'metadata_block_picture' in tags:
                import base64
                from mutagen.flac import Picture
                try:
                    b64_data = tags['metadata_block_picture'][0]
                    pic_data = base64.b64decode(b64_data)
                    pic = Picture(pic_data)
                    art_data = pic.data
                except Exception: pass
            elif tags and hasattr(tags, 'keys'):
                for key in tags.keys():
                    if key.startswith('APIC'):
                        art_data = tags[key].data
                        break
                    elif key == 'covr':
                        art_data = tags[key][0]
                        if not isinstance(art_data, bytes):
                            art_data = bytes(art_data)
                        break
            if art_data:
                cover_hash = hashlib.md5(art_data).hexdigest()
                self.cover_path = os.path.join(CACHE_DIR, f"{cover_hash}.jpg")
                if not os.path.exists(self.cover_path):
                    with open(self.cover_path, 'wb') as img_file:
                        img_file.write(art_data)
            if tags and hasattr(tags, 'keys'):
                lower_keys = {k.lower(): k for k in tags.keys()}
                track_num = None
                for t_name in ['trck', 'tracknumber', 'trkn']:
                    if t_name in lower_keys:
                        val = tags[lower_keys[t_name]]
                        val = val[0] if isinstance(val, list) and len(val) > 0 else val
                        if isinstance(val, tuple): val = val[0]
                        val_str = str(val)
                        if '/' in val_str: val_str = val_str.split('/')[0]
                        digits = ''.join(filter(str.isdigit, val_str))
                        if digits: 
                            track_num = int(digits)
                            break
                if track_num is not None:
                    self.track_number = track_num
            if self.track_number == 0:
                import re
                match = re.match(r'^(\d+)', os.path.basename(self.filepath))
                if match:
                    self.track_number = int(match.group(1))
            def parse_rg(val):
                if not val: return 0.0
                import re
                m = re.search(r'([-+]?\d*\.?\d+)', str(val))
                if m:
                    try: return float(m.group(1))
                    except ValueError: pass
                return 0.0
            if tags and 'get_tag' in locals():
                rg_track = get_tag(['REPLAYGAIN_TRACK_GAIN'])
                if rg_track:
                    self.replaygain_track = parse_rg(rg_track)
                rg_album = get_tag(['REPLAYGAIN_ALBUM_GAIN'])
                if rg_album:
                    self.replaygain_album = parse_rg(rg_album)
            if tags and hasattr(tags, 'getall'):
                try:
                    for txxx in tags.getall('TXXX'):
                        if txxx.desc and txxx.desc.upper() == 'REPLAYGAIN_TRACK_GAIN' and txxx.text:
                            self.replaygain_track = parse_rg(txxx.text[0])
                        elif txxx.desc and txxx.desc.upper() == 'REPLAYGAIN_ALBUM_GAIN' and txxx.text:
                            self.replaygain_album = parse_rg(txxx.text[0])
                except Exception:
                    pass
            if tags and hasattr(tags, 'keys') and '----:com.apple.iTunes:replaygain_track_gain' in tags:
                try:
                    rg_mp4 = tags['----:com.apple.iTunes:replaygain_track_gain'][0]
                    self.replaygain_track = parse_rg(rg_mp4.decode('utf-8') if isinstance(rg_mp4, bytes) else rg_mp4)
                except Exception:
                    pass
            if tags and hasattr(tags, 'keys') and '----:com.apple.iTunes:replaygain_album_gain' in tags:
                try:
                    rg_mp4_alb = tags['----:com.apple.iTunes:replaygain_album_gain'][0]
                    self.replaygain_album = parse_rg(rg_mp4_alb.decode('utf-8') if isinstance(rg_mp4_alb, bytes) else rg_mp4_alb)
                except Exception:
                    pass
        except Exception as e:
            logging.error(f"Error leyendo metadatos de {self.filepath}: {e}")