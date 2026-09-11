from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout
from qfluentwidgets import ComboBox, SwitchButton, Slider, FluentIcon as FIF, PushButton, LineEdit, CaptionLabel
from settings_manager import settings
from .base_settings_tab import BaseSettingsTab
from core.language_manager import tr
class PlaybackTab(BaseSettingsTab):
    def __init__(self, player, parent=None):
        super().__init__(player, parent)
        card1, cl1 = self._create_card(tr("Salida de Audio"), FIF.HEADPHONE)
        player.combo_audio_output = ComboBox()
        player.combo_audio_output.setFixedWidth(200)
        player.combo_audio_output.currentTextChanged.connect(player.settings_ui_controller.change_audio_output)
        self._setting_row(cl1, tr("Módulo de Salida"),
                          tr("API de sonido (DirectSound / WASAPI). WASAPI Exclusive bloquea el audio de otras apps."),
                          player.combo_audio_output)
        player.combo_audio_device = ComboBox()
        player.combo_audio_device.setFixedWidth(300)
        player.combo_audio_device.currentIndexChanged.connect(player.settings_ui_controller.change_audio_device)
        self._setting_row(cl1, tr("Dispositivo de Sonido"),
                          tr("Selecciona por qué altavoces o auriculares reproducir."),
                          player.combo_audio_device)
        player.input_buffer_size = LineEdit()
        player.input_buffer_size.setFixedWidth(100)
        player.input_buffer_size.setText(str(settings.get('audio_buffer_ms', 400)))
        player.btn_apply_buffer = PushButton(tr("Aplicar"))
        player.btn_apply_buffer.setFixedWidth(100)
        player.btn_apply_buffer.clicked.connect(player.settings_ui_controller.apply_buffer_size)
        buffer_ctrl = QHBoxLayout()
        buffer_ctrl.setSpacing(8)
        buffer_ctrl.addWidget(player.input_buffer_size)
        buffer_ctrl.addWidget(player.btn_apply_buffer)
        self._setting_row_layout(cl1, tr("Tamaño del Búfer"),
                                 tr("Audio pre-cargado en ms (defecto: 400). Mayor valor = más estable, menos reactivo."),
                                 buffer_ctrl, add_separator=True)
        player.toggle_fade_audio = SwitchButton()
        player.toggle_fade_audio.setOnText(tr("Sí"))
        player.toggle_fade_audio.setOffText(tr("No"))
        player.toggle_fade_audio.setChecked(settings.get('fade_audio', True))
        player.toggle_fade_audio.checkedChanged.connect(
            lambda checked: (settings.set('fade_audio', checked), settings.save(), player.audio_engine.reload_settings())
        )
        self._setting_row(cl1, tr("Fade In/Out de Audio"),
                          tr("Suaviza las transiciones al reproducir, pausar o reanudar (300ms). Desactívalo para un control instantáneo."),
                          player.toggle_fade_audio, add_separator=False)
        self.main_layout.addWidget(card1)
        self.main_layout.addSpacing(16)
        card2, cl2 = self._create_card(tr("Transiciones"), FIF.SCROLL)
        crossfade_ctrl = QHBoxLayout()
        crossfade_ctrl.setSpacing(10)
        player.crossfade_slider = Slider(Qt.Orientation.Horizontal)
        player.crossfade_slider.setRange(1, 12)
        player.crossfade_slider.setValue(settings.get('crossfade_seconds', 3))
        player.crossfade_slider.setFixedWidth(120)
        player.crossfade_slider.valueChanged.connect(player.settings_ui_controller.on_crossfade_seconds_changed)
        player.crossfade_label = CaptionLabel(f"{settings.get('crossfade_seconds', 3)}s")
        player.crossfade_label.setFixedWidth(25)
        player.switch_crossfade = SwitchButton()
        player.switch_crossfade.setChecked(settings.get('crossfade_enabled', False))
        player.switch_crossfade.checkedChanged.connect(player.settings_ui_controller.toggle_crossfade)
        crossfade_ctrl.addWidget(player.crossfade_slider)
        crossfade_ctrl.addWidget(player.crossfade_label)
        crossfade_ctrl.addWidget(player.switch_crossfade)
        self._setting_row_layout(cl2, tr("Crossfade"),
                                 tr("Desvanecimiento suave entre canciones consecutivas."),
                                 crossfade_ctrl, add_separator=False)
        self.main_layout.addWidget(card2)
        self.main_layout.addSpacing(16)
        self.main_layout.addStretch()
