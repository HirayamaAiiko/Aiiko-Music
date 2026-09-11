from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QMovie
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QListView, QAbstractItemView, QLabel)
from qfluentwidgets import SubtitleLabel, TransparentToolButton, FluentIcon as FIF
from config import *
from delegates.list_delegates import QueueListDelegate
from view_models.library_models import QueueListModel
from core.language_manager import tr
class DragScrollListView(QListView):
    _EDGE_ZONE = 50                                                 
    _SCROLL_SPEED = 6                    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_dragging = False
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setInterval(16)          
        self._scroll_timer.timeout.connect(self._auto_scroll_tick)
        self._scroll_direction = 0                              
        self._dragged_row = -1
    @property
    def is_dragging(self):
        return self._is_dragging
    @property
    def dragged_row(self):
        return self._dragged_row
    def startDrag(self, supportedActions):
        self._is_dragging = True
        idx = self.currentIndex()
        self._dragged_row = idx.row() if idx.isValid() else -1
        delegate = self.itemDelegate()
        if hasattr(delegate, '_is_dragging'):
            delegate._is_dragging = True
            delegate._dragged_row = self._dragged_row
        self.viewport().update()
        super().startDrag(supportedActions)
        self._is_dragging = False
        self._dragged_row = -1
        self._scroll_direction = 0
        self._scroll_timer.stop()
        if hasattr(delegate, '_is_dragging'):
            delegate._is_dragging = False
            delegate._dragged_row = -1
        self.viewport().update()
    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        pos_y = event.position().y()
        viewport_h = self.viewport().height()
        if pos_y < self._EDGE_ZONE:
            self._scroll_direction = -1
            if not self._scroll_timer.isActive():
                self._scroll_timer.start()
        elif pos_y > viewport_h - self._EDGE_ZONE:
            self._scroll_direction = 1
            if not self._scroll_timer.isActive():
                self._scroll_timer.start()
        else:
            self._scroll_direction = 0
            self._scroll_timer.stop()
    def dragLeaveEvent(self, event):
        super().dragLeaveEvent(event)
        self._scroll_direction = 0
        self._scroll_timer.stop()
    def _auto_scroll_tick(self):
        sb = self.verticalScrollBar()
        new_val = sb.value() + self._scroll_direction * self._SCROLL_SPEED
        sb.setValue(max(sb.minimum(), min(sb.maximum(), new_val)))
class StaticEqWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self._is_playing = False
    def set_playing(self, is_playing):
        self._is_playing = is_playing
        self.setVisible(is_playing)
        self.update()
    def paintEvent(self, event):
        if not self._is_playing: return
        import theme_manager
        from PyQt6.QtGui import QPainter, QColor
        from PyQt6.QtCore import Qt
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        accent = theme_manager.get_current_accent_hex()
        painter.setBrush(QColor(accent))
        bottom = self.height()
        painter.drawRect(0, bottom - 8, 4, 8)
        painter.drawRect(6, bottom - 14, 4, 14)
        painter.drawRect(12, bottom - 6, 4, 6)
        painter.end()
