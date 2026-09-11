import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QColor, QPainter
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QFileDialog
from qfluentwidgets import SubtitleLabel, CaptionLabel, LineEdit, PushButton, FluentIcon as FIF, MessageBoxBase
from widgets import AspectRatioLabel, SquareCoverLabel
from settings_manager import settings
from core.language_manager import tr
class PlaylistEditDialog(MessageBoxBase):
    def __init__(self, playlist_name, player, parent=None):
        super().__init__(parent)
        self.widget.setMinimumWidth(360)
        self.player = player
        self.playlist_name = playlist_name
        self._cover_path = None
        self.cover_reset = False
        self._build_ui()
        self.player.image_cache.cache_updated.connect(self._on_cache_updated)
    def _on_cache_updated(self):
        if self.isVisible():
            self._load_current_cover()
    def _build_ui(self):
        self.yesButton.setText(tr("Guardar"))
        self.cancelButton.setText(tr("Cancelar"))
        self.titleLabel = SubtitleLabel(tr("Editar Playlist"), self)
        self.titleLabel.setStyleSheet("font-size: 17px; font-weight: bold; margin-bottom: 12px;")
        self.viewLayout.addWidget(self.titleLabel)
        cover_row = QHBoxLayout()
        self._cover_label = SquareCoverLabel(radius=10, parent=self)
        self._cover_label.setFixedSize(120, 120)
        self._load_current_cover()
        cover_row.addStretch()
        cover_row.addWidget(self._cover_label)
        cover_row.addStretch()
        self.viewLayout.addLayout(cover_row)
        self.viewLayout.addSpacing(12)
        cover_btns = QHBoxLayout()
        cover_btns.setSpacing(8)
        btn_choose = PushButton(FIF.PHOTO, f" {tr('Elegir Imagen')}", self)
        btn_choose.setFixedHeight(32)
        btn_choose.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_choose.clicked.connect(self._choose_image)
        btn_reset = PushButton(FIF.DELETE, f" {tr('Restablecer')}", self)
        btn_reset.setFixedHeight(32)
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.clicked.connect(self._reset_cover)
        cover_btns.addStretch()
        cover_btns.addWidget(btn_choose)
        cover_btns.addWidget(btn_reset)
        cover_btns.addStretch()
        self.viewLayout.addLayout(cover_btns)
        self.viewLayout.addSpacing(12)
        self.hintLabel = CaptionLabel(tr("Nombre de la playlist"), self)
        self.hintLabel.setStyleSheet("color: rgba(255,255,255,0.50); font-size: 11px; margin-bottom: 4px;")
        self.viewLayout.addWidget(self.hintLabel)
        self._name_edit = LineEdit(self)
        self._name_edit.setText(self.playlist_name)
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
    def get_name(self):
        return self._name_edit.text().strip() or self.playlist_name
    def get_cover_path(self):
        return self._cover_path
    def _load_current_cover(self):
        covers_cfg = settings.get('playlist_covers', {})
        custom = covers_cfg.get(self.playlist_name)
        if not self.cover_reset and custom and os.path.exists(custom):
            pix = QPixmap(custom).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                         Qt.TransformationMode.SmoothTransformation)
            self._cover_label.setPixmap(pix)
        else:
            playlists = settings.get('playlists', {})
            fps = playlists.get(self.playlist_name, [])
            covers = []
            seen_covers = set()
            for fp in reversed(fps):
                track = next((t for t in self.player.library if t.filepath == fp), None)
                if track and hasattr(track, 'cover_path') and track.cover_path and os.path.exists(track.cover_path):
                    if track.cover_path not in seen_covers:
                        seen_covers.add(track.cover_path)
                        covers.append(track.cover_path)
                    if len(covers) == 4:
                        break
            pix = QPixmap(120, 120)
            pix.fill(QColor(58, 58, 64))
            p = QPainter(pix)
            if len(covers) == 1:
                cpix = self.player.image_cache.get_cached_pixmap(covers[0], 120, radius=0)
                p.drawPixmap(0, 0, 120, 120, cpix)
            elif covers:
                half = 59
                gap = 2
                positions = [(0, 0), (half + gap, 0), (0, half + gap), (half + gap, half + gap)]
                for i, cpath in enumerate(covers):
                    cpix = self.player.image_cache.get_cached_pixmap(cpath, half, radius=0)
                    p.drawPixmap(positions[i][0], positions[i][1], half, half, cpix)
            else:
                svg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "resources", "app", "logo_full.svg")
                if os.path.exists(svg_path):
                    from PyQt6.QtSvg import QSvgRenderer
                    pix.fill(Qt.GlobalColor.transparent)
                    renderer = QSvgRenderer(svg_path)
                    renderer.render(p)
            p.end()
            self._cover_label.setPixmap(pix)
    def _choose_image(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("Elegir imagen"), "", "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)")
        if path:
            self._cover_path = path
            self.cover_reset = False
            pix = QPixmap(path).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                       Qt.TransformationMode.SmoothTransformation)
            self._cover_label.setPixmap(pix)
    def _reset_cover(self):
        self._cover_path = None
        self.cover_reset = True
        self._load_current_cover()
    def showEvent(self, event):
        super().showEvent(event)
        self._name_edit.setFocus()