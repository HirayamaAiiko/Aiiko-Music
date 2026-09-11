import os
import json
import gzip
import time
import logging
import base64
import uuid
from contextlib import closing
from database import get_db_connection
from settings_manager import settings
from core.language_manager import tr
BACKUP_EXTENSION = ".aiiko"
BACKUP_FILTER = "Aiiko Music Backup (*.aiiko)"
_APP_SIGNATURE = "AiikoMusicBackup"
_FORMAT_VERSION = "2.0"
EXPORTABLE_TABLES = [
    {
        "key": "play_stats",
        "label": tr("Estadísticas de reproducción"),
        "description": tr("Conteos de reproducciones y última vez escuchada"),
    },
    {
        "key": "play_history",
        "label": tr("Historial de escucha"),
        "description": tr("Registro detallado de cada canción reproducida"),
    },
    {
        "key": "favorites",
        "label": tr("Favoritos"),
        "description": tr("Lista de canciones marcadas como favoritas"),
    },
    {
        "key": "playlists",
        "label": tr("Playlists"),
        "description": tr("Todas las playlists y sus canciones"),
    },
    {
        "key": "settings",
        "label": tr("Perfil y ajustes"),
        "description": tr("Nombre, foto de perfil y cumpleaños"),
    },
]
def get_default_filename():
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"Aiiko_Music_Backup_{ts}{BACKUP_EXTENSION}"
def export_data(filepath: str, table_keys: list[str]) -> dict:
    data = {
        "_signature": _APP_SIGNATURE,
        "_version": _FORMAT_VERSION,
        "_exported_at": time.time(),
        "_tables": table_keys,
    }
    counts = {}
    try:
        with closing(get_db_connection()) as conn:
            c = conn.cursor()
            if "play_stats" in table_keys:
                c.execute(
                    "SELECT filepath, title, artist, play_count, last_played "
                    "FROM tracks WHERE play_count > 0 OR last_played > 0"
                )
                rows = [
                    {"filepath": r[0], "title": r[1], "artist": r[2], "play_count": r[3], "last_played": r[4]}
                    for r in c.fetchall()
                ]
                data["play_stats"] = rows
                counts["play_stats"] = len(rows)
            if "play_history" in table_keys:
                c.execute(
                    "SELECT h.filepath, t.title, t.artist, h.timestamp, h.listen_type, "
                    "h.duration_listened_ms, h.total_duration_ms "
                    "FROM play_history h "
                    "LEFT JOIN tracks t ON h.filepath = t.filepath"
                )
                rows = [
                    {
                        "filepath": r[0], "title": r[1], "artist": r[2],
                        "timestamp": r[3], "listen_type": r[4],
                        "duration_listened_ms": r[5], "total_duration_ms": r[6],
                    }
                    for r in c.fetchall()
                ]
                data["play_history"] = rows
                counts["play_history"] = len(rows)
            if "favorites" in table_keys:
                c.execute(
                    "SELECT f.filepath, t.title, t.artist, f.added_at "
                    "FROM favorites f "
                    "LEFT JOIN tracks t ON f.filepath = t.filepath"
                )
                rows = [
                    {"filepath": r[0], "title": r[1], "artist": r[2], "added_at": r[3]}
                    for r in c.fetchall()
                ]
                data["favorites"] = rows
                counts["favorites"] = len(rows)
            if "playlists" in table_keys:
                c.execute("SELECT id, name, description, cover_path FROM playlists")
                playlists = []
                for row in c.fetchall():
                    c.execute(
                        "SELECT pt.filepath, t.title, t.artist, pt.position "
                        "FROM playlist_tracks pt "
                        "LEFT JOIN tracks t ON pt.filepath = t.filepath "
                        "WHERE pt.playlist_id = ? ORDER BY pt.position", (row[0],)
                    )
                    tracks = [
                        {"filepath": t[0], "title": t[1], "artist": t[2], "position": t[3]}
                        for t in c.fetchall()
                    ]
                    cover_path = row[3]
                    cover_b64 = None
                    if cover_path and os.path.exists(cover_path):
                        try:
                            with open(cover_path, "rb") as f:
                                cover_b64 = base64.b64encode(f.read()).decode("utf-8")
                        except Exception as e:
                            logging.error(f"Error codificando cover {cover_path}: {e}")
                    playlists.append({
                        "name": row[1], "description": row[2],
                        "cover_path": cover_path, "cover_b64": cover_b64, "tracks": tracks,
                    })
                data["playlists"] = playlists
                counts["playlists"] = len(playlists)
            if "settings" in table_keys:
                profile_photo_path = settings.get("user_profile_photo", "")
                profile_photo_b64 = None
                if profile_photo_path and os.path.exists(profile_photo_path):
                    try:
                        with open(profile_photo_path, "rb") as f:
                            profile_photo_b64 = base64.b64encode(f.read()).decode("utf-8")
                    except Exception as e:
                        logging.error(f"Error codificando foto de perfil: {e}")
                data["settings"] = {
                    "profile_name": settings.get("user_profile_name", ""),
                    "profile_photo": profile_photo_path,
                    "profile_photo_b64": profile_photo_b64,
                    "profile_birthday": settings.get("user_profile_birthday", ""),
                    "ui_scale": settings.get("ui_scale", 100),
                    "fade_audio": settings.get("fade_audio", True),
                    "square_covers": settings.get("square_covers", True),
                    "mini_player_glow": settings.get("mini_player_glow", False),
                    "eq_preset": settings.get("eq_preset", "Flat"),
                    "eq_preamp": settings.get("eq_preamp", 0.0),
                    "gapless_enabled": settings.get("gapless_enabled", True),
                    "app_theme": settings.get("app_theme", "Auto"),
                    "app_accent_name": settings.get("app_accent_name", "Teal (AIIKO)"),
                    "language": settings.get("language", "Auto"),
                    "startup_tab": settings.get("startup_tab", "dashboard"),
                    "discord_rpc": settings.get("rpc", False),
                    "smooth_lyrics": settings.get("smooth_lyrics", True),
                    "translation_lang": settings.get("translation_lang", "es"),
                    "dynamic_bg": settings.get("dynamic_bg", True),
                    "minimize_to_tray": settings.get("minimize_to_tray", False),
                    "close_to_tray": settings.get("close_to_tray", False),
                    "enable_page_animations": settings.get("enable_page_animations", True),
                    "eq_bands": settings.get("eq_bands", [0.0]*10),
                    "eq_enabled": settings.get("eq_enabled", False),
                    "crossfade_enabled": settings.get("crossfade_enabled", False),
                    "crossfade_seconds": settings.get("crossfade_seconds", 6),
                    "gradient_enabled": settings.get("gradient_enabled", False),
                }
                counts["settings"] = 1
        json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        with gzip.open(filepath, "wb") as f:
            f.write(json_bytes)
        logging.info(f"Backup exportado exitosamente: {filepath} ({counts})")
        return {"success": True, "message": "Exportación exitosa", "counts": counts}
    except Exception as e:
        logging.error(f"Error exportando backup: {e}")
        return {"success": False, "message": str(e), "counts": {}}
