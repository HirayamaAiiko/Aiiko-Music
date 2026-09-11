from PyQt6.QtWidgets import QHBoxLayout
from qfluentwidgets import PushButton, FluentIcon as FIF
from .base_settings_tab import BaseSettingsTab
from core.language_manager import tr
class CacheTab(BaseSettingsTab):
    def __init__(self, player, parent=None):
        super().__init__(player, parent)
        card1, cl1 = self._create_card(tr("Mantenimiento de Caché"), FIF.BRUSH)
        player.btn_repair_cache = PushButton(FIF.BRUSH, tr("Limpiar y Reparar"))
        player.btn_repair_cache.clicked.connect(player.library_sync_controller.repair_cover_cache)
        player.btn_repair_missing = PushButton(FIF.SEARCH, tr("Reparar Faltantes"))
        player.btn_repair_missing.clicked.connect(player.library_sync_controller.repair_missing_covers)
        cover_btns = QHBoxLayout()
        cover_btns.setSpacing(8)
        cover_btns.addWidget(player.btn_repair_missing)
        cover_btns.addWidget(player.btn_repair_cache)
        self._setting_row_layout(cl1, tr("Caché de Carátulas"),
                                 tr("Limpia y re-extrae las carátulas si algunas no se muestran correctamente."),
                                 cover_btns)
        player.btn_repair_artist_cache = PushButton(FIF.SYNC, tr("Recargar Info"))
        player.btn_repair_artist_cache.clicked.connect(player.library_sync_controller.repair_artist_cache)
        self._setting_row(cl1, tr("Caché de Artistas"),
                          tr("Limpia la info de artistas y permite recargarla desde la red."),
                          player.btn_repair_artist_cache, add_separator=False)
        card2, cl2 = self._create_card(tr("Caché de Letras"), FIF.DOCUMENT)
        self.btn_pregen_lyrics = PushButton(FIF.DOWNLOAD, tr("Pre-generar Caché"))
        self.btn_pregen_lyrics.clicked.connect(self._start_lyrics_pregen)
        self._setting_row(cl2, tr("Caché de Letras Offline"),
                          tr("Escanea la biblioteca y extrae las letras de los metadatos para carga instantánea."),
                          self.btn_pregen_lyrics, add_separator=False)
        self.main_layout.addWidget(card1)
        self.main_layout.addWidget(card2)
        self.main_layout.addStretch()
    def _start_lyrics_pregen(self):
        from qfluentwidgets import InfoBar, InfoBarPosition
        library = getattr(self.player, 'library', [])
        if not library:
            InfoBar.warning(
                title=tr("Biblioteca vacía"),
                content=tr("No hay canciones en la biblioteca para procesar."),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000,
            )
            return
        self.btn_pregen_lyrics.setEnabled(False)
        self.btn_pregen_lyrics.setText(tr("Generando…"))
        self._pregen_worker = _LyricsCacheGeneratorWorker(library, self)
        self._pregen_worker.progress.connect(self._on_pregen_progress)
        self._pregen_worker.finished_generation.connect(self._on_pregen_finished)
        self._pregen_worker.start()
    def _on_pregen_progress(self, current, total):
        self.btn_pregen_lyrics.setText(f"{tr('Generando…')} ({current}/{total})")
    def _on_pregen_finished(self, new_generated):
        from qfluentwidgets import InfoBar, InfoBarPosition
        self.btn_pregen_lyrics.setEnabled(True)
        self.btn_pregen_lyrics.setText(tr("Pre-generar Caché"))
        InfoBar.success(
            title=tr("Proceso Completado"),
            content=tr(f"Se generaron {new_generated} nuevas cachés de letras. Las demás ya estaban listas."),
            parent=self,
            position=InfoBarPosition.TOP,
            duration=4000,
        )
import os
import hashlib
import logging
from PyQt6.QtCore import QThread, pyqtSignal
class _LyricsCacheGeneratorWorker(QThread):
    progress = pyqtSignal(int, int)
    finished_generation = pyqtSignal(int)
    def __init__(self, library, parent=None):
        super().__init__(parent)
        self._library = library
        self.running = True
    def _clean_text(self, text):
        import html
        text = html.unescape(text).replace('\ufeff', '').replace('\x00', '')
        return text.replace('\r\n', '\n').replace('\r', '\n')
    def _fix_mojibake(self, text):
        try:
            return text.encode('latin1').decode('utf-8')
        except:
            return text
    def run(self):
        from config import LYRICS_CACHE_DIR
        from services.lyrics_service import LyricsLoaderWorker
        total = len(self._library)
        new_generated = 0
        for i, track in enumerate(self._library):
            if not self.running:
                break
            try:
                try:
                    mtime = os.path.getmtime(track.filepath)
                except:
                    mtime = getattr(track, 'mtime', 0)
                unique_string = f"{track.filepath}_{mtime}"
                track_hash = hashlib.md5(unique_string.encode('utf-8')).hexdigest()
                cache_file = os.path.join(LYRICS_CACHE_DIR, f"{track_hash}.json")
                if not os.path.exists(cache_file):
                    base_path = os.path.splitext(track.filepath)[0]
                    worker = LyricsLoaderWorker(track, base_path, self._clean_text, self._fix_mojibake)
                    worker.run()           
                    new_generated += 1
            except Exception as e:
                logging.debug(f"Error pre-generando caché para {track.filepath}: {e}")
            if i % 5 == 0 or i == total - 1:
                self.progress.emit(i + 1, total)
        self.finished_generation.emit(new_generated)