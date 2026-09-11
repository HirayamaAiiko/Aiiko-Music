import os
from datetime import date
from PyQt6.QtCore import Qt, QSize, QRectF, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont, QLinearGradient
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QDialog,
    QFileDialog, QSizePolicy, QFrame, QGraphicsDropShadowEffect,
    QStackedWidget
)
from PyQt6.QtSvgWidgets import QSvgWidget
from qfluentwidgets import (
    BodyLabel, CaptionLabel, SubtitleLabel,
    LineEdit, PrimaryPushButton, PushButton,
    ComboBox, FluentIcon as FIF, TransparentToolButton,
    CardWidget, SmoothScrollArea, MessageBoxBase, MessageBox
)
from settings_manager import settings
from core.language_manager import tr
PROFILE_NAME_KEY     = "user_profile_name"
PROFILE_PHOTO_KEY    = "user_profile_photo"
PROFILE_BIRTHDAY_KEY = "user_profile_birthday"            
PROFILE_CREATED_KEY  = "user_profile_created"                                 
_MONTHS = [
    tr("Enero"), tr("Febrero"), tr("Marzo"), tr("Abril"), tr("Mayo"), tr("Junio"),
    tr("Julio"), tr("Agosto"), tr("Septiembre"), tr("Octubre"), tr("Noviembre"), tr("Diciembre")
]
def _make_circular_pixmap(path: str, size: int) -> "QPixmap | None":
    if not path or not os.path.exists(path):
        return None
    src = QPixmap(path).scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation
    )
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)
    p = QPainter(result)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    clip = QPainterPath()
    clip.addEllipse(QRectF(0, 0, size, size))
    p.setClipPath(clip)
    x = (src.width()  - size) // 2
    y = (src.height() - size) // 2
    p.drawPixmap(-x, -y, src)
    p.end()
    return result
def _initials_pixmap(name: str, size: int, accent: str = "#7C3AED") -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0, QColor(accent))
    darker = QColor(accent)
    darker.setAlpha(180)
    grad.setColorAt(1, darker)
    p.setBrush(grad)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(0, 0, size, size)
    initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "U"
    font = QFont("Segoe UI", max(8, size // 3))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QColor("#FFFFFF"))
    p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, initials)
    p.end()
    return pix
def is_birthday_today() -> bool:
    bday = settings.get(PROFILE_BIRTHDAY_KEY, "")
    if not bday:
        return False
    try:
        month, day = bday.split("-")
        t = date.today()
        return t.month == int(month) and t.day == int(day)
    except Exception:
        return False
class ProfileCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 8))                              
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10.0, 10.0)
        pen = painter.pen()
        pen.setColor(QColor(255, 255, 255, 15))                               
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        painter.drawRoundedRect(rect, 9.5, 9.5)
        painter.end()
class AccountBadge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        ab_layout = QHBoxLayout(self)
        ab_layout.setContentsMargins(8, 0, 10, 0)
        ab_layout.setSpacing(6)
        self.acc_icon = QLabel()
        self.acc_icon.setPixmap(FIF.PEOPLE.icon(color=QColor(255, 255, 255, 180)).pixmap(14, 14))
        self.acc_icon.setStyleSheet("background: transparent; border: none;")
        ab_layout.addWidget(self.acc_icon)
        self.acc_text = CaptionLabel(tr("Cuenta local"))
        self.acc_text.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px; background: transparent; border: none;")
        ab_layout.addWidget(self.acc_text)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 15))                               
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 6.0, 6.0)
        painter.end()
class DataButton(QWidget):
    def __init__(self, title, subtitle, icon, callback, accent_color="#7C3AED", parent=None):
        super().__init__(parent)
        self.callback = callback
        self.icon = icon
        self.accent_color = accent_color
        self.is_hover = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(56)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(24, 24)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setPixmap(self.icon.icon(color=QColor(self.accent_color)).pixmap(20, 20))
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.icon_lbl)
        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        text_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        t_lbl = BodyLabel(title)
        t_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: white; background: transparent; border: none;")
        text_col.addWidget(t_lbl)
        s_lbl = CaptionLabel(subtitle)
        s_lbl.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 11px; background: transparent; border: none;")
        text_col.addWidget(s_lbl)
        layout.addLayout(text_col, 1)
        chevron = QLabel()
        chevron.setPixmap(FIF.CHEVRON_RIGHT.icon(color=QColor(255, 255, 255, 100)).pixmap(12, 12))
        chevron.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(chevron)
    def set_accent(self, accent_color):
        self.accent_color = accent_color
        self.icon_lbl.setPixmap(self.icon.icon(color=QColor(self.accent_color)).pixmap(20, 20))
    def mousePressEvent(self, event):
        self.callback()
    def enterEvent(self, event):
        self.is_hover = True
        self.update()
    def leaveEvent(self, event):
        self.is_hover = False
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        if self.is_hover:
            painter.setBrush(QColor(255, 255, 255, 8))                              
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 8.0, 8.0)
        painter.end()
