import json
import os
from PyQt6.QtCore import QObject, pyqtSignal
from settings_manager import settings
from config import INSTALL_ROOT
class EQController(QObject):
    profile_loaded = pyqtSignal(list, float)
    DEFAULT_PRESETS = {
        "Flat": ([0.0]*10, 0.0),
        "V-Shape": ([4.0, 3.0, -1.0, -2.0, 0.0, 1.0, 2.0, 2.5, 3.0, 3.5], -4.0),
        "Acoustic / Vocal": ([-2.0, -1.0, 0.0, 1.0, 2.0, 3.5, 3.0, 1.5, 0.5, 0.0], -3.5),
        "Jazz / Warm": ([2.0, 3.0, 2.0, 0.0, -1.0, 0.0, 1.0, 2.0, 1.5, 1.0], -3.0),
        "Rock / Metal": ([3.5, 2.5, -2.0, -3.5, -1.0, 1.0, 3.5, 2.0, 1.5, 2.0], -3.5),
        "Electronic / Dance": ([5.0, 4.0, 1.0, -1.5, -2.5, -1.0, 1.5, 3.0, 4.0, 4.5], -5.0),
        "Classical / Air": ([1.5, 1.0, 0.0, -1.0, -0.5, 0.0, 1.0, 1.5, 2.0, 2.5], -2.5),
        "Sub-Bass Focus": ([6.0, 5.0, 2.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.5, 1.0], -6.0)
    }
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.audio_engine = self.main_window.audio_engine
        self.presets_dir = os.path.join(INSTALL_ROOT, "presets")
        os.makedirs(self.presets_dir, exist_ok=True)
        self.PRESETS = self.DEFAULT_PRESETS.copy()
        self.load_custom_presets()
        self.current_preset = settings.get("eq_preset", "Flat")
        default_bands, default_preamp = self.PRESETS.get("Flat", ([0.0]*10, 0.0))
        self.current_bands = settings.get("eq_bands", default_bands.copy())
        self.current_preamp = settings.get("eq_preamp", default_preamp)
        self.is_enabled = settings.get("eq_enabled", False)
    def load_custom_presets(self):
        if not os.path.exists(self.presets_dir): return
        for file in os.listdir(self.presets_dir):
            if file.endswith(".aiikoeq"):
                try:
                    with open(os.path.join(self.presets_dir, file), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        name = data.get("name", file.replace(".aiikoeq", ""))
                        bands = data.get("bands")
                        preamp = data.get("preamp", 0.0)
                        if bands and len(bands) == 10:
                            self.PRESETS[name] = (bands, preamp)
                except Exception as e:
                    import logging
                    logging.error(f"Error cargando preset {file}: {e}")
    def save_preset(self, name):
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
        if not safe_name: safe_name = "Custom_Preset"
        file_path = os.path.join(self.presets_dir, f"{safe_name}.aiikoeq")
        data = {
            "name": safe_name,
            "bands": self.current_bands,
            "preamp": self.current_preamp
        }
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            self.PRESETS[safe_name] = (self.current_bands.copy(), self.current_preamp)
            self.current_preset = safe_name
            settings.set("eq_preset", safe_name)
            return safe_name
        except Exception as e:
            import logging
            logging.error(f"Error guardando preset {safe_name}: {e}")
            return None
    def delete_preset(self, name):
        if name in self.DEFAULT_PRESETS:
            return False                                  
        file_path = os.path.join(self.presets_dir, f"{name}.aiikoeq")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                import logging
                logging.error(f"Error eliminando preset {name}: {e}")
                return False
        if name in self.PRESETS:
            del self.PRESETS[name]
        if self.current_preset == name:
            self.current_preset = "Custom"
            settings.set("eq_preset", "Custom")
        return True
    def set_enabled(self, enabled):
        self.is_enabled = enabled
        settings.set("eq_enabled", enabled)
        self.apply_current_state()
        if hasattr(self.main_window, 'playback_ui_controller'):
            self.main_window.playback_ui_controller._update_eq_icons()
    def set_preamp(self, gain):
        self.current_preamp = gain
        settings.set("eq_preamp", gain)
        if self.is_enabled:
            self.audio_engine.set_eq_preamp(gain)
    def set_band(self, index, gain):
        if 0 <= index < 10:
            self.current_bands[index] = gain
            self.current_preset = "Custom"
            settings.set("eq_bands", self.current_bands)
            settings.set("eq_preset", "Custom")
            if self.is_enabled:
                self.audio_engine.set_eq_band(index, gain)
    def load_preset(self, preset_name):
        if preset_name in self.PRESETS:
            self.current_preset = preset_name
            bands, preamp = self.PRESETS[preset_name]
            self.current_bands = bands.copy()
            self.current_preamp = preamp
            settings.set("eq_preset", preset_name)
            settings.set("eq_bands", self.current_bands)
            settings.set("eq_preamp", self.current_preamp)
            self.apply_current_state()
            self.profile_loaded.emit(self.current_bands, self.current_preamp)
    def apply_current_state(self):
        for i in range(10):
            gain = self.current_bands[i] if self.is_enabled else 0.0
            self.audio_engine.set_eq_band(i, gain)
        preamp_gain = self.current_preamp if self.is_enabled else 0.0
        self.audio_engine.set_eq_preamp(preamp_gain)