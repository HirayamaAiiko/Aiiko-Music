import os
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QUrl, QRunnable, QThreadPool, QObject, QThread
from PyQt6.QtGui import QIcon, QPixmap, QImage, QPainter, QPainterPath, QColor
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSizePolicy, QStackedWidget, QFormLayout, QFileDialog)
from qfluentwidgets import (MessageBoxBase, LineEdit, PushButton, PrimaryPushButton, 
                            Pivot, TextEdit, SubtitleLabel, CaptionLabel, BodyLabel,
                            FluentIcon as FIF, SmoothScrollArea, isDarkTheme,
                            SegmentedWidget)
from services.metadata_editor import MetadataEditorService
from core.language_manager import tr
class DropImageWidget(QWidget):
    image_dropped = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedSize(200, 200)
        self.setObjectName("dropZone")
        self.setStyleSheet("""
            #dropZone {
                background: rgba(255, 255, 255, 0.05);
                border: 2px dashed rgba(255, 255, 255, 0.2);
                border-radius: 12px;
            }
            #dropZone:hover {
                background: rgba(255, 255, 255, 0.1);
                border: 2px dashed rgba(255, 255, 255, 0.5);
            }
        """)
        layout = QVBoxLayout(self)
        self.lbl_icon = QLabel(self)
        self.lbl_icon.setPixmap(FIF.PHOTO.icon(color="white").pixmap(48, 48))
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_text = BodyLabel(tr("Arrastra una imagen\no haz clic aquí"), self)
        self.lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_text.setStyleSheet("border: none; background: transparent;")
        self.lbl_image = QLabel(self)
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image.hide()
        layout.addStretch()
        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_text)
        layout.addWidget(self.lbl_image)
        layout.addStretch()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.image_dropped.emit(path)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.acceptDrops():
            self.trigger_file_dialog()
    def trigger_file_dialog(self):
        if not self.acceptDrops():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Seleccionar Carátula"), "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self.image_dropped.emit(path)
class MetadataLoaderWorker(QThread):
    finished_load = pyqtSignal(dict)
    def __init__(self, filepath, parent=None):
        super().__init__(parent)
        self.filepath = filepath
    def run(self):
        props = MetadataEditorService.get_file_properties(self.filepath)
        self.finished_load.emit(props)
