from datetime import datetime
import time
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QObject, QEvent, QPoint
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from qfluentwidgets import (TitleLabel, BodyLabel, SubtitleLabel, CaptionLabel,
                            PushButton, PrimaryPushButton, TransparentPushButton, ComboBox, SmoothScrollArea, FluentIcon as FIF)
from controllers.analytics_controller import AnalyticsController
from config import ICON_HEART
import theme_manager
from UI.user_profile_widget import UserProfileButton, is_birthday_today
from UI.dashboard.components.dashboard_cards import CoverCard, StatCard
from UI.dashboard.components.dashboard_buttons import _CarouselArrowBtn, QuickActionCard
from core.language_manager import tr
class _HorizontalDragFilter(QObject):
    def __init__(self, scroll_area, parent=None):
        super().__init__(parent or scroll_area)
        self._scroll = scroll_area
        self._dragging = False
        self._start_pos = QPoint()
        self._start_hbar = 0
    def eventFilter(self, obj, event):
        t = event.type()
        if t == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.globalPosition().toPoint()
            self._start_hbar = self._scroll.horizontalScrollBar().value()
            self._dragging = False
            return False
        if t == QEvent.Type.MouseMove and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._start_pos
            if not self._dragging and abs(delta.x()) > 8:
                self._dragging = True
            if self._dragging:
                self._scroll.horizontalScrollBar().setValue(self._start_hbar - delta.x())
                return True                                        
            return False
        if t == QEvent.Type.MouseButtonRelease:
            was_dragging = self._dragging
            self._dragging = False
            return was_dragging                                        
        return False
