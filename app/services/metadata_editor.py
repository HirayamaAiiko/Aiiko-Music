import os
import logging
import mutagen
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TYER, TCON, TRCK, APIC, SYLT, USLT, error as ID3Error
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggvorbis import OggVorbis
import traceback
class MetadataEditorService:
    @staticmethod
    def get_file_properties(filepath):
        if not os.path.exists(filepath):
            return {}
        stat = os.stat(filepath)
        size_mb = stat.st_size / (1024 * 1024)
        props = {
            "path": filepath,
            "size_mb": round(size_mb, 2),
            "bitrate": 0,
            "sample_rate": 0,
            "channels": 0,
            "format": os.path.splitext(filepath)[1][1:].upper()
        }
        try:
            audio = mutagen.File(filepath)
            if audio and hasattr(audio, 'info'):
                props["bitrate"] = getattr(audio.info, 'bitrate', 0)
                props["sample_rate"] = getattr(audio.info, 'sample_rate', 0)
                props["channels"] = getattr(audio.info, 'channels', 0)
            tags = getattr(audio, 'tags', audio) if audio else None
            props['albumartist'] = ''
            props['composer'] = ''
            props['lyrics_static'] = ''
            props['lyrics_sync'] = ''
            props['tracknumber'] = ''
            props['encoder'] = 'Desconocido'
            props['tag_ver'] = 'Desconocido'
            props['replaygain'] = 'No'
            if tags:
                ext = props['format'].lower()
                if ext == 'mp3':
                    props['albumartist'] = tags.getall('TPE2')[0].text[0] if tags.getall('TPE2') else ''
                    props['composer'] = tags.getall('TCOM')[0].text[0] if tags.getall('TCOM') else ''
                    props['tracknumber'] = tags.getall('TRCK')[0].text[0] if tags.getall('TRCK') else ''
                    uslt = tags.getall('USLT')
                    if uslt: props['lyrics_static'] = uslt[0].text
                    sylt = tags.getall('SYLT')
                    if sylt:
                        try:
                            lrc_lines = []
                            for item in sylt[0].text:
                                text_str, time_ms = item[0], item[1]
                                mins = time_ms // 60000
                                secs = (time_ms % 60000) / 1000
                                lrc_lines.append(f"[{mins:02d}:{secs:05.2f}]{text_str}")
                            props['lyrics_sync'] = "\n".join(lrc_lines)
                        except: pass
                    if hasattr(tags, 'version'):
                        props['tag_ver'] = f"ID3v{tags.version[0]}.{tags.version[1]}"
                    tsse = tags.getall('TSSE')
                    if tsse: props['encoder'] = tsse[0].text[0]
                    elif getattr(audio.info, 'encoder_info', None):
                        props['encoder'] = audio.info.encoder_info
                    for txxx in tags.getall('TXXX'):
                        if txxx.desc and txxx.desc.upper() == 'REPLAYGAIN_TRACK_GAIN':
                            if txxx.text:
                                props['replaygain'] = str(txxx.text[0])
                            break
                elif ext in ['flac', 'ogg']:
                    props['albumartist'] = tags.get('ALBUMARTIST', [''])[0]
                    props['composer'] = tags.get('COMPOSER', [''])[0]
                    props['lyrics_static'] = tags.get('UNSYNCED LYRICS', [''])[0]
                    props['lyrics_sync'] = tags.get('LYRICS', [''])[0]
                    if not props['lyrics_static'] and not props['lyrics_sync']:
                        props['lyrics_static'] = tags.get('UNSYNCEDLYRICS', [''])[0]
                    props['tag_ver'] = 'Vorbis Comments'
                    props['encoder'] = tags.get('ENCODER', ['Desconocido'])[0]
                    rg = tags.get('REPLAYGAIN_TRACK_GAIN', [])
                    if rg: props['replaygain'] = rg[0]
                elif ext in ['m4a', 'mp4']:
                    props['albumartist'] = tags.get('aART', [''])[0]
                    props['composer'] = tags.get('\xa9wrt', [''])[0]
                    props['lyrics_static'] = tags.get('\xa9lyr', [''])[0]
                    props['lyrics_sync'] = tags.get('LYRICS', [''])[0]
                    trkn = tags.get('trkn')
                    if trkn and isinstance(trkn, list):
                        props['tracknumber'] = f"{trkn[0][0]}/{trkn[0][1]}" if trkn[0][1] else str(trkn[0][0])
                    props['tag_ver'] = 'Apple/MP4 (Atoms)'
                    props['encoder'] = tags.get('\xa9too', ['Desconocido'])[0]
                    rg_mp4 = tags.get('----:com.apple.iTunes:replaygain_track_gain')
                    if rg_mp4:
                        try:
                            props['replaygain'] = rg_mp4[0].decode('utf-8')
                        except AttributeError:
                            props['replaygain'] = str(rg_mp4[0])
                        except:
                            pass
        except Exception:
            pass
        return props
    @staticmethod
    def save_metadata(filepath, metadata, new_cover_path=None):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"El archivo no existe: {filepath}")
        audio = mutagen.File(filepath)
        if audio is None:
            raise ValueError("Formato de audio no soportado o archivo corrupto.")
        ext = os.path.splitext(filepath)[1].lower()
        try:
            if ext == '.mp3':
                MetadataEditorService._save_mp3(audio, filepath, metadata, new_cover_path)
            elif ext == '.flac':
                MetadataEditorService._save_flac(audio, metadata, new_cover_path)
            elif ext in ['.m4a', '.mp4']:
                MetadataEditorService._save_m4a(audio, metadata, new_cover_path)
            elif ext == '.ogg':
                MetadataEditorService._save_ogg(audio, metadata, new_cover_path)
            else:
                MetadataEditorService._save_generic(audio, metadata)
            return True
        except Exception as e:
            logging.error(f"Error crítico al guardar metadatos en {filepath}: {traceback.format_exc()}")
            raise e
    @staticmethod
    def _save_mp3(audio, filepath, metadata, cover_path):
        if audio.tags is None:
            try:
                audio.add_tags()
            except ID3Error:
                audio.tags = ID3(filepath)
        tags = audio.tags
        from mutagen.id3 import TPE2, TCOM
        if 'title' in metadata: tags.add(TIT2(encoding=3, text=metadata['title']))
        if 'artist' in metadata: tags.add(TPE1(encoding=3, text=metadata['artist']))
        if 'album' in metadata: tags.add(TALB(encoding=3, text=metadata['album']))
        if 'albumartist' in metadata: tags.add(TPE2(encoding=3, text=metadata['albumartist']))
        if 'composer' in metadata: tags.add(TCOM(encoding=3, text=metadata['composer']))
        if 'year' in metadata: 
            tags.add(TDRC(encoding=3, text=str(metadata['year'])))
            tags.add(TYER(encoding=3, text=str(metadata['year'])))
        if 'genre' in metadata: tags.add(TCON(encoding=3, text=metadata['genre']))
        if 'tracknumber' in metadata: tags.add(TRCK(encoding=3, text=str(metadata['tracknumber'])))
        if 'lyrics_static' in metadata:
            keys_to_remove = [k for k in tags.keys() if k.startswith('USLT')]
            for k in keys_to_remove: tags.pop(k)
            if metadata['lyrics_static'].strip():
                tags.add(USLT(encoding=3, lang='eng', desc='', text=metadata['lyrics_static']))
        if 'lyrics_sync' in metadata:
            keys_to_remove = [k for k in tags.keys() if k.startswith('SYLT')]
            for k in keys_to_remove: tags.pop(k)
            sync_text = metadata['lyrics_sync'].strip()
            if sync_text:
                import re
                sylt_data = []
                for line in sync_text.split('\n'):
                    m = re.match(r'^\s*\[(\d+):(\d+(?:\.\d+)?)\](.*)', line)
                    if m:
                        mins, secs, text = m.groups()
                        time_ms = int(mins) * 60000 + int(float(secs) * 1000)
                        sylt_data.append((text.strip(), time_ms))
                if sylt_data:
                    tags.add(SYLT(encoding=3, lang='eng', format=2, type=1, desc='', text=sylt_data))
        if cover_path and os.path.exists(cover_path):
            with open(cover_path, 'rb') as f:
                img_data = f.read()
            keys_to_remove = [k for k in tags.keys() if k.startswith('APIC')]
            for k in keys_to_remove:
                tags.pop(k)
            mime = 'image/png' if cover_path.lower().endswith('.png') else 'image/jpeg'
            tags.add(
                APIC(
                    encoding=3, 
                    mime=mime, 
                    type=3,                       
                    desc='Front Cover',
                    data=img_data
                )
            )
        audio.save()
    @staticmethod
    def _save_flac(audio, metadata, cover_path):
        if 'title' in metadata: audio['TITLE'] = metadata['title']
        if 'artist' in metadata: audio['ARTIST'] = metadata['artist']
        if 'album' in metadata: audio['ALBUM'] = metadata['album']
        if 'albumartist' in metadata: audio['ALBUMARTIST'] = metadata['albumartist']
        if 'composer' in metadata: audio['COMPOSER'] = metadata['composer']
        if 'year' in metadata: 
            audio['DATE'] = str(metadata['year'])
            audio['YEAR'] = str(metadata['year'])
        if 'genre' in metadata: audio['GENRE'] = metadata['genre']
        if 'tracknumber' in metadata: audio['TRACKNUMBER'] = str(metadata['tracknumber'])
        if 'lyrics_static' in metadata: audio['UNSYNCED LYRICS'] = metadata['lyrics_static']
        if 'lyrics_sync' in metadata: audio['LYRICS'] = metadata['lyrics_sync']
        if cover_path and os.path.exists(cover_path):
            with open(cover_path, 'rb') as f:
                img_data = f.read()
            pic = Picture()
            pic.type = 3              
            pic.mime = 'image/png' if cover_path.lower().endswith('.png') else 'image/jpeg'
            pic.desc = 'Front Cover'
            pic.data = img_data
            audio.clear_pictures()
            audio.add_picture(pic)
        audio.save()
    @staticmethod
    def _save_m4a(audio, metadata, cover_path):
        if 'title' in metadata: audio['\xa9nam'] = metadata['title']
        if 'artist' in metadata: audio['\xa9ART'] = metadata['artist']
        if 'album' in metadata: audio['\xa9alb'] = metadata['album']
        if 'albumartist' in metadata: audio['aART'] = metadata['albumartist']
        if 'composer' in metadata: audio['\xa9wrt'] = metadata['composer']
        if 'year' in metadata: audio['\xa9day'] = str(metadata['year'])
        if 'genre' in metadata: audio['\xa9gen'] = metadata['genre']
        if 'lyrics_static' in metadata: audio['\xa9lyr'] = metadata['lyrics_static']
        if 'lyrics_sync' in metadata: audio['LYRICS'] = metadata['lyrics_sync']
        if 'tracknumber' in metadata:
            try:
                val = str(metadata['tracknumber'])
                if '/' in val:
                    parts = val.split('/')
                    audio['trkn'] = [(int(parts[0]), int(parts[1]))]
                else:
                    audio['trkn'] = [(int(val), 0)]
            except:
                pass
        if cover_path and os.path.exists(cover_path):
            with open(cover_path, 'rb') as f:
                img_data = f.read()
            img_format = MP4Cover.FORMAT_PNG if cover_path.lower().endswith('.png') else MP4Cover.FORMAT_JPEG
            audio['covr'] = [MP4Cover(img_data, imageformat=img_format)]
        audio.save()
    @staticmethod
    def _save_ogg(audio, metadata, cover_path):
        if 'title' in metadata: audio['TITLE'] = metadata['title']
        if 'artist' in metadata: audio['ARTIST'] = metadata['artist']
        if 'album' in metadata: audio['ALBUM'] = metadata['album']
        if 'albumartist' in metadata: audio['ALBUMARTIST'] = metadata['albumartist']
        if 'composer' in metadata: audio['COMPOSER'] = metadata['composer']
        if 'year' in metadata: audio['DATE'] = str(metadata['year'])
        if 'genre' in metadata: audio['GENRE'] = metadata['genre']
        if 'tracknumber' in metadata: audio['TRACKNUMBER'] = str(metadata['tracknumber'])
        if 'lyrics_static' in metadata: audio['UNSYNCED LYRICS'] = metadata['lyrics_static']
        if 'lyrics_sync' in metadata: audio['LYRICS'] = metadata['lyrics_sync']
        if cover_path and os.path.exists(cover_path):
            with open(cover_path, 'rb') as f:
                img_data = f.read()
            pic = Picture()
            pic.type = 3
            pic.mime = 'image/png' if cover_path.lower().endswith('.png') else 'image/jpeg'
            pic.desc = 'Front Cover'
            pic.data = img_data
            import base64
            b64_data = base64.b64encode(pic.write()).decode('ascii')
            audio['metadata_block_picture'] = [b64_data]
        audio.save()
    @staticmethod
    def _save_generic(audio, metadata):
        if hasattr(audio, 'tags') and audio.tags is not None:
            if 'title' in metadata: audio.tags['title'] = metadata['title']
            if 'artist' in metadata: audio.tags['artist'] = metadata['artist']
            if 'album' in metadata: audio.tags['album'] = metadata['album']
            if 'year' in metadata: audio.tags['date'] = str(metadata['year'])
            if 'genre' in metadata: audio.tags['genre'] = metadata['genre']
            audio.save()