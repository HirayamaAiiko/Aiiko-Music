import os
import hashlib
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtCore import Qt
from config import CACHE_DIR
class FullScreenBackgroundMixin:
    def _init_background(self):
        self._current_bg_color = QColor("#0A0A0F")
        from PyQt6.QtCore import QVariantAnimation
        self.bg_anim = QVariantAnimation(self)
        self.bg_anim.setDuration(1500)                       
        self.bg_anim.valueChanged.connect(self._on_bg_anim_update)
    def _on_bg_anim_update(self, color):
        self._current_bg_color = color
        self.update()
    def update_dynamic_bg(self, pixmap):
        both_hidden = not getattr(self, '_cover_visible', True) and not getattr(self, '_lyrics_visible', False)
        if both_hidden:
            new_color = QColor("#1E3440")
            self.bg_anim.stop()
            self.bg_anim.setStartValue(self._current_bg_color)
            self.bg_anim.setEndValue(new_color)
            self.bg_anim.start()
            return
        img_source = getattr(self, '_current_track', None).cover_path if hasattr(self, '_current_track') else None
        if not img_source:
            self._apply_fullscreen_bg_color(QColor("#0A0A0F"))
            return
        from PyQt6.QtCore import QThreadPool
        from services.color_extractor import ColorExtractorWorker
        worker = ColorExtractorWorker(img_source, fallback_color=QColor("#0A0A0F"))
        worker.signals.color_ready.connect(self._apply_fullscreen_bg_color)
        QThreadPool.globalInstance().start(worker)
    def _apply_fullscreen_bg_color(self, avg_color):
        both_hidden = not getattr(self, '_cover_visible', True) and not getattr(self, '_lyrics_visible', False)
        if both_hidden:
            return                                       
        new_color = avg_color.darker(250) if avg_color != QColor("#0A0A0F") else QColor("#0A0A0F")
        self.bg_anim.stop()
        self.bg_anim.setStartValue(self._current_bg_color)
        self.bg_anim.setEndValue(new_color)
        self.bg_anim.start()