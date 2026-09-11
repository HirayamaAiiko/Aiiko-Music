from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtGui import QIcon
from qfluentwidgets import ToolButton, FluentIcon as FIF
from core.language_manager import tr
class EditorToolbar(QWidget):
    action_paste = pyqtSignal()
    action_copy = pyqtSignal()
    action_clear = pyqtSignal()
    action_select_all = pyqtSignal()
    action_load_file = pyqtSignal()
    action_add_time = pyqtSignal()
    action_sync_back = pyqtSignal()
    action_sync_fwd = pyqtSignal()
    action_loop = pyqtSignal()
    action_reset = pyqtSignal()
    action_preview = pyqtSignal()
    action_play_pause = pyqtSignal()
    action_seek_back = pyqtSignal()
    action_seek_fwd = pyqtSignal()
    action_restart = pyqtSignal()
    def __init__(self, accent_color, initial_repeat_mode=0, parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        self.initial_repeat_mode = initial_repeat_mode
        self._icon_cache = {}
        self.init_ui()
    def _get_icon(self, filename, color="#FFFFFF"):
        cache_key = f"{filename}_{color}"
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        import os
        from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor
        from PyQt6.QtCore import Qt
        path = os.path.join("resources", "buttons", filename)
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return QIcon(path)
        tinted = QPixmap(pixmap.size())
        tinted.fill(Qt.GlobalColor.transparent)
        painter = QPainter(tinted)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), QColor(color))
        painter.end()
        icon = QIcon(tinted)
        self._icon_cache[cache_key] = icon
        return icon
    def init_ui(self):
        edit_bar = QHBoxLayout(self)
        edit_bar.setContentsMargins(0, 0, 0, 0)
        edit_bar.setSpacing(12)
        btn_paste = ToolButton(FIF.PASTE)
        btn_paste.setToolTip(tr("Pegar"))
        btn_paste.clicked.connect(self.action_paste.emit)
        btn_copy = ToolButton(FIF.COPY)
        btn_copy.setToolTip(tr("Copiar"))
        btn_copy.clicked.connect(self.action_copy.emit)
        btn_clear = ToolButton(FIF.BROOM)
        btn_clear.setToolTip(tr("Limpiar"))
        btn_clear.clicked.connect(self.action_clear.emit)
        btn_select_all = ToolButton(FIF.MENU)
        btn_select_all.setToolTip(tr("Seleccionar Todo"))
        btn_select_all.clicked.connect(self.action_select_all.emit)
        btn_load_file = ToolButton(FIF.DOCUMENT)
        btn_load_file.setToolTip(tr("Cargar desde archivo .lrc"))
        btn_load_file.clicked.connect(self.action_load_file.emit)
        btn_add_time = ToolButton(FIF.FLAG)
        btn_add_time.setToolTip(tr("Insertar tiempo actual del reproductor"))
        btn_add_time.clicked.connect(self.action_add_time.emit)
        btn_sync_back = ToolButton(FIF.LEFT_ARROW)
        btn_sync_back.setToolTip(tr("Retrasar 1 segundo (-1s)"))
        btn_sync_back.clicked.connect(self.action_sync_back.emit)
        btn_sync_fwd = ToolButton(FIF.RIGHT_ARROW)
        btn_sync_fwd.setToolTip(tr("Adelantar 1 segundo (+1s)"))
        btn_sync_fwd.clicked.connect(self.action_sync_fwd.emit)
        self.btn_reset = ToolButton(FIF.HISTORY)
        self.btn_reset.setToolTip(tr("Restablecer Letra Original"))
        self.btn_reset.clicked.connect(self.action_reset.emit)
        self.btn_preview = ToolButton(FIF.VIEW)
        self.btn_preview.setToolTip(tr("Activar/Desactivar Vista Previa"))
        self.btn_preview.clicked.connect(self.action_preview.emit)
        self.btn_loop = ToolButton(self._get_icon("repeat.svg"))
        self.btn_loop.setToolTip(tr("Repetir Canción (Bucle)"))
        self.btn_loop.clicked.connect(self.action_loop.emit)
        if self.initial_repeat_mode == 2:
            self.set_loop_active(True)
        self.btn_play = ToolButton(self._get_icon("play.svg"))
        self.btn_play.setToolTip(tr("Reproducir / Pausar"))
        self.btn_play.clicked.connect(self.action_play_pause.emit)
        self.btn_seek_back = ToolButton(self._get_icon("prev.svg"))
        self.btn_seek_back.setToolTip(tr("Retroceder 10 segundos"))
        self.btn_seek_back.clicked.connect(self.action_seek_back.emit)
        self.btn_seek_fwd = ToolButton(self._get_icon("next.svg"))
        self.btn_seek_fwd.setToolTip(tr("Adelantar 10 segundos"))
        self.btn_seek_fwd.clicked.connect(self.action_seek_fwd.emit)
        self.btn_restart = ToolButton(self._get_icon("restart.svg"))
        self.btn_restart.setToolTip(tr("Reiniciar canción"))
        self.btn_restart.clicked.connect(self.action_restart.emit)
        edit_bar.addWidget(btn_copy)
        edit_bar.addWidget(btn_paste)
        edit_bar.addWidget(btn_clear)
        edit_bar.addWidget(btn_select_all)
        edit_bar.addWidget(btn_load_file)
        edit_bar.addSpacing(12)
        edit_bar.addWidget(btn_add_time)
        edit_bar.addWidget(btn_sync_back)
        edit_bar.addWidget(btn_sync_fwd)
        edit_bar.addSpacing(12)
        edit_bar.addWidget(self.btn_restart)
        edit_bar.addWidget(self.btn_seek_back)
        edit_bar.addWidget(self.btn_play)
        edit_bar.addWidget(self.btn_seek_fwd)
        edit_bar.addWidget(self.btn_loop)
        edit_bar.addWidget(self.btn_reset)
        edit_bar.addWidget(self.btn_preview)
        edit_bar.addStretch()
    def set_loop_active(self, active):
        if active:
            self.btn_loop.setIcon(self._get_icon("repeat1.svg", self.accent_color))
            self.btn_loop.setToolTip(tr("Repetir Canción (Activado)"))
        else:
            self.btn_loop.setIcon(self._get_icon("repeat.svg"))
            self.btn_loop.setToolTip(tr("Repetir Canción (Bucle)"))
    def set_preview_active(self, active):
        if active:
            self.btn_preview.setIcon(FIF.VIEW.icon(color=self.accent_color))
            self.btn_preview.setToolTip(tr("Vista Previa (Activada)"))
        else:
            self.btn_preview.setIcon(FIF.VIEW.icon())
            self.btn_preview.setToolTip(tr("Activar Vista Previa"))
    def update_play_icon(self, is_playing):
        if is_playing:
            self.btn_play.setIcon(self._get_icon("pause.svg"))
        else:
            self.btn_play.setIcon(self._get_icon("play.svg"))
