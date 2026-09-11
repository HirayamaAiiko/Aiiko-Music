import sys
import os
from controllers.shortcut_controller import ShortcutController
from core.startup_sequence import StartupSequence
import time
import logging
from PyQt6.QtCore import Qt, QTimer, QSize, QUrl, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QObject, QEvent, QVariantAnimation
from PyQt6.QtGui import QIcon, QColor, QDesktopServices, QPainter, QPixmap, QImage, QPainterPath, QShortcut, QKeySequence
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QFileDialog, QAbstractItemView, 
                             QStackedWidget, QLabel, QListWidget, QListWidgetItem,
                             QInputDialog, QMessageBox, QListView, QDialog, QGraphicsDropShadowEffect, QGraphicsBlurEffect, QScrollArea, QSizePolicy, QStyledItemDelegate, QPushButton)
from qfluentwidgets import (setTheme, Theme, setThemeColor, Slider, PushButton,
                            TitleLabel, BodyLabel, CaptionLabel, Pivot, SegmentedWidget, RoundMenu, Action,
                            NavigationInterface, FluentIcon as FIF, TransparentToolButton,
                            InfoBar, InfoBarPosition)
from config import *
from database import init_db
from widgets import SmoothScrollFilter
from workers import AsyncImageLoader
from player_engine import AudioEngine
from settings_manager import settings
from core.queue_manager import PlaybackQueue
from core.image_cache import ImageCache
from core.playback_controller import PlaybackController
from core.library_manager import LibraryManager
from core.system_integration import SystemManager
from core.settings_sync import SettingsSyncManager
from controllers.library_controller import LibraryController
from controllers.app_controller import AppController
from controllers.player_controller import PlayerController
from controllers.navigation import NavigationController
from controllers.queue_controller import QueueController
from controllers.context_menu_manager import ContextMenuManager
from controllers.search_controller import SearchController
from controllers.playback_ui_controller import PlaybackUIController
from controllers.system_tray_controller import SystemTrayController
from controllers.theme_controller import ThemeController
from controllers.settings_ui_controller import SettingsUIController
from controllers.lyrics_ui_controller import LyricsUIController
from controllers.sleep_timer_controller import SleepTimerController
from controllers.library_sync_controller import LibrarySyncController
from core.notification_manager import notify
import theme_manager
ICON_SHUFFLE = getattr(FIF, 'RANDOM', getattr(FIF, 'SHUFFLE', FIF.SYNC))
ICON_REPEAT = getattr(FIF, 'REPEAT_ALL', getattr(FIF, 'REPEAT', FIF.UPDATE))
from qframelesswindow import FramelessWindow
from qfluentwidgets import MSFluentTitleBar, FluentStyleSheet, setTheme, Theme, setThemeColor
class MusicPlayer(FramelessWindow):
    def __init__(self, bootstrapper):
        self.bootstrapper = bootstrapper
        super().__init__()
        self.setTitleBar(MSFluentTitleBar(self))
        if hasattr(self, 'titleBar') and hasattr(self.titleBar, 'minBtn'):
            try: self.titleBar.minBtn.clicked.disconnect()
            except Exception: pass
            self.titleBar.minBtn.clicked.connect(self._on_minimize_btn_clicked)
            from qfluentwidgets import TransparentToolButton
            self.btn_title_search = TransparentToolButton(FIF.SEARCH, self.titleBar)
            self.btn_title_search.setToolTip("Buscar (Ctrl+F)")
            self.btn_title_search.setFixedSize(46, 32)
            self.btn_title_search.setIconSize(QSize(16, 16))
            self.titleBar.buttonLayout.insertWidget(0, self.btn_title_search)
            self.btn_title_search.clicked.connect(lambda: getattr(self, 'search_controller', None) and self.search_controller.show_spotlight_search())
        FluentStyleSheet.FLUENT_WINDOW.apply(self)
        self.ACCENT_COLORS = {name: theme_manager.get_accent_hex(name)
                              for name in theme_manager.get_accent_names()}
        app_accent_name = settings.get('app_accent_name', 'Teal (AIIKO)')
        app_accent_hex = theme_manager.get_accent_hex(app_accent_name)
        setTheme(Theme.DARK)
        setThemeColor(app_accent_hex)
        self.setStyleSheet("MusicPlayer { background-color: #121212; }")
        self.setWindowTitle("Aiiko Music")
        w = settings.get('window_width', 1280)
        h = settings.get('window_height', 670)
        pos_x = settings.get('window_x', None)
        pos_y = settings.get('window_y', None)
        self._start_maximized = settings.get('window_maximized', False)
        self.resize(w, h)
        if pos_x is not None and pos_y is not None:
            self.move(pos_x, pos_y)
        else:
            screen_geom = QApplication.primaryScreen().availableGeometry()
            self.move((screen_geom.width() - w) // 2, (screen_geom.height() - h) // 2)
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        if hasattr(self, 'titleBar'):
            self.titleBar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        if hasattr(self, 'windowEffect'):
            import sys
            is_win11 = False
            if sys.platform == "win32":
                try:
                    if sys.getwindowsversion().build >= 22000:
                        is_win11 = True
                except Exception:
                    pass
            if is_win11:
                self.windowEffect.setMicaEffect(self.winId(), isDarkMode=True)
            else:
                try: self.windowEffect.removeBackgroundEffect(self.winId())
                except Exception: pass
        if os.path.exists(ICON_FILE):
            self.setWindowIcon(QIcon(ICON_FILE))
        self.library = []
        self.queue = PlaybackQueue()
        self.ext_filepath = self.bootstrapper.ext_filepath
        self.ext_action = self.bootstrapper.ext_action
        if self.ext_filepath:
            if self.ext_filepath.lower().endswith('.aiiko'):
                pass
            else:
                from models import Track
                initial_track = Track(self.ext_filepath)
                self.queue.tracks = [initial_track]
                self.queue.current_index = 0
        self.songs_is_grid = settings.get('songs_is_grid', False)
        self.albums_is_grid = settings.get('albums_is_grid', False)
        self.artists_is_grid = settings.get('artists_is_grid', False)
        self.previous_page_index = 0
        self._needs_model_refresh = False
        self.queue_is_open = False
        self.queue_animation = None
        self.image_loader = AsyncImageLoader()
        self.image_cache = ImageCache(self.image_loader)
        self.image_loader.start()
        fast_audio_engine = self.bootstrapper.fast_audio_engine
        if fast_audio_engine is not None:
            self.audio_engine = fast_audio_engine
            self.audio_engine.setParent(self)
            self.audio_engine.reload_settings()
        else:
            self.audio_engine = AudioEngine(self)
        self.library_manager = LibraryManager(self)
        self.library_manager.set_image_cache(self.image_cache)
        self.system_manager = SystemManager(self, self.image_cache, self.ACCENT_COLORS)
        self.settings_sync = SettingsSyncManager(self)
        self.playback_controller = PlaybackController(self, self.audio_engine, self.queue)
        from controllers.smtc_controller import SMTCController
        self.smtc_controller = SMTCController(self.playback_controller)
        from controllers.eq_controller import EQController
        self.eq_controller = EQController(self)
        self.library_controller = LibraryController(self)
        self.app_controller = AppController(self)
        self.player_controller = PlayerController(self)
        self.navigation_controller = NavigationController(self)
        self.queue_controller = QueueController(self)
        self.context_menu_manager = ContextMenuManager(self)
        self.playback_ui_controller = PlaybackUIController(self)
        self.system_tray_controller = SystemTrayController(self)
        self.sleep_timer_controller = SleepTimerController(self)
        self.theme_controller = ThemeController(self)
        self.settings_ui_controller = SettingsUIController(self)
        self.lyrics_ui_controller = LyricsUIController(self)
        self.library_sync_controller = LibrarySyncController(self)
        notify.initialize(self)
        self.image_cache.cache_updated.connect(self._on_cache_updated)
        self.audio_engine.time_changed.connect(self.player_controller.update_audio_time)
        self.audio_engine.state_changed.connect(self.playback_ui_controller._update_play_icon)
        self.audio_engine.state_changed.connect(self.smtc_controller.update_playback_status)
        self.audio_engine.track_ended.connect(lambda: self.playback_controller.next_track(manual=False))
        self.audio_engine.error_occurred.connect(self.library_sync_controller.on_audio_error)
        self.library_manager.library_loaded.connect(self.library_sync_controller.on_library_loaded)
        self.library_manager.scan_batch_ready.connect(self.library_sync_controller.on_scan_batch)
        self.library_manager.scan_finished.connect(self.library_sync_controller.on_scan_finished)
        self.library_manager.watcher_new_track.connect(self.library_sync_controller.on_watcher_new_track)
        self.library_manager.watcher_track_removed.connect(self.library_sync_controller.on_watcher_track_removed)
        self.library_manager.batch_fetcher_progress.connect(self.library_sync_controller.on_batch_fetcher_progress)
        self.library_manager.batch_fetcher_finished.connect(self.library_sync_controller.on_batch_fetcher_finished)
        self.library_manager.repair_progress.connect(self.library_sync_controller.on_repair_progress)
        self.library_manager.repair_finished.connect(self.library_sync_controller.on_repair_finished)
        self.library_manager.diff_scan_new_tracks.connect(self.library_sync_controller.on_diff_scan_new_tracks)
        self.library_manager.diff_scan_removed_tracks.connect(self.library_sync_controller.on_diff_scan_removed_tracks)
        self.library_manager.diff_scan_finished.connect(self.library_sync_controller.on_diff_scan_finished)
        self.system_manager.toggle_play_requested.connect(self.playback_controller.toggle_play)
        self.system_manager.next_track_requested.connect(lambda: self.playback_controller.next_track(manual=True))
        self.system_manager.prev_track_requested.connect(lambda: self.playback_controller.prev_track(manual=True))
        self.is_slider_pressed = False
        self.show_lyrics = settings.get('now_playing_lyrics_visible', True)
        self.lyrics_manager = None 
        self.smooth_scrolls = [] 
        self.search_controller = SearchController(self)
        self.init_ui()
        self.shortcut_controller = ShortcutController(self)
        self.audio_engine.initialize(settings.get('volume', 80))
        self.eq_controller.apply_current_state()
        self.mini_slider.installEventFilter(self)
        self.player_controller.setup_slider_connections()
        self.theme_controller.apply_theme(full_refresh=True)
        if hasattr(self, 'btn_mini_eq'):
            self.btn_mini_eq.clicked.connect(self.show_equalizer)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui_timer)
        self.timer.start(100) 
        if self.ext_filepath and self.ext_filepath.lower().endswith('.aiiko'):
            QTimer.singleShot(500, lambda: self._handle_aiiko_import(self.ext_filepath))
    def show_equalizer(self):
        try:
            if not hasattr(self, 'eq_dialog') or self.eq_dialog is None:
                from UI.equalizer_view import EqualizerDialog
                self.eq_dialog = EqualizerDialog(self.eq_controller, self)
        except RuntimeError:
            from UI.equalizer_view import EqualizerDialog
            self.eq_dialog = EqualizerDialog(self.eq_controller, self)
        if hasattr(self, 'btn_mini_eq'):
            pos = self.btn_mini_eq.mapToGlobal(self.btn_mini_eq.rect().topLeft())
            self.eq_dialog.move(pos.x() - 500, pos.y() - 430)
        if not self.eq_dialog.isVisible():
            self.eq_dialog.show()
        else:
            self.eq_dialog.raise_()
        self.eq_dialog.activateWindow()
    def _handle_aiiko_import(self, filepath):
        from core.data_backup import validate_backup, import_data
        from qfluentwidgets import MessageBox
        from core.notification_manager import notify
        from core.language_manager import tr
        info = validate_backup(filepath)
        if not info:
            notify.warning(tr("Archivo no válido"), tr("Este archivo no es un backup de Aiiko Music."))
            return
        w = MessageBox(
            tr("Restaurar Configuración"),
            tr("¿Deseas importar el respaldo y configuraciones de este archivo?\n\n") + os.path.basename(filepath),
            self
        )
        if w.exec():
            w.deleteLater()
            result = import_data(filepath, table_filter=None)
            if result["success"]:
                notify.success(tr("Importación exitosa"), tr("Reinicia Aiiko Music para aplicar los cambios."))
                msg = MessageBox(
                    tr("Reinicio recomendado"),
                    tr("Tus datos y ajustes se han restaurado correctamente.\n\n"
                       "Para que los cambios de interfaz y configuraciones tomen efecto, "
                       "por favor cierra y vuelve a abrir Aiiko Music."),
                    self
                )
                msg.yesButton.setText(tr("Entendido"))
                msg.cancelButton.hide()
                msg.exec()
                msg.deleteLater()
            else:
                notify.error(tr("Error al importar"), result["message"])
        else:
            w.deleteLater()
    def _focus_in_page_search(self):
        idx = self.stacked_widget.currentIndex()
        if idx == 1 and hasattr(self, 'search_bar'):
            self.search_bar.setFocus()
            self.search_bar.selectAll()
        elif idx == 2 and hasattr(self, 'page_favorites') and hasattr(self.page_favorites, 'search_bar'):
            self.page_favorites.search_bar.setFocus()
            self.page_favorites.search_bar.selectAll()
        elif idx == 3 and hasattr(self, 'page_playlists'):
            if self.page_playlists.main_stack.currentIndex() == 0 and hasattr(self.page_playlists, 'grid_search'):
                self.page_playlists.grid_search.setFocus()
                self.page_playlists.grid_search.selectAll()
    def _on_cache_updated(self):
        self._needs_model_refresh = True
        try:
            if hasattr(self, 'list_songs') and self.list_songs.isVisible(): self.list_songs.viewport().update()
            if hasattr(self, 'list_albums') and self.list_albums.isVisible(): self.list_albums.viewport().update()
            if hasattr(self, 'list_artists') and self.list_artists.isVisible(): self.list_artists.viewport().update()
            if hasattr(self, 'page_library') and hasattr(self.page_library, 'folders_tab') and not getattr(self.page_library.folders_tab, 'is_placeholder', False):
                if self.page_library.folders_tab.list_songs.isVisible():
                    self.page_library.folders_tab.list_songs.viewport().update()
            if hasattr(self, 'page_favorites') and hasattr(self.page_favorites, 'list_favorites') and self.page_favorites.list_favorites.isVisible():
                self.page_favorites.list_favorites.viewport().update()
            if hasattr(self, 'page_playlists'):
                if hasattr(self.page_playlists, 'grid_page') and hasattr(self.page_playlists.grid_page, 'grid_view') and self.page_playlists.grid_page.grid_view.isVisible():
                    self.page_playlists.grid_page.grid_view.viewport().update()
                if hasattr(self, 'page_playlists') and hasattr(self.page_playlists, 'detail_page') and hasattr(self.page_playlists.detail_page, 'list_playlist_tracks') and self.page_playlists.detail_page.list_playlist_tracks.isVisible():
                    self.page_playlists.detail_page.list_playlist_tracks.viewport().update()
        except RuntimeError:
            pass
    def apply_smooth_scroll(self, widget, step=220, duration=450):
        scroller = SmoothScrollFilter(widget, step, duration, self)
        self.smooth_scrolls.append(scroller)
    def apply_blur(self):
        if not hasattr(self, '_blur_effect'):
            self._blur_effect = QGraphicsBlurEffect()
            self._blur_effect.setBlurRadius(15) 
            self.central_widget.setGraphicsEffect(self._blur_effect)
        self._blur_effect.setEnabled(True)
    def remove_blur(self):
        if hasattr(self, '_blur_effect'):
            self._blur_effect.setEnabled(False)
    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, '_startup_triggered', False):
            self._startup_triggered = True
            show_welcome = not settings.get('welcome_completed', False) or settings.get('dev_welcome_always', False)
            delay = 3800 if show_welcome else 400
            QTimer.singleShot(delay, lambda: StartupSequence(self, self.bootstrapper.app_start_time).execute_delayed_startup())
            if show_welcome:
                self._show_welcome()
        if hasattr(self, 'audio_engine'):
            if self.audio_engine._monitor_timer.interval() != 33:
                self.audio_engine._monitor_timer.setInterval(33)
            self.audio_engine.ui_visible = True
        if hasattr(self, 'timer'):
            if self.timer.interval() != 100:
                self.timer.setInterval(100)
                if getattr(self, '_needs_model_refresh', False):
                    self._flush_model_refresh()
    def _show_welcome(self):
        from UI.welcome_view import WelcomeOverlay
        self._welcome = WelcomeOverlay(self, self.central_widget)
        self._welcome.setGeometry(0, 0, self.central_widget.width(), self.central_widget.height())
        if hasattr(self, 'btn_title_search'):
            self.btn_title_search.setVisible(False)
        def on_welcome_finished():
            if hasattr(self, 'btn_title_search'):
                self.btn_title_search.setVisible(True)
            if hasattr(self, 'page_dashboard') and hasattr(self.page_dashboard, 'header_panel'):
                self.page_dashboard.header_panel.refresh_theme()
        self._welcome.finished.connect(on_welcome_finished)
        self._welcome.show_animated(instant=True)
    def closeEvent(self, event):
        settings.set('window_width', self.width())
        settings.set('window_height', self.height())
        settings.set('window_x', self.x())
        settings.set('window_y', self.y())
        settings.set('window_maximized', self.isMaximized())
        if settings.get('close_to_tray', False) and not getattr(self, 'force_quit', False):
            event.ignore()
            self.system_manager.show_tray_icon_only()
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.info(
                title="Aiiko Music",
                content="La aplicación sigue reproduciendo en segundo plano.",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            return
        if hasattr(self, 'fullscreen_view') and self.fullscreen_view:
            try:
                self.fullscreen_view.close()
            except Exception as e:
                import logging
                logging.error(f"Error al cerrar fullscreen_view: {e}")
        if hasattr(self, 'smtc_controller') and self.smtc_controller:
            self.smtc_controller.cleanup()
        self.system_tray_controller.perform_shutdown()
        super().closeEvent(event)
        QApplication.processEvents()
        import time
        time.sleep(0.1)                                                                    
        import logging
        logging.info("Cierre completado. Permitiendo que la aplicación termine naturalmente.")
    def _on_minimize_btn_clicked(self):
        if settings.get('minimize_to_tray', False):
            self.system_manager.show_tray_icon_only()
        else:
            self.showMinimized()
    def changeEvent(self, event):
        super().changeEvent(event)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'titleBar'):
            self.titleBar.raise_()
        if hasattr(self, 'queue_panel'):
            panel_width = self.queue_panel.width()
            panel_height = self.central_widget.height() - self.mini_player.height()
            if self.queue_is_open:
                self.queue_panel.setGeometry(self.width() - panel_width, 0, panel_width, panel_height)
            else:
                self.queue_panel.setGeometry(self.width(), 0, panel_width, panel_height)
        if hasattr(self, 'mini_volume_inline'):
            self.mini_volume_inline.setVisible(self.width() > 1167)
        self.search_controller.center_if_visible()
        try:
            if hasattr(self, '_welcome') and self._welcome and self._welcome.isVisible():
                self._welcome.setGeometry(0, 0, self.central_widget.width(), self.central_widget.height())
        except (RuntimeError, AttributeError):
            pass
        if hasattr(self, '_gradient_overlay') and self._gradient_overlay.isVisible():
            self._gradient_overlay.setGeometry(self.rect())
    def eventFilter(self, obj, event):
        if self.player_controller.handle_slider_click(obj, event):
            return True
        return super().eventFilter(obj, event)
    def init_ui(self):
        from view_models.library_models import TrackListModel, GroupListModel, GroupProxyModel
        self.track_model = TrackListModel(self)
        self.album_model = GroupListModel(self, is_artist=False)
        self.album_proxy = GroupProxyModel(self)
        self.album_proxy.setSourceModel(self.album_model)
        self.artist_model = GroupListModel(self, is_artist=True)
        self.artist_proxy = GroupProxyModel(self)
        self.artist_proxy.setSourceModel(self.artist_model)
        from UI.main_window_builder import MainWindowBuilder
        MainWindowBuilder.build(self)
        self.navigation_controller.setup_connections()
    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if not self.isMinimized() and not self.isHidden():
                self._last_known_maximized = self.isMaximized()
            is_background = (self.isMinimized() or self.isHidden()) and not getattr(self.system_manager, 'floating_active', False)
            if hasattr(self, 'audio_engine'):
                if is_background:
                    if self.audio_engine._monitor_timer.interval() != 500:
                        self.audio_engine._monitor_timer.setInterval(500)
                    self.audio_engine.ui_visible = False
                else:
                    if self.audio_engine._monitor_timer.interval() != 33:
                        self.audio_engine._monitor_timer.setInterval(33)
                    self.audio_engine.ui_visible = True
            if hasattr(self, 'timer'):
                if is_background:
                    if self.timer.interval() != 1000:
                        self.timer.setInterval(1000)
                else:
                    if self.timer.interval() != 100:
                        self.timer.setInterval(100)
                        if getattr(self, '_needs_model_refresh', False):
                            self._flush_model_refresh()
        super().changeEvent(event)
    def update_ui_timer(self):
        self.refresh_counter = getattr(self, 'refresh_counter', 0) + 1
        if getattr(self, '_needs_model_refresh', False) and self.refresh_counter % 5 == 0:
            if not (self.isMinimized() or self.isHidden()):
                self._flush_model_refresh()
        if self.refresh_counter % 10 == 0 and getattr(self, 'remote_server', None):
            if hasattr(self, 'audio_engine') and self.audio_engine.is_playing():
                pos = self.audio_engine.get_position()
                track = getattr(self.queue, 'get_current', lambda: None)()
                track_id = self.remote_server.get_track_id(track.filepath) if track else None
                self.remote_server.broadcast_time(pos, track_id)
    def _flush_model_refresh(self):
        if hasattr(self, 'track_model') and self.track_model:
            top_left = self.track_model.index(0, 0)
            bottom_right = self.track_model.index(self.track_model.rowCount() - 1, 0)
            self.track_model.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DecorationRole])
        self._needs_model_refresh = False
    def handle_external_file(self, filepath, action="play"):
        from models import Track
        from core.notification_manager import notify
        import os
        import logging
        valid_extensions = ('.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac')
        if not os.path.isfile(filepath):
            logging.warning(f"Archivo externo ignorado (no existe): {filepath}")
            return
        if filepath.lower().endswith('.aiiko'):
            self._handle_aiiko_import(filepath)
            return
        if not filepath.lower().endswith(valid_extensions):
            logging.warning(f"Archivo externo ignorado (no soportado): {filepath}")
            return
        try:
            track = Track(filepath)
            if action in ("enqueue", "enqueue-end"):
                self.queue_controller.add_to_queue(track)
                logging.info(f"Archivo externo añadido al final de la cola: {track.title}")
            elif action == "play-next":
                self.queue_controller.add_to_queue_next(track)
                logging.info(f"Archivo externo añadido a continuación: {track.title}")
            else:
                self.queue_controller.play_specific_track_global(track, self.queue.tracks + [track])
                logging.info(f"Archivo externo reproducido: {track.title}")
            self.showNormal()
            self.raise_()
            self.activateWindow()
        except Exception as e:
            logging.error(f"Error procesando archivo externo '{filepath}': {e}")
            notify.error("Error", f"No se pudo abrir el archivo: {os.path.basename(filepath)}")