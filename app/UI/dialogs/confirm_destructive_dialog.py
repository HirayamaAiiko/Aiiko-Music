from PyQt6.QtWidgets import QHBoxLayout
from qfluentwidgets import TitleLabel, BodyLabel, PushButton, MessageBoxBase
from settings_manager import settings
from core.language_manager import tr
class ConfirmDestructiveDialog(MessageBoxBase):
    def __init__(self, title, content, btn_soft_text, btn_hard_text, parent=None):
        super().__init__(parent)
        self.widget.setMinimumWidth(460)
        self.yesButton.hide()
        self.cancelButton.hide()
        if hasattr(self, 'buttonGroup'):
            self.buttonGroup.hide()
        self.titleLabel = TitleLabel(title, self)
        self.contentLabel = BodyLabel(content, self)
        self.contentLabel.setWordWrap(True)
        is_dark = settings.get('themeMode', 'Dark') == 'Dark'
        self.contentLabel.setStyleSheet(f"color: {'#CCCCCC' if is_dark else '#555555'}; background: transparent; border: none;")
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.contentLabel)
        self.viewLayout.addSpacing(16)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_cancel = PushButton(tr("Cancelar"), self)
        btn_soft = PushButton(btn_soft_text, self)
        btn_hard = PushButton(btn_hard_text, self)
        btn_hard.setStyleSheet("""
            PushButton { background-color: #d83b01; color: white; border: none; font-weight: bold; border-radius: 5px; padding: 6px 16px; }
            PushButton:hover { background-color: #e04a15; }
            PushButton:pressed { background-color: #b83201; }
        """)
        self.result_code = 0
        def on_soft():
            self.result_code = 1
            self.accept()
        def on_hard():
            self.result_code = 2
            self.accept()
        def on_cancel():
            self.result_code = 0
            self.reject()
        btn_soft.clicked.connect(on_soft)
        btn_hard.clicked.connect(on_hard)
        btn_cancel.clicked.connect(on_cancel)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch(1)
        btn_layout.addWidget(btn_soft)
        btn_layout.addWidget(btn_hard)
        self.viewLayout.addLayout(btn_layout)