from PyQt6.QtCore import Qt, QEvent, pyqtSignal
from PyQt6.QtGui import QKeySequence, QKeyEvent
from PyQt6.QtWidgets import QHBoxLayout
from qfluentwidgets import PushButton, PrimaryPushButton
from settings_manager import settings
from core.language_manager import tr
from core.notification_manager import notify
from UI.settings_tabs.base_settings_tab import BaseSettingsTab
class ShortcutGrabberButton(PushButton):
    shortcutCaptured = pyqtSignal(str)
    def __init__(self, current_sequence="", parent=None):
        super().__init__(parent)
        self.setText(current_sequence)
        self.is_recording = False
        self.setCheckable(True)
        self.toggled.connect(self._on_toggled)
        self.setMinimumWidth(150)
    def _on_toggled(self, checked):
        self.is_recording = checked
        if checked:
            self.setText(tr("Presiona una tecla..."))
            self.setFocus()
        else:
            self.clearFocus()
    def keyPressEvent(self, event: QKeyEvent):
        if not self.is_recording:
            super().keyPressEvent(event)
            return
        key = event.key()
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta, Qt.Key.Key_AltGr):
            return
        modifiers = event.modifiers()
        key_sequence = ""
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            key_sequence += "Ctrl+"
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            key_sequence += "Shift+"
        if modifiers & Qt.KeyboardModifier.AltModifier:
            key_sequence += "Alt+"
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            key_sequence += "Meta+"
        key_string = QKeySequence(key).toString()
        if not key_string:
            key_string = chr(key) if key < 256 else "Unknown"
        key_sequence += key_string
        self.setText(key_sequence)
        self.setChecked(False)
        self.is_recording = False
        self.shortcutCaptured.emit(key_sequence)
    def focusOutEvent(self, event):
        if self.is_recording:
            self.setChecked(False)
            self.is_recording = False
            self.setText(tr("Cancelado"))
        super().focusOutEvent(event)
class ShortcutsTab(BaseSettingsTab):
    def __init__(self, player, parent=None):
        super().__init__(player, parent)
        self._build_ui()
    def _build_ui(self):
        from qfluentwidgets import FluentIcon as FIF
        card, layout = self._create_card(tr("Atajos de Teclado"), icon=FIF.COMMAND_PROMPT)
        self.buttons = {}
        custom_shortcuts = settings.get('custom_shortcuts', {})
        default_shortcuts = self.player.shortcut_controller.DEFAULT_SHORTCUTS
        btn_reset = PrimaryPushButton(tr("Restaurar por defecto"))
        btn_reset.clicked.connect(self._restore_defaults)
        reset_layout = QHBoxLayout()
        reset_layout.addWidget(btn_reset, 0, Qt.AlignmentFlag.AlignRight)
        for action_id, data in default_shortcuts.items():
            current_key = custom_shortcuts.get(action_id, data["default"])
            btn_grabber = ShortcutGrabberButton(current_key)
            btn_grabber.shortcutCaptured.connect(
                lambda key, aid=action_id: self._on_shortcut_changed(aid, key)
            )
            btn_grabber.toggled.connect(
                lambda checked: self.player.shortcut_controller.set_enabled(not checked)
            )
            self.buttons[action_id] = btn_grabber
            self._setting_row(
                layout,
                data["name"],
                tr("Haz clic en el botón para asignar un nuevo atajo."),
                btn_grabber
            )
        layout.addSpacing(10)
        layout.addLayout(reset_layout)
        self.main_layout.addWidget(card)
        self.main_layout.addStretch()
    def _on_shortcut_changed(self, action_id, new_key):
        custom_shortcuts = settings.get('custom_shortcuts', {})
        default_shortcuts = self.player.shortcut_controller.DEFAULT_SHORTCUTS
        in_use_by = None
        for a_id, data in default_shortcuts.items():
            if a_id == action_id:
                continue
            current_key = custom_shortcuts.get(a_id, data["default"])
            if current_key == new_key:
                in_use_by = data["name"]
                break
        if in_use_by:
            notify.warning(
                tr("Atajo en uso"),
                f"{tr('El atajo')} {new_key} {tr('ya está asignado a')} '{in_use_by}'."
            )
        self.player.shortcut_controller.update_shortcut(action_id, new_key)
        updated_custom = settings.get('custom_shortcuts', {})
        for a_id, btn in self.buttons.items():
            curr = updated_custom.get(a_id, default_shortcuts[a_id]["default"])
            if btn.text() != curr:
                btn.setText(curr)
    def _restore_defaults(self):
        self.player.shortcut_controller.restore_defaults()
        custom_shortcuts = settings.get('custom_shortcuts', {})
        default_shortcuts = self.player.shortcut_controller.DEFAULT_SHORTCUTS
        for action_id, btn in self.buttons.items():
            current_key = custom_shortcuts.get(action_id, default_shortcuts[action_id]["default"])
            btn.setText(current_key)