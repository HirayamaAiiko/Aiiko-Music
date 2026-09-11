import os
import logging
import ctypes
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, pyqtSlot, QRunnable, QThreadPool
from .bass_bindings import *
from .bass_bindings import _load_bass_dll, _load_bassmix_dll, _load_basswasapi_dll
class StreamLoaderSignals(QObject):
    loaded = pyqtSignal(object, str, int)
    error = pyqtSignal(int, str)
class StreamLoaderWorker(QRunnable):
    def __init__(self, bass, filepath, is_mixer, flags, generation=0):
        super().__init__()
        self.bass = bass
        self.filepath = filepath
        self.is_mixer = is_mixer
        self.flags = flags
        self.generation = generation
        self.signals = StreamLoaderSignals()
    def run(self):
        if hasattr(self, 'engine') and getattr(self.engine, '_load_generation', 0) > self.generation:
            return
        filepath_buf = ctypes.create_unicode_buffer(self.filepath)
        stream = self.bass.BASS_StreamCreateFile(False, filepath_buf, 0, 0, self.flags)
        if not stream:
            err = self.bass.BASS_ErrorGetCode()
            try: self.signals.error.emit(err, self.filepath)
            except RuntimeError: pass
        else:
            if hasattr(self, 'engine') and getattr(self.engine, '_load_generation', 0) > self.generation:
                self.bass.BASS_StreamFree(stream)
                return
            try: self.signals.loaded.emit(stream, self.filepath, self.generation)
            except RuntimeError: pass
