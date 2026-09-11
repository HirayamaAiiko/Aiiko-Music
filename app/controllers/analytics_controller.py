import logging
from contextlib import closing
from database import get_db_connection
from models import Track
class AnalyticsController:
    @staticmethod
    def get_top_tracks(limit=10, time_range="month"):
        results = []
        try:
            import time
            import datetime as dt
            now = time.time()
            if time_range == "today":
                midnight = dt.datetime.combine(dt.date.today(), dt.time.min)
                start_time = midnight.timestamp()
            elif time_range == "week":
                start_time = now - (86400 * 7)
            elif time_range == "month":
                start_time = now - (86400 * 30)
            else:
                start_time = 0
            with closing(get_db_connection()) as conn:
                c = conn.cursor()
                if start_time == 0:
                    c.execute(
                        "SELECT filepath, title, artist, album, cover_path, play_count "
                        "FROM tracks WHERE play_count > 0 "
                        "ORDER BY play_count DESC LIMIT ?",
                        (limit,)
                    )
                else:
                    c.execute(
                        """
                        SELECT t.filepath, t.title, t.artist, t.album, t.cover_path, COUNT(h.id) as period_plays
                        FROM play_history h
                        JOIN tracks t ON h.filepath = t.filepath
                        WHERE h.timestamp >= ? AND h.listen_type IN ('listened', 'completed')
                        GROUP BY h.filepath
                        ORDER BY period_plays DESC
                        LIMIT ?
                        """,
                        (start_time, limit)
                    )
                for row in c.fetchall():
                    results.append({
                        "filepath": row[0],
                        "title": row[1],
                        "artist": row[2],
                        "album": row[3],
                        "cover_path": row[4],
                        "play_count": row[5],
                    })
        except Exception as e:
            logging.error(f"Analytics – get_top_tracks: {e}")
        return results
    @staticmethod
    def get_recently_played(limit=8):
        results = []
        try:
            with closing(get_db_connection()) as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT filepath, title, artist, album, cover_path, last_played "
                    "FROM tracks WHERE last_played > 0 "
                    "ORDER BY last_played DESC LIMIT ?",
                    (limit,)
                )
                for row in c.fetchall():
                    results.append({
                        "filepath": row[0],
                        "title": row[1],
                        "artist": row[2],
                        "album": row[3],
                        "cover_path": row[4],
                        "last_played": row[5],
                    })
        except Exception as e:
            logging.error(f"Analytics – get_recently_played: {e}")
        return results
    @staticmethod
    def get_recently_added(limit=10, days=14):
        results = []
        try:
            import time
            cutoff = time.time() - (days * 86400)
            with closing(get_db_connection()) as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT filepath, title, artist, album, cover_path, ctime "
                    "FROM tracks WHERE ctime > ? "
                    "ORDER BY ctime DESC LIMIT ?",
                    (cutoff, limit)
                )
                for row in c.fetchall():
                    results.append({
                        "filepath": row[0],
                        "title": row[1],
                        "artist": row[2],
                        "album": row[3],
                        "cover_path": row[4],
                        "ctime": row[5],
                    })
        except Exception as e:
            logging.error(f"Analytics – get_recently_added: {e}")
        return results
    @staticmethod
    def get_library_stats():
        stats = {"total_tracks": 0, "total_duration_ms": 0, "total_artists": 0, "total_albums": 0, "total_plays": 0}
        try:
            with closing(get_db_connection()) as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*), COALESCE(SUM(duration), 0), COALESCE(SUM(play_count), 0) FROM tracks")
                row = c.fetchone()
                if row:
                    stats["total_tracks"] = row[0]
                    stats["total_duration_ms"] = row[1]
                    stats["total_plays"] = row[2]
                c.execute("SELECT DISTINCT artist FROM tracks WHERE artist != 'Artista Desconocido'")
                from utils import get_artists_from_string
                unique_artists = set()
                for row in c.fetchall():
                    for a in get_artists_from_string(row[0]):
                        unique_artists.add(a.lower())
                stats["total_artists"] = len(unique_artists)
                c.execute("SELECT COUNT(DISTINCT album) FROM tracks WHERE album != 'Álbum Desconocido'")
                row = c.fetchone()
                if row:
                    stats["total_albums"] = row[0]
        except Exception as e:
            logging.error(f"Analytics – get_library_stats: {e}")
        return stats
    @staticmethod
    def get_user_profile_stats():
        stats = {"total_plays": 0, "total_listened_ms": 0, "unique_songs": 0}
        try:
            with closing(get_db_connection()) as conn:
                c = conn.cursor()
                c.execute("SELECT COALESCE(SUM(play_count), 0), COUNT(*) FROM tracks WHERE play_count > 0")
                row = c.fetchone()
                if row:
                    stats["total_plays"] = row[0]
                    stats["unique_songs"] = row[1]
                c.execute("SELECT COALESCE(SUM(duration_listened_ms), 0) FROM play_history")
                row = c.fetchone()
                if row:
                    stats["total_listened_ms"] = row[0]
        except Exception as e:
            logging.error(f"Analytics – get_user_profile_stats: {e}")
        return stats
    @staticmethod
    def _split_artists(raw: str) -> list[str]:
        import re
        pattern = r'\s*(?:,\s*|\s+&\s+|\s+feat\.?\s+|\s+ft\.?\s+|\s+Feat\.?\s+|\s+[xX]\s+|\s*/\s*|\s*;\s*|\s+with\s+)\s*'
        parts = re.split(pattern, raw)
        return [p.strip() for p in parts if p.strip()]
    @staticmethod
    def get_top_artists(limit=5):
        from collections import defaultdict
        artist_plays = defaultdict(int)
        try:
            with closing(get_db_connection()) as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT artist, SUM(play_count) as total_plays "
                    "FROM tracks WHERE play_count > 0 AND artist != 'Artista Desconocido' "
                    "GROUP BY artist"
                )
                from utils import normalize_artist_name
                for row in c.fetchall():
                    raw_artist = row[0]
                    total = row[1]
                    for individual in AnalyticsController._split_artists(raw_artist):
                        norm_ind = normalize_artist_name(individual)
                        if norm_ind:
                            artist_plays[norm_ind] += total
        except Exception as e:
            logging.error(f"Analytics – get_top_artists: {e}")
        sorted_artists = sorted(artist_plays.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [
            {"artist": name, "total_plays": plays, "track_count": 0}
            for name, plays in sorted_artists
        ]
    @staticmethod
    def format_duration(ms):
        total_seconds = ms / 1000
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        if hours > 0:
            return f"{hours} h, {minutes} min"
        return f"{minutes} min"
    @staticmethod
    def get_listen_quality_stats():
        stats = {"completed": 0, "listened": 0, "partial": 0, "played": 0}
        try:
            with closing(get_db_connection()) as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT listen_type, COUNT(*) FROM play_history GROUP BY listen_type"
                )
                for row in c.fetchall():
                    if row[0] in stats:
                        stats[row[0]] = row[1]
        except Exception as e:
            logging.error(f"Analytics – get_listen_quality_stats: {e}")
        return stats
    @staticmethod
    def get_weekly_listening_stats():
        import time, datetime as dt
        now = time.time()
        week_start = now - 7  * 86400
        prev_start = now - 14 * 86400
        result = {
            "total_ms": 0, "total_tracks": 0,
            "prev_ms":  0, "prev_tracks":  0,
            "by_day": [0] * 7,                                   
        }
        try:
            with closing(get_db_connection()) as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT COALESCE(SUM(duration_listened_ms),0), COUNT(*) "
                    "FROM play_history WHERE timestamp > ? "
                    "AND listen_type IN ('listened','completed')",
                    (week_start,)
                )
                row = c.fetchone()
                if row:
                    result["total_ms"]     = row[0]
                    result["total_tracks"] = row[1]
                c.execute(
                    "SELECT COALESCE(SUM(duration_listened_ms),0), COUNT(*) "
                    "FROM play_history WHERE timestamp > ? AND timestamp <= ? "
                    "AND listen_type IN ('listened','completed')",
                    (prev_start, week_start)
                )
                row = c.fetchone()
                if row:
                    result["prev_ms"]     = row[0]
                    result["prev_tracks"] = row[1]
                c.execute(
                    "SELECT timestamp FROM play_history WHERE timestamp > ? "
                    "AND listen_type IN ('listened','completed')",
                    (week_start,)
                )
                today = dt.date.today()
                for (ts,) in c.fetchall():
                    day = dt.date.fromtimestamp(ts)
                    delta = (today - day).days
                    if 0 <= delta < 7:
                        result["by_day"][6 - delta] += 1
        except Exception as e:
            logging.error(f"Analytics – get_weekly_listening_stats: {e}")
        return result
    @staticmethod
    def get_top_genres(limit=5):
        results = []
        try:
            with closing(get_db_connection()) as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT genre, COUNT(*) as cnt FROM tracks "
                    "WHERE genre != '' AND genre != 'Desconocido' "
                    "GROUP BY genre ORDER BY cnt DESC LIMIT ?",
                    (limit,)
                )
                rows = c.fetchall()
                total = sum(r[1] for r in rows) or 1
                for row in rows:
                    results.append({
                        "genre": row[0],
                        "count": row[1],
                        "pct": round(row[1] / total * 100),
                    })
        except Exception as e:
            logging.error(f"Analytics – get_top_genres: {e}")
        return results