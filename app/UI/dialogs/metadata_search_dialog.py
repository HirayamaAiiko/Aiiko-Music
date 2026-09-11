import os
import tempfile
import urllib.parse
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QObject, QByteArray
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QListWidget, QListWidgetItem, QSizePolicy)
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from qfluentwidgets import (MessageBoxBase, LineEdit, PushButton, PrimaryPushButton,
                             IndeterminateProgressRing, CaptionLabel, BodyLabel, SubtitleLabel,
                             FluentIcon as FIF, SmoothScrollArea)
import json
from core.language_manager import tr
class UrlImageLoader(QObject):
    finished = pyqtSignal(QPixmap)
    def __init__(self, url, manager, parent=None):
        super().__init__(parent)
        self.url = url
        self.manager = manager
        self.reply = None
    def start(self):
        self.reply = self.manager.get(QNetworkRequest(QUrl(self.url)))
        self.reply.finished.connect(self._on_finished)
    def _on_finished(self):
        if self.reply and self.reply.error() == QNetworkReply.NetworkError.NoError:
            data = self.reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                self.finished.emit(pixmap)
                self.reply.deleteLater()
                self.reply = None
                return
        self.finished.emit(QPixmap())
        if self.reply:
            self.reply.deleteLater()
            self.reply = None
class DeezerResultWidget(QWidget):
    def __init__(self, track_data, manager, parent=None):
        super().__init__(parent)
        self.track_data = track_data
        self.manager = manager
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)
        self.lbl_cover = QLabel(self)
        self.lbl_cover.setFixedSize(50, 50)
        self.lbl_cover.setStyleSheet("border-radius: 6px; background-color: rgba(255,255,255,0.05);")
        layout.addWidget(self.lbl_cover)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_title = BodyLabel(self.track_data.get('title', tr('Desconocido')), self)
        self.lbl_title.setStyleSheet("font-weight: bold;")
        artist_name = self.track_data.get('artist', {}).get('name', tr('Artista Desconocido'))
        album_name = self.track_data.get('album', {}).get('title', tr('Álbum Desconocido'))
        self.lbl_subtitle = CaptionLabel(f"{artist_name} • {album_name}", self)
        self.lbl_subtitle.setStyleSheet("color: gray;")
        info_layout.addWidget(self.lbl_title)
        info_layout.addWidget(self.lbl_subtitle)
        layout.addLayout(info_layout)
        layout.addStretch()
        cover_url = self.track_data.get('album', {}).get('cover_medium')
        if cover_url:
            self.loader = UrlImageLoader(cover_url, self.manager, self)
            self.loader.finished.connect(self._on_cover_loaded)
            self.loader.start()
        else:
            self.lbl_cover.setPixmap(FIF.ALBUM.icon(color="white").pixmap(50, 50))
    def _on_cover_loaded(self, pixmap):
        if not pixmap.isNull():
            scaled = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.lbl_cover.setPixmap(scaled)
        else:
            self.lbl_cover.setPixmap(FIF.ALBUM.icon(color="white").pixmap(50, 50))
