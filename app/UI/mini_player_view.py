from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QRadialGradient, QColor, QPixmap
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QSizePolicy)
from qfluentwidgets import (CaptionLabel, Slider, ToolButton, TransparentToolButton,
                            FluentIcon as FIF)
from config import *
from settings_manager import settings
from widgets import MarqueeLabel, MiniPlayerWidget
from core.language_manager import tr
class CoverLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(65, 65)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    def paintEvent(self, event):
        if not self.pixmap() or self.pixmap().isNull():
            from PyQt6.QtGui import QPainter, QColor
            from PyQt6.QtCore import Qt, QRectF
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#282828"))
            painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()).adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)
            painter.end()
        super().paintEvent(event)
from qfluentwidgets import FlyoutViewBase, Flyout, FlyoutAnimationType
class VolPopupWidget(FlyoutViewBase):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 50)
        popup_layout = QHBoxLayout(self)
        popup_layout.setContentsMargins(14, 8, 20, 8)
        self.vol_popup_icon = TransparentToolButton()
        from config import ICON_VOLUME, ICON_MUTE
        is_muted = getattr(player.player_controller, '_is_muted', False)
        icon_name = "mute.svg" if is_muted else "volume.svg"
        fallback = ICON_MUTE if is_muted else ICON_VOLUME
        self.vol_popup_icon.setIcon(player.playback_ui_controller._get_icon(icon_name, fallback))
        self.vol_popup_icon.setIconSize(QSize(22, 22))
        self.vol_popup_icon.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.vol_popup_icon.clicked.connect(player.player_controller.toggle_mute)
        popup_layout.addWidget(self.vol_popup_icon)
        self.mini_volume_popup = Slider(Qt.Orientation.Horizontal)
        self.mini_volume_popup.setRange(0, 100)
        self.mini_volume_popup.setValue(settings.get('volume', 80))
        self.mini_volume_popup.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.mini_volume_popup.valueChanged.connect(player.player_controller.set_volume)
        popup_layout.addWidget(self.mini_volume_popup, alignment=Qt.AlignmentFlag.AlignCenter)
        self.vol_label = CaptionLabel(f"{self.mini_volume_popup.value()}%")
        self.vol_label.setFixedWidth(32)
        self.vol_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.mini_volume_popup.valueChanged.connect(lambda v: self.vol_label.setText(f"{v}%"))
        popup_layout.addWidget(self.vol_label)
        def show_vol_tooltip(v):
            if self.mini_volume_popup.underMouse() or self.mini_volume_popup.isSliderDown():
                from PyQt6.QtWidgets import QToolTip
                from PyQt6.QtGui import QCursor
                QToolTip.showText(QCursor.pos(), f"{v}%", self.mini_volume_popup)
        self.mini_volume_popup.valueChanged.connect(show_vol_tooltip)
        player.vol_popup_icon = self.vol_popup_icon
        player.mini_volume_popup = self.mini_volume_popup
class HoverableInfoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._hovered = False
    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)
    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)
    def paintEvent(self, event):
        if self._hovered:
            from PyQt6.QtGui import QPainter, QColor
            from PyQt6.QtCore import Qt, QRectF
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 12)) 
            painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()).adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)
            painter.end()
        super().paintEvent(event)
class _ControlsGlowWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._accent = None
        self._cached_pixmap = None
        self._cached_size = None
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background: transparent;")
    def set_accent(self, accent_hex):
        self._accent = accent_hex
        self._cached_pixmap = None
        self.update()
    def paintEvent(self, event):
        from settings_manager import settings
        if not settings.get('mini_player_glow', True):
            return
        if not self._accent:
            return
        w, h = self.width(), self.height()
        if w < 1 or h < 1:
            return
        if self._cached_pixmap is None or self._cached_size != (w, h):
            self._cached_size = (w, h)
            self._cached_pixmap = QPixmap(w, h)
            self._cached_pixmap.fill(Qt.GlobalColor.transparent)
            p = QPainter(self._cached_pixmap)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            cx, cy = w / 2, h / 2
            radius = w * 0.38
            gradient = QRadialGradient(cx, cy, radius)
            c = QColor(self._accent)
            c.setAlphaF(0.12)
            gradient.setColorAt(0.0, c)
            c2 = QColor(self._accent)
            c2.setAlphaF(0.0)
            gradient.setColorAt(1.0, c2)
            p.setBrush(gradient)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(0, 0, w, h)
            p.end()
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._cached_pixmap)
        painter.end()
