from PyQt6.QtCore import Qt
from qfluentwidgets import ComboBox, SwitchButton, FluentIcon as FIF
from settings_manager import settings
from core.language_manager import tr, lang_manager
from .base_settings_tab import BaseSettingsTab
class GeneralTab(BaseSettingsTab):
    def __init__(self, player, parent=None):
        super().__init__(player, parent)
        card_start, cl_start = self._create_card(tr("Arranque"), FIF.HOME)
        player.combo_startup_tab = ComboBox()
        self.startup_map = [
            ('dashboard', tr("Inicio")),
            ('library', tr("Biblioteca")),
            ('favorites', tr("Favoritos")),
            ('playlists', tr("Playlists"))
        ]
        for key, text in self.startup_map:
            player.combo_startup_tab.addItem(text, userData=key)
        old_val = settings.get('startup_tab', 'dashboard')
        if old_val in ['Inicio', 'Home']: old_val = 'dashboard'
        elif old_val in ['Biblioteca', 'Library']: old_val = 'library'
        elif old_val in ['Favoritos', 'Favorites']: old_val = 'favorites'
        elif old_val == 'Playlists': old_val = 'playlists'
        current_idx = player.combo_startup_tab.findData(old_val)
        if current_idx >= 0:
            player.combo_startup_tab.setCurrentIndex(current_idx)
        player.combo_startup_tab.currentIndexChanged.connect(
            lambda idx: (settings.set('startup_tab', player.combo_startup_tab.itemData(idx)), settings.save())
        )
        self._setting_row(cl_start, tr("Pestaña Principal por Defecto"),
                          tr("Selecciona la sección de la aplicación que se abrirá al iniciar Aiiko."),
                          player.combo_startup_tab, add_separator=False)
        self.main_layout.addWidget(card_start)
        self.main_layout.addSpacing(16)
        card2, cl2 = self._create_card(tr("Bandeja del Sistema"), FIF.MINIMIZE)
        player.switch_minimize_tray = SwitchButton()
        player.switch_minimize_tray.setChecked(settings.get('minimize_to_tray', False))
        player.switch_minimize_tray.checkedChanged.connect(
            lambda checked: (settings.set('minimize_to_tray', checked), settings.save())
        )
        self._setting_row(cl2, tr("Minimizar a la bandeja"),
                          tr("Oculta la ventana en la bandeja del sistema al minimizar."),
                          player.switch_minimize_tray)
        player.switch_close_tray = SwitchButton()
        player.switch_close_tray.setChecked(settings.get('close_to_tray', False))
        player.switch_close_tray.checkedChanged.connect(
            lambda checked: (settings.set('close_to_tray', checked), settings.save())
        )
        self._setting_row(cl2, tr("Cerrar a la bandeja"),
                          tr("Sigue reproduciendo en la bandeja al cerrar la ventana."),
                          player.switch_close_tray, add_separator=False)
        self.main_layout.addWidget(card2)
        self.main_layout.addSpacing(16)
        card3, cl3 = self._create_card(tr("Idioma y Depuración"), FIF.LANGUAGE)
        self.combo_app_lang = ComboBox()
        avail_langs = lang_manager.get_available_languages()
        for code, name in avail_langs.items():
            self.combo_app_lang.addItem(name, userData=code)
        current_code = settings.get('language', 'es')
        current_idx = self.combo_app_lang.findData(current_code)
        if current_idx >= 0:
            self.combo_app_lang.setCurrentIndex(current_idx)
        self.combo_app_lang.currentIndexChanged.connect(self._change_app_lang)
        self._setting_row(cl3, tr("Idioma de la Interfaz (App)"),
                          tr("Selecciona el idioma de Aiiko Music (requiere reinicio para aplicar en todas las vistas)."),
                          self.combo_app_lang)
        player.combo_translation_lang = ComboBox()
        player.combo_translation_lang.addItems(["es", "en", "fr", "pt", "ja", "de", "it"])
        player.combo_translation_lang.setCurrentText(settings.get('translation_lang', 'es'))
        player.combo_translation_lang.currentTextChanged.connect(player.settings_ui_controller.change_translation_lang)
        self._setting_row(cl3, tr("Idioma de Traducción de Letras"),
                          tr("Selecciona a qué idioma se traducirán las letras de las canciones."),
                          player.combo_translation_lang)
        player.switch_enable_logs = SwitchButton()
        player.switch_enable_logs.checkedChanged.connect(player.settings_sync.toggle_logs)
        self._setting_row(cl3, tr("Registro de Logs"),
                          tr("Activa la escritura de logs para depuración de errores."),
                          player.switch_enable_logs, add_separator=False)
        self.main_layout.addWidget(card3)
        self.main_layout.addStretch()
    def _change_app_lang(self, idx):
        code = self.combo_app_lang.itemData(idx)
        if code != settings.get('language', 'es'):
            settings.set('language', code)
            settings.save()
            lang_manager.load_language(code)
            from core.language_manager import tr
            from qfluentwidgets import MessageBox
            import sys, subprocess
            from PyQt6.QtWidgets import QApplication
            w = MessageBox(
                tr("Reiniciar aplicación"),
                tr("Para aplicar el nuevo idioma a toda la interfaz, es necesario reiniciar la aplicación. ¿Deseas reiniciar ahora?"),
                self.window()
            )
            w.yesButton.setText(tr("Reiniciar ahora"))
            w.cancelButton.setText(tr("Más tarde"))
            if w.exec():
                if getattr(sys, 'frozen', False):
                    subprocess.Popen([sys.executable, '--restart'])
                else:
                    subprocess.Popen([sys.executable] + sys.argv + ['--restart'])
                QApplication.quit()