def validate_backup(filepath: str) -> dict | None:
    try:
        with gzip.open(filepath, "rb") as f:
            raw = f.read()
        data = json.loads(raw.decode("utf-8"))
        if data.get("_signature") != _APP_SIGNATURE:
            return _try_legacy_format(filepath)
        return {
            "version": data.get("_version", "?"),
            "exported_at": data.get("_exported_at", 0),
            "tables": data.get("_tables", []),
            "_data": data,
        }
    except gzip.BadGzipFile:
        return _try_legacy_format(filepath)
    except Exception as e:
        logging.error(f"Error validando backup: {e}")
        return None
def _try_legacy_format(filepath: str) -> dict | None:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("_meta", {}).get("app") == "Aiiko Music":
            return {
                "version": "1.0 (legacy)",
                "exported_at": data.get("_meta", {}).get("exported_at", 0),
                "tables": data.get("_meta", {}).get("tables", []),
                "_data": data,
            }
    except Exception:
        pass
    return None
def _resolve_filepath(c, filepath: str, title: str | None, artist: str | None) -> str | None:
    if not filepath:
        return None
    c.execute("SELECT filepath FROM tracks WHERE filepath = ?", (filepath,))
    if c.fetchone():
        return filepath
    if title and artist:
        c.execute("SELECT filepath FROM tracks WHERE title = ? AND artist = ?", (title, artist))
        row = c.fetchone()
        if row:
            return row[0]
    return None
