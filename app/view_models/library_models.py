from PyQt6.QtCore import Qt, QAbstractListModel, QSortFilterProxyModel, QModelIndex
class TrackListModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tracks = []
        self.is_grid = False
    def rowCount(self, parent=QModelIndex()):
        return len(self.tracks)
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        track = self.tracks[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return "" if self.is_grid else f"{track.title} - {track.artist}"
        elif role == Qt.ItemDataRole.UserRole:
            return track
        elif role == Qt.ItemDataRole.DecorationRole:
            if self.parent() and hasattr(self.parent(), 'image_cache'):
                size = 160 if self.is_grid else 65
                return self.parent().image_cache.get_cached_icon(track, size)
            return None
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter if self.is_grid else (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        elif role == Qt.ItemDataRole.UserRole + 2:
            if self.parent() and hasattr(self.parent(), 'image_cache') and hasattr(track, 'cover_path'):
                return self.parent().image_cache.get_image_opacity(track.cover_path)
            return 1.0
        return None
    def add_tracks(self, new_tracks):
        self.beginInsertRows(QModelIndex(), len(self.tracks), len(self.tracks) + len(new_tracks) - 1)
        self.tracks.extend(new_tracks)
        self.endInsertRows()
    def set_tracks(self, tracks):
        self.beginResetModel()
        self.tracks = tracks
        self.endResetModel()
class QueueListModel(TrackListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_index = -1
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        track = self.tracks[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return ""
        elif role == Qt.ItemDataRole.UserRole:
            return track
        return None
    def update_current_index(self, index):
        if self.current_index == index:
            return
        old_index = self.current_index
        self.current_index = index
        if old_index >= 0 and old_index < len(self.tracks):
            idx = self.index(old_index, 0)
            self.dataChanged.emit(idx, idx)
        if self.current_index >= 0 and self.current_index < len(self.tracks):
            idx = self.index(self.current_index, 0)
            self.dataChanged.emit(idx, idx)
    def supportedDropActions(self):
        return Qt.DropAction.MoveAction
    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        else:
            return default_flags | Qt.ItemFlag.ItemIsDropEnabled
    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild):
        if sourceRow == destinationChild or sourceRow == destinationChild - 1:
            return False
        old_idx = self.current_index
        if old_idx >= 0:
            if sourceRow <= old_idx < sourceRow + count:
                dest = destinationChild
                if sourceRow < destinationChild:
                    dest -= count
                self.current_index = dest + (old_idx - sourceRow)
            else:
                new_idx = old_idx
                if sourceRow < old_idx:
                    new_idx -= count
                dest = destinationChild
                if sourceRow < destinationChild:
                    dest -= count
                if dest <= new_idx:
                    new_idx += count
                self.current_index = new_idx
        self.beginMoveRows(sourceParent, sourceRow, sourceRow + count - 1, destinationParent, destinationChild)
        items_to_move = self.tracks[sourceRow:sourceRow+count]
        del self.tracks[sourceRow:sourceRow+count]
        if sourceRow < destinationChild:
            destinationChild -= count
        for i, item in enumerate(items_to_move):
            self.tracks.insert(destinationChild + i, item)
        self.endMoveRows()
        return True
class TrackProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        track = self.sourceModel().tracks[source_row]
        query = self.filterRegularExpression().pattern().lower()
        if not query:
            return True
        return query in track.title.lower() or query in track.artist.lower() or query in track.album.lower()
class GroupListModel(QAbstractListModel):
    def __init__(self, parent=None, is_artist=False):
        super().__init__(parent)
        self.items = []                                                                
        self.is_artist = is_artist
    def rowCount(self, parent=QModelIndex()):
        return len(self.items)
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        name, track, custom_cover = self.items[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return ""
        elif role == Qt.ItemDataRole.UserRole:
            return name
        elif role == Qt.ItemDataRole.UserRole + 1:
            return track
        elif role == Qt.ItemDataRole.DecorationRole:
            if self.parent() and hasattr(self.parent(), 'image_cache'):
                if self.is_artist and custom_cover:
                    class FakeTrack: pass
                    ft = FakeTrack()
                    ft.cover_path = custom_cover
                    from qfluentwidgets import FluentIcon as FIF
                    return self.parent().image_cache.get_cached_icon(ft, 160, radius=80, fallback_icon=FIF.PEOPLE)
                else:
                    radius = 80 if self.is_artist else 8
                    from qfluentwidgets import FluentIcon as FIF
                    fallback = FIF.PEOPLE if self.is_artist else FIF.ALBUM
                    return self.parent().image_cache.get_cached_icon(track, 160, radius=radius, fallback_icon=fallback)
            return None
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        elif role == Qt.ItemDataRole.UserRole + 2:
            if self.parent() and hasattr(self.parent(), 'image_cache'):
                if self.is_artist and custom_cover:
                    return self.parent().image_cache.get_image_opacity(custom_cover)
                elif track and hasattr(track, 'cover_path'):
                    return self.parent().image_cache.get_image_opacity(track.cover_path)
            return 1.0
        return None
    def set_items(self, items):
        self.beginResetModel()
        self.items = items
        self.endResetModel()
class GroupProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        name, _, _ = self.sourceModel().items[source_row]
        query = self.filterRegularExpression().pattern().lower()
        return query in name.lower()