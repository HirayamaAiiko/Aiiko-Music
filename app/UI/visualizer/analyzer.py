import numpy as np
class SpectrumAnalyzer:
    def __init__(self, sample_rate=44100, num_bins=4096, num_bands=64):
        self.sample_rate = sample_rate
        self.num_bins = num_bins
        self.num_bands = num_bands
        self.min_freq = 40.0
        self.max_freq = 16000.0
        self.current_dist_mode = -1
        self.update_distribution()
    def update_distribution(self):
        from .config import VISUALIZER_CONFIG
        self.current_dist_mode = int(VISUALIZER_CONFIG.get('freq_distribution_mode', 0))
        min_freq = self.min_freq
        max_freq = self.max_freq
        mode = self.current_dist_mode
        if mode == 1:
            freqs = np.linspace(min_freq, max_freq, self.num_bands + 1)
        elif mode == 2:
            def freq_to_mel(f): return 2595.0 * np.log10(1.0 + f / 700.0)
            def mel_to_freq(m): return 700.0 * (10**(m / 2595.0) - 1.0)
            m_min, m_max = freq_to_mel(min_freq), freq_to_mel(max_freq)
            m_points = np.linspace(m_min, m_max, self.num_bands + 1)
            freqs = mel_to_freq(m_points)
        elif mode == 3:
            indices = np.linspace(0.0, 1.0, self.num_bands + 1) ** 1.6
            freqs = 10 ** (np.log10(min_freq) + indices * (np.log10(max_freq) - np.log10(min_freq)))
        else:
            freqs = np.logspace(np.log10(min_freq), np.log10(max_freq), self.num_bands + 1)
        nyquist = self.sample_rate / 2.0
        df = nyquist / self.num_bins
        self.band_indices = []
        new_limits = []
        for i in range(self.num_bands):
            start_bin = int(freqs[i] / df)
            end_bin = int(freqs[i+1] / df)
            start_bin = max(1, start_bin)
            end_bin = max(start_bin + 1, min(end_bin, self.num_bins))
            self.band_indices.append((start_bin, end_bin))
            new_limits.append((start_bin, end_bin))
        self.band_limits = new_limits
    def process(self, fft_data):
        from .config import VISUALIZER_CONFIG
        if getattr(self, 'current_dist_mode', -1) != VISUALIZER_CONFIG.get('freq_distribution_mode', 0):
            self.update_distribution()
        if fft_data is None or len(fft_data) < self.num_bins:
            return np.zeros(self.num_bands)
        magnitudes = np.array(fft_data[:self.num_bins])
        bands = np.zeros(self.num_bands)
        for i, (start, end) in enumerate(self.band_indices):
            if start < end:
                bands[i] = np.mean(magnitudes[start:end])
        return bands