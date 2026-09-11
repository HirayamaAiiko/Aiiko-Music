import math
from PyQt6.QtCore import Qt, QSize, QRect, QTime, QPointF
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PyQt6.QtGui import QColor, QPainter, QFont, QFontMetrics, QPainterPath, QLinearGradient, QPolygonF, QPen
from qfluentwidgets import FluentIcon as FIF
from config import ICON_HEART
from delegates.base_delegates import _get_accent_color
from core.language_manager import tr
class SongListDelegate(QStyledItemDelegate):
    def __init__(self, parent_view, player, is_album_view=False, is_artist_view=False, is_table_view=False, show_cover_in_table=False):
        super().__init__(parent_view)
        self.parent_view = parent_view
        self.player = player
        self.is_album_view = is_album_view
        self.is_artist_view = is_artist_view
        self.is_table_view = is_table_view
        self.show_cover_in_table = show_cover_in_table
        self.parent_view.setMouseTracking(True)
        self.last_heart_rects = {}
        self._font_title = None
        self._font_artist = None
        self._fm_title = None
        self._fm_artist = None
        self._cached_bg_alpha = 15
        self._cached_hover_alpha = 25
        self._cached_text_color = '#FFFFFF'
        self._cached_accent = QColor('#1DB954')
        self._cached_favs = set()
        self._last_cache_time = 0
        self._heart_icon_cache = {}
    def _update_cache(self):
        import time
        now = time.time()
        if now - self._last_cache_time < 1.0:                              
            return
        import theme_manager
        from settings_manager import settings
        theme_td = theme_manager.get_theme(settings.get('app_theme', 'Oscuro (Dark)'))
        self._cached_bg_alpha = 15 if theme_td.get('mode', 'dark') == 'dark' else 25
        self._cached_hover_alpha = 25 if theme_td.get('mode', 'dark') == 'dark' else 50
        self._cached_text_color = theme_td.get('text_color', '#FFFFFF')
        self._cached_accent = _get_accent_color()
        self._cached_favs = set(settings.get('favorites', []))
        self._last_cache_time = now
        tc = self._cached_text_color
        self._heart_icon_cache = {
            'active': self.player.playback_ui_controller._get_icon('heart_active.svg', ICON_HEART, '#FF5252'),
            'hover': self.player.playback_ui_controller._get_icon('heart.svg', ICON_HEART, '#FF5252'),
            'inactive': self.player.playback_ui_controller._get_icon('heart.svg', ICON_HEART, tc),
        }
    def sizeHint(self, option, index):
        return QSize(0, 50 if (self.is_table_view or self.is_artist_view or self.is_album_view) else 70)
    def paint(self, painter, option, index):
        track = index.data(Qt.ItemDataRole.UserRole)
        if not track: return
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        is_hovered = bool(opt.state & QStyle.StateFlag.State_MouseOver)
        is_selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        rect = opt.rect
        margin = 2
        bg_rect = rect.adjusted(5, margin, -5, -margin)
        self._update_cache()
        bg_alpha = self._cached_bg_alpha
        hover_alpha = self._cached_hover_alpha
        text_color = self._cached_text_color
        is_dragging = getattr(self.parent_view, 'is_dragging', False)
        dragged_indexes = getattr(self.parent_view, 'dragged_indexes', [])
        if is_dragging and index.row() not in dragged_indexes:
            painter.setOpacity(0.30)
        current_track = None
        if hasattr(self.player, 'queue'):
            q = self.player.queue
            if getattr(q, 'current_index', -1) >= 0 and getattr(q, 'tracks', []):
                try:
                    current_track = q.tracks[q.current_index]
                except IndexError:
                    pass
        is_playing = current_track is not None and hasattr(track, 'filepath') and hasattr(current_track, 'filepath') and track.filepath == current_track.filepath
        if is_selected:
            accent = self._cached_accent
            painter.setBrush(QColor(accent.red(), accent.green(), accent.blue(), 40))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(bg_rect, 8, 8)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            if is_hovered:
                painter.setBrush(QColor(150, 150, 150, hover_alpha))
                painter.drawRoundedRect(bg_rect, 8, 8)
            elif not self.is_album_view and not self.is_artist_view and not self.is_table_view and index.row() % 2 == 0:
                painter.setBrush(QColor(150, 150, 150, bg_alpha))
                painter.drawRoundedRect(bg_rect, 8, 8)
        if is_playing:
            painter.setBrush(self._cached_accent)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(bg_rect.x(), bg_rect.y() + 4, 3, bg_rect.height() - 8, 1, 1)
        if (self.is_album_view or self.is_artist_view or self.is_table_view) and not is_hovered and not is_selected:
            painter.setPen(QPen(QColor(150, 150, 150, 45), 1))
            painter.drawLine(rect.x() + 15, rect.bottom(), rect.right() - 15, rect.bottom())
        if not self._font_title:
            self._font_title = QFont(option.font)
            self._font_title.setPixelSize(15)
            self._font_title.setBold(True)
            self._fm_title = QFontMetrics(self._font_title)
            self._font_artist = QFont(option.font)
            self._font_artist.setPixelSize(13)
            self._fm_artist = QFontMetrics(self._font_artist)
        if self.is_album_view or self.is_table_view or self.is_artist_view:
            painter.setFont(self._font_artist)
            painter.setPen(QColor(136, 136, 136))
            col_num = 50 if self.is_table_view else 40
            num_rect = QRect(bg_rect.x(), bg_rect.y(), col_num, bg_rect.height())
            if is_playing:
                eq_x = bg_rect.x() + (col_num - 16) // 2
                eq_rect = QRect(eq_x, bg_rect.y() + (bg_rect.height() - 14) // 2, 16, 14)
                painter.setBrush(self._cached_accent)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(eq_rect.x(), eq_rect.bottom() - 8, 4, 8)
                painter.drawRect(eq_rect.x() + 6, eq_rect.bottom() - 14, 4, 14)
                painter.drawRect(eq_rect.x() + 12, eq_rect.bottom() - 6, 4, 6)
            else:
                painter.drawText(num_rect, Qt.AlignmentFlag.AlignCenter, str(index.row() + 1))
        if not self.is_album_view and (not self.is_table_view or self.show_cover_in_table):
            cover_size = 38 if (self.is_artist_view or self.is_table_view) else 56
            cover_x_offset = 50 if self.is_table_view else (40 if self.is_artist_view else 10)
            cover_rect = QRect(bg_rect.x() + cover_x_offset, bg_rect.y() + (bg_rect.height() - cover_size) // 2, cover_size, cover_size)
            icon = self.player.image_cache.get_cached_icon(track, 65, radius=4 if (self.is_artist_view or self.is_table_view) else 8, fallback_icon=FIF.MUSIC)
            if icon and not icon.isNull():
                pixmap = icon.pixmap(cover_size, cover_size)
                opacity = self.player.image_cache.get_image_opacity(track.cover_path) if hasattr(track, 'cover_path') else 1.0
                if opacity < 1.0: painter.setOpacity(opacity)
                painter.drawPixmap(cover_rect, pixmap)
                if opacity < 1.0: painter.setOpacity(1.0)
            text_x = cover_rect.right() + 7 if self.is_table_view else cover_rect.right() + 15
        else:
            text_x = bg_rect.x() + 50
        title_color = self._cached_accent if is_playing else QColor(text_color)
        if is_playing and not (self.is_album_view or self.is_table_view or self.is_artist_view):
            y_title_center = (bg_rect.height() - 34) // 2 + (20 - 14) // 2
            eq_rect = QRect(text_x, bg_rect.y() + y_title_center, 16, 14)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(title_color)
            painter.drawRect(eq_rect.x(), eq_rect.bottom() - 8, 4, 8)
            painter.drawRect(eq_rect.x() + 6, eq_rect.bottom() - 14, 4, 14)
            painter.drawRect(eq_rect.x() + 12, eq_rect.bottom() - 6, 4, 6)
            text_x += 22
        if self.is_table_view:
            cover_padding = 45 if self.show_cover_in_table else 0
            W = bg_rect.width() - 50 - cover_padding - 130                                                 
            if self.is_album_view:
                w_title = W
                w_artist = 0
                w_album = 0
            elif self.is_artist_view:
                w_title = W
                w_artist = 0
                w_album = 0
            else:
                w_title = int(W * 0.40)
                w_artist = int(W * 0.30)
                w_album = int(W * 0.30)
            painter.setFont(self._font_title)
            painter.setPen(title_color)
            avail_w = w_title - (text_x - (bg_rect.x() + 50 + cover_padding))
            if self.is_artist_view:
                y_offset = (bg_rect.height() - 34) // 2
                title_rect = QRect(text_x, bg_rect.y() + y_offset, avail_w, 18)
                disp_title = tr("Título Desconocido") if getattr(track, 'title', None) == "Título Desconocido" else track.title
                elided_title = self._fm_title.elidedText(disp_title, Qt.TextElideMode.ElideRight, title_rect.width() - 10)
                painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)
                painter.setFont(self._font_artist)
                painter.setPen(QColor(136, 136, 136))
                artist_rect = QRect(text_x, title_rect.bottom(), avail_w, 16)
                disp_artist = tr("Artista Desconocido") if getattr(track, 'artist', None) in ("Artista Desconocido", "Unknown Artist") else track.artist
                elided_artist = self._fm_artist.elidedText(disp_artist, Qt.TextElideMode.ElideRight, artist_rect.width() - 10)
                painter.drawText(artist_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_artist)
            else:
                title_rect = QRect(text_x, bg_rect.y(), avail_w, bg_rect.height())
                disp_title = tr("Título Desconocido") if getattr(track, 'title', None) == "Título Desconocido" else track.title
                elided_title = self._fm_title.elidedText(disp_title, Qt.TextElideMode.ElideRight, title_rect.width() - 10)
                painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)
            if w_artist > 0:
                painter.setFont(self._font_artist)
                painter.setPen(QColor(136, 136, 136))
                artist_rect = QRect(bg_rect.x() + 50 + cover_padding + w_title, bg_rect.y(), w_artist, bg_rect.height())
                disp_artist = tr("Artista Desconocido") if getattr(track, 'artist', None) in ("Artista Desconocido", "Unknown Artist") else track.artist
                elided_artist = self._fm_artist.elidedText(disp_artist, Qt.TextElideMode.ElideRight, artist_rect.width() - 10)
                painter.drawText(artist_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_artist)
            if w_album > 0:
                album_rect = QRect(artist_rect.right(), bg_rect.y(), w_album, bg_rect.height())
                disp_album = tr("Álbum Desconocido") if getattr(track, 'album', None) in ("Álbum Desconocido", "Unknown Album") else (track.album or tr("Álbum Desconocido"))
                elided_album = self._fm_artist.elidedText(disp_album, Qt.TextElideMode.ElideRight, album_rect.width() - 10)
                painter.drawText(album_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_album)
        else:
            painter.setFont(self._font_title)
            painter.setPen(title_color)
            y_offset = (bg_rect.height() - 34) // 2
            title_rect = QRect(text_x, bg_rect.y() + y_offset, bg_rect.width() - 200, 18)
            disp_title = tr("Título Desconocido") if getattr(track, 'title', None) == "Título Desconocido" else track.title
            elided_title = self._fm_title.elidedText(disp_title, Qt.TextElideMode.ElideRight, title_rect.width())
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)
            painter.setFont(self._font_artist)
            painter.setPen(QColor(136, 136, 136))
            artist_rect = QRect(text_x, title_rect.bottom(), bg_rect.width() - 200, 16)
            disp_artist = tr("Artista Desconocido") if getattr(track, 'artist', None) in ("Artista Desconocido", "Unknown Artist") else track.artist
            elided_artist = self._fm_artist.elidedText(disp_artist, Qt.TextElideMode.ElideRight, artist_rect.width())
            painter.drawText(artist_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_artist)
        dur_s = track.duration / 1000 if hasattr(track, 'duration') and track.duration else 0
        dur_str = QTime(0, 0, 0).addSecs(math.floor(dur_s)).toString("mm:ss")
        painter.setFont(self._font_artist)
        painter.setPen(QColor(136, 136, 136))
        dur_rect = QRect(bg_rect.right() - 130, bg_rect.y(), 50, bg_rect.height())
        painter.drawText(dur_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, dur_str)
        is_fav = track.filepath in self._cached_favs
        heart_rect = QRect(bg_rect.right() - 50, bg_rect.y() + (bg_rect.height() - 24) // 2, 24, 24)
        is_hovering_heart = getattr(self, f'_heart_hover_{index.row()}', False)
        if is_fav:
            h_icon = self._heart_icon_cache.get('active')
        elif is_hovering_heart:
            h_icon = self._heart_icon_cache.get('hover')
        else:
            h_icon = self._heart_icon_cache.get('inactive')
        if h_icon:
            painter.drawPixmap(heart_rect, h_icon.pixmap(24, 24))
        self.last_heart_rects[index.row()] = heart_rect
        painter.restore()
    def editorEvent(self, event, model, option, index):
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                heart_rect = self.last_heart_rects.get(index.row())
                if heart_rect and heart_rect.contains(event.pos()):
                    track = index.data(Qt.ItemDataRole.UserRole)
                    if track:
                        self.player.app_controller.toggle_favorite_track(track)
                        self._last_cache_time = 0                                    
                        self.parent_view.update(index)
                        return True
        elif event.type() == QEvent.Type.MouseMove:
            heart_rect = self.last_heart_rects.get(index.row())
            if heart_rect:
                is_currently_hovering = heart_rect.contains(event.pos())
                was_hovering = getattr(self, f'_heart_hover_{index.row()}', False)
                if is_currently_hovering != was_hovering:
                    setattr(self, f'_heart_hover_{index.row()}', is_currently_hovering)
                    self.parent_view.update(index)
        return super().editorEvent(event, model, option, index)
class QueueListDelegate(QStyledItemDelegate):
    def __init__(self, parent_view, player):
        super().__init__(parent_view)
        self.parent_view = parent_view
        self.player = player
        self._font_title = None
        self._font_artist = None
        self._is_dragging = False
        self._dragged_row = -1
    def sizeHint(self, option, index):
        return QSize(0, 60)
    def paint(self, painter, option, index):
        track = index.data(Qt.ItemDataRole.UserRole)
        if not track: return
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._is_dragging and index.row() != self._dragged_row:
            painter.setOpacity(0.30)
        is_hovered = bool(opt.state & QStyle.StateFlag.State_MouseOver)
        is_selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        is_playing = (index.row() == index.model().current_index)
        rect = opt.rect
        bg_rect = rect.adjusted(5, 2, -5, -2)
        if is_playing:
            painter.setBrush(QColor(150, 150, 150, 25))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(bg_rect, 6, 6)
            painter.setBrush(_get_accent_color())
            painter.drawRoundedRect(bg_rect.x(), bg_rect.y() + 4, 3, bg_rect.height() - 8, 1, 1)
        elif is_selected:
            accent = _get_accent_color()
            painter.setBrush(QColor(accent.red(), accent.green(), accent.blue(), 40))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(bg_rect, 6, 6)
        elif is_hovered:
            painter.setBrush(QColor(150, 150, 150, 25))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(bg_rect, 6, 6)
        cover_size = 40
        cover_rect = QRect(bg_rect.x() + 8, bg_rect.y() + (bg_rect.height() - cover_size) // 2, cover_size, cover_size)
        icon = self.player.image_cache.get_cached_icon(track, 65, radius=6, fallback_icon=FIF.MUSIC)
        if icon and not icon.isNull():
            opacity = self.player.image_cache.get_image_opacity(track.cover_path) if hasattr(track, 'cover_path') else 1.0
            if opacity < 1.0: painter.setOpacity(opacity)
            painter.drawPixmap(cover_rect, icon.pixmap(cover_size, cover_size))
            if opacity < 1.0: painter.setOpacity(1.0)
        if not self._font_title:
            self._font_title = QFont(option.font)
            self._font_title.setPixelSize(15)
            self._font_title.setBold(True)
            self._font_artist = QFont(option.font)
            self._font_artist.setPixelSize(13)
            self._fm_title_queue = QFontMetrics(self._font_title)
            self._fm_artist_queue = QFontMetrics(self._font_artist)
        text_x = cover_rect.right() + 12
        drag_handle_w = 24
        text_w = bg_rect.width() - (text_x - bg_rect.x()) - drag_handle_w - 12
        title_color = _get_accent_color() if is_playing else QColor('#FFFFFF')
        if is_playing:
            eq_rect = QRect(text_x, bg_rect.y() + 13, 16, 14)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(title_color)
            painter.drawRect(eq_rect.x(), eq_rect.bottom() - 8, 4, 8)
            painter.drawRect(eq_rect.x() + 6, eq_rect.bottom() - 14, 4, 14)
            painter.drawRect(eq_rect.x() + 12, eq_rect.bottom() - 6, 4, 6)
            text_x += 22
            text_w -= 22
        painter.setFont(self._font_title)
        painter.setPen(title_color)
        title_rect = QRect(text_x, bg_rect.y() + 10, text_w, 20)
        disp_title = tr("Título Desconocido") if getattr(track, 'title', None) == "Título Desconocido" else track.title
        elided_title = self._fm_title_queue.elidedText(disp_title, Qt.TextElideMode.ElideRight, text_w)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)
        painter.setFont(self._font_artist)
        painter.setPen(QColor('#A0A0A0'))
        artist_rect = QRect(text_x, title_rect.bottom() + 2, text_w, 18)
        disp_artist = tr("Artista Desconocido") if getattr(track, 'artist', None) in ("Artista Desconocido", "Unknown Artist") else track.artist
        elided_artist = self._fm_artist_queue.elidedText(disp_artist, Qt.TextElideMode.ElideRight, text_w)
        painter.drawText(artist_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_artist)
        handle_color = QColor(255, 255, 255, 80 if is_hovered else 40)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(handle_color)
        hx = bg_rect.right() - drag_handle_w
        hy = bg_rect.y() + (bg_rect.height() // 2) - 6
        for i in range(3):
            painter.drawRoundedRect(hx, hy + i * 5, 16, 2, 1, 1)
        painter.restore()
class AlbumListDelegate(QStyledItemDelegate):
    def __init__(self, parent_view=None):
        super().__init__(parent_view)
        self._font_title = None
        self._font_artist = None
    def sizeHint(self, option, index):
        if self.parent() and self.parent().gridSize().width() > 0:
            return QSize(self.parent().gridSize().width(), 50)
        return QSize(250, 50)
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        is_hovered = bool(opt.state & QStyle.StateFlag.State_MouseOver)
        is_selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        bg_rect = opt.rect.adjusted(5, 2, -5, -2)
        rect = opt.rect
        import theme_manager
        from settings_manager import settings
        theme_td = theme_manager.get_theme(settings.get('app_theme', 'Oscuro (Dark)'))
        text_color = theme_td.get('text_color', '#FFFFFF')
        if is_selected:
            accent = _get_accent_color()
            painter.setBrush(QColor(accent.red(), accent.green(), accent.blue(), 40))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(bg_rect, 8, 8)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            if is_hovered:
                alpha = 20 if theme_td.get('mode', 'dark') == 'dark' else 35
                painter.setBrush(QColor(150, 150, 150, alpha))
                painter.drawRoundedRect(bg_rect, 8, 8)
        painter.setPen(QPen(QColor(150, 150, 150, 45), 1))
        painter.drawLine(rect.x() + 15, rect.bottom(), rect.right() - 15, rect.bottom())
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        m = 5
        col_num = 50
        col_end = 0
        cover_padding = 45
        scroll_offset = 0
        if self.parent() and self.parent().verticalScrollBar().isVisible():
            scroll_offset = self.parent().verticalScrollBar().width()
        eff_w = self.parent().width() - 2 * m - scroll_offset if self.parent() else bg_rect.width()
        W = eff_w - col_num - cover_padding - col_end
        w_title = int(W * 0.40)
        w_artist = int(W * 0.30)
        w_year = int(W * 0.30)
        if not self._font_title:
            self._font_title = QFont(option.font)
            self._font_title.setPixelSize(15)
            self._font_title.setBold(True)
            self._font_artist = QFont(option.font)
            self._font_artist.setPixelSize(13)
        num_rect = QRect(bg_rect.x(), bg_rect.y(), col_num, bg_rect.height())
        painter.setFont(self._font_artist)
        painter.setPen(QColor(136, 136, 136))
        painter.drawText(num_rect, Qt.AlignmentFlag.AlignCenter, str(index.row() + 1))
        cover_x_offset = col_num
        cover_size = 38
        cover_rect = QRect(bg_rect.x() + cover_x_offset, bg_rect.y() + (bg_rect.height() - cover_size) // 2, cover_size, cover_size)
        if icon and not icon.isNull():
            painter.drawPixmap(cover_rect, icon.pixmap(cover_size, cover_size))
        x = bg_rect.x() + col_num + cover_padding
        y_offset = (bg_rect.height() - 18) // 2
        album_name = index.data(Qt.ItemDataRole.UserRole)
        track = index.data(Qt.ItemDataRole.UserRole + 1)
        artist_str = track.artist if track else "Desconocido"
        year_str = track.year if track and hasattr(track, 'year') else ""
        title_rect = QRect(x, bg_rect.y() + y_offset, w_title - 10, 18)
        painter.setFont(self._font_title)
        painter.setPen(QColor(text_color))
        fm_title = QFontMetrics(self._font_title)
        elided_title = fm_title.elidedText(album_name or tr("Álbum Desconocido"), Qt.TextElideMode.ElideRight, title_rect.width())
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)
        artist_rect = QRect(x + w_title, bg_rect.y() + y_offset, w_artist - 10, 18)
        painter.setFont(self._font_artist)
        painter.setPen(QColor(136, 136, 136))
        fm_artist = QFontMetrics(self._font_artist)
        elided_artist = fm_artist.elidedText(artist_str, Qt.TextElideMode.ElideRight, artist_rect.width())
        painter.drawText(artist_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_artist)
        year_rect = QRect(x + w_title + w_artist, bg_rect.y() + y_offset, w_year - 10, 18)
        elided_year = fm_artist.elidedText(str(year_str), Qt.TextElideMode.ElideRight, year_rect.width())
        painter.drawText(year_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_year)
        painter.restore()
class ArtistListDelegate(QStyledItemDelegate):
    def __init__(self, parent_view=None):
        super().__init__(parent_view)
        self._font_title = None
        self._font_artist = None
    def sizeHint(self, option, index):
        if self.parent() and self.parent().gridSize().width() > 0:
            return QSize(self.parent().gridSize().width(), 70)
        return QSize(250, 70)
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        is_hovered = bool(opt.state & QStyle.StateFlag.State_MouseOver)
        is_selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        bg_rect = opt.rect.adjusted(5, 2, -5, -2)
        import theme_manager
        from settings_manager import settings
        theme_td = theme_manager.get_theme(settings.get('app_theme', 'Oscuro (Dark)'))
        text_color = theme_td.get('text_color', '#FFFFFF')
        if is_selected:
            accent = _get_accent_color()
            painter.setBrush(QColor(accent.red(), accent.green(), accent.blue(), 40))
            painter.setPen(QPen(accent, 1))
            painter.drawRoundedRect(bg_rect, 8, 8)
        elif is_hovered:
            alpha = 15 if theme_td.get('mode', 'dark') == 'dark' else 25
            painter.setBrush(QColor(255, 255, 255, alpha))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(bg_rect, 8, 8)
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        cover_size = 50                                             
        cover_rect = QRect(bg_rect.x() + 20, bg_rect.y() + (bg_rect.height() - cover_size) // 2, cover_size, cover_size)
        if icon and not icon.isNull():
            painter.drawPixmap(cover_rect, icon.pixmap(cover_size, cover_size))
        artist_name = index.data(Qt.ItemDataRole.UserRole)
        if not self._font_title:
            self._font_title = QFont(option.font)
            self._font_title.setPixelSize(15)
            self._font_title.setBold(True)
        x = cover_rect.right() + 25
        y_offset = (bg_rect.height() - 18) // 2
        title_rect = QRect(x, bg_rect.y() + y_offset, bg_rect.width() - (x - bg_rect.x()) - 20, 18)
        painter.setFont(self._font_title)
        painter.setPen(QColor(text_color))
        fm_title = QFontMetrics(self._font_title)
        elided_title = fm_title.elidedText(artist_name or tr("Artista Desconocido"), Qt.TextElideMode.ElideRight, title_rect.width())
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)
        if not is_selected and not is_hovered:
            painter.setPen(QColor(255, 255, 255, 12))
            painter.drawLine(bg_rect.x() + 15, bg_rect.bottom(), bg_rect.right() - 15, bg_rect.bottom())
        painter.restore()