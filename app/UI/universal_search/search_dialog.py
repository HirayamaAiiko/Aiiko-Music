from PyQt6.QtCore import Qt, QSize, QRect, QEvent, pyqtProperty, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QFontMetrics, QFont
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QListWidget, QListWidgetItem, QApplication, QGraphicsOpacityEffect,
                             QStyledItemDelegate, QStyle, QFrame, QLineEdit)
from qfluentwidgets import FluentIcon as FIF
from utils import get_artists_from_string
from settings_manager import settings
from core.language_manager import tr
from UI.universal_search.components import DarkOverlayWidget, FilterChip
from UI.universal_search.best_result_card import BestResultCard
from UI.universal_search.list_delegate import SpotlightListDelegate
class SpotlightSearchDialog(QWidget):
    def __init__(self, parent=None, player=None):
        super().__init__(parent)
        self.player = player
        self.hide() 
        self.setObjectName("SpotlightOverlay")
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)                                             
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.setInterval(200)                              
        self.resize_timer.timeout.connect(self._on_resize_finished)
        self.dark_overlay = DarkOverlayWidget(self)
        self.container = QWidget(self)
        self.container.setFixedWidth(850)                                    
        self.container.setObjectName("SpotlightContainer")
        self.container.setStyleSheet("""
            QWidget#SpotlightContainer {
                background-color: #121216;
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)
        import theme_manager
        accent_hex = theme_manager.get_current_accent_hex()
        accent_color = QColor(accent_hex)
        accent_color_dim = QColor(accent_hex)
        accent_color_dim.setAlpha(200)
        self.search_icon_label = QLabel()
        self.search_icon_label.setPixmap(FIF.SEARCH.icon(color=accent_color_dim).pixmap(24, 24))
        self.search_input = QLineEdit(self.container)
        self.search_input.setMinimumWidth(500) 
        self.search_input.setPlaceholderText(tr("Buscar canción, artista o álbum..."))
        self.search_input.setStyleSheet("""
            QLineEdit {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                font-size: 22px; 
                font-weight: 400;
                border: none; 
                background: transparent; 
                color: rgba(255, 255, 255, 0.95);
                padding-left: 5px;
            }
        """)
        self.search_input.textChanged.connect(self.filter_tracks)
        self.search_input.returnPressed.connect(self.play_first_or_selected)
        self.search_input.installEventFilter(self)
        search_layout.addWidget(self.search_icon_label)
        search_layout.addWidget(self.search_input, 1)
        self.btn_close = QWidget()
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        close_layout = QHBoxLayout(self.btn_close)
        close_layout.setContentsMargins(0, 0, 0, 0)
        close_layout.setSpacing(8)
        self.x_icon = QLabel()
        self.x_icon.setFixedSize(28, 28)
        self.x_icon.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.06);
                border-radius: 14px;
            }
        """)
        self.x_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.x_icon.setPixmap(FIF.CLOSE.icon(color=QColor(255, 255, 255, 150)).pixmap(12, 12))
        self.esc_badge = QLabel("ESC")
        self.esc_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.esc_badge.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #A064FF;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        close_layout.addWidget(self.x_icon)
        close_layout.addWidget(self.esc_badge)
        self.btn_close.mousePressEvent = lambda e: self.fade_out_and_hide()
        search_layout.addWidget(self.btn_close)
        layout.addLayout(search_layout)
        self.separator = QWidget()
        self.separator.setFixedHeight(2)
        self.separator.setObjectName("SpotlightSeparator")
        self.separator.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #A064FF, stop:0.4 rgba(160, 100, 255, 0.6), stop:1 rgba(255, 255, 255, 0.05));
                border-radius: 1px;
            }
        """)
        layout.addWidget(self.separator)
        self.tabs_container = QWidget(self.container)
        self.tabs_layout = QHBoxLayout(self.tabs_container)
        self.tabs_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs_layout.setSpacing(12)
        self.tabs_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filter_buttons = {}
        filters = [
            ("Canciones", FIF.MUSIC, True),
            ("Álbumes", FIF.ALBUM, False),
            ("Artistas", FIF.PEOPLE, False),
            ("Playlists", FIF.FOLDER, False)
        ]
        import theme_manager as _tm
        _accent_hex = _tm.get_current_accent_hex()
        _accent_qcolor = QColor(_accent_hex)
        _accent_qcolor_active = QColor(_accent_hex)
        _accent_qcolor_active.setAlpha(255)
        for name, icon_enum, is_active in filters:
            btn = FilterChip(name, icon_enum)
            btn.set_active(is_active, _accent_hex)
            self.tabs_layout.addWidget(btn)
            self.filter_buttons[name] = {'widget': btn, 'badge': btn.badge, 'active': is_active}
            btn.clicked.connect(self.set_filter)
        layout.addWidget(self.tabs_container)
        self.tabs_container.hide()
        self.current_filter = "Canciones"
        self.best_result_track = None
        self.results_list = QListWidget(self.container)
        self.results_list.setStyleSheet("""
            QListWidget { 
                background: transparent; 
                border: none; 
                outline: none; 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                font-size: 15px;
            }
            QListWidget::item { 
                border-radius: 8px; 
                color: rgba(255, 255, 255, 0.85);
            }
            QListWidget::item:selected, QListWidget::item:hover { 
                background-color: transparent; 
                color: white;
            }
        """)
        self.results_list.setIconSize(QSize(40, 40))
        self.results_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.spotlight_delegate = SpotlightListDelegate(self.results_list, self.player)
        self.results_list.setItemDelegate(self.spotlight_delegate)
        self.results_list.itemClicked.connect(self.play_selected_track)
        self.results_list.itemActivated.connect(self.play_selected_track)
        if self.player and hasattr(self.player, 'apply_smooth_scroll'):
            self.player.apply_smooth_scroll(self.results_list)
        self.results_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self.show_context_menu)
        if self.player and hasattr(self.player, 'image_cache'):
            self.player.image_cache.cache_updated.connect(self.results_list.viewport().update)
        layout.addWidget(self.results_list)
        self.results_list.hide()
        self.max_results = 20
        self.anim_duration = 150                                     
        self.opacity_effect = QGraphicsOpacityEffect(self.container)
        self.container.setGraphicsEffect(self.opacity_effect)
        self.anim_group = QParallelAnimationGroup(self)
        self.fade_anim = QPropertyAnimation(self.dark_overlay, b"bg_alpha")
        self.fade_anim.setDuration(self.anim_duration)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim_group.addAnimation(self.fade_anim)
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(self.anim_duration)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim_group.addAnimation(self.opacity_anim)
        if self.player:
            self.player.installEventFilter(self)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.bg_label.setGeometry(self.rect())
        self.dark_overlay.setGeometry(self.rect())
        self.center_on_parent()
        if self.isVisible() and hasattr(self, 'resize_timer') and self.player:
            self.resize_timer.start()
    def _on_resize_finished(self):
        if not self.isVisible() or not self.player:
            return
        old_pos = self.pos()
        self.move(-10000, -10000)
        raw_pixmap = self.player.grab()
        self.move(old_pos)
        blurred_pixmap = self._bake_blur(raw_pixmap)
        self.bg_label.setPixmap(blurred_pixmap)
    def _bake_blur(self, pixmap):
        from PyQt6.QtWidgets import QGraphicsScene, QGraphicsBlurEffect
        from PyQt6.QtGui import QPainter, QPixmap
        from PyQt6.QtCore import Qt
        if pixmap.isNull():
            return pixmap
        scene = QGraphicsScene()
        item = scene.addPixmap(pixmap)
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(10)
        blur.setBlurHints(QGraphicsBlurEffect.BlurHint.PerformanceHint)
        item.setGraphicsEffect(blur)
        res = QPixmap(pixmap.size())
        res.fill(Qt.GlobalColor.transparent)
        painter = QPainter(res)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        scene.render(painter)
        painter.end()
        scene.clear()
        return res
    def center_on_parent(self):
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.container.width()) // 2
            y = parent_rect.height() // 5 
            self.container.move(x, y)
    def mousePressEvent(self, event):
        if not self.container.geometry().contains(event.pos()):
            self.fade_out_and_hide()
        super().mousePressEvent(event)
    def eventFilter(self, obj, event):
        if self.player and obj == self.player:
            if event.type() in (QEvent.Type.Move, QEvent.Type.Resize):
                if self.isVisible():
                    self.setGeometry(self.player.rect())
                    self.center_on_parent()
        if obj == self.search_input:
            if event.type() in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
                if event.key() == Qt.Key.Key_Escape:
                    if event.type() == QEvent.Type.ShortcutOverride:
                        event.accept()                                   
                        return True
                    else:
                        self.fade_out_and_hide()
                        return True
        return super().eventFilter(obj, event)
    def show(self):
        if self.isVisible():
            self.fade_out_and_hide()
        else:
            if self.player:
                self.bg_label.setGraphicsEffect(None)                
                raw_pixmap = self.player.grab()
                blurred_pixmap = self._bake_blur(raw_pixmap)
                self.bg_label.setPixmap(blurred_pixmap)
                self.bg_label.setGeometry(self.rect())
                self.dark_overlay.setGeometry(self.rect())
            super().show()
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.fade_out_and_hide()
            return
        elif event.key() == Qt.Key.Key_Down and self.search_input.hasFocus():
            self.results_list.setFocus()
            if self.results_list.currentRow() < 0 and self.results_list.count() > 0:
                self.results_list.setCurrentRow(0)
            return
        elif event.key() == Qt.Key.Key_Up and self.results_list.hasFocus():
            if self.results_list.currentRow() <= 0:
                self.search_input.setFocus()
            return
        if not self.search_input.hasFocus() and (event.text().isprintable() or event.key() == Qt.Key.Key_Backspace):
            self.search_input.setFocus()
            QApplication.sendEvent(self.search_input, event)
            return
        super().keyPressEvent(event)
    def wheelEvent(self, event):
        if hasattr(self, 'results_list') and self.results_list.isVisible():
            QApplication.sendEvent(self.results_list.viewport(), event)
        else:
            super().wheelEvent(event)
    def showEvent(self, event):
        super().showEvent(event)
        import theme_manager
        accent_hex = theme_manager.get_current_accent_hex()
        accent = QColor(accent_hex)
        r, g, b = accent.red(), accent.green(), accent.blue()
        accent_dim = QColor(accent_hex)
        accent_dim.setAlpha(200)
        self.search_icon_label.setPixmap(FIF.SEARCH.icon(color=accent_dim).pixmap(24, 24))
        self.esc_badge.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                color: {accent_hex};
                font-size: 13px;
                font-weight: bold;
            }}
        """)
        self.separator.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent_hex}, stop:0.4 rgba({r},{g},{b},0.6), stop:1 rgba(255,255,255,0.05));
                border-radius: 1px;
            }}
        """)
        self.set_filter(self.current_filter)
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.raise_()
        self.search_input.clear()
        self.filter_tracks("") 
        self.center_on_parent()
        self.container.show()
        self.anim_group.stop()
        self.opacity_effect.setOpacity(0.0)
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(50)
        try:
            self.anim_group.finished.disconnect()
        except TypeError:
            pass
        self.anim_group.start()
        self.search_input.setFocus()
    def fade_out_and_hide(self):
        self.anim_group.stop()
        self.opacity_anim.setStartValue(self.opacity_effect.opacity())
        self.opacity_anim.setEndValue(0.0)
        self.fade_anim.setStartValue(self.dark_overlay.bg_alpha)
        self.fade_anim.setEndValue(0)
        try:
            self.anim_group.finished.disconnect()
        except TypeError:
            pass
        self.anim_group.finished.connect(self._on_fade_out_finished)
        self.anim_group.start()
    def _on_fade_out_finished(self):
        self.container.hide()
        self.hide()
        self.bg_label.clear()                               
        self._cached_search_results = None                             
    def _update_list_height(self):
        count = self.results_list.count()
        if count == 0:
            return
        parent_height = self.parent().height() if self.parent() else 800
        self.container.adjustSize()
        actual_overhead = self.container.height() - self.results_list.height()
        container_y = parent_height // 5
        max_available_height = parent_height - container_y - actual_overhead - 40                           
        max_available_height = max(50, max_available_height)                  
        desired_height = 0
        for i in range(count):
            item = self.results_list.item(i)
            h = item.sizeHint().height()
            if h <= 0: h = 50 
            if desired_height + h > max_available_height:
                break
            desired_height += h
        final_height = desired_height + 4
        self.results_list.setFixedHeight(int(final_height))
        self.container.adjustSize()
        self.center_on_parent()
    def set_filter(self, filter_name):
        self.current_filter = filter_name
        import theme_manager
        accent_hex = theme_manager.get_current_accent_hex()
        accent = QColor(accent_hex)
        r, g, b = accent.red(), accent.green(), accent.blue()
        for name, data in self.filter_buttons.items():
            btn = data['widget']
            is_active = (name == filter_name)
            data['active'] = is_active
            btn.set_active(is_active, accent_hex)
        self.filter_tracks(self.search_input.text(), force_filter=True)
    def _do_search(self, query_parts):
        canciones = []
        albumes = set()
        artistas = set()
        playlists_matches = []
        for track in self.player.library:
            haystack_cancion = f"{track.title} {track.artist} {track.album}".lower()
            if all(part in haystack_cancion for part in query_parts):
                canciones.append(track)
            haystack_album = f"{track.album} {track.artist}".lower() if track.album else ""
            if haystack_album and all(part in haystack_album for part in query_parts):
                albumes.add(track.album)
            haystack_artist = track.artist.lower() if track.artist else ""
            if haystack_artist and all(part in haystack_artist for part in query_parts):
                for a in get_artists_from_string(track.artist):
                    if all(part in a.lower() for part in query_parts):
                        artistas.add(a)
        playlists_data = settings.get('playlists', {})
        for p_name in playlists_data.keys():
            if all(part in p_name.lower() for part in query_parts):
                playlists_matches.append(p_name)
        return {'canciones': canciones, 'albumes': albumes, 'artistas': artistas, 'playlists': playlists_matches}
    def filter_tracks(self, text, force_filter=False):
        self.results_list.clear()
        self.best_result_track = None
        if not text.strip() or not self.player:
            self.separator.hide()
            self.tabs_container.hide()
            self.results_list.hide()
            self._cached_search_results = None
            self.container.adjustSize()
            return
        query_parts = text.lower().split()
        if not force_filter or not hasattr(self, '_cached_search_results') or self._cached_search_results is None:
            self._cached_search_results = self._do_search(query_parts)
        canciones = self._cached_search_results['canciones']
        albumes = self._cached_search_results['albumes']
        artistas = self._cached_search_results['artistas']
        playlists_matches = self._cached_search_results['playlists']
        self.filter_buttons["Canciones"]['badge'].setText(str(len(canciones)))
        self.filter_buttons["Álbumes"]['badge'].setText(str(len(albumes)))
        self.filter_buttons["Artistas"]['badge'].setText(str(len(artistas)))
        self.filter_buttons["Playlists"]['badge'].setText(str(len(playlists_matches)))
        self.separator.show()
        self.tabs_container.show()
        count = 0
        import theme_manager
        accent_hex = theme_manager.get_current_accent_hex()
        def _add_header(title, m_top):
            header_widget = QWidget()
            layout = QHBoxLayout(header_widget)
            layout.setContentsMargins(2, m_top, 2, 8)
            lbl = QLabel(title)
            lbl.setStyleSheet(f"color: {accent_hex}; font-size: 16px; font-weight: bold;")
            layout.addWidget(lbl)
            layout.addStretch()
            header_widget.setFixedHeight(40)
            item = QListWidgetItem()
            item.setSizeHint(QSize(self.results_list.width(), 40))
            item.setData(Qt.ItemDataRole.UserRole, "WIDGET_ITEM")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, header_widget)
        if self.current_filter == "Canciones":
            best_results = canciones[:1]
            other_results = canciones[1:self.max_results]
            if best_results:
                _add_header("Mejor resultado", 5)
                for track in best_results:
                    item = QListWidgetItem()
                    item.setData(Qt.ItemDataRole.UserRole, track)
                    self.results_list.addItem(item)
                    count += 1
            if other_results:
                _add_header("Canciones", 10)
                for track in other_results:
                    item = QListWidgetItem()
                    item.setData(Qt.ItemDataRole.UserRole, track)
                    self.results_list.addItem(item)
                    count += 1
        elif self.current_filter == "Álbumes":
            if albumes:
                _add_header("Álbumes", 5)
            for alb in sorted(list(albumes)):
                if count >= self.max_results: break
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, {'type': 'album', 'name': alb})
                self.results_list.addItem(item)
                count += 1
        elif self.current_filter == "Artistas":
            if artistas:
                _add_header("Artistas", 5)
            for art in sorted(list(artistas)):
                if count >= self.max_results: break
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, {'type': 'artist', 'name': art})
                self.results_list.addItem(item)
                count += 1
        elif self.current_filter == "Playlists":
            if playlists_matches:
                _add_header("Playlists", 5)
            for p in sorted(playlists_matches):
                if count >= self.max_results: break
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, {'type': 'playlist', 'name': p})
                self.results_list.addItem(item)
                count += 1
        if count > 0:
            self.results_list.show()
            self._update_list_height()
            if self.results_list.count() > 1:
                self.results_list.setCurrentRow(1)
        else:
            self.results_list.hide()
            self.container.adjustSize()
    def play_best_result(self):
        pass                   
    def play_first_or_selected(self):
        if self.results_list.count() > 0 and self.results_list.currentRow() >= 0:
            current = self.results_list.currentItem()
            self.play_selected_track(current)
    def play_selected_track(self, item):
        item_data = item.data(Qt.ItemDataRole.UserRole)
        if item_data == "WIDGET_ITEM":
            return
        if hasattr(item_data, 'filepath'):
            self.play_track(item_data)
        elif isinstance(item_data, dict):
            tipo = item_data.get('type')
            if tipo == 'album':
                self.player.navigation_controller.open_album_detail(target_album_name=item_data['name'])
                self.fade_out_and_hide()
            elif tipo == 'artist':
                self.player.navigation_controller.open_artist_detail(artist_name_str=item_data['name'])
                self.fade_out_and_hide()
            elif tipo == 'playlist':
                if hasattr(self.player, 'stacked_widget') and hasattr(self.player, 'page_playlists'):
                    self.player.stacked_widget.setCurrentIndex(3)
                    p_name = item_data['name']
                    p_filepaths = settings.get('playlists', {}).get(p_name, [])
                    if hasattr(self.player.page_playlists, '_open_playlist'):
                        self.player.page_playlists._open_playlist(p_name, p_filepaths)
                self.fade_out_and_hide()
    def play_track(self, track):
        if track and self.player:
            self.player.queue_controller.play_specific_track_global(track, list(self.player.library))
        self.fade_out_and_hide()
    def show_context_menu(self, pos):
        item = self.results_list.itemAt(pos)
        if not item: return
        item_data = item.data(Qt.ItemDataRole.UserRole)
        if not item_data or not self.player: return
        if not hasattr(item_data, 'filepath'):
            return
        queue = []
        for i in range(self.results_list.count()):
            q_data = self.results_list.item(i).data(Qt.ItemDataRole.UserRole)
            if q_data and hasattr(q_data, 'filepath'): queue.append(q_data)
        if hasattr(self.player, 'context_menu_manager'):
            global_pos = self.results_list.viewport().mapToGlobal(pos)
            self.player.context_menu_manager.show_song_context_menu_at(item_data, global_pos, queue)