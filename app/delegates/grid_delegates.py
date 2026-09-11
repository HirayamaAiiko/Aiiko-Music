from PyQt6.QtCore import Qt, QAbstractListModel, QSortFilterProxyModel, QModelIndex, QRect, QSize, QTime, QTimer, pyqtSignal
from PyQt6.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem
from PyQt6.QtGui import QColor, QPen, QPainter, QFont, QFontMetrics
import math
import time
from qfluentwidgets import FluentIcon as FIF
from config import ICON_HEART
from core.language_manager import tr
from delegates.base_delegates import AnimatedGridDelegate, _get_accent_color
class CircularHoverDelegate(AnimatedGridDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._font_bold = None
    def sizeHint(self, option, index):
        return QSize(190, 265)
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        opacity = index.data(Qt.ItemDataRole.UserRole + 2)
        if opacity is not None and opacity < 1.0:
            painter.setOpacity(opacity)
        icon_size = 160
        icon_rect = QRect(opt.rect.x() + (opt.rect.width() - icon_size) // 2, opt.rect.y() + 10, icon_size, icon_size)
        hover_rect = QRect(opt.rect.x() + (opt.rect.width() - 170) // 2, opt.rect.y() + 5, 170, 250)
        is_hovered = self.check_hover_state(opt, index)
        if opt.state & QStyle.StateFlag.State_Selected or is_hovered:
            if opt.state & QStyle.StateFlag.State_Selected:
                accent = _get_accent_color()
                brush_color = QColor(accent.red(), accent.green(), accent.blue(), 40)
                painter.setBrush(brush_color)
                painter.setPen(QPen(accent, 2))
            else:
                painter.setBrush(QColor(255, 255, 255, 15)) 
                painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(hover_rect, 10, 10)
        opt.state &= ~QStyle.StateFlag.State_Selected
        opt.state &= ~QStyle.StateFlag.State_MouseOver
        opt.state &= ~QStyle.StateFlag.State_HasFocus
        opt.text = ""                                           
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if icon and not icon.isNull():
            painter.drawPixmap(icon_rect, icon.pixmap(icon_size, icon_size))
        if opacity is not None and opacity < 1.0:
            painter.setOpacity(1.0)
        artist_name = index.data(Qt.ItemDataRole.UserRole)
        if artist_name:
            if not self._font_bold:
                self._font_bold = QFont(option.font)
                self._font_bold.setBold(True)
                self._font_bold.setPixelSize(15)
            text_rect_y = opt.rect.y() + 10 + icon_size + 5                       
            title_rect = QRect(opt.rect.x() + 5, text_rect_y, opt.rect.width() - 10, 20)
            self.draw_marquee_text(painter, title_rect, artist_name, self._font_bold, QColor(255, 255, 255), is_hovered)
        painter.restore()
class AlbumGridDelegate(AnimatedGridDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._font_bold = None
        self._font_normal = None
    def sizeHint(self, option, index):
        return QSize(190, 265)
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        opacity = index.data(Qt.ItemDataRole.UserRole + 2)
        if opacity is not None and opacity < 1.0:
            painter.setOpacity(opacity)
        icon_size = 160
        icon_rect = QRect(opt.rect.x() + (opt.rect.width() - icon_size) // 2, opt.rect.y() + 10, icon_size, icon_size)
        hover_rect = QRect(opt.rect.x() + (opt.rect.width() - 170) // 2, opt.rect.y() + 5, 170, 250)
        is_hovered = self.check_hover_state(opt, index)
        if opt.state & QStyle.StateFlag.State_Selected or is_hovered:
            if opt.state & QStyle.StateFlag.State_Selected:
                accent = _get_accent_color()
                brush_color = QColor(accent.red(), accent.green(), accent.blue(), 40)
                painter.setBrush(brush_color)
                painter.setPen(QPen(accent, 2))
            else:
                painter.setBrush(QColor(255, 255, 255, 15)) 
                painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(hover_rect, 10, 10)
        opt.state &= ~QStyle.StateFlag.State_Selected
        opt.state &= ~QStyle.StateFlag.State_MouseOver
        opt.text = ""
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if icon and not icon.isNull():
            painter.drawPixmap(icon_rect, icon.pixmap(icon_size, icon_size))
        album_name = index.data(Qt.ItemDataRole.UserRole)
        track = index.data(Qt.ItemDataRole.UserRole + 1)
        if not album_name:
            painter.restore()
            return
        artist_str = track.artist if track else "Desconocido"
        text_rect_y = opt.rect.y() + 10 + icon_size + 5                                               
        if not self._font_bold:
            self._font_bold = QFont(option.font)
            self._font_bold.setBold(True)
            self._font_bold.setPixelSize(15)
            self._font_normal = QFont(option.font)
            self._font_normal.setPixelSize(13)
        title_rect = QRect(opt.rect.x() + 5, text_rect_y, opt.rect.width() - 10, 20)
        self.draw_marquee_text(painter, title_rect, album_name, self._font_bold, QColor(255, 255, 255), is_hovered)
        artist_rect = QRect(opt.rect.x() + 5, text_rect_y + 20, opt.rect.width() - 10, 20)
        self.draw_marquee_text(painter, artist_rect, artist_str, self._font_normal, QColor(180, 180, 180), is_hovered)
        if opacity is not None and opacity < 1.0:
            painter.setOpacity(1.0)
        painter.restore()
class SongGridDelegate(AnimatedGridDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._font_bold = None
        self._font_normal = None
    def sizeHint(self, option, index):
        return QSize(190, 265)
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        icon_size = 160
        opacity = index.data(Qt.ItemDataRole.UserRole + 2)
        if opacity is not None and opacity < 1.0:
            painter.setOpacity(opacity)
        icon_rect = QRect(opt.rect.x() + (opt.rect.width() - icon_size) // 2, opt.rect.y() + 10, icon_size, icon_size)
        hover_rect = QRect(opt.rect.x() + (opt.rect.width() - 170) // 2, opt.rect.y() + 5, 170, 250)
        is_hovered = self.check_hover_state(opt, index)
        if opt.state & QStyle.StateFlag.State_Selected or is_hovered:
            if opt.state & QStyle.StateFlag.State_Selected:
                accent = _get_accent_color()
                brush_color = QColor(accent.red(), accent.green(), accent.blue(), 40)
                painter.setBrush(brush_color)
                painter.setPen(QPen(accent, 2))
            else:
                painter.setBrush(QColor(255, 255, 255, 15)) 
                painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(hover_rect, 10, 10)
        opt.state &= ~QStyle.StateFlag.State_Selected
        opt.state &= ~QStyle.StateFlag.State_MouseOver
        opt.state &= ~QStyle.StateFlag.State_HasFocus
        opt.text = ""
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if icon and not icon.isNull():
            painter.drawPixmap(icon_rect, icon.pixmap(icon_size, icon_size))
        if opacity is not None and opacity < 1.0:
            painter.setOpacity(1.0)
        track = index.data(Qt.ItemDataRole.UserRole)
        if not track:
            painter.restore()
            return
        text_rect_y = opt.rect.y() + 10 + icon_size + 5                                               
        if not self._font_bold:
            self._font_bold = QFont(option.font)
            self._font_bold.setBold(True)
            self._font_bold.setPixelSize(15)
            self._font_normal = QFont(option.font)
            self._font_normal.setPixelSize(13)
        title_color = QColor(255, 255, 255)
        current_track = None
        if not hasattr(self, '_cached_player'):
            self._cached_player = None
            if self.parent_view and hasattr(self.parent_view, 'parent'):
                p = self.parent_view.parent()
                while p:
                    if hasattr(p, 'queue'):                                                              
                        self._cached_player = p
                        break
                    p = p.parent() if hasattr(p, 'parent') and callable(p.parent) else None
        if self._cached_player and hasattr(self._cached_player, 'queue'):
            q = self._cached_player.queue
            if q and getattr(q, 'current_index', -1) >= 0 and getattr(q, 'tracks', []):
                try:
                    current_track = q.tracks[q.current_index]
                except IndexError:
                    pass
        if current_track and hasattr(track, 'filepath') and hasattr(current_track, 'filepath') and track.filepath == current_track.filepath:
            title_color = _get_accent_color()
            if is_hovered or (opt.state & QStyle.StateFlag.State_Selected):
                pass                       
        title_rect = QRect(opt.rect.x() + 5, text_rect_y, opt.rect.width() - 10, 20)
        self.draw_marquee_text(painter, title_rect, track.title, self._font_bold, title_color, is_hovered)
        artist_rect = QRect(opt.rect.x() + 5, text_rect_y + 20, opt.rect.width() - 10, 20)
        self.draw_marquee_text(painter, artist_rect, track.artist, self._font_normal, QColor(180, 180, 180), is_hovered)
        painter.restore()
class PlaylistGridDelegate(AnimatedGridDelegate):
    CARD_SIZE = 160
    play_clicked = pyqtSignal(str)                                  
    def __init__(self, parent=None, player=None):
        super().__init__(parent)
        self.player = player
        self._font_bold = None
        self._font_normal = None
        self._btn_glow_intensities = {}
        if parent:
            parent.setMouseTracking(True)
    def _on_timer(self):
        super()._on_timer()
        needs_update = False
        if self.parent_view:
            model = self.parent_view.model()
            if model:
                for row in list(self._btn_glow_intensities.keys()):
                    target = 1.0 if getattr(self, f'_btn_hover_{row}', False) else 0.0
                    current = self._btn_glow_intensities.get(row, 0.0)
                    if current != target:
                        step = 0.15                                                
                        if target > current:
                            current = min(1.0, current + step)
                        else:
                            current = max(0.0, current - step)
                        self._btn_glow_intensities[row] = current
                        needs_update = True
                        idx = model.index(row, 0)
                        if idx.isValid():
                            self.parent_view.update(idx)
        if needs_update and not self.timer.isActive():
            self.timer.start()
    def sizeHint(self, option, index):
        return QSize(190, 265)
    def _get_play_btn_rect(self, option):
        card = self.CARD_SIZE
        icon_rect = QRect(
            option.rect.x() + (option.rect.width() - card) // 2,
            option.rect.y() + 10, card, card
        )
        btn_size = 48
        return QRect(
            icon_rect.x() + (icon_rect.width() - btn_size) // 2,
            icon_rect.y() + (icon_rect.height() - btn_size) // 2,
            btn_size, btn_size
        )
    def editorEvent(self, event, model, option, index):
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                pos = event.position().toPoint() if hasattr(event.position(), 'toPoint') else event.pos()
                btn_rect = self._get_play_btn_rect(option)
                if btn_rect.contains(pos):
                    data = index.data(Qt.ItemDataRole.UserRole)
                    if data:
                        self.play_clicked.emit(data.get('name', ''))
                        return True
        elif event.type() == QEvent.Type.MouseMove:
            pos = event.position().toPoint() if hasattr(event.position(), 'toPoint') else event.pos()
            btn_rect = self._get_play_btn_rect(option)
            is_currently_hovering_btn = btn_rect.contains(pos)
            was_hovering_btn = getattr(self, f'_btn_hover_{index.row()}', False)
            if is_currently_hovering_btn != was_hovering_btn:
                setattr(self, f'_btn_hover_{index.row()}', is_currently_hovering_btn)
                if index.row() not in self._btn_glow_intensities:
                    self._btn_glow_intensities[index.row()] = 0.0
                if not self.timer.isActive():
                    self.timer.start()
        return super().editorEvent(event, model, option, index)
    def paint(self, painter, option, index):
        import os
        from config import APP_ROOT
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        card = self.CARD_SIZE
        icon_rect = QRect(
            opt.rect.x() + (opt.rect.width() - card) // 2,
            opt.rect.y() + 10, card, card
        )
        hover_rect = QRect(
            opt.rect.x() + (opt.rect.width() - 170) // 2,
            opt.rect.y() + 5, 170, 250
        )
        is_hovered = self.check_hover_state(opt, index)
        is_selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        if is_selected:
            import theme_manager
            accent_hex = theme_manager.get_current_accent_hex()
            accent = QColor(accent_hex)
            painter.setBrush(QColor(accent.red(), accent.green(), accent.blue(), 30))
            painter.setPen(QPen(accent, 2))
            painter.drawRoundedRect(hover_rect, 10, 10)
            painter.setPen(Qt.PenStyle.NoPen)                          
        elif is_hovered:
            painter.setBrush(QColor(255, 255, 255, 15))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(hover_rect, 10, 10)
        data = index.data(Qt.ItemDataRole.UserRole)
        if not data:
            painter.restore()
            return
        p_name = data.get('name', '')
        count = data.get('count', 0)
        covers = data.get('covers', [])
        custom_cover = data.get('custom_cover', None)
        from settings_manager import settings
        radius = 0 if settings.get('square_covers', False) else 10
        from PyQt6.QtGui import QPainterPath
        clip = QPainterPath()
        clip.addRoundedRect(float(icon_rect.x()), float(icon_rect.y()),
                            float(icon_rect.width()), float(icon_rect.height()), radius, radius)
        painter.setClipPath(clip)
        if custom_cover and isinstance(custom_cover, str) and os.path.exists(custom_cover):
            pix = self.player.image_cache.get_cached_pixmap(custom_cover, card, radius=0)
            painter.drawPixmap(icon_rect, pix)
        elif covers:
            half = 79
            gap = 2
            positions = [
                (icon_rect.x(), icon_rect.y()),
                (icon_rect.x() + half + gap, icon_rect.y()),
                (icon_rect.x(), icon_rect.y() + half + gap),
                (icon_rect.x() + half + gap, icon_rect.y() + half + gap),
            ]
            for i, (px, py) in enumerate(positions):
                if i < len(covers) and isinstance(covers[i], str):
                    cpix = self.player.image_cache.get_cached_pixmap(covers[i], half, radius=0)
                    painter.drawPixmap(px, py, half, half, cpix)
                else:
                    painter.fillRect(px, py, half, half, QColor(60, 60, 60))
        else:
            painter.fillRect(icon_rect, QColor(45, 45, 50))
            painter.setClipping(False)
            if not hasattr(PlaylistGridDelegate, '_empty_playlist_pixmap_cache'):
                PlaylistGridDelegate._empty_playlist_pixmap_cache = {}
            ic_size = 56
            if ic_size not in PlaylistGridDelegate._empty_playlist_pixmap_cache:
                svg_path = os.path.join(APP_ROOT, "resources", "app", "logo_full.svg")
                if os.path.exists(svg_path):
                    from PyQt6.QtGui import QPixmap
                    from PyQt6.QtSvg import QSvgRenderer
                    tmp_pix = QPixmap(ic_size, ic_size)
                    tmp_pix.fill(Qt.GlobalColor.transparent)
                    tmp_painter = QPainter(tmp_pix)
                    tmp_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    tmp_painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                    renderer = QSvgRenderer(svg_path)
                    renderer.render(tmp_painter)
                    tmp_painter.end()
                    PlaylistGridDelegate._empty_playlist_pixmap_cache[ic_size] = tmp_pix
                else:
                    PlaylistGridDelegate._empty_playlist_pixmap_cache[ic_size] = None
            cached_pix = PlaylistGridDelegate._empty_playlist_pixmap_cache.get(ic_size)
            ic_rect = QRect(icon_rect.x() + (card - ic_size) // 2,
                            icon_rect.y() + (card - ic_size) // 2, ic_size, ic_size)
            if cached_pix:
                painter.drawPixmap(ic_rect.x(), ic_rect.y(), cached_pix)
            else:
                icon = FIF.MUSIC_FOLDER.icon() if hasattr(FIF, 'MUSIC_FOLDER') else FIF.FOLDER.icon()
                icon.paint(painter, ic_rect)
        painter.setClipping(False)
        if is_hovered:
            clip2 = QPainterPath()
            clip2.addRoundedRect(float(icon_rect.x()), float(icon_rect.y()),
                                 float(icon_rect.width()), float(icon_rect.height()), radius, radius)
            painter.setClipPath(clip2)
            painter.fillRect(icon_rect, QColor(0, 0, 0, 100))
            painter.setClipping(False)
            btn_size = 48
            btn_rect = QRect(
                icon_rect.x() + (icon_rect.width() - btn_size) // 2,
                icon_rect.y() + (icon_rect.height() - btn_size) // 2,
                btn_size, btn_size
            )
            from PyQt6.QtGui import QRadialGradient, QPolygonF
            from PyQt6.QtCore import QPointF
            accent = _get_accent_color()
            cx = btn_rect.x() + btn_rect.width() / 2.0
            cy = btn_rect.y() + btn_rect.height() / 2.0
            intensity = self._btn_glow_intensities.get(index.row(), 0.0)
            if intensity > 0.0:
                glow_radius = 32.0
                gradient = QRadialGradient(QPointF(cx, cy), glow_radius)
                alpha = int(160 * intensity)
                base_glow = QColor(accent)
                base_glow.setAlpha(alpha)
                mid_glow = QColor(accent)
                mid_glow.setAlpha(int(alpha * 0.3))
                transparent = QColor(accent)
                transparent.setAlpha(0)
                stop_edge = 24.0 / glow_radius
                gradient.setColorAt(0.0, base_glow)
                gradient.setColorAt(stop_edge, base_glow)
                gradient.setColorAt(stop_edge + 0.1, mid_glow)
                gradient.setColorAt(1.0, transparent)
                painter.setBrush(gradient)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(cx, cy), glow_radius, glow_radius)
            painter.setBrush(accent)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(btn_rect)
            painter.setBrush(QColor(255, 255, 255))
            triangle = QPolygonF([
                QPointF(cx - 6, cy - 10),
                QPointF(cx - 6, cy + 10),
                QPointF(cx + 10, cy),
            ])
            painter.drawPolygon(triangle)
        opt.state &= ~QStyle.StateFlag.State_Selected
        opt.state &= ~QStyle.StateFlag.State_MouseOver
        opt.state &= ~QStyle.StateFlag.State_HasFocus
        opt.text = ""
        if not self._font_bold:
            base_size = option.font.pixelSize()
            if base_size <= 0:
                base_size = 12                                                                 
            self._font_bold = QFont(option.font)
            self._font_bold.setBold(True)
            self._font_bold.setPixelSize(15)
            self._font_normal = QFont(option.font)
            self._font_normal.setPixelSize(13)
        text_y = opt.rect.y() + 10 + card + 5
        title_rect = QRect(opt.rect.x() + 5, text_y, opt.rect.width() - 10, 20)
        self.draw_marquee_text(painter, title_rect, p_name, self._font_bold,
                               QColor(255, 255, 255), is_hovered)
        count_text = tr("{count} canciones").format(count=count) if count != 1 else tr("1 canción")
        count_rect = QRect(opt.rect.x() + 5, text_y + 20, opt.rect.width() - 10, 20)
        painter.setFont(self._font_normal)
        painter.setPen(QColor(150, 150, 150))
        painter.drawText(count_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, count_text)
        painter.restore()