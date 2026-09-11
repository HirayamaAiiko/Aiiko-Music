import os
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect
from PyQt6.QtWidgets import QListWidgetItem
from qfluentwidgets import RoundMenu, Action, FluentIcon as FIF
from settings_manager import settings
from utils import sanitize_text, get_artists_from_string
from workers import ArtistInfoFetcherThread
from core.language_manager import tr
class PageRouterMixin:
    def switch_page(self, index, force_reset=False):
        if getattr(self, '_switching_page', False):
            return
        if self.mw.stacked_widget.currentIndex() == index:
            if not force_reset:
                return
            if index == 3 and hasattr(self.mw, 'page_playlists') and hasattr(self.mw.page_playlists, 'main_stack'):
                if self.mw.page_playlists.main_stack.currentIndex() != 0:
                    if hasattr(self.mw.page_playlists, '_back_to_grid'):
                        self.mw.page_playlists._back_to_grid()
                    else:
                        self.mw.page_playlists.main_stack.setCurrentIndex(0)
                    self._nav_history_map.setdefault(index, []).clear()
                    self.update_return_button()
            elif index == 1:
                changed = False
                if hasattr(self.mw, 'stacked_lib'):
                    cw = self.mw.stacked_lib.currentWidget()
                    if cw == getattr(self.mw, 'album_detail_widget', None):
                        self.switch_library_tab('albums', 1)
                        changed = True
                    elif cw == getattr(self.mw, 'artist_detail_widget', None):
                        self.switch_library_tab('artists', 2)
                        changed = True
                if changed and hasattr(self.mw, 'page_library') and hasattr(self.mw.page_library, 'header_widget'):
                    self.mw.page_library.header_widget.show()
                if changed:
                    self._nav_history_map.setdefault(index, []).clear()
                    self.update_return_button()
            return
        self._switching_page = True
        route_keys = ['dashboard', 'library', 'favorites', 'playlists', 'now_playing', 'settings']
        if self.mw.stacked_widget.currentIndex() != 4 and index == 4:
            self.mw.previous_page_index = self.mw.stacked_widget.currentIndex()
        elif index != 4:
            self.mw.previous_page_index = index
        from PyQt6.QtWidgets import QGraphicsOpacityEffect, QLabel
        from settings_manager import settings
        anim_enabled = settings.get('enable_page_animations', True)
        if hasattr(self.mw, 'now_playing_anim') and self.mw.now_playing_anim.state() == QPropertyAnimation.State.Running:
            self.mw.now_playing_anim.stop()
            if self.mw.page_now_playing.parentWidget() != self.mw.stacked_widget:
                self.mw.stacked_widget.insertWidget(4, self.mw.page_now_playing)
            if index != 4:
                self.mw.page_now_playing.hide()
        is_exiting_now_playing = (self.mw.stacked_widget.currentIndex() == 4 and index != 4)
        if anim_enabled and is_exiting_now_playing:
            parent_w = self.mw.stacked_widget.parentWidget()
            self.mw.page_now_playing.setParent(parent_w)
            if index < len(route_keys):
                self.mw.nav_interface.blockSignals(True)
                self.mw.nav_interface.setCurrentItem(route_keys[index])
                self.mw.nav_interface.blockSignals(False)
            self.mw.stacked_widget.blockSignals(True)
            self.mw.stacked_widget.setCurrentIndex(index)
            self.mw.stacked_widget.blockSignals(False)
            target_rect = self.mw.stacked_widget.geometry()
            self.mw.page_now_playing.setGeometry(target_rect)
            self.mw.page_now_playing.show()
            self.mw.page_now_playing.raise_()
            if hasattr(self.mw.page_now_playing, 'full_title') and hasattr(self.mw.page_now_playing.full_title, 'timer'):
                self.mw.page_now_playing.full_title.timer.stop()
            if hasattr(self.mw.page_now_playing, 'full_artist') and hasattr(self.mw.page_now_playing.full_artist, '_scroll_timer'):
                self.mw.page_now_playing.full_artist._scroll_timer.stop()
            from PyQt6.QtWidgets import QGraphicsOpacityEffect
            effect = QGraphicsOpacityEffect(self.mw.page_now_playing)
            self.mw.page_now_playing.setGraphicsEffect(effect)
            self.mw.now_playing_anim = QPropertyAnimation(effect, b"opacity")
            self.mw.now_playing_anim.setDuration(150)                                
            self.mw.now_playing_anim.setStartValue(1.0)
            self.mw.now_playing_anim.setEndValue(0.0)
            def on_exit_finished():
                self.mw.page_now_playing.hide()
                self.mw.page_now_playing.setGraphicsEffect(None)                 
                self.mw.stacked_widget.insertWidget(4, self.mw.page_now_playing)
                if hasattr(self.mw.page_now_playing, 'full_title') and hasattr(self.mw.page_now_playing.full_title, 'timer'):
                    self.mw.page_now_playing.full_title.timer.start(30)
                if hasattr(self.mw.page_now_playing, 'full_artist') and hasattr(self.mw.page_now_playing.full_artist, '_scroll_timer'):
                    self.mw.page_now_playing.full_artist._scroll_timer.start(30)
                if getattr(self.mw.stacked_widget.widget(index), 'is_placeholder', False):
                    from PyQt6.QtCore import QTimer
                    def do_heavy():
                        self.preload_view(index)
                        if not getattr(self, '_restoring', False):
                            self.update_return_button()
                        if force_reset and hasattr(self, '_reset_view_state'):
                            self._reset_view_state(index)
                        self._notify_page_ready(index)
                    QTimer.singleShot(50, do_heavy)
                else:
                    if index == 0:
                        if hasattr(self.mw, 'page_dashboard'): self.mw.page_dashboard.refresh()
                    elif index == 2: self.mw.library_controller.refresh_favorites_view()
                    elif index == 3: self.mw.library_controller.refresh_playlists_view_details()
                    if not getattr(self, '_restoring', False):
                        self.update_return_button()
                    if force_reset and hasattr(self, '_reset_view_state'):
                        self._reset_view_state(index)
                self._switching_page = False
            self.mw.now_playing_anim.finished.connect(on_exit_finished)
            self.mw.now_playing_anim.start()
            return
        if anim_enabled and index == 4:
            parent_w = self.mw.stacked_widget.parentWidget()
            self.mw.page_now_playing.setParent(parent_w)
            if index < len(route_keys):
                self.mw.nav_interface.blockSignals(True)
                self.mw.nav_interface.setCurrentItem(route_keys[index])
                self.mw.nav_interface.blockSignals(False)
            target_rect = self.mw.stacked_widget.geometry()
            self.mw.page_now_playing.setGeometry(target_rect)
            self.mw.page_now_playing.show() 
            self.mw.page_now_playing.raise_()
            if hasattr(self.mw.page_now_playing, 'full_title') and hasattr(self.mw.page_now_playing.full_title, 'timer'):
                self.mw.page_now_playing.full_title.timer.stop()
            if hasattr(self.mw.page_now_playing, 'full_artist') and hasattr(self.mw.page_now_playing.full_artist, '_scroll_timer'):
                self.mw.page_now_playing.full_artist._scroll_timer.stop()
            from PyQt6.QtWidgets import QGraphicsOpacityEffect
            effect = QGraphicsOpacityEffect(self.mw.page_now_playing)
            self.mw.page_now_playing.setGraphicsEffect(effect)
            self.mw.now_playing_anim = QPropertyAnimation(effect, b"opacity")
            self.mw.now_playing_anim.setDuration(150)             
            self.mw.now_playing_anim.setStartValue(0.0)
            self.mw.now_playing_anim.setEndValue(1.0)
            def on_entry_finished():
                self.mw.page_now_playing.setGraphicsEffect(None)                 
                self.mw.stacked_widget.insertWidget(4, self.mw.page_now_playing)
                self.mw.stacked_widget.setCurrentIndex(4) 
                if hasattr(self.mw.page_now_playing, 'full_title') and hasattr(self.mw.page_now_playing.full_title, 'timer'):
                    self.mw.page_now_playing.full_title.timer.start(30)
                if hasattr(self.mw.page_now_playing, 'full_artist') and hasattr(self.mw.page_now_playing.full_artist, '_scroll_timer'):
                    self.mw.page_now_playing.full_artist._scroll_timer.start(30)
            self.mw.now_playing_anim.finished.connect(on_entry_finished)
            self.mw.now_playing_anim.start()
            self._switching_page = False
            return
        if index < len(route_keys):
            self.mw.nav_interface.blockSignals(True)
            self.mw.nav_interface.setCurrentItem(route_keys[index])
            self.mw.nav_interface.blockSignals(False)
        def do_switch():
            try:
                try:
                    if getattr(self.mw.stacked_widget.widget(index), 'is_placeholder', False):
                        self.mw.stacked_widget.setCurrentIndex(index)
                        def do_heavy_load():
                            self.preload_view(index)
                            if hasattr(self, '_restoring') and self._restoring:
                                pass
                            else:
                                self.update_return_button()
                            if force_reset and hasattr(self, '_reset_view_state'):
                                self._reset_view_state(index)
                            self._notify_page_ready(index)
                        from PyQt6.QtCore import QTimer
                        QTimer.singleShot(50, do_heavy_load)
                        return
                except Exception as e:
                    pass
                self.mw.stacked_widget.blockSignals(True)
                self.mw.stacked_widget.setCurrentIndex(index)
                self.mw.stacked_widget.blockSignals(False)
                if index == 0:
                    if hasattr(self.mw, 'page_dashboard'): self.mw.page_dashboard.refresh()
                elif index == 1:
                    pass
                elif index == 2: self.mw.library_controller.refresh_favorites_view()
                elif index == 3: self.mw.library_controller.refresh_playlists_view_details()
            finally:
                if not getattr(self, '_restoring', False):
                    self.update_return_button()
                self._switching_page = False
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(20, do_switch)
    def switch_library_tab(self, tab_name, index, delay_ms=250):
        if hasattr(self.mw, 'pivot'):
            self.mw.pivot.blockSignals(True)
            self.mw.pivot.setCurrentItem(tab_name)
            self.mw.pivot.blockSignals(False)
        if not hasattr(self.mw, 'stacked_lib'):
            return
        try:
            old_widget = self.mw.stacked_lib.widget(index)
            if getattr(old_widget, 'is_placeholder', False):
                import logging
                logging.info(f"Instanciando lazy tab {tab_name}...")
                self.mw.stacked_lib.setCurrentIndex(index)
                self.mw.current_lib_tab = tab_name
                def build_lazy_tab():
                    try:
                        new_tab = None
                        if tab_name == 'albums':
                            from UI.library.albums.albums_tab import AlbumsTab
                            new_tab = AlbumsTab(self.mw, parent=self.mw.stacked_lib)
                            self.mw.page_library.albums_tab = new_tab
                        elif tab_name == 'artists':
                            from UI.library.artists.artists_tab import ArtistsTab
                            new_tab = ArtistsTab(self.mw, parent=self.mw.stacked_lib)
                            self.mw.page_library.artists_tab = new_tab
                        elif tab_name == 'folders':
                            from UI.library.folders.folders_tab import FoldersTab
                            new_tab = FoldersTab(self.mw, parent=self.mw.stacked_lib)
                            self.mw.page_library.folders_tab = new_tab
                        if new_tab:
                            self.mw.stacked_lib.removeWidget(old_widget)
                            self.mw.stacked_lib.insertWidget(index, new_tab)
                            old_widget.deleteLater()
                            self.mw.stacked_lib.setCurrentIndex(index)
                            if hasattr(self.mw, 'library') and self.mw.library:
                                pass                                                                                         
                            if hasattr(self.mw, 'theme_controller'):
                                from PyQt6.QtCore import QTimer as _QTimer
                                from qfluentwidgets.common.style_sheet import updateStyleSheet as _updateStyleSheet
                                _QTimer.singleShot(0, _updateStyleSheet)
                                _QTimer.singleShot(0, lambda: self.mw.theme_controller.apply_theme(full_refresh=False))
                            self._notify_tab_ready(tab_name)
                            if hasattr(self.mw, 'library_controller'):
                                self.mw.library_controller.update_library_count()
                    except Exception as e:
                        import logging
                        logging.error(f"Error en lazy load de tab {tab_name}: {e}")
                from PyQt6.QtCore import QTimer
                if delay_ms > 0:
                    QTimer.singleShot(delay_ms, build_lazy_tab)
                else:
                    QTimer.singleShot(0, build_lazy_tab)
        except Exception as e:
            import logging
            logging.error(f"Error en lazy load setup de {tab_name}: {e}")
        self.mw.stacked_lib.setCurrentIndex(index)
        self.mw.current_lib_tab = tab_name
        if hasattr(self.mw, 'page_library') and hasattr(self.mw.page_library, 'header_widget'):
            self.mw.page_library.header_widget.show()
        if not hasattr(self.mw, 'sort_combo'):
            return
        self.mw.sort_combo.blockSignals(True)
        self.mw.sort_combo.clear()
        if hasattr(self.mw, 'btn_view_mode'):
            self.mw.btn_view_mode.show()
        if tab_name in ('songs', 'folders'):
            self.mw.sort_combo.addItems([
                tr("A-Z"), tr("Z-A"), tr("Artista"), tr("Álbum"), 
                tr("Año (Reciente)"), tr("Fecha Modificación"), 
                tr("Fecha de Creación (Reciente)"), tr("Fecha de Creación (Antiguo)"),
                tr("Favoritos"), tr("Duración (Mayor)"), tr("Duración (Menor)"),
                tr("ReplayGain")
            ])
        else:
            self.mw.sort_combo.addItems([tr("A-Z"), tr("Z-A")])
        sort_configs = settings.get('sort_configs', {})
        saved_idx = sort_configs.get(tab_name, 0)
        if saved_idx >= self.mw.sort_combo.count():
            saved_idx = 0
        self.mw.sort_combo.setCurrentIndex(saved_idx)
        self.mw.sort_combo.blockSignals(False)
        if hasattr(self.mw, 'library_controller'):
            self.mw.library_controller.update_library_count()
    def toggle_fullscreen(self):
        if not hasattr(self.mw, 'fullscreen_view'):
            from UI.fullscreen import FullScreenPlayer
            self.mw.fullscreen_view = FullScreenPlayer(self.mw)
        anim_enabled = settings.get('enable_page_animations', True)
        if hasattr(self.mw, 'fullscreen_anim') and self.mw.fullscreen_anim:
            self.mw.fullscreen_anim.stop()
            try:
                self.mw.fullscreen_anim.finished.disconnect()
            except:
                pass
            self.mw.fullscreen_anim.deleteLater()
            self.mw.fullscreen_anim = None
        if self.mw.fullscreen_view.isVisible():
            if anim_enabled:
                self.mw.fullscreen_anim = QPropertyAnimation(self.mw.fullscreen_view, b"windowOpacity")
                self.mw.fullscreen_anim.setDuration(250)
                self.mw.fullscreen_anim.setStartValue(self.mw.fullscreen_view.windowOpacity())
                self.mw.fullscreen_anim.setEndValue(0.0)
                self.mw.fullscreen_anim.finished.connect(self.mw.fullscreen_view.hide)
                self.mw.fullscreen_anim.start()
            else:
                self.mw.fullscreen_view.hide()
        else:
            if hasattr(self.mw, 'queue') and self.mw.queue.tracks and 0 <= self.mw.queue.current_index < len(self.mw.queue.tracks):
                track = self.mw.queue.tracks[self.mw.queue.current_index]
                cover_pixmap = None
                if track.cover_path:
                    cached = self.mw.image_cache.get_cached_pixmap(track.cover_path, 450, 20)
                    if cached and not cached.isNull():
                        cover_pixmap = cached
                self.mw.fullscreen_view.update_metadata(track, cover_pixmap, self.mw.audio_engine.is_playing())
                self.mw.image_cache.assign_async_pixmap(self.mw.fullscreen_view.cover, track, 450, 20)
                curr_ms = self.mw.audio_engine.get_position()
                total_ms = self.mw.audio_engine.get_length()
                self.mw.fullscreen_view.update_progress(curr_ms, total_ms)
            if self.mw.windowHandle() and self.mw.windowHandle().screen():
                target_screen = self.mw.windowHandle().screen()
                if self.mw.fullscreen_view.screen() != target_screen:
                    self.mw.fullscreen_view.setScreen(target_screen)
            if anim_enabled:
                self.mw.fullscreen_view.setWindowOpacity(0.0)
                self.mw.fullscreen_view.showFullScreen()
                self.mw.fullscreen_anim = QPropertyAnimation(self.mw.fullscreen_view, b"windowOpacity")
                self.mw.fullscreen_anim.setDuration(300)
                self.mw.fullscreen_anim.setStartValue(0.0)
                self.mw.fullscreen_anim.setEndValue(1.0)
                self.mw.fullscreen_anim.start()
            else:
                self.mw.fullscreen_view.setWindowOpacity(1.0)
                self.mw.fullscreen_view.showFullScreen()
    def toggle_now_playing(self):
        if self.mw.stacked_widget.currentIndex() == 4:
            target_index = getattr(self.mw, 'previous_page_index', 0)
            if target_index == 4: target_index = 0 
            self.switch_page(target_index)
        else:
            self.switch_page(4)