def import_data(filepath: str, table_filter: list[str] | None = None) -> dict:
    info = validate_backup(filepath)
    if not info:
        return {
            "success": False,
            "message": "El archivo no es un backup válido de Aiiko Music.",
            "imported": [],
        }
    data = info["_data"]
    imported = []
    allowed = set(table_filter) if table_filter else None
    try:
        with closing(get_db_connection()) as conn:
            with conn:
                c = conn.cursor()
                if "play_stats" in data and (allowed is None or "play_stats" in allowed):
                    for s in data["play_stats"]:
                        real_path = _resolve_filepath(c, s["filepath"], s.get("title"), s.get("artist"))
                        if real_path:
                            c.execute(
                                "UPDATE tracks SET play_count = MAX(play_count, ?), "
                                "last_played = MAX(last_played, ?) WHERE filepath = ?",
                                (s["play_count"], s["last_played"], real_path),
                            )
                    imported.append("Estadísticas")
                if "play_history" in data and (allowed is None or "play_history" in allowed):
                    for h in data["play_history"]:
                        real_path = _resolve_filepath(c, h["filepath"], h.get("title"), h.get("artist"))
                        if real_path:
                            c.execute(
                                "SELECT COUNT(*) FROM play_history "
                                "WHERE filepath = ? AND timestamp = ?",
                                (real_path, h["timestamp"]),
                            )
                            if c.fetchone()[0] == 0:
                                c.execute(
                                    "INSERT INTO play_history (filepath, timestamp, listen_type, "
                                    "duration_listened_ms, total_duration_ms) VALUES (?, ?, ?, ?, ?)",
                                    (
                                        real_path, h["timestamp"], h["listen_type"],
                                        h.get("duration_listened_ms", 0),
                                        h.get("total_duration_ms", 0),
                                    ),
                                )
                    imported.append("Historial")
                if "favorites" in data and (allowed is None or "favorites" in allowed):
                    for fav in data["favorites"]:
                        real_path = _resolve_filepath(c, fav["filepath"], fav.get("title"), fav.get("artist"))
                        if real_path:
                            c.execute(
                                "INSERT OR IGNORE INTO favorites (filepath, added_at) VALUES (?, ?)",
                                (real_path, fav.get("added_at", 0)),
                            )
                    imported.append("Favoritos")
                if "playlists" in data and (allowed is None or "playlists" in allowed):
                    for pl in data["playlists"]:
                        c.execute("SELECT id FROM playlists WHERE name = ?", (pl["name"],))
                        existing = c.fetchone()
                        if not existing:
                            new_cover_path = pl.get("cover_path", "")
                            cover_b64 = pl.get("cover_b64")
                            if cover_b64:
                                try:
                                    from config import CACHE_DIR
                                    covers_dir = os.path.join(CACHE_DIR, "playlists")
                                    os.makedirs(covers_dir, exist_ok=True)
                                    filename = f"{uuid.uuid4().hex}.jpg"
                                    dest_path = os.path.join(covers_dir, filename)
                                    with open(dest_path, "wb") as f:
                                        f.write(base64.b64decode(cover_b64))
                                    new_cover_path = dest_path
                                except Exception as e:
                                    logging.error(f"Error decodificando cover_b64 para {pl['name']}: {e}")
                            c.execute(
                                "INSERT INTO playlists (name, description, cover_path) VALUES (?, ?, ?)",
                                (pl["name"], pl.get("description", ""), new_cover_path),
                            )
                            pl_id = c.lastrowid
                            for t in pl.get("tracks", []):
                                real_path = _resolve_filepath(c, t["filepath"], t.get("title"), t.get("artist"))
                                if real_path:
                                    c.execute(
                                        "INSERT INTO playlist_tracks (playlist_id, filepath, position) "
                                        "VALUES (?, ?, ?)",
                                        (pl_id, real_path, t["position"]),
                                    )
                        imported.append("Playlists")
                if "settings" in data and (allowed is None or "settings" in allowed):
                    s = data["settings"]
                    if s.get("profile_name"):
                        settings.set("user_profile_name", s["profile_name"])
                    if s.get("profile_birthday"):
                        settings.set("user_profile_birthday", s["profile_birthday"])
                    profile_photo = s.get("profile_photo")
                    profile_photo_b64 = s.get("profile_photo_b64")
                    if profile_photo_b64:
                        try:
                            from config import CACHE_DIR
                            profile_dir = os.path.join(CACHE_DIR, "profile")
                            os.makedirs(profile_dir, exist_ok=True)
                            filename = f"avatar_{uuid.uuid4().hex}.jpg"
                            dest_path = os.path.join(profile_dir, filename)
                            with open(dest_path, "wb") as f:
                                f.write(base64.b64decode(profile_photo_b64))
                            settings.set("user_profile_photo", dest_path)
                        except Exception as e:
                            logging.error(f"Error decodificando profile_photo_b64: {e}")
                            if profile_photo:
                                settings.set("user_profile_photo", profile_photo)
                    elif profile_photo:                                        
                        settings.set("user_profile_photo", profile_photo)
                    generic_keys = [
                        "ui_scale", "fade_audio", "square_covers", "mini_player_glow",
                        "eq_preset", "eq_preamp", "gapless_enabled", "app_theme",
                        "app_accent_name", "language", "startup_tab", "discord_rpc", "smooth_lyrics",
                        "translation_lang", "dynamic_bg", "minimize_to_tray", "close_to_tray",
                        "enable_page_animations", "eq_bands", "eq_enabled",
                        "crossfade_enabled", "crossfade_seconds", "gradient_enabled"
                    ]
                    for key in generic_keys:
                        if key in s:
                            real_key = "rpc" if key == "discord_rpc" else key
                            settings.set(real_key, s[key])
                    settings.save()
                    imported.append("Perfil y Ajustes")
        logging.info(f"Backup importado: {imported}")
        return {"success": True, "message": "Importación exitosa", "imported": imported}
    except Exception as e:
        logging.error(f"Error importando backup: {e}")
        return {"success": False, "message": str(e), "imported": []}