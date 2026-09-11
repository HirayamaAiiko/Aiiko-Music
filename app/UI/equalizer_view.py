from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QWidget, QPushButton, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QSize, QRectF, QPoint, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QPolygonF, QLinearGradient
from qfluentwidgets import (Slider, ComboBox, SwitchButton, TransparentToolButton, 
                            FluentIcon as FIF, PushButton, MessageBoxBase, SubtitleLabel, LineEdit)
from theme_manager import get_current_accent_hex, get_theme
from settings_manager import settings
class EQVerticalSlider(Slider):
    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Vertical, parent)
        self.setRange(-150, 150)
        self.setMinimumHeight(180)
        self.setInvertedControls(True)
        self.valueChanged.connect(self.update)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self.height()
        w = self.width()
        r = 8                      
        cx = w / 2
        margin = r + 1.5
        val_ratio = (self.value() - self.minimum()) / (self.maximum() - self.minimum())
        handle_y = margin + (h - 2*margin) * val_ratio
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 30))
        painter.drawRoundedRect(QRectF(cx - 1, margin, 2, h - 2*margin), 1, 1)
        is_enabled = getattr(self, 'is_enabled', True)
        accent = QColor(get_current_accent_hex()) if is_enabled else QColor("#555555")
        painter.setBrush(accent)
        painter.drawRoundedRect(QRectF(cx - 1, handle_y, 2, (h - margin) - handle_y), 1, 1)
        handle_rect = QRectF(cx - r, handle_y - r, r*2, r*2).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setBrush(QColor("#2A2A2A"))
        painter.setPen(QPen(QColor(255, 255, 255, 50), 1.0))
        painter.drawEllipse(handle_rect)
        inner_r = 4.5
        painter.setBrush(accent)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - inner_r, handle_y - inner_r, inner_r*2, inner_r*2))
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLineEdit
class ValueBadge(QLineEdit):
    valueChanged = pyqtSignal(float)
    def __init__(self, value, parent=None):
        super().__init__(parent)
        self.value = value
        self.is_enabled = True
        self.setFixedSize(40, 22)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.editingFinished.connect(self._on_editing_finished)
        self._update_appearance()
    def set_value(self, value):
        if not self.hasFocus():
            self.value = value
            self._update_appearance()
    def _update_appearance(self):
        val_str = f"{self.value:+.1f}"
        self.setText(val_str)
        accent = get_current_accent_hex() if self.is_enabled else "#555555"
        text_color = accent if self.value != 0.0 else "#AAAAAA"
        current_state = (accent, text_color)
        if getattr(self, '_last_style_state', None) != current_state:
            self.setStyleSheet(f"""
                QLineEdit {{
                    background-color: #151820;
                    border-radius: 4px;
                    color: {text_color};
                    font-size: 11px;
                    font-weight: 500;
                    border: 1px solid rgba(255, 255, 255, 10);
                }}
                QLineEdit:focus {{
                    border: 1px solid {accent};
                    background-color: #1A1D26;
                }}
            """)
            self._last_style_state = current_state
    def _on_editing_finished(self):
        text = self.text().replace(',', '.').replace('+', '')
        try:
            new_val = float(text)
            new_val = max(-15.0, min(15.0, new_val))
        except ValueError:
            new_val = self.value
        if new_val != self.value:
            self.value = new_val
            self.valueChanged.emit(self.value)
        self._update_appearance()
class PresetInputDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Guardar Perfil", self)
        self.lineEdit = LineEdit(self)
        self.lineEdit.setPlaceholderText("Nombre del preajuste")
        self.lineEdit.setClearButtonEnabled(True)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.lineEdit)
        self.widget.setMinimumWidth(320)
        self.yesButton.setText("Guardar")
        self.cancelButton.setText("Cancelar")
