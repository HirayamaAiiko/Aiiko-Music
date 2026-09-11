import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QScrollArea, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen
from UI.welcome_view.components import make_label, TEXT_WHITE, TEXT_DIM
from settings_manager import settings
from core.language_manager import tr
from qfluentwidgets import FluentIcon as FIF, IconWidget, SmoothScrollArea, TransparentToolButton, PushButton
class ColoredIconWidget(QLabel):
    def __init__(self, icon_enum, color_hex, size=24, parent=None):
        super().__init__(parent)
        self._icon = icon_enum
        self._color = QColor(color_hex)
        self._size = size
        self.setFixedSize(size, size)
        self._update_pixmap()
    def set_color(self, hex_c):
        self._color = QColor(hex_c)
        self._update_pixmap()
    def _update_pixmap(self):
        icon = self._icon.icon(color=self._color)
        self.setPixmap(icon.pixmap(self._size, self._size))
class FolderCard(QWidget):
    removed = pyqtSignal(str)
    def __init__(self, path, overlay_accent, parent=None):
        super().__init__(parent)
        self.path = path
        self._accent = overlay_accent
        self.setFixedHeight(72)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 0, 20, 0)
        self.main_layout.setSpacing(16)
        self.icon_widget = ColoredIconWidget(FIF.FOLDER, self._accent, parent=self)
        self.main_layout.addWidget(self.icon_widget)
        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        text_layout.setSpacing(2)
        name = os.path.basename(path) or path
        self.lbl_name = make_label(name, f"font-size: 15px; font-weight: bold; color: {TEXT_WHITE.name()};")
        self.lbl_path = make_label(path, f"font-size: 12px; color: {TEXT_DIM.name()};")
        text_layout.addWidget(self.lbl_name)
        text_layout.addWidget(self.lbl_path)
        self.main_layout.addLayout(text_layout, 1)
        self.btn_close = TransparentToolButton(FIF.CLOSE, self)
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(lambda: self.removed.emit(self.path))
        self.main_layout.addWidget(self.btn_close)
        self._hover = False
        self._update_styles()
    def enterEvent(self, e):
        self._hover = True
        self.update()
    def leaveEvent(self, e):
        self._hover = False
        self.update()
    def _update_styles(self):
        self.icon_widget.set_color(self._accent)
    def update_accent(self, hex_c):
        self._accent = hex_c
        self._update_styles()
        self.update()
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg_color = QColor(255, 255, 255, 15) if self._hover else QColor(255, 255, 255, 5)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg_color)
        p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0), 8.0, 8.0)
        pen = QPen(QColor(255, 255, 255, 15))
        pen.setWidthF(1.0)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0), 7.5, 7.5)
        p.end()
class PageLibrary(QWidget):
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
        self.title = make_label(tr("¿Dónde está tu música?"), title_style)
        self.desc = make_label(tr("Añade las carpetas locales donde guardas tus archivos de audio\n(MP3, FLAC, M4A, WAV, OGG...)."), desc_style)
        self.desc.setContentsMargins(0, 0, 0, 16)
        self.container_layout.addWidget(self.title)
        self.container_layout.addWidget(self.desc)
        self.lbl_folders = make_label(tr("Carpetas añadidas"), f"font-size: 16px; font-weight: bold; color: {TEXT_WHITE.name()};")
        self.container_layout.addWidget(self.lbl_folders)
        self.scroll = SmoothScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("SmoothScrollArea { background: transparent; border: none; } QWidget#ScrollContent { background: transparent; }")
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("ScrollContent")
        self.folders_layout = QVBoxLayout(self.scroll_content)
        self.folders_layout.setContentsMargins(0, 0, 0, 0)
        self.folders_layout.setSpacing(12)
        self.folders_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        self.container_layout.addWidget(self.scroll, 1)
        self.btn_add = PushButton(tr("+ Añadir carpeta"))
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.setFixedHeight(48)
        self.btn_add.clicked.connect(self._add_folder)
        self.container_layout.addWidget(self.btn_add)
        self.main_layout.addWidget(self.container)
        self.update_dynamic_colors(self.overlay._current_accent)
        self._refresh_list()
    def _add_folder(self):
        directory = QFileDialog.getExistingDirectory(self.mw, tr("Seleccionar Carpeta de Música"))
        if directory:
            folders = settings.get('folders', [])
            if directory not in folders:
                folders.append(directory)
                settings.set('folders', folders)
                settings.save()
                if hasattr(self.mw, 'list_folders'):
                    self.mw.list_folders.addItem(directory)
            self._refresh_list()
    def _remove_folder(self, path):
        folders = settings.get('folders', [])
        if path in folders:
            folders.remove(path)
            settings.set('folders', folders)
            settings.save()
            if hasattr(self.mw, 'list_folders'):
                for i in range(self.mw.list_folders.count()):
                    if self.mw.list_folders.item(i).text() == path:
                        self.mw.list_folders.takeItem(i)
                        break
            self._refresh_list()
    def _refresh_list(self):
        while self.folders_layout.count():
            item = self.folders_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        folders = settings.get('folders', [])
        for f in folders:
            card = FolderCard(f, self.overlay._current_accent)
            card.removed.connect(self._remove_folder)
            self.folders_layout.addWidget(card)
    def update_dynamic_colors(self, hex_c):
        from PyQt6.QtGui import QColor
        for i in range(self.folders_layout.count()):
            widget = self.folders_layout.itemAt(i).widget()
            if isinstance(widget, FolderCard):
                widget.update_accent(hex_c)
    def retranslate_ui(self):
        self.title.setText(tr("¿Dónde está tu música?"))
        self.desc.setText(tr("Añade las carpetas locales donde guardas tus archivos de audio\n(MP3, FLAC, M4A, WAV, OGG...)."))
        self.btn_add.setText(tr("+ Añadir carpeta"))
        self.lbl_folders.setText(tr("Carpetas añadidas"))