import os
import re
from PyQt6.QtGui import QPixmap, QImage, QColor, QPainter, QPainterPath
from PyQt6.QtCore import Qt
SANITIZER_PATTERN = re.compile(r'[\x00-\x1f\x7f-\x9f]')
ARTIST_SPLIT_PATTERN = re.compile(r'[\x00&,;/]')
def get_rounded_pixmap(image_path, size, radius=12):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    if not image_path or not os.path.exists(image_path):
        pixmap.fill(QColor("#2A2A2A"))
        return pixmap
    from PyQt6.QtGui import QImageReader
    from PyQt6.QtCore import QSize
    reader = QImageReader(image_path)
    reader.setScaledSize(QSize(size, size))
    img = reader.read()
    if img.isNull():
        pixmap.fill(QColor("#2A2A2A"))
        return pixmap
    scaled_img = QPixmap.fromImage(img).scaled(
        size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
    )
    out_pixmap = QPixmap(size, size)
    out_pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(out_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size, size, radius, radius)
    painter.setClipPath(path)
    x = (size - scaled_img.width()) // 2
    y = (size - scaled_img.height()) // 2
    painter.drawPixmap(x, y, scaled_img)
    painter.end()
    return out_pixmap
def normalize_artist_name(name):
    if not name: return ""
    name = re.split(r'(?i)\b(?:feat\.?|ft\.?|featuring|remix|mix|vs\.?|x)\b', name)[0]
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'\[.*?\]', '', name)
    return name.strip().title()
def sanitize_text(text):
    if not text: return ""
    return SANITIZER_PATTERN.sub('', text).strip()
def get_artists_from_string(artist_string):
    if not artist_string: return ["Desconocido"]
    strict_parts = re.split(r'[\x00;/]', artist_string)
    artists = []
    for part in strict_parts:
        part = part.strip()
        if not part: continue
        if ',' in part:
            subparts = part.split(',')
            for sp in subparts:
                clean_sp = sanitize_text(sp)
                if clean_sp.startswith('&'):
                    clean_sp = clean_sp[1:].strip()
                elif clean_sp.lower().startswith('and '):
                    clean_sp = clean_sp[4:].strip()
                if clean_sp: artists.append(clean_sp)
        else:
            subparts = part.split('&')
            for sp in subparts:
                clean_sp = sanitize_text(sp)
                if clean_sp: artists.append(clean_sp)
    return artists if artists else ["Desconocido"]
def match_track_to_album(track, target_album, target_artist=None, merge_albums=True):
    clean_album = sanitize_text(track.album).lower()
    t_album = target_album.lower()
    if merge_albums:
        if t_album in ("album_desconocido", "álbum_desconocido", "desconocido"):
            if clean_album in ("album_desconocido", "álbum_desconocido", "desconocido", ""):
                return True
    if sanitize_text(track.album) == target_album:
        if target_artist:
            if merge_albums:
                t_artist = getattr(track, 'album_artist', None) or track.artist
                primary_artist = sanitize_text(get_artists_from_string(t_artist)[0])
                safe_primary_artist = sanitize_text(get_artists_from_string(target_artist)[0])
                return primary_artist == safe_primary_artist
            else:
                t_artist = sanitize_text(getattr(track, 'album_artist', None) or track.artist)
                return t_artist == target_artist
        return True
    return False
def get_album_group_key(track, merge_albums=True):
    clean_album = sanitize_text(track.album)
    if merge_albums:
        if clean_album.lower() in ("álbum desconocido", "album desconocido", "desconocido", ""):
            return "album_desconocido_global"
        else:
            t_artist = getattr(track, 'album_artist', None) or track.artist
            primary_artist = get_artists_from_string(t_artist)[0]
            clean_artist = sanitize_text(primary_artist)
            return f"{clean_album}_|_{clean_artist}"
    else:
        t_artist = getattr(track, 'album_artist', None) or track.artist
        clean_artist = sanitize_text(t_artist)
        return f"{clean_album}_|_{clean_artist}"