class ProfileEditDialog(MessageBoxBase):
    profile_saved = pyqtSignal()
    def __init__(self, accent: str = "#7C3AED", parent=None):
        super().__init__(parent)
        self._accent = accent
        self._current_photo = settings.get(PROFILE_PHOTO_KEY, "")
        if not settings.get(PROFILE_CREATED_KEY):
            from core.language_manager import tr
            today = date.today()
            month_name = _MONTHS[today.month - 1].lower()
            settings.set(PROFILE_CREATED_KEY, tr("Miembro desde {month} {year}").format(month=month_name, year=today.year))
            settings.save()
        self.widget.setMinimumWidth(800)
        self._build_ui()
        self._load_values()
    def _make_card(self):
        pass
    def _build_ui(self):
        self.viewLayout.setSpacing(20)
        self.viewLayout.setContentsMargins(24, 24, 24, 24)
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        self.titleLabel = SubtitleLabel(tr("Editar perfil"), self)
        self.titleLabel.setStyleSheet("font-size: 22px; font-weight: bold; color: white; background: transparent; border: none;")
        self.subtitleLabel = CaptionLabel(tr("Personaliza tu información"), self)
        self.subtitleLabel.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 13px; background: transparent; border: none;")
        header_layout.addWidget(self.titleLabel)
        header_layout.addWidget(self.subtitleLabel)
        self.viewLayout.addLayout(header_layout)
        card1 = ProfileCard(self)
        c1_layout = QHBoxLayout(card1)
        c1_layout.setContentsMargins(24, 24, 24, 24)
        c1_layout.setSpacing(24)
        self._avatar_wrapper = QWidget()
        self._avatar_wrapper.setFixedSize(120, 120)
        self._avatar_wrapper.setStyleSheet("background: transparent; border: none;")
        self._avatar_lbl = QLabel(self._avatar_wrapper)
        self._avatar_lbl.setFixedSize(120, 120)
        self._avatar_lbl.move(0, 0)
        self._avatar_lbl.setStyleSheet("background: transparent; border: none;")
        self._camera_btn = TransparentToolButton(FIF.CAMERA, self._avatar_wrapper)
        self._camera_btn.setFixedSize(32, 32)
        self._camera_btn.move(120 - 34, 120 - 34)                       
        self._camera_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._camera_btn.setToolTip(tr("Cambiar foto"))
        self._camera_btn.clicked.connect(self._on_change_photo)
        self._camera_btn.setStyleSheet("""
            TransparentToolButton {
                background: #1e1e1e;
                border: 2px solid #2b2b2b;
                border-radius: 16px;
                padding: 4px;
            }
            TransparentToolButton:hover {
                background: #2a2a2a;
            }
        """)
        c1_layout.addWidget(self._avatar_wrapper)
        c1_info_layout = QVBoxLayout()
        c1_info_layout.setSpacing(8)
        c1_info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._display_name_lbl = SubtitleLabel("Usuario", self)
        self._display_name_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background: transparent; border: none;")
        c1_info_layout.addWidget(self._display_name_lbl)
        account_badge = AccountBadge(self)
        c1_info_layout.addWidget(account_badge, 0, Qt.AlignmentFlag.AlignLeft)
        member_lbl_layout = QHBoxLayout()
        member_lbl_layout.setSpacing(8)
        cal_icon = QLabel()
        cal_icon.setPixmap(FIF.CALENDAR.icon(color=QColor(self._accent)).pixmap(14, 14))
        cal_icon.setStyleSheet("background: transparent; border: none;")
        member_lbl_layout.addWidget(cal_icon)
        member_text = CaptionLabel(settings.get(PROFILE_CREATED_KEY, ""))
        member_text.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 12px; background: transparent; border: none;")
        member_lbl_layout.addWidget(member_text)
        member_lbl_layout.addStretch()
        c1_info_layout.addLayout(member_lbl_layout)
        stats_play_layout = QHBoxLayout()
        stats_play_layout.setSpacing(8)
        play_icon = QLabel()
        play_icon.setPixmap(FIF.PLAY.icon(color=QColor(self._accent)).pixmap(14, 14))
        play_icon.setStyleSheet("background: transparent; border: none;")
        stats_play_layout.addWidget(play_icon)
        self._play_text = CaptionLabel(tr("0 Reproducciones"))
        self._play_text.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 12px; background: transparent; border: none;")
        stats_play_layout.addWidget(self._play_text)
        stats_play_layout.addStretch()
        c1_info_layout.addLayout(stats_play_layout)
        stats_time_layout = QHBoxLayout()
        stats_time_layout.setSpacing(8)
        time_icon = QLabel()
        time_icon.setPixmap(FIF.HISTORY.icon(color=QColor(self._accent)).pixmap(14, 14))
        time_icon.setStyleSheet("background: transparent; border: none;")
        stats_time_layout.addWidget(time_icon)
        self._time_text = CaptionLabel(tr("0 Horas escuchadas"))
        self._time_text.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 12px; background: transparent; border: none;")
        stats_time_layout.addWidget(self._time_text)
        stats_time_layout.addStretch()
        c1_info_layout.addLayout(stats_time_layout)
        stats_music_layout = QHBoxLayout()
        stats_music_layout.setSpacing(8)
        music_icon = QLabel()
        music_icon.setPixmap(FIF.MUSIC.icon(color=QColor(self._accent)).pixmap(14, 14))
        music_icon.setStyleSheet("background: transparent; border: none;")
        stats_music_layout.addWidget(music_icon)
        self._music_text = CaptionLabel(tr("0 Canciones distintas"))
        self._music_text.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 12px; background: transparent; border: none;")
        stats_music_layout.addWidget(self._music_text)
        stats_music_layout.addStretch()
        c1_info_layout.addLayout(stats_music_layout)
        c1_layout.addLayout(c1_info_layout)
        c1_layout.addStretch()
        card2 = ProfileCard(self)
        c2_layout = QVBoxLayout(card2)
        c2_layout.setContentsMargins(20, 20, 20, 20)
        c2_layout.setSpacing(16)
        c2_title = BodyLabel(tr("Información personal"))
        c2_title.setStyleSheet("font-size: 14px; font-weight: bold; color: white; background: transparent; border: none;")
        c2_layout.addWidget(c2_title)
        name_lbl = CaptionLabel(tr("NOMBRE"), self)
        name_lbl.setStyleSheet(f"color: {self._accent}; letter-spacing: 1px; font-size: 11px; font-weight: 700; background: transparent; border: none;")
        c2_layout.addWidget(name_lbl)
        self._name_edit = LineEdit(self)
        self._name_edit.setPlaceholderText(tr("Tu nombre"))
        self._name_edit.setMaxLength(40)
        self._name_edit.setFixedHeight(40)
        c2_layout.addWidget(self._name_edit)
        c2_layout.addSpacing(4)
        bday_lbl = CaptionLabel(tr("CUMPLEAÑOS"), self)
        bday_lbl.setStyleSheet(f"color: {self._accent}; letter-spacing: 1px; font-size: 11px; font-weight: 700; background: transparent; border: none;")
        c2_layout.addWidget(bday_lbl)
        bday_row = QHBoxLayout()
        bday_row.setSpacing(16)
        self._month_combo = ComboBox(self)
        self._month_combo.addItems(_MONTHS)
        self._month_combo.setFixedHeight(40)
        bday_row.addWidget(self._month_combo, 1)
        self._day_combo = ComboBox(self)
        self._day_combo.setFixedHeight(40)
        bday_row.addWidget(self._day_combo, 1)
        c2_layout.addLayout(bday_row)
        self._month_combo.currentIndexChanged.connect(self._on_month_changed)
        card3 = ProfileCard(self)
        c3_layout = QVBoxLayout(card3)
        c3_layout.setContentsMargins(20, 20, 20, 20)
        c3_layout.setSpacing(16)
        c3_title = BodyLabel(tr("Opciones avanzadas"))
        c3_title.setStyleSheet("font-size: 14px; font-weight: bold; color: white; background: transparent; border: none;")
        c3_layout.addWidget(c3_title)
        c3_subtitle = CaptionLabel(tr("Exporta o importa tus datos para respaldar tu información o usarla en otros dispositivos."))
        c3_subtitle.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 12px; background: transparent; border: none;")
        c3_subtitle.setWordWrap(True)
        c3_layout.addWidget(c3_subtitle)
        c3_layout.addSpacing(4)
        btn_export = DataButton(
            tr("Exportar datos"), tr("Guarda tu información en un archivo"), FIF.UP, self._on_export, self._accent, self
        )
        c3_layout.addWidget(btn_export)
        c3_sep = QFrame()
        c3_sep.setFixedHeight(1)
        c3_sep.setStyleSheet("background: rgba(255,255,255,0.06); border: none;")
        c3_layout.addWidget(c3_sep)
        btn_import = DataButton(
            tr("Importar datos"), tr("Restaura tus ajustes e historial"), FIF.DOWN, self._on_import, self._accent, self
        )
        c3_layout.addWidget(btn_import)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        left_col = QVBoxLayout()
        left_col.setSpacing(16)
        left_col.addWidget(card1)
        left_col.addStretch()
        from config import APP_ROOT
        graphic_path = os.path.join(APP_ROOT, "resources", "graphics", "flower_wave.svg")
        if os.path.exists(graphic_path):
            graphic_widget = QSvgWidget(graphic_path)
            graphic_widget.setFixedSize(280, 280)
            graphic_container = QWidget()
            g_layout = QHBoxLayout(graphic_container)
            g_layout.setContentsMargins(0, 0, 0, 0)
            g_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            g_layout.addWidget(graphic_widget)
            left_col.addWidget(graphic_container)
        else:
            left_col.addStretch()
        v_line = QFrame()
        v_line.setFixedWidth(1)
        v_line.setStyleSheet("background: rgba(255,255,255,0.06); border: none;")
        right_col = QVBoxLayout()
        right_col.setSpacing(16)
        right_col.addWidget(card2)
        right_col.addWidget(card3)
        right_col.addStretch()
        content_layout.addLayout(left_col, 1)
        content_layout.addWidget(v_line)
        content_layout.addLayout(right_col, 1)
        self.viewLayout.addLayout(content_layout)
        self.yesButton.setText(tr("Guardar cambios"))
        self.yesButton.setIcon(FIF.SAVE)
        self.yesButton.setFixedSize(180, 40)
        self.cancelButton.setText(tr("Cancelar"))
        self.cancelButton.setFixedSize(180, 40)
    def _load_values(self):
        name  = settings.get(PROFILE_NAME_KEY, tr("Usuario"))
        bday  = settings.get(PROFILE_BIRTHDAY_KEY, "")
        self._display_name_lbl.setText(name)
        self._name_edit.setText(name)
        self._update_avatar(self._current_photo, name)
        try:
            from controllers.analytics_controller import AnalyticsController
            stats = AnalyticsController.get_user_profile_stats()
            plays = stats.get("total_plays", 0)
            unique = stats.get("unique_songs", 0)
            ms = stats.get("total_listened_ms", 0)
            hours = ms / (1000 * 60 * 60)
            self._play_text.setText(tr("{} Reproducciones").format(f"{plays:,}"))
            if hours < 1:
                minutes = ms / (1000 * 60)
                self._time_text.setText(tr("{:.0f} Minutos escuchados").format(minutes))
            else:
                self._time_text.setText(tr("{:.1f} Horas escuchadas").format(hours))
            self._music_text.setText(tr("{} Canciones distintas").format(f"{unique:,}"))
        except Exception as e:
            import logging
            logging.error(f"Error cargando estadísticas del perfil: {e}")
        self._name_edit.textChanged.connect(self._on_name_changed)
        if bday:
            try:
                month, day = bday.split("-")
                month_idx = int(month) - 1
                self._month_combo.setCurrentIndex(month_idx)
                self._on_month_changed(month_idx)
                self._day_combo.setCurrentText(str(int(day)))
            except Exception:
                self._month_combo.setCurrentIndex(0)
                self._on_month_changed(0)
        else:
            self._month_combo.setCurrentIndex(0)
            self._on_month_changed(0)
    def _on_month_changed(self, index: int):
        days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if index < 0 or index > 11:
            return
        current_day = self._day_combo.currentText()
        max_days = days_in_month[index]
        self._day_combo.clear()
        self._day_combo.addItems([str(d) for d in range(1, max_days + 1)])
        if current_day:
            try:
                day_int = int(current_day)
                if day_int <= max_days:
                    self._day_combo.setCurrentText(current_day)
                else:
                    self._day_combo.setCurrentText(str(max_days))
            except ValueError:
                self._day_combo.setCurrentIndex(0)
    def _on_name_changed(self, text):
        display = text.strip() or tr("Usuario")
        self._display_name_lbl.setText(display)
        if not self._current_photo:
            self._update_avatar("", display)
    def _update_avatar(self, photo_path: str, name: str = ""):
        size = 110
        ring_size = 120
        pix = _make_circular_pixmap(photo_path, size)
        if not pix:
            pix = _initials_pixmap(name or "U", size, self._accent)
        result = QPixmap(ring_size, ring_size)
        result.fill(Qt.GlobalColor.transparent)
        p = QPainter(result)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        from PyQt6.QtGui import QPen
        pen = QPen(QColor(self._accent), 3)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(1, 1, ring_size - 2, ring_size - 2)
        offset = (ring_size - size) // 2
        p.drawPixmap(offset, offset, pix)
        p.end()
        self._avatar_lbl.setPixmap(result)
    def _on_change_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Seleccionar foto de perfil"), "",
            tr("Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)")
        )
        if path:
            self._current_photo = path
            self._update_avatar(path, self._name_edit.text())
    def accept(self):
        name  = self._name_edit.text().strip() or tr("Usuario")
        month = self._month_combo.currentIndex() + 1
        day   = self._day_combo.currentIndex() + 1
        settings.set(PROFILE_NAME_KEY,     name)
        settings.set(PROFILE_BIRTHDAY_KEY, f"{month:02d}-{day:02d}")
        settings.save()
        self.new_photo_path = self._current_photo or ""
        self.profile_saved.emit()
        super().accept()
    def _on_export(self):
        from core.data_backup import export_data, get_default_filename, BACKUP_FILTER, EXPORTABLE_TABLES
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Exportar datos de Aiiko Music"),
            get_default_filename(), BACKUP_FILTER,
        )
        if not path:
            return
        selected = [t["key"] for t in EXPORTABLE_TABLES]
        result = export_data(path, selected)
        from core.notification_manager import notify
        if result["success"]:
            notify.success(
                tr("Exportación exitosa"),
                tr("Backup guardado: {file}").format(file=os.path.basename(path))
            )
        else:
            notify.error(
                tr("Error al exportar"), 
                result["message"]
            )
    def _on_import(self):
        from core.data_backup import validate_backup, import_data, BACKUP_FILTER
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Importar datos de Aiiko Music"), "",
            f"{BACKUP_FILTER};;Archivo JSON legacy (*.json)",
        )
        if not path:
            return
        info = validate_backup(path)
        from core.notification_manager import notify
        if not info:
            notify.warning(
                tr("Archivo no válido"),
                tr("Este archivo no es un backup de Aiiko Music.")
            )
            return
        w = MessageBox(
            tr("Advertencia de Restauración"),
            tr("¿Estás seguro de que deseas importar este respaldo?\n\n"
               "Los datos de reproducción se sumarán a los actuales y tu "
               "configuración será sobrescrita. Esta acción no se puede deshacer."),
            self
        )
        if not w.exec():
            return
        result = import_data(path, table_filter=None)
        if result["success"]:
            notify.success(
                tr("Importación exitosa"),
                tr("Restaurado: {imported}").format(imported=', '.join(result['imported']))
            )
            self._load_values()
            msg = MessageBox(
                tr("Reinicio recomendado"),
                tr("Tus datos y ajustes se han restaurado correctamente.\n\n"
                   "Para que los cambios de interfaz, temas, ecualizador y demás configuraciones "
                   "tomen efecto por completo, por favor cierra y vuelve a abrir Aiiko Music."),
                self
            )
            msg.yesButton.setText(tr("Entendido"))
            msg.cancelButton.hide()
            msg.exec()
        else:
            notify.error(
                tr("Error al importar"), 
                result["message"]
            )
