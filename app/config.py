import os
from qfluentwidgets import FluentIcon as FIF
import sys
import os
if getattr(sys, 'frozen', False):
    INSTALL_ROOT = os.path.dirname(sys.executable)
    APP_ROOT = sys._MEIPASS
else:
    INSTALL_ROOT = os.path.dirname(os.path.abspath(__file__))
    APP_ROOT = INSTALL_ROOT
APP_NAME = "Aiiko Music"
APP_VERSION = "1.0.1"
APP_AUTHOR = "Aiiko Hirayama"
DISCORD_CLIENT_ID = "YOUR_DISCORD_CLIENT_ID"                               
LASTFM_API_KEY = "YOUR_LASTFM_API_KEY"
LASTFM_API_SECRET = "YOUR_LASTFM_API_SECRET"
USER_DATA_DIR = INSTALL_ROOT
if sys.platform == 'win32' and not os.path.exists(os.path.join(INSTALL_ROOT, "portable.txt")):
    try:
        test_file = os.path.join(INSTALL_ROOT, ".write_test")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
    except PermissionError:
        USER_DATA_DIR = os.path.join(os.environ.get('APPDATA', INSTALL_ROOT), "Aiiko Music")
if sys.platform == 'win32':
    CACHE_DIR = os.path.join(os.environ.get('APPDATA', INSTALL_ROOT), "Aiiko Music", "cache")
else:
    CACHE_DIR = os.path.join(USER_DATA_DIR, "cache")
LOGS_DIR = os.path.join(USER_DATA_DIR, "logs")
THEMES_DIR = os.path.join(USER_DATA_DIR, "themes")
SETTINGS_FILE = os.path.join(USER_DATA_DIR, "aiiko_settings.json")
LIBRARY_FILE = os.path.join(USER_DATA_DIR, "aiiko_library.json")
RESOURCES_DIR = os.path.join(APP_ROOT, "resources")
ICON_FILE = os.path.join(APP_ROOT, "icon.png")
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(os.path.join(CACHE_DIR, "thumbnails"), exist_ok=True)
LYRICS_CACHE_DIR = os.path.join(CACHE_DIR, "lyrics")
os.makedirs(LYRICS_CACHE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(THEMES_DIR, exist_ok=True)
import logging
from logging.handlers import RotatingFileHandler
log_file = os.path.join(LOGS_DIR, "aiiko_music.log")
log_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
if root_logger.hasHandlers():
    root_logger.handlers.clear()
import queue
from logging.handlers import QueueHandler, QueueListener
import atexit
log_queue = queue.Queue(-1)                
queue_handler = QueueHandler(log_queue)
root_logger.addHandler(queue_handler)
queue_listener = QueueListener(log_queue, file_handler, console_handler, respect_handler_level=True)
queue_listener.start()
atexit.register(queue_listener.stop)
import platform
try:
    import psutil
    ram_gb = f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"
except ImportError:
    ram_gb = "Desconocido (psutil no instalado)"
try:
    root_logger.info("==================================================")
    root_logger.info("--- AIIKO MUSIC LOGS ---")
    root_logger.info(f"OS: {platform.system()} {platform.release()} ({platform.version()}) - {platform.architecture()[0]}")
    root_logger.info(f"CPU: {platform.processor()}")
    root_logger.info(f"RAM Total: {ram_gb}")
    root_logger.info(f"Python: {platform.python_version()}")
    root_logger.info("==================================================")
except Exception:
    pass
def get_safe_icon(primary_name, fallback_name):
    if hasattr(FIF, primary_name): return getattr(FIF, primary_name)
    if hasattr(FIF, fallback_name): return getattr(FIF, fallback_name)
    return FIF.DOCUMENT 
ICON_PREV = get_safe_icon('PREVIOUS', 'LEFT_ARROW')
ICON_NEXT = get_safe_icon('NEXT', 'RIGHT_ARROW')
ICON_PLAY = get_safe_icon('PLAY_SOLID', 'PLAY')
ICON_PAUSE = get_safe_icon('PAUSE_BOLD', 'PAUSE')
ICON_SHUFFLE = get_safe_icon('RANDOM', 'SYNC')
ICON_REPEAT = get_safe_icon('REPEAT', 'UPDATE')
ICON_TIMER = get_safe_icon('HISTORY', 'CLOCK')
ICON_VOLUME = get_safe_icon('VOLUME', 'MICROPHONE')
ICON_MUTE = get_safe_icon('MUTE', 'CLOSE')
ICON_ALBUM = get_safe_icon('ALBUM', 'CD')
ICON_LIST = get_safe_icon('MENU', 'ALIGNMENT')
ICON_GRID = get_safe_icon('TILES', 'GRID')
ICON_HEART = get_safe_icon('HEART', 'FAVORITES')
ICON_ADD = get_safe_icon('ADD', 'PLUS')
ICON_DELETE = get_safe_icon('DELETE', 'REMOVE')
def get_custom_styles(accent_hex):
    hex_color = accent_hex.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"""
    QListWidget, QListView {{
        background-color: transparent;
        border: none;
        outline: none;
    }}
    QListWidget#LyricsList::item {{
        padding: 8px 0px;
    }}
    QListWidget#GridList::item, QListView#SongsList::item, QListWidget#SongsList::item, QListWidget#PlaylistsList::item {{
        background-color: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        margin: 5px;
        padding: 8px;
    }}
    QListWidget#GridList::item:hover, QListView#SongsList::item:hover, QListWidget#SongsList::item:hover, QListWidget#PlaylistsList::item:hover {{
        background-color: rgba({r}, {g}, {b}, 0.08);
    }}
    QListWidget#GridList::item:selected, QListView#SongsList::item:selected, QListWidget#SongsList::item:selected, QListWidget#PlaylistsList::item:selected {{
        background-color: transparent; 
        border: none;
    }}
    QListWidget#ArtistGridList::item {{
        background-color: transparent;
        border-radius: 12px;
        margin: 5px;
        padding: 8px;
    }}
    QListWidget#ArtistGridList::item:hover {{
        background-color: rgba({r}, {g}, {b}, 0.05);
    }}
    QListWidget#ArtistGridList::item:selected {{
        background-color: rgba({r}, {g}, {b}, 0.1); 
        border: 1px solid transparent;
    }}
    QListWidget#QueueList::item {{
        background-color: transparent;
        border-radius: 6px;
        margin: 2px 5px;
        padding: 4px;
    }}
    QListWidget#QueueList::item:hover {{
        background-color: rgba({r}, {g}, {b}, 0.08);
    }}
    QListWidget#QueueList::item:selected {{
        background-color: rgba({r}, {g}, {b}, 0.15); 
        border: 1px solid transparent;
    }}
    """
