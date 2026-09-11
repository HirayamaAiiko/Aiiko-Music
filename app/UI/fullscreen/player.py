import logging
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QIcon
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QSizePolicy, QListWidget, QAbstractItemView)
from qfluentwidgets import TransparentToolButton, Slider, FluentIcon as FIF
from config import ICON_FILE, ICON_PREV, ICON_PLAY, ICON_NEXT, ICON_VOLUME
from widgets import MarqueeLabel
from core.language_manager import tr
from settings_manager import settings
import theme_manager
from services.lyrics_service import LyricsManager
from .components import FullScreenCover, FullScreenSlider, ShortcutsOverlay
from .background import FullScreenBackgroundMixin
from .interactions import FullScreenInteractionsMixin
from .metadata import FullScreenMetadataMixin
try:
    from UI.visualizer.widget import VisualizerWidget
except ImportError as e:
    logging.warning(f"No se pudo cargar el visualizador (probablemente falte numpy): {e}")
    VisualizerWidget = None
class FullScreenPlayer(FullScreenBackgroundMixin, FullScreenInteractionsMixin, FullScreenMetadataMixin, QWidget):
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
        self._init_background()
        self._build_ui()
        self._init_interactions()
        try:
            if VisualizerWidget:
                self.visualizer = VisualizerWidget(self.player.audio_engine, parent=self)
                self.visualizer.lower()
                self.visualizer.setVisible(False)
            else:
                self.visualizer = None
        except Exception as e:
            logging.error(f"Error instanciando visualizer overlay: {e}")
            self.visualizer = None
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, self._current_bg_color)
        gradient.setColorAt(1.0, QColor("#060608"))
        painter.fillRect(self.rect(), gradient)
        painter.end()
    def closeEvent(self, event):
        try:
            self.player.mini_volume_inline.valueChanged.disconnect(self.vol_slider.setValue)
        except TypeError:
            pass
        super().closeEvent(event)
    def eventFilter(self, obj, event):
        if obj == self.btn_info:
            from PyQt6.QtCore import QEvent
            if event.type() == QEvent.Type.Enter:
                self.shortcuts_overlay.refresh_shortcuts()
                self.shortcuts_overlay.show()
                pos = self.btn_info.mapTo(self, self.btn_info.rect().bottomLeft())
                x = pos.x() - self.shortcuts_overlay.width() + self.btn_info.width()
                self.shortcuts_overlay.move(x, pos.y() + 10)
                self.shortcuts_overlay.raise_()
                return True
            elif event.type() == QEvent.Type.Leave:
                self.shortcuts_overlay.hide()
                return True
        return super().eventFilter(obj, event)
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.header_widget = QWidget()
        self.header_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        header = QHBoxLayout(self.header_widget)
        header.setContentsMargins(30, 20, 30, 0)
        header.addStretch()
        self.btn_info = TransparentToolButton()
        self.btn_info.setIcon(self.player.playback_ui_controller._get_icon("info.svg", FIF.INFO, '#FFFFFF'))
        self.btn_info.setIconSize(QSize(22, 22))
        self.btn_info.setToolTip("Atajos de teclado")
        self.btn_info.installEventFilter(self)
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
        header.addWidget(self.btn_info)
        header.addSpacing(5)
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
        self.center_logo_label = QLabel()
        self.center_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_logo_label.setVisible(False)
        self.center_layout.addWidget(self.center_logo_label, 1)
        self._init_center_logo()
        self.lyrics_panel.setVisible(self._lyrics_visible)
        if self._lyrics_visible:
            accent = theme_manager.get_current_accent_hex()
            self.btn_toggle_lyrics.setIcon(self.player.playback_ui_controller._get_icon("hide_lyrics.svg", FIF.ALIGNMENT, accent))
            self.btn_toggle_lyrics.setToolTip(tr("Ocultar Letras"))
        else:
            self.btn_toggle_lyrics.setToolTip(tr("Mostrar Letras"))
        root.addLayout(self.center_layout, 1)
        self.shortcuts_overlay = ShortcutsOverlay(self)
        self.shortcuts_overlay.hide()
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
        self.slider = FullScreenSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderMoved.connect(self._on_slider_moved)
        self.slider.sliderReleased.connect(self._on_slider_released)
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
    def _init_center_logo(self):
        from config import APP_ROOT
        import os
        from PyQt6.QtSvg import QSvgRenderer
        from PyQt6.QtGui import QPixmap, QPainter
        logo_svg = os.path.join(APP_ROOT, "resources", "app", "logo_full.svg")
        if os.path.exists(logo_svg):
            svg = QSvgRenderer(logo_svg)
            if svg.isValid():
                size = 300
                pix = QPixmap(size, size)
                pix.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pix)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                svg.render(painter)
                painter.end()
                self.center_logo_label.setPixmap(pix)