class MetadataSearchDialog(MessageBoxBase):
    metadata_selected = pyqtSignal(dict, str)                                                
    def __init__(self, default_query, parent=None):
        super().__init__(parent)
        self.default_query = default_query
        self.selected_metadata = None
        self.temp_cover_path = None
        self.network_manager = QNetworkAccessManager(self)
        self.widget.setMinimumWidth(500)
        self.widget.setMinimumHeight(450)
        self.viewLayout.setSpacing(10)
        self.viewLayout.setContentsMargins(20, 20, 20, 20)
        self._build_search_ui()
        self.yesButton.setText(tr("Aplicar"))
        self.yesButton.setEnabled(False)
        self.cancelButton.setText(tr("Cancelar"))
        self.btn_search.clicked.connect(self._perform_search)
        self.le_search.returnPressed.connect(self._perform_search)
        self.list_results.itemSelectionChanged.connect(self._on_selection_changed)
        self.yesButton.clicked.connect(self._on_apply)
        if self.default_query and self.default_query.strip():
            self.le_search.setText(self.default_query)
            self._perform_search()
    def _build_search_ui(self):
        lbl_title = SubtitleLabel(tr("Buscar Metadatos en Internet"), self)
        self.viewLayout.addWidget(lbl_title)
        search_layout = QHBoxLayout()
        self.le_search = LineEdit(self)
        self.le_search.setPlaceholderText(tr("Introduce el título de la canción o artista..."))
        self.le_search.setClearButtonEnabled(True)
        self.btn_search = PushButton(tr("Buscar"), self)
        self.btn_search.setIcon(FIF.SEARCH)
        search_layout.addWidget(self.le_search)
        search_layout.addWidget(self.btn_search)
        self.viewLayout.addLayout(search_layout)
        self.loader_ring = IndeterminateProgressRing(self)
        self.loader_ring.setVisible(False)
        self.loader_ring.setFixedHeight(40)
        self.viewLayout.addWidget(self.loader_ring, 0, Qt.AlignmentFlag.AlignCenter)
        self.list_results = QListWidget(self)
        self.list_results.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
            QListWidget::item {
                background: transparent;
                border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            }
            QListWidget::item:selected {
                background: rgba(255, 255, 255, 0.08);
                border-radius: 6px;
            }
        """)
        player = self.parent().parent() if self.parent() and hasattr(self.parent(), 'parent') else None
        if player and hasattr(player, 'apply_smooth_scroll'):
            player.apply_smooth_scroll(self.list_results)
        self.viewLayout.addWidget(self.list_results, 1)
    def _perform_search(self):
        query = self.le_search.text().strip()
        if not query:
            return
        self.list_results.clear()
        self.loader_ring.setVisible(True)
        self.btn_search.setEnabled(False)
        self.yesButton.setEnabled(False)
        url = f"https://api.deezer.com/search?q={urllib.parse.quote(query)}"
        reply = self.network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda: self._on_search_finished(reply))
    def _on_search_finished(self, reply):
        self.loader_ring.setVisible(False)
        self.btn_search.setEnabled(True)
        if reply.error() != QNetworkReply.NetworkError.NoError:
            reply.deleteLater()
            return
        try:
            data = json.loads(str(reply.readAll().data(), encoding='utf-8'))
            tracks = data.get('data', [])
            for track in tracks:
                item = QListWidgetItem(self.list_results)
                item.setData(Qt.ItemDataRole.UserRole, track)
                widget = DeezerResultWidget(track, self.network_manager, self)
                item.setSizeHint(widget.sizeHint())
                self.list_results.setItemWidget(item, widget)
            if not tracks:
                empty_item = QListWidgetItem(self.list_results)
                empty_label = BodyLabel(tr("No se encontraron resultados."), self)
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setStyleSheet("padding: 20px; color: gray;")
                empty_item.setSizeHint(empty_label.sizeHint())
                self.list_results.setItemWidget(empty_item, empty_label)
        except Exception as e:
            print(f"Error procesando búsqueda de Deezer: {e}")
        reply.deleteLater()
    def _on_selection_changed(self):
        selected = self.list_results.selectedItems()
        if selected:
            data = selected[0].data(Qt.ItemDataRole.UserRole)
            self.yesButton.setEnabled(data is not None)
        else:
            self.yesButton.setEnabled(False)
    def _on_apply(self):
        selected = self.list_results.selectedItems()
        if not selected:
            return
        track_data = selected[0].data(Qt.ItemDataRole.UserRole)
        if not track_data:
            return
        self.loader_ring.setVisible(True)
        self.list_results.setEnabled(False)
        self.yesButton.setEnabled(False)
        track_id = track_data.get('id')
        album_id = track_data.get('album', {}).get('id')
        self._fetched_data = {
            'track': track_data,
            'details': None,
            'album_details': None
        }
        self._fetch_track_details(track_id, album_id)
    def _fetch_track_details(self, track_id, album_id):
        url = f"https://api.deezer.com/track/{track_id}"
        reply = self.network_manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda: self._on_track_details_finished(reply, album_id))
    def _on_track_details_finished(self, reply, album_id):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            try:
                self._fetched_data['details'] = json.loads(str(reply.readAll().data(), encoding='utf-8'))
            except:
                pass
        reply.deleteLater()
        if album_id:
            url = f"https://api.deezer.com/album/{album_id}"
            reply_album = self.network_manager.get(QNetworkRequest(QUrl(url)))
            reply_album.finished.connect(lambda: self._on_album_details_finished(reply_album))
        else:
            self._finalize_and_close()
    def _on_album_details_finished(self, reply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            try:
                self._fetched_data['album_details'] = json.loads(str(reply.readAll().data(), encoding='utf-8'))
            except:
                pass
        reply.deleteLater()
        self._download_cover()
    def _download_cover(self):
        album_data = self._fetched_data.get('album_details') or self._fetched_data['track'].get('album', {})
        cover_url = album_data.get('cover_xl') or album_data.get('cover_big') or album_data.get('cover_medium')
        if cover_url:
            reply = self.network_manager.get(QNetworkRequest(QUrl(cover_url)))
            reply.finished.connect(lambda: self._on_cover_download_finished(reply))
        else:
            self._finalize_and_close()
    def _on_cover_download_finished(self, reply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            try:
                temp_dir = tempfile.gettempdir()
                self.temp_cover_path = os.path.join(temp_dir, "temp_online_cover.jpg")
                with open(self.temp_cover_path, 'wb') as f:
                    f.write(reply.readAll().data())
            except Exception as e:
                print(f"Error guardando carátula temporal: {e}")
                self.temp_cover_path = None
        reply.deleteLater()
        self._finalize_and_close()
    def _finalize_and_close(self):
        self.loader_ring.setVisible(False)
        track = self._fetched_data['track']
        details = self._fetched_data.get('details') or {}
        album_details = self._fetched_data.get('album_details') or {}
        year = ""
        release_date = details.get('release_date') or album_details.get('release_date')
        if release_date and len(release_date) >= 4:
            year = release_date[:4]
        genre = ""
        genres_data = album_details.get('genres', {}).get('data', [])
        if genres_data:
            genre = genres_data[0].get('name', '')
        self.selected_metadata = {
            'title': details.get('title') or track.get('title'),
            'artist': details.get('artist', {}).get('name') or track.get('artist', {}).get('name'),
            'album': details.get('album', {}).get('title') or track.get('album', {}).get('title'),
            'albumartist': album_details.get('artist', {}).get('name') or details.get('artist', {}).get('name') or track.get('artist', {}).get('name'),
            'year': year,
            'genre': genre,
            'tracknumber': str(details.get('track_position', ''))
        }
        self.metadata_selected.emit(self.selected_metadata, self.temp_cover_path or "")
        self.accept()