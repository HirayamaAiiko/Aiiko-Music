from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt, QRect
from core.language_manager import tr
from PyQt6.QtSvg import QSvgRenderer
from qfluentwidgets import FluentIcon as FIF
class SongTableHeader(QWidget):
    def __init__(self, parent=None, solid_bg=False, is_album_view=False, is_artist_view=False, is_album_list=False):
        super().__init__(parent)
        self.is_album_view = is_album_view
        self.is_artist_view = is_artist_view
        self.is_album_list = is_album_list
        self.list_view = None
        self.solid_bg = solid_bg
        self.setFixedHeight(32)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("color: #888888; font-size: 13px; font-weight: bold;")
        self._clock_renderer = QSvgRenderer()
        try:
            with open("resources/buttons/clock.svg", "r", encoding="utf-8") as f:
                svg_data = f.read().replace('currentColor', '#888888').encode('utf-8')
                self._clock_renderer.load(svg_data)
        except Exception:
            pass
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if getattr(self, 'solid_bg', False):
            from qfluentwidgets import isDarkTheme
            bg_hex = None
            try:
                from settings_manager import settings
                import theme_manager
                theme_name = settings.get('app_theme', 'Oscuro (Dark)')
                theme_data = theme_manager.get_theme(theme_name)
                bg_hex = theme_data.get('page_content_bg') or theme_data.get('main_bg')
            except Exception:
                pass
            if bg_hex:
                bg_color = QColor(bg_hex)
            else:
                bg_color = QColor(32, 32, 32) if isDarkTheme() else QColor(243, 243, 243)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg_color)
            painter.drawRect(self.rect())
        scroll_offset = 0
        if self.list_view and self.list_view.verticalScrollBar().isVisible():
            scroll_offset = self.list_view.verticalScrollBar().width()
        from PyQt6.QtCore import QRectF
        bg_rect = QRectF(5, 0, self.width() - 10 - scroll_offset, self.height()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 10))
        painter.drawRoundedRect(bg_rect, 8, 8)
        painter.setPen(QColor(255, 255, 255, 20))
        painter.drawLine(int(bg_rect.left() + 8), self.height() - 1, int(bg_rect.right() - 8), self.height() - 1)
        painter.setPen(QColor(136, 136, 136))
        m = 5                                                         
        col_num = 50
        col_end = 0 if getattr(self, 'is_album_list', False) else 130
        has_covers = getattr(self, 'has_covers', False)
        cover_padding = 45 if has_covers else 0
        eff_w = self.width() - 2 * m - scroll_offset
        W = eff_w - col_num - cover_padding - col_end
        w_year = 0
        if getattr(self, 'is_album_list', False):
            w_title = int(W * 0.40)
            w_artist = int(W * 0.30)
            w_year = int(W * 0.30)
            w_album = 0
        elif getattr(self, 'is_album_view', False):
            w_title = W
            w_artist = 0
            w_year = 0
            w_album = 0
        elif getattr(self, 'is_artist_view', False):
            w_title = W
            w_artist = 0
            w_album = 0
        else:
            w_title = int(W * 0.40)
            w_artist = int(W * 0.30)
            w_album = int(W * 0.30)
        x = m                               
        if col_num > 0:
            painter.drawText(QRect(x, 0, col_num, self.height()), Qt.AlignmentFlag.AlignCenter, "#")
            x += col_num
        x += cover_padding
        if getattr(self, 'is_album_list', False):
            painter.drawText(QRect(x, 0, w_title, self.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, tr("ÁLBUM"))
            painter.drawText(QRect(x + w_title, 0, w_artist, self.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, tr("ARTISTA"))
            painter.drawText(QRect(x + w_title + w_artist, 0, w_year, self.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, tr("AÑO"))
        elif getattr(self, 'is_album_view', False):
            painter.drawText(QRect(x, 0, w_title, self.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, tr("TÍTULO"))
        elif getattr(self, 'is_artist_view', False):
            painter.drawText(QRect(x, 0, w_title, self.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, tr("TÍTULO"))
        else:
            painter.drawText(QRect(x, 0, w_title, self.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, tr("TÍTULO"))
            if w_artist > 0:
                painter.drawText(QRect(x + w_title, 0, w_artist, self.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, tr("ARTISTA"))
            if w_album > 0:
                painter.drawText(QRect(x + w_title + w_artist, 0, w_album, self.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, tr("ÁLBUM"))
        if col_end > 0:
            dur_center = int(bg_rect.right()) - 105
            heart_center = int(bg_rect.right()) - 38
            if getattr(self, '_clock_renderer', None) and self._clock_renderer.isValid():
                self._clock_renderer.render(painter, QRectF(dur_center - 8, (self.height() - 16) // 2, 16, 16))
            else:
                FIF.HISTORY.render(painter, QRectF(dur_center - 8, (self.height() - 16) // 2, 16, 16))
            FIF.HEART.render(painter, QRectF(heart_center - 8, (self.height() - 16) // 2, 16, 16))
        painter.end()
