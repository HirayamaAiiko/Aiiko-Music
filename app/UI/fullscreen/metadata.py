from PyQt6.QtGui import QPixmap
from config import ICON_PLAY, ICON_PAUSE, ICON_SHUFFLE, ICON_REPEAT
from core.language_manager import tr
import theme_manager
from qfluentwidgets import FluentIcon as FIF
class FullScreenMetadataMixin:
    def update_metadata(self, track, pixmap, is_playing):
        self._current_track = track
        self.title.setText(track.title)
        self.artist.setText(f"{track.artist} — {track.album}")
        if pixmap and not pixmap.isNull():
            self.cover.setPixmap(pixmap)
        else:
            self.cover.setPixmap(QPixmap())
        self.update_play_state(is_playing)
        if hasattr(self, 'lyrics_manager') and self.lyrics_manager:
            self.lyrics_manager.load(track)
        self.update_dynamic_bg(pixmap)
    def update_play_state(self, is_playing):
        if is_playing:
            self.btn_play.setIcon(self.player.playback_ui_controller._get_icon("pause.svg", ICON_PAUSE))
        else:
            self.btn_play.setIcon(self.player.playback_ui_controller._get_icon("play.svg", ICON_PLAY))
    def update_progress(self, curr_ms, total_ms):
        if not self._is_slider_pressed and total_ms > 0:
            self.slider.setValue(int((curr_ms / total_ms) * 1000))
            formatted = self.player.playback_ui_controller.format_time(curr_ms)
            self.time_curr.setText(formatted)
            self.slider.setToolTip(formatted)
        self.time_tot.setText(self.player.playback_ui_controller.format_time(total_ms))
        if (hasattr(self.player, 'queue') and self.player.queue.tracks
                and 0 <= self.player.queue.current_index < len(self.player.queue.tracks)):
            track = self.player.queue.tracks[self.player.queue.current_index]
            if hasattr(self, 'lyrics_manager') and self.lyrics_manager:
                self.lyrics_manager.sync(curr_ms, track)
    def _sync_shuffle_icon(self):
        if not hasattr(self.player, 'queue'): return
        accent = theme_manager.get_current_accent_hex()
        color = accent if self.player.queue.is_shuffled else '#FFFFFF'
        self.btn_shuffle.setIcon(
            self.player.playback_ui_controller._get_icon("shuffle.svg", ICON_SHUFFLE, color))
    def _sync_repeat_icon(self):
        if not hasattr(self.player, 'queue'): return
        accent = theme_manager.get_current_accent_hex()
        mode = self.player.queue.repeat_mode
        if mode == 0:
            self.btn_repeat.setIcon(
                self.player.playback_ui_controller._get_icon("repeat_off.svg", ICON_REPEAT, '#FFFFFF'))
        elif mode == 1:
            self.btn_repeat.setIcon(
                self.player.playback_ui_controller._get_icon("repeat.svg", ICON_REPEAT, accent))
        else:
            self.btn_repeat.setIcon(
                self.player.playback_ui_controller._get_icon("repeat1.svg", ICON_REPEAT, '#FFB900'))
    def _toggle_lyrics(self):
        from settings_manager import settings
        self._lyrics_visible = not getattr(self, '_lyrics_visible', False)
        settings.set('fullscreen_lyrics_visible', self._lyrics_visible)
        self.lyrics_panel.setVisible(self._lyrics_visible)
        self._update_center_visibility()
        if self._lyrics_visible:
            self.btn_toggle_lyrics.setToolTip(tr("Ocultar Letras"))
            accent = theme_manager.get_current_accent_hex()
            self.btn_toggle_lyrics.setIcon(self.player.playback_ui_controller._get_icon("hide_lyrics.svg", FIF.ALIGNMENT, accent))
        else:
            self.btn_toggle_lyrics.setToolTip(tr("Mostrar Letras"))
            self.btn_toggle_lyrics.setIcon(self.player.playback_ui_controller._get_icon("hide_lyrics.svg", FIF.ALIGNMENT, '#FFFFFF'))
    def _toggle_lyrics_translation(self):
        if not hasattr(self, 'lyrics_manager') or not self.lyrics_manager: return
        if not hasattr(self.lyrics_manager, 'display_mode'):
            self.lyrics_manager.display_mode = 'original'
        accent = theme_manager.get_current_accent_hex()
        if self.lyrics_manager.display_mode == 'original':
            self.lyrics_manager.display_mode = 'dual'
            self.btn_translate_lyrics.setToolTip(tr("Traductor: Dual"))
            self.btn_translate_lyrics.setIcon(self.player.playback_ui_controller._get_icon("translate_lyrics.svg", FIF.LANGUAGE, accent))
        elif self.lyrics_manager.display_mode == 'dual':
            self.lyrics_manager.display_mode = 'translated'
            self.btn_translate_lyrics.setToolTip(tr("Traductor: Solo Traducción"))
            self.btn_translate_lyrics.setIcon(self.player.playback_ui_controller._get_icon("translate_lyrics.svg", FIF.LANGUAGE, '#FFB900'))
        else:
            self.lyrics_manager.display_mode = 'original'
            self.btn_translate_lyrics.setToolTip(tr("Traductor: Original"))
            self.btn_translate_lyrics.setIcon(self.player.playback_ui_controller._get_icon("translate_lyrics.svg", FIF.LANGUAGE, '#FFFFFF'))
        self.lyrics_manager.update_display()
    def _toggle_visualizer(self):
        if hasattr(self, 'visualizer') and self.visualizer is not None:
            self.visualizer.setVisible(not self.visualizer.isVisible())
        else:
            from core.notification_manager import notify
            notify.warning("Visualizador No Disponible", "El motor del visualizador no pudo cargarse o faltan dependencias (Numpy).")
    def _toggle_cover(self):
        self._cover_visible = not getattr(self, '_cover_visible', True)
        self.left_container.setVisible(self._cover_visible)
        self._update_center_visibility()
    def _update_center_visibility(self):
        cover_vis = getattr(self, '_cover_visible', True)
        lyrics_vis = getattr(self, '_lyrics_visible', False)
        both_hidden = not cover_vis and not lyrics_vis
        if hasattr(self, 'center_logo_label'):
            self.center_logo_label.setVisible(both_hidden)
        if both_hidden:
            if hasattr(self, 'bg_anim'):
                from PyQt6.QtGui import QColor
                self.bg_anim.stop()
                self.bg_anim.setStartValue(self._current_bg_color)
                self.bg_anim.setEndValue(QColor("#1E3440"))
                self.bg_anim.start()
        else:
            if hasattr(self.player, 'queue') and self.player.queue.current_index >= 0:
                if self.player.queue.current_index < len(self.player.queue.tracks):
                    self.update_dynamic_bg(self.cover._original_pixmap if hasattr(self, 'cover') else None)