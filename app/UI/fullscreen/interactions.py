from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QParallelAnimationGroup, QAbstractAnimation, QEvent
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from settings_manager import settings
class FullScreenInteractionsMixin:
    def _init_interactions(self):
        self._setup_idle_timer()
        self._setup_shortcuts()
        self.installEventFilter(self)
    def _setup_idle_timer(self):
        self.header_opacity = QGraphicsOpacityEffect(self.header_widget)
        self.header_widget.setGraphicsEffect(self.header_opacity)
        self.bottom_opacity = QGraphicsOpacityEffect(self.bottom)
        self.bottom.setGraphicsEffect(self.bottom_opacity)
        self.anim_group = QParallelAnimationGroup(self)
        self.anim_header = QPropertyAnimation(self.header_opacity, b"opacity", self)
        self.anim_header.setDuration(300)
        self.anim_bottom = QPropertyAnimation(self.bottom_opacity, b"opacity", self)
        self.anim_bottom.setDuration(300)
        self.anim_group.addAnimation(self.anim_header)
        self.anim_group.addAnimation(self.anim_bottom)
        self.idle_timer = QTimer(self)
        self.idle_timer.setInterval(3000)
        self.idle_timer.timeout.connect(self._hide_controls)
        self.idle_timer.start()
    def _hide_controls(self):
        if self.header_opacity.opacity() == 0.0:
            return
        self.anim_group.stop()
        self.anim_header.setEndValue(0.0)
        self.anim_bottom.setEndValue(0.0)
        self.anim_group.start()
        self.setCursor(Qt.CursorShape.BlankCursor)
    def _show_controls(self):
        self.idle_timer.start()
        self.unsetCursor()
        if self.header_opacity.opacity() == 1.0:
            return
        if self.anim_group.state() == QAbstractAnimation.State.Running:
            if self.anim_header.endValue() == 1.0:
                return
        self.anim_group.stop()
        self.anim_header.setEndValue(1.0)
        self.anim_bottom.setEndValue(1.0)
        self.anim_group.start()
    def _setup_shortcuts(self):
        custom_shortcuts = settings.get('custom_shortcuts', {})
        key_esc = custom_shortcuts.get("esc", "Esc")
        key_space = custom_shortcuts.get("play_pause", "Space")
        key_l = custom_shortcuts.get("fs_lyrics", "L")
        key_t = custom_shortcuts.get("fs_translation", "T")
        key_p = custom_shortcuts.get("fs_visualizer", "P")
        key_c = custom_shortcuts.get("fs_cover", "C")
        self.sc_esc = QShortcut(QKeySequence(key_esc), self)
        self.sc_esc.activated.connect(self.player.navigation_controller.toggle_fullscreen)
        self.sc_space = QShortcut(QKeySequence(key_space), self)
        self.sc_space.activated.connect(self.player.playback_controller.toggle_play)
        self.sc_l = QShortcut(QKeySequence(key_l), self)
        self.sc_l.activated.connect(self._toggle_lyrics)
        self.sc_t = QShortcut(QKeySequence(key_t), self)
        self.sc_t.activated.connect(self._toggle_lyrics_translation)
        self.sc_p = QShortcut(QKeySequence(key_p), self)
        self.sc_p.activated.connect(self._toggle_visualizer)
        self.sc_c = QShortcut(QKeySequence(key_c), self)
        self.sc_c.activated.connect(self._toggle_cover)
        key_next = custom_shortcuts.get("next_track", "Ctrl+Right")
        key_prev = custom_shortcuts.get("prev_track", "Ctrl+Left")
        key_volup = custom_shortcuts.get("vol_up", "Ctrl+Up")
        key_voldown = custom_shortcuts.get("vol_down", "Ctrl+Down")
        self.sc_next = QShortcut(QKeySequence(key_next), self)
        self.sc_next.activated.connect(lambda: self.player.playback_controller.next_track(manual=True))
        self.sc_prev = QShortcut(QKeySequence(key_prev), self)
        self.sc_prev.activated.connect(lambda: self.player.playback_controller.prev_track(manual=True))
        self.sc_volup = QShortcut(QKeySequence(key_volup), self)
        self.sc_volup.activated.connect(lambda: self.player.player_controller.set_volume(min(100, settings.get('volume', 80) + 5)))
        self.sc_voldown = QShortcut(QKeySequence(key_voldown), self)
        self.sc_voldown.activated.connect(lambda: self.player.player_controller.set_volume(max(0, settings.get('volume', 80) - 5)))
        self.fs_shortcuts = {
            "esc": self.sc_esc,
            "play_pause": self.sc_space,
            "fs_lyrics": self.sc_l,
            "fs_translation": self.sc_t,
            "fs_visualizer": self.sc_p,
            "fs_cover": self.sc_c,
            "next_track": self.sc_next,
            "prev_track": self.sc_prev,
            "vol_up": self.sc_volup,
            "vol_down": self.sc_voldown
        }
    def update_shortcut(self, action_id, new_key):
        if action_id in self.fs_shortcuts:
            self.fs_shortcuts[action_id].setEnabled(False)
            self.fs_shortcuts[action_id].setParent(None)
            self.fs_shortcuts[action_id].deleteLater()
            shortcut = QShortcut(QKeySequence(new_key), self)
            if action_id == "fs_lyrics":
                shortcut.activated.connect(self._toggle_lyrics)
            elif action_id == "fs_translation":
                shortcut.activated.connect(self._toggle_lyrics_translation)
            elif action_id == "fs_visualizer":
                shortcut.activated.connect(self._toggle_visualizer)
            elif action_id == "fs_cover":
                shortcut.activated.connect(self._toggle_cover)
            elif action_id == "esc":
                shortcut.activated.connect(self.player.navigation_controller.toggle_fullscreen)
            elif action_id == "play_pause":
                shortcut.activated.connect(self.player.playback_controller.toggle_play)
            elif action_id == "next_track":
                shortcut.activated.connect(lambda: self.player.playback_controller.next_track(manual=True))
            elif action_id == "prev_track":
                shortcut.activated.connect(lambda: self.player.playback_controller.prev_track(manual=True))
            elif action_id == "vol_up":
                shortcut.activated.connect(lambda: self.player.player_controller.set_volume(min(100, settings.get('volume', 80) + 5)))
            elif action_id == "vol_down":
                shortcut.activated.connect(lambda: self.player.player_controller.set_volume(max(0, settings.get('volume', 80) - 5)))
            self.fs_shortcuts[action_id] = shortcut
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseMove:
            self._show_controls()
        return super().eventFilter(obj, event)
    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, '_sync_shuffle_icon'): self._sync_shuffle_icon()
        if hasattr(self, '_sync_repeat_icon'): self._sync_repeat_icon()
        if hasattr(self, 'idle_timer'): self.idle_timer.start()
        if hasattr(self, 'player') and hasattr(self.player, 'playback_ui_controller'):
            self.player.playback_ui_controller._update_fullscreen_icon()
    def hideEvent(self, event):
        super().hideEvent(event)
        if hasattr(self, 'idle_timer'): self.idle_timer.stop()
        if hasattr(self, 'player') and hasattr(self.player, 'playback_ui_controller'):
            self.player.playback_ui_controller._update_fullscreen_icon()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'visualizer') and self.visualizer:
            self.visualizer.setGeometry(self.rect())
    def _on_slider_pressed(self):
        self._is_slider_pressed = True
        self.player.is_slider_pressed = True
    def _on_slider_moved(self, value):
        length = self.player.audio_engine.get_length()
        if length > 0:
            ms = int((value / 1000) * length)
            formatted = self.player.playback_ui_controller.format_time(ms)
            self.time_curr.setText(formatted)
            self.slider.setToolTip(formatted)
    def _on_slider_released(self):
        self._is_slider_pressed = False
        self.player.is_slider_pressed = False
        length = self.player.audio_engine.get_length()
        if length > 0:
            ms = int((self.slider.value() / 1000) * length)
            self.player.audio_engine.set_position(ms)
            import time
            self.player._expected_seek_time = ms
            self.player._seek_lock_timestamp = time.time()