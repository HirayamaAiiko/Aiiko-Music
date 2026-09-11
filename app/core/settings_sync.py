import logging
from PyQt6.QtCore import QObject
from settings_manager import settings
class SettingsSyncManager(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
    def apply_settings_to_ui(self):
        mw = self.main_window
        if hasattr(mw, 'list_folders'):
            mw.list_folders.clear()
            for folder in settings.get('folders', []): 
                mw.list_folders.addItem(folder)
        if hasattr(mw, 'library_controller'):
            mw.library_controller.refresh_playlists_list()
        if hasattr(mw, 'switch_auto_scan'):
            mw.switch_auto_scan.blockSignals(True)
            mw.switch_auto_scan.setChecked(settings.get('auto_scan', False))
            mw.switch_auto_scan.blockSignals(False)
        if hasattr(mw, 'switch_dynamic_bg'):
            mw.switch_dynamic_bg.blockSignals(True)
            mw.switch_dynamic_bg.setChecked(settings.get('dynamic_bg', False))
            mw.switch_dynamic_bg.blockSignals(False)
        if hasattr(mw, 'switch_rpc'):
            mw.switch_rpc.blockSignals(True)
            mw.switch_rpc.setChecked(settings.get('rpc', False))
            mw.switch_rpc.blockSignals(False)
        enable_logs_val = settings.get('enable_logs', True)
        if hasattr(mw, 'switch_enable_logs'):
            mw.switch_enable_logs.blockSignals(True)
            mw.switch_enable_logs.setChecked(enable_logs_val)
            mw.switch_enable_logs.blockSignals(False)
        if not enable_logs_val:
            logging.disable(logging.CRITICAL)
        if hasattr(mw, 'switch_gapless') and hasattr(mw, 'switch_crossfade'):
            gapless_on = settings.get('gapless_enabled', True)
            crossfade_on = settings.get('crossfade_enabled', False)
            if gapless_on and crossfade_on:
                crossfade_on = False
                settings.set('crossfade_enabled', False)
                settings.save()
            mw.switch_gapless.blockSignals(True)
            mw.switch_crossfade.blockSignals(True)
            mw.switch_gapless.setChecked(gapless_on)
            mw.switch_crossfade.setChecked(crossfade_on)
            mw.switch_gapless.setEnabled(not crossfade_on)
            mw.switch_crossfade.setEnabled(not gapless_on)
            if hasattr(mw, 'crossfade_slider'):
                mw.crossfade_slider.setEnabled(crossfade_on and not gapless_on)
            mw.switch_gapless.blockSignals(False)
            mw.switch_crossfade.blockSignals(False)
        saved_vol = settings.get('volume', 80)
        if hasattr(mw, 'mini_volume_inline'): 
            mw.mini_volume_inline.setValue(saved_vol)
        mw.player_controller.set_volume(saved_vol)
    def _safe_get_scroll(self, mw, attr_name):
        try:
            if hasattr(mw, attr_name):
                widget = getattr(mw, attr_name)
                return widget.verticalScrollBar().value()
        except RuntimeError:
            pass
        return 0
    def sync_ui_to_settings(self):
        mw = self.main_window
        settings.set('volume', mw.mini_volume_inline.value() if hasattr(mw, 'mini_volume_inline') else 80)
        settings.set('last_queue_paths', [t.filepath for t in mw.queue.tracks] if hasattr(mw, 'queue') and mw.queue.tracks else [])
        settings.set('last_queue_index', getattr(mw.queue, 'current_index', -1) if hasattr(mw, 'queue') else -1)
        if hasattr(mw, 'audio_engine'):
            try:
                time_ms = mw.audio_engine.get_position()
                if time_ms > 0:
                    settings.set('last_playback_time', time_ms)
            except Exception as e:
                logging.error(f"Error al guardar posición de reproducción: {e}")
        settings.set('songs_is_grid', getattr(mw, 'songs_is_grid', False))
        settings.set('scroll_positions', {
            'songs': self._safe_get_scroll(mw, 'list_songs'),
            'albums': self._safe_get_scroll(mw, 'list_albums'),
            'artists': self._safe_get_scroll(mw, 'list_artists'),
        })
    def toggle_auto_scan(self, checked):
        settings.set('auto_scan', checked)
        settings.save()
    def toggle_logs(self, checked):
        settings.set('enable_logs', checked)
        settings.save()
        if checked:
            logging.disable(logging.NOTSET)
            logging.info("Registro de logs (Debug) activado.")
        else:
            logging.info("Registro de logs (Debug) desactivado.")
            logging.disable(logging.CRITICAL)
    def toggle_dynamic_bg(self, checked):
        settings.set('dynamic_bg', checked)
        settings.save()
        if self.main_window.queue.current_index >= 0 and self.main_window.queue.tracks:
            self.main_window.playback_ui_controller.update_now_playing_bg(self.main_window.queue.tracks[self.main_window.queue.current_index])
    def toggle_smooth_lyrics(self, checked):
        settings.set('smooth_lyrics', checked)
        settings.save()
    def toggle_crossfade(self, checked):
        settings.set('crossfade_enabled', checked)
        settings.save()
        if checked:
            self.main_window.audio_engine.set_crossfade(settings.get('crossfade_seconds', 3))
        else:
            self.main_window.audio_engine.set_crossfade(0)
    def on_crossfade_seconds_changed(self, value):
        settings.set('crossfade_seconds', value)
        settings.save()
        self.main_window.crossfade_label.setText(f"{value}s")
        if settings.get('crossfade_enabled', False):
            self.main_window.audio_engine.set_crossfade(value)
    def change_translation_lang(self, text):
        settings.set('translation_lang', text)
        settings.save()
        if hasattr(self.main_window, 'lyrics_manager') and self.main_window.lyrics_manager:
            self.main_window.lyrics_manager.set_target_lang(text)