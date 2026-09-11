from PyQt6.QtWidgets import QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from qfluentwidgets import SwitchButton, FluentIcon as FIF, PushButton, ListWidget
from settings_manager import settings
from .base_settings_tab import BaseSettingsTab
from core.language_manager import tr
class LibraryTab(BaseSettingsTab):
    def __init__(self, player, parent=None):
        super().__init__(player, parent)
        card1, cl1 = self._create_card(tr("Escaneo"), FIF.SYNC)
        player.switch_auto_scan = SwitchButton()
        player.switch_auto_scan.checkedChanged.connect(player.settings_sync.toggle_auto_scan)
        self._setting_row(cl1, tr("Escaneo automático al inicio"),
                          tr("Busca nueva música en tus carpetas cada vez que abras la aplicación."),
                          player.switch_auto_scan, add_separator=True)
        player.switch_merge_albums = SwitchButton()
        is_merged = settings.get('merge_collaborative_albums', True)
        player.switch_merge_albums.setChecked(is_merged)
        player.switch_merge_albums.checkedChanged.connect(self._on_merge_toggled)
        self._setting_row(cl1, tr("Consolidación inteligente de álbumes"),
                          tr("Fusiona los álbumes colaborativos (basados en el artista principal) y agrupa la música sin clasificar en un solo 'Álbum Desconocido'."),
                          player.switch_merge_albums, add_separator=True)
        player.switch_fetch_artists = SwitchButton()
        player.switch_fetch_artists.setChecked(settings.get('fetch_artist_info_network', False))
        player.switch_fetch_artists.checkedChanged.connect(self._on_fetch_artists_toggled)
        self._setting_row(cl1, tr("Obtener info de artistas online"),
                          tr("Descarga fotos y biografías de artistas automáticamente desde internet."),
                          player.switch_fetch_artists, add_separator=False)
        self.main_layout.addWidget(card1)
        self.main_layout.addSpacing(16)
        card2, cl2 = self._create_card(tr("Carpetas de Música"), FIF.FOLDER)
        player.list_folders = ListWidget()
        player.list_folders.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        player.list_folders.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        player.list_folders.setStyleSheet(
            "ListWidget { background-color: rgba(0,0,0,0.15); border-radius: 8px; "
            "border: 1px solid rgba(255,255,255,0.06); }"
            "ListWidget::item { padding: 6px; margin: 4px; border-radius: 6px; }"
            "ListWidget::item:hover { background-color: rgba(255, 255, 255, 0.05); }"
            "ListWidget::item:selected { background-color: rgba(255, 255, 255, 0.1); }"
        )
        def _update_folders_height():
            count = player.list_folders.count()
            if count == 0:
                player.list_folders.setFixedHeight(60)
            else:
                player.list_folders.setFixedHeight(count * 45 + 16)
        player.list_folders.model().rowsInserted.connect(lambda: QTimer.singleShot(10, _update_folders_height))
        player.list_folders.model().rowsRemoved.connect(lambda: QTimer.singleShot(10, _update_folders_height))
        QTimer.singleShot(50, _update_folders_height)
        cl2.addWidget(player.list_folders)
        cl2.addSpacing(12)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_verify = PushButton(getattr(FIF, 'SYNC', FIF.SYNC), tr("Verificar"))
        btn_verify.clicked.connect(lambda: player.library_sync_controller.start_background_scan(force_full=False))
        btn_rescan = PushButton(getattr(FIF, 'UPDATE', FIF.SYNC), tr("Re-escanear Todo"))
        btn_rescan.clicked.connect(lambda: player.library_sync_controller.start_background_scan(force_full=True))
        btn_add = PushButton(FIF.FOLDER_ADD, tr("Añadir"))
        btn_add.clicked.connect(player.app_controller.add_folder)
        from qfluentwidgets import ToolButton
        btn_remove = ToolButton(FIF.DELETE)
        btn_remove.setToolTip(tr("Eliminar"))
        btn_remove.clicked.connect(player.app_controller.remove_folder)
        btn_restore_ignored = PushButton(FIF.HISTORY, tr("Restaurar Ignoradas"))
        btn_restore_ignored.clicked.connect(self._on_restore_ignored)
        btn_layout.addWidget(btn_verify)
        btn_layout.addWidget(btn_rescan)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_remove)
        btn_layout.addWidget(btn_restore_ignored)
        btn_layout.addStretch()
        cl2.addLayout(btn_layout)
        self.main_layout.addWidget(card2)
        self.main_layout.addSpacing(16)
        card3, cl3 = self._create_card(tr("Integración con el Sistema"), FIF.APPLICATION)
        self._setting_row(cl3, tr("Asociar archivos de audio y datos"),
                          tr("Registra Aiiko Music como programa compatible para abrir archivos .mp3, .flac, .wav, .ogg, .m4a y copias de seguridad (.aiiko)."),
                          self._make_os_button(tr("Asociar"), self._on_register_associations))
        self._setting_row(cl3, tr("Menú contextual del Explorador"),
                          tr("Añade las opciones 'Reproducir con Aiiko Music' y 'Añadir a la cola' al menú del clic derecho."),
                          self._make_os_button(tr("Registrar"), self._on_register_context_menu))
        self._setting_row(cl3, tr("Establecer como predeterminado"),
                          tr("Abre la configuración de Windows para que puedas elegir Aiiko Music como reproductor por defecto."),
                          self._make_os_button(tr("Abrir Ajustes"), self._on_set_default))
        self._setting_row(cl3, tr("Desregistrar todo"),
                          tr("Elimina todas las asociaciones y entradas del menú contextual creadas por Aiiko Music."),
                          self._make_os_button(tr("Desregistrar"), self._on_unregister),
                          add_separator=False)
        self.main_layout.addWidget(card3)
        self.main_layout.addStretch()
    def _make_os_button(self, text, callback):
        btn = PushButton(text)
        btn.clicked.connect(callback)
        return btn
    def _on_register_associations(self):
        from core.os_integration import register_file_associations
        from core.notification_manager import notify
        if register_file_associations():
            notify.success(tr("Asociaciones registradas"), tr("Aiiko Music ahora aparece como opción para abrir archivos de audio."))
        else:
            notify.error(tr("Error"), tr("No se pudieron registrar las asociaciones de archivo."))
    def _on_register_context_menu(self):
        from core.os_integration import register_context_menu
        from core.notification_manager import notify
        if register_context_menu():
            notify.success(tr("Menú contextual registrado"), tr("Las opciones 'Reproducir' y 'Añadir a la cola' ya están disponibles en el Explorador."))
        else:
            notify.error(tr("Error"), tr("No se pudo registrar el menú contextual."))
    def _on_set_default(self):
        from core.os_integration import set_as_default
        set_as_default()
    def _on_unregister(self):
        from core.os_integration import unregister_all
        from core.notification_manager import notify
        if unregister_all():
            notify.success(tr("Desregistrado"), tr("Todas las asociaciones y entradas del menú han sido eliminadas."))
        else:
            notify.error(tr("Error"), tr("No se pudo completar la desregistración."))
    def _on_merge_toggled(self, checked):
        settings.set('merge_collaborative_albums', checked)
        QTimer.singleShot(50, lambda: self.player.library_controller.refresh_library_views(skip_dashboard=True))
    def _on_fetch_artists_toggled(self, checked):
        settings.set('fetch_artist_info_network', checked)
        settings.save()
    def _on_restore_ignored(self):
        from database import get_ignored_tracks
        from core.notification_manager import notify
        from UI.dialogs.ignored_tracks_dialog import IgnoredTracksDialog
        ignored = get_ignored_tracks()
        if not ignored:
            notify.info(tr("Sin elementos"), tr("No hay canciones en la lista negra."))
            return
        dialog = IgnoredTracksDialog(ignored, self.player, parent=self.window())
        dialog.exec()
