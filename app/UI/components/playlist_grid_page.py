import re
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListView, QAbstractItemView, QPushButton, QStackedWidget
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from qfluentwidgets import TitleLabel, SearchLineEdit, ComboBox, TransparentToolButton, FluentIcon as FIF, RoundMenu, Action, SubtitleLabel, BodyLabel, PushButton
from delegates.grid_delegates import PlaylistGridDelegate
from view_models.playlist_models import PlaylistGridModel
from widgets import ResponsiveGridHelper, AspectRatioLabel
from settings_manager import settings
from core.notification_manager import notify
from UI.dialogs.playlist_edit_dialog import PlaylistEditDialog
from core.language_manager import tr
class PlaylistGridPage(QWidget):
    open_playlist = pyqtSignal(str, list)
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self._build_ui()
    def _build_ui(self):
        grid_layout = QVBoxLayout(self)
        grid_layout.setContentsMargins(30, 10, 30, 0)
        header = QHBoxLayout()
        header.addWidget(TitleLabel(tr("Mis Playlists")))
        header.addStretch()
        self.grid_search = SearchLineEdit()
        from PyQt6.QtCore import QSize
        self.grid_search.searchButton.setIconSize(QSize(14, 14))
        self.grid_search.clearButton.setIconSize(QSize(14, 14))
        self.grid_search.setPlaceholderText(tr("Buscar playlist..."))
        self.grid_search.setFixedWidth(220)
        self.grid_search.textChanged.connect(self._filter_grid)
        header.addWidget(self.grid_search)
        from UI.components.sort_filter_button import SortFilterButton
        self.sort_combo = SortFilterButton([tr("A-Z"), tr("Z-A"), tr("Más canciones"), tr("Menos canciones")])
        sort_configs = settings.get('sort_configs', {})
        saved_idx = sort_configs.get('playlists', 0)
        if 0 <= saved_idx < self.sort_combo.count():
            self.sort_combo.setCurrentIndex(saved_idx)
        self.sort_combo.currentIndexChanged.connect(self._sort_grid)
        header.addWidget(self.sort_combo)
        self.btn_new_pl = TransparentToolButton()
        self.btn_new_pl.setIcon(FIF.ADD)
        self.btn_new_pl.setToolTip(tr("Nueva Playlist"))
        self.btn_new_pl.clicked.connect(self.player.app_controller.create_new_playlist)
        header.addWidget(self.btn_new_pl)
        self.btn_delete_group = PushButton(FIF.DELETE, tr(" Eliminar Seleccionadas"))
        self.btn_delete_group.setToolTip(tr("Eliminar playlists seleccionadas"))
        self.btn_delete_group.clicked.connect(self._delete_selected_playlists)
        self.btn_delete_group.hide()
        header.addWidget(self.btn_delete_group)
        grid_layout.addLayout(header)
        self.stacked = QStackedWidget()
        self._grid_model = PlaylistGridModel(self.player, self)
        self.grid_view = QListView()
        self.grid_view.setObjectName("GridList")
        self.grid_view.setModel(self._grid_model)
        self.grid_view.setViewMode(QListView.ViewMode.IconMode)
        self.grid_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.grid_view.setIconSize(QSize(160, 160))
        self.grid_view.setGridSize(QSize(190, 265))
        self.grid_view.setUniformItemSizes(True)
        self.grid_view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.grid_view.verticalScrollBar().setSingleStep(15)
        self.grid_view.setViewportMargins(0, 15, 0, 0)
        self.grid_view.setStyleSheet("QListView::item { background-color: transparent; border: none; }")
        self._grid_delegate = PlaylistGridDelegate(self.grid_view, player=self.player)
        self.grid_view.setItemDelegate(self._grid_delegate)
        self.grid_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.grid_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.grid_view.customContextMenuRequested.connect(self._show_grid_context_menu)
        self.grid_view.selectionModel().selectionChanged.connect(self._on_grid_selection_changed)
        self.grid_view.clicked.connect(self._on_grid_clicked)
        self._grid_delegate.play_clicked.connect(self._quick_play_playlist)
        self.player.apply_smooth_scroll(self.grid_view, step=250)
        self._grid_helper = ResponsiveGridHelper(self.grid_view, parent=self)
        self.stacked.addWidget(self.grid_view)
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.addStretch()
        empty_icon = AspectRatioLabel()
        empty_icon.setFixedSize(120, 120)
        import os
        from PyQt6.QtGui import QPixmap, QPainter, QColor
        svg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "resources", "app", "logo_full.svg")
        if os.path.exists(svg_path):
            from PyQt6.QtSvg import QSvgRenderer
            icon_pixmap = QPixmap(120, 120)
            icon_pixmap.fill(Qt.GlobalColor.transparent)
            p_icon = QPainter(icon_pixmap)
            p_icon.setRenderHint(QPainter.RenderHint.Antialiasing)
            p_icon.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            renderer = QSvgRenderer(svg_path)
            renderer.render(p_icon)
            p_icon.end()
            empty_icon.setPixmap(icon_pixmap)
        empty_layout.addWidget(empty_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        empty_title = SubtitleLabel(tr("Aún no tienes playlists"))
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)
        empty_desc = BodyLabel(tr("Haz clic en el botón '+' para crear una nueva playlist\ny organizar tu música favorita."))
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_desc.setStyleSheet("color: #888888;")
        empty_layout.addWidget(empty_desc)
        empty_layout.addStretch()
        self.stacked.addWidget(self.empty_widget)
        grid_layout.addWidget(self.stacked)
        self._cache_update_timer = QTimer(self)
        self._cache_update_timer.setSingleShot(True)
        self._cache_update_timer.setInterval(100)
        self._cache_update_timer.timeout.connect(self._do_update_grid)
        self.player.image_cache.cache_updated.connect(self._on_cache_updated)
    def _on_cache_updated(self):
        if self.isVisible() and not self._cache_update_timer.isActive():
            self._cache_update_timer.start()
    def _do_update_grid(self):
        if self.isVisible():
            self.grid_view.viewport().update()
    def load_playlists(self, playlists_dict):
        if not playlists_dict:
            self.stacked.setCurrentWidget(self.empty_widget)
            self.grid_search.setDisabled(True)
            self.sort_combo.setDisabled(True)
            self.btn_delete_group.hide()
        else:
            self.stacked.setCurrentWidget(self.grid_view)
            self.grid_search.setDisabled(False)
            self.sort_combo.setDisabled(False)
        self._grid_model.set_playlists(playlists_dict, self.player.library)
        self._grid_helper.force_recalculate()
    def _filter_grid(self, text):
        text = text.lower()
        for row in range(self._grid_model.rowCount()):
            index = self._grid_model.index(row, 0)
            data = index.data(Qt.ItemDataRole.UserRole)
            match = not text or text in data.get('name', '').lower()
            self.grid_view.setRowHidden(row, not match)
    def _sort_grid(self, index):
        sort_configs = settings.get('sort_configs', {})
        sort_configs['playlists'] = index
        settings.set('sort_configs', sort_configs)
        settings.save()
        items = self._grid_model._items
        if not items: return
        self._grid_model.layoutAboutToBeChanged.emit()
        if index == 0:         
            items.sort(key=lambda d: d['name'].lower())
        elif index == 1:       
            items.sort(key=lambda d: d['name'].lower(), reverse=True)
        elif index == 2:                 
            items.sort(key=lambda d: d['count'], reverse=True)
        elif index == 3:                   
            items.sort(key=lambda d: d['count'])
        self._grid_model.layoutChanged.emit()
    def _quick_play_playlist(self, playlist_name):
        import time
        self._last_play_click_time = time.time()
        playlists = settings.get('playlists', {})
        filepaths = playlists.get(playlist_name, [])
        if not filepaths: return
        tracks = [t for fp in filepaths for t in self.player.library if t.filepath == fp]
        if tracks:
            self.player.queue_controller.play_specific_track_global(tracks[0], tracks)
    def _on_grid_clicked(self, index):
        from PyQt6.QtWidgets import QApplication
        modifiers = QApplication.keyboardModifiers()
        if modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            return
        if len(self.grid_view.selectionModel().selectedIndexes()) > 1:
            return
        import time
        if hasattr(self, '_last_play_click_time') and time.time() - self._last_play_click_time < 0.2:
            return
        data = index.data(Qt.ItemDataRole.UserRole)
        if data:
            self.open_playlist.emit(data['name'], data['filepaths'])
    def _on_grid_selection_changed(self):
        selected = self.grid_view.selectionModel().selectedIndexes()
        if len(selected) > 1:
            self.btn_delete_group.show()
        else:
            self.btn_delete_group.hide()
    def _delete_selected_playlists(self):
        selected = self.grid_view.selectionModel().selectedIndexes()
        if len(selected) < 2: return
        names = [idx.data(Qt.ItemDataRole.UserRole).get('name', '') for idx in selected if idx.data(Qt.ItemDataRole.UserRole)]
        if notify.confirm(tr('Confirmar'), tr('¿Eliminar {count} playlists seleccionadas?').format(count=len(names))):
            playlists = settings.get('playlists', {})
            covers = settings.get('playlist_covers', {})
            for name in names:
                playlists.pop(name, None)
                covers.pop(name, None)
            settings.set('playlists', playlists)
            settings.set('playlist_covers', covers)
            settings.save()
            self.player.library_controller.refresh_playlists_list()
            self.player.library_controller.refresh_artist_related_playlists()
    def _show_grid_context_menu(self, pos):
        index = self.grid_view.indexAt(pos)
        if not index.isValid(): return
        data = index.data(Qt.ItemDataRole.UserRole)
        if not data: return
        selected_indexes = self.grid_view.selectionModel().selectedIndexes()
        global_pos = self.grid_view.viewport().mapToGlobal(pos)
        menu = RoundMenu(parent=self.player)
        if len(selected_indexes) > 1:
            action_del_multi = Action(FIF.DELETE, tr("Eliminar {count} playlists").format(count=len(selected_indexes)), triggered=self._delete_selected_playlists)
            menu.addAction(action_del_multi)
        else:
            playlist_name = data.get('name', '')
            action_edit = Action(FIF.EDIT, tr("Editar Playlist"), triggered=lambda: self._edit_playlist_from_grid(playlist_name))
            menu.addAction(action_edit)
            action_dup = Action(FIF.COPY, tr("Duplicar"), triggered=lambda: self._duplicate_playlist(playlist_name))
            menu.addAction(action_dup)
            menu.addSeparator()
            action_del = Action(FIF.DELETE, tr("Eliminar"), triggered=lambda: self._delete_playlist_from_grid(playlist_name))
            menu.addAction(action_del)
        menu.exec(global_pos)
    def _edit_playlist_from_grid(self, name):
        dlg = PlaylistEditDialog(name, self.player, parent=self.player)
        if dlg.exec():
            new_name = dlg.get_name()
            new_cover_path = dlg.get_cover_path()
            playlists = settings.get('playlists', {})
            covers = settings.get('playlist_covers', {})
            if new_name != name:
                if new_name in playlists:
                    notify.warning(tr("Error"), tr("Ya existe una playlist con ese nombre."))
                    return
                playlists[new_name] = playlists.pop(name)
                if name in covers:
                    covers[new_name] = covers.pop(name)
                settings.set('playlists', playlists)
            if new_cover_path:
                covers[new_name if new_name != name else name] = new_cover_path
            elif new_cover_path is None and dlg.cover_reset:
                key = new_name if new_name != name else name
                covers.pop(key, None)
            settings.set('playlist_covers', covers)
            settings.save()
            self.player.library_controller.refresh_playlists_list()
    def _duplicate_playlist(self, name):
        playlists = settings.get('playlists', {})
        covers = settings.get('playlist_covers', {})
        base_name = name
        m = re.match(r"^(.*) \((\d+)\)$", name)
        if m: base_name = m.group(1)
        new_name = f"{base_name} (1)"
        counter = 1
        while new_name in playlists:
            counter += 1
            new_name = f"{base_name} ({counter})"
        playlists[new_name] = list(playlists.get(name, []))
        if name in covers:
            covers[new_name] = covers[name]
        settings.set('playlists', playlists)
        settings.set('playlist_covers', covers)
        settings.save()
        self.player.library_controller.refresh_playlists_list()
    def _delete_playlist_from_grid(self, name):
        if notify.confirm(tr('Confirmar'), tr('¿Eliminar la playlist "{name}"?').format(name=name)):
            playlists = settings.get('playlists', {})
            if name in playlists:
                del playlists[name]
                settings.set('playlists', playlists)
                covers = settings.get('playlist_covers', {})
                if name in covers:
                    del covers[name]
                    settings.set('playlist_covers', covers)
                settings.save()
                self.player.library_controller.refresh_playlists_list()
                self.player.library_controller.refresh_artist_related_playlists()