class PlayCircleButton(TransparentToolButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(45, 45)
        self.setIconSize(QSize(26, 26))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._hovered = False
        self._pressed = False
        self._accent = "#000000"
        self.is_playing = False
    def set_accent(self, accent_hex):
        self._accent = accent_hex
        self.update()
    def enterEvent(self, e):
        self._hovered = True
        super().enterEvent(e)
        self.update()
    def leaveEvent(self, e):
        self._hovered = False
        super().leaveEvent(e)
        self.update()
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
        super().mousePressEvent(e)
        self.update()
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._pressed = False
        super().mouseReleaseEvent(e)
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._accent)
        border_color = c
        bg_color = QColor(Qt.GlobalColor.transparent)
        if self._pressed:
            border_color = c.darker(120)
            bg_color = QColor(255, 255, 255, 8)
        elif self._hovered:
            border_color = c.lighter(130)
            bg_color = QColor(255, 255, 255, 15)
        painter.setBrush(bg_color)
        from PyQt6.QtGui import QPen
        from PyQt6.QtCore import QRectF
        pen = QPen(border_color, 2.0)
        painter.setPen(pen)
        painter.drawEllipse(QRectF(1.0, 1.0, self.width() - 2.0, self.height() - 2.0))
        if not self.icon().isNull():
            icon_size = self.iconSize()
            x = (self.width() - icon_size.width()) // 2
            y = (self.height() - icon_size.height()) // 2
            offset_x = 0 if self.is_playing else 2
            self.icon().paint(painter, x + offset_x, y, icon_size.width(), icon_size.height(), Qt.AlignmentFlag.AlignCenter)
        painter.end()
