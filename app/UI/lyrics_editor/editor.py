import os
import logging
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel
from PyQt6.QtGui import QColor, QCursor, QKeySequence, QShortcut
from qfluentwidgets import TitleLabel, BodyLabel, PrimaryPushButton, FluentIcon as FIF, ComboBox, PushButton
from core.notification_manager import notify
from core.language_manager import tr
from theme_manager import get_current_accent_hex
from services.lyrics_fetcher import LyricsFetcherThread
from UI.lyrics_editor.components import LyricsHighlighter, CodeEditor, EditorContainer
from UI.lyrics_editor.widgets.track_info_card import TrackInfoCard
from UI.lyrics_editor.widgets.search_panel import SearchPanel
from UI.lyrics_editor.widgets.editor_toolbar import EditorToolbar
from UI.lyrics_editor.managers.file_io_manager import FileIOManager
from UI.lyrics_editor.managers.sync_preview_manager import SyncPreviewManager
from UI.lyrics_editor.managers.text_ops_manager import TextOpsManager
class LyricsEditorDialog(QDialog):
    def __init__(self, track, parent=None):
        super().__init__(parent)
        self.track = track
        self.accent_color = get_current_accent_hex()
        parent_window = self.parent()
        self.initial_repeat_mode = getattr(parent_window.queue, 'repeat_mode', 0) if hasattr(parent_window, 'queue') else 0
        self.setWindowTitle("Lyrics Editor v1.0.0 - Aiiko Music")
        self.setMinimumSize(1050, 700)
        self.resize(1050, 700)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._setup_ui()
        self._setup_managers(parent_window)
        self._connect_signals()
        self._load_initial_data()
    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter
        from PyQt6.QtCore import QRectF
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#141414"))
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()).adjusted(0.5, 0.5, -0.5, -0.5), 10.0, 10.0)
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 20, 32, 24)
        layout.setSpacing(12)
        self.top_section = QWidget()
        top_layout = QVBoxLayout(self.top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(16)
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title = TitleLabel(tr("Editar letra"))
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        subtitle = BodyLabel(tr("Edita o busca la letra de tu canción."))
        subtitle.setStyleSheet("color: #999; font-size: 13px;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        top_layout.addLayout(header_layout)
        self.info_card = TrackInfoCard(self.track, self.accent_color)
        top_layout.addWidget(self.info_card)
        self.search_panel = SearchPanel(self.track.title, self.track.artist, self.accent_color)
        top_layout.addWidget(self.search_panel)
        self.combo_versions = ComboBox()
        self.combo_versions.setFixedWidth(200)
        self.combo_versions.hide()
        layout.addWidget(self.top_section)
        self.toolbar = EditorToolbar(self.accent_color, self.initial_repeat_mode)
        self.toolbar.layout().addWidget(self.combo_versions)
        layout.addWidget(self.toolbar)
        editor_wrapper = QWidget()
        editor_v = QVBoxLayout(editor_wrapper)
        editor_v.setContentsMargins(0,0,0,0)
        self.editor_container = EditorContainer()
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(0, 10, 0, 10)
        overlay = QWidget()
        top_ed_bar = QHBoxLayout(overlay)
        top_ed_bar.setContentsMargins(0, 0, 0, 0)
        top_ed_bar.setSpacing(8)
        self.lbl_lines = QLabel("0 líneas")
        self.lbl_lines.setStyleSheet(f"color: {self.accent_color}; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        self.btn_full = PushButton()
        self.btn_full.setIcon(FIF.FULL_SCREEN.icon(color="#CCC"))
        self.btn_full.setFixedSize(24, 24)
        self.btn_full.setStyleSheet("background: transparent; border: none;")
        self.btn_full.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        top_ed_bar.addWidget(self.lbl_lines)
        top_ed_bar.addWidget(self.btn_full)
        self.editor_container.set_overlay(overlay)
        self.text_editor = CodeEditor()
        self.text_editor.setPlaceholderText(tr("[00:12.34] Pega tu letra aquí...\nO búscala en internet usando el botón superior."))
        self.highlighter = LyricsHighlighter(self.text_editor.document(), self.accent_color)
        editor_layout.addWidget(self.text_editor)
        editor_v.addWidget(self.editor_container, 1)
        layout.addWidget(editor_wrapper, 1)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        action_layout.setContentsMargins(0, 10, 0, 0)
        self.btn_delete = PushButton(tr("Eliminar LRC"))
        self.btn_delete.hide()
        btn_cancel = PushButton(tr("Cancelar"))
        self.btn_save = PrimaryPushButton(tr("Guardar Archivo .lrc"))
        self.btn_embed = PrimaryPushButton(tr("Incrustar en Metadatos"))
        if self.track and getattr(self.track, 'filepath', '').lower().endswith('.wav'):
            self.btn_embed.hide()
        action_layout.addWidget(self.btn_delete)
        action_layout.addStretch()
        action_layout.addWidget(btn_cancel)
        action_layout.addWidget(self.btn_save)
        action_layout.addWidget(self.btn_embed)
        layout.addLayout(action_layout)
        self.is_expanded = False
        self.auto_repeat_activated = False
        self.btn_full.clicked.connect(self._toggle_fullscreen)
        btn_cancel.clicked.connect(self.close)
    def _setup_managers(self, parent_window):
        audio_engine = getattr(parent_window, 'audio_engine', None)
        queue = getattr(parent_window, 'queue', None)
        self.file_manager = FileIOManager(self.track, self.text_editor)
        self.sync_manager = SyncPreviewManager(audio_engine, self.text_editor, self.accent_color, queue)
        self.text_manager = TextOpsManager(self.text_editor)
        if audio_engine:
            audio_engine.state_changed.connect(self.toolbar.update_play_icon)
            self.toolbar.update_play_icon(audio_engine.is_playing())
    def _connect_signals(self):
        self.text_editor.blockCountChanged.connect(self._update_line_count)
        self.text_editor.textChanged.connect(self._on_text_changed)
        self.toolbar.action_copy.connect(self._copy_lyrics)
        self.toolbar.action_paste.connect(self.text_editor.paste)
        self.toolbar.action_clear.connect(self.text_editor.clear)
        self.toolbar.action_select_all.connect(self.text_editor.selectAll)
        self.toolbar.action_load_file.connect(self._on_load_file)
        self.toolbar.action_add_time.connect(lambda: self.text_manager.insert_timestamp(getattr(self.parent(), 'audio_engine', None)))
        self.toolbar.action_sync_back.connect(lambda: self.text_manager.batch_adjust_time(-1))
        self.toolbar.action_sync_fwd.connect(lambda: self.text_manager.batch_adjust_time(1))
        self.toolbar.action_reset.connect(self._load_initial_data)
        self.toolbar.action_preview.connect(self._toggle_preview)
        self.toolbar.action_loop.connect(self._toggle_loop_mode)
        self.toolbar.action_play_pause.connect(self._toggle_play_pause)
        self.toolbar.action_seek_back.connect(self._seek_back)
        self.toolbar.action_seek_fwd.connect(self._seek_fwd)
        self.toolbar.action_restart.connect(self._restart)
        self.shortcut_seek_back = QShortcut(QKeySequence("Ctrl+Left"), self)
        self.shortcut_seek_back.activated.connect(self._seek_back)
        self.shortcut_seek_back.setContext(Qt.ShortcutContext.WindowShortcut)
        self.shortcut_seek_fwd = QShortcut(QKeySequence("Ctrl+Right"), self)
        self.shortcut_seek_fwd.activated.connect(self._seek_fwd)
        self.shortcut_seek_fwd.setContext(Qt.ShortcutContext.WindowShortcut)
        self.shortcut_restart = QShortcut(QKeySequence("Ctrl+Home"), self)
        self.shortcut_restart.activated.connect(self._restart)
        self.shortcut_restart.setContext(Qt.ShortcutContext.WindowShortcut)
        self.search_panel.search_requested.connect(self._start_search)
        self.combo_versions.currentIndexChanged.connect(self._on_combo_version_changed)
        self.btn_save.clicked.connect(self._save_lrc)
        self.btn_embed.clicked.connect(self._embed_metadata)
        self.btn_delete.clicked.connect(self._delete_lrc)
    def _load_initial_data(self):
        loaded, format_text = self.file_manager.load_existing_lyrics()
        if loaded:
            self.info_card.update_source_badge(format_text, True)
            if "Archivo" in format_text:
                self.btn_delete.show()
            else:
                self.btn_delete.hide()
        else:
            self.btn_delete.hide()
    def _update_line_count(self, count):
        self.lbl_lines.setText(f"{count} líneas")
        text = self.text_editor.toPlainText()
        import re
        is_synced = bool(re.search(r'\[\d{2}:\d{2}', text))
        if count <= 1 and not text.strip():
            self.info_card.update_format_val("Desconocido")
        elif is_synced:
            self.info_card.update_format_val("LRC (Sincronizado)")
        else:
            self.info_card.update_format_val("Texto Plano")
    def _on_text_changed(self):
        if not self.auto_repeat_activated:
            self.auto_repeat_activated = True
            parent = self.parent()
            if hasattr(parent, 'queue') and getattr(parent.queue, 'repeat_mode', 0) != 2:
                parent.queue.set_repeat_mode(2)
                self.toolbar.set_loop_active(True)
                if hasattr(parent, 'playback_ui_controller'):
                    parent.playback_ui_controller._update_repeat_icon()
                if hasattr(parent, 'queue_controller'):
                    parent.queue_controller.update_gapless_preload()
    def _toggle_fullscreen(self):
        self.is_expanded = not self.is_expanded
        self.top_section.setVisible(not self.is_expanded)
        icon = FIF.BACK_TO_WINDOW if self.is_expanded else FIF.FULL_SCREEN
        self.btn_full.setIcon(icon.icon(color="#CCC"))
    def _copy_lyrics(self):
        text = self.text_editor.toPlainText()
        from PyQt6.QtGui import QGuiApplication
        if not self.text_editor.textCursor().hasSelection():
            QGuiApplication.clipboard().setText(text)
            notify.success(tr("Copiado"), tr("Toda la letra copiada al portapapeles."), parent=self)
        else:
            QGuiApplication.clipboard().setText(self.text_editor.textCursor().selectedText())
            notify.success(tr("Copiado"), tr("Texto seleccionado copiado al portapapeles."), parent=self)
    def _on_load_file(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, tr("Cargar archivo de letra"), "", "Archivos de Letras (*.lrc *.txt);;Todos los archivos (*)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_editor.setPlainText(content)
                notify.success(tr("Cargado"), tr("Archivo cargado al editor."), parent=self)
            except Exception as e:
                logging.error(f"Error loading file: {e}")
                notify.error(tr("Error"), tr(f"No se pudo leer el archivo:\n{e}"), parent=self)
    def _toggle_preview(self):
        parent = self.parent()
        if not self.sync_manager.preview_active:
            if hasattr(parent, 'queue') and getattr(parent.queue, 'current_index', -1) >= 0:
                tracks = getattr(parent.queue, 'tracks', [])
                idx = parent.queue.current_index
                if 0 <= idx < len(tracks):
                    current_track = tracks[idx]
                    if current_track != self.track:
                        from core.notification_manager import notify
                        notify.warning("Vista Previa no disponible", "El reproductor avanzó a otra canción. Reproduce esta pista nuevamente para sincronizar visualmente.", parent=self)
                        return
        active = self.sync_manager.toggle_preview()
        self.toolbar.set_preview_active(active)
    def _toggle_loop_mode(self):
        parent = self.parent()
        if hasattr(parent, 'queue'):
            current = getattr(parent.queue, 'repeat_mode', 0)
            new_mode = 0 if current == 2 else 2
            parent.queue.set_repeat_mode(new_mode)
            self.toolbar.set_loop_active(new_mode == 2)
            if hasattr(parent, 'playback_ui_controller'):
                parent.playback_ui_controller._update_repeat_icon()
            if hasattr(parent, 'queue_controller'):
                parent.queue_controller.update_gapless_preload()
    def _toggle_play_pause(self):
        parent = self.parent()
        if hasattr(parent, 'playback_controller'):
            parent.playback_controller.toggle_play()
    def _seek_back(self):
        parent = self.parent()
        if hasattr(parent, 'audio_engine'):
            current_pos = parent.audio_engine.get_position()
            parent.audio_engine.set_position(max(0, current_pos - 10000))
    def _seek_fwd(self):
        parent = self.parent()
        if hasattr(parent, 'audio_engine'):
            current_pos = parent.audio_engine.get_position()
            total_duration = parent.audio_engine.get_length()
            parent.audio_engine.set_position(min(total_duration, current_pos + 10000))
    def _restart(self):
        parent = self.parent()
        if hasattr(parent, 'audio_engine'):
            parent.audio_engine.set_position(0)
    def _start_search(self, title, artist):
        if not title or not artist:
            notify.warning("Datos incompletos", "Por favor ingresa título y artista.", parent=self)
            return
        self.search_panel.set_loading(True)
        self.combo_versions.hide()
        self.text_editor.setPlaceholderText(tr("Buscando en la base de datos de LRCLIB.net...\nPor favor, espera."))
        self.fetcher = LyricsFetcherThread(title, artist)
        self.fetcher.result_ready.connect(self._on_search_result)
        self.fetcher.start()
    def _on_search_result(self, results):
        self.search_panel.set_loading(False)
        self.results_cache = results
        self.combo_versions.blockSignals(True)
        self.combo_versions.clear()
        if self.results_cache:
            if len(self.results_cache) > 1:
                self.combo_versions.show()
            else:
                self.combo_versions.hide()
            for idx, result in enumerate(self.results_cache):
                type_str = "Sync." if result['is_synced'] else "Plain"
                self.combo_versions.addItem(f"Opción {idx+1} ({type_str})")
            self.combo_versions.blockSignals(False)
            self.combo_versions.setCurrentIndex(0)
            self._display_current_result(0, show_notify=True)
        else:
            self.combo_versions.blockSignals(False)
            self.combo_versions.hide()
            notify.error("Sin resultados", "No se encontraron letras para esta cancion.", parent=self)
            self.text_editor.setPlainText("")
            self.text_editor.setPlaceholderText(tr("No se encontro nada.\nPuedes buscar la letra en Google, pegarla aqui y editarla manualmente."))
    def _on_combo_version_changed(self, index):
        self._display_current_result(index, show_notify=False)
    def _display_current_result(self, index, show_notify=False):
        if not self.results_cache or index < 0 or index >= len(self.results_cache): return
        result = self.results_cache[index]
        self.text_editor.setPlainText(result['text'])
        if show_notify:
            if result['is_synced']:
                notify.success("Letra Sincronizada", "Esta version tiene marcas de tiempo (Karaoke).", parent=self)
            else:
                notify.warning("Letra Estatica", "Esta version es texto plano (Sin sincronizar).", parent=self)
    def _save_lrc(self):
        if self.file_manager.save_lyrics_file():
            self.accept()
    def _embed_metadata(self):
        if self.file_manager.embed_lyrics_to_file():
            self.accept()
    def _delete_lrc(self):
        if self.file_manager.delete_lyrics_file():
            self.info_card.update_source_badge(tr("Sin letra"), False)
            self.btn_delete.hide()
    def _cleanup(self):
        parent = self.parent()
        if hasattr(parent, 'audio_engine'):
            try:
                parent.audio_engine.state_changed.disconnect(self.toolbar.update_play_icon)
            except Exception:
                pass
        self.sync_manager.stop()
        if hasattr(self, 'fetcher') and self.fetcher.isRunning():
            self.fetcher.quit()
            self.fetcher.wait(500)
        if hasattr(parent, 'queue'):
            current_mode = getattr(parent.queue, 'repeat_mode', 0)
            if current_mode != self.initial_repeat_mode:
                parent.queue.set_repeat_mode(self.initial_repeat_mode)
                if hasattr(parent, 'playback_ui_controller'):
                    parent.playback_ui_controller._update_repeat_icon()
                if hasattr(parent, 'queue_controller'):
                    parent.queue_controller.update_gapless_preload()
    def closeEvent(self, event):
        self._cleanup()
        super().closeEvent(event)
    def accept(self):
        self._cleanup()
        super().accept()
    def reject(self):
        self._cleanup()
        super().reject()