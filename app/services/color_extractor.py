import os
import hashlib
import logging
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QRunnable
from PyQt6.QtGui import QImage, QColor, QImageReader
from PyQt6.QtCore import QSize
from config import CACHE_DIR
class ColorExtractorSignals(QObject):
    color_ready = pyqtSignal(QColor)
class ColorExtractorWorker(QRunnable):
    def __init__(self, img_source, fallback_color=QColor("#121212")):
        super().__init__()
        self.img_source = img_source
        self.fallback_color = fallback_color
        self.signals = ColorExtractorSignals()
    def run(self):
        try:
            img = QImage()
            is_valid = False
            if isinstance(self.img_source, QImage) and not self.img_source.isNull():
                img = self.img_source
                is_valid = True
            elif isinstance(self.img_source, str) and self.img_source:
                file_hash = hashlib.md5(self.img_source.encode('utf-8')).hexdigest()
                thumb_mini = os.path.join(CACHE_DIR, "thumbnails", f"{file_hash}_65.jpg")
                thumb_full = os.path.join(CACHE_DIR, "thumbnails", f"{file_hash}_450.jpg")
                target_path = None
                if os.path.exists(thumb_mini):
                    target_path = thumb_mini
                elif os.path.exists(thumb_full):
                    target_path = thumb_full
                elif self.img_source.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
                    target_path = self.img_source
                if target_path:
                    reader = QImageReader(target_path)
                    reader.setScaledSize(QSize(64, 64))
                    img = reader.read()
                    if not img.isNull():
                        is_valid = True
            if is_valid:
                scaled = img.scaled(1, 1, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                avg_color = scaled.pixelColor(0, 0)
                try:
                    self.signals.color_ready.emit(avg_color)
                except RuntimeError:
                    pass                                                                              
                return
        except Exception as e:
            logging.debug(f"Error asíncrono extrayendo color: {e}")
        try:
            self.signals.color_ready.emit(self.fallback_color)
        except RuntimeError:
            pass