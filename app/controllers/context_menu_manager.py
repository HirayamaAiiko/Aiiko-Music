import os
import sys
import logging
from PyQt6.QtCore import Qt
from qfluentwidgets import RoundMenu, Action
from qfluentwidgets import FluentIcon as FIF
from config import ICON_PLAY, ICON_DELETE, ICON_HEART
from settings_manager import settings
from core.notification_manager import notify
from core.language_manager import tr
class ContextMenuManager:
    def __init__(self, main_window):
        self.main_window = main_window
    def _close_search_if_open(self):
        try:
            if hasattr(self.main_window, 'search_controller'):
                if hasattr(self.main_window.search_controller, 'spotlight_dialog'):
                    if self.main_window.search_controller.spotlight_dialog.isVisible():
                        self.main_window.search_controller.spotlight_dialog.fade_out_and_hide()
        except:
            pass
    def show_song_context_menu(self, pos, list_widget):
        item = list_widget.itemAt(pos)
        if not item: return
        track = item.data(Qt.ItemDataRole.UserRole)
        if not track: return
        queue = [list_widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(list_widget.count()) if list_widget.item(i).data(Qt.ItemDataRole.UserRole)]
        selected_items = list_widget.selectedItems()
        if item in selected_items:
            selected_tracks = [i.data(Qt.ItemDataRole.UserRole) for i in selected_items if i.data(Qt.ItemDataRole.UserRole)]
        else:
            selected_tracks = [track]
        self._build_context_menu(selected_tracks, pos, list_widget, queue)
    def show_song_context_menu_listview(self, pos, list_view=None):
        if list_view is None:
            list_view = self.main_window.list_songs
        index = list_view.indexAt(pos)
        if not index.isValid(): return
        track = index.data(Qt.ItemDataRole.UserRole)
        if not track: return
        source_queue = list(list_view.model().tracks) if hasattr(list_view.model(), 'tracks') else list(self.main_window.track_model.tracks)
        if hasattr(list_view, '_selection_tracker'):
            selected_tracks = list_view._selection_tracker.get_selected_tracks()
        else:
            selection_model = list_view.selectionModel()
            selected_indexes = selection_model.selectedIndexes() if selection_model else []
            selected_indexes = [idx for idx in selected_indexes if idx.column() == 0]
            if index in selected_indexes:
                selected_indexes.sort(key=lambda idx: idx.row())
                selected_tracks = [idx.data(Qt.ItemDataRole.UserRole) for idx in selected_indexes if idx.data(Qt.ItemDataRole.UserRole)]
            else:
                selected_tracks = [track]
        if track not in selected_tracks:
            selected_tracks = [track]
        self._build_context_menu(selected_tracks, pos, list_view, source_queue)
    def _populate_common_actions(self, menu, selected_tracks, source_queue):
        primary_track = selected_tracks[0]
        menu.addAction(Action(ICON_PLAY, tr("Reproducir"), triggered=lambda: self.main_window.queue_controller.play_specific_track_global(primary_track, source_queue)))
        queue_menu = RoundMenu(tr("Añadir a la cola"), parent=menu)
        queue_menu.setIcon(FIF.ADD)
        queue_menu.addAction(Action(FIF.ADD, tr("Añadir a continuación"), triggered=lambda: self.main_window.queue_controller.add_to_queue_next(selected_tracks)))
        queue_menu.addAction(Action(FIF.ADD, tr("Añadir al final"), triggered=lambda: self.main_window.queue_controller.add_to_queue(selected_tracks)))
        menu.addMenu(queue_menu)
        if primary_track.album and primary_track.album not in ["Desconocido", "Unknown", "", tr("Álbum Desconocido")]:
            t_artist = getattr(primary_track, 'album_artist', None) or primary_track.artist
            menu.addAction(Action(FIF.ALBUM, tr("Ir al álbum"), triggered=lambda: [self._close_search_if_open(), self.main_window.navigation_controller.open_album_detail(target_album_name=primary_track.album, target_artist_name=t_artist)]))
        from utils import get_artists_from_string
        artists = get_artists_from_string(primary_track.artist)
        if len(artists) == 1:
            menu.addAction(Action(FIF.PEOPLE, tr("Ir al artista"), triggered=lambda _, a=artists[0]: [self._close_search_if_open(), self.main_window.navigation_controller.open_artist_detail(artist_name_str=a)]))
        elif len(artists) > 1:
            artist_menu = RoundMenu(tr("Ir al artista"), parent=menu)
            artist_menu.setIcon(FIF.PEOPLE)
            for a in artists:
                artist_menu.addAction(Action(FIF.PEOPLE, a, triggered=lambda _, artist=a: [self._close_search_if_open(), self.main_window.navigation_controller.open_artist_detail(artist_name_str=artist)]))
            menu.addMenu(artist_menu)
        menu.addAction(Action(FIF.FOLDER, tr("Localizar en el explorador"), triggered=lambda: self.locate_in_explorer(primary_track.filepath)))
        favs = settings.get('favorites', [])
        is_fav = primary_track.filepath in favs
        fav_text, fav_icon = (tr("Quitar de Favoritos"), ICON_DELETE) if is_fav else (tr("Añadir a Favoritos"), ICON_HEART)
        force_fav_state = False if is_fav else True
        menu.addAction(Action(fav_icon, fav_text, triggered=lambda _, ts=selected_tracks, fs=force_fav_state: self.main_window.app_controller.toggle_favorite_tracks(ts, force_state=fs)))
        playlists = settings.get('playlists', {})
        if playlists:
            playlist_menu = RoundMenu(tr("Añadir a Playlist"), parent=menu)
            playlist_menu.setIcon(FIF.FOLDER_ADD)
            for p_name in playlists.keys():
                playlist_menu.addAction(Action(p_name, triggered=lambda _, p=p_name, ts=selected_tracks: self.main_window.app_controller.add_to_playlist(p, ts)))
            menu.addMenu(playlist_menu)
        menu.addSeparator()
        if len(selected_tracks) == 1:
            menu.addAction(Action(FIF.EDIT, tr("Propiedades"), triggered=lambda: self.main_window.app_controller.edit_track_metadata(primary_track)))
        menu.addAction(Action(FIF.DELETE, tr("Eliminar") if len(selected_tracks) == 1 else tr("Eliminar {count} canciones").format(count=len(selected_tracks)), triggered=lambda: self.delete_tracks_prompt(selected_tracks)))
    def _build_context_menu(self, selected_tracks, pos, widget, source_queue):
        menu = RoundMenu(parent=self.main_window)
        self._active_menu = menu
        from PyQt6.QtCore import Qt
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._populate_common_actions(menu, selected_tracks, source_queue)
        menu.exec(widget.mapToGlobal(pos))
    def show_song_context_menu_at(self, track, global_pos, source_queue):
        menu = RoundMenu(parent=self.main_window)
        self._active_menu = menu
        from PyQt6.QtCore import Qt
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._populate_common_actions(menu, [track], source_queue)
        menu.exec(global_pos)
    def show_song_context_menu_multiple_at(self, selected_tracks, global_pos, source_queue):
        menu = RoundMenu(parent=self.main_window)
        self._active_menu = menu
        from PyQt6.QtCore import Qt
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._populate_common_actions(menu, selected_tracks, source_queue)
        menu.exec(global_pos)
    def locate_in_explorer(self, filepath):
        import subprocess
        try:
            if os.name == 'nt': subprocess.run(['explorer', '/select,', os.path.normpath(filepath)])
            elif sys.platform == 'darwin': subprocess.run(['open', '-R', filepath])
            else: subprocess.run(['xdg-open', os.path.dirname(filepath)])
        except Exception as e: logging.error(f"Error abriendo explorador: {e}")
    def delete_tracks_prompt(self, tracks):
        is_batch = len(tracks) > 1
        title = tr("Eliminar {count} canciones").format(count=len(tracks)) if is_batch else tr("Eliminar canción")
        message = tr("¿Estás seguro de que deseas eliminar {count} canciones?\n\nPuedes quitarlas solo de la biblioteca o eliminar los archivos del PC (se moverán a la papelera).").format(count=len(tracks)) if is_batch else tr("¿Estás seguro de que deseas eliminar '{title}'?\n\nPuedes quitarla solo de la biblioteca o eliminar el archivo del PC (se moverá a la papelera).").format(title=tracks[0].title)
        result = notify.confirm_destructive(
            title,
            message,
            tr("Solo de biblioteca"),
            tr("Eliminar del PC")
        )
        if result == 1:                      
            self.main_window.app_controller.remove_invalid_tracks(tracks, add_to_blacklist=True)
            notify.success(tr("Eliminadas") if is_batch else tr("Eliminada"), tr("{count} canciones eliminadas de la biblioteca.").format(count=len(tracks)) if is_batch else tr("Canción eliminada de la biblioteca."))
        elif result == 2:                   
            try:
                from send2trash import send2trash
                for track in tracks:
                    clean_path = os.path.abspath(os.path.normpath(track.filepath))
                    send2trash(clean_path)
                self.main_window.app_controller.remove_invalid_tracks(tracks)
                notify.success(tr("Eliminadas") if is_batch else tr("Eliminada"), tr("{count} archivos enviados a la papelera.").format(count=len(tracks)) if is_batch else tr("Archivo enviado a la papelera."))
            except Exception as e:
                logging.error(f"Error al enviar a papelera: {e}")
                notify.error(tr("Error"), tr("No se pudo eliminar: {error}").format(error=e))
    def show_album_context_menu_at(self, album_name, representative_track, global_pos):
        menu = RoundMenu(parent=self.main_window)
        album_tracks = [t for t in getattr(self.main_window, 'library', []) if getattr(t, 'album', '') == album_name]
        menu.addAction(Action(ICON_PLAY, tr("Reproducir"), triggered=lambda: self.main_window.queue_controller.play_specific_track_global(album_tracks[0], album_tracks) if album_tracks else None))
        queue_menu = RoundMenu(tr("Añadir a la cola"), parent=menu)
        queue_menu.setIcon(FIF.ADD)
        queue_menu.addAction(Action(FIF.ADD, tr("Añadir a continuación"), triggered=lambda: self.main_window.queue_controller.add_to_queue_next(album_tracks)))
        queue_menu.addAction(Action(FIF.ADD, tr("Añadir al final"), triggered=lambda: self.main_window.queue_controller.add_to_queue(album_tracks)))
        menu.addMenu(queue_menu)
        from utils import get_artists_from_string
        artists = get_artists_from_string(representative_track.artist) if representative_track else []
        if len(artists) == 1:
            menu.addAction(Action(FIF.PEOPLE, tr("Ir al artista"), triggered=lambda _, a=artists[0]: [self._close_search_if_open(), self.main_window.navigation_controller.open_artist_detail(artist_name_str=a)]))
        elif len(artists) > 1:
            artist_menu = RoundMenu(tr("Ir al artista"), parent=menu)
            artist_menu.setIcon(FIF.PEOPLE)
            for a in artists:
                artist_menu.addAction(Action(FIF.PEOPLE, a, triggered=lambda _, artist=a: [self._close_search_if_open(), self.main_window.navigation_controller.open_artist_detail(artist_name_str=artist)]))
            menu.addMenu(artist_menu)
        playlists = settings.get('playlists', {})
        if playlists and album_tracks:
            playlist_menu = RoundMenu(tr("Añadir a Playlist"), parent=menu)
            playlist_menu.setIcon(FIF.FOLDER_ADD)
            for p_name in playlists.keys():
                playlist_menu.addAction(Action(p_name, triggered=lambda _, p=p_name, ts=album_tracks: self.main_window.app_controller.add_to_playlist(p, ts)))
            menu.addMenu(playlist_menu)
        menu.exec(global_pos)