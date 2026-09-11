import numpy as np
import time
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer, Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QBrush, QGradient
from .analyzer import SpectrumAnalyzer
from .engine import PropagationEngine
from .config import VISUALIZER_CONFIG
import theme_manager
class VisualizerWidget(QWidget):
    def __init__(self, audio_engine, num_bands=64, fps=60, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.audio_engine = audio_engine
        self.num_bands = num_bands
        self.analyzer = SpectrumAnalyzer(num_bands=num_bands)
        self.prop_engine = PropagationEngine(num_bands=num_bands)
        self.current_visual_data = np.zeros(num_bands)
        self._shared_grad_left = QLinearGradient(0.0, 0.0, 1.0, 0.0)
        self._shared_grad_left.setCoordinateMode(QGradient.CoordinateMode.ObjectBoundingMode)
        self._shared_grad_right = QLinearGradient(1.0, 0.0, 0.0, 0.0)
        self._shared_grad_right.setCoordinateMode(QGradient.CoordinateMode.ObjectBoundingMode)
        self.global_hue = 0.0
        self.last_update_time = time.time()
        self.expected_dt = 1.0 / fps
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self.update_visualization)
        self.fps_interval_high = 1000 // fps
        self.fps_interval_low = 1000 // 30                          
    def showEvent(self, event):
        super().showEvent(event)
        if not self.render_timer.isActive():
            self.render_timer.start(self.fps_interval_high)
        win = self.window()
        if win and not getattr(self, '_window_filter_installed', False):
            from PyQt6.QtCore import QEvent
            win.installEventFilter(self)
            self._window_filter_installed = True
    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj == self.window() and event.type() == QEvent.Type.WindowStateChange:
            if self.window().isMinimized():
                if self.render_timer.isActive():
                    self.render_timer.stop()
            else:
                if not self.render_timer.isActive():
                    self.render_timer.start(self.fps_interval_high)
        return super().eventFilter(obj, event)
    def hideEvent(self, event):
        super().hideEvent(event)
        if self.render_timer.isActive():
            self.render_timer.stop()
    def update_visualization(self):
        window = self.window()
        if window and (window.isMinimized() or window.isHidden()):
            return
        self.render_timer.setInterval(self.fps_interval_low)
        if window and window.isActiveWindow():
            self.render_timer.setInterval(self.fps_interval_high)
        if not self.audio_engine or not getattr(self.audio_engine, '_initialized', False) or not self.audio_engine.is_playing():
            target_bands = np.zeros(self.num_bands)
        else:
            fft_data = self.audio_engine.get_fft_data()
            target_bands = self.analyzer.process(fft_data)
        current_time = time.time()
        dt = current_time - getattr(self, 'last_update_time', current_time - self.expected_dt)
        self.last_update_time = current_time
        dt_multiplier = max(0.1, min(10.0, dt / self.expected_dt))                                                
        self.current_visual_data = self.prop_engine.update(target_bands, dt_multiplier)
        global_intensity = np.mean(self.current_visual_data) / 100.0
        hue_shift_speed = 0.0005 + (global_intensity ** 1.5) * 0.015
        self.global_hue = (self.global_hue + hue_shift_speed) % 1.0
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = float(self.height())
        w = float(self.width())
        if h == 0 or w == 0:
            return
        bar_height = 2.5
        total_bar_height = self.num_bands * bar_height
        spacing = (h - total_bar_height) / max(1.0, float(self.num_bands - 1))
        max_bar_width = w * VISUALIZER_CONFIG['max_bar_width_pct']
        bass_energy = sum(self.current_visual_data[0:5]) / 5.0
        bass_norm = min(100.0, max(0.0, bass_energy))
        global_ducking = 1.0 - ((bass_norm / 100.0) * VISUALIZER_CONFIG['ducking_strength'])
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(self.num_bands):
            freq_index = self.num_bands - 1 - i
            val = self.current_visual_data[freq_index]
            freq = 40.0 * ((16000.0 / 40.0) ** (freq_index / self.num_bands))
            current_max_width = max_bar_width
            start_f = VISUALIZER_CONFIG['taper_start_freq']
            if freq > start_f:
                taper_factor = max(VISUALIZER_CONFIG['taper_end_width_pct'], 1.0 - ((freq - start_f) / (16000.0 - start_f)))
                current_max_width = max_bar_width * taper_factor
            val_norm = min(100.0, max(0.0, val))
            visibility_curve = max(0.0, (val_norm - 1.0) / 99.0)
            bar_w = visibility_curve * current_max_width
            if freq_index < 5:
                bar_ducking = 1.0
            elif freq_index < 18:
                t = (freq_index - 5) / 13.0
                bar_ducking = 1.0 * (1.0 - t) + global_ducking * t
            else:
                bar_ducking = global_ducking
            bar_w = bar_w * bar_ducking
            y = i * (bar_height + spacing)
            vertical_hue_offset = (i / float(self.num_bands)) * 0.15
            current_hue = (self.global_hue + vertical_hue_offset) % 1.0
            intensity = max(0.0, min(1.0, val_norm / 100.0))
            dyn_lightness = 0.50 + (intensity * VISUALIZER_CONFIG['color_brightness_boost'])  
            dyn_alpha = 0.35 + (intensity * VISUALIZER_CONFIG['color_opacity_boost'])
            color_solid = QColor.fromHslF(current_hue, 0.95, dyn_lightness, dyn_alpha)
            color_transparent = QColor(color_solid)
            color_transparent.setAlpha(0)
            if bar_w > 0.1:
                corner_rad = (bar_w / 2.0) * VISUALIZER_CONFIG['corner_radius_pct']
                fade_start = max(0.0, (bar_w - 15.0) / bar_w)
                self._shared_grad_left.setStops([(0.0, color_solid), (fade_start, color_solid), (1.0, color_transparent)])
                painter.setBrush(QBrush(self._shared_grad_left))
                painter.drawRoundedRect(QRectF(0.0, y, bar_w, bar_height), corner_rad, corner_rad)
                self._shared_grad_right.setStops([(0.0, color_solid), (fade_start, color_solid), (1.0, color_transparent)])
                painter.setBrush(QBrush(self._shared_grad_right))
                painter.drawRoundedRect(QRectF(w - bar_w, y, bar_w, bar_height), corner_rad, corner_rad)
