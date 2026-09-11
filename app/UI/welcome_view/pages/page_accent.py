from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt6.QtCore import Qt, QTimer
from UI.welcome_view.components import make_label, ColorCircle, TEXT_WHITE, TEXT_DIM
from settings_manager import settings
import theme_manager
from core.language_manager import tr
class PageAccent(QWidget):
    def __init__(self, overlay, parent=None):
        super().__init__(parent)
        self.overlay = overlay
        self.mw = overlay.main_window
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.container = QWidget()
        self.container.setFixedWidth(600)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(16)
        title_style = f"font-size: 28px; font-weight: 800; color: {TEXT_WHITE.name()};"
        desc_style = f"font-size: 15px; color: {TEXT_DIM.name()};"
        self.title = make_label(tr("Hazlo tuyo"), title_style)
        self.desc = make_label(tr("Elige un color de acento. Este color iluminará toda tu experiencia."), desc_style)
        self.desc.setContentsMargins(0, 0, 0, 16)
        self.container_layout.addWidget(self.title)
        self.container_layout.addWidget(self.desc)
        grid = QGridLayout()
        grid.setSpacing(24)
        grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._circles = []
        current = settings.get('app_accent_name', 'Cian (AIIKO)')
        names = ["Color del Sistema"] + [n for n in theme_manager.get_accent_names() if n != "Color del Sistema"]
        row, col = 0, 0
        for name in names:
            hex_c = theme_manager.get_accent_hex(name)
            circle = ColorCircle(name, hex_c)
            circle.set_selected(name == current)
            circle.clicked.connect(self._on_accent_picked)
            self._circles.append(circle)
            grid.addWidget(circle, row, col)
            col += 1
            if col > 7:
                col = 0; row += 1
        self.container_layout.addLayout(grid)
        self.lbl_accent = make_label(current, f"font-size: 16px; font-weight: bold; color: {TEXT_WHITE.name()};")
        self.lbl_accent.setContentsMargins(0, 16, 0, 0)
        self.container_layout.addWidget(self.lbl_accent)
        from qfluentwidgets import SwitchButton
        net_widget = QWidget()
        net_layout = QHBoxLayout(net_widget)
        net_layout.setContentsMargins(0, 0, 0, 0)
        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        text_layout.setSpacing(2)
        lbl_title = make_label(tr("Obtener info de artistas online"), f"font-size: 15px; font-weight: bold; color: {TEXT_WHITE.name()};")
        lbl_desc = make_label(tr("Descarga fotos y biografías de artistas automáticamente desde internet."), f"font-size: 13px; color: {TEXT_DIM.name()};")
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_desc)
        self.switch_network = SwitchButton()
        self.switch_network.setChecked(settings.get('fetch_artist_info_network', False))
        self.switch_network.checkedChanged.connect(self._on_network_toggled)
        net_layout.addLayout(text_layout)
        net_layout.addStretch()
        net_layout.addWidget(self.switch_network)
        self.container_layout.addSpacing(16)
        self.container_layout.addWidget(net_widget)
        self.main_layout.addWidget(self.container)
    def _on_accent_picked(self, name, hex_c):
        for c in self._circles: c.set_selected(c._name == name)
        self.lbl_accent.setText(name)
        settings.set('app_accent_name', name)
        settings.save()
        self.overlay.update_dynamic_colors(hex_c)
        if hasattr(self.mw, 'theme_controller'):
            QTimer.singleShot(100, lambda: self.mw.theme_controller.change_accent(name))
    def update_dynamic_colors(self, hex_c):
        self.lbl_accent.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {hex_c}; background: transparent;")
    def _on_network_toggled(self, checked):
        settings.set('fetch_artist_info_network', checked)
        settings.save()
    def retranslate_ui(self):
        self.title.setText(tr("Hazlo tuyo"))
        self.desc.setText(tr("Elige un color de acento. Este color iluminará toda tu experiencia."))
