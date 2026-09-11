import os
import json
import logging
import shutil
from config import APP_ROOT, INSTALL_ROOT
THEMES_DIR = os.path.join(INSTALL_ROOT, "themes")
os.makedirs(THEMES_DIR, exist_ok=True)
internal_themes = os.path.join(APP_ROOT, "themes")
if os.path.exists(internal_themes) and THEMES_DIR != internal_themes:
    if not os.listdir(THEMES_DIR):
        for item in os.listdir(internal_themes):
            s = os.path.join(internal_themes, item)
            d = os.path.join(THEMES_DIR, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)
_loaded_themes: dict = {}                                                    
BUILTIN_ACCENTS = {
    "Carmesí": "#E03131",
    "Naranja": "#FD7E14",
    "Ámbar": "#FAB005",
    "Esmeralda": "#2F9E44",
    "Turquesa": "#099268",
    "Cian (AIIKO)": "#14B8A6",
    "Azul": "#1C7ED6",
    "Índigo": "#4263EB",
    "Púrpura": "#7048E8",
    "Fucsia": "#D6336C",
    "Rosa": "#F06595"
}
def _ensure_loaded():
    if _loaded_themes:
        return
    reload()
def reload():
    global _loaded_themes
    _loaded_themes.clear()
    for filename in sorted(os.listdir(THEMES_DIR)):
        if not filename.endswith('.json'):
            continue
        filepath = os.path.join(THEMES_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logging.warning(f"No se pudo leer el tema '{filename}': {e}")
            continue
        kind = data.get('type')
        name = data.get('name')
        if not name:
            continue
        if kind == 'theme':
            _loaded_themes[name] = data
        else:
            logging.debug(f"Archivo de tema ignorado (type desconocido): {filename}")
    if not _loaded_themes:
        _loaded_themes['Oscuro (Dark)'] = _default_theme()
    logging.info(f"Temas cargados: {list(_loaded_themes.keys())}")
def get_theme_names() -> list[str]:
    _ensure_loaded()
    return list(_loaded_themes.keys())
def get_theme(name: str) -> dict:
    _ensure_loaded()
    return _loaded_themes.get(name, _default_theme())
def get_accent_names() -> list[str]:
    return list(BUILTIN_ACCENTS.keys()) + ["Color del Sistema"]
def get_system_accent_color() -> str:
    import platform
    if platform.system() == "Windows":
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\DWM")
            value, _ = winreg.QueryValueEx(key, "ColorizationColor")
            return f"#{value & 0xFFFFFF:06x}"
        except Exception:
            pass
    try:
        from qfluentwidgets import themeColor
        return themeColor().name()
    except Exception:
        return "#8B0BF8"
def get_accent_hex(name: str) -> str:
    if name == "Color del Sistema":
        return get_system_accent_color()
    if name == "Personalizado":
        try:
            from settings_manager import settings
            return settings.get('app_custom_accent_hex', '#8B0BF8')
        except Exception:
            return '#8B0BF8'
    return BUILTIN_ACCENTS.get(name, '#1DB954')
def get_current_accent_hex() -> str:
    try:
        from settings_manager import settings
        name = settings.get('app_accent_name', 'Cian (AIIKO)')
    except Exception:
        name = 'Cian (AIIKO)'
    return get_accent_hex(name)
def _default_theme() -> dict:
    return {
        "type": "theme",
        "name": "Oscuro (Dark)",
        "main_bg": "#202020",
        "mini_player_bg": "#161616",
        "mini_player_border": "#383838",
        "now_playing_bg": None,
        "page_content_bg": None,
        "queue_bg": "#161616",
        "queue_border": "#333",
        "sidebar_bg": None,
        "spotlight_bg": None,
        "spotlight_border": None
    }