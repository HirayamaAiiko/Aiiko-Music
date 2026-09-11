from PyQt6.QtCore import Qt, QSize, QObject, QEvent
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QAbstractItemView, QSizePolicy, QLabel)
from PyQt6.QtGui import QPainter, QColor
from qfluentwidgets import (TransparentToolButton, FluentIcon as FIF)
from widgets import MarqueeLabel, MarqueeHtmlLabel, AspectRatioLabel
from services.lyrics_service import LyricsManager
from core.language_manager import tr
import theme_manager
class BadgeLabel(QLabel):
    def __init__(self, text="", bg_color=QColor(255, 255, 255, 20), parent=None):
        super().__init__(text, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.bg_color = bg_color
    def set_bg_color(self, color: QColor):
        self.bg_color = color
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.bg_color)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 6.0, 6.0)
        painter.end()
        super().paintEvent(event)
class NowPlayingView(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.setObjectName("NowPlayingPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui(player)
    def _build_ui(self, player):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        player.btn_timer = TransparentToolButton()
        player.btn_timer.setIcon(player.playback_ui_controller._get_icon("timer.svg", FIF.IOT, '#FFFFFF'))
        player.btn_timer.setIconSize(QSize(22, 22))
        player.btn_timer.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.btn_timer.setToolTip(tr("Temporizador"))
        player.btn_timer.clicked.connect(player.lyrics_ui_controller.show_timer_menu)
        player.btn_edit_lyrics = TransparentToolButton()
        player.btn_edit_lyrics.setIcon(player.playback_ui_controller._get_icon("edit_lyrics.svg", FIF.EDIT, '#FFFFFF'))
        player.btn_edit_lyrics.setIconSize(QSize(22, 22))
        player.btn_edit_lyrics.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.btn_edit_lyrics.setToolTip(tr("Buscar y Editar Letras"))
        player.btn_edit_lyrics.clicked.connect(player.lyrics_ui_controller.open_lyrics_editor)
        player.btn_translate_lyrics = TransparentToolButton()
        player.btn_translate_lyrics.setIcon(player.playback_ui_controller._get_icon("translate_lyrics.svg", FIF.LANGUAGE, '#FFFFFF'))
        player.btn_translate_lyrics.setIconSize(QSize(22, 22))
        player.btn_translate_lyrics.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.btn_translate_lyrics.setToolTip(tr("Traducir Letras"))
        player.btn_translate_lyrics.clicked.connect(player.lyrics_ui_controller.toggle_lyrics_translation)
        player.btn_info = TransparentToolButton()
        player.btn_info.setIcon(player.playback_ui_controller._get_icon("info.svg", FIF.INFO, '#FFFFFF'))
        player.btn_info.setIconSize(QSize(22, 22))
        player.btn_info.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.btn_info.setToolTip(tr("Información y Metadata"))
        def _open_current_metadata():
            if player.queue.tracks and 0 <= player.queue.current_index < len(player.queue.tracks):
                track = player.queue.tracks[player.queue.current_index]
                player.app_controller.edit_track_metadata(track)
        player.btn_info.clicked.connect(_open_current_metadata)
        player.btn_lyrics_toggle = TransparentToolButton()
        player.btn_lyrics_toggle.setIcon(player.playback_ui_controller._get_icon("hide_lyrics.svg", FIF.ALIGNMENT, '#FFFFFF'))
        player.btn_lyrics_toggle.setIconSize(QSize(22, 22))
        player.btn_lyrics_toggle.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        player.btn_lyrics_toggle.setToolTip(tr("Ocultar Letras"))
        player.btn_lyrics_toggle.clicked.connect(player.lyrics_ui_controller.toggle_lyrics)
        class ToolBtnHoverFilter(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Type.Enter:
                    accent = theme_manager.get_current_accent_hex()
                    hover_color = accent
                    if obj == player.btn_translate_lyrics:
                        mode = getattr(player.lyrics_manager, 'display_mode', 'original') if hasattr(player, 'lyrics_manager') else 'original'
                        if mode == 'translated':
                            hover_color = '#FFB900'
                    if hasattr(obj, '_label'):
                        obj._label.setStyleSheet(f"color: {hover_color}; font-size: 11px; font-weight: 500;")
                    if obj == player.btn_info:
                        obj.setIcon(player.playback_ui_controller._get_icon("info.svg", FIF.INFO, hover_color))
                    elif obj == player.btn_timer:
                        from config import ICON_TIMER
                        obj.setIcon(player.playback_ui_controller._get_icon("timer.svg", ICON_TIMER, hover_color))
                    elif obj == player.btn_edit_lyrics:
                        obj.setIcon(player.playback_ui_controller._get_icon("edit_lyrics.svg", FIF.EDIT, hover_color))
                    elif obj == player.btn_translate_lyrics:
                        obj.setIcon(player.playback_ui_controller._get_icon("translate_lyrics.svg", FIF.LANGUAGE, hover_color))
                    elif obj == player.btn_lyrics_toggle:
                        obj.setIcon(player.playback_ui_controller._get_icon("hide_lyrics.svg", FIF.ALIGNMENT, hover_color))
                elif event.type() == QEvent.Type.Leave:
                    if obj == player.btn_info:
                        player.playback_ui_controller.update_tool_btn_state(obj, "info.svg", FIF.INFO, '#FFFFFF')
                    elif obj == player.btn_timer:
                        from config import ICON_TIMER
                        is_active = hasattr(player, 'sleep_timer_controller') and player.sleep_timer_controller.is_active()
                        color = theme_manager.get_current_accent_hex() if is_active else '#FFFFFF'
                        player.playback_ui_controller.update_tool_btn_state(obj, "timer.svg", ICON_TIMER, color)
                    elif obj == player.btn_edit_lyrics:
                        player.playback_ui_controller.update_tool_btn_state(obj, "edit_lyrics.svg", FIF.EDIT, '#FFFFFF')
                    elif obj == player.btn_translate_lyrics:
                        mode = getattr(player.lyrics_manager, 'display_mode', 'original') if hasattr(player, 'lyrics_manager') else 'original'
                        color = theme_manager.get_current_accent_hex() if mode == 'dual' else ('#FFB900' if mode == 'translated' else '#FFFFFF')
                        player.playback_ui_controller.update_tool_btn_state(obj, "translate_lyrics.svg", FIF.LANGUAGE, color)
                    elif obj == player.btn_lyrics_toggle:
                        is_active = getattr(player, 'show_lyrics', True)
                        color = theme_manager.get_current_accent_hex() if is_active else '#FFFFFF'
                        player.playback_ui_controller.update_tool_btn_state(obj, "hide_lyrics.svg", FIF.ALIGNMENT, color)
                return False
        player._hover_filter = ToolBtnHoverFilter(player)
        player.btn_info.installEventFilter(player._hover_filter)
        player.btn_timer.installEventFilter(player._hover_filter)
        player.btn_edit_lyrics.installEventFilter(player._hover_filter)
        player.btn_translate_lyrics.installEventFilter(player._hover_filter)
        player.btn_lyrics_toggle.installEventFilter(player._hover_filter)
        def create_labeled_btn(btn, text):
            container = QWidget()
            lyt = QVBoxLayout(container)
            lyt.setContentsMargins(5, 0, 5, 0)
            lyt.setSpacing(2)
            lyt.addWidget(btn, 0, Qt.AlignmentFlag.AlignHCenter)
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #A0A0A0; font-size: 11px; font-weight: 500;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn._label = lbl
            lyt.addWidget(lbl, 0, Qt.AlignmentFlag.AlignHCenter)
            return container
        top_layout.addWidget(create_labeled_btn(player.btn_info, tr("Info")))
        top_layout.addWidget(create_labeled_btn(player.btn_timer, tr("Tiempo")))
        top_layout.addWidget(create_labeled_btn(player.btn_edit_lyrics, tr("Editor")))
        top_layout.addWidget(create_labeled_btn(player.btn_translate_lyrics, tr("Traducir")))
        top_layout.addWidget(create_labeled_btn(player.btn_lyrics_toggle, tr("Letras")))
        layout.addLayout(top_layout)
        center_layout = QHBoxLayout()
        left_container = QWidget()
        left_container.setMaximumWidth(500)
        left_container.setMinimumWidth(250)
        left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cover_panel = QVBoxLayout(left_container)
        cover_panel.setContentsMargins(0, 0, 0, 0)
        cover_panel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        player.full_cover = AspectRatioLabel()
        player.full_cover.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        player.full_title = MarqueeLabel("Aiiko Music")
        player.full_title.setStyleSheet("font-size: 28px; font-weight: bold; background: transparent;")
        player.full_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player.full_title.setFixedHeight(45)
        player.full_artist = MarqueeHtmlLabel(tr("Selecciona una pista"))
        player.full_artist.linkActivated.connect(player.navigation_controller.handle_now_playing_link)
        player.full_artist.setStyleSheet("font-size: 14px; background: transparent;")
        player.full_artist.setFixedHeight(22)
        player.info_layout = QHBoxLayout()
        player.info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player.info_layout.setSpacing(10)
        badge_style = """
            QLabel {
                background: transparent;
                padding: 4px 8px;
                font-size: 11px;
                color: #A0A0A0;
            }
        """
        player.lbl_file_type = BadgeLabel("---")
        player.lbl_file_type.setStyleSheet(badge_style)
        player.lbl_file_type.hide()
        player.lbl_bitrate = BadgeLabel("---")
        player.lbl_bitrate.setStyleSheet(badge_style)
        player.lbl_bitrate.hide()
        player.lbl_samplerate = BadgeLabel("---")
        player.lbl_samplerate.setStyleSheet(badge_style)
        player.lbl_samplerate.hide()
        player.lbl_hq = BadgeLabel("HQ", bg_color=QColor(147, 112, 219, 51))                           
        player.lbl_hq.setStyleSheet("""
            QLabel {
                background: transparent;
                padding: 4px 8px;
                font-size: 11px;
                color: #DDA0DD;
                font-weight: bold;
            }
        """)
        player.lbl_hq.hide()
        player.btn_favorite_np = TransparentToolButton()
        player.btn_favorite_np.setIcon(FIF.HEART)
        player.btn_favorite_np.setFixedSize(32, 32)
        player.btn_favorite_np.setIconSize(QSize(24, 24))
        player.btn_favorite_np.clicked.connect(player.app_controller.toggle_favorite)
        player.info_layout.addWidget(player.lbl_file_type)
        player.info_layout.addWidget(player.lbl_bitrate)
        player.info_layout.addWidget(player.lbl_samplerate)
        player.info_layout.addWidget(player.lbl_hq)
        player.info_layout.addWidget(player.btn_favorite_np)
        cover_panel.addStretch(1)
        cover_panel.addWidget(player.full_cover, stretch=10)
        cover_panel.addSpacing(15)
        cover_panel.addWidget(player.full_title)
        cover_panel.addWidget(player.full_artist)
        cover_panel.addSpacing(10)
        cover_panel.addLayout(player.info_layout)
        cover_panel.addStretch(1)
        left_wrapper = QHBoxLayout()
        left_wrapper.addStretch(1)
        left_wrapper.addWidget(left_container, 2)
        left_wrapper.addStretch(1)
        center_layout.addLayout(left_wrapper, 1)
        player.lyrics_panel = QListWidget()
        player.lyrics_panel.setObjectName("LyricsList")
        player.lyrics_panel.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        player.lyrics_panel.verticalScrollBar().setSingleStep(15)
        player.lyrics_panel.setWordWrap(True)
        player.lyrics_panel.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        player.lyrics_panel.setResizeMode(QListWidget.ResizeMode.Adjust)
        if hasattr(player, 'apply_smooth_scroll'):
            player.apply_smooth_scroll(player.lyrics_panel, step=100)
        player.lyrics_manager = LyricsManager(player.lyrics_panel)
        center_layout.addWidget(player.lyrics_panel, 1)
        layout.addLayout(center_layout, 1)
        player.lyrics_panel.setVisible(player.show_lyrics)
        import theme_manager
        if player.show_lyrics:
            accent = theme_manager.get_current_accent_hex()
            player.btn_lyrics_toggle.setIcon(player.playback_ui_controller._get_icon("hide_lyrics.svg", FIF.ALIGNMENT, accent))
            player.btn_lyrics_toggle.setToolTip(tr("Ocultar Letras"))
        else:
            player.btn_lyrics_toggle.setToolTip(tr("Mostrar Letras"))