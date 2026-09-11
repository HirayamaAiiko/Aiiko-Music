from PyQt6.QtCore import Qt, QSize, QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal, pyqtProperty, QEvent
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPixmap, QIcon, QCursor
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QToolTip
)
from qfluentwidgets import TransparentToolButton, FluentIcon as FIF, CaptionLabel, Slider
from widgets import MarqueeLabel, SquareCoverLabel
from core.language_manager import tr
class VLine(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(1)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); margin-top: 12px; margin-bottom: 12px;")
ICON_PREV = getattr(FIF, 'PREVIOUS', getattr(FIF, 'LEFT', FIF.CARE_LEFT_SOLID))
ICON_NEXT = getattr(FIF, 'NEXT', getattr(FIF, 'RIGHT', FIF.CARE_RIGHT_SOLID))
ICON_PLAY = getattr(FIF, 'PLAY_SOLID', getattr(FIF, 'PLAY', FIF.CARE_RIGHT_SOLID))
ICON_PAUSE = getattr(FIF, 'PAUSE', getattr(FIF, 'PAUSE_BOLD', FIF.REMOVE))
ICON_PIN = getattr(FIF, 'PIN', getattr(FIF, 'KEEP_WINDOW', FIF.ADD))
class FloatingMiniPlayer(QWidget):
    play_pause_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    restore_clicked = pyqtSignal()
    pin_clicked = pyqtSignal(bool)
    @pyqtProperty(float)
    def popup_opacity(self):
        return self._opacity
    @popup_opacity.setter 
    def popup_opacity(self, val):
        self._opacity = val
        self.update()
    def __init__(self, image_cache=None, parent=None):
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint 
                         | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(440, 80)
        self._drag_pos = None
        self._opacity = 0.0
        self._bg_color = QColor("#1C1C1E")
        self._border_color = QColor(255, 255, 255, 15)
        self._accent_color = QColor("#1DB954")
        self._is_playing = False
        self._is_pinned = True
        self.image_cache = image_cache
        self._current_title = "Aiiko Music"
        self._current_artist = "—"
        self._progress = 0.0
        main = QHBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(12)
        self.cover = SquareCoverLabel(radius=6)
        self.cover.setFixedSize(52, 52)
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        self.lbl_title = QLabel("Aiiko Music")
        self.lbl_title.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        self.lbl_title.setFixedHeight(18)
        self.lbl_title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.lbl_title.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_title.mouseDoubleClickEvent = lambda e: self.restore_clicked.emit() if e.button() == Qt.MouseButton.LeftButton else None
        self.lbl_artist = QLabel("—")
        self.lbl_artist.setStyleSheet("color: rgba(255,255,255,0.55); font-size: 12px;")
        self.lbl_artist.setFixedHeight(16)
        self.lbl_artist.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.lbl_artist.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_artist.mouseDoubleClickEvent = lambda e: self.restore_clicked.emit() if e.button() == Qt.MouseButton.LeftButton else None
        self.progress_area = QWidget()
        self.progress_area.setFixedHeight(14)
        prog_layout = QHBoxLayout(self.progress_area)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_curr_time = QLabel("0:00")
        self.lbl_curr_time.setStyleSheet(f"color: {self._accent_color.name()}; font-size: 10px;")
        self.lbl_total_time = QLabel("0:00")
        self.lbl_total_time.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 10px;")
        prog_layout.addWidget(self.lbl_curr_time)
        prog_layout.addStretch()
        prog_layout.addWidget(self.lbl_total_time)
        info_layout.addWidget(self.lbl_title)
        info_layout.addWidget(self.lbl_artist)
        info_layout.addStretch()
        info_layout.addWidget(self.progress_area)
        self.info_container = QWidget()
        self.info_container.setLayout(info_layout)
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        self.btn_prev = TransparentToolButton(ICON_PREV)
        self.btn_prev.setFixedSize(30, 30)
        self.btn_prev.setIconSize(QSize(14, 14))
        self.btn_prev.clicked.connect(self.prev_clicked.emit)
        self.btn_play = TransparentToolButton(ICON_PLAY)
        self.btn_play.setFixedSize(36, 36)
        self.btn_play.setIconSize(QSize(18, 18))
        self.btn_play.clicked.connect(self.play_pause_clicked.emit)
        self.btn_next = TransparentToolButton(ICON_NEXT)
        self.btn_next.setFixedSize(30, 30)
        self.btn_next.setIconSize(QSize(14, 14))
        self.btn_next.clicked.connect(self.next_clicked.emit)
        controls_layout.addWidget(self.btn_prev)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_next)
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)
        self.btn_pin = TransparentToolButton(ICON_PIN)
        self.btn_pin.setFixedSize(28, 28)
        self.btn_pin.setIconSize(QSize(14, 14))
        self.btn_pin.setToolTip(tr("Always on Top"))
        self.btn_pin.clicked.connect(self.toggle_pin)
        self.btn_pin.setStyleSheet("TransparentToolButton { background-color: transparent; border-radius: 4px; }")
        self.btn_pin.setIcon(ICON_PIN.icon(color=self._accent_color.name()))
        self.btn_close = TransparentToolButton(FIF.CLOSE)
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setIconSize(QSize(12, 12))
        self.btn_close.clicked.connect(self.restore_clicked.emit)
        actions_layout.addWidget(self.btn_pin)
        actions_layout.addWidget(self.btn_close)
        main.addWidget(self.cover)
        main.addWidget(self.info_container, 1)
        main.addSpacing(6)
        main.addWidget(VLine(self))
        main.addSpacing(6)
        main.addLayout(controls_layout)
        main.addSpacing(8)
        main.addLayout(actions_layout)
    def toggle_pin(self):
        self._is_pinned = not self._is_pinned
        if self._is_pinned:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
            self.btn_pin.setIcon(ICON_PIN.icon(color=self._accent_color.name()))
        else:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
            self.btn_pin.setIcon(ICON_PIN.icon(color="#FFFFFF"))
        self.show()                 
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._elide_texts()
    def _elide_texts(self):
        t_metrics = self.lbl_title.fontMetrics()
        elided_title = t_metrics.elidedText(self._current_title, Qt.TextElideMode.ElideRight, self.lbl_title.width())
        self.lbl_title.setText(elided_title)
        a_metrics = self.lbl_artist.fontMetrics()
        elided_artist = a_metrics.elidedText(self._current_artist, Qt.TextElideMode.ElideRight, self.lbl_artist.width())
        self.lbl_artist.setText(elided_artist)
    def set_accent_color(self, hex_color):
        self._accent_color = QColor(hex_color)
        self.lbl_curr_time.setStyleSheet(f"color: {hex_color}; font-size: 11px;")
        if self._is_pinned:
            self.btn_pin.setIcon(ICON_PIN.icon(color=hex_color))
        self.update()
    def update_track(self, track):
        self._current_title = track.title or "Aiiko Music"
        self._current_artist = track.artist or "—"
        self._progress = 0.0
        self._elide_texts()
        album = getattr(track, 'album', None) or tr("Álbum desconocido")
        tooltip = f"<b>{self._current_title}</b><br>{self._current_artist}<br><i>{album}</i>"
        self.info_container.setToolTip(tooltip)
        if self.image_cache:
            self.image_cache.assign_async_pixmap(self.cover, track, 65, 0)
        else:
            self.cover.setPixmap(QPixmap())
    def update_play_state(self, is_playing):
        self._is_playing = is_playing
        self.btn_play.setIcon(QIcon(ICON_PAUSE.icon()) if is_playing else QIcon(ICON_PLAY.icon()))
    def update_progress(self, curr_ms, total_ms):
        if total_ms > 0:
            self._progress = min(1.0, max(0.0, curr_ms / total_ms))
            def format_time(ms):
                s = int(ms / 1000)
                m = s // 60
                s = s % 60
                return f"{m}:{s:02d}"
            self.lbl_curr_time.setText(format_time(curr_ms))
            self.lbl_total_time.setText(format_time(total_ms))
            self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)
        from PyQt6.QtCore import QRectF
        rect = QRectF(0, 0, self.width(), self.height()).adjusted(4.5, 4.5, -4.5, -4.5)
        for i in range(4):
            sc = QColor(0, 0, 0, int(25 - i * 5))
            sp = QPainterPath()
            sr = rect.adjusted(-i*2, -i+i, i*2, i*2)
            sp.addRoundedRect(sr, 10, 10)
            painter.fillPath(sp, sc)
        bp = QPainterPath()
        bp.addRoundedRect(rect, 8, 8)
        painter.fillPath(bp, self._bg_color)
        p_pos = self.progress_area.mapTo(self, QPoint(0, 0))
        bar_y = float(p_pos.y() - 6)
        bar_x = float(p_pos.x())
        max_w = float(self.progress_area.width())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 30))
        bp_path = QPainterPath()
        bp_path.addRoundedRect(bar_x, bar_y, max_w, 3, 1.5, 1.5)
        painter.fillPath(bp_path, QColor(255, 255, 255, 30))
        if self._progress > 0:
            painter.setBrush(self._accent_color)
            ap_path = QPainterPath()
            ap_path.addRoundedRect(bar_x, bar_y, max_w * self._progress, 3, 1.5, 1.5)
            painter.fillPath(ap_path, self._accent_color)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(self._border_color)
        painter.drawRoundedRect(rect, 8, 8)
        painter.end()
    def show_animated(self):
        self._opacity = 0.0
        self.show()
        self._anim = QPropertyAnimation(self, b"popup_opacity")
        self._anim.setDuration(250)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._anim.start()
    def fade_out(self):
        self._anim = QPropertyAnimation(self, b"popup_opacity")
        self._anim.setDuration(180)
        self._anim.setStartValue(self._opacity)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InQuad)
        self._anim.finished.connect(self.hide)
        self._anim.start()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
    def apply_theme(self, bg_color=None, border_color=None):
        if bg_color and border_color:
            self._bg_color = QColor(bg_color)
            self._border_color = QColor(border_color)
        else:
            self._bg_color = QColor("#1A1A1E")
            self._border_color = QColor(255, 255, 255, 15)
        self.update()