class DashboardMainPanel(QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self.setStyleSheet("background: transparent;")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 4, 12, 20)
        self.current_top_filter = "today"
        self._quick_action_cards = []
        self._build_stats_section()
        def go_to_library():
            self.player.navigation_controller.switch_page(1)
        self._build_carousel_section(
            tr("Escuchado Recientemente"),
            "_recent_scroll", "_recent_container", "_recent_widget", "_recent_empty",
            tr("¡Bienvenido a Aiiko Music!\nEmpieza reproduciendo algunas canciones."),
            empty_action_text=tr("Ir a mi Biblioteca"),
            empty_action_cb=go_to_library,
            empty_icon=FIF.HEADPHONE
        )
        self._build_carousel_section(
            tr("Tus Más Escuchadas"),
            "_top_scroll", "_top_container", "_top_widget", "_top_empty",
            tr("Aún no tienes canciones con suficientes reproducciones.\nDescubre música nueva en tu biblioteca."),
            empty_action_text=tr("Explorar Biblioteca"),
            empty_action_cb=go_to_library,
            empty_icon=FIF.HEART,
            has_filter=True
        )
        self._build_carousel_section(
            tr("Agregados Recientemente"),
            "_added_scroll", "_added_container", "_added_widget", "_added_empty",
            tr("No se encontraron canciones nuevas en los últimos 14 días."),
            badge=tr("Últimos 14 días")
        )
        self.main_layout.addStretch()
    def _get_accent(self):
        from settings_manager import settings
        return theme_manager.get_accent_hex(settings.get('app_accent_name', 'Teal (AIIKO)'))
    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    def _build_stats_section(self):
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        accent = self._get_accent()
        self.stat_tracks   = StatCard(FIF.MUSIC,   "—", tr("Canciones"),        color=accent)
        self.stat_duration = StatCard(FIF.HISTORY,  "—", tr("Duración total"),    color=accent)
        self.stat_artists  = StatCard(FIF.PEOPLE,   "—", tr("Artistas"),          color=accent)
        self.stat_plays    = StatCard(FIF.PLAY,     "—", tr("Reproducciones"),    color=accent)
        for card in (self.stat_tracks, self.stat_duration, self.stat_artists, self.stat_plays):
            stats_row.addWidget(card, 4)
        self.main_layout.addLayout(stats_row)
        from qfluentwidgets import FlowLayout
        actions_row = FlowLayout()
        actions_row.setContentsMargins(0, 0, 0, 0)
        actions_row.setVerticalSpacing(10)
        actions_row.setHorizontalSpacing(10)
        accent = self._get_accent()
        icon_shuffle = self.player.playback_ui_controller._get_icon('shuffle.svg', FIF.SYNC)
        btn_shuffle = QuickActionCard(tr("Aleatorio"), icon_shuffle, accent, is_active=False)
        btn_shuffle.clicked.connect(self._on_shuffle_all)
        actions_row.addWidget(btn_shuffle)
        self._quick_action_cards.append(btn_shuffle)
        icon_fav = self.player.playback_ui_controller._get_icon('heart_active.svg', ICON_HEART, color_hex="#FF5252")
        btn_fav = QuickActionCard(tr("Favoritos Mix"), icon_fav, accent, is_active=False)
        btn_fav.clicked.connect(self._on_play_favorites)
        actions_row.addWidget(btn_fav)
        self._quick_action_cards.append(btn_fav)
        def nav_action(p, tab=None, tab_idx=None):
            self.player.navigation_controller.switch_page(p)
            if tab and tab_idx is not None:
                self.player.navigation_controller._execute_when_page_ready(
                    p, 
                    lambda: self.player.navigation_controller.switch_library_tab(tab, tab_idx)
                )
        for label, icon, p, tab, tab_idx, is_active in [
            (tr("Biblioteca"),  FIF.MUSIC,        1, None,      None, False),
            (tr("Favoritos"),   FIF.HEART,        2, None,      None, False),
            (tr("Playlists"),   FIF.MUSIC_FOLDER, 3, None,      None, False),
            (tr("Álbumes"),     FIF.ALBUM,        1, 'albums',  1,    False),
            (tr("Artistas"),    FIF.PEOPLE,       1, 'artists', 2,    False),
        ]:
            btn = QuickActionCard(label, icon, accent, is_active=is_active)
            btn.clicked.connect(lambda _=False, pg=p, t=tab, ti=tab_idx: nav_action(pg, t, ti))
            actions_row.addWidget(btn)
            self._quick_action_cards.append(btn)
        self.main_layout.addLayout(actions_row)
    def refresh_theme(self):
        accent = self._get_accent()
        for card in (self.stat_tracks, self.stat_duration, self.stat_artists, self.stat_plays):
            if hasattr(card, 'set_accent'):
                card.set_accent(accent)
        for btn in getattr(self, '_quick_action_cards', []):
            if hasattr(btn, 'set_accent'):
                btn.set_accent(accent)
    def _build_carousel_section(self, title, scroll_attr, container_attr,
                                 widget_attr, empty_attr, empty_text,
                                 badge=None, has_filter=False,
                                 empty_action_text=None, empty_action_cb=None,
                                 empty_icon=None):
        header = QHBoxLayout()
        lbl = SubtitleLabel(title)
        lbl.setStyleSheet("font-size: 15px; font-weight: bold; background: transparent;")
        header.addWidget(lbl)
        if badge:
            badge_lbl = CaptionLabel(badge)
            badge_lbl.setStyleSheet("color: #888888; padding-left: 10px; font-size: 13px; background: transparent;")
            header.addWidget(badge_lbl, 0, Qt.AlignmentFlag.AlignBottom)
        header.addStretch()
        if has_filter:
            self.top_filter_cb = ComboBox()
            self.top_filter_cb.addItems([tr("Hoy"), tr("Esta semana"), tr("Este mes"), tr("Todo el tiempo")])
            self.top_filter_cb.setCurrentIndex(0)                   
            self.top_filter_cb.setFixedWidth(140)
            self.top_filter_cb.currentIndexChanged.connect(self._on_top_filter_changed)
            header.addWidget(self.top_filter_cb)
        self.main_layout.addLayout(header)
        container = QHBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.setSpacing(12)
        inner_widget = QWidget()
        inner_widget.setStyleSheet("background: transparent;")
        inner_widget.setLayout(container)
        scroll = SmoothScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedHeight(230)
        scroll.setStyleSheet("SmoothScrollArea { border: none; background: transparent; }")
        scroll.setWidget(inner_widget)
        scroll.viewport().installEventFilter(_HorizontalDragFilter(scroll))
        btn_left  = _CarouselArrowBtn("left")
        btn_right = _CarouselArrowBtn("right")
        def _update_arrows():
            hbar = scroll.horizontalScrollBar()
            btn_left.set_active(hbar.value() > 0)
            btn_right.set_active(hbar.value() < hbar.maximum())
        scroll.horizontalScrollBar().valueChanged.connect(lambda _: _update_arrows())
        scroll.horizontalScrollBar().rangeChanged.connect(lambda *_: _update_arrows())
        _update_arrows()
        def _smooth_scroll(target_val):
            hbar = scroll.horizontalScrollBar()
            if not hasattr(scroll, "_scroll_anim"):
                scroll._scroll_anim = QPropertyAnimation(hbar, b"value", scroll)
                scroll._scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                scroll._scroll_anim.setDuration(350)
            scroll._scroll_anim.stop()
            scroll._scroll_anim.setStartValue(hbar.value())
            scroll._scroll_anim.setEndValue(target_val)
            scroll._scroll_anim.start()
        _STEP = 172 * 2
        btn_left.clicked.connect(
            lambda: _smooth_scroll(max(0, scroll.horizontalScrollBar().value() - _STEP))
        )
        btn_right.clicked.connect(
            lambda: _smooth_scroll(min(scroll.horizontalScrollBar().maximum(),
                                       scroll.horizontalScrollBar().value() + _STEP))
        )
        from PyQt6.QtCore import QTimer as _QTimer
        _timer = _QTimer(scroll)
        _timer.setSingleShot(True)
        _timer.setInterval(1500)
        def _show_hbar(sc=scroll, t=_timer):
            sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            sc.horizontalScrollBar().show()
            t.start()
        def _hide_hbar(sc=scroll):
            sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            sc.horizontalScrollBar().hide()
        _timer.timeout.connect(_hide_hbar)
        scroll.horizontalScrollBar().valueChanged.connect(lambda _: _show_hbar())
        empty_container = QWidget()
        empty_container.setFixedHeight(230)
        empty_layout = QVBoxLayout(empty_container)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_layout.setSpacing(12)
        if empty_icon:
            from qfluentwidgets import IconWidget
            icon_widget = IconWidget(empty_icon)
            icon_widget.setFixedSize(48, 48)
            empty_layout.addWidget(icon_widget, 0, Qt.AlignmentFlag.AlignCenter)
        empty_lbl = BodyLabel(empty_text)
        empty_lbl.setStyleSheet("color: #888888; font-size: 13px; background: transparent;")
        empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_lbl, 0, Qt.AlignmentFlag.AlignCenter)
        if empty_action_text and empty_action_cb:
            btn = PrimaryPushButton(empty_action_text)
            btn.clicked.connect(empty_action_cb)
            empty_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
        empty_container.hide()
        carousel_row = QHBoxLayout()
        carousel_row.setContentsMargins(0, 0, 0, 0)
        carousel_row.setSpacing(0)
        carousel_row.addWidget(btn_left)
        carousel_row.addWidget(scroll, 1)
        carousel_row.addWidget(empty_container, 1)
        carousel_row.addWidget(btn_right)
        self.main_layout.addLayout(carousel_row)
        setattr(self, scroll_attr,     scroll)
        setattr(self, container_attr,  container)
        setattr(self, widget_attr,     inner_widget)
        setattr(self, empty_attr,      empty_container)
    def _on_top_filter_changed(self, index):
        mapping = {0: "today", 1: "week", 2: "month", 3: "all"}
        self.current_top_filter = mapping.get(index, "today")
        if hasattr(self.player, 'page_dashboard'):
            self.player.page_dashboard.refresh_top_tracks()
    def update_data(self, data):
        stats = data["stats"]
        self.stat_tracks.value_label.setText(str(stats["total_tracks"]))
        self.stat_duration.value_label.setText(
            AnalyticsController.format_duration(stats["total_duration_ms"])
        )
        self.stat_artists.value_label.setText(str(stats["total_artists"]))
        self.stat_plays.value_label.setText(str(stats["total_plays"]))
        self._refresh_carousel(
            data["recent"], self._recent_scroll, self._recent_container,
            self._recent_widget, self._recent_empty, subtitle_key="artist"
        )
        added = data["added"]
        if not added:
            self._added_scroll.hide()
            self._added_empty.show()
            for i in range(self._added_container.count()):
                item = self._added_container.itemAt(i)
                if item and item.widget():
                    item.widget().hide()
        else:
            self._added_scroll.show()
            self._added_empty.hide()
            now = time.time()
            for item in added:
                days_ago = int((now - (item.get("ctime") or now)) / 86400)
                if days_ago > 0:
                    d_txt = tr("día") if days_ago == 1 else tr("días")
                    item["_custom_subtitle"] = tr("Hace {count} {days}").format(count=days_ago, days=d_txt)
                else:
                    item["_custom_subtitle"] = tr("Hoy")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self._refresh_carousel(
            data["top"], self._top_scroll, self._top_container,
            self._top_widget, self._top_empty,
            subtitle_key="artist", play_count=True
        ))
        if added:
            QTimer.singleShot(100, lambda: self._refresh_carousel(
                added, self._added_scroll, self._added_container,
                self._added_widget, self._added_empty, subtitle_key="_custom_subtitle"
            ))
    def _refresh_carousel(self, items, scroll, container, parent_widget, empty_lbl,
                          subtitle_key="artist", play_count=False):
        if not items:
            scroll.hide()
            empty_lbl.show()
            for i in range(container.count()):
                item = container.itemAt(i)
                if item and item.widget():
                    item.widget().hide()
            return
        scroll.show()
        empty_lbl.hide()
        for i in range(container.count() - 1, -1, -1):
            item = container.itemAt(i)
            if item and item.spacerItem():
                container.removeItem(item)
        child_widgets = [container.itemAt(i).widget() for i in range(container.count()) if container.itemAt(i).widget() is not None]
        for i, item in enumerate(items):
            raw_title = item.get("title", "")
            if raw_title in ("Desconocido", "Artista Desconocido", "Álbum Desconocido"):
                raw_title = tr(raw_title)
            raw_subtitle = item.get(subtitle_key, "")
            if raw_subtitle in ("Desconocido", "Artista Desconocido", "Álbum Desconocido"):
                raw_subtitle = tr(raw_subtitle)
            if play_count:
                subtitle = f'{raw_subtitle} • {item.get("play_count", 0)}x'
            else:
                subtitle = raw_subtitle
            fp = item["filepath"]
            if i < len(child_widgets):
                card = child_widgets[i]
                card.update_data(
                    title=raw_title,
                    subtitle=subtitle,
                    cover_path=item.get("cover_path"),
                    filepath=fp
                )
                try: card.clicked.disconnect()
                except TypeError: pass
                card.clicked.connect(lambda _=False, f=fp: self._play_by_filepath(f))
                card.show()
            else:
                card = CoverCard(
                    title=raw_title,
                    subtitle=subtitle,
                    cover_path=item.get("cover_path"),
                    filepath=fp,
                    parent=parent_widget
                )
                card.clicked.connect(lambda _=False, f=fp: self._play_by_filepath(f))
                container.addWidget(card)
        for i in range(len(child_widgets) - 1, len(items) - 1, -1):
            card = child_widgets[i]
            container.removeWidget(card)
            card.deleteLater()
        container.addStretch()
    def _on_shuffle_all(self):
        if not getattr(self.player, 'library', None):
            return
        self.player.queue.set_queue(list(self.player.library))
        self.player.queue.current_index = -1
        if not getattr(self.player.queue, 'is_shuffled', False):
            self.player.queue_controller.toggle_shuffle()
        track = self.player.queue.get_next()
        if track:
            self.player.playback_controller.play_track(track)
        self.player.queue_controller.refresh_queue_ui()
    def _on_play_favorites(self):
        from database import get_favorites_db
        import random
        fav_paths = get_favorites_db()
        if not fav_paths:
            return
        fav_paths_set = set(fav_paths)
        fav_tracks = [t for t in self.player.library if t.filepath in fav_paths_set]
        if not fav_tracks:
            return
        random.shuffle(fav_tracks)
        self.player.queue_controller.play_specific_track_global(fav_tracks[0], fav_tracks)
    def _play_by_filepath(self, filepath):
        lib = self.player.library
        if not hasattr(self.player, '_library_dict') or len(self.player._library_dict) != len(lib):
            self.player._library_dict = {t.filepath: t for t in lib}
        track = self.player._library_dict.get(filepath)
        if not track:
            return
        queue = self.player.queue
        current_track = queue.get_current()
        if current_track and current_track.filepath == filepath:
            return
        track._is_dashboard_injection = True
        if current_track and getattr(current_track, '_is_dashboard_injection', False):
            queue.tracks[queue.current_index] = track
            self.player.playback_controller.play_track(track)
            self.player.queue_controller.refresh_queue_ui()
            return
        if queue.current_index >= 0:
            queue.tracks.insert(queue.current_index + 1, track)
        else:
            queue.tracks.insert(0, track)
        track_to_play = queue.get_next()
        if track_to_play:
            self.player.playback_controller.play_track(track_to_play)
        self.player.queue_controller.refresh_queue_ui()