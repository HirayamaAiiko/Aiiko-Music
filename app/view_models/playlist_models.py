import os
from PyQt6.QtCore import Qt, QAbstractListModel, QModelIndex, pyqtSignal
from PyQt6.QtGui import QPixmap
from settings_manager import settings
class PlaylistTrackModel(QAbstractListModel):
    tracks_reordered = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks = []
    def rowCount(self, parent=QModelIndex()):
        return len(self._tracks)
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._tracks):
            return None
        if role == Qt.ItemDataRole.UserRole:
            return self._tracks[index.row()]
        return None
    def supportedDropActions(self):
        return Qt.DropAction.MoveAction
    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemFlag.ItemIsDragEnabled
        else:
            return default_flags | Qt.ItemFlag.ItemIsDropEnabled
    def mimeTypes(self):
        return ["application/x-aiiko-playlist-tracks"]
    def mimeData(self, indexes):
        from PyQt6.QtCore import QMimeData
        import json
        mime_data = QMimeData()
        rows = sorted(list(set(i.row() for i in indexes)))
        data = json.dumps(rows).encode('utf-8')
        mime_data.setData("application/x-aiiko-playlist-tracks", data)
        return mime_data
    def dropMimeData(self, data, action, row, column, parent):
        if not data.hasFormat("application/x-aiiko-playlist-tracks"):
            return False
        if action == Qt.DropAction.IgnoreAction:
            return True
        import json
        qbytearray_data = data.data("application/x-aiiko-playlist-tracks")
        raw_data = qbytearray_data.data()
        source_rows = json.loads(raw_data.decode('utf-8'))
        if not source_rows:
            return False
        if row != -1:
            begin_row = row
        elif parent.isValid():
            begin_row = parent.row()
        else:
            begin_row = self.rowCount(QModelIndex())
        tracks_to_move = [self._tracks[r] for r in source_rows]
        offset = sum(1 for r in source_rows if r < begin_row)
        insert_row = begin_row - offset
        self.beginResetModel()
        for r in reversed(source_rows):
            del self._tracks[r]
        for i, track in enumerate(tracks_to_move):
            self._tracks.insert(insert_row + i, track)
        self.endResetModel()
        self.tracks_reordered.emit()
        return True
    def set_tracks(self, tracks):
        self.beginResetModel()
        self._tracks = list(tracks)
        self.endResetModel()
    def tracks(self):
        return self._tracks
class PlaylistGridModel(QAbstractListModel):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self._items = []                                                                     
        self.player = player
    def rowCount(self, parent=QModelIndex()):
        return len(self._items)
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._items):
            return None
        if role == Qt.ItemDataRole.UserRole:
            return self._items[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return ""                                          
        return None
    def set_playlists(self, playlists_dict, library):
        self.beginResetModel()
        self._items = []
        playlist_covers_cfg = settings.get('playlist_covers', {})
        for p_name, filepaths in playlists_dict.items():
            covers = []
            seen_covers = set()
            for fp in reversed(filepaths):
                track = next((t for t in library if t.filepath == fp), None)
                if track and hasattr(track, 'cover_path') and track.cover_path and os.path.exists(track.cover_path):
                    if track.cover_path not in seen_covers:
                        seen_covers.add(track.cover_path)
                        covers.append(track.cover_path)
                    if len(covers) == 4:
                        break
            custom_cover = None
            custom_path = playlist_covers_cfg.get(p_name)
            if custom_path and os.path.exists(custom_path):
                custom_cover = custom_path
            self._items.append({
                'name': p_name,
                'covers': covers,
                'custom_cover': custom_cover,
                'count': len(filepaths),
                'filepaths': filepaths,
            })
        self.endResetModel()
    def items(self):
        return self._items