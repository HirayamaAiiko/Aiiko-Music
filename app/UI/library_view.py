from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QSizePolicy)
from qfluentwidgets import (TitleLabel, SearchLineEdit, ComboBox, TransparentToolButton)
from config import ICON_GRID
from widgets import CustomLibraryTabs
from core.language_manager import tr
class LibraryView(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.setObjectName("PageContent")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.player = player
        self._build_ui(player)
    def _build_ui(self, player):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 10, 30, 0)
        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)
        title_lbl = TitleLabel(tr("Mi Biblioteca"))
        header_layout.addWidget(title_lbl)
        header_layout.addSpacing(12)
        from PyQt6.QtWidgets import QFrame
        v_line = QFrame()
        v_line.setFrameShape(QFrame.Shape.VLine)
        v_line.setStyleSheet("color: rgba(255, 255, 255, 0.1); margin-top: 5px; margin-bottom: 5px;")
        header_layout.addWidget(v_line)
        header_layout.addSpacing(12)
        player.pivot = CustomLibraryTabs(player)
        header_layout.addWidget(player.pivot)
        header_layout.setAlignment(player.pivot, Qt.AlignmentFlag.AlignVCenter)
        header_layout.addStretch()
        player.search_bar = SearchLineEdit()
        from PyQt6.QtCore import QSize
        player.search_bar.searchButton.setIconSize(QSize(14, 14))
        player.search_bar.clearButton.setIconSize(QSize(14, 14))
        player.search_bar.setPlaceholderText(tr("Buscar canción, artista, álbum..."))
        player.search_bar.setFixedWidth(280)
        player.search_timer = QTimer(player)
        player.search_timer.setSingleShot(True)
        player.search_timer.timeout.connect(player.library_controller.apply_filter)
        player.search_bar.textChanged.connect(player.library_controller.filter_library)
        from qfluentwidgets import FluentIcon as FIF
        self.btn_search_icon = TransparentToolButton()
        self.btn_search_icon.setIcon(FIF.SEARCH)
        self.btn_search_icon.setToolTip(tr("Buscar"))
        self.btn_search_icon.hide()
        self.btn_search_icon.clicked.connect(self._on_search_icon_clicked)
        from PyQt6.QtGui import QColor
        player.pivot.lbl_count.setTextColor(QColor('#888888'), QColor('#888888'))
        font = player.pivot.lbl_count.font()
        font.setPixelSize(13)
        player.pivot.lbl_count.setFont(font)
        player.pivot.lbl_count.setContentsMargins(0, 0, 12, 0)
        header_layout.addWidget(player.pivot.lbl_count)
        header_layout.setAlignment(player.pivot.lbl_count, Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.btn_search_icon)
        header_layout.addWidget(player.search_bar)
        player.search_bar.installEventFilter(self)
        from UI.components.sort_filter_button import SortFilterButton
        player.sort_combo = SortFilterButton([
            tr("A-Z"), tr("Z-A"), tr("Artista"), tr("Álbum"), 
            tr("Año (Reciente)"), tr("Fecha Modificación"), 
            tr("Fecha de Creación (Reciente)"), tr("Fecha de Creación (Antiguo)"),
            tr("Favoritos"), tr("Duración (Mayor)"), tr("Duración (Menor)"),
            tr("ReplayGain")
        ])
        from settings_manager import settings
        sort_configs = settings.get('sort_configs', {})
        saved_idx = sort_configs.get('songs', 0)
        if 0 <= saved_idx < player.sort_combo.count():
            player.sort_combo.setCurrentIndex(saved_idx)
        player.sort_combo.currentIndexChanged.connect(player.library_controller.sort_current_tab)
        header_layout.addWidget(player.sort_combo)
        player.btn_view_mode = TransparentToolButton()
        player.btn_view_mode.setIcon(player.playback_ui_controller._get_icon("grid.svg", ICON_GRID))
        player.btn_view_mode.setToolTip(tr("Alternar Vista"))
        player.btn_view_mode.clicked.connect(player.library_controller.toggle_current_tab_view)
        header_layout.addWidget(player.btn_view_mode)
        layout.addWidget(self.header_widget)
        player.stacked_lib = QStackedWidget()
        class SimplePlaceholder(QWidget):
            def __init__(self):
                super().__init__()
                self.is_placeholder = True
                self.setStyleSheet("background: transparent;")
        from UI.library.songs_tab import SongsTab
        self.songs_tab = SongsTab(player)
        player.stacked_lib.addWidget(self.songs_tab)
        self.albums_tab = SimplePlaceholder()
        player.stacked_lib.addWidget(self.albums_tab)
        self.artists_tab = SimplePlaceholder()
        player.stacked_lib.addWidget(self.artists_tab)
        self.folders_tab = SimplePlaceholder()
        player.stacked_lib.addWidget(self.folders_tab)
        from qfluentwidgets import FluentIcon as FIF
        player.pivot.addItem('songs', tr('Canciones'), FIF.MUSIC, lambda: player.navigation_controller.switch_library_tab('songs', 0))
        player.pivot.addItem('albums', tr('Álbumes'), FIF.ALBUM, lambda: player.navigation_controller.switch_library_tab('albums', 1))
        player.pivot.addItem('artists', tr('Artistas'), FIF.PEOPLE, lambda: player.navigation_controller.switch_library_tab('artists', 2))
        player.pivot.addItem('folders', tr('Carpetas'), FIF.FOLDER, lambda: player.navigation_controller.switch_library_tab('folders', 3))
        player.pivot.setCurrentItem('songs')
        player.pivot.currentItemChanged.connect(self._update_view_mode_icon)
        layout.addWidget(player.stacked_lib)
        self.zero_state_widget = QWidget()
        self.zero_state_widget.hide()
        zero_layout = QVBoxLayout(self.zero_state_widget)
        zero_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zero_layout.setSpacing(20)
        from qfluentwidgets import IconWidget, PrimaryPushButton, BodyLabel
        zero_icon = IconWidget(FIF.FOLDER_ADD)
        zero_icon.setFixedSize(80, 80)
        zero_layout.addWidget(zero_icon, 0, Qt.AlignmentFlag.AlignCenter)
        zero_lbl = TitleLabel(tr("Bienvenido a tu Biblioteca"))
        zero_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zero_layout.addWidget(zero_lbl, 0, Qt.AlignmentFlag.AlignCenter)
        zero_desc = BodyLabel(tr("Aún no has configurado ninguna carpeta de música.\nAgrega tu carpeta principal para que la magia comience."))
        zero_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zero_desc.setStyleSheet("color: #888888; font-size: 14px;")
        zero_layout.addWidget(zero_desc, 0, Qt.AlignmentFlag.AlignCenter)
        btn_add_folder = PrimaryPushButton(tr("Agregar Carpeta de Música"))
        btn_add_folder.setFixedSize(220, 40)
        def on_add_clicked():
            self.player.app_controller.add_folder()
            self.check_zero_state()
        btn_add_folder.clicked.connect(on_add_clicked)
        zero_layout.addWidget(btn_add_folder, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.zero_state_widget)
        self.check_zero_state()
    def check_zero_state(self):
        from settings_manager import settings
        folders = settings.get("folders", [])
        if not folders:
            self.header_widget.hide()
            self.player.stacked_lib.hide()
            self.zero_state_widget.show()
        else:
            self.header_widget.show()
            self.player.stacked_lib.show()
            self.zero_state_widget.hide()
    def showEvent(self, event):
        super().showEvent(event)
        self.check_zero_state()
    def _update_view_mode_icon(self, routeKey):
        from config import ICON_LIST, ICON_GRID
        is_grid = True
        if routeKey == 'songs':
            is_grid = self.player.songs_is_grid
        elif routeKey == 'albums':
            is_grid = self.player.albums_is_grid
        elif routeKey == 'artists':
            is_grid = self.player.artists_is_grid
        elif routeKey == 'folders':
            is_grid = getattr(self.player, 'folders_is_grid', False)
        self.player.btn_view_mode.setIcon(
            self.player.playback_ui_controller._get_icon(
                "list.svg" if is_grid else "grid.svg", 
                ICON_LIST if is_grid else ICON_GRID
            )
        )
    def _on_search_icon_clicked(self):
        self.player.pivot.hide()
        self.btn_search_icon.hide()
        self.player.search_bar.show()
        self.player.search_bar.setFocus()
    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj == self.player.search_bar and event.type() == QEvent.Type.FocusOut:
            self._update_responsive_layout()
        return super().eventFilter(obj, event)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_responsive_layout()
    def _update_responsive_layout(self):
        is_compact_search = self.width() <= 1250
        is_compact_tabs = self.width() <= 930
        if hasattr(self.player.pivot, 'set_icon_mode'):
            self.player.pivot.set_icon_mode(is_compact_tabs)
        if is_compact_search:
            if not self.player.search_bar.text() and not self.player.search_bar.hasFocus():
                self.player.search_bar.hide()
                self.btn_search_icon.show()
                self.player.pivot.show()
            else:
                self.btn_search_icon.hide()
                self.player.pivot.hide()
                self.player.search_bar.show()
        else:
            self.player.search_bar.show()
            self.btn_search_icon.hide()
            self.player.pivot.show()