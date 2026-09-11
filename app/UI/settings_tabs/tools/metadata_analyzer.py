import os
import logging
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSizePolicy, QFrame, QHeaderView, QAbstractItemView,
    QTableWidgetItem
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from qfluentwidgets import (
    BodyLabel, CaptionLabel, SubtitleLabel,
    PushButton, ProgressBar, TransparentToolButton,
    FluentIcon as FIF, SmoothScrollArea, TableWidget,
    InfoBar, InfoBarPosition
)
from settings_manager import settings
from core.language_manager import tr
from services.lyrics_service import LyricsLoaderWorker
from config import LYRICS_CACHE_DIR
class _MetadataScanWorker(QThread):
    progress = pyqtSignal(int, int)                            
    scan_complete = pyqtSignal(dict)                          
    def __init__(self, library, parent=None):
        super().__init__(parent)
        self._library = library
        self.running = True
    def run(self):
        total = len(self._library)
        result = {
            "total": total,
            "missing_genre": [],
            "missing_year": [],
            "missing_artist": [],
            "missing_album": [],
            "missing_cover": [],
            "no_duration": [],
            "complete": 0,
        }
        for i, track in enumerate(self._library):
            if not self.running:
                return
            issues = []
            genre = getattr(track, 'genre', '') or ''
            if not genre.strip() or genre.strip().lower() == 'desconocido':
                result["missing_genre"].append(track)
                issues.append("genre")
            year = getattr(track, 'year', '') or ''
            if not year.strip() or year.strip().lower() == 'desconocido':
                result["missing_year"].append(track)
                issues.append("year")
            artist = getattr(track, 'artist', '') or ''
            if not artist.strip() or artist.strip().lower() == 'artista desconocido':
                result["missing_artist"].append(track)
                issues.append("artist")
            album = getattr(track, 'album', '') or ''
            if not album.strip() or album.strip().lower() in ('álbum desconocido', 'album desconocido'):
                result["missing_album"].append(track)
                issues.append("album")
            cover = getattr(track, 'cover_path', None)
            if not cover or not os.path.exists(cover):
                result["missing_cover"].append(track)
                issues.append("cover")
            dur = getattr(track, 'duration', 0) or 0
            if dur <= 0:
                result["no_duration"].append(track)
                issues.append("duration")
            if not issues:
                result["complete"] += 1
            if i % 50 == 0 or i == total - 1:
                self.progress.emit(i + 1, total)
        self.scan_complete.emit(result)
class _MetadataRepairWorker(QThread):
    progress = pyqtSignal(int, int)
    finished_repair = pyqtSignal(int)
    def __init__(self, tracks_to_repair, parent=None):
        super().__init__(parent)
        self._tracks = tracks_to_repair
        self.running = True
    def run(self):
        from database import get_db_connection
        import sqlite3
        import mutagen
        total = len(self._tracks)
        repaired = 0
        for i, track in enumerate(self._tracks):
            if not self.running:
                break
            try:
                track.extract_metadata()
                repaired += 1
            except Exception as e:
                logging.debug(f"Error re-extrayendo metadata: {e}")
            if i % 5 == 0 or i == total - 1:
                self.progress.emit(i + 1, total)
        self.finished_repair.emit(repaired)
