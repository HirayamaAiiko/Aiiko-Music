from PyQt6.QtWidgets import QVBoxLayout
from qfluentwidgets import SubtitleLabel, CaptionLabel, LineEdit, MessageBoxBase
from core.language_manager import tr
class PlaylistCreateDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.widget.setMinimumWidth(360)
        self._build_ui()
    def _build_ui(self):
        self.yesButton.setText(tr("Crear"))
        self.cancelButton.setText(tr("Cancelar"))
        self.titleLabel = SubtitleLabel(tr("Crear Playlist"), self)
        self.titleLabel.setStyleSheet("font-size: 17px; font-weight: bold; margin-bottom: 8px;")
        self.viewLayout.addWidget(self.titleLabel)
        self.hintLabel = CaptionLabel(tr("Nombre de la nueva playlist"), self)
        self.hintLabel.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 11px; margin-bottom: 4px;")
        self.viewLayout.addWidget(self.hintLabel)
        self._name_edit = LineEdit(self)
        self._name_edit.setPlaceholderText(tr("Ej. Favoritas, Rock 80s..."))
        self._name_edit.setFixedHeight(36)
        self._name_edit.returnPressed.connect(self._accept_dialog)
        self.viewLayout.addWidget(self._name_edit)
        self._name_edit.textChanged.connect(self._validate)
        self._validate(self._name_edit.text())
    def _validate(self, text):
        self.yesButton.setEnabled(bool(text.strip()))
    def _accept_dialog(self):
        if self.yesButton.isEnabled():
            self.accept()
    def get_name(self) -> str:
        return self._name_edit.text().strip()
    def showEvent(self, event):
        super().showEvent(event)
        self._name_edit.setFocus()