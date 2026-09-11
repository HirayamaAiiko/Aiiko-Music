import os
import uuid
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage
class ImageCacheTask(QThread):
    finished_processing = pyqtSignal(str, str, str)                               
    def __init__(self, item_key: str, source_path: str, cache_dir: str, old_cache_path: str = None, max_size: int = 800, parent=None):
        super().__init__(parent)
        self.item_key = item_key
        self.source_path = source_path
        self.cache_dir = cache_dir
        self.old_cache_path = old_cache_path
        self.max_size = max_size
        self.finished.connect(self.deleteLater)
    def run(self):
        new_dest_path = ""
        if self.old_cache_path and os.path.exists(self.old_cache_path) and self.cache_dir in self.old_cache_path:
            try:
                os.remove(self.old_cache_path)
            except Exception:
                pass
        if self.source_path and os.path.exists(self.source_path):
            os.makedirs(self.cache_dir, exist_ok=True)
            img = QImage(self.source_path)
            if not img.isNull():
                size = min(img.width(), img.height())
                x = (img.width() - size) // 2
                y = (img.height() - size) // 2
                cropped = img.copy(x, y, size, size)
                if size > self.max_size:
                    cropped = cropped.scaled(self.max_size, self.max_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                filename = f"{uuid.uuid4().hex}.jpg"
                new_dest_path = os.path.join(self.cache_dir, filename)
                cropped.save(new_dest_path, "JPEG", 90)
        self.finished_processing.emit(self.item_key, new_dest_path, self.old_cache_path or "")