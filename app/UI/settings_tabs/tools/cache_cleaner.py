\
\
\
\
\
\
\
\
\
\
\
\
\
\
import os
import json
import hashlib
import logging
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSizePolicy, QFrame
)
from qfluentwidgets import (
    BodyLabel, CaptionLabel, SubtitleLabel,
    PushButton, ProgressBar, TransparentToolButton,
    FluentIcon as FIF, SmoothScrollArea,
    InfoBar, InfoBarPosition
)
from config import LYRICS_CACHE_DIR
from database import get_db_connection
from core.language_manager import tr
class _CacheScanWorker(QThread):
    progress = pyqtSignal(int, int)
    scan_complete = pyqtSignal(list, int)                                
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
    def run(self):
        orphaned_files = []
        total_bytes = 0
        try:
            valid_lyrics_hashes = set()
            valid_cover_hashes = set()
            from contextlib import closing
            with closing(get_db_connection()) as conn:
                c = conn.cursor()
                c.execute("SELECT filepath, mtime, cover_path FROM tracks")
                for row in c.fetchall():
                    filepath, mtime, cover_path = row
                    if mtime is None:
                        mtime = 0
                    lyrics_string = f"{filepath}_{mtime}"
                    lyrics_hash = hashlib.md5(lyrics_string.encode('utf-8')).hexdigest()
                    valid_lyrics_hashes.add(f"{lyrics_hash}.json")
                    if cover_path:
                        cover_hash = hashlib.md5(cover_path.encode('utf-8')).hexdigest()
                        valid_cover_hashes.add(cover_hash)
            files_to_scan = []
            if os.path.exists(LYRICS_CACHE_DIR):
                for f in os.listdir(LYRICS_CACHE_DIR):
                    if f.endswith('.json'):
                        files_to_scan.append(('lyrics', os.path.join(LYRICS_CACHE_DIR, f), f))
            from config import CACHE_DIR
            cover_cache_dir = os.path.join(CACHE_DIR, "thumbnails")
            if os.path.exists(cover_cache_dir):
                for f in os.listdir(cover_cache_dir):
                    if f.endswith('.jpg'):
                        files_to_scan.append(('cover', os.path.join(cover_cache_dir, f), f))
            total = len(files_to_scan)
            for i, (f_type, file_path, filename) in enumerate(files_to_scan):
                if not self.running:
                    return
                is_orphaned = False
                if f_type == 'lyrics':
                    if filename not in valid_lyrics_hashes:
                        is_orphaned = True
                elif f_type == 'cover':
                    file_hash = filename.split('_')[0]
                    if file_hash not in valid_cover_hashes:
                        is_orphaned = True
                if is_orphaned:
                    orphaned_files.append(file_path)
                    try:
                        total_bytes += os.path.getsize(file_path)
                    except Exception:
                        pass
                if total > 0 and (i % 20 == 0 or i == total - 1):
                    self.progress.emit(i + 1, total)
            if total == 0:
                self.progress.emit(1, 1)
            self.scan_complete.emit(orphaned_files, total_bytes)
        except Exception as e:
            logging.error(f"Error escaneando caché integral: {e}")
            self.scan_complete.emit([], 0)
class _CacheCleanupWorker(QThread):
    progress = pyqtSignal(int, int)
    finished_clean = pyqtSignal(int)
    def __init__(self, orphaned_files, parent=None):
        super().__init__(parent)
        self.orphaned_files = orphaned_files
    def run(self):
        cleaned = 0
        total = len(self.orphaned_files)
        for i, file_path in enumerate(self.orphaned_files):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    cleaned += 1
            except Exception as e:
                logging.debug(f"Error borrando archivo caché {file_path}: {e}")
            if i % 10 == 0 or i == total - 1:
                self.progress.emit(i + 1, total)
        self.finished_clean.emit(cleaned)