class MiniPlayerView(MiniPlayerWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self._build_ui(player)
    def _build_ui(self, player):
        self.setMinimumHeight(85)
        self.setMaximumHeight(120)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 10, 10, 10)
        player.mini_cover = CoverLabel()
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        info_layout.setSpacing(1)
        player.mini_title = MarqueeLabel("Aiiko Music")
        player.mini_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        player.mini_artist = QLabel(tr("Selecciona una pista"))
        player.mini_artist.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        player.mini_artist.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        player.mini_album = QLabel("")
        player.mini_album.setStyleSheet("color: #888888; font-size: 11px;")
        player.mini_album.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        info_layout.addWidget(player.mini_title)
        info_layout.addWidget(player.mini_artist)
        info_layout.addWidget(player.mini_album)
        info_container = QWidget()
        info_container.setMinimumWidth(80)
        info_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        info_container.setCursor(Qt.CursorShape.PointingHandCursor)
        info_wrapper = QHBoxLayout(info_container)
        info_wrapper.setContentsMargins(0, 0, 0, 0)
        info_wrapper.addLayout(info_layout)
        player.mini_info_clickable = HoverableInfoWidget()
        clickable_layout = QHBoxLayout(player.mini_info_clickable)
        clickable_layout.setContentsMargins(6, 6, 12, 6)
        clickable_layout.setSpacing(15)
        clickable_layout.addWidget(player.mini_cover)
        clickable_layout.addWidget(info_container, 1)
        player.mini_info_clickable.mousePressEvent = lambda e: player.navigation_controller.toggle_now_playing() if e.button() == Qt.MouseButton.LeftButton else None
        controls_layout = QVBoxLayout()
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row.setSpacing(5)
        player.btn_mini_shuffle = TransparentToolButton()
        player.btn_mini_shuffle.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.playback_ui_controller._update_shuffle_icon()
        player.btn_mini_shuffle.clicked.connect(player.queue_controller.toggle_shuffle)
        player.btn_mini_prev = TransparentToolButton()
        player.btn_mini_prev.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.btn_mini_prev.setIcon(player.playback_ui_controller._get_icon("prev.svg", ICON_PREV))
        player.btn_mini_prev.clicked.connect(lambda: player.playback_controller.prev_track(manual=True))
        player.btn_mini_play = PlayCircleButton()
        self._apply_play_btn_accent(player)
        player.playback_ui_controller._update_play_icon(False)
        player.btn_mini_play.clicked.connect(player.playback_controller.toggle_play)
        player.btn_mini_next = TransparentToolButton()
        player.btn_mini_next.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.btn_mini_next.setIcon(player.playback_ui_controller._get_icon("next.svg", ICON_NEXT))
        player.btn_mini_next.clicked.connect(lambda: player.playback_controller.next_track(manual=True))
        player.btn_mini_repeat = TransparentToolButton()
        player.btn_mini_repeat.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.playback_ui_controller._update_repeat_icon()
        player.btn_mini_repeat.clicked.connect(player.queue_controller.toggle_repeat)
        for btn in [player.btn_mini_shuffle, player.btn_mini_prev, player.btn_mini_next, player.btn_mini_repeat]:
            btn.setIconSize(QSize(22, 22))
        from PyQt6.QtCore import QEvent, QObject
        class MiniPlayerHoverFilter(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Type.Enter:
                    import theme_manager
                    accent = theme_manager.get_current_accent_hex()
                    if obj == player.btn_mini_shuffle:
                        obj.setIcon(player.playback_ui_controller._get_icon("shuffle.svg", ICON_SHUFFLE, accent))
                    elif obj == player.btn_mini_prev:
                        obj.setIcon(player.playback_ui_controller._get_icon("prev.svg", ICON_PREV, accent))
                    elif obj == player.btn_mini_next:
                        obj.setIcon(player.playback_ui_controller._get_icon("next.svg", ICON_NEXT, accent))
                    elif obj == player.btn_mini_play:
                        is_playing = getattr(obj, 'is_playing', False)
                        if is_playing:
                            obj.setIcon(player.playback_ui_controller._get_icon("pause.svg", ICON_PAUSE, accent))
                        else:
                            obj.setIcon(player.playback_ui_controller._get_icon("play.svg", ICON_PLAY, accent))
                    elif obj == player.btn_mini_repeat:
                        mode = getattr(player.queue, 'repeat_mode', 0)
                        if mode == 0:
                            obj.setIcon(player.playback_ui_controller._get_icon("repeat_off.svg", ICON_REPEAT, accent))
                        elif mode == 1:
                            obj.setIcon(player.playback_ui_controller._get_icon("repeat.svg", ICON_REPEAT, accent))
                        elif mode == 2:
                            obj.setIcon(player.playback_ui_controller._get_icon("repeat1.svg", ICON_REPEAT, '#FFB900'))
                elif event.type() == QEvent.Type.Leave:
                    if obj == player.btn_mini_shuffle:
                        player.playback_ui_controller._update_shuffle_icon()
                    elif obj == player.btn_mini_prev:
                        obj.setIcon(player.playback_ui_controller._get_icon("prev.svg", ICON_PREV, '#FFFFFF'))
                    elif obj == player.btn_mini_next:
                        obj.setIcon(player.playback_ui_controller._get_icon("next.svg", ICON_NEXT, '#FFFFFF'))
                    elif obj == player.btn_mini_play:
                        is_playing = getattr(obj, 'is_playing', False)
                        player.playback_ui_controller._update_play_icon(is_playing)
                    elif obj == player.btn_mini_repeat:
                        player.playback_ui_controller._update_repeat_icon()
                return False
        player._mini_hover_filter = MiniPlayerHoverFilter(player)
        player.btn_mini_shuffle.installEventFilter(player._mini_hover_filter)
        player.btn_mini_prev.installEventFilter(player._mini_hover_filter)
        player.btn_mini_play.installEventFilter(player._mini_hover_filter)
        player.btn_mini_next.installEventFilter(player._mini_hover_filter)
        player.btn_mini_repeat.installEventFilter(player._mini_hover_filter)
        btn_row.addWidget(player.btn_mini_shuffle)
        btn_row.addWidget(player.btn_mini_prev)
        btn_row.addWidget(player.btn_mini_play)
        btn_row.addWidget(player.btn_mini_next)
        btn_row.addWidget(player.btn_mini_repeat)
        prog_row = QHBoxLayout()
        player.mini_time_curr = CaptionLabel(tr("0:00"))
        player.mini_time_curr.setMinimumWidth(45)
        player.mini_time_curr.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        class HoverSlider(Slider):
            def __init__(self, orientation, parent=None):
                super().__init__(orientation, parent)
                from PyQt6.QtCore import QTimer
                self._hide_timer = QTimer(self)
                self._hide_timer.setSingleShot(True)
                self._hide_timer.setInterval(800)                   
                self._hide_timer.timeout.connect(self._do_hide)
                if hasattr(self, 'handle'):
                    self.handle.hide()
            def _do_hide(self):
                if hasattr(self, 'handle') and not self.isSliderDown():
                    self.handle.hide()
            def enterEvent(self, e):
                self._hide_timer.stop()
                if hasattr(self, 'handle'):
                    self.handle.show()
                super().enterEvent(e)
            def leaveEvent(self, e):
                if not self.isSliderDown():
                    self._hide_timer.start()
                super().leaveEvent(e)
            def mousePressEvent(self, e):
                if e.button() == Qt.MouseButton.LeftButton:
                    self.setSliderDown(True)
                    val = self.minimum() + ((self.maximum() - self.minimum()) * e.position().x()) / self.width()
                    self.setValue(int(val))
                    self.sliderPressed.emit()
                    self.sliderMoved.emit(int(val))
                super().mousePressEvent(e)
            def mouseMoveEvent(self, e):
                if self.isSliderDown():
                    val = self.minimum() + ((self.maximum() - self.minimum()) * e.position().x()) / self.width()
                    val = max(self.minimum(), min(self.maximum(), val))
                    self.setValue(int(val))
                    self.sliderMoved.emit(int(val))
                super().mouseMoveEvent(e)
            def mouseReleaseEvent(self, e):
                if e.button() == Qt.MouseButton.LeftButton and self.isSliderDown():
                    self.setSliderDown(False)
                    self.sliderReleased.emit()
                super().mouseReleaseEvent(e)
                pos = e.position().toPoint() if hasattr(e, 'position') else e.pos()
                if not self.rect().contains(pos):
                    self._hide_timer.start()
        player.mini_slider = HoverSlider(Qt.Orientation.Horizontal)
        player.mini_slider.setRange(0, 1000)
        player.mini_time_tot = CaptionLabel(tr("0:00"))
        player.mini_time_tot.setMinimumWidth(45)
        player.mini_time_tot.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        prog_row.addWidget(player.mini_time_curr)
        prog_row.addWidget(player.mini_slider)
        prog_row.addWidget(player.mini_time_tot)
        controls_layout.addLayout(btn_row)
        controls_layout.addLayout(prog_row)
        extra_layout = QHBoxLayout()
        extra_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        extra_layout.setSpacing(2)
        player.btn_mini_queue = TransparentToolButton()
        player.btn_mini_queue.setIcon(player.playback_ui_controller._get_icon("queue.svg", FIF.TILES))
        player.btn_mini_queue.setIconSize(QSize(22, 22))
        player.btn_mini_queue.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.btn_mini_queue.setToolTip(tr("Cola de Reproducción"))
        player.btn_mini_queue.clicked.connect(player.queue_controller.toggle_queue_panel)
        player.btn_fullscreen = TransparentToolButton()
        player.btn_fullscreen.setIcon(player.playback_ui_controller._get_icon("fullscreen.svg", FIF.FULL_SCREEN))
        player.btn_fullscreen.setIconSize(QSize(22, 22))
        player.btn_fullscreen.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.btn_fullscreen.setToolTip(tr("Pantalla Completa"))
        player.btn_fullscreen.clicked.connect(player.navigation_controller.toggle_fullscreen)
        player.vol_icon = TransparentToolButton()
        player.vol_icon.setIcon(player.playback_ui_controller._get_icon("volume.svg", ICON_VOLUME))
        player.vol_icon.setIconSize(QSize(22, 22))
        player.vol_icon.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.mini_volume_inline = Slider(Qt.Orientation.Horizontal)
        player.mini_volume_inline.setRange(0, 100)
        player.mini_volume_inline.setValue(settings.get('volume', 80))
        player.mini_volume_inline.setMinimumWidth(60)
        player.mini_volume_inline.setMaximumWidth(140)
        player.mini_volume_inline.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        player.mini_volume_inline.valueChanged.connect(player.player_controller.set_volume)
        def show_inline_vol_tooltip(v):
            if player.mini_volume_inline.underMouse() or player.mini_volume_inline.isSliderDown():
                from PyQt6.QtWidgets import QToolTip
                from PyQt6.QtGui import QCursor
                QToolTip.showText(QCursor.pos(), f"{v}%", player.mini_volume_inline)
        player.mini_volume_inline.valueChanged.connect(show_inline_vol_tooltip)
        def handle_vol_icon_click():
            if player.mini_volume_inline.isVisible():
                player.player_controller.toggle_mute()
            else:
                player.vol_popup = VolPopupWidget(player)
                player.mini_volume_inline.valueChanged.connect(player.vol_popup.mini_volume_popup.setValue)
                player.vol_popup.mini_volume_popup.valueChanged.connect(player.mini_volume_inline.setValue)
                Flyout.make(player.vol_popup, player.vol_icon, player.vol_icon.window(), FlyoutAnimationType.FADE_IN)
        player.vol_icon.clicked.connect(handle_vol_icon_click)
        player.btn_floating_player = TransparentToolButton()
        player.btn_floating_player.setIcon(player.playback_ui_controller._get_icon("minimize.svg", FIF.MINIMIZE))
        player.btn_floating_player.setIconSize(QSize(22, 22))
        player.btn_floating_player.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.btn_floating_player.setToolTip(tr("Mini Player"))
        player.btn_floating_player.clicked.connect(player.system_tray_controller.toggle_floating_player)
        player.btn_mini_eq = TransparentToolButton()
        player.btn_mini_eq.setIcon(player.playback_ui_controller._get_icon("equalizer.svg", FIF.MIX_VOLUMES))
        player.btn_mini_eq.setIconSize(QSize(22, 22))
        player.btn_mini_eq.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.btn_mini_eq.setToolTip(tr("Ecualizador Nativo"))
        extra_layout.addWidget(player.btn_mini_eq)
        extra_layout.addWidget(player.btn_mini_queue)
        extra_layout.addWidget(player.btn_fullscreen)
        extra_layout.addWidget(player.btn_floating_player)
        vol_group = QHBoxLayout()
        vol_group.setContentsMargins(0, 0, 0, 0)
        vol_group.setSpacing(0)
        vol_group.addWidget(player.vol_icon)
        vol_group.addWidget(player.mini_volume_inline)
        extra_layout.addLayout(vol_group)
        player.mini_info_clickable.setMinimumWidth(0)                                
        layout.addWidget(player.mini_info_clickable, 1)
        layout.addLayout(controls_layout, 2)
        layout.addLayout(extra_layout, 1)
        player._controls_glow = _ControlsGlowWidget(self)
        player._controls_glow.lower()                                 
        player._controls_glow.setGeometry(self.rect())
    def resizeEvent(self, event):
        super().resizeEvent(event)
        parent = self.parent() if hasattr(self, 'parent') else None
        glow = None
        if parent and hasattr(parent, '_controls_glow'):
            glow = parent._controls_glow
        elif hasattr(self, '_player_ref') and hasattr(self._player_ref, '_controls_glow'):
            glow = self._player_ref._controls_glow
        for child in self.children():
            if isinstance(child, _ControlsGlowWidget):
                child.setGeometry(self.rect())
                break
    @staticmethod
    def _apply_play_btn_accent(player):
        import theme_manager
        accent = theme_manager.get_accent_hex(
            settings.get('app_accent_name', 'Teal (AIIKO)')
        )
        if isinstance(player.btn_mini_play, PlayCircleButton):
            player.btn_mini_play.set_accent(accent)
        if hasattr(player, '_controls_glow'):
            player._controls_glow.set_accent(accent)