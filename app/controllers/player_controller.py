import logging
from PyQt6.QtCore import QObject, Qt, QTimer
from PyQt6.QtGui import QColor
from settings_manager import settings
class PlayerController(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self._is_vol_animating = False
        self._volume_before_mute = 80
    def set_volume(self, value):
        if self._is_vol_animating: return
        self.mw.audio_engine.set_volume(value)
        if hasattr(self.mw, 'mini_volume_inline') and self.mw.mini_volume_inline.value() != value:
            self.mw.mini_volume_inline.setValue(value)
        try:
            if hasattr(self.mw, 'mini_volume_popup') and self.mw.mini_volume_popup.value() != value:
                self.mw.mini_volume_popup.setValue(value)
        except RuntimeError:
            pass
        if hasattr(self.mw, 'fullscreen_view') and hasattr(self.mw.fullscreen_view, 'vol_slider') and self.mw.fullscreen_view.vol_slider.value() != value:
            self.mw.fullscreen_view.vol_slider.setValue(value)
        if hasattr(self.mw, 'mini_volume_inline'): self.mw.mini_volume_inline.setToolTip(f"Volumen: {value}%")
        try:
            if hasattr(self.mw, 'mini_volume_popup'): self.mw.mini_volume_popup.setToolTip(f"Volumen: {value}%")
        except RuntimeError:
            pass
        settings.set('volume', value)
    def toggle_mute(self):
        if not hasattr(self, '_is_muted'):
            self._is_muted = False
        self._is_muted = not self._is_muted
        self.mw.audio_engine.set_mute(self._is_muted)
        from config import ICON_MUTE, ICON_VOLUME
        icon = self.mw.playback_ui_controller._get_icon("mute.svg", ICON_MUTE) if self._is_muted else self.mw.playback_ui_controller._get_icon("volume.svg", ICON_VOLUME)
        try:
            self.mw.vol_icon.setIcon(icon)
        except RuntimeError: pass
        try:
            if hasattr(self.mw, 'vol_popup_icon'):
                self.mw.vol_popup_icon.setIcon(icon)
        except RuntimeError: pass
        try:
            if hasattr(self.mw, 'fullscreen_view') and hasattr(self.mw.fullscreen_view, 'vol_icon'):
                self.mw.fullscreen_view.vol_icon.setIcon(icon)
        except RuntimeError: pass
        if self._is_muted:
            if not getattr(self, '_is_vol_animating', False):
                self._volume_before_mute = self.mw.mini_volume_inline.value()
            self._animate_volume_slider(0)
        else:
            target = getattr(self, '_volume_before_mute', 80)
            self._animate_volume_slider(target)
    def _animate_volume_slider(self, target_value):
        from PyQt6.QtCore import QParallelAnimationGroup, QPropertyAnimation, QEasingCurve
        if hasattr(self, '_vol_anim_group'):
            self._vol_anim_group.stop()
            self._vol_anim_group.deleteLater()
        self._vol_anim_group = QParallelAnimationGroup(self)
        self._anim_inline = QPropertyAnimation(self.mw.mini_volume_inline, b"value")
        self._anim_inline.setDuration(300)
        self._anim_inline.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_inline.setStartValue(self.mw.mini_volume_inline.value())
        self._anim_inline.setEndValue(target_value)
        self._vol_anim_group.addAnimation(self._anim_inline)
        try:
            if hasattr(self.mw, 'mini_volume_popup'):
                self._anim_popup = QPropertyAnimation(self.mw.mini_volume_popup, b"value")
                self._anim_popup.setDuration(300)
                self._anim_popup.setEasingCurve(QEasingCurve.Type.OutCubic)
                self._anim_popup.setStartValue(self.mw.mini_volume_popup.value())
                self._anim_popup.setEndValue(target_value)
                self._vol_anim_group.addAnimation(self._anim_popup)
        except RuntimeError:
            pass
        if hasattr(self.mw, 'fullscreen_view') and hasattr(self.mw.fullscreen_view, 'vol_slider'):
            self._anim_fs = QPropertyAnimation(self.mw.fullscreen_view.vol_slider, b"value")
            self._anim_fs.setDuration(300)
            self._anim_fs.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._anim_fs.setStartValue(self.mw.fullscreen_view.vol_slider.value())
            self._anim_fs.setEndValue(target_value)
            self._vol_anim_group.addAnimation(self._anim_fs)
        self._vol_anim_group.finished.connect(self._on_vol_anim_finished)
        self._is_vol_animating = True
        self._vol_anim_group.start()
    def _on_vol_anim_finished(self):
        self._is_vol_animating = False
    def update_audio_time(self, curr_ms, total_ms):
        mw = self.mw
        if hasattr(mw, '_expected_seek_time'):
            import time
            elapsed = time.time() - getattr(mw, '_seek_lock_timestamp', 0)
            if abs(curr_ms - mw._expected_seek_time) > 1000 and elapsed < 1.0:
                return                                                                 
            else:
                delattr(mw, '_expected_seek_time')
        mw.system_manager.update_floating_progress(curr_ms, total_ms)
        if hasattr(mw, 'fullscreen_view') and mw.fullscreen_view.isVisible():
            mw.fullscreen_view.update_progress(curr_ms, total_ms)
        if mw.isMinimized() or not mw.isVisible():
            return
        if not mw.is_slider_pressed and not mw.mini_slider.isSliderDown():
            val = int((curr_ms / total_ms) * 1000) if total_ms > 0 else 0
            if mw.mini_slider.value() != val:
                mw.mini_slider.setValue(val)
            tot_str = mw.playback_ui_controller.format_time(total_ms)
            curr_str = mw.playback_ui_controller.format_time(curr_ms)
            if mw.mini_time_tot.text() != tot_str:
                mw.mini_time_tot.setText(tot_str)
            if mw.mini_time_curr.text() != curr_str:
                mw.mini_time_curr.setText(curr_str)
            if mw.show_lyrics and mw.lyrics_manager and 0 <= mw.queue.current_index < len(mw.queue.tracks):
                track = mw.queue.tracks[mw.queue.current_index]
                mw.lyrics_manager.sync(curr_ms, track)
    def setup_slider_connections(self):
        self.mw.mini_slider.sliderPressed.connect(self._on_slider_pressed)
        self.mw.mini_slider.sliderReleased.connect(self._on_slider_released)
        self.mw.mini_slider.sliderMoved.connect(self._on_slider_moved)
    def _on_slider_pressed(self):
        self.mw.is_slider_pressed = True
    def _on_slider_released(self):
        val = self.mw.mini_slider.value()
        total_ms = self.mw.audio_engine.get_length()
        if total_ms > 0:
            target_ms = int((val / 1000) * total_ms)
            self.mw.audio_engine.set_position(target_ms)
            import time
            self.mw._expected_seek_time = target_ms
            self.mw._seek_lock_timestamp = time.time()
        self.mw.is_slider_pressed = False
    def _on_slider_moved(self, value):
        total_ms = self.mw.audio_engine.get_length()
        if total_ms > 0:
            preview_ms = int((value / 1000) * total_ms)
            self.mw.mini_time_curr.setText(self.mw.playback_ui_controller.format_time(preview_ms))
    def handle_slider_click(self, obj, event):
        return False