class PinnedTrackWidget(QWidget):
    clicked = pyqtSignal()
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._is_hovered = False
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(40, 40)
        self.cover_label.setStyleSheet("background: transparent;")
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.title_label = QLabel()
        self.title_label.setStyleSheet("color: white; font-weight: bold; font-size: 15px; background: transparent;")
        self.artist_label = QLabel()
        self.artist_label.setStyleSheet("color: #A0A0A0; font-size: 13px; background: transparent;")
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.artist_label)
        layout.addWidget(self.cover_label)
        layout.addLayout(text_layout)
        layout.addStretch()
        self.eq_widget = StaticEqWidget()
        layout.addWidget(self.eq_widget)
        self.hide()
    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor
        from PyQt6.QtCore import Qt
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        if self._is_hovered:
            painter.setBrush(QColor(255, 255, 255, 20))        
        else:
            painter.setBrush(QColor(255, 255, 255, 13))        
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 8.0, 8.0)
        painter.end()
    def enterEvent(self, event):
        self._is_hovered = True
        self.update()
        super().enterEvent(event)
    def leaveEvent(self, event):
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)
    def contextMenuEvent(self, event):
        self.player.queue_controller.show_pinned_track_context_menu(event.globalPos())
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    def update_track(self, track, pixmap, is_playing):
        if not track:
            self.hide()
            return
        self.show()
        metrics = self.title_label.fontMetrics()
        elided_title = metrics.elidedText(track.title, Qt.TextElideMode.ElideRight, 200)
        self.title_label.setText(elided_title)
        metrics_artist = self.artist_label.fontMetrics()
        elided_artist = metrics_artist.elidedText(track.artist, Qt.TextElideMode.ElideRight, 200)
        self.artist_label.setText(elided_artist)
        if pixmap and not pixmap.isNull():
            rounded_pixmap = QPixmap(40, 40)
            rounded_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 40, 40, 6, 6)
            painter.setClipPath(path)
            scaled = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            x = (40 - scaled.width()) // 2
            y = (40 - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.end()
            self.cover_label.setPixmap(rounded_pixmap)
        self.update_theme()
        self.update_play_state(is_playing)
    def update_theme(self):
        import theme_manager
        accent = theme_manager.get_current_accent_hex()
        self.title_label.setStyleSheet(f"color: {accent}; font-weight: bold; font-size: 15px; background: transparent;")
        if hasattr(self, 'eq_widget'):
            self.eq_widget.update()
    def showEvent(self, event):
        super().showEvent(event)
    def hideEvent(self, event):
        super().hideEvent(event)
    def update_play_state(self, is_playing):
        self._is_playing_state = is_playing
        self.eq_widget.set_playing(is_playing)
class QueuePanel(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.setObjectName("QueuePanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#QueuePanel { background: transparent; border: none; }")
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.shadow_widget = QWidget()
        self.shadow_widget.setFixedWidth(15)
        self.shadow_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0,0,0,0), stop:1 rgba(0,0,0,60));
                border: none;
            }
        """)
        self.content_widget = QWidget()
        self.content_widget.setObjectName("QueueContent")
        self.content_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        main_layout.addWidget(self.shadow_widget)
        main_layout.addWidget(self.content_widget)
        self._build_ui(player)
    def _build_ui(self, player):
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(15, 20, 15, 10)
        header_top_layout = QHBoxLayout()
        header_top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        from qfluentwidgets import TitleLabel, BodyLabel
        player.lbl_queue_title = TitleLabel(tr("A continuación"))
        player.lbl_queue_title.setStyleSheet("font-weight: bold; font-size: 20px; color: white; border: none; background: transparent;")
        header_top_layout.addWidget(player.lbl_queue_title)
        header_top_layout.addStretch()
        btn_clear_queue = TransparentToolButton()
        btn_clear_queue.setIcon(player.playback_ui_controller._get_icon("delete.svg", FIF.DELETE))
        btn_clear_queue.setToolTip(tr("Quitar seleccionados o Limpiar cola"))
        btn_clear_queue.clicked.connect(player.library_controller.delete_selected_queue_items)
        btn_close_queue = TransparentToolButton()
        btn_close_queue.setIcon(player.playback_ui_controller._get_icon("close.svg", FIF.CLOSE))
        btn_close_queue.setToolTip(tr("Cerrar Cola"))
        btn_close_queue.clicked.connect(player.queue_controller.toggle_queue_panel)
        header_top_layout.addWidget(btn_clear_queue)
        header_top_layout.addWidget(btn_close_queue)
        layout.addLayout(header_top_layout)
        player.lbl_queue_subtitle = BodyLabel("")
        player.lbl_queue_subtitle.setTextFormat(Qt.TextFormat.RichText)
        player.lbl_queue_subtitle.setStyleSheet("font-size: 13px; color: #A0A0A0; background: transparent;")
        layout.addWidget(player.lbl_queue_subtitle)
        layout.addSpacing(15)
        header_playing_layout = QHBoxLayout()
        header_playing_layout.setContentsMargins(0, 0, 0, 0)
        header_playing_layout.setSpacing(8)
        player.icon_en_reproduccion = QLabel()
        player.icon_en_reproduccion.setFixedSize(14, 14)
        player.lbl_en_reproduccion = QLabel(tr("EN REPRODUCCIÓN"))
        player.lbl_en_reproduccion.setStyleSheet("font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        header_playing_layout.addWidget(player.icon_en_reproduccion)
        header_playing_layout.addWidget(player.lbl_en_reproduccion)
        header_playing_layout.addStretch()
        layout.addLayout(header_playing_layout)
        layout.addSpacing(5)
        player.pinned_track_widget = PinnedTrackWidget(player)
        player.pinned_track_widget.clicked.connect(player.queue_controller.scroll_to_current)
        layout.addWidget(player.pinned_track_widget)
        layout.addSpacing(10)
        from PyQt6.QtWidgets import QFrame
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); border: none;")
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        layout.addSpacing(10)
        header_next_layout = QHBoxLayout()
        header_next_layout.setContentsMargins(0, 0, 0, 0)
        header_next_layout.setSpacing(8)
        player.icon_proximas = QLabel()
        player.icon_proximas.setFixedSize(14, 14)
        player.lbl_proximas = QLabel(tr("PRÓXIMAS CANCIONES (0)"))
        player.lbl_proximas.setStyleSheet("font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        header_next_layout.addWidget(player.icon_proximas)
        header_next_layout.addWidget(player.lbl_proximas)
        header_next_layout.addStretch()
        layout.addLayout(header_next_layout)
        layout.addSpacing(5)
        player.queue_model = QueueListModel(player)
        player.list_queue_ui = DragScrollListView()
        player.list_queue_ui.setModel(player.queue_model)
        player.list_queue_ui.setObjectName("QueueList")
        player.list_queue_ui.setIconSize(QSize(30, 30))
        player.list_queue_ui.setStyleSheet("border: none; background-color: transparent;")
        player.list_queue_ui.setUniformItemSizes(True)
        player.queue_delegate = QueueListDelegate(player.list_queue_ui, player)
        player.list_queue_ui.setItemDelegate(player.queue_delegate)
        player.list_queue_ui.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        player.list_queue_ui.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        player.list_queue_ui.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        player.list_queue_ui.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        player.list_queue_ui.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        player.queue_model.rowsMoved.connect(player.queue_controller.sync_queue_from_ui)
        player.list_queue_ui.doubleClicked.connect(player.queue_controller.play_from_queue_ui)
        player.list_queue_ui.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        player.list_queue_ui.customContextMenuRequested.connect(player.queue_controller.show_queue_context_menu)
        player.apply_smooth_scroll(player.list_queue_ui)
        layout.addWidget(player.list_queue_ui)