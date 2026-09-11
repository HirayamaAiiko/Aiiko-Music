from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from UI.welcome_view.components import make_label, TEXT_WHITE, TEXT_DIM
from core.language_manager import tr
from settings_manager import settings
from PyQt6.QtCore import QTimer
class PageReady(QWidget):
    def __init__(self, overlay, parent=None):
        super().__init__(parent)
        self.overlay = overlay
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.container = QWidget()
        self.container.setFixedWidth(600)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(16)
        title_style = f"font-size: 28px; font-weight: 800; color: {TEXT_WHITE.name()};"
        self.desc_style = f"font-size: 15px; color: {TEXT_DIM.name()};"
        self.title = make_label(tr("Analizando biblioteca..."), title_style)
        self.desc = make_label(tr("Buscando tus canciones locales. Esto puede tomar un momento..."), self.desc_style)
        self.desc.setContentsMargins(0, 0, 0, 16)
        self.container_layout.addWidget(self.title)
        self.container_layout.addWidget(self.desc)
        self.main_layout.addWidget(self.container)
    def start_scan(self):
        if getattr(self, '_scanned', False):
            self.overlay.btn_next.setText(tr("Entrar a Aiiko"))
            self.overlay.btn_next.setVisible(True)
            return
        self._scanned = True
        mw = self.overlay.main_window
        folders = settings.get('folders', [])
        if folders and hasattr(mw, 'library_sync_controller'):
            mw.library_manager.scan_finished.connect(self._on_scan_finished)
            mw.library_sync_controller.start_background_scan(show_dialog=False)
            if hasattr(mw.library_manager, 'scanner') and mw.library_manager.scanner:
                if hasattr(mw.library_manager.scanner, 'progress_count'):
                    mw.library_manager.scanner.progress_count.connect(self._on_scan_progress)
        else:
            QTimer.singleShot(1000, self._on_scan_finished)
    def _on_scan_progress(self, current, total):
        accent = self.overlay._current_accent
        msg = tr('Procesado <font color="{0}"><b>{1}</b></font> canciones de <font color="{0}"><b>{2}</b></font> en total.').format(accent, current, total)
        self.desc.setText(msg)
    def _on_scan_finished(self):
        try:
            from database import get_db_connection
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute('SELECT COUNT(*) FROM tracks')
                count = cur.fetchone()[0]
        except Exception:
            count = 0
        self.title.setText(tr("¡Todo Listo!"))
        accent = self.overlay._current_accent
        msg = tr('Encontramos <font color="{0}"><b>{1}</b></font> canciones en tu biblioteca.<br>Tu música está lista para reproducirse.').format(accent, count)
        if getattr(self.overlay, '_language_changed', False):
            msg += "<br><br>" + tr("(La aplicación se reiniciará para aplicar el nuevo idioma)")
        self.desc.setText(msg)
        self.overlay.btn_next.setText(tr("Entrar a Aiiko"))
        self.overlay.btn_next.setVisible(True)
    def update_dynamic_colors(self, hex_c):
        pass
    def retranslate_ui(self):
        pass
