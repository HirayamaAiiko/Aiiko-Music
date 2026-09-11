import os
import logging
import hashlib
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QRunnable, QThreadPool
from PyQt6.QtGui import QImage, QColor
from config import CACHE_DIR
from settings_manager import settings
from core.language_manager import tr
class PlaybackUIController:
    def __init__(self, main_window):
        self.main_window = main_window
    def update_metadata_ui(self, track):
        mw = self.main_window
        artist_display = tr("Artista Desconocido") if not track.artist or track.artist in ("Artista Desconocido", "Desconocido") else track.artist
        album_display = tr("Álbum Desconocido") if not track.album or track.album in ("Álbum Desconocido", "Desconocido") else track.album
        mw.mini_title.setText(track.title or tr("Desconocido"))
        mw.mini_artist.setText(artist_display)
        if hasattr(mw, 'mini_album'):
            mw.mini_album.setText(album_display if track.album and track.album not in ("Desconocido", "Álbum Desconocido") else "")
        mw.full_title.setText(track.title or tr("Desconocido"))
        self.refresh_full_artist_html(track)
        if hasattr(mw, 'lbl_file_type'):
            mw.lbl_file_type.setText(track.file_type)
            mw.lbl_file_type.show()
            bitrate_kbps = track.bitrate // 1000 if track.bitrate else 0
            if bitrate_kbps > 0:
                mw.lbl_bitrate.setText(f"{bitrate_kbps} kbps")
                mw.lbl_bitrate.show()
            else:
                mw.lbl_bitrate.hide()
            sample_hz = track.sample_rate
            if sample_hz > 0:
                if sample_hz >= 1000:
                    mw.lbl_samplerate.setText(f"{sample_hz/1000:.1f} kHz")
                else:
                    mw.lbl_samplerate.setText(f"{sample_hz} Hz")
                mw.lbl_samplerate.show()
            else:
                mw.lbl_samplerate.hide()
            is_hq = False
            if track.file_type in ['FLAC', 'ALAC', 'WAV', 'DSD', 'DSF', 'OGG']:
                is_hq = True
            elif bitrate_kbps >= 320 or sample_hz >= 48000:
                is_hq = True
            mw.lbl_hq.setVisible(is_hq)
        if hasattr(mw, 'pinned_track_widget'):
            mw.pinned_track_widget.update_track(track, None, mw.audio_engine.is_playing() if hasattr(mw, 'audio_engine') else False)
        if getattr(mw, 'system_manager', None) and getattr(mw.system_manager, 'floating_player', None) and mw.system_manager.floating_player.isVisible():
            mw.system_manager.floating_player.update_track(track)
        if hasattr(mw, 'fullscreen_view') and mw.fullscreen_view.isVisible():
            mw.fullscreen_view.update_metadata(track, None, mw.audio_engine.is_playing())
        from PyQt6.QtCore import QTimer
        if hasattr(self, '_heavy_ui_timer'):
            self._heavy_ui_timer.stop()
            self._heavy_ui_timer.deleteLater()
        self._heavy_ui_timer = QTimer(self.main_window)
        self._heavy_ui_timer.setSingleShot(True)
        self._heavy_ui_timer.timeout.connect(lambda t=track: self._execute_heavy_metadata_ui(t))
        self._heavy_ui_timer.start(150)
    def _execute_heavy_metadata_ui(self, track):
        mw = self.main_window
        mw.image_cache.assign_async_pixmap(mw.mini_cover, track, 65, 8)
        mw.image_cache.assign_async_pixmap(mw.full_cover, track, 450, 20)
        if hasattr(mw, 'pinned_track_widget'):
            mw.image_cache.assign_async_pixmap(mw.pinned_track_widget.cover_label, track, 40, 6)
        if hasattr(mw, 'fullscreen_view') and mw.fullscreen_view.isVisible():
            cover_pixmap = None
            if track.cover_path:
                cached = mw.image_cache.get_cached_pixmap(track.cover_path, 450, 20)
                if cached and not cached.isNull():
                    cover_pixmap = cached
            mw.fullscreen_view.update_metadata(track, cover_pixmap, mw.audio_engine.is_playing())
            mw.image_cache.assign_async_pixmap(mw.fullscreen_view.cover, track, 450, 20)
        self.update_now_playing_bg(track)
    def refresh_full_artist_html(self, track=None):
        mw = self.main_window
        if not track:
            if hasattr(mw, 'queue') and mw.queue.tracks and 0 <= mw.queue.current_index < len(mw.queue.tracks):
                track = mw.queue.tracks[mw.queue.current_index]
            else:
                return
        artist_display = tr("Artista Desconocido") if not track.artist or track.artist in ("Artista Desconocido", "Desconocido") else track.artist
        album_display = tr("Álbum Desconocido") if not track.album or track.album in ("Álbum Desconocido", "Desconocido") else track.album
        accent = mw.ACCENT_COLORS.get(settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954')
        artist_album_html = f'<a href="artist" style="color:{accent}; text-decoration:none;">{artist_display}</a> • <a href="album" style="color:{accent}; text-decoration:none;">{album_display}</a>'
        if hasattr(mw, 'full_artist'):
            mw.full_artist.setText(artist_album_html)
    def _get_accent_gradient_style(self):
        accent_hex = self.main_window.ACCENT_COLORS.get(
            settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954'
        )
        accent = QColor(accent_hex)
        dark_accent = QColor.fromHslF(
            accent.hslHueF(),
            max(0.3, accent.hslSaturationF() * 0.6),
            0.08
        )
        mid_accent = QColor.fromHslF(
            accent.hslHueF(),
            max(0.2, accent.hslSaturationF() * 0.4),
            0.06
        )
        return f"""
            QWidget#NowPlayingPage {{ 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 {dark_accent.name()}, stop:0.6 {mid_accent.name()}, stop:1 #121212); 
            }}
        """
    def update_now_playing_bg(self, track):
        mw = self.main_window
        mw.page_now_playing.setObjectName("NowPlayingPage")
        mw.page_now_playing.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        fallback = self._get_accent_gradient_style()
        if not settings.get('dynamic_bg'):
            mw.page_now_playing.setStyleSheet(fallback)
            return
        img_source = track.cover_path
        if img_source:
            file_hash = hashlib.md5(img_source.encode('utf-8')).hexdigest()
            thumb_mini = os.path.join(CACHE_DIR, "thumbnails", f"{file_hash}_65.jpg")
            thumb_full = os.path.join(CACHE_DIR, "thumbnails", f"{file_hash}_450.jpg")
            if os.path.exists(thumb_mini):
                img_source = thumb_mini
            elif os.path.exists(thumb_full):
                img_source = thumb_full
            elif not img_source.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
                img_source = None
        if not img_source:
            mw.page_now_playing.setStyleSheet(fallback)
            return
        from services.color_extractor import ColorExtractorWorker
        worker = ColorExtractorWorker(img_source)
        worker.signals.color_ready.connect(self._apply_now_playing_bg_style)
        QThreadPool.globalInstance().start(worker)
    def _apply_now_playing_bg_style(self, color):
        if hasattr(self.main_window, 'page_now_playing'):
            if color == QColor("#121212") or not color.isValid():
                style = self._get_accent_gradient_style()
            else:
                top_color = color.darker(180).name()
                bottom_color = "#121212"
                style = f"""
                QWidget#NowPlayingPage {{ 
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                stop:0 {top_color}, stop:1 {bottom_color}); 
                }}
                """
            self.main_window.page_now_playing.setStyleSheet(style)
    def format_time(self, ms):
        if ms < 0: return "0:00"
        ms = int(ms)
        s = ms // 1000
        m = s // 60
        return f"{m}:{s%60:02d}"
    def _create_tinted_icon(self, filepath, color_hex):
        from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor
        pixmap = QPixmap(filepath)
        if pixmap.isNull(): return QIcon()
        tinted = QPixmap(pixmap.size())
        tinted.fill(Qt.GlobalColor.transparent)
        painter = QPainter(tinted)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), QColor(color_hex))
        painter.end()
        return QIcon(tinted)
    def _get_icon(self, filename, fallback_icon, color_hex='#FFFFFF'):
        cache_key = f"{filename}_{color_hex}"
        if not hasattr(self, '_icon_cache'):
            self._icon_cache = {}
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        from PyQt6.QtGui import QColor
        from config import RESOURCES_DIR
        import os
        path = os.path.join(RESOURCES_DIR, "buttons", filename)
        if os.path.exists(path): 
            icon = self._create_tinted_icon(path, color_hex)
        else:
            icon = fallback_icon.icon(color=QColor(color_hex)) if hasattr(fallback_icon, 'icon') else fallback_icon
        self._icon_cache[cache_key] = icon
        return icon
    def update_tool_btn_state(self, btn, icon_filename, icon_enum, color_hex):
        btn.setIcon(self._get_icon(icon_filename, icon_enum, color_hex))
        if hasattr(btn, '_label'):
            lbl_color = color_hex if color_hex != '#FFFFFF' else '#A0A0A0'
            btn._label.setStyleSheet(f"color: {lbl_color}; font-size: 11px; font-weight: 500;")
    def _update_shuffle_icon(self):
        from config import ICON_SHUFFLE
        mw = self.main_window
        accent = mw.ACCENT_COLORS.get(settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954')
        color = accent if mw.queue.is_shuffled else '#FFFFFF'
        mw.btn_mini_shuffle.setIcon(self._get_icon("shuffle.svg", ICON_SHUFFLE, color))
        if hasattr(mw, 'fullscreen_view') and mw.fullscreen_view.isVisible():
            mw.fullscreen_view._sync_shuffle_icon()
    def _update_play_icon(self, is_playing=False):
        from config import ICON_PLAY, ICON_PAUSE
        mw = self.main_window
        if hasattr(mw.btn_mini_play, 'is_playing'):
            mw.btn_mini_play.is_playing = is_playing
        if is_playing:
            mw.btn_mini_play.setIcon(self._get_icon("pause.svg", ICON_PAUSE, '#FFFFFF'))
        else:
            mw.btn_mini_play.setIcon(self._get_icon("play.svg", ICON_PLAY, '#FFFFFF'))
        mw.system_manager.update_floating_play_state(is_playing)
        if hasattr(mw, 'fullscreen_view') and mw.fullscreen_view.isVisible():
            mw.fullscreen_view.update_play_state(is_playing)
        if hasattr(mw, 'pinned_track_widget'):
            mw.pinned_track_widget.update_play_state(is_playing)
    def _update_repeat_icon(self):
        from config import ICON_REPEAT
        mw = self.main_window
        accent = mw.ACCENT_COLORS.get(settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954')
        if mw.queue.repeat_mode == 0: mw.btn_mini_repeat.setIcon(self._get_icon("repeat_off.svg", ICON_REPEAT, '#FFFFFF'))
        elif mw.queue.repeat_mode == 1: mw.btn_mini_repeat.setIcon(self._get_icon("repeat.svg", ICON_REPEAT, accent))
        else: mw.btn_mini_repeat.setIcon(self._get_icon("repeat1.svg", ICON_REPEAT, '#FFB900'))
        if hasattr(mw, 'fullscreen_view') and mw.fullscreen_view.isVisible():
            mw.fullscreen_view._sync_repeat_icon()
    def _update_eq_icons(self):
        from qfluentwidgets import FluentIcon as FIF
        mw = self.main_window
        accent = mw.ACCENT_COLORS.get(settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954')
        is_enabled = getattr(mw.eq_controller, 'is_enabled', False) if hasattr(mw, 'eq_controller') else False
        color = accent if is_enabled else '#FFFFFF'
        if hasattr(mw, 'btn_mini_eq'):
            mw.btn_mini_eq.setIcon(self._get_icon("equalizer.svg", FIF.MIX_VOLUMES, color))
    def _update_queue_icon(self):
        from qfluentwidgets import FluentIcon as FIF
        mw = self.main_window
        accent = mw.ACCENT_COLORS.get(settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954')
        is_open = getattr(mw, 'queue_is_open', False)
        color = accent if is_open else '#FFFFFF'
        if hasattr(mw, 'btn_mini_queue'):
            mw.btn_mini_queue.setIcon(self._get_icon("queue.svg", FIF.TILES, color))
    def update_favorite_icon_ui(self):
        from config import ICON_HEART
        mw = self.main_window
        if mw.queue.current_index >= 0 and mw.queue.tracks:
            track = mw.queue.tracks[mw.queue.current_index]
            favs = settings.get('favorites', [])
            accent = mw.ACCENT_COLORS.get(settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954')
            if track.filepath in favs: 
                icon = self._get_icon("heart_active.svg", ICON_HEART, accent)
            else: 
                icon = self._get_icon("heart.svg", ICON_HEART, '#FFFFFF')
            if hasattr(mw, 'btn_favorite_np'):
                mw.btn_favorite_np.setIcon(icon)
        mw = self.main_window
        if mw.queue.current_index >= 0 and mw.queue.tracks:
            track = mw.queue.tracks[mw.queue.current_index]
            favs = settings.get('favorites', [])
            accent = mw.ACCENT_COLORS.get(settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954')
            if track.filepath in favs: 
                icon = self._get_icon("heart_active.svg", ICON_HEART, accent)
            else: 
                icon = self._get_icon("heart.svg", ICON_HEART, '#FFFFFF')
            if hasattr(mw, 'btn_favorite_np'):
                mw.btn_favorite_np.setIcon(icon)
    def _update_fullscreen_icon(self):
        from qfluentwidgets import FluentIcon as FIF
        mw = self.main_window
        accent = mw.ACCENT_COLORS.get(settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954')
        is_fullscreen = hasattr(mw, 'fullscreen_view') and mw.fullscreen_view.isVisible()
        color = accent if is_fullscreen else '#FFFFFF'
        icon_name = "fullscreen.svg"
        if hasattr(mw, 'btn_fullscreen'):
            mw.btn_fullscreen.setIcon(self._get_icon(icon_name, FIF.FULL_SCREEN, color))