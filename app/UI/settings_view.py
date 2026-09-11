from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget
from qfluentwidgets import TitleLabel
from UI.components.custom_animated_tabs import CustomAnimatedTabs
from settings_manager import settings
from UI.settings_tabs import AppearanceTab, GeneralTab, PlaybackTab, LibraryTab, CacheTab, AboutTab, RemoteTab, ServicesTab
from UI.settings_tabs.shortcuts_tab import ShortcutsTab
from core.language_manager import tr
class SettingsView(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.setObjectName("PageContent")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.player = player
        self.tabs_to_load = [
            ('general', tr('General'), GeneralTab),
            ('appearance', tr('Apariencia'), AppearanceTab),
            ('playback', tr('Reproducción'), PlaybackTab),
            ('library', tr('Biblioteca'), LibraryTab),
            ('shortcuts', tr('Atajos'), ShortcutsTab),
            ('remote', tr('Control Remoto'), RemoteTab),
            ('services', tr('Servicios'), ServicesTab),
            ('cache', tr('Caché'), CacheTab),
            ('about', tr('Acerca de'), AboutTab)
        ]
        self.current_load_index = 0
        self._build_ui()
    def _build_ui(self):
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_stack = QStackedWidget(self)
        self.root_layout.addWidget(self.root_stack)
        from UI.components.loading_placeholder import LoadingPlaceholder
        self.inner_loader = LoadingPlaceholder("Cargando Ajustes...", use_glitch=False)
        self.root_stack.addWidget(self.inner_loader)
        self.content_page = QWidget(self)
        main_layout = QVBoxLayout(self.content_page)
        main_layout.setContentsMargins(40, 10, 40, 0)
        main_layout.addWidget(TitleLabel(tr("Ajustes")))
        main_layout.addSpacing(15)
        self.pivot = CustomAnimatedTabs(self.content_page)
        from UI.dashboard.components.dashboard_buttons import _CarouselArrowBtn
        from qfluentwidgets import SmoothScrollArea
        from UI.dashboard.components.dashboard_main_panel import _HorizontalDragFilter
        self.pivot_scroll = SmoothScrollArea()
        self.pivot_scroll.setWidgetResizable(True)
        self.pivot_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pivot_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pivot_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.pivot_scroll.viewport().setStyleSheet("background: transparent;")
        pivot_wrapper = QWidget()
        pivot_wrapper.setObjectName("pivot_wrapper")
        pivot_wrapper.setStyleSheet("QWidget#pivot_wrapper { background: transparent; }")
        pivot_wrapper_layout = QHBoxLayout(pivot_wrapper)
        pivot_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        pivot_wrapper_layout.addWidget(self.pivot, alignment=Qt.AlignmentFlag.AlignVCenter)
        pivot_wrapper_layout.addStretch()
        self.pivot_scroll.setWidget(pivot_wrapper)
        self.pivot_scroll.setFixedHeight(40)
        self.pivot_scroll.viewport().installEventFilter(_HorizontalDragFilter(self.pivot_scroll))
        from qfluentwidgets import ToolButton, FluentIcon as FIF
        btn_left  = ToolButton(FIF.LEFT_ARROW)
        btn_right = ToolButton(FIF.RIGHT_ARROW)
        btn_left.setFixedSize(32, 32)
        btn_right.setFixedSize(32, 32)
        btn_left.setStyleSheet("ToolButton { background: transparent; border: none; }")
        btn_right.setStyleSheet("ToolButton { background: transparent; border: none; }")
        btn_left.hide()
        btn_right.hide()
        def _update_arrows():
            if not getattr(self, '_fully_loaded', False): return
            hbar = self.pivot_scroll.horizontalScrollBar()
            max_val = hbar.maximum()
            needs_arrows = max_val > 0
            if needs_arrows != btn_left.isVisible():
                btn_left.setVisible(needs_arrows)
                btn_right.setVisible(needs_arrows)
            if needs_arrows:
                btn_left.setEnabled(hbar.value() > 0)
                btn_right.setEnabled(hbar.value() < max_val)
        self._update_arrows = _update_arrows
        self.pivot_scroll.horizontalScrollBar().valueChanged.connect(lambda _: _update_arrows())
        self.pivot_scroll.horizontalScrollBar().rangeChanged.connect(lambda *_: _update_arrows())
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, _update_arrows)
        def _smooth_scroll(target_val):
            hbar = self.pivot_scroll.horizontalScrollBar()
            if not hasattr(self.pivot_scroll, "_scroll_anim"):
                from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
                self.pivot_scroll._scroll_anim = QPropertyAnimation(hbar, b"value", self.pivot_scroll)
                self.pivot_scroll._scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                self.pivot_scroll._scroll_anim.setDuration(350)
            self.pivot_scroll._scroll_anim.stop()
            self.pivot_scroll._scroll_anim.setStartValue(hbar.value())
            self.pivot_scroll._scroll_anim.setEndValue(target_val)
            self.pivot_scroll._scroll_anim.start()
        _STEP = 150
        btn_left.clicked.connect(lambda: _smooth_scroll(max(0, self.pivot_scroll.horizontalScrollBar().value() - _STEP)))
        btn_right.clicked.connect(lambda: _smooth_scroll(min(self.pivot_scroll.horizontalScrollBar().maximum(), self.pivot_scroll.horizontalScrollBar().value() + _STEP)))
        pivot_container = QWidget()
        pivot_container.setFixedHeight(40)
        pivot_layout = QHBoxLayout(pivot_container)
        pivot_layout.setContentsMargins(0, 0, 0, 0)
        pivot_layout.setSpacing(5)
        pivot_layout.addWidget(btn_left, alignment=Qt.AlignmentFlag.AlignVCenter)
        pivot_layout.addWidget(self.pivot_scroll, 1, alignment=Qt.AlignmentFlag.AlignVCenter)
        pivot_layout.addWidget(btn_right, alignment=Qt.AlignmentFlag.AlignVCenter)
        main_layout.addWidget(pivot_container)
        main_layout.addSpacing(15)
        self.stacked_widget = QStackedWidget(self.content_page)
        main_layout.addWidget(self.stacked_widget)
        self.root_stack.addWidget(self.content_page)
        self.root_stack.setCurrentWidget(self.inner_loader)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(10, self._load_next_tab)
    def _load_next_tab(self):
        if self.current_load_index >= len(self.tabs_to_load):
            self._finish_loading()
            return
        key, name, cls = self.tabs_to_load[self.current_load_index]
        try:
            tab_instance = cls(self.player, self)
            setattr(self, f"tab_{key}", tab_instance)
            self.stacked_widget.addWidget(tab_instance)
            self.pivot.addItem(key, name, callback=lambda k=key, t=tab_instance: self.stacked_widget.setCurrentWidget(t))
        except Exception as e:
            import logging
            logging.error(f"Error cargando pestaña de ajustes '{key}': {e}")
        self.current_load_index += 1
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(20, self._load_next_tab)
    def _finish_loading(self):
        target = getattr(self.player, '_target_settings_tab', None) or getattr(self, 'target_tab_on_load', 'general')
        if hasattr(self.player, '_target_settings_tab'):
            delattr(self.player, '_target_settings_tab')
        self.pivot.setCurrentItem(target)
        if hasattr(self, f'tab_{target}'):
            self.stacked_widget.setCurrentWidget(getattr(self, f'tab_{target}'))
        self.root_stack.setCurrentWidget(self.content_page)
        if hasattr(self, 'inner_loader'):
            self.root_stack.removeWidget(self.inner_loader)
            self.inner_loader.deleteLater()
            delattr(self, 'inner_loader')
        if hasattr(self.player, 'settings_sync'):
            self.player.settings_sync.apply_settings_to_ui()
        if hasattr(self.player, 'settings_ui_controller'):
            self.player.settings_ui_controller.init_audio_settings_ui()
        self._fully_loaded = True
        if hasattr(self, '_update_arrows'):
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(50, self._update_arrows)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, '_fully_loaded', False) and hasattr(self, '_update_arrows'):
            self._update_arrows()
    def refresh_theme(self):
        tab_keys = ['general', 'appearance', 'playback', 'library', 'shortcuts', 'remote', 'services', 'cache', 'about']
        for key in tab_keys:
            tab = getattr(self, f"tab_{key}", None)
            if tab and hasattr(tab, 'refresh_theme'):
                tab.refresh_theme()