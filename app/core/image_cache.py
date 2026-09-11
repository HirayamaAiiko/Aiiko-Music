import os
import weakref
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QTimer
from qfluentwidgets import FluentIcon as FIF
class ImageCache(QObject):
    cache_updated = pyqtSignal()
    def __init__(self, image_loader=None):
        super().__init__()
        self.pixmap_cache = {}
        self.pending_icons = {}
        self.pending_labels = {}
        self.image_loader = image_loader
        self.fade_starts = {}
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self._on_fade_tick)
        self.fade_timer.setInterval(32)
        if self.image_loader:
            self.image_loader.image_ready.connect(self.on_image_loaded_async)
    def on_image_loaded_async(self, filepath, size, radius, qimage):
        pixmap = QPixmap.fromImage(qimage)
        self.pixmap_cache[f"pix_{filepath}_{size}_{radius}"] = pixmap
        icon = QIcon(pixmap)
        self.pixmap_cache[f"icon_{filepath}_{size}_{radius}"] = icon
        import time
        self.fade_starts[filepath] = time.time()
        if not self.fade_timer.isActive():
            self.fade_timer.start()
        self.cache_updated.emit()
        if filepath in self.pending_icons:
            valid_items = []
            for pending_tuple in self.pending_icons[filepath]:
                try:
                    item_ref = pending_tuple[0]
                    item = item_ref()
                    if item is None: continue
                    item_size = pending_tuple[1]
                    item_radius = pending_tuple[2] if len(pending_tuple) > 2 else 8
                    if hasattr(item, 'listWidget') and item.listWidget() is not None: 
                        if item_size == size and item_radius == radius: item.setIcon(icon)
                        else: valid_items.append(pending_tuple)
                except Exception: pass 
            if valid_items: self.pending_icons[filepath] = valid_items
            else: del self.pending_icons[filepath]
        if filepath in self.pending_labels:
            valid_labels = []
            for label_tuple in self.pending_labels[filepath]:
                try:
                    label_ref = label_tuple[0]
                    label = label_ref()
                    if label is None: continue
                    _ = label.objectName()                  
                    label_size = label_tuple[1]
                    label_radius = label_tuple[2]
                    if label_size == size and label_radius == radius:
                        label.setPixmap(pixmap)
                    else:
                        valid_labels.append(label_tuple)
                except Exception: pass
            if valid_labels: self.pending_labels[filepath] = valid_labels
            else: del self.pending_labels[filepath]
    def _on_fade_tick(self):
        import time
        now = time.time()
        active_fades = False
        for k, start_t in list(self.fade_starts.items()):
            if now - start_t >= 0.3:
                del self.fade_starts[k]
            else:
                active_fades = True
        self.cache_updated.emit()
        if not active_fades:
            self.fade_timer.stop()
    def get_image_opacity(self, filepath, duration=0.3):
        if not filepath or filepath not in self.fade_starts:
            return 1.0
        import time
        elapsed = time.time() - self.fade_starts[filepath]
        if elapsed >= duration:
            del self.fade_starts[filepath]
            return 1.0
        return elapsed / duration
    def clear(self):
        self.pixmap_cache.clear()
        self.pending_icons.clear()
        self.pending_labels.clear()
        if hasattr(self, 'image_loader') and self.image_loader and hasattr(self.image_loader, 'seen'):
            self.image_loader.seen.clear()
    def get_cached_pixmap(self, path, size, radius=12, fallback_icon=None):
        from settings_manager import settings
        if settings.get('square_covers', False) and radius < 80:
            radius = 0
        max_cache_size = settings.get('advanced_image_cache_size', 200)
        if len(self.pixmap_cache) > max_cache_size:
            keys_to_remove = []
            remove_count = max(50, max_cache_size // 4)
            for k in list(self.pixmap_cache.keys()):
                if not k.startswith("fb_"): 
                    keys_to_remove.append(k)
                    if len(keys_to_remove) >= remove_count: break
            for k in keys_to_remove:
                del self.pixmap_cache[k]
                if k.startswith("pix_"):
                    task_id = k[4:] 
                    if hasattr(self, 'image_loader') and self.image_loader and task_id in self.image_loader.seen:
                        try: self.image_loader.seen.remove(task_id)
                        except Exception: pass
        if fallback_icon is None: fallback_icon = FIF.MUSIC
        key = f"pix_{path}_{size}_{radius}"
        if key in self.pixmap_cache:
            val = self.pixmap_cache.pop(key)
            self.pixmap_cache[key] = val
            return val
        fb_key = f"fb_pix_{size}_{radius}_{fallback_icon.name}" 
        if fb_key not in self.pixmap_cache:
            fb = QPixmap(size, size)
            fb.fill(Qt.GlobalColor.transparent)
            painter = QPainter(fb)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            path_obj = QPainterPath()
            path_obj.addRoundedRect(0, 0, size, size, radius, radius)
            painter.setClipPath(path_obj)
            painter.fillRect(0, 0, size, size, QColor(0, 0, 0, 0))
            icon_size = int(size * 0.4) 
            from PyQt6.QtSvg import QSvgRenderer
            if fallback_icon == FIF.MUSIC:
                svg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "filetypes", "default_cover.svg")
                if os.path.exists(svg_path):
                    renderer = QSvgRenderer(svg_path)
                    renderer.render(painter)
                else:
                    icon_pixmap = fallback_icon.icon().pixmap(icon_size, icon_size)
                    x = (size - icon_pixmap.width()) // 2
                    y = (size - icon_pixmap.height()) // 2
                    painter.drawPixmap(x, y, icon_pixmap)
            elif fallback_icon == FIF.ALBUM:
                svg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "filetypes", "default_album_cover.svg")
                if os.path.exists(svg_path):
                    renderer = QSvgRenderer(svg_path)
                    renderer.render(painter)
                else:
                    icon_pixmap = fallback_icon.icon().pixmap(icon_size, icon_size)
                    x = (size - icon_pixmap.width()) // 2
                    y = (size - icon_pixmap.height()) // 2
                    painter.drawPixmap(x, y, icon_pixmap)
            elif fallback_icon == FIF.PEOPLE:
                svg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "filetypes", "default_artist_cover.svg")
                if os.path.exists(svg_path):
                    renderer = QSvgRenderer(svg_path)
                    renderer.render(painter)
                else:
                    icon_pixmap = fallback_icon.icon().pixmap(icon_size, icon_size)
                    x = (size - icon_pixmap.width()) // 2
                    y = (size - icon_pixmap.height()) // 2
                    painter.drawPixmap(x, y, icon_pixmap)
            else:
                icon_pixmap = fallback_icon.icon().pixmap(icon_size, icon_size)
                x = (size - icon_pixmap.width()) // 2
                y = (size - icon_pixmap.height()) // 2
                painter.drawPixmap(x, y, icon_pixmap)
            painter.end()
            self.pixmap_cache[fb_key] = fb
        if not path: return self.pixmap_cache[fb_key]
        if self.image_loader:
            self.image_loader.add_task(path, size, radius)
        return self.pixmap_cache[fb_key]
    def get_cached_icon(self, track, size, radius=8, fallback_icon=None):
        from settings_manager import settings
        if settings.get('square_covers', False) and radius < 80:
            radius = 0
        if fallback_icon is None: fallback_icon = FIF.MUSIC
        key = f"icon_{track.cover_path}_{size}_{radius}"
        if key in self.pixmap_cache:
            val = self.pixmap_cache.pop(key)
            self.pixmap_cache[key] = val
            pix_key = key.replace("icon_", "pix_", 1)
            if pix_key in self.pixmap_cache:
                self.pixmap_cache[pix_key] = self.pixmap_cache.pop(pix_key)
            return val
        pixmap = self.get_cached_pixmap(track.cover_path, size, radius, fallback_icon)
        fb_key = f"fb_icon_{size}_{radius}_{fallback_icon.name}"
        if fb_key not in self.pixmap_cache:
            self.pixmap_cache[fb_key] = QIcon(self.get_cached_pixmap(None, size, radius, fallback_icon))
        if not hasattr(track, 'cover_path') or not track.cover_path: return self.pixmap_cache[fb_key]
        return self.pixmap_cache[fb_key]
    def assign_async_icon(self, item, track, size, radius=8):
        from settings_manager import settings
        if settings.get('square_covers', False) and radius < 80:
            radius = 0
        key = f"icon_{track.cover_path}_{size}_{radius}"
        is_loaded = hasattr(track, 'cover_path') and track.cover_path and key in self.pixmap_cache
        item.setIcon(self.get_cached_icon(track, size, radius=radius))
        if not is_loaded and hasattr(track, 'cover_path') and track.cover_path:
            if track.cover_path not in self.pending_icons:
                self.pending_icons[track.cover_path] = []
            for pending_item in self.pending_icons[track.cover_path]:
                if pending_item[0]() is item:
                    return
            self.pending_icons[track.cover_path].append((weakref.ref(item), size, radius))
    def assign_async_pixmap(self, label, track, size, radius=12, fallback_icon=None):
        from settings_manager import settings
        if settings.get('square_covers', False) and radius < 80:
            radius = 0
        key = f"pix_{track.cover_path}_{size}_{radius}"
        is_loaded = hasattr(track, 'cover_path') and track.cover_path and key in self.pixmap_cache
        label_pixmap = getattr(label, '_pixmap', None)
        if label_pixmap is None and hasattr(label, 'pixmap') and callable(label.pixmap):
            label_pixmap = label.pixmap()
        if is_loaded or label_pixmap is None or label_pixmap.isNull():
            label.setPixmap(self.get_cached_pixmap(track.cover_path, size, radius, fallback_icon))
        else:
            if hasattr(track, 'cover_path') and track.cover_path:
                self.get_cached_pixmap(track.cover_path, size, radius, fallback_icon)
            else:
                label.setPixmap(self.get_cached_pixmap(None, size, radius, fallback_icon))
        if not is_loaded and hasattr(track, 'cover_path') and track.cover_path:
            if track.cover_path not in self.pending_labels:
                self.pending_labels[track.cover_path] = []
            for pending_label in self.pending_labels[track.cover_path]:
                if pending_label[0]() is label:
                    return
            self.pending_labels[track.cover_path].append((weakref.ref(label), size, radius))