class CacheCleanerTool(QWidget):
    def __init__(self, player, accent_hex, parent=None):
        super().__init__(parent)
        self.player = player
        self._accent = accent_hex
        self._orphaned_files = []
        self._scan_worker = None
        self._clean_worker = None
        self._build_ui()
    def _build_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)
        header = QWidget()
        header.setFixedHeight(80)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)
        self.btn_back = TransparentToolButton()
        self.btn_back.setIcon(FIF.LEFT_ARROW)
        self.btn_back.setIconSize(QSize(20, 20))
        self.btn_back.clicked.connect(lambda: self.parent().setCurrentIndex(0))
        h_lay.addWidget(self.btn_back)
        title_lay = QVBoxLayout()
        title_lay.setContentsMargins(10, 15, 0, 15)
        title_lay.setSpacing(2)
        lbl_t = SubtitleLabel(tr("Limpieza de Caché Huérfana"))
        lbl_t.setStyleSheet("font-weight: bold;")
        title_lay.addWidget(lbl_t)
        lbl_st = CaptionLabel(tr("Elimina residuos de canciones editadas o eliminadas de la biblioteca."))
        lbl_st.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px;")
        title_lay.addWidget(lbl_st)
        h_lay.addLayout(title_lay)
        h_lay.addStretch()
        self.btn_scan = PushButton(tr("Escanear Caché"))
        self.btn_scan.setIcon(FIF.SEARCH)
        self.btn_scan.clicked.connect(self._start_scan)
        h_lay.addWidget(self.btn_scan)
        main_lay.addWidget(header)
        self.scroll = SmoothScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        c_lay = QVBoxLayout(container)
        c_lay.setContentsMargins(40, 20, 40, 40)
        c_lay.setSpacing(20)
        self.progress_bar = ProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.hide()
        c_lay.addWidget(self.progress_bar)
        self.lbl_status = BodyLabel(tr("Presiona 'Escanear Caché' para buscar archivos huérfanos."))
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: rgba(255,255,255,0.7);")
        c_lay.addWidget(self.lbl_status)
        self.summary_card = QFrame()
        self.summary_card.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 12px;
            }}
        """)
        s_lay = QVBoxLayout(self.summary_card)
        s_lay.setContentsMargins(30, 30, 30, 30)
        self.lbl_files_count = SubtitleLabel("0")
        self.lbl_files_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_files_count.setStyleSheet(f"color: {self._accent}; font-size: 36px; font-weight: bold; border: none; background: transparent;")
        s_lay.addWidget(self.lbl_files_count)
        lbl_files_title = BodyLabel(tr("Archivos Huérfanos Encontrados"))
        lbl_files_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_files_title.setStyleSheet("border: none; background: transparent;")
        s_lay.addWidget(lbl_files_title)
        self.lbl_bytes = CaptionLabel("0 MB")
        self.lbl_bytes.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_bytes.setStyleSheet("color: rgba(255,255,255,0.5); border: none; background: transparent; margin-top: 10px;")
        s_lay.addWidget(self.lbl_bytes)
        self.btn_clean = PushButton(tr("Limpiar Archivos Ahora"))
        self.btn_clean.setIcon(FIF.DELETE)
        self.btn_clean.setStyleSheet(f"background-color: {self._accent}; color: white; border: none;")
        self.btn_clean.setFixedSize(200, 40)
        self.btn_clean.hide()
        self.btn_clean.clicked.connect(self._start_clean)
        btn_lay = QHBoxLayout()
        btn_lay.addWidget(self.btn_clean, 0, Qt.AlignmentFlag.AlignCenter)
        s_lay.addLayout(btn_lay)
        self.summary_card.hide()
        c_lay.addWidget(self.summary_card)
        c_lay.addStretch()
        self.scroll.setWidget(container)
        main_lay.addWidget(self.scroll)
    def _format_size(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"
    def _start_scan(self):
        if self._scan_worker and self._scan_worker.isRunning():
            return
        self.btn_scan.setEnabled(False)
        self.btn_clean.hide()
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.lbl_status.setText(tr("Escaneando hashes de la biblioteca y caché local..."))
        self.summary_card.hide()
        self._orphaned_files = []
        self._scan_worker = _CacheScanWorker(self)
        self._scan_worker.progress.connect(self._update_progress)
        self._scan_worker.scan_complete.connect(self._on_scan_complete)
        self._scan_worker.start()
    def _update_progress(self, curr, total):
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(curr)
    def _on_scan_complete(self, orphaned, total_bytes):
        self.btn_scan.setEnabled(True)
        self.progress_bar.hide()
        self._orphaned_files = orphaned
        self.lbl_files_count.setText(str(len(orphaned)))
        self.lbl_bytes.setText(self._format_size(total_bytes))
        self.summary_card.show()
        if orphaned:
            self.lbl_status.setText(tr("Escaneo completado. Se encontraron archivos que ya no están en uso."))
            self.btn_clean.show()
        else:
            self.lbl_status.setText(tr("Escaneo completado. La caché está perfectamente limpia."))
    def _start_clean(self):
        if not self._orphaned_files:
            return
        if self._clean_worker and self._clean_worker.isRunning():
            return
        self.btn_scan.setEnabled(False)
        self.btn_clean.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.lbl_status.setText(tr("Eliminando archivos huérfanos..."))
        self._clean_worker = _CacheCleanupWorker(self._orphaned_files, self)
        self._clean_worker.progress.connect(self._update_progress)
        self._clean_worker.finished_clean.connect(self._on_clean_complete)
        self._clean_worker.start()
    def _on_clean_complete(self, cleaned_count):
        self.btn_scan.setEnabled(True)
        self.btn_clean.setEnabled(True)
        self.btn_clean.hide()
        self.progress_bar.hide()
        self._orphaned_files = []
        self.lbl_files_count.setText("0")
        self.lbl_bytes.setText("0 B")
        self.lbl_status.setText(tr(f"Limpieza completada. Se eliminaron {cleaned_count} archivos correctamente."))
        InfoBar.success(
            title=tr("Caché Limpiada"),
            content=tr("Se liberó espacio y se eliminaron residuos antiguos."),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
