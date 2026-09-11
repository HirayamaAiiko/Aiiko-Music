from datetime import datetime
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import TitleLabel, BodyLabel, SmoothScrollArea
from UI.user_profile_widget import UserProfileButton, is_birthday_today
from UI.dashboard.dashboard_worker import DashboardRefreshWorker
from UI.dashboard.components.dashboard_sidebar_panel import DashboardSidebarPanel
from UI.dashboard.components.dashboard_main_panel import DashboardMainPanel
from UI.dashboard.components.dashboard_header import DashboardHeader
import theme_manager
class DashboardView(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.setObjectName("PageContent")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._SIDEBAR_MIN_WIDTH = 1260
        self._CONTENT_MIN_WIDTH = 600
        self.setMinimumWidth(self._CONTENT_MIN_WIDTH)
        self._build_ui()
    def _get_accent(self):
        from settings_manager import settings
        return theme_manager.get_accent_hex(settings.get('app_accent_name', 'Teal (AIIKO)'))
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 0, 24, 0)
        root.setSpacing(12)
        self.header_panel = DashboardHeader(self)
        root.addWidget(self.header_panel)
        columns = QHBoxLayout()
        columns.setSpacing(12)
        columns.setContentsMargins(0, 0, 0, 0)
        self._left_scroll = left_scroll = SmoothScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setStyleSheet("SmoothScrollArea { border: none; background: transparent; }")
        self.main_panel = DashboardMainPanel(self.player, self)
        left_scroll.setWidget(self.main_panel)
        self._scroll_hide_timer = QTimer(self)
        self._scroll_hide_timer.setSingleShot(True)
        self._scroll_hide_timer.setInterval(1500)
        def _show_vbar():
            left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            left_scroll.verticalScrollBar().show()
            self._scroll_hide_timer.start()
        def _hide_vbar():
            left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            left_scroll.verticalScrollBar().hide()
        self._scroll_hide_timer.timeout.connect(_hide_vbar)
        left_scroll.verticalScrollBar().valueChanged.connect(lambda _: _show_vbar())
        self._right_col = right_col = QWidget()
        right_col.setFixedWidth(300)
        right_col.setStyleSheet("background: transparent;")
        right_col_layout = QVBoxLayout(right_col)
        right_col_layout.setContentsMargins(10, 4, 0, 0)
        right_col_layout.setSpacing(0)
        right_scroll = SmoothScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setStyleSheet("SmoothScrollArea { border: none; background: transparent; }")
        self.sidebar_panel = DashboardSidebarPanel(self)
        self.sidebar_panel.artist_clicked.connect(self._on_artist_clicked)
        self.sidebar_panel.explore_clicked.connect(lambda: self.player.navigation_controller.switch_page(1))
        right_scroll.setWidget(self.sidebar_panel)
        right_col_layout.addWidget(right_scroll, 1)
        columns.addWidget(left_scroll, 1)
        columns.addWidget(right_col, 0)
        root.addLayout(columns, 1)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_right_col'):
            if not getattr(self, '_content_hidden', False):
                self._right_col.setVisible(self.width() >= self._SIDEBAR_MIN_WIDTH)
    def set_content_visible(self, visible):
        self._content_hidden = not visible
        if hasattr(self, '_left_scroll'):
            self._left_scroll.setVisible(visible)
        if hasattr(self, '_right_col'):
            if visible:
                self._right_col.setVisible(self.width() >= self._SIDEBAR_MIN_WIDTH)
            else:
                self._right_col.setVisible(False)
    def refresh_theme(self):
        if hasattr(self, 'header_panel') and hasattr(self.header_panel, 'refresh_theme'):
            self.header_panel.refresh_theme()
        if hasattr(self, 'main_panel') and hasattr(self.main_panel, 'refresh_theme'):
            self.main_panel.refresh_theme()
        if getattr(self, '_is_loaded', False):
            self.refresh(force=True)
    def refresh(self, force=False):
        self.header_panel._update_greeting()
        if getattr(self, '_is_loaded', False) and not force:
            return
        self._is_loaded = True
        worker = getattr(self, '_worker', None)
        try:
            if worker and worker.isRunning():
                return
        except RuntimeError:
            pass                                        
        time_range = getattr(self.main_panel, 'current_top_filter', 'today')
        self._worker = DashboardRefreshWorker(library=self.player.library, time_range=time_range, parent=self)
        self._worker.data_ready.connect(self._apply_data)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()
    def _apply_data(self, data):
        self.main_panel.update_data(data)
        self.sidebar_panel.update_data(data)
        self.header_panel.update_data(data)
    def refresh_top_tracks(self):
        time_range = getattr(self.main_panel, 'current_top_filter', 'today')
        def _fetch_top():
            from controllers.analytics_controller import AnalyticsController as AC
            return AC.get_top_tracks(limit=10, time_range=time_range)
        def _apply_top(top):
            if hasattr(self, 'main_panel'):
                self.main_panel._refresh_carousel(
                    top, self.main_panel._top_scroll, self.main_panel._top_container,
                    self.main_panel._top_widget, self.main_panel._top_empty,
                    subtitle_key="artist", play_count=True
                )
        self._run_async(_fetch_top, _apply_top)
    def refresh_recently_played(self):
        def _fetch_recent():
            from controllers.analytics_controller import AnalyticsController as AC
            return AC.get_recently_played(limit=10)
        def _apply_recent(recent):
            if hasattr(self, 'main_panel'):
                self.main_panel._refresh_carousel(
                    recent, self.main_panel._recent_scroll, self.main_panel._recent_container,
                    self.main_panel._recent_widget, self.main_panel._recent_empty,
                    subtitle_key="artist"
                )
        self._run_async(_fetch_recent, _apply_recent)
    def _run_async(self, worker_func, callback_func):
        from PyQt6.QtCore import QThread, pyqtSignal
        class GenericWorker(QThread):
            finished_data = pyqtSignal(object)
            def run(self):
                try:
                    data = worker_func()
                    self.finished_data.emit(data)
                except Exception as e:
                    import logging
                    logging.error(f"Error asíncrono dashboard: {e}")
        worker = GenericWorker(self)
        worker.finished_data.connect(callback_func)
        worker.finished.connect(worker.deleteLater)
        if not hasattr(self, '_async_workers'):
            self._async_workers = []
        self._async_workers.append(worker)
        worker.finished.connect(lambda w=worker: self._async_workers.remove(w) if w in self._async_workers else None)
        worker.start()
    def refresh_recently_added(self):
        import time as _time
        from controllers.analytics_controller import AnalyticsController as AC
        added = AC.get_recently_added(limit=15, days=14)
        if added:
            now = _time.time()
            for item in added:
                days_ago = int((now - (item.get("ctime") or now)) / 86400)
                item["_custom_subtitle"] = f"Hace {days_ago} día{'s' if days_ago != 1 else ''}" if days_ago > 0 else "Hoy"
        self.main_panel._refresh_carousel(
            added, self.main_panel._added_scroll, self.main_panel._added_container,
            self.main_panel._added_widget, self.main_panel._added_empty,
            subtitle_key="_custom_subtitle"
        )
    def refresh_after_playback(self):
        if not getattr(self, '_is_loaded', False):
            return
        self.refresh_recently_played()
        self.refresh_top_tracks()
    def _on_artist_clicked(self, artist_name: str):
        if hasattr(self.player, 'navigation_controller'):
            self.player.navigation_controller._navigate_to_artist(artist_name)