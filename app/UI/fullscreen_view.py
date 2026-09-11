import os
import logging
from PyQt6.QtCore import Qt, QSize, QEvent, QTimer, QPropertyAnimation, QParallelAnimationGroup, QAbstractAnimation, QVariantAnimation
from PyQt6.QtGui import QColor, QPixmap, QPainter, QPainterPath, QImage, QIcon, QLinearGradient
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QSizePolicy, QListWidget, QListWidgetItem,
                             QAbstractItemView, QGraphicsOpacityEffect, QGraphicsDropShadowEffect)
from qfluentwidgets import TransparentToolButton, Slider, FluentIcon as FIF
from widgets import MarqueeLabel
from config import *
from services.lyrics_service import LyricsManager
from settings_manager import settings
import theme_manager
from core.language_manager import tr
try:
    from UI.visualizer.widget import VisualizerWidget
except ImportError as e:
    logging.warning(f"No se pudo cargar el visualizador (probablemente falte numpy): {e}")
    VisualizerWidget = None
from PyQt6.QtCore import pyqtSignal
class FullScreenCover(QLabel):
    pixmapChanged = pyqtSignal(object)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.setMaximumSize(550, 550)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._original_pixmap = None
        self._scale_factor = 1.0
        self._radius = 0 if settings.get('square_covers', False) else 20
    def update_cover_style(self):
        self._radius = 0 if settings.get('square_covers', False) else 20
        self.update()
    def set_scale_factor(self, scale):
        self._scale_factor = scale
        if self._original_pixmap:
            self.update()
    def setPixmap(self, pixmap):
        self._original_pixmap = pixmap
        self.update()
        self.pixmapChanged.emit(pixmap)
    def paintEvent(self, event):
        if not self._original_pixmap or self._original_pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        w = self.width()
        h = self.height()
        side = min(w, h)
        x = (w - side) // 2
        y = (h - side) // 2
        path = QPainterPath()
        path.addRoundedRect(x, y, side, side, self._radius, self._radius)
        painter.setClipPath(path)
        scaled = self._original_pixmap.scaled(side, side,
                                               Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                               Qt.TransformationMode.SmoothTransformation)
        new_w = int(side * self._scale_factor)
        new_h = int(side * self._scale_factor)
        x = x + (side - new_w) // 2
        y = y + (side - new_h) // 2
        if self._scale_factor != 1.0:
            final_pixmap = scaled.scaled(new_w, new_h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(x, y, final_pixmap)
        else:
            painter.drawPixmap(x, y, scaled)
        painter.end()
class FullScreenPlayer(QWidget):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self._is_slider_pressed = False
        self._lyrics_visible = settings.get('fullscreen_lyrics_visible', False)
        self.setWindowTitle("Aiiko Music")
        self.setWindowIcon(QIcon(ICON_FILE))
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("FullScreenPlayer")
        self.setMouseTracking(True)
        self.installEventFilter(self)
        self._current_bg_color = QColor("#0A0A0F")
        self.bg_anim = QVariantAnimation(self)
        self.bg_anim.setDuration(1500)                       
        self.bg_anim.valueChanged.connect(self._on_bg_anim_update)
        self._build_ui()
        try:
            if VisualizerWidget:
                self.visualizer = VisualizerWidget(self.player.audio_engine, parent=self)
                self.visualizer.lower()
                self.visualizer.setVisible(False)
            else:
                self.visualizer = None
        except Exception as e:
            import logging
            logging.error(f"Error instanciando visualizer overlay: {e}")
            self.visualizer = None
        self._setup_idle_timer()
        self._setup_shortcuts()
    def _on_bg_anim_update(self, color):
        self._current_bg_color = color
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, self._current_bg_color)
        gradient.setColorAt(1.0, QColor("#060608"))
        painter.fillRect(self.rect(), gradient)
        painter.end()
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.header_widget = QWidget()
        self.header_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        header = QHBoxLayout(self.header_widget)
        header.setContentsMargins(30, 20, 30, 0)
        header.addStretch()
        self.btn_translate_lyrics = TransparentToolButton()
        self.btn_translate_lyrics.setIcon(self.player.playback_ui_controller._get_icon("translate_lyrics.svg", FIF.LANGUAGE, '#FFFFFF'))
        self.btn_translate_lyrics.setIconSize(QSize(22, 22))
        self.btn_translate_lyrics.setToolTip(tr("Traductor: Original"))
        self.btn_translate_lyrics.clicked.connect(self._toggle_lyrics_translation)
        self.btn_toggle_lyrics = TransparentToolButton()
        self.btn_toggle_lyrics.setIcon(self.player.playback_ui_controller._get_icon("hide_lyrics.svg", FIF.ALIGNMENT, '#FFFFFF'))
        self.btn_toggle_lyrics.setIconSize(QSize(22, 22))
        self.btn_toggle_lyrics.setToolTip(tr("Mostrar/Ocultar Letras"))
        self.btn_toggle_lyrics.clicked.connect(self._toggle_lyrics)
        self.btn_exit = TransparentToolButton()
        self.btn_exit.setIcon(self.player.playback_ui_controller._get_icon("close.svg", FIF.CLOSE))
        self.btn_exit.setIconSize(QSize(22, 22))
        self.btn_exit.setToolTip(tr("Cerrar (ESC)"))
        self.btn_exit.clicked.connect(self.player.navigation_controller.toggle_fullscreen)
        header.addWidget(self.btn_translate_lyrics)
        header.addSpacing(5)
        header.addWidget(self.btn_toggle_lyrics)
        header.addSpacing(5)
        header.addWidget(self.btn_exit)
        root.addWidget(self.header_widget)
        self.center_layout = QHBoxLayout()
        self.center_layout.setContentsMargins(50, 20, 50, 20)
        self.center_layout.setSpacing(40)
        self.left_container = QWidget()
        self.left_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.left_container.setMaximumWidth(600)
        self.left_container.setMinimumWidth(300)
        self.left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cover_panel = QVBoxLayout(self.left_container)
        cover_panel.setContentsMargins(0, 0, 0, 0)
        cover_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover = FullScreenCover()
        self.cover.pixmapChanged.connect(self.update_dynamic_bg)
        self.shadow = QGraphicsDropShadowEffect(self.cover)
        self.shadow.setBlurRadius(60)
        self.shadow.setColor(QColor(0, 0, 0, 150))
        self.shadow.setOffset(0, 15)
        self.cover.setGraphicsEffect(self.shadow)
        cover_panel.addStretch(1)
        cover_panel.addWidget(self.cover, stretch=10)
        cover_panel.addSpacing(30)
        self.title = MarqueeLabel("Aiiko Music")
        self.title.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.title.setStyleSheet("font-size: 32px; font-weight: bold; color: #FFFFFF;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFixedHeight(50)
        self.artist = QLabel("Selecciona una pista")
        self.artist.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.artist.setStyleSheet("font-size: 16px; color: #999999;")
        self.artist.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artist.setFixedHeight(28)
        cover_panel.addWidget(self.title)
        cover_panel.addWidget(self.artist)
        cover_panel.addStretch(1)
        self.center_layout.addWidget(self.left_container, 1)
        self.lyrics_panel = QListWidget()
        self.lyrics_panel.setObjectName("FullscreenLyrics")
        self.lyrics_panel.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.lyrics_panel.verticalScrollBar().setSingleStep(15)
        self.lyrics_panel.setWordWrap(True)
        self.lyrics_panel.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lyrics_panel.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lyrics_panel.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.lyrics_panel.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.lyrics_panel.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: transparent;
                border: none;
                padding: 4px 0px;
            }
            QListWidget::item:selected {
                background-color: transparent;
            }
        """)
        self.lyrics_panel.setContentsMargins(20, 0, 20, 0)
        self.lyrics_panel.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lyrics_panel.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.lyrics_manager = LyricsManager(self.lyrics_panel)
        if hasattr(self.player, 'apply_smooth_scroll'):
            self.player.apply_smooth_scroll(self.lyrics_panel, step=100)
        self.center_layout.addWidget(self.lyrics_panel, 1)
        self.lyrics_panel.setVisible(self._lyrics_visible)
        if self._lyrics_visible:
            accent = theme_manager.get_current_accent_hex()
            self.btn_toggle_lyrics.setIcon(self.player.playback_ui_controller._get_icon("hide_lyrics.svg", FIF.ALIGNMENT, accent))
            self.btn_toggle_lyrics.setToolTip(tr("Ocultar Letras"))
        else:
            self.btn_toggle_lyrics.setToolTip(tr("Mostrar Letras"))
        root.addLayout(self.center_layout, 1)
        self._update_center_visibility()
        self.bottom = QWidget()
        self.bottom.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.bottom.setFixedHeight(120)
        bottom_layout = QVBoxLayout(self.bottom)
        bottom_layout.setContentsMargins(120, 0, 120, 30)
        bottom_layout.setSpacing(10)
        prog_layout = QHBoxLayout()
        prog_layout.setSpacing(12)
        self.time_curr = QLabel("0:00")
        self.time_curr.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.time_curr.setStyleSheet("color: #888; font-size: 13px;")
        self.time_curr.setFixedWidth(50)
        self.time_curr.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.slider = Slider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderMoved.connect(self._on_slider_moved)
        self.slider.sliderReleased.connect(self._on_slider_released)
        self.slider.installEventFilter(self)
        self.time_tot = QLabel("0:00")
        self.time_tot.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.time_tot.setStyleSheet("color: #888; font-size: 13px;")
        self.time_tot.setFixedWidth(50)
        self.time_tot.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        prog_layout.addWidget(self.time_curr)
        prog_layout.addWidget(self.slider)
        prog_layout.addWidget(self.time_tot)
        bottom_layout.addLayout(prog_layout)
        btn_container = QHBoxLayout()
        left_space = QWidget()
        left_space.setFixedWidth(180)
        btn_container.addWidget(left_space)
        btn_container.addStretch()
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(50)
        self.btn_shuffle = TransparentToolButton()
        self.btn_shuffle.setIconSize(QSize(26, 26))
        self.btn_shuffle.clicked.connect(self.player.queue_controller.toggle_shuffle)
        self.btn_prev = TransparentToolButton()
        self.btn_prev.setIcon(self.player.playback_ui_controller._get_icon("prev.svg", ICON_PREV))
        self.btn_prev.setIconSize(QSize(36, 36))
        self.btn_prev.clicked.connect(lambda: self.player.playback_controller.prev_track(manual=True))
        self.btn_play = TransparentToolButton()
        self.btn_play.setIcon(self.player.playback_ui_controller._get_icon("play.svg", ICON_PLAY))
        self.btn_play.setIconSize(QSize(70, 70))
        self.btn_play.clicked.connect(self.player.playback_controller.toggle_play)
        self.btn_next = TransparentToolButton()
        self.btn_next.setIcon(self.player.playback_ui_controller._get_icon("next.svg", ICON_NEXT))
        self.btn_next.setIconSize(QSize(36, 36))
        self.btn_next.clicked.connect(lambda: self.player.playback_controller.next_track(manual=True))
        self.btn_repeat = TransparentToolButton()
        self.btn_repeat.setIconSize(QSize(26, 26))
        self.btn_repeat.clicked.connect(self.player.queue_controller.toggle_repeat)
        btn_layout.addWidget(self.btn_shuffle)
        btn_layout.addWidget(self.btn_prev)
        btn_layout.addWidget(self.btn_play)
        btn_layout.addWidget(self.btn_next)
        btn_layout.addWidget(self.btn_repeat)
        btn_container.addLayout(btn_layout)
        btn_container.addStretch()
        vol_layout = QHBoxLayout()
        vol_layout.setContentsMargins(0, 0, 0, 0)
        vol_layout.setSpacing(10)
        vol_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.vol_icon = TransparentToolButton()
        self.vol_icon.setIconSize(QSize(26, 26))
        self.vol_icon.setIcon(self.player.playback_ui_controller._get_icon("volume.svg", ICON_VOLUME))
        self.vol_icon.clicked.connect(self.player.player_controller.toggle_mute)
        self.vol_slider = Slider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(settings.get('volume', 80))
        self.vol_slider.setFixedWidth(100)
        self.vol_slider.valueChanged.connect(self.player.player_controller.set_volume)
        self.player.mini_volume_inline.valueChanged.connect(self.vol_slider.setValue)
        self.vol_slider.valueChanged.connect(self.player.mini_volume_inline.setValue)
        vol_layout.addWidget(self.vol_icon)
        vol_layout.addWidget(self.vol_slider)
        vol_container = QWidget()
        vol_container.setFixedWidth(180)
        vol_container.setLayout(vol_layout)
        btn_container.addWidget(vol_container)
        bottom_layout.addLayout(btn_container)
        root.addWidget(self.bottom)
    def _setup_idle_timer(self):
        self.header_opacity = QGraphicsOpacityEffect(self.header_widget)
        self.header_widget.setGraphicsEffect(self.header_opacity)
        self.bottom_opacity = QGraphicsOpacityEffect(self.bottom)
        self.bottom.setGraphicsEffect(self.bottom_opacity)
        self.anim_group = QParallelAnimationGroup()
        self.anim_header = QPropertyAnimation(self.header_opacity, b"opacity")
        self.anim_header.setDuration(300)
        self.anim_bottom = QPropertyAnimation(self.bottom_opacity, b"opacity")
        self.anim_bottom.setDuration(300)
        self.anim_group.addAnimation(self.anim_header)
        self.anim_group.addAnimation(self.anim_bottom)
        self.idle_timer = QTimer(self)
        self.idle_timer.setInterval(3000)
        self.idle_timer.timeout.connect(self._hide_controls)
        self.idle_timer.start()
    def _hide_controls(self):
        if self.header_opacity.opacity() == 0.0:
            return
        self.anim_group.stop()
        self.anim_header.setEndValue(0.0)
        self.anim_bottom.setEndValue(0.0)
        self.anim_group.start()
        self.setCursor(Qt.CursorShape.BlankCursor)
    def _show_controls(self):
        self.idle_timer.start()
        self.unsetCursor()
        if self.header_opacity.opacity() == 1.0:
            return
        if self.anim_group.state() == QAbstractAnimation.State.Running:
            if self.anim_header.endValue() == 1.0:
                return
        self.anim_group.stop()
        self.anim_header.setEndValue(1.0)
        self.anim_bottom.setEndValue(1.0)
        self.anim_group.start()
    def _setup_shortcuts(self):
        from PyQt6.QtGui import QShortcut, QKeySequence
        custom_shortcuts = settings.get('custom_shortcuts', {})
        key_esc = custom_shortcuts.get("esc", "Esc")
        key_space = custom_shortcuts.get("play_pause", "Space")
        key_l = custom_shortcuts.get("fs_lyrics", "L")
        key_t = custom_shortcuts.get("fs_translation", "T")
        key_p = custom_shortcuts.get("fs_visualizer", "P")
        key_c = custom_shortcuts.get("fs_cover", "C")
        self.sc_esc = QShortcut(QKeySequence(key_esc), self)
        self.sc_esc.activated.connect(self.player.navigation_controller.toggle_fullscreen)
        self.sc_space = QShortcut(QKeySequence(key_space), self)
        self.sc_space.activated.connect(self.player.playback_controller.toggle_play)
        self.sc_l = QShortcut(QKeySequence(key_l), self)
        self.sc_l.activated.connect(self._toggle_lyrics)
        self.sc_t = QShortcut(QKeySequence(key_t), self)
        self.sc_t.activated.connect(self._toggle_lyrics_translation)
        self.sc_p = QShortcut(QKeySequence(key_p), self)
        self.sc_p.activated.connect(self._toggle_visualizer)
        self.sc_c = QShortcut(QKeySequence(key_c), self)
        self.sc_c.activated.connect(self._toggle_cover)
        self.fs_shortcuts = {
            "esc": self.sc_esc,
            "play_pause": self.sc_space,
            "fs_lyrics": self.sc_l,
            "fs_translation": self.sc_t,
            "fs_visualizer": self.sc_p,
            "fs_cover": self.sc_c
        }
    def update_shortcut(self, action_id, new_key):
        if action_id in self.fs_shortcuts:
            from PyQt6.QtGui import QShortcut, QKeySequence
            self.fs_shortcuts[action_id].setEnabled(False)
            self.fs_shortcuts[action_id].setParent(None)
            self.fs_shortcuts[action_id].deleteLater()
            shortcut = QShortcut(QKeySequence(new_key), self)
            if action_id == "fs_lyrics":
                shortcut.activated.connect(self._toggle_lyrics)
            elif action_id == "fs_translation":
                shortcut.activated.connect(self._toggle_lyrics_translation)
            elif action_id == "fs_visualizer":
                shortcut.activated.connect(self._toggle_visualizer)
            elif action_id == "fs_cover":
                shortcut.activated.connect(self._toggle_cover)
            elif action_id == "esc":
                shortcut.activated.connect(self.player.navigation_controller.toggle_fullscreen)
            elif action_id == "play_pause":
                shortcut.activated.connect(self.player.playback_controller.toggle_play)
            self.fs_shortcuts[action_id] = shortcut
    def _toggle_visualizer(self):
        if hasattr(self, 'visualizer') and self.visualizer is not None:
            self.visualizer.setVisible(not self.visualizer.isVisible())
        else:
            from core.notification_manager import notify
            notify.warning("Visualizador No Disponible", "El motor del visualizador no pudo cargarse o faltan dependencias (Numpy).")
    def _toggle_cover(self):
        self._cover_visible = not getattr(self, '_cover_visible', True)
        self.left_container.setVisible(self._cover_visible)
        self._update_center_visibility()
    def _update_center_visibility(self):
        cover_vis = getattr(self, '_cover_visible', True)
        lyrics_vis = getattr(self, '_lyrics_visible', False)
        both_hidden = not cover_vis and not lyrics_vis
        if both_hidden:
            self.bg_anim.stop()
            self.bg_anim.setStartValue(self._current_bg_color)
            self.bg_anim.setEndValue(QColor("#030305"))                  
            self.bg_anim.start()
        else:
            if hasattr(self.player, 'queue') and self.player.queue.current_index >= 0:
                if self.player.queue.current_index < len(self.player.queue.tracks):
                    self.update_dynamic_bg(self.cover._original_pixmap if hasattr(self, 'cover') else None)
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseMove:
            self._show_controls()
        if obj == getattr(self, 'slider', None) and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton and not self.slider.isSliderDown():
                self._is_slider_pressed = True
                self.player.is_slider_pressed = True
                val = int(obj.minimum() + (obj.maximum() - obj.minimum()) * event.position().x() / obj.width())
                obj.setValue(val)
                total_ms = self.player.audio_engine.get_length()
                if total_ms > 0:
                    target_ms = int((val / 1000) * total_ms)
                    self.player.audio_engine.set_position(target_ms)
                QTimer.singleShot(300, self._allow_slider_update)
                return True
        return super().eventFilter(obj, event)
    def showEvent(self, event):
        super().showEvent(event)
        self._sync_shuffle_icon()
        self._sync_repeat_icon()
        if hasattr(self, 'idle_timer'): self.idle_timer.start()
    def hideEvent(self, event):
        super().hideEvent(event)
        if hasattr(self, 'idle_timer'): self.idle_timer.stop()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'visualizer'):
            self.visualizer.setGeometry(self.rect())
    def _toggle_lyrics(self):
        self._lyrics_visible = not getattr(self, '_lyrics_visible', False)
        settings.set('fullscreen_lyrics_visible', self._lyrics_visible)
        self.lyrics_panel.setVisible(self._lyrics_visible)
        self._update_center_visibility()
        import theme_manager
        if self._lyrics_visible:
            self.btn_toggle_lyrics.setToolTip(tr("Ocultar Letras"))
            accent = theme_manager.get_current_accent_hex()
            self.btn_toggle_lyrics.setIcon(self.player.playback_ui_controller._get_icon("hide_lyrics.svg", FIF.ALIGNMENT, accent))
        else:
            self.btn_toggle_lyrics.setToolTip(tr("Mostrar Letras"))
            self.btn_toggle_lyrics.setIcon(self.player.playback_ui_controller._get_icon("hide_lyrics.svg", FIF.ALIGNMENT, '#FFFFFF'))
    def _toggle_lyrics_translation(self):
        if not hasattr(self, 'lyrics_manager') or not self.lyrics_manager: return
        if not hasattr(self.lyrics_manager, 'display_mode'):
            self.lyrics_manager.display_mode = 'original'
        accent = theme_manager.get_current_accent_hex()
        if self.lyrics_manager.display_mode == 'original':
            self.lyrics_manager.display_mode = 'dual'
            self.btn_translate_lyrics.setToolTip(tr("Traductor: Dual"))
            self.btn_translate_lyrics.setIcon(self.player.playback_ui_controller._get_icon("translate_lyrics.svg", FIF.LANGUAGE, accent))
        elif self.lyrics_manager.display_mode == 'dual':
            self.lyrics_manager.display_mode = 'translated'
            self.btn_translate_lyrics.setToolTip(tr("Traductor: Solo Traducción"))
            self.btn_translate_lyrics.setIcon(self.player.playback_ui_controller._get_icon("translate_lyrics.svg", FIF.LANGUAGE, '#FFB900'))
        else:
            self.lyrics_manager.display_mode = 'original'
            self.btn_translate_lyrics.setToolTip(tr("Traductor: Original"))
            self.btn_translate_lyrics.setIcon(self.player.playback_ui_controller._get_icon("translate_lyrics.svg", FIF.LANGUAGE, '#FFFFFF'))
        self.lyrics_manager.update_display()
    def update_dynamic_bg(self, pixmap):
        if not pixmap or pixmap.isNull():
            new_color = QColor("#0A0A0F")
        else:
            try:
                img_path = getattr(self, '_current_track', None).cover_path if hasattr(self, '_current_track') else None
                loaded_from_disk = False
                from PyQt6.QtGui import QImage
                if img_path:
                    import hashlib
                    import os
                    from config import CACHE_DIR
                    file_hash = hashlib.md5(img_path.encode('utf-8')).hexdigest()
                    thumb_65 = os.path.join(CACHE_DIR, "thumbnails", f"{file_hash}_65.jpg")
                    thumb_450 = os.path.join(CACHE_DIR, "thumbnails", f"{file_hash}_450.jpg")
                    if os.path.exists(thumb_65):
                        img = QImage(thumb_65)
                        loaded_from_disk = not img.isNull()
                    elif os.path.exists(thumb_450):
                        img = QImage(thumb_450)
                        loaded_from_disk = not img.isNull()
                if loaded_from_disk:
                    scaled = img.scaled(1, 1, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
                    avg_color = scaled.pixelColor(0, 0)
                    new_color = avg_color.darker(250)
                else:
                    if img_path and os.path.exists(img_path):
                        img = QImage(img_path)
                        scaled = img.scaled(1, 1, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
                        avg_color = scaled.pixelColor(0, 0)
                        new_color = avg_color.darker(250)
                    else:
                        new_color = QColor("#0A0A0F")
            except Exception as e:
                import logging
                logging.debug(f"Error extrayendo color fullscreen: {e}")
                new_color = QColor("#0A0A0F")
        self.bg_anim.stop()
        self.bg_anim.setStartValue(self._current_bg_color)
        self.bg_anim.setEndValue(new_color)
        self.bg_anim.start()
    def _on_slider_pressed(self):
        self._is_slider_pressed = True
        self.player.is_slider_pressed = True
    def _on_slider_moved(self, value):
        length = self.player.audio_engine.get_length()
        if length > 0:
            ms = int((value / 1000) * length)
            formatted = self.player.playback_ui_controller.format_time(ms)
            self.time_curr.setText(formatted)
            self.slider.setToolTip(formatted)
    def _on_slider_released(self):
        self._is_slider_pressed = False
        self.player.is_slider_pressed = False
        length = self.player.audio_engine.get_length()
        if length > 0:
            ms = int((self.slider.value() / 1000) * length)
            self.player.audio_engine.set_position(ms)
        QTimer.singleShot(300, self._allow_slider_update)
    def _allow_slider_update(self):
        self._is_slider_pressed = False
        self.player.is_slider_pressed = False
    def update_metadata(self, track, pixmap, is_playing):
        self._current_track = track
        self.title.setText(track.title)
        self.artist.setText(f"{track.artist} — {track.album}")
        if pixmap and not pixmap.isNull():
            self.cover.setPixmap(pixmap)
        else:
            self.cover.setPixmap(QPixmap())
        self.update_play_state(is_playing)
        self.lyrics_manager.load(track)
        self.update_dynamic_bg(pixmap)
    def update_play_state(self, is_playing):
        if is_playing:
            self.btn_play.setIcon(self.player.playback_ui_controller._get_icon("pause.svg", ICON_PAUSE))
        else:
            self.btn_play.setIcon(self.player.playback_ui_controller._get_icon("play.svg", ICON_PLAY))
    def update_progress(self, curr_ms, total_ms):
        if not self._is_slider_pressed and total_ms > 0:
            self.slider.setValue(int((curr_ms / total_ms) * 1000))
            formatted = self.player.playback_ui_controller.format_time(curr_ms)
            self.time_curr.setText(formatted)
            self.slider.setToolTip(formatted)
        self.time_tot.setText(self.player.playback_ui_controller.format_time(total_ms))
        if (hasattr(self.player, 'queue') and self.player.queue.tracks
                and 0 <= self.player.queue.current_index < len(self.player.queue.tracks)):
            track = self.player.queue.tracks[self.player.queue.current_index]
            self.lyrics_manager.sync(curr_ms, track)
    def _sync_shuffle_icon(self):
        accent = theme_manager.get_current_accent_hex()
        color = accent if self.player.queue.is_shuffled else '#FFFFFF'
        self.btn_shuffle.setIcon(
            self.player.playback_ui_controller._get_icon("shuffle.svg", ICON_SHUFFLE, color))
    def _sync_repeat_icon(self):
        accent = theme_manager.get_current_accent_hex()
        mode = self.player.queue.repeat_mode
        if mode == 0:
            self.btn_repeat.setIcon(
                self.player.playback_ui_controller._get_icon("repeat_off.svg", ICON_REPEAT, '#FFFFFF'))
        elif mode == 1:
            self.btn_repeat.setIcon(
                self.player.playback_ui_controller._get_icon("repeat.svg", ICON_REPEAT, accent))
        else:
            self.btn_repeat.setIcon(
                self.player.playback_ui_controller._get_icon("repeat1.svg", ICON_REPEAT, '#FFB900'))