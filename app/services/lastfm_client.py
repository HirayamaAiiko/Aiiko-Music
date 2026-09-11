import requests
import json
import logging
import urllib.parse
from functools import lru_cache
class LastFMClient:
    API_KEY = "YOUR_LASTFM_API_KEY"
    BASE_URL = "http://ws.audioscrobbler.com/2.0/"
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "AIIKOMusicPro/1.0"})
    def get_artist_info(self, artist_name, lang="es"):
        if not artist_name or artist_name.lower() == "desconocido":
            return None
        params = {
            "method": "artist.getinfo",
            "artist": artist_name,
            "api_key": self.API_KEY,
            "format": "json",
            "autocorrect": 1,
            "lang": lang
        }
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "artist" in data:
                    artist_data = data["artist"]
                    tags = []
                    if "tags" in artist_data and "tag" in artist_data["tags"]:
                        tag_list = artist_data["tags"]["tag"]
                        if isinstance(tag_list, dict):
                            tags.append(tag_list.get("name", "").title())
                        elif isinstance(tag_list, list):
                            tags = [t.get("name", "").title() for t in tag_list if t.get("name")]
                    bio_summary = ""
                    bio_content = ""
                    if "bio" in artist_data:
                        bio_summary = artist_data["bio"].get("summary", "")
                        bio_content = artist_data["bio"].get("content", "")
                        if "<a href=" in bio_summary:
                            bio_summary = bio_summary.split("<a href=")[0].strip()
                        if "<a href=" in bio_content:
                            bio_content = bio_content.split("<a href=")[0].strip()
                    result = {
                        "bio_summary": bio_summary,
                        "bio_content": bio_content,
                        "tags": tags[:5]                  
                    }
                    if not bio_summary and lang == "es":
                        en_result = self.get_artist_info(artist_name, lang="en")
                        if en_result and en_result.get("bio_summary"):
                            result["bio_summary"] = en_result["bio_summary"]
                            result["bio_content"] = en_result["bio_content"]
                            if not result["tags"] and en_result.get("tags"):
                                result["tags"] = en_result["tags"]
                    return result
        except Exception as e:
            logging.error(f"Last.fm API error: {e}")
        return None