_FIELD_LABELS = {
    "missing_genre":  ("Género", "#E879F9"),                     
    "missing_year":   ("Año", "#F59E0B"),                  
    "missing_artist": ("Artista", "#60A5FA"),              
    "missing_album":  ("Álbum", "#34D399"),                     
    "missing_cover":  ("Carátula", "#F87171"),              
    "no_duration":    ("Duración", "#A78BFA"),                 
}
class _CircularGauge(QWidget):
    def __init__(self, pct: int, color: str, accent: str, parent=None):
        super().__init__(parent)
        self._pct = pct
        self._color = QColor(color)
        self._accent = QColor(accent)
        self.setStyleSheet("background: transparent; border: none;")
    def paintEvent(self, event):
        from PyQt6.QtCore import QRectF
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = min(self.width(), self.height())
        margin = 4
        rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
        pen_bg = QPen(QColor(255, 255, 255, 15), 5)
        pen_bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen_bg)
        p.drawArc(rect, 0, 360 * 16)
        pen_fg = QPen(self._color, 5)
        pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen_fg)
        span = int(self._pct / 100 * 360 * 16)
        p.drawArc(rect, 90 * 16, -span)
        p.setPen(QColor(255, 255, 255, 220))
        font = p.font()
        font.setPixelSize(13)
        font.setBold(True)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self._pct}%")
        p.end()
