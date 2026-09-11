from PyQt6.QtCore import Qt, QSize, QRect, QEvent, pyqtProperty, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QFontMetrics, QFont
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QListWidget, QListWidgetItem, QApplication, QGraphicsOpacityEffect,
                             QStyledItemDelegate, QStyle, QFrame, QLineEdit)
from qfluentwidgets import FluentIcon as FIF
from utils import get_artists_from_string
from settings_manager import settings
from core.language_manager import tr
class SpotlightListDelegate(QStyledItemDelegate):
    _icon_cache = {}
    def __init__(self, parent_view, player):
        super().__init__(parent_view)
        self.player = player
        self._cached_fonts = {}
    def _get_fonts_and_metrics(self, base_font):
        key = base_font.key()
        if key not in self._cached_fonts:
            font_title = QFont(base_font)
            font_title.setPixelSize(13)
            font_title.setBold(True)
            fm_title = QFontMetrics(font_title)
            font_artist = QFont(base_font)
            font_artist.setPixelSize(12)
            font_artist.setBold(False)
            fm_artist = QFontMetrics(font_artist)
            self._cached_fonts[key] = (font_title, fm_title, font_artist, fm_artist)
        return self._cached_fonts[key]
    def sizeHint(self, option, index):
        item_data = index.data(Qt.ItemDataRole.UserRole)
        if item_data == "WIDGET_ITEM":
            size = index.data(Qt.ItemDataRole.SizeHintRole)
            if size is not None:
                return size
        return QSize(option.rect.width(), 50)
    @classmethod
    def _get_fallback_icon(cls, icon_enum):
        import theme_manager
        accent_hex = theme_manager.get_current_accent_hex()
        key = (icon_enum.value if hasattr(icon_enum, 'value') else str(icon_enum)) + accent_hex
        if key not in cls._icon_cache:
            cls._icon_cache[key] = icon_enum.icon(color=QColor(accent_hex))
        return cls._icon_cache[key]
    def paint(self, painter, option, index):
        item_data = index.data(Qt.ItemDataRole.UserRole)
        if not item_data: return
        if item_data == "WIDGET_ITEM":
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.save()
        if option.state & QStyle.StateFlag.State_Selected or option.state & QStyle.StateFlag.State_MouseOver:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 20))
            painter.drawRoundedRect(option.rect.adjusted(2, 2, -2, -2), 8, 8)
        bg_rect = option.rect
        cover_size = 40
        cover_rect = QRect(bg_rect.x() + 10, bg_rect.y() + (bg_rect.height() - cover_size) // 2, cover_size, cover_size)
        text_x = cover_rect.right() + 12
        text_y_center = bg_rect.y() + bg_rect.height() // 2
        font_title, fm_title, font_artist, fm_artist = self._get_fonts_and_metrics(option.font)
        title_text = ""
        subtitle_text = ""
        icon = None
        if hasattr(item_data, 'filepath'):
            title_text = item_data.title
            subtitle_text = item_data.artist
            icon = self.player.image_cache.get_cached_icon(item_data, 50, radius=4, fallback_icon=FIF.MUSIC)
        elif isinstance(item_data, dict):
            title_text = item_data.get('name', '')
            tipo = item_data.get('type', '')
            if tipo == 'album':
                subtitle_text = "Álbum"
                icon = self._get_fallback_icon(FIF.ALBUM)
            elif tipo == 'artist':
                subtitle_text = "Artista"
                icon = self._get_fallback_icon(FIF.PEOPLE)
            elif tipo == 'playlist':
                subtitle_text = "Playlist"
                icon = self._get_fallback_icon(FIF.FOLDER)
        if icon:
            if hasattr(icon, 'paint'):
                icon.paint(painter, cover_rect, Qt.AlignmentFlag.AlignCenter)
            else:
                painter.drawPixmap(cover_rect, icon)
        painter.setFont(font_title)
        painter.setPen(QColor(255, 255, 255))
        title_rect = QRect(text_x, text_y_center - 18, bg_rect.width() - text_x - 10, 20)
        elided_title = fm_title.elidedText(title_text, Qt.TextElideMode.ElideRight, title_rect.width())
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)
        painter.setFont(font_artist)
        painter.setPen(QColor(136, 136, 136))
        artist_rect = QRect(text_x, text_y_center, bg_rect.width() - text_x - 10, 20)
        elided_artist = fm_artist.elidedText(subtitle_text, Qt.TextElideMode.ElideRight, artist_rect.width())
        painter.drawText(artist_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_artist)
        painter.restore()