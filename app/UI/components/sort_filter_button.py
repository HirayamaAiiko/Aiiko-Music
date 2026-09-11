from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from qfluentwidgets import DropDownToolButton, RoundMenu, Action, FluentIcon as FIF
from core.language_manager import tr
class SortFilterButton(QWidget):
    currentIndexChanged = pyqtSignal(int)
    def __init__(self, options, parent=None):
        super().__init__(parent)
        self._options = options
        self._current_index = -1
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.btn = DropDownToolButton(FIF.SCROLL, self)
        self.btn.setToolTip(tr("Ordenar"))
        layout.addWidget(self.btn)
        self.sort_menu = RoundMenu(parent=self.btn)
        self.sort_actions = []
        for i, opt in enumerate(options):
            action = Action(opt, triggered=lambda c, idx=i: self.setCurrentIndex(idx))
            self.sort_menu.addAction(action)
            self.sort_actions.append(action)
        self.btn.setMenu(self.sort_menu)
    def clear(self):
        self._options.clear()
        self._current_index = -1
        self.sort_menu.clear()
        self.sort_actions.clear()
    def addItems(self, options):
        start_idx = len(self._options)
        self._options.extend(options)
        for i, opt in enumerate(options):
            idx = start_idx + i
            action = Action(opt, triggered=lambda c, x=idx: self.setCurrentIndex(x))
            self.sort_menu.addAction(action)
            self.sort_actions.append(action)
    def setCurrentIndex(self, index):
        if not (0 <= index < len(self._options)):
            return
        import theme_manager
        from PyQt6.QtGui import QPixmap, QIcon, QColor
        from PyQt6.QtCore import Qt
        accent = theme_manager.get_current_accent_hex()
        empty_pix = QPixmap(16, 16)
        empty_pix.fill(Qt.GlobalColor.transparent)
        empty_icon = QIcon(empty_pix)
        active_icon = FIF.ACCEPT.icon(color=accent)
        if self._current_index != index:
            self._current_index = index
            for i, act in enumerate(self.sort_actions):
                act.setIcon(active_icon if i == index else empty_icon)
            self.currentIndexChanged.emit(index)
        else:
            for i, act in enumerate(self.sort_actions):
                act.setIcon(active_icon if i == index else empty_icon)
    def currentIndex(self):
        return self._current_index
    def count(self):
        return len(self._options)