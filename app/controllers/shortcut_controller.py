from PyQt6.QtCore import QObject
from PyQt6.QtGui import QShortcut, QKeySequence
from settings_manager import settings
from core.language_manager import tr
class ShortcutController(QObject):
    DEFAULT_SHORTCUTS = {
        "play_pause": {"default": "Space", "name": tr("Reproducir / Pausar")},
        "next_track": {"default": "Ctrl+Right", "name": tr("Siguiente Canción")},
        "prev_track": {"default": "Ctrl+Left", "name": tr("Canción Anterior")},
        "vol_up": {"default": "Ctrl+Up", "name": tr("Subir Volumen")},
        "vol_down": {"default": "Ctrl+Down", "name": tr("Bajar Volumen")},
        "mute": {"default": "Ctrl+M", "name": tr("Silenciar / Desilenciar")},
        "shuffle": {"default": "Ctrl+S", "name": tr("Modo Aleatorio")},
        "repeat": {"default": "Ctrl+R", "name": tr("Modo Repetir")},
        "queue": {"default": "Ctrl+L", "name": tr("Cola de Reproducción")},
        "spotlight": {"default": "Ctrl+F", "name": tr("Búsqueda Global (Spotlight)")},
        "search": {"default": "Ctrl+Shift+F", "name": tr("Buscar en la vista actual")},
        "fullscreen": {"default": "F11", "name": tr("Pantalla Completa")},
        "fs_lyrics": {"default": "L", "name": tr("Mostrar/Ocultar Letras (Pantalla Completa)")},
        "fs_translation": {"default": "T", "name": tr("Alternar Traducción (Pantalla Completa)")},
        "fs_visualizer": {"default": "P", "name": tr("Alternar Visualizador (Pantalla Completa)")},
        "fs_cover": {"default": "C", "name": tr("Mostrar/Ocultar Carátula (Pantalla Completa)")},
        "esc": {"default": "Esc", "name": tr("Cerrar / Salir")},
        "help": {"default": "F1", "name": tr("Ayuda de Atajos")}
    }
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.shortcuts = {}
        self._setup_shortcuts()
    def _setup_shortcuts(self):
        custom_shortcuts = settings.get('custom_shortcuts', {})
        from UI.dialogs.shortcuts_dialog import show_shortcuts_help
        self.actions = {
            "play_pause": self.main_window.playback_controller.toggle_play,
            "next_track": lambda: self.main_window.playback_controller.next_track(manual=True),
            "prev_track": lambda: self.main_window.playback_controller.prev_track(manual=True),
            "vol_up": lambda: self.main_window.player_controller.set_volume(min(100, settings.get('volume', 80) + 5)),
            "vol_down": lambda: self.main_window.player_controller.set_volume(max(0, settings.get('volume', 80) - 5)),
            "mute": self.main_window.player_controller.toggle_mute,
            "shuffle": self.main_window.queue_controller.toggle_shuffle,
            "repeat": self.main_window.queue_controller.toggle_repeat,
            "queue": self.main_window.queue_controller.toggle_queue_panel,
            "spotlight": self.main_window.search_controller.show_spotlight_search,
            "search": self._focus_in_page_search,
            "fullscreen": self.main_window.navigation_controller.toggle_fullscreen,
            "esc": self.main_window.navigation_controller.handle_esc_key,
            "help": lambda: show_shortcuts_help(self.main_window)
        }
        for action_id, data in self.DEFAULT_SHORTCUTS.items():
            key = custom_shortcuts.get(action_id, data["default"])
            if action_id in ["fs_lyrics", "fs_translation", "fs_visualizer", "fs_cover"]:
                continue
            shortcut = QShortcut(QKeySequence(key), self.main_window)
            if action_id in self.actions:
                shortcut.activated.connect(self.actions[action_id])
            self.shortcuts[action_id] = shortcut
    def update_shortcut(self, action_id, new_key):
        if hasattr(self.main_window, 'fullscreen_view') and self.main_window.fullscreen_view:
            if action_id in ["fs_lyrics", "fs_translation", "fs_visualizer", "fs_cover", "esc", "play_pause", "next_track", "prev_track", "vol_up", "vol_down"]:
                self.main_window.fullscreen_view.update_shortcut(action_id, new_key)
        if action_id in ["fs_lyrics", "fs_translation", "fs_visualizer", "fs_cover"]:
            return
        if action_id in self.shortcuts:
            self.shortcuts[action_id].setEnabled(False)
            self.shortcuts[action_id].setParent(None)
            self.shortcuts[action_id].deleteLater()
            shortcut = QShortcut(QKeySequence(new_key), self.main_window)
            shortcut.activated.connect(self.actions[action_id])
            self.shortcuts[action_id] = shortcut
            custom_shortcuts = settings.get('custom_shortcuts', {})
            custom_shortcuts[action_id] = new_key
            settings.set('custom_shortcuts', custom_shortcuts)
    def set_enabled(self, enabled: bool):
        for shortcut in self.shortcuts.values():
            shortcut.setEnabled(enabled)
    def restore_defaults(self):
        settings.set('custom_shortcuts', {})
        for action_id, data in self.DEFAULT_SHORTCUTS.items():
            self.update_shortcut(action_id, data["default"])
    def _focus_in_page_search(self):
        idx = self.main_window.stacked_widget.currentIndex()
        if idx == 1 and hasattr(self.main_window, 'search_bar'):
            self.main_window.search_bar.setFocus()
            self.main_window.search_bar.selectAll()
        elif idx == 2 and hasattr(self.main_window, 'page_favorites') and hasattr(self.main_window.page_favorites, 'search_bar'):
            self.main_window.page_favorites.search_bar.setFocus()
            self.main_window.page_favorites.search_bar.selectAll()
        elif idx == 3 and hasattr(self.main_window, 'page_playlists'):
            if self.main_window.page_playlists.main_stack.currentIndex() == 0 and hasattr(self.main_window.page_playlists, 'grid_search'):
                self.main_window.page_playlists.grid_search.setFocus()
                self.main_window.page_playlists.grid_search.selectAll()