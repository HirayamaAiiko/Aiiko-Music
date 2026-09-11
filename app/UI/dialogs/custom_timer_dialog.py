from PyQt6.QtWidgets import QHBoxLayout
from qfluentwidgets import MessageBoxBase, SubtitleLabel, ComboBox, SpinBox, BodyLabel
from core.language_manager import tr
class CustomTimerDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.widget.setMinimumWidth(350)
        self.titleLabel = SubtitleLabel(tr("Temporizador Personalizado"), self.widget)
        self.mode_combo = ComboBox(self.widget)
        self.mode_combo.addItem(tr("Minutos"), userData="time")
        self.mode_combo.addItem(tr("Canciones"), userData="song")
        self.value_spin = SpinBox(self.widget)
        self.value_spin.setRange(1, 999)
        self.value_spin.setValue(15)
        self.viewLayout.addWidget(self.titleLabel)
        h_layout = QHBoxLayout()
        h_layout.addWidget(BodyLabel(tr("Apagar tras: "), self.widget))
        h_layout.addWidget(self.value_spin)
        h_layout.addWidget(self.mode_combo)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addLayout(h_layout)
        self.viewLayout.addSpacing(10)
        self.yesButton.setText(tr("Aceptar"))
        self.cancelButton.setText(tr("Cancelar"))
    def get_result(self):
        mode = self.mode_combo.currentData()
        value = self.value_spin.value()
        return mode, value