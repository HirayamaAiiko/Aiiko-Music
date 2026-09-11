from PyQt6.QtCore import QThread, pyqtSignal
class DashboardRefreshWorker(QThread):
    data_ready = pyqtSignal(dict)
    def __init__(self, library, time_range="month", parent=None):
        super().__init__(parent)
        self._library = library
        self._time_range = time_range
    def run(self):
        try:
            from controllers.analytics_controller import AnalyticsController as AC
            top_artists = AC.get_top_artists(limit=5)
            data = {
                "stats":   AC.get_library_stats(),
                "recent":  AC.get_recently_played(limit=10),
                "top":     AC.get_top_tracks(limit=10, time_range=self._time_range),
                "added":   AC.get_recently_added(limit=15, days=14),
                "artists": top_artists,
                "weekly":  AC.get_weekly_listening_stats(),
                "genres":  AC.get_top_genres(limit=5),
                "playlist_info": self._get_first_playlist_info(),
                "recent_history": self._get_last_session_info(),
                "artist_covers": self._build_artist_covers(top_artists),
            }
            self.data_ready.emit(data)
        except Exception as e:
            import logging
            logging.error(f"DashboardRefreshWorker error: {e}", exc_info=True)
    def _get_first_playlist_info(self):
        try:
            from database import get_playlists_db
            pl_dict = get_playlists_db()
            if not pl_dict: return None
            pl_name = list(pl_dict.keys())[0]
            paths = set(pl_dict[pl_name])
            if not paths: return None
            dur = 0
            for t in self._library:
                if t.filepath in paths:
                    dur += getattr(t, 'duration', 0)
            return {"name": pl_name, "count": len(paths), "duration_ms": dur}
        except Exception:
            return None
    def _get_last_session_info(self):
        try:
            from controllers.analytics_controller import AnalyticsController as AC
            from database import get_db_connection
            from contextlib import closing
            import time
            recent = AC.get_recently_played(limit=2)
            if not recent: return None
            now = time.time()
            recent[0]["days_since_app_used"] = (now - recent[0]["last_played"]) / 86400
            filepath = recent[0]["filepath"]
            with closing(get_db_connection()) as conn:
                c = conn.cursor()
                c.execute("SELECT timestamp FROM play_history WHERE filepath = ? ORDER BY timestamp DESC LIMIT 2", (filepath,))
                rows = c.fetchall()
                if len(rows) >= 2:
                    last_ts = rows[0][0]
                    prev_ts = rows[1][0]
                    days_between = (last_ts - prev_ts) / 86400
                    recent[0]["days_since_prev_play"] = days_between
                else:
                    recent[0]["days_since_prev_play"] = 0
            return recent
        except Exception:
            return None
    def _build_artist_covers(self, top_artists):
        from controllers.analytics_controller import AnalyticsController as AC
        covers = {}
        try:
            from database import get_db_connection
            from contextlib import closing
            with closing(get_db_connection()) as conn:
                c = conn.cursor()
                from utils import normalize_artist_name
                c.execute("SELECT name, cover_path FROM artists WHERE cover_path IS NOT NULL AND cover_path != ''")
                for name, path in c.fetchall():
                    norm_name = normalize_artist_name(name)
                    if norm_name:
                        covers[norm_name] = path
        except Exception:
            pass
        target_artists = {a["artist"] for a in top_artists}
        missing = target_artists - set(covers.keys())
        if missing:
            for t in self._library:
                if not missing:
                    break
                cover = getattr(t, 'cover_path', None)
                if cover and any(m.lower() in t.artist.lower() for m in missing):
                    for ind in AC._split_artists(t.artist):
                        norm_ind = normalize_artist_name(ind)
                        if norm_ind in missing:
                            covers[norm_ind] = cover
                            missing.remove(norm_ind)
        return covers