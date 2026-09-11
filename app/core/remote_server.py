import asyncio
import threading
import logging
import json
import socket
import os
import urllib.parse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import websockets
import h11
from zeroconf import ServiceInfo, Zeroconf
from PyQt6.QtCore import QObject, pyqtSignal
from pydantic import BaseModel
from typing import List
logger = logging.getLogger(__name__)
class SyncRequest(BaseModel):
    client_ids: List[str]
class CommandDispatcher(QObject):
    dispatch = pyqtSignal(dict)
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        if not self.active_connections:
            return
        async def send_to_client(connection):
            try:
                async with asyncio.timeout(2.0):
                    await connection.send_text(message)
                return None
            except Exception:
                return connection
        results = await asyncio.gather(*[send_to_client(c) for c in self.active_connections], return_exceptions=True)
        for res in results:
            if res and isinstance(res, WebSocket):
                self.disconnect(res)
class RemoteServer:
    def __init__(self, main_window, port=8080, server_name="Aiiko Server"):
        self.main_window = main_window
        self.port = port
        self.server_name = server_name
        self.app = FastAPI(title="Aiiko Remote API")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.manager = ConnectionManager()
        self.server_thread = None
        self._uvicorn_server = None
        self.zeroconf = None
        self.loop = None
        self._id_cache = {}
        self.dispatcher = CommandDispatcher()
        self.dispatcher.dispatch.connect(self._execute_on_main_thread)
        self._setup_routes()
        if hasattr(self.main_window, 'audio_engine'):
            try:
                self.main_window.audio_engine.state_changed.connect(self.broadcast_state)
            except Exception:
                pass
        if hasattr(self.main_window, 'playback_controller'):
            try:
                self.main_window.playback_controller.track_loaded.connect(lambda _: self.broadcast_state())
            except Exception:
                pass
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    def get_track_id(self, filepath):
        if filepath not in self._id_cache:
            import hashlib
            self._id_cache[filepath] = hashlib.md5(filepath.encode('utf-8')).hexdigest()
        return self._id_cache[filepath]
    def get_library_hash(self):
        import hashlib
        current_ids = [self.get_track_id(t.filepath) for t in self.main_window.library]
        current_ids.sort()
        return hashlib.md5("".join(current_ids).encode('utf-8')).hexdigest()
    def _setup_routes(self):
        @self.app.get("/")
        def read_root():
            return {"status": "Aiiko Music Server Running"}
        def _get_library_snapshot():
            while True:
                try:
                    return list(self.main_window.library)
                except RuntimeError:
                    import time
                    time.sleep(0.01)
        @self.app.get("/api/library")
        def get_library():
            try:
                tracks = []
                library_snapshot = _get_library_snapshot()
                for t in library_snapshot:
                    t_id = self.get_track_id(t.filepath)
                    tracks.append({
                        "id": t_id,
                        "title": t.title,
                        "artist": t.artist,
                        "album": t.album,
                        "duration_ms": t.duration,
                        "cover_url": f"/api/cover/{t_id}",
                        "filepath": t.filepath               
                    })
                return JSONResponse(content=tracks)
            except Exception as e:
                logger.error(f"Error fetching library: {e}")
                return JSONResponse(status_code=500, content={"error": str(e)})
        @self.app.get("/api/library/hash")
        def get_library_hash_api():
            try:
                return {"hash": self.get_library_hash()}
            except Exception as e:
                logger.error(f"Error computing library hash: {e}")
                return JSONResponse(status_code=500, content={"error": str(e)})
        @self.app.post("/api/library/sync")
        def sync_library(request: SyncRequest):
            try:
                client_ids = set(request.client_ids)
                library_snapshot = _get_library_snapshot()
                server_tracks = {self.get_track_id(t.filepath): t for t in library_snapshot}
                server_ids = set(server_tracks.keys())
                added_ids = server_ids - client_ids
                removed_ids = client_ids - server_ids
                added_tracks = []
                for t_id in added_ids:
                    t = server_tracks[t_id]
                    added_tracks.append({
                        "id": t_id,
                        "title": t.title,
                        "artist": t.artist,
                        "album": t.album,
                        "duration_ms": t.duration,
                        "cover_url": f"/api/cover/{t_id}",
                        "filepath": t.filepath
                    })
                return {
                    "hash": self.get_library_hash(),
                    "added": added_tracks,
                    "removed": list(removed_ids)
                }
            except Exception as e:
                logger.error(f"Error synchronizing library: {e}")
                return JSONResponse(status_code=500, content={"error": str(e)})
        @self.app.get("/api/search")
        def search_library(q: str = ""):
            try:
                query = q.lower().strip()
                if not query: return {"results": []}
                library_snapshot = _get_library_snapshot()
                results = []
                for t in library_snapshot:
                    if query in (t.title or "").lower() or query in (t.artist or "").lower() or query in (t.album or "").lower():
                        t_id = self.get_track_id(t.filepath)
                        results.append({
                            "id": t_id,
                            "title": t.title,
                            "artist": t.artist,
                            "album": t.album,
                            "duration_ms": t.duration,
                            "cover_url": f"/api/cover/{t_id}"
                        })
                        if len(results) >= 50:                  
                            break
                return {"results": results}
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": str(e)})
        @self.app.get("/api/lyrics/{track_id}")
        def get_lyrics(track_id: str):
            try:
                logger.info(f"[RemoteServer] API GET /api/lyrics/{track_id} requested.")
                library_snapshot = _get_library_snapshot()
                target_track = next((t for t in library_snapshot if self.get_track_id(t.filepath) == track_id), None)
                if not target_track:
                    return JSONResponse(status_code=404, content={"error": "Track not found"})
                from config import LYRICS_CACHE_DIR
                import hashlib
                unique_string = f"{target_track.filepath}_{getattr(target_track, 'mtime', 0)}"
                track_hash = hashlib.md5(unique_string.encode('utf-8')).hexdigest()
                cache_file = os.path.join(LYRICS_CACHE_DIR, f"{track_hash}.json")
                if os.path.exists(cache_file):
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return data
                return JSONResponse(status_code=404, content={"error": "Lyrics not found"})
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": str(e)})
        @self.app.get("/api/favorites")
        def get_favorites():
            try:
                from settings_manager import settings
                fav_paths = settings.get('favorites', [])
                fav_ids = []
                for p in fav_paths:
                    try:
                        fav_ids.append(self.get_track_id(p))
                    except Exception:
                        pass
                return {"favorites": fav_ids}
            except Exception as e:
                logger.error(f"Error fetching favorites: {e}")
                return JSONResponse(status_code=500, content={"error": str(e)})
        @self.app.get("/api/queue")
        def get_queue():
            if not hasattr(self.main_window, 'queue'): return {"queue": [], "active_index": -1}
            queue_list = []
            queue_snapshot = []
            while True:
                try:
                    queue_snapshot = list(self.main_window.queue.tracks)
                    break
                except RuntimeError:
                    import time
                    time.sleep(0.01)
            for t in queue_snapshot:
                t_id = self.get_track_id(t.filepath)
                queue_list.append({
                        "id": t_id,
                        "title": t.title,
                        "artist": t.artist,
                        "album": t.album,
                        "duration_ms": t.duration,
                        "cover_url": f"/api/cover/{t_id}"
                })
            return {"queue": queue_list, "active_index": self.main_window.queue.current_index}
        @self.app.get("/api/cover/{track_id}")
        def get_cover(track_id: str, size: int = None):
            from config import CACHE_DIR
            if size and size in [65, 160, 220, 450]:
                thumb_path = os.path.join(CACHE_DIR, "thumbnails", f"{track_id}_{size}.jpg")
                if os.path.exists(thumb_path):
                    return FileResponse(thumb_path)
            for t in self.main_window.library:
                if self.get_track_id(t.filepath) == track_id:
                    if t.cover_path and os.path.exists(t.cover_path):
                        return FileResponse(t.cover_path)
                    break
            return JSONResponse(status_code=404, content={"error": "Cover not found"})
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.manager.connect(websocket)
            initial_state = self.get_playback_state()
            await websocket.send_text(json.dumps({"event": "state_sync", "data": initial_state}))
            try:
                while True:
                    data = await websocket.receive_text()
                    try:
                        cmd = json.loads(data)
                        logger.info(f"[RemoteServer] Recibido WS: {data}")
                        self.handle_command(cmd)
                    except json.JSONDecodeError:
                        logger.warning(f"[RemoteServer] JSON inválido recibido: {data}")
            except WebSocketDisconnect:
                self.manager.disconnect(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.manager.disconnect(websocket)
    def handle_command(self, cmd):
        command = cmd.get("command")
        if not command: return
        self.dispatcher.dispatch.emit(cmd)
    def _execute_on_main_thread(self, cmd):
        command = cmd.get("command")
        if not command: return
        if command == "play_pause":
            self.main_window.playback_controller.toggle_play()
        elif command == "next":
            self.main_window.playback_controller.next_track(manual=True)
        elif command == "previous":
            self.main_window.playback_controller.prev_track(manual=True)
        elif command == "set_volume":
            val = cmd.get("value", 100)
            self.main_window.playback_controller.volume = val
            self.main_window.player_controller.set_volume(val)
            self.broadcast_state()
        elif command == "seek":
            time_ms = cmd.get("time_ms", 0)
            self.main_window.audio_engine.set_position(time_ms)
        elif command == "play_track":
            track_id = cmd.get("track_id")
            if track_id:
                found_track = None
                for t in self.main_window.library:
                    if self.get_track_id(t.filepath) == track_id:
                        found_track = t
                        break
                if found_track:
                    queue_mgr = self.main_window.queue
                    if found_track in queue_mgr.tracks:
                        try:
                            idx = queue_mgr.tracks.index(found_track)
                            self.main_window.queue_controller.play_from_queue_ui(idx)
                        except ValueError:
                            self.main_window.queue_controller.play_specific_track_global(found_track, queue_mgr.tracks)
                    else:
                        self.main_window.queue_controller.play_specific_track_global(found_track, self.main_window.library)
        elif command == "toggle_favorite":
            track_id = cmd.get("track_id")
            if not track_id and self.main_window.queue.get_current():
                track_id = self.get_track_id(self.main_window.queue.get_current().filepath)
            if track_id:
                found_track = None
                for t in self.main_window.library:
                    if self.get_track_id(t.filepath) == track_id:
                        found_track = t
                        break
                if found_track:
                    if hasattr(self.main_window, 'app_controller'):
                        self.main_window.app_controller.toggle_favorite_track(found_track)
                    self.broadcast_state()
                    self.broadcast_favorites()
        elif command == "shuffle":
            state = cmd.get("state", None)
            if state is not None:
                self.main_window.queue.shuffle(state)
                self.main_window.playback_ui_controller._update_shuffle_icon()
                self.main_window.queue_controller.update_gapless_preload()
            else:
                self.main_window.queue_controller.toggle_shuffle()
            self.broadcast_state()
            self.broadcast_queue()
        elif command == "repeat":
            mode = cmd.get("mode", cmd.get("value", None))                          
            if mode is not None:
                self.main_window.queue.set_repeat_mode(mode)
                self.main_window.playback_ui_controller._update_repeat_icon()
                self.main_window.queue_controller.update_gapless_preload()
            else:
                self.main_window.queue_controller.toggle_repeat()
            self.broadcast_state()
        elif command == "clear_queue":
            self.main_window.queue_controller.clear_queue()
        elif command == "add_next":
            track_id = cmd.get("track_id")
            if track_id:
                t = next((t for t in self.main_window.library if self.get_track_id(t.filepath) == track_id), None)
                if t:
                    self.main_window.queue_controller.add_to_queue_next(t)
                    self.broadcast_queue()
        elif command == "add_to_queue":
            track_id = cmd.get("track_id")
            if track_id:
                t = next((t for t in self.main_window.library if self.get_track_id(t.filepath) == track_id), None)
                if t:
                    self.main_window.queue_controller.add_to_queue(t)
                    self.broadcast_queue()
        else:
            logger.warning(f"[RemoteServer] Comando desconocido o sin acción: '{command}'")
    def get_playback_state(self, force_playing_state=None):
        if not hasattr(self.main_window, 'playback_controller'): return {}
        if force_playing_state is not None:
            is_playing = force_playing_state
        else:
            is_playing = self.main_window.audio_engine.is_playing() if hasattr(self.main_window, 'audio_engine') else False
        vol = self.main_window.playback_controller.volume if hasattr(self.main_window.playback_controller, 'volume') else 100
        time_ms = self.main_window.audio_engine.get_position() if hasattr(self.main_window, 'audio_engine') else 0
        track = None
        is_fav = False
        if hasattr(self.main_window, 'queue') and self.main_window.queue.get_current():
            t = self.main_window.queue.get_current()
            t_id = self.get_track_id(t.filepath)
            from settings_manager import settings
            is_fav = t.filepath in settings.get('favorites', [])
            track = {
                "id": t_id,
                "title": t.title,
                "artist": t.artist,
                "album": t.album,
                "duration_ms": t.duration,
                "cover_url": f"/api/cover/{t_id}",
                "is_favorite": is_fav
            }
        return {
            "is_playing": is_playing,
            "volume": vol,
            "current_time_ms": time_ms,
            "current_track": track,
            "active_queue_index": self.main_window.queue.current_index if hasattr(self.main_window, 'queue') else -1,
            "shuffle_enabled": self.main_window.queue.is_shuffled if hasattr(self.main_window, 'queue') else False,
            "repeat_mode": self.main_window.queue.repeat_mode if hasattr(self.main_window, 'queue') else 0
        }
    def broadcast_state(self, force_playing_state=None):
        if not isinstance(force_playing_state, bool):
            force_playing_state = None
        if self.loop and self.loop.is_running():
            state = self.get_playback_state(force_playing_state)
            msg = json.dumps({"event": "state_sync", "data": state})
            logger.info(f"[RemoteServer] Broadcasting state_sync: is_playing={state.get('is_playing')}")
            asyncio.run_coroutine_threadsafe(self.manager.broadcast(msg), self.loop)
    def broadcast_queue(self):
        if self.loop and self.loop.is_running():
            if not hasattr(self.main_window, 'queue'): return
            queue_list = []
            for t in self.main_window.queue.tracks:
                t_id = self.get_track_id(t.filepath)
                queue_list.append({
                        "id": t_id,
                        "title": t.title,
                        "artist": t.artist,
                        "album": t.album,
                        "duration_ms": t.duration,
                        "cover_url": f"/api/cover/{t_id}"
                })
            payload = {"queue": queue_list, "active_index": self.main_window.queue.current_index}
            msg = json.dumps({"event": "queue_sync", "data": payload})
            asyncio.run_coroutine_threadsafe(self.manager.broadcast(msg), self.loop)
    def broadcast_favorites(self):
        if self.loop and self.loop.is_running():
            from settings_manager import settings
            fav_paths = settings.get('favorites', [])
            fav_ids = []
            for p in fav_paths:
                try:
                    fav_ids.append(self.get_track_id(p))
                except Exception:
                    pass
            msg = json.dumps({"event": "favorites_sync", "data": {"favorites": fav_ids}})
            asyncio.run_coroutine_threadsafe(self.manager.broadcast(msg), self.loop)
    def broadcast_time(self, time_ms, track_id=None):
        if self.loop and self.loop.is_running():
            payload = {"event": "time_update", "current_time_ms": time_ms}
            if track_id:
                payload["track_id"] = track_id
            msg = json.dumps(payload)
            asyncio.run_coroutine_threadsafe(self.manager.broadcast(msg), self.loop)
    def _run_server(self):
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            config = uvicorn.Config(
                app=self.app, 
                host="0.0.0.0", 
                port=self.port, 
                log_level="error", 
                loop="asyncio",
                ws="websockets",
                http="h11",
                log_config=None
            )
            self._uvicorn_server = uvicorn.Server(config)
            logger.info(f"Iniciando Aiiko Remote Server en el puerto {self.port}")
            self.loop.run_until_complete(self._uvicorn_server.serve())
        except Exception as e:
            logger.error(f"FATAL ERROR en _run_server: {e}", exc_info=True)
        finally:
            if self.loop:
                try:
                    for task in asyncio.all_tasks(self.loop):
                        task.cancel()
                    self.loop.close()
                    logger.info("[RemoteServer] Asyncio loop cerrado correctamente.")
                except Exception as e:
                    logger.error(f"Error cerrando asyncio loop: {e}")
    def _register_zeroconf(self):
        try:
            ip = self.get_local_ip()
            desc = {'version': '1.0', 'app': 'Aiiko Music', 'name': self.server_name}
            self._service_info = ServiceInfo(
                "_aiiko._tcp.local.",
                f"{self.server_name.replace(' ', '_')}_{socket.gethostname()}._aiiko._tcp.local.",
                addresses=[socket.inet_aton(ip)],
                port=self.port,
                properties=desc,
                server=f"{socket.gethostname()}.local."
            )
            self.zeroconf = Zeroconf()
            self.zeroconf.register_service(self._service_info)
            logger.info(f"Servicio ZeroConf registrado: {ip}:{self.port}")
            self._rebroadcast_thread = threading.Thread(target=self._rebroadcast_loop, daemon=True)
            self._rebroadcast_thread.start()
        except Exception as e:
            logger.error(f"Error registrando ZeroConf: {e}")
    def _rebroadcast_loop(self):
        import time
        while self._uvicorn_server is None:
            time.sleep(1)
        while not getattr(self._uvicorn_server, 'should_exit', False):
            time.sleep(8)
            if len(self.manager.active_connections) == 0:
                if self.zeroconf and hasattr(self, '_service_info'):
                    try:
                        self._service_info.properties[b'ts'] = str(time.time()).encode('utf-8')
                        self.zeroconf.update_service(self._service_info)
                    except Exception as e:
                        pass
    def _run_server_and_zeroconf(self):
        self._register_zeroconf()
        self._run_server()
    def start(self):
        self.server_thread = threading.Thread(target=self._run_server_and_zeroconf, daemon=True)
        self.server_thread.start()
    def stop(self):
        def _do_stop():
            if self.zeroconf:
                try:
                    self.zeroconf.close()
                except: pass
            if self._uvicorn_server:
                self._uvicorn_server.should_exit = True
            logger.info("Aiiko Remote Server detenido de forma asíncrona.")
        threading.Thread(target=_do_stop, daemon=True).start()
