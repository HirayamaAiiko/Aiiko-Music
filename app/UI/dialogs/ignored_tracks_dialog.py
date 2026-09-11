import os
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QListWidgetItem, QAbstractItemView
from qfluentwidgets import MessageBoxBase, SubtitleLabel, BodyLabel, IndeterminateProgressRing, CheckBox, ListWidget
from models import Track
from database import remove_ignored_track, save_batch
from core.notification_manager import notify
from core.language_manager import tr
class RestoreWorker(QThread):
    track_ready = pyqtSignal(object)
    finished = pyqtSignal(int)
    def __init__(self, paths, parent=None):
        super().__init__(parent)
        self.paths = paths
        self.running = True
    def run(self):
        restored_count = 0
        for path in self.paths:
            if not self.running: break
            remove_ignored_track(path)
            if os.path.exists(path):
                try:
                    track = Track(path, lazy=False)
                    self.track_ready.emit(track)
                except Exception as e:
                    import logging
                    logging.error(f"Error cargando track restaurado {path}: {e}")
            restored_count += 1
        self.finished.emit(restored_count)
class IgnoredTracksDialog(MessageBoxBase):
    def __init__(self, ignored_paths, player, parent=None):
        super().__init__(parent)
        self.ignored_paths = ignored_paths
        self.player = player
        self.worker = None
        self.titleLabel = SubtitleLabel(tr("Restaurar Canciones Ignoradas"), self)
        self.infoLabel = BodyLabel(tr("Selecciona las canciones que deseas volver a incluir en tu biblioteca:"), self)
        self.chk_select_all = CheckBox(tr("Seleccionar Todo"), self)
        self.chk_select_all.stateChanged.connect(self._on_select_all_changed)
        self.list_widget = ListWidget(self)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        for path in sorted(self.ignored_paths):
            item = QListWidgetItem(os.path.basename(path))
            item.setToolTip(path)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)
        self.loader_ring = IndeterminateProgressRing(self)
        self.loader_ring.setVisible(False)
        self.loader_ring.setFixedHeight(40)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.infoLabel)
        self.viewLayout.addSpacing(4)
        self.viewLayout.addWidget(self.chk_select_all)
        self.viewLayout.addWidget(self.list_widget)
        self.viewLayout.addWidget(self.loader_ring, 0, Qt.AlignmentFlag.AlignCenter)
        self.widget.setMinimumWidth(600)
        self.widget.setMinimumHeight(500)
        self.yesButton.setText(tr("Restaurar Seleccionadas"))
        self.cancelButton.setText(tr("Cancelar"))
        self.yesButton.clicked.disconnect()
        self.yesButton.clicked.connect(self._on_restore_clicked)
    def _on_select_all_changed(self, state):
        check_state = Qt.CheckState.Checked if state == 2 else Qt.CheckState.Unchecked
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(check_state)
    def _on_restore_clicked(self):
        paths_to_restore = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                paths_to_restore.append(item.data(Qt.ItemDataRole.UserRole))
        if not paths_to_restore:
            self.reject()
            return
        self.list_widget.setEnabled(False)
        self.yesButton.setEnabled(False)
        self.cancelButton.setEnabled(False)
        self.loader_ring.setVisible(True)
        self.restored_tracks_cache = []
        self.worker = RestoreWorker(paths_to_restore, self)
        self.worker.track_ready.connect(self._on_track_ready)
        self.worker.finished.connect(self._on_restore_finished)
        self.worker.start()
    def reject(self):
        if self.worker and self.worker.isRunning():
            self.worker.running = False
            self.worker.wait()
        super().reject()
    def _on_track_ready(self, track):
        self.restored_tracks_cache.append(track)
    def _on_restore_finished(self, count):
        if self.restored_tracks_cache:
            save_batch(self.restored_tracks_cache)
            for t in self.restored_tracks_cache:
                self.player.library_sync_controller.on_watcher_new_track(t)
        if count > 0:
            notify.success(tr("Restauradas"), tr("Se restauraron {count} canciones a la biblioteca al instante.").format(count=count))
        self.accept()
