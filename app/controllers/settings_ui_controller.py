import logging
import ctypes
from core.notification_manager import notify
from settings_manager import settings
class SettingsUIController:
    def __init__(self, main_window):
        self.mw = main_window
    def init_audio_settings_ui(self):
        self.mw.combo_audio_output.blockSignals(True)
        self.mw.combo_audio_output.clear()
        self.mw.combo_audio_output.addItem("BASS Engine (DirectSound / Compartido)", userData="bass_default")
        self.mw.combo_audio_output.addItem("BASS WASAPI (Exclusivo - Baja Latencia)", userData="bass_wasapi")
        saved_output = settings.get('audio_output_mode', 'bass_default')
        if saved_output == 'bass_wasapi':
            self.mw.combo_audio_output.setCurrentIndex(1)
        else:
            self.mw.combo_audio_output.setCurrentIndex(0)
        self.mw.combo_audio_output.setEnabled(True)
        self.mw.combo_audio_output.blockSignals(False)
        if self.mw.audio_engine:
            if hasattr(self.mw.audio_engine, 'get_audio_devices'):
                devices = self.mw.audio_engine.get_audio_devices()
            else:
                devices = [{"id": "default", "name": "Sistema por defecto"}]
            self.mw.combo_audio_device.blockSignals(True)
            self.mw.combo_audio_device.clear()
            for dev in devices:
                self.mw.combo_audio_device.addItem(dev['name'], userData=dev['id'])
            saved_mode = settings.get('audio_output_mode', 'bass_default')
            if saved_mode == 'bass_wasapi':
                saved_device = settings.get('wasapi_device_id', "-1")
            else:
                saved_device = settings.get('audio_device_id', "default")
            for i in range(self.mw.combo_audio_device.count()):
                if self.mw.combo_audio_device.itemData(i) == str(saved_device) or self.mw.combo_audio_device.itemData(i) == saved_device:
                    self.mw.combo_audio_device.setCurrentIndex(i)
                    break
            self.mw.combo_audio_device.blockSignals(False)
    def change_audio_output(self, text):
        idx = self.mw.combo_audio_output.currentIndex()
        if idx >= 0:
            mode = self.mw.combo_audio_output.itemData(idx)
            settings.set('audio_output_mode', mode)
            settings.save()
            from qfluentwidgets import MessageBox
            from core.language_manager import tr
            msg = MessageBox(
                tr("Reinicio Requerido"),
                tr("Has cambiado el motor de salida de audio.\n\nEl modo WASAPI Exclusivo requiere reiniciar la aplicación para reclamar el control de la tarjeta de sonido, lo que silenciará otras aplicaciones.\n\n¿Deseas reiniciar Aiiko Music ahora?"),
                self.mw
            )
            msg.yesButton.setText(tr("Reiniciar"))
            if msg.exec():
                import sys, subprocess, time
                time.sleep(0.1)
                if getattr(sys, 'frozen', False):
                    subprocess.Popen([sys.executable, '--restart'])
                else:
                    subprocess.Popen([sys.executable] + sys.argv + ['--restart'])
                self.mw.close()
    def change_audio_device(self, index):
        if index >= 0:
            dev_id = self.mw.combo_audio_device.itemData(index)
            mode = settings.get('audio_output_mode', 'bass_default')
            if mode == 'bass_wasapi':
                settings.set('wasapi_device_id', dev_id)
            else:
                settings.set('audio_device_id', dev_id)
            settings.save()
            if self.mw.audio_engine:
                if hasattr(self.mw.audio_engine, 'set_audio_device'):
                    self.mw.audio_engine.set_audio_device(dev_id)
    def apply_buffer_size(self):
        val = self.mw.input_buffer_size.text().strip()
        try:
            val_int = int(val)
            if val_int < 100: val_int = 100
            if val_int > 10000: val_int = 10000
            settings.set('audio_buffer_ms', val_int)
            settings.save()
            self.mw.input_buffer_size.setText(str(val_int))
            was_playing = False
            curr_pos = 0
            track = None
            if self.mw.audio_engine:
                was_playing = self.mw.audio_engine.is_playing()
                curr_pos = self.mw.audio_engine.get_position()
            if hasattr(self.mw, 'queue') and self.mw.queue.tracks and self.mw.queue.current_index >= 0:
                track = self.mw.queue.tracks[self.mw.queue.current_index]
            if self.mw.audio_engine and hasattr(self.mw.audio_engine, 'apply_buffer_config'):
                self.mw.audio_engine.apply_buffer_config(val_int)
                if track:
                    self.mw.audio_engine.play_file(track.filepath, start_time=curr_pos)
                    if not was_playing:
                        self.mw.audio_engine._bass.BASS_ChannelSetAttribute(
                            self.mw.audio_engine._stream, 2, ctypes.c_float(0.0)                   
                        )
                        if getattr(self.mw.audio_engine, '_mixer', 0):
                            self.mw.audio_engine._bassmix.BASS_Mixer_ChannelFlags(
                                self.mw.audio_engine._stream, 0x20000, 0x20000                    
                            )
                        else:
                            self.mw.audio_engine._bass.BASS_ChannelPause(self.mw.audio_engine._stream)
                        self.mw.audio_engine.state_changed.emit(False)
            notify.success(
                title="Búfer Actualizado",
                content=f"Caché de audio configurado a {val_int}ms y aplicado al motor BASS con soporte asíncrono."
            )
        except ValueError:
            notify.error(
                title="Valor Inválido",
                content="Por favor, ingresa un número válido (ej. 300, 800, 1500)."
            )
    def toggle_smooth_lyrics(self, checked):
        settings.set('smooth_lyrics', checked)
        settings.save()
        if hasattr(self.mw, 'lyrics_manager') and self.mw.lyrics_manager:
            self.mw.lyrics_manager.set_smooth_lyrics(checked)
    def toggle_crossfade(self, checked):
        settings.set('crossfade_enabled', checked)
        if hasattr(self.mw, 'crossfade_slider'):
            self.mw.crossfade_slider.setEnabled(checked)
        if checked:
            settings.set('gapless_enabled', False)
            self.mw.audio_engine.set_crossfade(settings.get('crossfade_seconds', 3))
            from core.notification_manager import notify
            from core.language_manager import tr
            notify.info(tr("Crossfade Activado"), tr("La reproducción Gapless (Sin pausas) se ha desactivado temporalmente para permitir el cruce de volumen."))
        else:
            settings.set('gapless_enabled', True)
            self.mw.audio_engine.set_crossfade(0)
        settings.save()
    def on_crossfade_seconds_changed(self, value):
        settings.set('crossfade_seconds', value)
        settings.save()
        self.mw.crossfade_label.setText(f"{value}s")
        if settings.get('crossfade_enabled', False):
            self.mw.audio_engine.set_crossfade(value)
    def change_translation_lang(self, text):
        settings.set('translation_lang', text)
        settings.save()
        if hasattr(self.mw, 'lyrics_manager') and self.mw.lyrics_manager:
            self.mw.lyrics_manager.set_target_lang(text)
    def apply_settings_from_manager(self):
        for folder in settings.get('folders', []):
            self.mw.list_folders.addItem(folder)
        self.mw.library_controller.refresh_playlists_list()
        self.mw.switch_auto_scan.blockSignals(True)
        self.mw.switch_dynamic_bg.blockSignals(True)
        self.mw.switch_rpc.blockSignals(True)
        if hasattr(self.mw, 'switch_minimize_tray'):
            self.mw.switch_minimize_tray.blockSignals(True)
            self.mw.switch_close_tray.blockSignals(True)
        if hasattr(self.mw, 'switch_enable_logs'):
            self.mw.switch_enable_logs.blockSignals(True)
        self.mw.switch_auto_scan.setChecked(settings.get('auto_scan', False))
        self.mw.switch_dynamic_bg.setChecked(settings.get('dynamic_bg', False))
        self.mw.switch_rpc.setChecked(settings.get('rpc', False))
        if hasattr(self.mw, 'switch_crossfade'):
            crossfade_on = settings.get('crossfade_enabled', False)
            self.mw.switch_crossfade.blockSignals(True)
            self.mw.switch_crossfade.setChecked(crossfade_on)
            if hasattr(self.mw, 'crossfade_slider'):
                self.mw.crossfade_slider.setEnabled(crossfade_on)
            self.mw.switch_crossfade.blockSignals(False)
        if hasattr(self.mw, 'switch_minimize_tray'):
            self.mw.switch_minimize_tray.setChecked(settings.get('minimize_to_tray', False))
            self.mw.switch_close_tray.setChecked(settings.get('close_to_tray', False))
            self.mw.switch_minimize_tray.blockSignals(False)
            self.mw.switch_close_tray.blockSignals(False)
        enable_logs_val = settings.get('enable_logs', True)
        if hasattr(self.mw, 'switch_enable_logs'):
            self.mw.switch_enable_logs.setChecked(enable_logs_val)
        if not enable_logs_val:
            logging.disable(logging.CRITICAL)
        else:
            logging.disable(logging.NOTSET)
    def sync_settings_to_manager(self):
        settings.set('volume', self.mw.mini_volume_inline.value() if hasattr(self.mw, 'mini_volume_inline') else 80)
        settings.set('last_queue_paths', [t.filepath for t in self.mw.queue.tracks] if hasattr(self.mw, 'queue') and self.mw.queue.tracks else [])
        settings.set('last_queue_index', getattr(self.mw.queue, 'current_index', -1) if hasattr(self.mw, 'queue') else -1)
        if hasattr(self.mw, 'audio_engine') and self.mw.audio_engine.player:
            time_ms = self.mw.audio_engine.get_position()
            if time_ms > 0:
                settings.set('last_playback_time', time_ms)
        settings.set('songs_is_grid', getattr(self.mw, 'songs_is_grid', False))
        settings.set('scroll_positions', {
            'songs': self.mw.list_songs.verticalScrollBar().value() if hasattr(self.mw, 'list_songs') else 0,
            'albums': self.mw.list_albums.verticalScrollBar().value() if hasattr(self.mw, 'list_albums') else 0,
            'artists': self.mw.list_artists.verticalScrollBar().value() if hasattr(self.mw, 'list_artists') else 0,
        })
    def open_logs_folder(self):
        import os
        import subprocess
        from config import LOGS_DIR
        if os.name == 'nt':
            os.startfile(LOGS_DIR)
        elif os.name == 'posix':
            subprocess.Popen(['xdg-open', LOGS_DIR])