from PyQt6.QtCore import pyqtSignal, QVariantAnimation, QEasingCurve, Qt, QTimer
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtGui import QPainter
class CustomAnimatedTabs(QWidget):
    currentItemChanged = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.items = {}
        self.callbacks = {}
        self.original_texts = {}
        self.original_icons = {}
        self.is_icon_mode = False
        self.current_key = None
        self.layout.addStretch()
        self.indicator_x = 0.0
        self.indicator_width = 0.0
        self.start_x = 0.0
        self.start_width = 0.0
        self.end_x = 0.0
        self.end_width = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuint)
        self.anim.valueChanged.connect(self._on_anim_step)
        self._pending_key = None
    def _on_anim_step(self, progress):
        self.indicator_x = self.start_x + (self.end_x - self.start_x) * progress
        self.indicator_width = self.start_width + (self.end_width - self.start_width) * progress
        self.update()
    def addItem(self, key, text, icon=None, callback=None):
        self.original_texts[key] = text
        self.original_icons[key] = icon
        btn = QPushButton()
        if self.is_icon_mode and icon:
            from PyQt6.QtCore import QSize
            btn.setIcon(icon.icon() if hasattr(icon, 'icon') else icon)
            btn.setIconSize(QSize(18, 18))
            btn.setToolTip(text)
        else:
            btn.setText(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFlat(True)
        btn.clicked.connect(lambda _, k=key: self.setCurrentItem(k, True))
        btn.setStyleSheet("""
            QPushButton {
                color: #A0A0A0;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 6px 12px;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        insert_pos = len(self.items)
        self.layout.insertWidget(insert_pos, btn)
        self.items[key] = btn
        self.callbacks[key] = callback
    def _get_target_metrics(self, btn):
        from PyQt6.QtGui import QFont, QFontMetrics
        font = btn.font()
        font.setPixelSize(16)
        font.setBold(True)
        fm = QFontMetrics(font)
        if self.is_icon_mode:
            content_width = 18.0                   
        else:
            content_width = float(fm.horizontalAdvance(btn.text()))
            if not btn.text() and self.current_key:
                 content_width = float(fm.horizontalAdvance(self.original_texts.get(self.current_key, "")))
        btn_center_x = float(btn.x()) + float(btn.width()) / 2.0
        return btn_center_x - (content_width / 2.0), content_width
    def set_icon_mode(self, enabled):
        if self.is_icon_mode == enabled:
            return
        self.is_icon_mode = enabled
        from PyQt6.QtCore import QSize
        from PyQt6.QtGui import QIcon
        for key, btn in self.items.items():
            if enabled:
                btn.setText("")
                btn.setFixedWidth(40)
                icon = self.original_icons.get(key)
                if icon:
                    btn.setIcon(icon.icon() if hasattr(icon, 'icon') else icon)
                    btn.setIconSize(QSize(18, 18))
                btn.setToolTip(self.original_texts.get(key, ""))
            else:
                btn.setText(self.original_texts.get(key, ""))
                btn.setMinimumWidth(0)
                btn.setMaximumWidth(16777215)
                btn.setIcon(QIcon())
                btn.setToolTip("")
        self.layout.invalidate()
        self.layout.activate()
        if self.current_key and self.current_key in self.items:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self._update_indicator_now)
    def _update_indicator_now(self):
        if self.current_key and self.current_key in self.items:
            btn = self.items[self.current_key]
            self.indicator_x, self.indicator_width = self._get_target_metrics(btn)
            self.update()
    def currentRouteKey(self):
        return self.current_key
    def setCurrentItem(self, key, trigger=False):
        if key not in self.items: return
        self.current_key = key
        btn = self.items[key]
        for k, b in self.items.items():
            if k == key:
                b.setStyleSheet("""
                    QPushButton {
                        color: white;
                        font-size: 16px;
                        font-weight: bold;
                        background: transparent;
                        border: none;
                        padding: 6px 12px;
                    }
                """)
            else:
                b.setStyleSheet("""
                    QPushButton {
                        color: #A0A0A0;
                        font-size: 16px;
                        font-weight: bold;
                        background: transparent;
                        border: none;
                        padding: 6px 12px;
                    }
                    QPushButton:hover {
                        color: white;
                    }
                """)
        self.end_x, self.end_width = self._get_target_metrics(btn)
        if self.indicator_width == 0:
            self._pending_key = key
            self.update()
        else:
            self.start_x = self.indicator_x
            self.start_width = self.indicator_width
            self.anim.stop()
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.anim.start()
        if trigger and key in self.callbacks and self.callbacks[key] is not None:
            self.callbacks[key]()
        self.currentItemChanged.emit(key)
    def showEvent(self, event):
        super().showEvent(event)
        def _update_indicator_later():
            if self._pending_key and self._pending_key in self.items:
                btn = self.items[self._pending_key]
                self.indicator_x, self.indicator_width = self._get_target_metrics(btn)
                self._pending_key = None
                self.update()
            elif self.current_key and self.current_key in self.items:
                btn = self.items[self.current_key]
                self.indicator_x, self.indicator_width = self._get_target_metrics(btn)
                self.update()
        QTimer.singleShot(0, _update_indicator_later)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_key and self.current_key in self.items and self.anim.state() != QVariantAnimation.State.Running:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self._update_indicator_now)
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.indicator_width == 0: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        from qfluentwidgets import themeColor
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(themeColor())
        y = self.height() - 3
        painter.drawRoundedRect(int(self.indicator_x), y, int(self.indicator_width), 3, 1.5, 1.5)
        painter.end()