class MetadataEditorDialog(MessageBoxBase):
    metadata_saved = pyqtSignal(dict, str)                                                      
    def __init__(self, track, parent=None):
        super().__init__(parent)
        self.track = track
        self._new_cover_path = None
        self._original_cover = track.cover_path
        self.widget.setMinimumWidth(550)
        self.widget.setMaximumWidth(800)
        self._build_header()
        self._build_tabs()
        self._is_edit_mode = False
        try:
            self.yesButton.disconnect()
        except TypeError:
            pass
        self.yesButton.clicked.connect(self._on_yes_clicked)
        self._set_edit_mode(False)
        self._populate_data()
    def _build_header(self):
        self.header_widget = QWidget(self)
        self.header_widget.setMinimumHeight(100)
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(20, 20, 20, 10)
        self.cover_label = QLabel(self.header_widget)
        self.cover_label.setFixedSize(100, 100)
        self.cover_label.setStyleSheet("border-radius: 8px;")
        info_layout = QVBoxLayout()
        self.lbl_title = SubtitleLabel(tr("Título de la canción"), self.header_widget)
        self.lbl_artist = BodyLabel(tr("Artista"), self.header_widget)
        self.lbl_artist.setStyleSheet("color: gray;")
        info_layout.addWidget(self.lbl_title)
        info_layout.addWidget(self.lbl_artist)
        info_layout.addStretch()
        self.btn_web_search = PushButton(FIF.GLOBE, tr("Buscar en Internet"), self.header_widget)
        self.btn_web_search.clicked.connect(self._open_metadata_search)
        self.header_layout.addWidget(self.cover_label)
        self.header_layout.addLayout(info_layout)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.btn_web_search, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.viewLayout.insertWidget(0, self.header_widget)
    def _set_edit_mode(self, enabled: bool):
        self._is_edit_mode = enabled
        self.le_title.setReadOnly(not enabled)
        self.le_artist.setReadOnly(not enabled)
        self.le_albumartist.setReadOnly(not enabled)
        self.le_album.setReadOnly(not enabled)
        self.le_composer.setReadOnly(not enabled)
        self.le_year.setReadOnly(not enabled)
        self.le_genre.setReadOnly(not enabled)
        self.le_tracknum.setReadOnly(not enabled)
        self.te_lyrics_static.setReadOnly(not enabled)
        self.te_lyrics_sync.setReadOnly(not enabled)
        self.drop_zone.setAcceptDrops(enabled)
        if not enabled:
            self.drop_zone.lbl_text.setText(tr("Carátula (Solo lectura)"))
            self.drop_zone.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.drop_zone.lbl_text.setText(tr("Arrastra una imagen\no haz clic aquí"))
            self.drop_zone.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select_art.setVisible(enabled)
        if not enabled:
            self.btn_reset_art.hide()
        elif self._new_cover_path:
            self.btn_reset_art.show()
        self.btn_web_search.setVisible(enabled)
        if enabled:
            self.yesButton.setText(tr("Guardar Cambios"))
            self.yesButton.setIcon(FIF.SAVE)
            self.cancelButton.setText(tr("Cancelar"))
        else:
            self.yesButton.setText(tr("Editar Metadatos"))
            self.yesButton.setIcon(FIF.EDIT)
            self.cancelButton.setText(tr("Cerrar"))
    def _on_yes_clicked(self):
        if not self._is_edit_mode:
            self._set_edit_mode(True)
        else:
            self.accept()
    def _build_tabs(self):
        self.pivot = Pivot(self)
        self.stacked_widget = QStackedWidget(self)
        self.tab_general = SmoothScrollArea()
        self.tab_general.setWidgetResizable(True)
        self.tab_general.setStyleSheet("QScrollArea { border: none; }")
        general_content = QWidget()
        general_content.setObjectName("generalContent")
        form_layout = QFormLayout(general_content)
        form_layout.setSpacing(15)
        self.le_title = LineEdit(self)
        self.le_artist = LineEdit(self)
        self.le_albumartist = LineEdit(self)
        self.le_album = LineEdit(self)
        self.le_composer = LineEdit(self)
        self.le_year = LineEdit(self)
        self.le_year.setMaxLength(4)
        self.le_genre = LineEdit(self)
        self.le_tracknum = LineEdit(self)
        form_layout.addRow(tr("Título:"), self.le_title)
        form_layout.addRow(tr("Artista:"), self.le_artist)
        form_layout.addRow(tr("Artista del Álbum:"), self.le_albumartist)
        form_layout.addRow(tr("Álbum:"), self.le_album)
        form_layout.addRow(tr("Compositor:"), self.le_composer)
        form_layout.addRow(tr("Año:"), self.le_year)
        form_layout.addRow(tr("Género:"), self.le_genre)
        form_layout.addRow(tr("Pista:"), self.le_tracknum)
        self.tab_general.setWidget(general_content)
        self.tab_artwork = QWidget(self)
        art_layout = QVBoxLayout(self.tab_artwork)
        art_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_zone = DropImageWidget(self.tab_artwork)
        self.drop_zone.image_dropped.connect(self._on_image_dropped)
        art_layout.addWidget(self.drop_zone)
        self.btn_select_art = PushButton(tr("Seleccionar Imagen..."), self.tab_artwork)
        self.btn_select_art.clicked.connect(self.drop_zone.trigger_file_dialog)
        self.btn_reset_art = PushButton(tr("Restaurar Original"), self.tab_artwork)
        self.btn_reset_art.clicked.connect(self._reset_artwork)
        self.btn_reset_art.hide()
        art_layout.addSpacing(15)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.btn_select_art)
        buttons_layout.addWidget(self.btn_reset_art)
        art_layout.addLayout(buttons_layout)
        self.tab_lyrics = QWidget(self)
        lyrics_layout = QVBoxLayout(self.tab_lyrics)
        self.lyric_segment = SegmentedWidget(self)
        self.lyric_segment.addItem('static', tr('Normal (Estática)'))
        self.lyric_segment.addItem('sync', tr('Sincronizada (LRC)'))
        self.lyric_stack = QStackedWidget(self)
        self.te_lyrics_static = TextEdit(self)
        self.te_lyrics_static.setPlaceholderText(tr("Pega las letras estáticas aquí..."))
        self.te_lyrics_sync = TextEdit(self)
        self.te_lyrics_sync.setPlaceholderText(tr("Pega las letras con tiempos [00:15.30] LRC aquí..."))
        self.lyric_stack.addWidget(self.te_lyrics_static)
        self.lyric_stack.addWidget(self.te_lyrics_sync)
        self.lyric_segment.currentItemChanged.connect(
            lambda k: self.lyric_stack.setCurrentIndex(0 if k == 'static' else 1)
        )
        self.lyric_segment.setCurrentItem('static')
        lyrics_layout.addWidget(self.lyric_segment, 0, Qt.AlignmentFlag.AlignHCenter)
        lyrics_layout.addWidget(self.lyric_stack)
        self.tab_props = QWidget(self)
        props_main_layout = QHBoxLayout(self.tab_props)
        col1_layout = QFormLayout()
        col1_layout.setSpacing(10)
        col2_layout = QFormLayout()
        col2_layout.setSpacing(10)
        self.lbl_format = BodyLabel(tr("-"), self)
        self.lbl_tag_ver = BodyLabel(tr("ID3 / Vorbis"), self)
        self.lbl_size = BodyLabel(tr("-"), self)
        self.lbl_duration = BodyLabel(tr("-"), self)
        self.lbl_added = BodyLabel(tr("-"), self)
        self.lbl_modified = BodyLabel(tr("-"), self)
        self.lbl_last_played = BodyLabel(tr("-"), self)
        self.lbl_play_count = BodyLabel(tr("-"), self)
        self.lbl_skip_count = BodyLabel(tr("0"), self)
        self.lbl_encoder = BodyLabel(tr("Desconocido"), self)
        self.lbl_channels = BodyLabel(tr("-"), self)
        self.lbl_bitrate = BodyLabel(tr("-"), self)
        self.lbl_sample = BodyLabel(tr("-"), self)
        self.lbl_rg = BodyLabel(tr("-"), self)
        col1_layout.addRow(tr("Tipo:"), self.lbl_format)
        col1_layout.addRow(tr("Versión etiqueta:"), self.lbl_tag_ver)
        col1_layout.addRow(tr("Tamaño:"), self.lbl_size)
        col1_layout.addRow(tr("Duración:"), self.lbl_duration)
        col1_layout.addRow(tr("Añadido:"), self.lbl_added)
        col1_layout.addRow(tr("Modificado:"), self.lbl_modified)
        col1_layout.addRow(tr("Última vez:"), self.lbl_last_played)
        col1_layout.addRow(tr("Reproducciones:"), self.lbl_play_count)
        col1_layout.addRow(tr("Saltos:"), self.lbl_skip_count)
        col2_layout.addRow(tr("Codificador:"), self.lbl_encoder)
        col2_layout.addRow(tr("Canales:"), self.lbl_channels)
        col2_layout.addRow(tr("Tasa bits:"), self.lbl_bitrate)
        col2_layout.addRow(tr("Frecuencia:"), self.lbl_sample)
        col2_layout.addRow(tr("ReplayGain:"), self.lbl_rg)
        props_main_layout.addLayout(col1_layout)
        props_main_layout.addLayout(col2_layout)
        self.addSubInterface(self.tab_general, "general", tr("General"))
        self.addSubInterface(self.tab_artwork, "artwork", tr("Carátula"))
        self.addSubInterface(self.tab_lyrics, "lyrics", tr("Letras"))
        self.addSubInterface(self.tab_props, "props", tr("Archivo"))
        self.viewLayout.addWidget(self.pivot)
        self.viewLayout.addWidget(self.stacked_widget)
        self.stacked_widget.setFixedHeight(280)
        self.pivot.setCurrentItem("general")
    def addSubInterface(self, widget, objectName, text):
        widget.setObjectName(objectName)
        self.stacked_widget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stacked_widget.setCurrentWidget(widget)
        )
    def _populate_data(self):
        t = self.track
        max_label_width = 450
        title_metrics = self.lbl_title.fontMetrics()
        elided_title = title_metrics.elidedText(t.title, Qt.TextElideMode.ElideRight, max_label_width)
        self.lbl_title.setText(elided_title)
        self.lbl_title.setToolTip(t.title)
        artist_metrics = self.lbl_artist.fontMetrics()
        elided_artist = artist_metrics.elidedText(t.artist, Qt.TextElideMode.ElideRight, max_label_width)
        self.lbl_artist.setText(elided_artist)
        self.lbl_artist.setToolTip(t.artist)
        self.le_title.setText(t.title)
        self.le_artist.setText(t.artist)
        self.le_album.setText(t.album)
        self.le_year.setText(t.year if t.year != "Desconocido" else "")
        self.le_genre.setText(t.genre if t.genre != "Desconocido" else "")
        self._props_cache = {}
        self.le_albumartist.setPlaceholderText(tr("Cargando..."))
        self.le_composer.setPlaceholderText(tr("Cargando..."))
        if not hasattr(self, '_loader_workers'):
            self._loader_workers = []
        worker = MetadataLoaderWorker(t.filepath, parent=self)
        worker.finished_load.connect(self._on_properties_loaded)
        worker.finished.connect(lambda w=worker: self._loader_workers.remove(w) if w in self._loader_workers else None)
        self._loader_workers.append(worker)
        worker.start()
        self._update_cover_preview(t.cover_path)
    def _on_properties_loaded(self, props):
        self._props_cache = props
        self.le_albumartist.setPlaceholderText("")
        self.le_composer.setPlaceholderText("")
        self.le_albumartist.setText(props.get('albumartist', ''))
        self.le_composer.setText(props.get('composer', ''))
        self.le_tracknum.setText(props.get('tracknumber', ''))
        self.te_lyrics_static.setText(props.get('lyrics_static', ''))
        self.te_lyrics_sync.setText(props.get('lyrics_sync', ''))
        if props:
            self.lbl_format.setText(props.get('format', 'MPEG archivo de audio'))
            self.lbl_size.setText(f"{props.get('size_mb', 0)} MB")
            dur = getattr(self.track, 'duration', 0)
            if dur > 0:
                mins = int((dur / 1000) // 60)
                secs = int((dur / 1000) % 60)
                self.lbl_duration.setText(f"{mins}:{secs:02d}")
            import datetime
            def format_ts(ts):
                if not ts: return "Desconocido"
                return datetime.datetime.fromtimestamp(ts).strftime('%d/%m/%Y %H:%M')
            self.lbl_added.setText(format_ts(getattr(self.track, 'ctime', 0)))
            self.lbl_modified.setText(format_ts(getattr(self.track, 'mtime', 0)))
            self.lbl_last_played.setText(format_ts(getattr(self.track, 'last_played', 0)))
            self.lbl_play_count.setText(str(getattr(self.track, 'play_count', 0)))
            chan = props.get('channels', 2)
            self.lbl_channels.setText(tr("Estéreo") if chan == 2 else tr("Mono") if chan == 1 else str(chan))
            self.lbl_bitrate.setText(f"{props.get('bitrate', 0) // 1000} kbps")
            self.lbl_sample.setText(f"{props.get('sample_rate', 0)} Hz")
            self.lbl_encoder.setText(props.get('encoder', 'Desconocido'))
            self.lbl_tag_ver.setText(props.get('tag_ver', 'Desconocido'))
            self.lbl_rg.setText(props.get('replaygain', 'No'))
    def _update_cover_preview(self, path):
        if path and os.path.exists(path):
            original = QPixmap(path)
            if not original.isNull():
                pixmap = original.scaled(
                    100, 100, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
                )
                self.cover_label.setPixmap(pixmap)
                zone_pixmap = original.scaled(
                    180, 180, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
                )
                self.drop_zone.lbl_icon.hide()
                self.drop_zone.lbl_text.hide()
                target = QPixmap(180, 180)
                target.fill(Qt.GlobalColor.transparent)
                painter = QPainter(target)
                if painter.isActive():
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    path_clipper = QPainterPath()
                    path_clipper.addRoundedRect(0, 0, 180, 180, 12, 12)
                    painter.setClipPath(path_clipper)
                    painter.drawPixmap(0, 0, zone_pixmap)
                    painter.end()
                self.drop_zone.lbl_image.setPixmap(target)
                self.drop_zone.lbl_image.show()
                self.drop_zone.setStyleSheet("""
                    #dropZone {
                        background: transparent;
                        border: none;
                    }
                """)
                return
        self.cover_label.setPixmap(FIF.ALBUM.icon(color="white").pixmap(100, 100))
    def _on_image_dropped(self, path):
        self._new_cover_path = path
        self._update_cover_preview(path)
        self.btn_reset_art.show()
    def _reset_artwork(self):
        self._new_cover_path = None
        self.btn_reset_art.hide()
        self.drop_zone.setStyleSheet("""
            #dropZone {
                background: rgba(255, 255, 255, 0.05);
                border: 2px dashed rgba(255, 255, 255, 0.2);
                border-radius: 12px;
            }
        """)
        self.drop_zone.lbl_icon.show()
        self.drop_zone.lbl_text.show()
        self.drop_zone.lbl_image.hide()
        self._update_cover_preview(self._original_cover)
    def accept(self):
        changed = {}
        props = self._props_cache
        if self.le_title.text() != self.track.title: changed['title'] = self.le_title.text()
        if self.le_artist.text() != self.track.artist: changed['artist'] = self.le_artist.text()
        if self.le_album.text() != self.track.album: changed['album'] = self.le_album.text()
        if self.le_year.text() != self.track.year and self.le_year.text() != "": changed['year'] = self.le_year.text()
        if self.le_genre.text() != self.track.genre and self.le_genre.text() != "": changed['genre'] = self.le_genre.text()
        if self.le_albumartist.text() != props.get('albumartist', ''): changed['albumartist'] = self.le_albumartist.text()
        if self.le_composer.text() != props.get('composer', ''): changed['composer'] = self.le_composer.text()
        if self.le_tracknum.text() != props.get('tracknumber', ''): changed['tracknumber'] = self.le_tracknum.text()
        lyrics_static = self.te_lyrics_static.toPlainText()
        if lyrics_static != props.get('lyrics_static', ''): changed['lyrics_static'] = lyrics_static
        lyrics_sync = self.te_lyrics_sync.toPlainText()
        if lyrics_sync != props.get('lyrics_sync', ''): changed['lyrics_sync'] = lyrics_sync
        if changed or self._new_cover_path:
            self.metadata_saved.emit(changed, self._new_cover_path)
        super().accept()
    def _open_metadata_search(self):
        from UI.dialogs.metadata_search_dialog import MetadataSearchDialog
        query_parts = []
        if self.track.title and self.track.title != tr("Desconocido"):
            query_parts.append(self.track.title)
        if self.track.artist and self.track.artist != tr("Desconocido"):
            query_parts.append(self.track.artist)
        default_query = " ".join(query_parts)
        if not default_query.strip():
            default_query = os.path.splitext(os.path.basename(self.track.filepath))[0]
        dialog = MetadataSearchDialog(default_query, self)
        dialog.metadata_selected.connect(self._on_metadata_selected_from_search)
        dialog.exec()
    def _on_metadata_selected_from_search(self, metadata, cover_path):
        if 'title' in metadata: self.le_title.setText(metadata['title'])
        if 'artist' in metadata: self.le_artist.setText(metadata['artist'])
        if 'album' in metadata: self.le_album.setText(metadata['album'])
        if 'albumartist' in metadata: self.le_albumartist.setText(metadata['albumartist'])
        if 'year' in metadata: self.le_year.setText(metadata['year'])
        if 'genre' in metadata: self.le_genre.setText(metadata['genre'])
        if 'tracknumber' in metadata: self.le_tracknum.setText(metadata['tracknumber'])
        if cover_path:
            self._new_cover_path = cover_path
            self._update_cover_preview(cover_path)
            self.btn_reset_art.show()