from PyQt6.QtCore import QObject, Qt
class SelectionTracker(QObject):
    def __init__(self, list_view):
        super().__init__(list_view)
        self.list_view = list_view
        self.selected_tracks_chronological = []
        selection_model = self.list_view.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)
    def _on_selection_changed(self, selected, deselected):
        for index in deselected.indexes():
            if index.column() != 0: continue
            track = index.data(Qt.ItemDataRole.UserRole)
            if track in self.selected_tracks_chronological:
                self.selected_tracks_chronological.remove(track)
        for index in selected.indexes():
            if index.column() != 0: continue
            track = index.data(Qt.ItemDataRole.UserRole)
            if track and track not in self.selected_tracks_chronological:
                self.selected_tracks_chronological.append(track)
    def get_selected_tracks(self):
        selection_model = self.list_view.selectionModel()
        if not selection_model:
            return []
        valid_tracks = []
        for index in selection_model.selectedIndexes():
            if index.column() == 0:
                track = index.data(Qt.ItemDataRole.UserRole)
                if track:
                    valid_tracks.append(track)
        self.selected_tracks_chronological = [t for t in self.selected_tracks_chronological if t in valid_tracks]
        for t in valid_tracks:
            if t not in self.selected_tracks_chronological:
                self.selected_tracks_chronological.append(t)
        return list(self.selected_tracks_chronological)