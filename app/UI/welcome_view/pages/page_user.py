from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from qfluentwidgets import LineEdit
from UI.welcome_view.components import make_label, TEXT_WHITE, TEXT_DIM
from settings_manager import settings
from core.language_manager import tr
class PageUser(QWidget):
    def __init__(self, overlay, parent=None):
        super().__init__(parent)
        self.overlay = overlay
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
        self.title = make_label(tr("¿Cómo te llamamos?"), title_style)
        self.desc = make_label(tr("Ingresa un nombre para tu perfil. Esto es para el dashboard y tus estadísticas de escucha locales."), desc_style)
        self.desc.setContentsMargins(0, 0, 0, 16)
        self.container_layout.addWidget(self.title)
        self.container_layout.addWidget(self.desc)
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText(tr("Tu nombre o apodo"))
        self.name_edit.setMaxLength(40)
        self.name_edit.setFixedHeight(44)
        self.name_edit.setMinimumWidth(0)
        self.name_edit.setMaximumWidth(16777215)
        current = settings.get("user_profile_name", "")
        if current:
            self.name_edit.setText(current)
        self.name_edit.textChanged.connect(lambda t: settings.set("user_profile_name", t.strip()))
        self.container_layout.addWidget(self.name_edit)
        self.main_layout.addWidget(self.container)
    def update_dynamic_colors(self, hex_c):
        pass
    def retranslate_ui(self):
        self.title.setText(tr("¿Cómo te llamamos?"))
        self.desc.setText(tr("Ingresa un nombre para tu perfil. Esto es para el dashboard y tus estadísticas de escucha locales."))
        self.name_edit.setPlaceholderText(tr("Tu nombre o apodo"))
