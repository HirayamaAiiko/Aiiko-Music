from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel
from qfluentwidgets import SwitchButton, FluentIcon as FIF, ImageLabel
from settings_manager import settings
from core.language_manager import tr
from .base_settings_tab import BaseSettingsTab
class LastfmDashboardWorker(QThread):
    result_ready = pyqtSignal(dict)
    def __init__(self, username, download_avatar=True, parent=None):
        super().__init__(parent)
        self.username = username
        self.download_avatar = download_avatar
    def run(self):
        from services.lastfm_service import LastfmService
        import requests
        import tempfile
        import os
        info = LastfmService.fetch_user_info(self.username)
        if self.download_avatar and info and info.get('avatar_url'):
            try:
                resp = requests.get(info['avatar_url'], timeout=5, headers={'Cache-Control': 'no-cache'})
                if resp.status_code == 200:
                    tmp_path = os.path.join(tempfile.gettempdir(), "aiiko_lastfm_avatar.png")
                    with open(tmp_path, 'wb') as f:
                        f.write(resp.content)
                    info['local_avatar_path'] = tmp_path
            except:
                pass
        self.result_ready.emit(info if info else {})
class ServicesTab(BaseSettingsTab):
    def __init__(self, player, parent=None):
        super().__init__(player, parent)
        card1, cl1 = self._create_card(tr("Integraciones"), ('services/discord', FIF.LINK))
        player.switch_rpc = SwitchButton()
        player.switch_rpc.checkedChanged.connect(player.system_tray_controller.toggle_discord_rpc)
        def _update_dashboard_discord():
            if hasattr(player, 'page_dashboard') and hasattr(player.page_dashboard, 'header_panel'):
                player.page_dashboard.header_panel._update_service_indicators()
        player.switch_rpc.checkedChanged.connect(_update_dashboard_discord)
        from services.discord_service import RPC_AVAILABLE
        rpc_desc = tr("Muestra la canción que escuchas como estado en Discord.")
        if not RPC_AVAILABLE:
            player.switch_rpc.setDisabled(True)
            rpc_desc += "\n❌ " + tr("Librería 'pypresence' no instalada.")
        self._setting_row(cl1, tr("Discord Rich Presence"), rpc_desc,
                          player.switch_rpc, add_separator=False)
        self.main_layout.addWidget(card1)
        self.main_layout.addSpacing(16)
        card2, cl2 = self._create_card("Last.fm", ('services/lastfm', FIF.PEOPLE))
        from qfluentwidgets import PrimaryPushButton, PushButton, MessageBox, BodyLabel, CaptionLabel
        from services.lastfm_service import LastfmService
        row = QHBoxLayout()
        row.setContentsMargins(0, 8, 0, 8)
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(48, 48)
        self.avatar_label.hide()
        row.addWidget(self.avatar_label)
        row.addSpacing(12)
        info = QVBoxLayout()
        info.setSpacing(2)
        self.lastfm_title = BodyLabel(tr("Scrobbling"))
        self.lastfm_title.setStyleSheet("color: rgba(255,255,255,0.90); font-size: 14px; font-weight: 600; background: transparent; border: none;")
        info.addWidget(self.lastfm_title)
        self.lastfm_desc_label = CaptionLabel("")
        self.lastfm_desc_label.setWordWrap(True)
        self.lastfm_desc_label.setStyleSheet("color: rgba(255,255,255,0.40); font-size: 13px; background: transparent; border: none;")
        info.addWidget(self.lastfm_desc_label)
        self.lastfm_stats_label = CaptionLabel("")
        self.lastfm_stats_label.setStyleSheet("color: rgba(255,255,255,0.60); font-size: 12px; font-weight: bold; background: transparent; border: none;")
        self.lastfm_stats_label.hide()
        info.addWidget(self.lastfm_stats_label)
        row.addLayout(info, 1)
        row.addSpacing(20)
        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(8)
        self.btn_lastfm = PrimaryPushButton(tr("Conectar con Last.fm"))
        self.btn_lastfm_disconnect = PushButton(tr("Desconectar"))
        self.btn_lastfm.clicked.connect(self._connect_lastfm)
        self.btn_lastfm_disconnect.clicked.connect(self._disconnect_lastfm)
        btns_layout.addWidget(self.btn_lastfm)
        btns_layout.addWidget(self.btn_lastfm_disconnect)
        row.addLayout(btns_layout)
        cl2.addLayout(row)
        self._update_lastfm_ui()
        self.main_layout.addWidget(card2)
        self.main_layout.addStretch()
    def _update_lastfm_ui(self, is_refresh=False):
        from services.lastfm_service import LastfmService
        username = settings.get('lastfm_username', '')
        if LastfmService.is_connected() and username:
            if not is_refresh:
                self.lastfm_desc_label.setText(f'<span style="color:#1DB954; font-size:13px;">{tr("Cargando perfil...")}</span>')
            self.btn_lastfm.hide()
            self.btn_lastfm_disconnect.show()
            self._dashboard_worker = LastfmDashboardWorker(username, download_avatar=(not is_refresh), parent=self)
            self._dashboard_worker.result_ready.connect(lambda info: self._on_dashboard_ready(info, is_refresh))
            self._dashboard_worker.start()
        else:
            self.lastfm_title.setText(tr("Scrobbling"))
            self.lastfm_desc_label.setText(tr("Registra tus reproducciones en tu cuenta de Last.fm."))
            self.lastfm_desc_label.setStyleSheet("color: rgba(255,255,255,0.40); font-size: 13px; background: transparent; border: none;")
            self.avatar_label.hide()
            self.lastfm_stats_label.hide()
            self.btn_lastfm.show()
            self.btn_lastfm_disconnect.hide()
        if hasattr(self.player, 'page_dashboard') and hasattr(self.player.page_dashboard, 'header_panel'):
            self.player.page_dashboard.header_panel._update_service_indicators()
    def _on_dashboard_ready(self, info, is_refresh=False):
        if not info:
            if not is_refresh:
                self.lastfm_desc_label.setText(f'<span style="color:#1DB954; font-size:13px;">{tr("Conectado")}</span>')
            return
        realname = info.get('realname') or info.get('name')
        playcount = info.get('playcount', '0')
        self.lastfm_title.setText(realname)
        self.lastfm_desc_label.setText(f'<span style="color:#1DB954; font-size:13px;">@{info.get("name")}</span>')
        self.lastfm_stats_label.setText(f"{int(playcount):,} Scrobbles")
        self.lastfm_stats_label.show()
        if not is_refresh:
            avatar_path = info.get('local_avatar_path')
            from utils import get_rounded_pixmap
            if avatar_path:
                pixmap = get_rounded_pixmap(avatar_path, 48, radius=24)
                self.avatar_label.setPixmap(pixmap)
                self.avatar_label.show()
    def _connect_lastfm(self):
        from services.lastfm_service import LastfmService
        from qfluentwidgets import MessageBox
        import webbrowser
        if not LastfmService.is_configured():
            MessageBox(tr("Error"), tr("Las claves de API de Last.fm no están configuradas en config.py."), self.window()).exec()
            return
        token = LastfmService.get_token()
        if token == "ERROR_10":
            MessageBox(tr("Clave de API Inválida"), tr("La clave de API de Last.fm actual ha sido revocada o es inválida.\n\nPor favor, crea tu propia clave de API en:\nhttps://www.last.fm/api/account/create\n\nY pégala en tu archivo config.py"), self.window()).exec()
            return
        elif not token or token.startswith("ERROR_"):
            MessageBox(tr("Error"), tr("No se pudo conectar con Last.fm. Revisa tu conexión a internet o verifica las claves API."), self.window()).exec()
            return
        url = LastfmService.get_auth_url(token)
        webbrowser.open(url)
        w = MessageBox(
            tr("Autorización Requerida"),
            tr("Se ha abierto tu navegador web. Por favor, autoriza a Aiiko Music en Last.fm y luego haz clic en 'Continuar' aquí."),
            self.window()
        )
        w.yesButton.setText(tr("Continuar"))
        w.cancelButton.setText(tr("Cancelar"))
        if w.exec():
            if LastfmService.get_session(token):
                from core.notification_manager import notify
                notify.success("Last.fm", tr("Conectado exitosamente como {username}").format(username=settings.get('lastfm_username')))
                self._update_lastfm_ui()
                self.parent().parent().parent().update() 
            else:
                MessageBox(tr("Error"), tr("No se pudo obtener la sesión. Asegúrate de haber autorizado la aplicación."), self.window()).exec()
    def _disconnect_lastfm(self):
        from services.lastfm_service import LastfmService
        LastfmService.disconnect()
        self._update_lastfm_ui()
    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, 'btn_lastfm_disconnect', None) and not self.btn_lastfm.isVisible():
            self._update_lastfm_ui(is_refresh=True)