class EqualizerSlider(QWidget):
    def __init__(self, index, freq_label, initial_value, parent=None):
        super().__init__(parent)
        self.index = index
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        self.slider = EQVerticalSlider()
        self.slider.setValue(-int(initial_value * 10))
        self.freq_label = QLabel(freq_label)
        self.freq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.freq_label.setStyleSheet("font-size: 11px; font-weight: 500; color: #CCCCCC;")
        self.value_badge = ValueBadge(initial_value)
        self.value_badge.valueChanged.connect(self._on_badge_changed)
        self.layout.addWidget(self.slider, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(self.freq_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(self.value_badge, alignment=Qt.AlignmentFlag.AlignHCenter)
    def _on_badge_changed(self, value):
        self.slider.setValue(-int(value * 10))
    def set_value(self, value):
        self.slider.blockSignals(True)
        self.slider.setValue(-int(value * 10))
        self.update_label_text(value)
        self.slider.blockSignals(False)
    def update_label_text(self, value):
        self.value_badge.set_value(value)
class EQGraphContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sliders = []                                 
    def set_sliders(self, sliders):
        self.sliders = sliders
    def paintEvent(self, event):
        if not self.sliders:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        first_sl = self.sliders[0].slider
        r = 8                   
        pt_top = first_sl.mapTo(self, QPoint(0, r))
        pt_bottom = first_sl.mapTo(self, QPoint(0, first_sl.height() - r))
        top_y = pt_top.y()
        bottom_y = pt_bottom.y()
        pen = QPen(QColor(255, 255, 255, 30))
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        steps = 4
        for i in range(steps + 1):
            y = top_y + (bottom_y - top_y) * (i / steps)
            painter.drawLine(0, int(y), self.width(), int(y))
        points = []
        for eq_widget in self.sliders:
            sl = eq_widget.slider
            val_ratio = (sl.value() - sl.minimum()) / (sl.maximum() - sl.minimum())
            handle_y = r + (sl.height() - 2*r) * val_ratio
            pt = sl.mapTo(self, QPoint(int(sl.width()/2), int(handle_y)))
            points.append(pt)
        if len(points) < 2:
            return
        poly = QPolygonF()
        poly.append(QPointF(points[0].x(), bottom_y))
        for p in points:
            poly.append(QPointF(p))
        poly.append(QPointF(points[-1].x(), bottom_y))
        is_enabled = getattr(self, 'is_enabled', True)
        base_color = QColor(get_current_accent_hex()) if is_enabled else QColor("#555555")
        grad = QLinearGradient(0, top_y, 0, bottom_y)
        c1 = QColor(base_color)
        c1.setAlpha(60)                    
        c2 = QColor(base_color)
        c2.setAlpha(0)                        
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawPolygon(poly)
        line_pen = QPen(base_color, 1.5)
        painter.setPen(line_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(len(points)-1):
            painter.drawLine(points[i], points[i+1])
class OutlineButton(QPushButton):
    def __init__(self, icon, text, parent=None):
        super().__init__(text, parent)
        self.icon_enum = icon
        self.setIcon(icon.icon(color=QColor("#DDDDDD")))
        self._hovered = False
        self.setStyleSheet("""
            QPushButton { color: #DDDDDD; background: transparent; border: none; padding: 0 12px; font-size: 13px; font-weight: 500; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)
    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 15))
            painter.drawRoundedRect(0, 0, self.width(), self.height(), 6, 6)
        pen = QPen(QColor(255, 255, 255, 30))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0), 5.5, 5.5)
        painter.end()
        super().paintEvent(event)
class EqualizerDialog(QDialog):
    def __init__(self, eq_controller, parent=None):
        super().__init__(parent)
        self.eq_controller = eq_controller
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Ecualizador")
        self.setFixedSize(760, 480)
        self._is_updating = False
        self._is_tracking = False
        self._start_pos = None
        theme = get_theme(settings.get('app_theme', 'Oscuro (Dark)'))
        self.bg_color = '#0B0E14'
        self.init_ui()
        self.load_state()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        painter.setBrush(QBrush(QColor(self.bg_color)))
        painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5), 10, 10)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.pos().y() < 70:
                self._is_tracking = True
                self._start_pos = event.pos()
                event.accept()
    def mouseMoveEvent(self, event):
        if self._is_tracking and self._start_pos is not None:
            self.move(self.pos() + event.pos() - self._start_pos)
            event.accept()
    def mouseReleaseEvent(self, event):
        self._is_tracking = False
        event.accept()
    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(0)
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(5, 0, 5, 20)
        icon_lbl = QLabel()
        import os
        from config import RESOURCES_DIR
        from PyQt6.QtGui import QPixmap, QPainter
        icon_path = os.path.join(RESOURCES_DIR, "buttons", "equalizer.svg")
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            tinted = QPixmap(pixmap.size())
            tinted.fill(Qt.GlobalColor.transparent)
            painter = QPainter(tinted)
            painter.drawPixmap(0, 0, pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(tinted.rect(), QColor(get_current_accent_hex()))
            painter.end()
            icon_lbl.setPixmap(tinted.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            icon_lbl.setPixmap(FIF.MIX_VOLUMES.icon(color=QColor(get_current_accent_hex())).pixmap(28, 28))
        self.header_layout.addWidget(icon_lbl)
        self.header_layout.addSpacing(10)
        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)
        self.title_label = QLabel("Ecualizador")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        self.subtitle_label = QLabel("Ajusta el sonido a tu preferencia")
        self.subtitle_label.setStyleSheet("font-size: 12px; color: #888888;")
        title_vbox.addWidget(self.title_label)
        title_vbox.addWidget(self.subtitle_label)
        self.header_layout.addLayout(title_vbox)
        self.header_layout.addStretch()
        lbl_activo = QLabel("Activado")
        lbl_activo.setStyleSheet("color: #DDDDDD; font-size: 13px;")
        self.header_layout.addWidget(lbl_activo)
        self.header_layout.addSpacing(6)
        self.enable_switch = SwitchButton()
        self.enable_switch.checkedChanged.connect(self.on_enable_changed)
        self.header_layout.addWidget(self.enable_switch)
        self.header_layout.addSpacing(15)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #333333;")
        sep.setFixedHeight(20)
        self.header_layout.addWidget(sep)
        self.header_layout.addSpacing(15)
        lbl_perfil = QLabel("Perfil")
        lbl_perfil.setStyleSheet("color: #888888; font-size: 13px;")
        self.header_layout.addWidget(lbl_perfil)
        self.header_layout.addSpacing(8)
        self.preset_combo = ComboBox()
        self.preset_combo.setFixedWidth(130)
        self.preset_combo.setFixedHeight(30)
        for preset in self.eq_controller.PRESETS.keys():
            self.preset_combo.addItem(preset)
        self.preset_combo.addItem("Custom")
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        self.header_layout.addWidget(self.preset_combo)
        self.delete_preset_btn = TransparentToolButton()
        self.delete_preset_btn.setIcon(FIF.DELETE)
        self.delete_preset_btn.setIconSize(QSize(14, 14))
        self.delete_preset_btn.clicked.connect(self.on_delete_preset_clicked)
        self.delete_preset_btn.hide()                     
        self.header_layout.addWidget(self.delete_preset_btn)
        self.header_layout.addSpacing(20)
        self.close_btn = TransparentToolButton()
        self.close_btn.setIcon(FIF.CLOSE)
        self.close_btn.setIconSize(QSize(14, 14))
        self.close_btn.clicked.connect(self.close)
        self.header_layout.addWidget(self.close_btn)
        self.main_layout.addLayout(self.header_layout)
        h_sep = QFrame()
        h_sep.setFrameShape(QFrame.Shape.HLine)
        h_sep.setStyleSheet("color: rgba(255, 255, 255, 30);")
        self.main_layout.addWidget(h_sep)
        self.main_layout.addSpacing(20)
        self.body_layout = QHBoxLayout()
        self.body_layout.setContentsMargins(10, 0, 10, 0)
        self.scale_layout = QVBoxLayout()
        self.scale_layout.setContentsMargins(0, 15, 10, 68) 
        self.scale_layout.setSpacing(0)
        labels_db = ["+15 dB", "+7.5 dB", "0 dB", "-7.5 dB", "-15 dB"]
        for db_str in labels_db:
            lbl = QLabel(db_str)
            lbl.setStyleSheet("color: #AAAAAA; font-size: 11px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.scale_layout.addWidget(lbl)
            if db_str != "-15 dB":
                self.scale_layout.addStretch()
        self.body_layout.addLayout(self.scale_layout)
        self.preamp_widget = EqualizerSlider(-1, "Pre-Amp", 0.0)
        self.preamp_widget.slider.valueChanged.connect(self.on_preamp_changed)
        self.body_layout.addWidget(self.preamp_widget)
        v_sep = QFrame()
        v_sep.setFrameShape(QFrame.Shape.VLine)
        v_sep.setStyleSheet("color: rgba(255, 255, 255, 30);")
        self.body_layout.addWidget(v_sep)
        self.body_layout.addSpacing(5)
        self.graph_container = EQGraphContainer()
        self.sliders_layout = QHBoxLayout(self.graph_container)
        self.sliders_layout.setContentsMargins(0, 0, 0, 0)
        self.sliders_layout.setSpacing(10)
        self.sliders = [self.preamp_widget]                                                              
        eq_band_widgets = []
        freqs = ["80", "120", "250", "500", "1K", "2K", "4K", "8K", "12K", "16K"]
        for i, freq in enumerate(freqs):
            slider_widget = EqualizerSlider(i, freq, 0.0)
            slider_widget.slider.valueChanged.connect(self.on_slider_interaction)
            slider_widget.slider.valueChanged.connect(lambda val, idx=i: self.on_slider_changed(idx, val))
            self.sliders_layout.addWidget(slider_widget)
            self.sliders.append(slider_widget)
            eq_band_widgets.append(slider_widget)
        self.graph_container.set_sliders(eq_band_widgets)                           
        self.body_layout.addWidget(self.graph_container, stretch=1)
        self.main_layout.addLayout(self.body_layout)
        self.main_layout.addSpacing(25)
        self.footer_layout = QHBoxLayout()
        self.footer_layout.setContentsMargins(10, 0, 10, 0)
        self.save_btn = OutlineButton(FIF.SAVE, " Guardar perfil")
        self.save_btn.setFixedHeight(34)
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.footer_layout.addWidget(self.save_btn)
        self.footer_layout.addStretch()
        self.reset_btn = OutlineButton(FIF.SYNC, " Restablecer")
        self.reset_btn.setFixedHeight(34)
        self.reset_btn.clicked.connect(lambda: self.on_preset_changed("Flat"))
        self.footer_layout.addWidget(self.reset_btn)
        self.main_layout.addLayout(self.footer_layout)
        self.eq_controller.profile_loaded.connect(self.update_sliders_from_profile)
        self._update_delete_button_visibility()
    def _update_delete_button_visibility(self):
        curr = self.preset_combo.currentText()
        if curr != "Custom" and curr not in self.eq_controller.DEFAULT_PRESETS:
            self.delete_preset_btn.show()
        else:
            self.delete_preset_btn.hide()
    def on_delete_preset_clicked(self):
        from qfluentwidgets import MessageBox
        curr = self.preset_combo.currentText()
        if curr != "Custom" and curr not in self.eq_controller.DEFAULT_PRESETS:
            msg = MessageBox("Eliminar Perfil", f"¿Estás seguro que deseas eliminar el perfil '{curr}'?", self)
            if msg.exec():
                if self.eq_controller.delete_preset(curr):
                    self._is_updating = True
                    idx = self.preset_combo.findText(curr)
                    if idx >= 0:
                        self.preset_combo.removeItem(idx)
                    self.preset_combo.setCurrentText("Custom")
                    self._update_delete_button_visibility()
                    self._is_updating = False
    def on_slider_interaction(self):
        self.graph_container.update()
    def on_save_clicked(self):
        from qfluentwidgets import MessageBox
        dialog = PresetInputDialog(self)
        if dialog.exec():
            name = dialog.lineEdit.text().strip()
            if name:
                saved_name = self.eq_controller.save_preset(name)
                if saved_name:
                    if saved_name not in [self.preset_combo.itemText(i) for i in range(self.preset_combo.count())]:
                        self.preset_combo.addItem(saved_name)
                    self._is_updating = True
                    self.preset_combo.setCurrentText(saved_name)
                    self._is_updating = False
                    msg = MessageBox("Perfil Guardado", f"Se ha guardado el perfil '{saved_name}' exitosamente.", self)
                    msg.exec()
    def load_state(self):
        self._is_updating = True
        self.enable_switch.setChecked(self.eq_controller.is_enabled)
        self.preset_combo.setCurrentText(self.eq_controller.current_preset)
        self.update_sliders_from_profile(self.eq_controller.current_bands, self.eq_controller.current_preamp)
        self.update_ui_state(self.eq_controller.is_enabled)
        self._is_updating = False
    def on_enable_changed(self, is_checked):
        self.eq_controller.set_enabled(is_checked)
        self.update_ui_state(is_checked)
    def update_ui_state(self, is_enabled):
        self.graph_container.is_enabled = is_enabled
        self.graph_container.update()
        for slider_widget in self.sliders:
            slider_widget.slider.is_enabled = is_enabled
            slider_widget.slider.update()
            slider_widget.value_badge.is_enabled = is_enabled
            slider_widget.value_badge._update_appearance()
    def on_preset_changed(self, preset_name):
        if self._is_updating: return
        self._update_delete_button_visibility()
        if preset_name != "Custom":
            self._is_updating = True
            self.preset_combo.setCurrentText(preset_name)
            self.eq_controller.load_preset(preset_name)
            self._is_updating = False
    def on_preamp_changed(self, value):
        if self._is_updating: return
        gain = -value / 10.0
        self.preamp_widget.update_label_text(gain)
        self.eq_controller.set_preamp(gain)
    def on_slider_changed(self, index, value):
        if self._is_updating: return
        gain = -value / 10.0
        self.sliders[index+1].update_label_text(gain)                                 
        self.eq_controller.set_band(index, gain)
        self._is_updating = True
        self.preset_combo.setCurrentText("Custom")
        self._is_updating = False
    def update_sliders_from_profile(self, bands, preamp):
        self._is_updating = True
        self.sliders[0].slider.setValue(-int(preamp * 10))
        self.sliders[0].update_label_text(preamp)
        for i, gain in enumerate(bands):
            idx = i + 1                    
            self.sliders[idx].slider.setValue(-int(gain * 10))
            self.sliders[idx].update_label_text(gain)
        self.graph_container.update()
        self._is_updating = False