import requests
import logging
from PyQt6.QtCore import QThread, pyqtSignal
class LyricsFetcherThread(QThread):
    result_ready = pyqtSignal(list)
    def __init__(self, title, artist):
        super().__init__()
        self.title = title
        self.artist = artist
    def run(self):
        try:
            url = "https://lrclib.net/api/search"
            params = {
                "track_name": self.title,
                "artist_name": self.artist
            }
            headers = {"User-Agent": "AIIKOMusicPro/1.0 (https://github.com/tu-usuario/aiiko)"}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            results = []
            if response.status_code == 200:
                data = response.json()
                if data:
                    for item in data:
                        if item.get('syncedLyrics'):
                            results.append({'text': item['syncedLyrics'], 'is_synced': True, 'id': item.get('id')})
                    for item in data:
                        if not item.get('syncedLyrics') and item.get('plainLyrics'):
                            results.append({'text': item['plainLyrics'], 'is_synced': False, 'id': item.get('id')})
            self.result_ready.emit(results)
        except Exception as e:
            logging.error(f"Error buscando letra online: {e}")
            self.result_ready.emit([])