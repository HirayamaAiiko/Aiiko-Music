import logging
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QPropertyAnimation
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction, QIcon
from qfluentwidgets import FluentIcon as FIF
from settings_manager import settings
from core.language_manager import tr
from services.discord_service import DiscordRPCManager, RPC_AVAILABLE
from UI.floating_player import FloatingMiniPlayer
class SystemManager(QObject):
    toggle_play_requested = pyqtSignal()
    next_track_requested = pyqtSignal()
    prev_track_requested = pyqtSignal()
    def __init__(self, main_window, image_cache, accent_colors_dict):
        super().__init__(main_window)
        self.main_window = main_window
        self.image_cache = image_cache
        self.accent_colors_dict = accent_colors_dict
        self.floating_player = None
        self.tray_icon = None
        self.floating_active = False
        self.discord_rpc = DiscordRPCManager()
        self.discord_client_id = "YOUR_DISCORD_CLIENT_ID"
        self.hotkey_listener = None
        self._rpc_heartbeat = QTimer(self)
        self._rpc_heartbeat.setInterval(30000)               
        self._rpc_heartbeat.timeout.connect(self._rpc_heartbeat_check)
        if settings.get('rpc', False):
            QTimer.singleShot(3000, self._auto_connect_rpc)                                  
        self.init_tray_icon()
    def init_floating_player(self):
        if self.floating_player is not None:
            return
        self.floating_player = FloatingMiniPlayer(image_cache=self.image_cache)
        app_accent_name = settings.get('app_accent_name', 'Teal (AIIKO)')
        self.floating_player.set_accent_color(self.accent_colors_dict.get(app_accent_name, '#1DB954'))
        self.floating_player.play_pause_clicked.connect(self.toggle_play_requested.emit)
        self.floating_player.next_clicked.connect(self.next_track_requested.emit)
        self.floating_player.prev_clicked.connect(self.prev_track_requested.emit)
        self.floating_player.restore_clicked.connect(self.restore_from_floating)
        self.init_tray_icon()
    def _is_windows_dark_mode(self):
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "SystemUsesLightTheme")
            return value == 0
        except Exception:
            return True
    def init_tray_icon(self):
        if self.tray_icon is not None:
            return
        self.tray_icon = QSystemTrayIcon(self.main_window)
        import os, sys
        app_root = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if self._is_windows_dark_mode():
            icon_path = os.path.join(app_root, "resources", "app", "logo_tray_black_bg_white_icon.svg")
            if os.path.exists(icon_path):
                from PyQt6.QtSvg import QSvgRenderer
                from PyQt6.QtGui import QPixmap, QPainter
                from PyQt6.QtCore import Qt, QRectF
                renderer = QSvgRenderer(icon_path)
                pixmap = QPixmap(128, 128)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                zoom_margin = -12
                target_rect = QRectF(zoom_margin, zoom_margin, 128 - (zoom_margin * 2), 128 - (zoom_margin * 2))
                renderer.render(painter, target_rect)
                painter.end()
                icon = QIcon(pixmap)
            else:
                icon = self.main_window.windowIcon()
        else:
            icon_path = os.path.join(app_root, "resources", "app", "logo_tray_white_bg_black_icon.svg")
            if os.path.exists(icon_path):
                from PyQt6.QtSvg import QSvgRenderer
                from PyQt6.QtGui import QPixmap, QPainter
                from PyQt6.QtCore import Qt, QRectF
                renderer = QSvgRenderer(icon_path)
                pixmap = QPixmap(128, 128)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                zoom_margin = -12
                target_rect = QRectF(zoom_margin, zoom_margin, 128 - (zoom_margin * 2), 128 - (zoom_margin * 2))
                renderer.render(painter, target_rect)
                painter.end()
                icon = QIcon(pixmap)
            else:
                icon = self.main_window.windowIcon()
        if icon.isNull():
            icon = QIcon(FIF.MUSIC.icon())
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Aiiko Music")
        self.tray_icon.activated.connect(self._on_tray_activated)
        tray_menu = QMenu()
        act_prev = QAction("Anterior", self.main_window)
        act_prev.triggered.connect(self.prev_track_requested.emit)
        tray_menu.addAction(act_prev)
        self._tray_play_action = QAction("Pausar", self.main_window)
        self._tray_play_action.triggered.connect(self.toggle_play_requested.emit)
        tray_menu.addAction(self._tray_play_action)
        act_next = QAction("Siguiente", self.main_window)
        act_next.triggered.connect(self.next_track_requested.emit)
        tray_menu.addAction(act_next)
        tray_menu.addSeparator()
        act_show = QAction("Abrir Aiiko Music", self.main_window)
        act_show.triggered.connect(self.restore_from_tray)
        tray_menu.addAction(act_show)
        act_settings = QAction("Configuración", self.main_window)
        act_settings.triggered.connect(self._open_settings_from_tray)
        tray_menu.addAction(act_settings)
        tray_menu.addSeparator()
        act_exit = QAction("Salir", self.main_window)
        act_exit.triggered.connect(self.quit_app)
        tray_menu.addAction(act_exit)
        tray_menu.addSeparator()
        act_close_menu = QAction("Cerrar menú", self.main_window)
        act_close_menu.triggered.connect(tray_menu.hide)
        tray_menu.addAction(act_close_menu)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    def quit_app(self):
        self.main_window.force_quit = True
        self.main_window.close()
        QApplication.processEvents()
        import time
        time.sleep(0.1)
        import os
        os._exit(0)
    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.restore_from_tray()
    def show_tray_icon_only(self):
        self.init_tray_icon()
        self.tray_icon.show()
        self.hide_window_animated()
    def restore_from_tray(self):
        if self.floating_active or self.main_window.isHidden() or self.main_window.windowOpacity() < 1.0 or self.main_window.isMinimized():
            self.restore_from_floating()
        else:
            self.main_window.raise_()
            self.main_window.activateWindow()
    def toggle_floating_player(self, current_track, is_playing):
        self.init_floating_player()
        if self.floating_active:
            self.restore_from_floating()
        else:
            self.floating_active = True
            if current_track:
                self.floating_player.update_track(current_track)
            self.floating_player.update_play_state(is_playing)
            screen = QApplication.primaryScreen().availableGeometry()
            fw = self.floating_player.width()
            fh = self.floating_player.height()
            self.floating_player.move(screen.right() - fw - 24, screen.bottom() - fh - 80)
            self.floating_player.show_animated()
            self.tray_icon.show()
            self.hide_window_animated()
    def hide_window_animated(self):
        self.normal_geometry = self.main_window.normalGeometry()
        from settings_manager import settings
        use_fade = settings.get('minimize_to_tray', False) or settings.get('close_to_tray', False)
        if use_fade:
            self.fade_out_anim = QPropertyAnimation(self.main_window, b"windowOpacity")
            self.fade_out_anim.setDuration(250)
            self.fade_out_anim.setStartValue(self.main_window.windowOpacity())
            self.fade_out_anim.setEndValue(0.01)
            self.fade_out_anim.finished.connect(self.main_window.hide)
            self.fade_out_anim.start()
        else:
            self.main_window.hide()
        if hasattr(self.main_window, 'audio_engine'):
            if self.main_window.audio_engine._monitor_timer.interval() != 500:
                self.main_window.audio_engine._monitor_timer.setInterval(500)
            self.main_window.audio_engine.ui_visible = False
        if hasattr(self.main_window, 'timer'):
            if self.main_window.timer.interval() != 1000:
                self.main_window.timer.setInterval(1000)
    def restore_from_floating(self):
        self.floating_active = False
        if self.floating_player and self.floating_player.isVisible():
            self.floating_player.fade_out()
        from settings_manager import settings
        use_fade = settings.get('minimize_to_tray', False) or settings.get('close_to_tray', False)
        was_maximized = getattr(self.main_window, '_last_known_maximized', False)
        if use_fade:
            self.main_window.setWindowOpacity(0.01)
        else:
            self.main_window.setWindowOpacity(1.0)
        if was_maximized:
            self.main_window.showMaximized()
        else:
            self.main_window.showNormal()
        self.main_window.raise_()
        self.main_window.activateWindow()
        if hasattr(self.main_window, 'audio_engine'):
            if self.main_window.audio_engine._monitor_timer.interval() != 33:
                self.main_window.audio_engine._monitor_timer.setInterval(33)
            self.main_window.audio_engine.ui_visible = True
        if hasattr(self.main_window, 'timer'):
            if self.main_window.timer.interval() != 100:
                self.main_window.timer.setInterval(100)
                if getattr(self.main_window, '_needs_model_refresh', False) and hasattr(self.main_window, '_flush_model_refresh'):
                    self.main_window._flush_model_refresh()
        if use_fade:
            self.fade_anim = QPropertyAnimation(self.main_window, b"windowOpacity")
            self.fade_anim.setDuration(250)
            self.fade_anim.setStartValue(0.01)
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()
    def update_floating_progress(self, curr_ms, total_ms):
        if self.floating_player and self.floating_player.isVisible():
            self.floating_player.update_progress(curr_ms, total_ms)
    def update_floating_play_state(self, is_playing):
        if self.floating_player and self.floating_player.isVisible():
            self.floating_player.update_play_state(is_playing)
        self.update_tray_play_state(is_playing)
    def update_tray_track_info(self, track):
        if self.tray_icon and track:
            title = track.title or tr("Sin título")
            artist = tr("Artista Desconocido") if not track.artist or track.artist in ("Artista Desconocido", "Desconocido") else track.artist
            self.tray_icon.setToolTip(f"Aiiko Music - {title} - {artist}")
    def update_tray_play_state(self, is_playing):
        if hasattr(self, '_tray_play_action'):
            self._tray_play_action.setText("Pausar" if is_playing else "Reproducir")
    def _open_settings_from_tray(self):
        self.restore_from_tray()
        if hasattr(self.main_window, 'navigation_controller'):
            self.main_window.navigation_controller.switch_page(5)
    def init_global_hotkeys(self):
        logging.info("Soporte pynput deshabilitado en favor de SMTC nativo (0% CPU).")
    def _auto_connect_rpc(self):
        if not settings.get('rpc', False):
            return
        if self.discord_rpc.enabled:
            return                
        if self.connect_rpc():
            if hasattr(self.main_window, 'system_tray_controller'):
                self.main_window.system_tray_controller.update_discord_rpc()
        if not self._rpc_heartbeat.isActive():
            self._rpc_heartbeat.start()
    def _rpc_heartbeat_check(self):
        if not settings.get('rpc', False):
            self._rpc_heartbeat.stop()
            return
        if not self.discord_rpc.enabled or self.discord_rpc.rpc is None:
            logging.debug("Discord RPC heartbeat: reconectando...")
            if self.connect_rpc():
                if hasattr(self.main_window, 'system_tray_controller'):
                    self.main_window.system_tray_controller.update_discord_rpc()
    def connect_rpc(self):
        if RPC_AVAILABLE:
            success = self.discord_rpc.connect(self.discord_client_id)
            if success and not self._rpc_heartbeat.isActive():
                self._rpc_heartbeat.start()
            return success
        return False
    def disconnect_rpc(self):
        self._rpc_heartbeat.stop()
        self.discord_rpc.disconnect()
    def shutdown(self):
        if self.floating_player:
            self.floating_player.close()
        if self.tray_icon:
            self.tray_icon.hide()
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except: pass
        self.disconnect_rpc()