import time
from PyQt6.QtCore import QObject, QTimer
from config import ICON_TIMER
from settings_manager import settings
from core.language_manager import tr
class SleepTimerController(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self._end_time = 0
        self._songs_left = 0
        self._active_preset = None
        self._just_paused_by_timer = False
        self._polling_timer = QTimer(self)
        self._polling_timer.timeout.connect(self._check_time_timer)
        self._polling_timer.setInterval(100)        
    def set_time_timer(self, minutes):
        self._end_time = time.time() + (minutes * 60)
        self._songs_left = 0
        self._active_preset = f"time_{minutes}"
        self._just_paused_by_timer = False
        self.mw.btn_timer.setToolTip(f"Apaga en {minutes}m")
        self._update_timer_button(active=True)
        self._polling_timer.start()
    def set_song_timer(self, count):
        self._songs_left = count
        self._end_time = 0
        self._active_preset = f"song_{count}"
        self._just_paused_by_timer = False
        self.mw.btn_timer.setToolTip(f"Apaga en {count} Canción(es)")
        self._update_timer_button(active=True)
        self._polling_timer.stop()                              
    def clear_timer(self):
        self._end_time = 0
        self._songs_left = 0
        self._active_preset = None
        self._just_paused_by_timer = False
        self.mw.btn_timer.setToolTip(tr("Temporizador (Desactivado)"))
        self._update_timer_button(active=False)
        self._polling_timer.stop()
    def _update_timer_button(self, active):
        accent = self.mw.ACCENT_COLORS.get(settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954')
        color = accent if active else '#FFFFFF'
        if hasattr(self.mw, 'playback_ui_controller'):
            self.mw.playback_ui_controller.update_tool_btn_state(self.mw.btn_timer, "timer.svg", ICON_TIMER, color)
    def _check_time_timer(self):
        if self._end_time > 0 and time.time() >= self._end_time:
            self._trigger_pause()
    def _trigger_pause(self):
        self._just_paused_by_timer = True
        self.mw.audio_engine.pause()
        self.clear_timer()
        if hasattr(self.mw, 'system_tray_controller'):
            self.mw.system_tray_controller.update_discord_rpc()
        if getattr(self.mw, 'remote_server', None):
            self.mw.remote_server.broadcast_state()
    def evaluate_song_transition(self, was_natural_end=False):
        if self._songs_left > 0:
            if was_natural_end:
                self._songs_left -= 1
                if self._songs_left == 0:
                    self._trigger_pause()
                    return True
            else:
                pass
        return False
    def is_last_song(self):
        return self._songs_left == 1
    def is_active(self):
        return self._end_time > 0 or self._songs_left > 0
    def did_just_pause_playback(self):
        val = self._just_paused_by_timer
        self._just_paused_by_timer = False
        return val
    def get_active_preset(self):
        return self._active_preset