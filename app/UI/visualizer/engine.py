import numpy as np
from .config import VISUALIZER_CONFIG
class PropagationEngine:
    def __init__(self, num_bands=64):
        self.num_bands = num_bands
        self.current_values = np.zeros(num_bands)
        self.velocities = np.zeros(num_bands)
        self.attack_speed = 0.85                                        
        self.tension = 0.45                                            
        self.damping = 0.70                            
        self._cache_static_arrays()
    def _cache_static_arrays(self):
        xp = [0.0, 0.15, 0.35, 0.55, 0.75, 1.0]
        fp = [VISUALIZER_CONFIG['eq_sub_bass'], VISUALIZER_CONFIG['eq_bass'],  VISUALIZER_CONFIG['eq_low_mid'],  
              VISUALIZER_CONFIG['eq_mid'],  VISUALIZER_CONFIG['eq_high_mid'], VISUALIZER_CONFIG['eq_high']]
        x_eval = np.linspace(0.0, 1.0, self.num_bands)
        self.eq_curve = np.interp(x_eval, xp, fp)
        c_bass = VISUALIZER_CONFIG['bass_center_weight']
        s_bass = (1.0 - c_bass) / 2.0
        self.kernel_bass = np.array([s_bass, c_bass, s_bass])
        c_rest = VISUALIZER_CONFIG['rest_center_weight']
        s_rest = VISUALIZER_CONFIG['rest_side_weight']
        o_rest = max(0.0, (1.0 - c_rest - 2.0 * s_rest) / 2.0)
        self.kernel_rest = np.array([o_rest, s_rest, c_rest, s_rest, o_rest])
        trans_bar = int(VISUALIZER_CONFIG['bass_transition_bar'])
        self.blend = np.clip((np.arange(self.num_bands) - trans_bar) / float(trans_bar), 0.0, 1.0)
    def update(self, target_magnitudes, dt_multiplier=1.0):
        target = target_magnitudes * VISUALIZER_CONFIG['global_sensitivity'] 
        target = target * self.eq_curve
        target = np.clip(target, 0, 100)
        padded_bass = np.pad(target, (1, 1), mode='edge')
        target_bass = np.convolve(padded_bass, self.kernel_bass, mode='valid')
        padded_rest = np.pad(target, (2, 2), mode='edge')
        target_rest = np.convolve(padded_rest, self.kernel_rest, mode='valid')
        target = target_bass * (1.0 - self.blend) + target_rest * self.blend
        attack_speed = VISUALIZER_CONFIG['attack_speed']
        decay_speed = VISUALIZER_CONFIG['decay_speed']
        eff_attack = 1.0 - (1.0 - attack_speed) ** dt_multiplier
        eff_decay = 1.0 - (1.0 - decay_speed) ** dt_multiplier
        for i in range(self.num_bands):
            diff = target[i] - self.current_values[i]
            if diff > 0:
                self.current_values[i] += diff * eff_attack
            else:
                self.current_values[i] += diff * eff_decay
        self.current_values = np.clip(self.current_values, 0, 100)
        return self.current_values