from PyQt6.QtCore import pyqtProperty, QPropertyAnimation
from PyQt6.QtGui import QConicalGradient
class AnimatedAvatarWidget(QWidget):
    def __init__(self, size=40, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._pixmap = None
        self._is_birthday = False
        self._angle = 0.0
        self._animation = None
    @pyqtProperty(float)
    def angle(self):
        return self._angle
    @angle.setter
    def angle(self, val):
        self._angle = val
        self.update()
    def set_data(self, pixmap, is_birthday):
        self._pixmap = pixmap
        self._is_birthday = is_birthday
        if self._is_birthday:
            if not self._animation:
                self._animation = QPropertyAnimation(self, b"angle", self)
                self._animation.setDuration(3000)                                           
                self._animation.setStartValue(0.0)
                self._animation.setEndValue(360.0)
                self._animation.setLoopCount(-1)           
            self._animation.start()
        else:
            if self._animation:
                self._animation.stop()
                self._animation = None
            self._angle = 0.0
        self.update()
    def paintEvent(self, event):
        if not self._pixmap:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawPixmap(0, 0, self._pixmap)
        if self._is_birthday:
            from PyQt6.QtGui import QPen
            grad = QConicalGradient(self.width() / 2, self.height() / 2, self._angle)
            grad.setColorAt(0.0, QColor("#FFDF00"))
            grad.setColorAt(0.15, QColor("#D4AF37"))
            grad.setColorAt(0.3, QColor("#FFDF00"))
            grad.setColorAt(0.5, QColor("#FFFFFF"))                     
            grad.setColorAt(0.7, QColor("#FFDF00"))
            grad.setColorAt(0.85, QColor("#D4AF37"))
            grad.setColorAt(1.0, QColor("#FFDF00"))
            pen = QPen(grad, 2.5)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(1, 1, self.width() - 2, self.height() - 2)
        painter.end()
class UserProfileButton(QWidget):
    profile_updated = pyqtSignal()
    def __init__(self, accent: str = None, parent=None):
        super().__init__(parent)
        import theme_manager
        self._accent = accent or theme_manager.get_accent_hex(settings.get('app_accent_name', 'Teal (AIIKO)'))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tr("Editar perfil"))
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(56)
        self.setStyleSheet("background: transparent;")
        self._build_ui()
        self.refresh()
    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)
        layout.addStretch()
        self._name_lbl = BodyLabel("")
        self._name_lbl.setStyleSheet(
            "font-weight: 600; font-size: 14px; background: transparent;"
        )
        self._name_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self._name_lbl)
        self._avatar_widget = AnimatedAvatarWidget(size=40)
        layout.addWidget(self._avatar_widget)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            import theme_manager
            current_accent = theme_manager.get_accent_hex(settings.get('app_accent_name', 'Teal (AIIKO)'))
            self.dlg = ProfileEditDialog(accent=current_accent, parent=self.window())
            self.dlg.profile_saved.connect(self._on_saved)
            self.dlg.exec()
        super().mousePressEvent(event)
    def _on_saved(self):
        self.refresh()
        photo_path = getattr(self.dlg, "new_photo_path", "")
        import os
        from config import CACHE_DIR
        profile_cache_dir = os.path.join(CACHE_DIR, "profile")
        if photo_path and os.path.exists(photo_path) and profile_cache_dir not in photo_path:
            from core.image_processing_worker import ImageCacheTask
            old_photo = settings.get(PROFILE_PHOTO_KEY, "")
            if profile_cache_dir not in old_photo:
                old_photo = None
            self._photo_task = ImageCacheTask(
                item_key="profile_photo",
                source_path=photo_path,
                cache_dir=profile_cache_dir,
                old_cache_path=old_photo,
                max_size=400,
                parent=self
            )
            self._photo_task.finished_processing.connect(self._on_photo_processed)
            self._photo_task.start()
        else:
            if not photo_path:
                old_photo = settings.get(PROFILE_PHOTO_KEY, "")
                if old_photo and profile_cache_dir in old_photo:
                    from core.image_processing_worker import ImageCacheTask
                    self._photo_task = ImageCacheTask(
                        item_key="profile_photo",
                        source_path=None,
                        cache_dir=profile_cache_dir,
                        old_cache_path=old_photo,
                        max_size=400,
                        parent=self
                    )
                    self._photo_task.start()
            settings.set(PROFILE_PHOTO_KEY, photo_path)
            settings.save()
            self.refresh()
            self.profile_updated.emit()
    def _on_photo_processed(self, key, new_path, old_path):
        from settings_manager import settings
        settings.set(PROFILE_PHOTO_KEY, new_path)
        settings.save()
        self.refresh()
        self.profile_updated.emit()
    def set_accent(self, accent: str):
        self._accent = accent
        self.refresh()
    def refresh(self):
        from settings_manager import settings
        import theme_manager
        self._accent = theme_manager.get_accent_hex(settings.get('app_accent_name', 'Teal (AIIKO)'))
        name  = settings.get(PROFILE_NAME_KEY, tr("Usuario"))
        photo = settings.get(PROFILE_PHOTO_KEY, "")
        self._name_lbl.setText(name)
        pix = _make_circular_pixmap(photo, 40) or _initials_pixmap(name, 40, self._accent)
        self._avatar_widget.set_data(pix, is_birthday_today())