class MetadataAnalyzerTool(QWidget):
    def __init__(self, player, accent: str = "#1DB954", parent=None):
        super().__init__(parent)
        self.player = player
        self._accent = accent
        self._scan_result = None
        self._worker = None
        self._repair_worker = None
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        self._build_ui()
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        header = QHBoxLayout()
        header.setSpacing(12)
        back_btn = TransparentToolButton(FIF.LEFT_ARROW)
        back_btn.setFixedSize(32, 32)
        back_btn.setIconSize(QSize(16, 16))
        back_btn.setToolTip(tr("Volver a Herramientas"))
        back_btn.clicked.connect(self._on_back)
        header.addWidget(back_btn)
        title = SubtitleLabel(tr("Analizador de Metadatos"))
        title.setStyleSheet("font-weight: 700; background: transparent;")
        header.addWidget(title)
        header.addStretch()
        root.addLayout(header)
        desc = CaptionLabel(
            tr("Analiza tu biblioteca para encontrar canciones con metadatos "
               "incompletos (género, año, artista, álbum, carátula, duración) "
               "y re-extraerlos automáticamente desde los archivos de audio.")
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            "color: rgba(255,255,255,0.50); font-size: 12px; "
            "background: transparent; border: none;"
        )
        root.addWidget(desc)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(12)
        self._btn_scan = PushButton(FIF.SEARCH, tr("Analizar biblioteca"))
        self._btn_scan.setFixedHeight(36)
        self._btn_scan.setMinimumWidth(180)
        self._btn_scan.clicked.connect(self._start_scan)
        btn_row.addWidget(self._btn_scan)
        btn_row.addStretch()
        root.addLayout(btn_row)
        self._progress = ProgressBar()
        self._progress.setFixedHeight(4)
        self._progress.setVisible(False)
        self._progress.setStyleSheet(
            f"ProgressBar::chunk {{ background: {self._accent}; border-radius: 2px; }}"
        )
        root.addWidget(self._progress)
        self._results_scroll = SmoothScrollArea()
        self._results_scroll.setWidgetResizable(True)
        self._results_scroll.setStyleSheet(
            "SmoothScrollArea { background: transparent; border: none; }"
        )
        self._results_content = QWidget()
        self._results_content.setStyleSheet("background: transparent;")
        self._results_layout = QVBoxLayout(self._results_content)
        self._results_layout.setContentsMargins(0, 0, 10, 0)
        self._results_layout.setSpacing(12)
        self._results_scroll.setWidget(self._results_content)
        root.addWidget(self._results_scroll, 1)
        self._placeholder = CaptionLabel(
            tr('Pulsa "Analizar Biblioteca" para comenzar el diagnóstico.')
        )
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(
            "color: rgba(255,255,255,0.25); font-size: 13px; "
            "background: transparent; padding: 40px;"
        )
        self._results_layout.addWidget(self._placeholder)
        self._results_layout.addStretch()
    def _start_scan(self):
        library = getattr(self.player, 'library', [])
        if not library:
            InfoBar.warning(
                title=tr("Biblioteca vacía"),
                content=tr("No hay canciones en la biblioteca para analizar."),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000,
            )
            return
        self._btn_scan.setEnabled(False)
        self._btn_scan.setText(tr("Analizando…"))
        self._progress.setVisible(True)
        self._progress.setValue(0)
        if self._worker and self._worker.isRunning():
            self._worker.running = False
            self._worker.quit()
            self._worker.wait(500)
        self._worker = _MetadataScanWorker(library, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.scan_complete.connect(self._on_scan_complete)
        self._worker.start()
    def _on_progress(self, current, total):
        if total > 0:
            self._progress.setValue(int(current / total * 100))
    def _on_scan_complete(self, result):
        self._scan_result = result
        self._btn_scan.setEnabled(True)
        self._btn_scan.setText(tr("Analizar Biblioteca"))
        self._progress.setVisible(False)
        self._build_results(result)
    def _build_results(self, data: dict):
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        total = data["total"]
        complete = data["complete"]
        incomplete = total - complete
        pct = int(complete / total * 100) if total else 0
        summary_card = self._make_summary_card(total, complete, incomplete, pct)
        self._results_layout.addWidget(summary_card)
        detail_hdr = QHBoxLayout()
        detail_title = BodyLabel(tr("Detalles por metadato"))
        detail_title.setStyleSheet(
            "color: rgba(255,255,255,0.85); font-weight: 700; font-size: 14px; "
            "background: transparent; border: none;"
        )
        detail_hdr.addWidget(detail_title)
        detail_hdr.addStretch()
        detail_hdr_widget = QWidget()
        detail_hdr_widget.setStyleSheet("background: transparent;")
        detail_hdr_widget.setLayout(detail_hdr)
        self._results_layout.addWidget(detail_hdr_widget)
        for key, (label, color) in _FIELD_LABELS.items():
            tracks_list = data.get(key, [])
            count = len(tracks_list)
            card = self._make_field_card(key, label, color, count, total, tracks_list)
            self._results_layout.addWidget(card)
        if incomplete > 0:
            repair_row = QHBoxLayout()
            repair_row.setContentsMargins(0, 8, 0, 0)
            self._btn_repair = PushButton(tr("Re-extraer metadatos de TODOS los incompletos"))
            self._btn_repair.setFixedHeight(38)
            self._btn_repair.setMinimumWidth(340)
            self._btn_repair.setStyleSheet(
                "PushButton { font-size: 12px; border-radius: 8px; padding: 0 16px; "
                "background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10); color: white; } "
                "PushButton:hover { background: rgba(255,255,255,0.12); }"
            )
            self._btn_repair.clicked.connect(self._repair_all)
            repair_row.addWidget(self._btn_repair)
            repair_row.addStretch()
            repair_widget = QWidget()
            repair_widget.setStyleSheet("background: transparent;")
            repair_widget.setLayout(repair_row)
            self._results_layout.addWidget(repair_widget)
        self._results_layout.addStretch()
    def _make_summary_card(self, total, complete, incomplete, pct):
        card = QWidget()
        card.setObjectName("ToolsSummaryCard")
        card.setStyleSheet("""
            QWidget#ToolsSummaryCard {
                background-color: rgba(255, 255, 255, 0.04);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.06);
            }
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)
        hdr = QHBoxLayout()
        title = BodyLabel(tr("Resumen del análisis"))
        title.setStyleSheet(
            "color: rgba(255,255,255,0.85); font-weight: 700; font-size: 14px; "
            "background: transparent; border: none;"
        )
        hdr.addWidget(title)
        hdr.addStretch()
        badge = QLabel(tr("✓ Completado"))
        badge.setStyleSheet(
            f"color: {self._accent}; font-size: 11px; font-weight: 600; "
            "background: rgba(29,185,84,0.12); border-radius: 10px; "
            "padding: 3px 10px; border: none;"
        )
        hdr.addWidget(badge)
        lay.addLayout(hdr)
        bar_bg = QWidget()
        bar_bg.setFixedHeight(6)
        bar_bg.setStyleSheet(
            "background: rgba(255,255,255,0.06); border-radius: 3px;"
        )
        bar_fill = QWidget(bar_bg)
        fill_w = max(2, int(pct / 100 * 400)) if pct > 0 else 0
        bar_fill.setGeometry(0, 0, fill_w, 6)
        color_fill = "#34D399" if pct >= 80 else ("#F59E0B" if pct >= 50 else "#F87171")
        if pct >= 80:
            grad = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {self._accent}, stop:1 #34D399)"
        elif pct >= 50:
            grad = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {self._accent}, stop:1 #F59E0B)"
        else:
            grad = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {self._accent}, stop:1 #F87171)"
        bar_fill.setStyleSheet(
            f"background: {grad}; border-radius: 3px;"
        )
        lay.addWidget(bar_bg)
        lay.addSpacing(4)
        stats_row = QHBoxLayout()
        stats_row.setSpacing(0)
        _stat_data = [
            (f"{total:,}", tr("Total"), "rgba(255,255,255,0.85)"),
            (f"{complete:,}", tr("Completos"), "#34D399"),
            (f"{incomplete:,}", tr("Incompletos"), "#F87171"),
        ]
        for val, lbl, col in _stat_data:
            stat_w = QWidget()
            stat_w.setStyleSheet("background: transparent; border: none;")
            stat_lay = QHBoxLayout(stat_w)
            stat_lay.setContentsMargins(0, 0, 24, 0)
            stat_lay.setSpacing(8)
            text_col = QVBoxLayout()
            text_col.setSpacing(0)
            v = BodyLabel(val)
            v.setStyleSheet(
                f"color: {col}; font-weight: 700; font-size: 18px; "
                "background: transparent; border: none;"
            )
            text_col.addWidget(v)
            d = CaptionLabel(lbl)
            d.setStyleSheet(
                "color: rgba(255,255,255,0.40); font-size: 10px; "
                "background: transparent; border: none;"
            )
            text_col.addWidget(d)
            stat_lay.addLayout(text_col)
            stats_row.addWidget(stat_w)
        stats_row.addStretch()
        gauge = _CircularGauge(pct, color_fill, self._accent)
        gauge.setFixedSize(56, 56)
        stats_row.addWidget(gauge)
        lay.addLayout(stats_row)
        return card
    def _make_field_card(self, key, label, color, count, total, tracks_list):
        card = QWidget()
        uid = f"FieldCard_{key}"
        card.setObjectName(uid)
        card.setStyleSheet(f"""
            QWidget#{uid} {{
                background-color: rgba(255, 255, 255, 0.03);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(0)
        hdr = QHBoxLayout()
        hdr.setSpacing(10)
        dot = QLabel("●")
        dot.setFixedWidth(10)
        dot.setStyleSheet(
            f"color: {color}; font-size: 8px; background: transparent; border: none;"
        )
        hdr.addWidget(dot)
        _field_icons = {
            "missing_genre": "🏷",
            "missing_year": "📅",
            "missing_artist": "👤",
            "missing_album": "💿",
            "missing_cover": "🖼",
            "no_duration": "⏱",
        }
        icon_lbl = QLabel(_field_icons.get(key, "❓"))
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(
            "background: rgba(255,255,255,0.04); border-radius: 8px; "
            "font-size: 16px; border: none;"
        )
        hdr.addWidget(icon_lbl)
        _field_descs = {
            "missing_genre": "Canciones sin información de género.",
            "missing_year": "Canciones sin información de año.",
            "missing_artist": "Canciones sin información de artista.",
            "missing_album": "Canciones sin información de álbum.",
            "missing_cover": "Canciones sin carátula embebida.",
            "no_duration": "Canciones sin duración detectada.",
        }
        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        name = BodyLabel(tr("{label} faltante").format(label=tr(label)))
        name.setStyleSheet(
            "color: rgba(255,255,255,0.90); font-weight: 600; font-size: 13px; "
            "background: transparent; border: none;"
        )
        title_col.addWidget(name)
        desc = CaptionLabel(tr(_field_descs.get(key, "")))
        desc.setStyleSheet(
            "color: rgba(255,255,255,0.35); font-size: 10px; "
            "background: transparent; border: none;"
        )
        title_col.addWidget(desc)
        hdr.addLayout(title_col, 1)
        pct_val = int(count / total * 100) if total else 0
        badge = CaptionLabel(tr("{count} tracks").format(count=count))
        badge.setStyleSheet(
            f"color: {color}; font-size: 11px; font-weight: 600; "
            "background: transparent; border: none;"
        )
        hdr.addWidget(badge)
        pct_lbl = CaptionLabel(f"{pct_val}%")
        pct_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.40); font-size: 11px; "
            "background: transparent; border: none; margin-right: 4px;"
        )
        hdr.addWidget(pct_lbl)
        arrow = TransparentToolButton(FIF.CHEVRON_RIGHT)
        arrow.setFixedSize(28, 28)
        arrow.setIconSize(QSize(12, 12))
        hdr.addWidget(arrow)
        lay.addLayout(hdr)
        mini_bar_bg = QWidget()
        mini_bar_bg.setFixedHeight(3)
        mini_bar_bg.setStyleSheet(
            "background: rgba(255,255,255,0.04); border-radius: 1px; margin-top: 6px;"
        )
        mini_fill = QWidget(mini_bar_bg)
        fill_w = max(1, int(pct_val / 100 * 300)) if pct_val > 0 else 0
        mini_fill.setGeometry(0, 0, fill_w, 3)
        mini_fill.setStyleSheet(f"background: {color}; border-radius: 1px;")
        lay.addWidget(mini_bar_bg)
        expand_panel = QWidget()
        expand_panel.setStyleSheet("background: transparent; border: none;")
        expand_panel.setVisible(False)
        expand_lay = QHBoxLayout(expand_panel)
        expand_lay.setContentsMargins(52, 10, 0, 4)
        expand_lay.setSpacing(10)
        if count > 0:
            btn_view = PushButton(tr("Vista previa ({count})").format(count=min(count, 50)))
            btn_view.setFixedHeight(32)
            btn_view.setMinimumWidth(170)
            btn_view.setStyleSheet(
                "PushButton { font-size: 12px; border-radius: 6px; padding: 0 14px; "
                "background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10); color: white; } "
                "PushButton:hover { background: rgba(255,255,255,0.12); }"
            )
            btn_view.clicked.connect(lambda checked, k=key: self._show_tracks_table(k))
            expand_lay.addWidget(btn_view)
            btn_fix = PushButton(tr("Re-extraer"))
            btn_fix.setFixedHeight(32)
            btn_fix.setMinimumWidth(120)
            btn_fix.setStyleSheet(
                "PushButton { font-size: 12px; border-radius: 6px; padding: 0 14px; "
                "background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10); color: white; } "
                "PushButton:hover { background: rgba(255,255,255,0.12); }"
            )
            btn_fix.clicked.connect(lambda checked, k=key: self._repair_field(k))
            expand_lay.addWidget(btn_fix)
        expand_lay.addStretch()
        lay.addWidget(expand_panel)
        _expanded = [False]
        def _toggle():
            _expanded[0] = not _expanded[0]
            expand_panel.setVisible(_expanded[0])
            arrow.setIcon(FIF.CHEVRON_RIGHT if not _expanded[0] else FIF.UP)
        arrow.clicked.connect(_toggle)
        hdr_widget = QWidget()
        hdr_widget.setStyleSheet("background: transparent; border: none;")
        hdr_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        return card
    def _show_tracks_table(self, field_key):
        if not self._scan_result:
            return
        tracks = self._scan_result.get(field_key, [])[:50]
        if not tracks:
            return
        label, color = _FIELD_LABELS.get(field_key, ("?", "#888"))
        for i in range(self._results_layout.count()):
            item = self._results_layout.itemAt(i)
            w = item.widget() if item else None
            if w and w.objectName() == "ToolsDetailTable":
                w.deleteLater()
        container = QWidget()
        container.setObjectName("ToolsDetailTable")
        container.setStyleSheet("""
            QWidget#ToolsDetailTable {
                background-color: rgba(255, 255, 255, 0.03);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
        """)
        c_lay = QVBoxLayout(container)
        c_lay.setContentsMargins(16, 12, 16, 12)
        c_lay.setSpacing(8)
        hdr = BodyLabel(tr("Tracks sin {label} (mostrando {count})").format(label=tr(label), count=len(tracks)))
        hdr.setStyleSheet(
            f"color: {color}; font-weight: 600; font-size: 13px; "
            "background: transparent; border: none;"
        )
        c_lay.addWidget(hdr)
        table = TableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels([tr("Título"), tr("Artista"), tr("Álbum"), tr("Archivo")])
        table.setRowCount(len(tracks))
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setMinimumHeight(min(300, 32 + len(tracks) * 30))
        table.setStyleSheet(
            "TableWidget { background: rgba(0,0,0,0.15); border: none; border-radius: 8px; }"
            "QHeaderView::section { background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.6); "
            "border: none; padding: 4px 8px; font-size: 11px; }"
        )
        for row, t in enumerate(tracks):
            table.setItem(row, 0, QTableWidgetItem(t.title or ""))
            table.setItem(row, 1, QTableWidgetItem(t.artist or ""))
            table.setItem(row, 2, QTableWidgetItem(t.album or ""))
            table.setItem(row, 3, QTableWidgetItem(os.path.basename(t.filepath)))
        hh = table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        c_lay.addWidget(table)
        idx = max(0, self._results_layout.count() - 1)
        self._results_layout.insertWidget(idx, container)
    def _repair_field(self, field_key):
        if not self._scan_result:
            return
        tracks = self._scan_result.get(field_key, [])
        if not tracks:
            return
        self._run_repair(tracks, field_key)
    def _repair_all(self):
        if not self._scan_result:
            return
        seen = set()
        all_tracks = []
        for key in _FIELD_LABELS:
            for t in self._scan_result.get(key, []):
                if t.filepath not in seen:
                    seen.add(t.filepath)
                    all_tracks.append(t)
        if all_tracks:
            self._run_repair(all_tracks, "all")
    def _run_repair(self, tracks, label):
        self._btn_scan.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)
        if hasattr(self, '_btn_repair'):
            self._btn_repair.setEnabled(False)
        if self._repair_worker and self._repair_worker.isRunning():
            self._repair_worker.running = False
            self._repair_worker.quit()
            self._repair_worker.wait(500)
        self._repair_worker = _MetadataRepairWorker(tracks, self)
        self._repair_worker.progress.connect(self._on_progress)
        self._repair_worker.finished_repair.connect(
            lambda repaired: self._on_repair_done(repaired, label)
        )
        self._repair_worker.start()
    def _on_repair_done(self, repaired, label):
        self._progress.setVisible(False)
        self._btn_scan.setEnabled(True)
        if hasattr(self, '_btn_repair'):
            self._btn_repair.setEnabled(True)
        try:
            from database import save_library_cache
            save_library_cache(self.player.library)
        except Exception as e:
            logging.error(f"Error guardando biblioteca tras reparación: {e}")
        InfoBar.success(
            title=tr("Reparación completada"),
            content=tr("Se re-extrajeron metadatos de {count} canciones.").format(count=repaired),
            parent=self,
            position=InfoBarPosition.TOP,
            duration=4000,
        )
        self._start_scan()
    def _on_back(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, 'setCurrentIndex'):
                parent.setCurrentIndex(0)
                return
            parent = parent.parent()