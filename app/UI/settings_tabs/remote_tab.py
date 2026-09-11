from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from qfluentwidgets import SwitchButton, LineEdit, PrimaryPushButton, FluentIcon as FIF
from settings_manager import settings
from core.language_manager import tr
from core.notification_manager import notify
from .base_settings_tab import BaseSettingsTab
class RemoteTab(BaseSettingsTab):
    def __init__(self, player, parent=None):
        super().__init__(player, parent)
        card_server, cl_server = self._create_card(tr("Servidor Local"), FIF.WIFI)
        self.switch_enable = SwitchButton()
        self.switch_enable.setChecked(settings.get('remote_enabled', False))
        self.switch_enable.checkedChanged.connect(self._on_enable_changed)
        self._setting_row(cl_server, tr("Activar Control Remoto"),
                          tr("Permite que la aplicación Android controle Aiiko Music en la red local."),
                          self.switch_enable)
        self.line_name = LineEdit()
        self.line_name.setFixedWidth(200)
        self.line_name.setText(settings.get('remote_name', 'Aiiko Server'))
        self.line_name.textChanged.connect(self._on_name_changed)
        self._setting_row(cl_server, tr("Nombre del Servidor"),
                          tr("Este nombre aparecerá en la app de Android al buscar dispositivos."),
                          self.line_name)
        self.btn_copy_ip = PrimaryPushButton(tr("Copiar IP"))
        self.btn_copy_ip.setIcon(FIF.INFO)
        self.btn_copy_ip.setFixedWidth(120)
        self.btn_copy_ip.clicked.connect(self._on_copy_ip)
        self._setting_row(cl_server, tr("Estado de la Conexión"),
                          tr("Servidor inactivo."),
                          self.btn_copy_ip, add_separator=False)
        row_layout = cl_server.itemAt(cl_server.count() - 1).layout()
        info_layout = row_layout.itemAt(0).layout()
        self.lbl_status_desc = info_layout.itemAt(1).widget()
        self.main_layout.addWidget(card_server)
        self.main_layout.addStretch()
        self._update_info_card()
        from PyQt6.QtCore import QTimer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_info_card)
        self.update_timer.start(2000)
    def _on_enable_changed(self, checked):
        self.switch_enable.setEnabled(False)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2500, lambda: self.switch_enable.setEnabled(True))
        settings.set('remote_enabled', checked)
        if checked:
            if not getattr(self.player, 'remote_server', None):
                from core.remote_server import RemoteServer
                name = settings.get('remote_name', 'Aiiko Server')
                self.player.remote_server = RemoteServer(self.player, port=8080, server_name=name)
                self.player.remote_server.start()
                notify.success(tr("Control Remoto"), tr("Servidor iniciado correctamente."), self.player)
        else:
            if getattr(self.player, 'remote_server', None):
                self.player.remote_server.stop()
                self.player.remote_server = None
                notify.warning(tr("Control Remoto"), tr("Servidor detenido."), self.player)
        self._update_info_card()
    def _on_name_changed(self, text):
        settings.set('remote_name', text)
        if getattr(self.player, 'remote_server', None):
            self.player.remote_server.server_name = text
    def _update_info_card(self):
        is_enabled = settings.get('remote_enabled', False)
        if is_enabled and getattr(self.player, 'remote_server', None):
            ip = self.player.remote_server.get_local_ip()
            clients_count = len(self.player.remote_server.manager.active_connections)
            if clients_count > 0:
                msg = tr("Ejecutándose en {ip}:8080 • {clients_count} dispositivo(s) conectado(s)").format(ip=ip, clients_count=clients_count)
                self.lbl_status_desc.setText(msg)
                self.lbl_status_desc.setStyleSheet("color: #1DB954; font-weight: bold; font-size: 11px;")
            else:
                msg = tr("Ejecutándose en {ip}:8080 • Esperando conexión...").format(ip=ip)
                self.lbl_status_desc.setText(msg)
                self.lbl_status_desc.setStyleSheet("color: rgba(255,255,255,0.40); font-size: 11px;")
            self.btn_copy_ip.setEnabled(True)
        else:
            self.lbl_status_desc.setText(tr("Servidor inactivo."))
            self.lbl_status_desc.setStyleSheet("color: rgba(255,255,255,0.40); font-size: 11px;")
            self.btn_copy_ip.setEnabled(False)
    def _on_copy_ip(self):
        if getattr(self.player, 'remote_server', None):
            ip = self.player.remote_server.get_local_ip()
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(ip)
            notify.success(tr("Copiado"), tr("Dirección IP copiada al portapapeles."), self.player)