class AudioEngine(QObject):
    time_changed = pyqtSignal(int, int)                           
    state_changed = pyqtSignal(bool)                    
    ui_visible = True
    track_ended = pyqtSignal()                                          
    crossfade_advance = pyqtSignal()                                                            
    error_occurred = pyqtSignal(str)
    track_load_failed = pyqtSignal(str)                       
    _internal_track_ended = pyqtSignal(object)                             
    _internal_gapless_transition = pyqtSignal(str)                   
    gapless_transition_occurred = pyqtSignal(str)                                             
    def __init__(self, parent=None):
        super().__init__(parent)
        self._internal_track_ended.connect(self._handle_track_ended)
        self._internal_gapless_transition.connect(self._handle_gapless_transition)
        self._bass = None                                    
        self._stream = 0                                                        
        self._ui_stream = 0                                                                     
        self._fading_streams = []                                                        
        self._active_crossfades = {}                                                          
        self._sync_handles = {}                                               
        self._next_stream = 0                                       
        self._next_filepath = None
        self._next_injected = False                                        
        self._current_filepath = None
        self._load_generation = 0
        self._last_played_generation = 0
        self._loader_pool = QThreadPool(self)
        self._loader_pool.setMaxThreadCount(1)
        self._wasapi_proc_ref = None                                 
        self._output_mode = "bass_default"
        self._saved_volume = 80                                  
        self._is_changing_track = False
        self._crossfade_ms = 0
        self._crossfade_triggered = False
        self._initialized = False
        self._fade_audio = True
        self._eq_handles = {}
        self._eq_frequencies = [80, 120, 250, 500, 1000, 2000, 4000, 8000, 12000, 16000]
        self._end_sync_callback = SYNCPROC(self._on_stream_end)
        self._settings = __import__('settings_manager').settings
        self._fft_buffer = (ctypes.c_float * 4096)()
        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._monitor_playback)
        self._monitor_timer.start(33)
    def initialize(self, initial_volume=80):
        if self._initialized:
            return
        try:
            logging.info("Inicializando motor BASS Audio (AudioEngine)...")
            self._bass = _load_bass_dll()
            self._bassmix = _load_bassmix_dll()
            self._basswasapi = _load_basswasapi_dll()
            from settings_manager import settings
            self._output_mode = settings.get('audio_output_mode', 'bass_default')
            if self._output_mode == 'bass_wasapi' and self._basswasapi:
                logging.info("Intentando inicializar en modo WASAPI (Exclusivo)...")
                if not self._bass.BASS_Init(0, 44100, 0, None, None):
                    err = self._bass.BASS_ErrorGetCode()
                    if err != 14:
                        self.error_occurred.emit(f"Error inicializando BASS Audio (código: {err})")
                        return
                buf_ms = settings.get('audio_buffer_ms', 400)
                self._bass.BASS_SetConfig(BASS_CONFIG_BUFFER, buf_ms)
                wasapi_dev = settings.get('wasapi_device_id', "-1")
                try: wasapi_dev = int(wasapi_dev)
                except ValueError: wasapi_dev = -1
                if self._bassmix:
                    self._mixer = self._bassmix.BASS_Mixer_StreamCreate(44100, 2, BASS_SAMPLE_FLOAT | BASS_STREAM_DECODE)
                else:
                    self._mixer = 0
                def _wasapi_callback(buffer, length, user):
                    if not self._mixer: return 0
                    res = self._bass.BASS_ChannelGetData(self._mixer, buffer, length)
                    if res == 0xFFFFFFFF: return 0
                    return res
                self._wasapi_proc_ref = WASAPIPROC(_wasapi_callback)
                if not self._basswasapi.BASS_WASAPI_Init(wasapi_dev, 44100, 2, BASS_WASAPI_EXCLUSIVE | BASS_WASAPI_BUFFER, 0.2, 0, self._wasapi_proc_ref, None):
                    err = self._bass.BASS_ErrorGetCode()
                    logging.error(f"Fallo BASS WASAPI Init (error: {err}). Volviendo a DirectSound.")
                    self._output_mode = "bass_default"
                    self._bass.BASS_Free()
                    if not self._bass.BASS_Init(-1, 44100, 0, None, None):
                        self.error_occurred.emit("Fallo en fallback a DirectSound.")
                        return
                    if self._bassmix:
                        self._mixer = self._bassmix.BASS_Mixer_StreamCreate(44100, 2, BASS_SAMPLE_FLOAT | BASS_MIXER_NONSTOP)
                        if self._mixer: self._bass.BASS_ChannelPlay(self._mixer, False)
                else:
                    self._basswasapi.BASS_WASAPI_Start()
                    logging.info("BASS WASAPI (Exclusive Mode) iniciado con éxito.")
            else:
                self._output_mode = "bass_default"
                if not self._bass.BASS_Init(-1, 44100, 0, None, None):
                    err = self._bass.BASS_ErrorGetCode()
                    if err != 14:
                        self.error_occurred.emit(f"Error inicializando BASS Audio (código: {err})")
                        return
                buf_ms = settings.get('audio_buffer_ms', 400)
                self._bass.BASS_SetConfig(BASS_CONFIG_BUFFER, buf_ms)
                self._bass.BASS_SetConfig(BASS_CONFIG_UPDATEPERIOD, 10)
                if self._bassmix:
                    self._mixer = self._bassmix.BASS_Mixer_StreamCreate(44100, 2, BASS_SAMPLE_FLOAT | BASS_MIXER_NONSTOP)
                    if self._mixer:
                        self._bass.BASS_ChannelPlay(self._mixer, False)
                        logging.info("BASS Mixer (bassmix.dll) activado para latencia cero (DirectSound/Compartido).")
                    else:
                        self._mixer = 0
                else:
                    self._mixer = 0
            from config import APP_ROOT
            flac_path = os.path.join(APP_ROOT, "libs", "bassflac.dll")
            if os.path.exists(flac_path):
                plugin = self._bass.BASS_PluginLoad(flac_path.encode('utf-8'), 0)
                if plugin:
                    logging.info("Plugin BASSFLAC cargado correctamente.")
                else:
                    logging.warning(f"No se pudo cargar BASSFLAC (error: {self._bass.BASS_ErrorGetCode()})")
            from core.audio.bass_bindings import _load_bass_fx_dll
            self._bass_fx = _load_bass_fx_dll()
            if self._bass_fx:
                version = self._bass_fx.BASS_FX_GetVersion()
                logging.info(f"Plugin BASS_FX cargado correctamente (Versión: {version}).")
            else:
                logging.warning("No se pudo encontrar o cargar bass_fx.dll")
            self._saved_volume = initial_volume
            self._initialized = True
            self.reload_settings()                      
            self._eq_handles = {}
            self._eq_frequencies = [80, 120, 250, 500, 1000, 2000, 4000, 8000, 12000, 16000]
            self._init_eq()
            self._audio_devices_cache = self._fetch_audio_devices()
            logging.info("Motor BASS Audio inicializado correctamente.")
        except FileNotFoundError as e:
            self.error_occurred.emit(str(e))
        except Exception as e:
            logging.error(f"Error crítico inicializando BASS: {e}")
            self.error_occurred.emit(f"Error Crítico: No se pudo iniciar BASS Audio: {e}")
    def _init_eq(self):
        if not self._mixer: return
        try:
            from core.audio.bass_bindings import BASS_FX_BFX_PEAKEQ
            for i, freq in enumerate(self._eq_frequencies):
                fx_handle = self._bass.BASS_ChannelSetFX(self._mixer, BASS_FX_BFX_PEAKEQ, 0)
                if fx_handle:
                    self._eq_handles[i] = fx_handle
                else:
                    logging.warning(f"No se pudo inicializar la banda EQ {freq}Hz. Error: {self._bass.BASS_ErrorGetCode()}")
        except Exception as e:
            logging.error(f"Error en BASS EQ init: {e}")
    def set_eq_band(self, index, gain_db):
        if index not in self._eq_handles: return
        fx_handle = self._eq_handles[index]
        freq = self._eq_frequencies[index]
        try:
            from core.audio.bass_bindings import BASS_BFX_PEAKEQ, BASS_BFX_CHANALL
            param = BASS_BFX_PEAKEQ()
            param.lBand = index
            param.fCenter = float(freq)
            param.fBandwidth = 0.0                                     
            param.fQ = 1.41                                 
            param.fGain = float(gain_db)
            param.lChannel = BASS_BFX_CHANALL
            self._bass.BASS_FXSetParameters(fx_handle, ctypes.byref(param))
        except Exception as e:
            logging.error(f"Error al cambiar EQ banda {index}: {e}")
    def set_eq_preamp(self, gain_db):
        if not getattr(self, '_mixer', 0): return
        try:
            from core.audio.bass_bindings import BASS_ATTRIB_VOL
            linear_vol = 10 ** (gain_db / 20.0)
            self._preamp_linear_vol = linear_vol
            active = self._bass.BASS_ChannelIsActive(self._mixer)
            if active == 1:          
                self._bass.BASS_ChannelSetAttribute(self._mixer, BASS_ATTRIB_VOL, ctypes.c_float(linear_vol))
        except Exception as e:
            logging.error(f"Error ajustando Preamp: {e}")
    def apply_buffer_config(self, buffer_ms):
        if self._initialized:
            self._bass.BASS_SetConfig(BASS_CONFIG_BUFFER, buffer_ms)
    def reload_settings(self):
        from settings_manager import settings
        self._fade_audio = settings.get('fade_audio', True)
    @property
    def player(self):
        return self if self._initialized else None
    @property
    def instance(self):
        return self._bass if self._initialized else None
    def get_audio_devices(self):
        if hasattr(self, '_audio_devices_cache'):
            return self._audio_devices_cache
        return self._fetch_audio_devices()
    def _fetch_audio_devices(self):
        if not self._initialized: return []
        devices = []
        devices.append({"id": "default", "name": "Sistema por defecto"})
        if getattr(self, '_output_mode', 'bass_default') == 'bass_wasapi' and getattr(self, '_basswasapi', None):
            info = BASS_DEVICEINFO()
            idx = 0
            while self._basswasapi.BASS_WASAPI_GetDeviceInfo(idx, ctypes.byref(info)):
                if (info.flags & 1) and not (info.flags & 8):
                    try:
                        name = info.name.decode('mbcs', errors='ignore') if info.name else f"WASAPI Device {idx}"
                    except:
                        name = f"Dispositivo WASAPI {idx}"
                    devices.append({'id': str(idx), 'name': name})
                idx += 1
        else:
            info = BASS_DEVICEINFO()
            idx = 1                                                             
            while self._bass.BASS_GetDeviceInfo(idx, ctypes.byref(info)):
                if info.flags & 1:                      
                    try:
                        name = info.name.decode('mbcs', errors='ignore') if info.name else f"Device {idx}"
                    except:
                        name = f"Dispositivo {idx}"
                    devices.append({'id': str(idx), 'name': name})
                idx += 1
        return devices
    def set_audio_device(self, device_id):
        if not self._initialized: return False
        if getattr(self, '_output_mode', 'bass_default') == 'bass_wasapi':
            return True
        try:
            if device_id == "default":
                dev_idx = -1
            else:
                dev_idx = int(device_id)
        except ValueError:
            return False
        info = BASS_DEVICEINFO()
        if dev_idx != -1 and self._bass.BASS_GetDeviceInfo(dev_idx, ctypes.byref(info)):
            if not (info.flags & 4):                       
                self._bass.BASS_Init(dev_idx, 44100, 0, None, None)
        self._bass.BASS_SetDevice(dev_idx)
        target_stream = getattr(self, '_mixer', 0)
        if not target_stream:
            target_stream = self._stream
        if target_stream:
            self._bass.BASS_ChannelSetDevice(target_stream, dev_idx)
        return True
    def play_file(self, filepath, start_time=0, use_crossfade=False):
        if not self._initialized:
            self.initialize()
        if not os.path.exists(filepath):
            self.error_occurred.emit(f"Archivo no encontrado: {filepath}")
            self.track_load_failed.emit(filepath)
            return False
        self._is_changing_track = True
        self._current_filepath = filepath
        do_crossfade = use_crossfade and self._crossfade_ms > 0 and self._stream and self.is_playing() and start_time == 0
        if not use_crossfade and hasattr(self, '_active_crossfades'):
            for s, info in list(self._active_crossfades.items()):
                if info['type'] == 'out':
                    self._free_fading_stream(s)
            self._active_crossfades.clear()
        if do_crossfade:
            old_stream = self._stream
            self._ui_stream = old_stream
            self._fading_streams.append(old_stream)
            if old_stream in self._sync_handles:
                if getattr(self, '_mixer', 0):
                    self._bassmix.BASS_Mixer_ChannelRemoveSync(old_stream, self._sync_handles[old_stream])
                else:
                    self._bass.BASS_ChannelRemoveSync(old_stream, self._sync_handles[old_stream])
                del self._sync_handles[old_stream]
            if getattr(self, '_mixer', 0):
                pos_bytes = self._bassmix.BASS_Mixer_ChannelGetPosition(old_stream, BASS_POS_BYTE)
            else:
                pos_bytes = self._bass.BASS_ChannelGetPosition(old_stream, BASS_POS_BYTE)
            start_ms = int(self._bass.BASS_ChannelBytes2Seconds(old_stream, pos_bytes) * 1000) if pos_bytes not in (-1, 0xFFFFFFFFFFFFFFFF) else 0
            self._active_crossfades[old_stream] = {
                'start_ms': start_ms,
                'duration': self._crossfade_ms,
                'type': 'out',
                'initial': self._saved_volume / 100.0
            }
        else:
            if self._stream:
                old_stream = self._stream
                if not self.is_playing():
                    if old_stream in self._sync_handles:
                        if getattr(self, '_mixer', 0):
                            self._bassmix.BASS_Mixer_ChannelRemoveSync(old_stream, self._sync_handles[old_stream])
                        else:
                            self._bass.BASS_ChannelRemoveSync(old_stream, self._sync_handles[old_stream])
                        del self._sync_handles[old_stream]
                    if getattr(self, '_mixer', 0):
                        self._bassmix.BASS_Mixer_ChannelRemove(old_stream)
                    self._async_free(old_stream)
                else:
                    self._fading_streams.append(old_stream)
                    if old_stream in self._sync_handles:
                        if getattr(self, '_mixer', 0):
                            self._bassmix.BASS_Mixer_ChannelRemoveSync(old_stream, self._sync_handles[old_stream])
                        else:
                            self._bass.BASS_ChannelRemoveSync(old_stream, self._sync_handles[old_stream])
                        del self._sync_handles[old_stream]
                    self._bass.BASS_ChannelSlideAttribute(old_stream, BASS_ATTRIB_VOL | BASS_SLIDE_LOG, ctypes.c_float(0.0), 50)
                    QTimer.singleShot(200, lambda s=old_stream: self._free_fading_stream(s))
        self._stream = 0
        self._crossfade_triggered = False
        if getattr(self, '_next_stream', 0) and self._next_filepath == filepath:
            self._load_generation += 1
            self._last_played_generation = self._load_generation
            self._stream = self._next_stream
            self._next_stream = 0
            self._next_filepath = None
            self._next_injected = False
            self._finalize_play(start_time, do_crossfade)
        else:
            self._release_preload()
            flags = BASS_UNICODE | BASS_SAMPLE_FLOAT | 0x20000 | 0x40000000
            if getattr(self, '_mixer', 0):
                flags |= BASS_STREAM_DECODE
            self._load_generation = getattr(self, '_load_generation', 0) + 1
            current_gen = self._load_generation
            worker = StreamLoaderWorker(self._bass, filepath, getattr(self, '_mixer', 0), flags, current_gen)
            worker.engine = self                                       
            worker.signals.loaded.connect(lambda stream, sig_path, gen, path=filepath, st=start_time, dc=do_crossfade: self._on_stream_loaded(stream, path, st, dc, gen))
            worker.signals.error.connect(lambda err, path=filepath: self._on_stream_error(err, path))
            self._loader_pool.start(worker)
        return True
    def _on_stream_error(self, err_code, filepath):
        if self._current_filepath == filepath:
            self.error_occurred.emit(f"Error abriendo archivo (BASS error: {err_code}): {filepath}")
            self.track_load_failed.emit(filepath)
            self._is_changing_track = False
    def _on_stream_loaded(self, stream, filepath, start_time, do_crossfade, generation=0):
        if generation > 0 and generation < getattr(self, '_last_played_generation', 0):
            self._bass.BASS_StreamFree(stream)
            return
        self._last_played_generation = generation
        self._current_filepath = filepath
        if getattr(self, '_stream', 0):
            import logging
            logging.warning(f"Descartando stream duplicado asíncrono para prevenir ghost stream: {filepath}")
            self._bass.BASS_StreamFree(stream)
            return
        self._stream = stream
        self._finalize_play(start_time, do_crossfade)
    def _finalize_play(self, start_time, do_crossfade):
        if getattr(self, '_mixer', 0):
            self._bassmix.BASS_Mixer_ChannelRemove(self._stream)
            self._bassmix.BASS_Mixer_StreamAddChannel(self._mixer, self._stream, 0x800000)
        target_vol = self._saved_volume / 100.0
        if do_crossfade:
            self._bass.BASS_ChannelSetAttribute(self._stream, BASS_ATTRIB_VOL, ctypes.c_float(0.0))
        else:
            self._bass.BASS_ChannelSetAttribute(self._stream, BASS_ATTRIB_VOL, ctypes.c_float(target_vol))
        if start_time > 0:
            self.set_position(start_time)
        self._register_end_sync(self._stream)
        if getattr(self, '_mixer', 0):
            self._bass.BASS_ChannelSetAttribute(self._mixer, BASS_ATTRIB_VOL, ctypes.c_float(getattr(self, '_preamp_linear_vol', 1.0)))
            if getattr(self, '_output_mode', 'bass_default') == 'bass_wasapi' and getattr(self, '_basswasapi', None):
                self._basswasapi.BASS_WASAPI_Start()
            else:
                active = self._bass.BASS_ChannelIsActive(self._mixer)
                if active == 3:         
                    self._bass.BASS_ChannelPlay(self._mixer, True)
                else:
                    self._bass.BASS_ChannelPlay(self._mixer, False)
        else:
            self._bass.BASS_ChannelPlay(self._stream, False)
        if do_crossfade:
            self._active_crossfades[self._stream] = {
                'start_ms': start_time,
                'duration': self._crossfade_ms,
                'type': 'in',
                'target': target_vol
            }
        else:
            QTimer.singleShot(50, self._unlock_track_change)
        self.state_changed.emit(True)
        return True
    def _async_free(self, stream):
        if not stream: return
        try:
            if getattr(self, '_mixer', 0):
                self._bassmix.BASS_Mixer_ChannelRemove(stream)
            self._bass.BASS_StreamFree(stream)
        except Exception as e:
            import logging
            logging.debug(f"Error liberando stream: {e}")
    def _free_fading_stream(self, stream):
        if getattr(self, '_ui_stream', 0) == stream:
            self._ui_stream = 0
        if stream in self._fading_streams:
            self._fading_streams.remove(stream)
            self._async_free(stream)
    def _unlock_track_change(self):
        self._is_changing_track = False
    def _free_old_stream_delayed(self, stream):
        if stream:
            try:
                if getattr(self, '_mixer', 0):
                    self._bassmix.BASS_Mixer_ChannelRemove(stream)
                self._bass.BASS_StreamFree(stream)
            except Exception as e:
                logging.error(f"Error liberando stream diferido: {e}")
    def _register_end_sync(self, stream: int):
        if getattr(self, '_mixer', 0):
            sync_handle = self._bassmix.BASS_Mixer_ChannelSetSync(
                stream,
                BASS_SYNC_END | BASS_SYNC_ONETIME | 0x40000000,                    
                0,
                self._end_sync_callback,
                None
            )
        else:
            sync_handle = self._bass.BASS_ChannelSetSync(
                stream,
                BASS_SYNC_END | BASS_SYNC_ONETIME | 0x40000000,
                0,
                self._end_sync_callback,
                None
            )
        self._sync_handles[stream] = sync_handle
    def _on_stream_end(self, sync_handle, channel, data, user):
        if channel != self._stream:
            return
        gapless_enabled = self._settings.get('gapless_enabled', True)
        if not getattr(self, '_next_stream', 0) or not getattr(self, '_next_injected', False) or self._crossfade_ms > 0 or not getattr(self, '_mixer', 0) or not gapless_enabled:
            QMetaObject.invokeMethod(
                self, 
                "_notify_natural_end", 
                Qt.ConnectionType.QueuedConnection, 
                Q_ARG(object, channel)
            )
            return
        try:
            old_stream = self._stream
            next_filepath_local = self._next_filepath
            self._stream = self._next_stream
            self._current_filepath = next_filepath_local
            self._next_stream = 0
            self._next_filepath = None
            self._next_injected = False
            QMetaObject.invokeMethod(
                self,
                "_finalize_gapless_transition",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(object, old_stream),
                Q_ARG(object, next_filepath_local)
            )
        except Exception as e:
            logging.exception(f"[Gapless V4] Excepción en _on_stream_end, usando fallback. Error: {e}")
            QMetaObject.invokeMethod(
                self, 
                "_notify_natural_end", 
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(object, channel)
            )
    @pyqtSlot(object)
    def _notify_natural_end(self, stream_handle):
        logging.warning(f"[Gapless V4] PATH FALLBACK TOMADO → canal {stream_handle}")
        self._internal_track_ended.emit(stream_handle)
    @pyqtSlot(object, object)
    def _finalize_gapless_transition(self, old_stream, filepath):
        from settings_manager import settings
        buffer_ms = int(settings.get('audio_buffer_ms', 400))
        delay_ms = max(1000, buffer_ms + 500)
        QTimer.singleShot(delay_ms, lambda s=old_stream: self._free_old_stream_delayed(s))
        if old_stream in self._sync_handles:
            del self._sync_handles[old_stream]
        self._register_end_sync(self._stream)
        logging.info(f"[Gapless V4] PATH GAPLESS (Inyección Futura) COMPLETADO → {filepath}")
        self.gapless_transition_occurred.emit(filepath)
    def _handle_gapless_transition(self, new_filepath):
        pass
    def _handle_track_ended(self, ended_stream_handle):
        if self._is_changing_track or ended_stream_handle != getattr(self, '_stream', 0):
            return
        self._is_changing_track = True
        logging.info("Track ended (BASS SYNC_END)")
        self.track_ended.emit()
    def _release_preload(self):
        if getattr(self, '_next_stream', 0):
            if getattr(self, '_mixer', 0) and getattr(self, '_next_injected', False):
                self._bassmix.BASS_Mixer_ChannelRemove(self._next_stream)
            self._bass.BASS_StreamFree(self._next_stream)
            self._next_stream = 0
            self._next_filepath = None
            self._next_injected = False
    def preload_track(self, filepath):
        if not self._initialized or not getattr(self, '_mixer', 0):
            return
        if getattr(self, '_next_filepath', None) == filepath:
            return
        self._release_preload()
        if not filepath or not __import__('os').path.exists(filepath):
            return
        self._next_filepath = filepath
        flags = BASS_UNICODE | BASS_SAMPLE_FLOAT | 0x20000 | 0x40000000 | BASS_STREAM_DECODE
        worker = StreamLoaderWorker(self._bass, filepath, self._mixer, flags, 0)
        worker.signals.loaded.connect(lambda stream, sig_path, gen, path=filepath: self._on_preload_loaded(stream, path))
        worker.signals.error.connect(lambda err, path=filepath: self._on_preload_error(err, path))
        self._loader_pool.start(worker)
    def _on_preload_loaded(self, stream, filepath):
        if getattr(self, '_next_filepath', None) != filepath:
            self._bass.BASS_StreamFree(stream)
            return
        self._next_stream = stream
        target_vol = self._saved_volume / 100.0
        self._bass.BASS_ChannelSetAttribute(self._next_stream, BASS_ATTRIB_VOL, ctypes.c_float(target_vol))
        self._next_injected = False
    def _on_preload_error(self, err_code, filepath):
        if getattr(self, '_next_filepath', None) == filepath:
            logging.warning(f"No se pudo precargar asíncronamente (BASS error: {err_code}): {filepath}")
            self._next_filepath = None
            self._next_stream = 0
    def _inject_next_to_future(self):
        if not getattr(self, '_mixer', 0) or not getattr(self, '_stream', 0) or not getattr(self, '_next_stream', 0):
            return
        if getattr(self, '_next_injected', False):
            return
        len_bytes = self._bass.BASS_ChannelGetLength(self._stream, BASS_POS_BYTE)
        pos_bytes = self._bass.BASS_ChannelGetPosition(self._stream, BASS_POS_BYTE)
        if len_bytes == -1 or len_bytes == 0xFFFFFFFFFFFFFFFF or pos_bytes == -1 or pos_bytes == 0xFFFFFFFFFFFFFFFF:
            return
        rem_bytes = max(0, len_bytes - pos_bytes)
        rem_sec = self._bass.BASS_ChannelBytes2Seconds(self._stream, rem_bytes)
        mix_delay_bytes = self._bass.BASS_ChannelSeconds2Bytes(self._mixer, rem_sec)
        flags = 0x800000
        res = self._bassmix.BASS_Mixer_StreamAddChannelEx(self._mixer, self._next_stream, flags, mix_delay_bytes, 0)
        if res:
            self._next_injected = True
            logging.info(f"[Gapless V4] Inyección al futuro exitosa. Canción B insertada con retraso de {rem_sec:.2f}s ({mix_delay_bytes} bytes).")
        else:
            err = self._bass.BASS_ErrorGetCode()
            logging.warning(f"[Gapless V4] Falló inyección al futuro (Error: {err})")
    def pause(self):
        if not self._stream: return
        self._is_pausing = True
        if self._fade_audio:
            if getattr(self, '_mixer', 0):
                self._bass.BASS_ChannelSlideAttribute(
                    self._mixer, BASS_ATTRIB_VOL | BASS_SLIDE_LOG, ctypes.c_float(0.0), 300
                )
            else:
                self._bass.BASS_ChannelSlideAttribute(
                    self._stream, BASS_ATTRIB_VOL | BASS_SLIDE_LOG, ctypes.c_float(0.0), 300
                )
            QTimer.singleShot(310, self._pause_after_fade)
        else:
            if getattr(self, '_mixer', 0):
                self._bass.BASS_ChannelSetAttribute(self._mixer, BASS_ATTRIB_VOL, ctypes.c_float(0.0))
            else:
                self._bass.BASS_ChannelSetAttribute(self._stream, BASS_ATTRIB_VOL, ctypes.c_float(0.0))
            self._pause_after_fade()
        self.state_changed.emit(False)
    def _pause_after_fade(self):
        if not getattr(self, '_is_pausing', False): return
        if self._stream:
            if getattr(self, '_mixer', 0):
                self._bassmix.BASS_Mixer_ChannelFlags(self._stream, BASS_MIXER_PAUSE, BASS_MIXER_PAUSE)
                if getattr(self, '_output_mode', 'bass_default') == 'bass_wasapi' and getattr(self, '_basswasapi', None):
                    self._basswasapi.BASS_WASAPI_Stop(False)
                else:
                    self._bass.BASS_ChannelPause(self._mixer)
            else:
                self._bass.BASS_ChannelPause(self._stream)
        self.state_changed.emit(False)
    def resume(self):
        if not self._stream: return
        self._is_pausing = False
        if self._fade_audio:
            if getattr(self, '_mixer', 0):
                self._bassmix.BASS_Mixer_ChannelFlags(self._stream, 0, BASS_MIXER_PAUSE)
                if getattr(self, '_output_mode', 'bass_default') == 'bass_wasapi' and getattr(self, '_basswasapi', None):
                    self._basswasapi.BASS_WASAPI_Start()
                else:
                    self._bass.BASS_ChannelPlay(self._mixer, False)
                target_vol = getattr(self, '_preamp_linear_vol', 1.0)
                self._bass.BASS_ChannelSlideAttribute(
                    self._mixer, BASS_ATTRIB_VOL | BASS_SLIDE_LOG, ctypes.c_float(target_vol), 300
                )
            else:
                self._bass.BASS_ChannelSetAttribute(self._stream, BASS_ATTRIB_VOL, ctypes.c_float(0.0))
                self._bass.BASS_ChannelPlay(self._stream, False)
                target_vol = self._saved_volume / 100.0
                self._bass.BASS_ChannelSlideAttribute(
                    self._stream, BASS_ATTRIB_VOL | BASS_SLIDE_LOG, ctypes.c_float(target_vol), 300
                )
        else:
            if getattr(self, '_mixer', 0):
                target_vol = getattr(self, '_preamp_linear_vol', 1.0)
                self._bass.BASS_ChannelSetAttribute(self._mixer, BASS_ATTRIB_VOL, ctypes.c_float(target_vol))
                self._bassmix.BASS_Mixer_ChannelFlags(self._stream, 0, BASS_MIXER_PAUSE)
                if getattr(self, '_output_mode', 'bass_default') == 'bass_wasapi' and getattr(self, '_basswasapi', None):
                    self._basswasapi.BASS_WASAPI_Start()
                else:
                    self._bass.BASS_ChannelPlay(self._mixer, False)
            else:
                target_vol = self._saved_volume / 100.0
                self._bass.BASS_ChannelSetAttribute(self._stream, BASS_ATTRIB_VOL, ctypes.c_float(target_vol))
                self._bass.BASS_ChannelPlay(self._stream, False)
        self.state_changed.emit(True)
    def stop(self):
        if self._stream:
            if getattr(self, '_mixer', 0):
                self._bassmix.BASS_Mixer_ChannelRemove(self._stream)
            else:
                self._bass.BASS_ChannelStop(self._stream)
            self.state_changed.emit(False)
        self._release_preload()
    def unload(self):
        if self._stream:
            self.stop()
            self._bass.BASS_StreamFree(self._stream)
            if self._stream in self._sync_handles:
                del self._sync_handles[self._stream]
            self._stream = 0
            self._current_filepath = None
        self._release_preload()
        self.state_changed.emit(False)
    def toggle_play_pause(self):
        if not self._stream: return
        if self.is_playing():
            self.pause()
        else:
            self.resume()
    def _get_position_ms(self):
        if not self._stream: return 0
        if getattr(self, '_mixer', 0):
            pos_bytes = self._bassmix.BASS_Mixer_ChannelGetPosition(self._stream, BASS_POS_BYTE)
        else:
            pos_bytes = self._bass.BASS_ChannelGetPosition(self._stream, BASS_POS_BYTE)
        if pos_bytes == -1 or pos_bytes == 0xFFFFFFFFFFFFFFFF:
            return 0
        return int(self._bass.BASS_ChannelBytes2Seconds(self._stream, pos_bytes) * 1000)
    def _get_length_ms(self):
        if not self._stream: return 0
        len_bytes = self._bass.BASS_ChannelGetLength(self._stream, BASS_POS_BYTE)
        if len_bytes == -1 or len_bytes == 0xFFFFFFFFFFFFFFFF:
            return 0
        return int(self._bass.BASS_ChannelBytes2Seconds(self._stream, len_bytes) * 1000)
    def get_position(self):
        return self._get_position_ms()
    def set_position(self, pos_ms):
        if self._stream:
            if getattr(self, '_next_stream', 0) and getattr(self, '_next_injected', False):
                if getattr(self, '_mixer', 0):
                    self._bassmix.BASS_Mixer_ChannelRemove(self._next_stream)
                self._next_injected = False
            pos_bytes = self._bass.BASS_ChannelSeconds2Bytes(self._stream, pos_ms / 1000.0)
            if getattr(self, '_mixer', 0):
                self._bassmix.BASS_Mixer_ChannelSetPosition(self._stream, pos_bytes, 0)                    
            else:
                self._bass.BASS_ChannelSetPosition(self._stream, pos_bytes, 0)
    def get_length(self):
        return self._get_length_ms()
    def get_fft_data(self):
        if not self._stream or not self._initialized:
            return None
        target = self._mixer if getattr(self, '_mixer', 0) else self._stream
        from core.audio.bass_bindings import BASS_DATA_FFT8192
        if getattr(self, '_output_mode', 'bass_default') == 'bass_wasapi' and getattr(self, '_basswasapi', None):
            res = self._basswasapi.BASS_WASAPI_GetData(ctypes.byref(self._fft_buffer), BASS_DATA_FFT8192)
        else:
            res = self._bass.BASS_ChannelGetData(target, ctypes.byref(self._fft_buffer), BASS_DATA_FFT8192)
        if res == 0xFFFFFFFF or res == 4294967295:             
            return None
        import numpy as np
        return np.array(self._fft_buffer, dtype=np.float32)
    def _apply_log_volume(self, ui_volume):
        if self._stream:
            if hasattr(self, '_active_crossfades') and self._stream in self._active_crossfades:
                self._active_crossfades[self._stream]['target'] = ui_volume / 100.0
            else:
                self._bass.BASS_ChannelSetAttribute(
                    self._stream, BASS_ATTRIB_VOL, ctypes.c_float(ui_volume / 100.0)
                )
    def set_volume(self, volume):
        self._saved_volume = int(volume)
        self._apply_log_volume(self._saved_volume)
    def set_mute(self, muted):
        if self._stream:
            if muted:
                self._bass.BASS_ChannelSetAttribute(self._stream, BASS_ATTRIB_VOL, ctypes.c_float(0.0))
            else:
                self._apply_log_volume(self._saved_volume)
    def is_muted(self):
        if not self._stream: return False
        vol = ctypes.c_float(0)
        self._bass.BASS_ChannelGetAttribute(self._stream, BASS_ATTRIB_VOL, ctypes.byref(vol))
        return vol.value < 0.01
    def is_playing(self):
        if not self._stream: return False
        if getattr(self, '_mixer', 0):
            flags = self._bassmix.BASS_Mixer_ChannelFlags(self._stream, 0, 0)
            return not bool(flags & BASS_MIXER_PAUSE)
        return self._bass.BASS_ChannelIsActive(self._stream) == BASS_ACTIVE_PLAYING
    def get_state(self):
        if not self._stream: return "NothingSpecial"
        if self.is_playing(): return "Playing"
        if getattr(self, '_mixer', 0):
            flags = self._bassmix.BASS_Mixer_ChannelFlags(self._stream, 0, 0)
            if flags & BASS_MIXER_PAUSE: return "Paused"
            return "Stopped"
        else:
            active = self._bass.BASS_ChannelIsActive(self._stream)
            if active == BASS_ACTIVE_PAUSED: return "Paused"
            elif active == BASS_ACTIVE_STOPPED: return "Stopped"
            return "NothingSpecial"
    def get_media(self):
        return self._stream != 0
    def set_crossfade(self, seconds):
        self._crossfade_ms = int(seconds * 1000)
    def restore_volume_after_crossfade(self):
        pass
    def _monitor_playback(self):
        if not self._stream or not self._initialized:
            return
        if hasattr(self, '_active_crossfades') and self._active_crossfades:
            import math
            to_remove = []
            for stream, data in self._active_crossfades.items():
                if getattr(self, '_mixer', 0):
                    pos_bytes = self._bassmix.BASS_Mixer_ChannelGetPosition(stream, BASS_POS_BYTE)
                else:
                    pos_bytes = self._bass.BASS_ChannelGetPosition(stream, BASS_POS_BYTE)
                if pos_bytes == -1 or pos_bytes == 0xFFFFFFFFFFFFFFFF or self._bass.BASS_ChannelIsActive(stream) == 0:
                    progress = 1.0
                else:
                    curr_ms = int(self._bass.BASS_ChannelBytes2Seconds(stream, pos_bytes) * 1000)
                    elapsed_ms = curr_ms - data['start_ms']
                    if elapsed_ms < 0: elapsed_ms = 0
                    progress = min(1.0, elapsed_ms / data['duration'])
                if data['type'] == 'out':
                    vol = math.sqrt(1.0 - progress) * data.get('initial', 1.0)
                else:
                    vol = math.sqrt(progress) * data.get('target', 1.0)
                self._bass.BASS_ChannelSetAttribute(stream, BASS_ATTRIB_VOL, ctypes.c_float(vol))
                if progress >= 1.0:
                    to_remove.append(stream)
            for stream in to_remove:
                info = self._active_crossfades.pop(stream)
                if info['type'] == 'out':
                    self._free_fading_stream(stream)
                elif info['type'] == 'in':
                    self._unlock_track_change()
        stream_to_monitor = getattr(self, '_ui_stream', 0)
        if not stream_to_monitor:
            stream_to_monitor = self._stream
        if getattr(self, '_mixer', 0):
            flags_ui = self._bassmix.BASS_Mixer_ChannelFlags(stream_to_monitor, 0, 0)
            ui_active = BASS_ACTIVE_PAUSED if (flags_ui & BASS_MIXER_PAUSE) else BASS_ACTIVE_PLAYING
        else:
            ui_active = self._bass.BASS_ChannelIsActive(stream_to_monitor)
        if ui_active in [BASS_ACTIVE_PLAYING, BASS_ACTIVE_PAUSED]:
            if getattr(self, '_mixer', 0):
                pos_bytes = self._bassmix.BASS_Mixer_ChannelGetPosition(stream_to_monitor, BASS_POS_BYTE)
            else:
                pos_bytes = self._bass.BASS_ChannelGetPosition(stream_to_monitor, BASS_POS_BYTE)
            len_bytes = self._bass.BASS_ChannelGetLength(stream_to_monitor, BASS_POS_BYTE)
            curr_ms = 0
            total_ms = 0
            if pos_bytes != -1 and pos_bytes != 0xFFFFFFFFFFFFFFFF:
                curr_ms = int(self._bass.BASS_ChannelBytes2Seconds(stream_to_monitor, pos_bytes) * 1000)
            if len_bytes != -1 and len_bytes != 0xFFFFFFFFFFFFFFFF:
                total_ms = int(self._bass.BASS_ChannelBytes2Seconds(stream_to_monitor, len_bytes) * 1000)
            if total_ms > 0 and curr_ms >= 0:
                if curr_ms != getattr(self, '_last_emitted_ms', -1):
                    if getattr(self, 'ui_visible', True):
                        self.time_changed.emit(curr_ms, total_ms)
                    self._last_emitted_ms = curr_ms
        if getattr(self, '_mixer', 0):
            flags_main = self._bassmix.BASS_Mixer_ChannelFlags(self._stream, 0, 0)
            main_active = BASS_ACTIVE_PAUSED if (flags_main & BASS_MIXER_PAUSE) else BASS_ACTIVE_PLAYING
        else:
            main_active = self._bass.BASS_ChannelIsActive(self._stream)
        if main_active in [BASS_ACTIVE_PLAYING, BASS_ACTIVE_PAUSED]:
            curr_ms_main = self._get_position_ms()
            total_ms_main = self._get_length_ms()
            if total_ms_main > 0 and curr_ms_main >= 0:
                time_left = total_ms_main - curr_ms_main
                if getattr(self, '_next_stream', 0) and not getattr(self, '_next_injected', False):
                    if time_left <= 15000 or total_ms_main <= 15000:
                        self._inject_next_to_future()
                if self._crossfade_ms > 0 and main_active == BASS_ACTIVE_PLAYING and not self._crossfade_triggered:
                    if 0 < time_left <= self._crossfade_ms:
                        self._crossfade_triggered = True
                        self._is_changing_track = True                       
                        logging.info("Crossfade Trigger: Adelantando fin de pista para superposición.")
                        self.crossfade_advance.emit()
    def cleanup(self):
        for stream in self._fading_streams:
            if getattr(self, '_mixer', 0):
                self._bassmix.BASS_Mixer_ChannelRemove(stream)
            self._bass.BASS_StreamFree(stream)
        self._fading_streams.clear()
        if getattr(self, '_next_stream', 0):
            if getattr(self, '_mixer', 0):
                self._bassmix.BASS_Mixer_ChannelRemove(self._next_stream)
            self._bass.BASS_StreamFree(self._next_stream)
            self._next_stream = 0
            self._next_filepath = None
        if self._stream:
            if getattr(self, '_mixer', 0):
                self._bassmix.BASS_Mixer_ChannelRemove(self._stream)
            self._bass.BASS_StreamFree(self._stream)
            self._stream = 0
        if getattr(self, '_mixer', 0):
            self._bass.BASS_StreamFree(self._mixer)
            self._mixer = 0
        if getattr(self, '_output_mode', 'bass_default') == 'bass_wasapi' and getattr(self, '_basswasapi', None):
            try:
                self._basswasapi.BASS_WASAPI_Free()
            except Exception as e:
                import logging
                logging.debug(f"Error liberando WASAPI: {e}")
        if self._bass and self._initialized:
            self._bass.BASS_Free()
            self._initialized = False