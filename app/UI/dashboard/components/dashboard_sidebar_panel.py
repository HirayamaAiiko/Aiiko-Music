from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy
from qfluentwidgets import SubtitleLabel, BodyLabel, CaptionLabel, CardWidget
from controllers.analytics_controller import AnalyticsController
from UI.dashboard.components.dashboard_charts import WeeklyBarChart
from UI.dashboard.components.dashboard_sidebar import ArtistRow, GenreRow
from core.language_manager import tr
class DashboardSidebarPanel(QWidget):
    artist_clicked = pyqtSignal(str)
    explore_clicked = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.sidebar_layout = QVBoxLayout(self)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_layout.setSpacing(16)
        self._build_sidebar_artists()
        self._build_sidebar_listen_state()
        self._build_sidebar_genres()
        self.sidebar_layout.addStretch()
    def _get_accent(self):
        import theme_manager
        from settings_manager import settings
        return theme_manager.get_accent_hex(settings.get('app_accent_name', 'Teal (AIIKO)'))
    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    def _build_sidebar_artists(self):
        header = QHBoxLayout()
        lbl = SubtitleLabel(tr("Top Artistas"))
        lbl.setStyleSheet("font-size: 15px; font-weight: bold; background: transparent;")
        header.addWidget(lbl)
        header.addStretch()
        self.sidebar_layout.addLayout(header)
        self.artists_card = CardWidget()
        self.artists_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.artists_card_layout = QVBoxLayout(self.artists_card)
        self.artists_card_layout.setContentsMargins(8, 8, 8, 8)
        self.artists_card_layout.setSpacing(0)
        self._artists_empty_container = QWidget()
        empty_layout = QVBoxLayout(self._artists_empty_container)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setContentsMargins(0, 20, 0, 20)
        empty_layout.setSpacing(12)
        lbl_empty = BodyLabel(tr("Aún no tienes artistas favoritos"))
        lbl_empty.setStyleSheet("color: #888888; font-size: 13px;")
        empty_layout.addWidget(lbl_empty, 0, Qt.AlignmentFlag.AlignCenter)
        from qfluentwidgets import PrimaryPushButton
        btn_explore = PrimaryPushButton(tr("Explorar Música"))
        btn_explore.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_explore.clicked.connect(self.explore_clicked.emit)
        empty_layout.addWidget(btn_explore, 0, Qt.AlignmentFlag.AlignCenter)
        self.artists_card_layout.addWidget(self._artists_empty_container)
        self._artists_empty_container.hide()
        self._artist_rows = []
        self._artist_seps = []
        self.sidebar_layout.addWidget(self.artists_card)
    def _build_sidebar_listen_state(self):
        header = QHBoxLayout()
        lbl = SubtitleLabel(tr("Estado de Escucha"))
        lbl.setStyleSheet("font-size: 15px; font-weight: bold; background: transparent;")
        header.addWidget(lbl)
        header.addStretch()
        self.sidebar_layout.addLayout(header)
        self.listen_state_card = CardWidget()
        self.listen_state_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        card_layout = QVBoxLayout(self.listen_state_card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(12)
        mini_row = QHBoxLayout()
        mini_row.setSpacing(8)
        left_stat = QVBoxLayout()
        time_lbl = CaptionLabel(tr("Tiempo de escucha"))
        time_lbl.setStyleSheet("color: #888888; font-size: 12px; background: transparent;")
        time_lbl.setWordWrap(True)
        left_stat.addWidget(time_lbl)
        self._listen_time_val = SubtitleLabel(tr("—"))
        self._listen_time_val.setWordWrap(True)
        self._listen_time_val.setStyleSheet("font-weight: bold; font-size: 16px; background: transparent;")
        left_stat.addWidget(self._listen_time_val)
        self._listen_time_pct = CaptionLabel("")
        self._listen_time_pct.setStyleSheet("color: #666666; font-size: 12px; background: transparent;")
        self._listen_time_pct.setWordWrap(True)
        left_stat.addWidget(self._listen_time_pct)
        mini_row.addLayout(left_stat, 1)
        vsep = QFrame()
        vsep.setFixedWidth(1)
        vsep.setStyleSheet("background: rgba(255,255,255,0.07);")
        mini_row.addWidget(vsep)
        right_stat = QVBoxLayout()
        right_stat.setContentsMargins(8, 0, 0, 0)
        tracks_lbl = CaptionLabel(tr("Canciones escuchadas"))
        tracks_lbl.setStyleSheet("color: #888888; font-size: 12px; background: transparent;")
        tracks_lbl.setWordWrap(True)
        right_stat.addWidget(tracks_lbl)
        self._listen_tracks_val = SubtitleLabel(tr("—"))
        self._listen_tracks_val.setWordWrap(True)
        self._listen_tracks_val.setStyleSheet("font-weight: bold; font-size: 16px; background: transparent;")
        right_stat.addWidget(self._listen_tracks_val)
        self._listen_tracks_pct = CaptionLabel("")
        self._listen_tracks_pct.setStyleSheet("color: #666666; font-size: 12px; background: transparent;")
        self._listen_tracks_pct.setWordWrap(True)
        right_stat.addWidget(self._listen_tracks_pct)
        mini_row.addLayout(right_stat, 1)
        card_layout.addLayout(mini_row)
        hsep = QFrame()
        hsep.setFixedHeight(1)
        hsep.setStyleSheet("background: rgba(255,255,255,0.07);")
        card_layout.addWidget(hsep)
        self._week_chart = WeeklyBarChart()
        self._week_chart.setFixedHeight(80)
        card_layout.addWidget(self._week_chart)
        self.sidebar_layout.addWidget(self.listen_state_card)
    def _build_sidebar_genres(self):
        header = QHBoxLayout()
        lbl = SubtitleLabel(tr("Géneros más escuchados"))
        lbl.setStyleSheet("font-size: 15px; font-weight: bold; background: transparent;")
        header.addWidget(lbl)
        header.addStretch()
        self.sidebar_layout.addLayout(header)
        self.genres_card = CardWidget()
        self.genres_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.genres_card_layout = QVBoxLayout(self.genres_card)
        self.genres_card_layout.setContentsMargins(14, 10, 14, 10)
        self.genres_card_layout.setSpacing(8)
        self.sidebar_layout.addWidget(self.genres_card)
    def update_data(self, data):
        accent = self._get_accent()
        artist_covers = data["artist_covers"]
        top_artists = data["artists"]
        if not top_artists:
            self._artists_empty_container.show()
            for row in self._artist_rows:
                row.hide()
            for sep in self._artist_seps:
                sep.hide()
        else:
            self._artists_empty_container.hide()
            for i, d in enumerate(top_artists):
                artist_name = d["artist"]
                if artist_name in ("Desconocido", "Artista Desconocido", "Álbum Desconocido"):
                    artist_name = tr(artist_name)
                if i < len(self._artist_rows):
                    row = self._artist_rows[i]
                    row.update_data(
                        rank=i + 1, artist_name=artist_name,
                        total_plays=d["total_plays"],
                        cover_path=artist_covers.get(d["artist"]),
                        accent=accent
                    )
                    row.show()
                else:
                    row = ArtistRow(
                        rank=i + 1, artist_name=artist_name,
                        total_plays=d["total_plays"],
                        cover_path=artist_covers.get(d["artist"]),
                        accent=accent, parent=self.artists_card
                    )
                    row.clicked.connect(self.artist_clicked.emit)
                    self.artists_card_layout.insertWidget(self.artists_card_layout.count() - 1, row)
                    self._artist_rows.append(row)
                if i < len(top_artists) - 1:
                    if i < len(self._artist_seps):
                        self._artist_seps[i].show()
                    else:
                        sep = QFrame()
                        sep.setFixedHeight(1)
                        sep.setStyleSheet("background-color: rgba(255,255,255,0.05);")
                        self.artists_card_layout.insertWidget(self.artists_card_layout.count() - 1, sep)
                        self._artist_seps.append(sep)
            for i in range(len(top_artists), len(self._artist_rows)):
                self._artist_rows[i].hide()
            for i in range(len(top_artists) - 1, len(self._artist_seps)):
                if i >= 0:
                    self._artist_seps[i].hide()
        weekly = data["weekly"]
        self._listen_time_val.setText(AnalyticsController.format_duration(weekly["total_ms"]))
        self._listen_tracks_val.setText(str(weekly["total_tracks"]))
        def pct_label(curr, prev):
            if prev == 0:
                return tr("▲ Primera semana") if curr > 0 else ""
            delta = round((curr - prev) / prev * 100)
            arrow = "▲" if delta >= 0 else "▼"
            color = "#22C55E" if delta >= 0 else "#EF4444"
            return tr('<span style="color:{color}">{arrow} {delta}% vs sem. anterior</span>').format(color=color, arrow=arrow, delta=abs(delta))
        self._listen_time_pct.setText(pct_label(weekly["total_ms"], weekly["prev_ms"]))
        self._listen_time_pct.setTextFormat(Qt.TextFormat.RichText)
        self._listen_tracks_pct.setText(pct_label(weekly["total_tracks"], weekly["prev_tracks"]))
        self._listen_tracks_pct.setTextFormat(Qt.TextFormat.RichText)
        self._week_chart.set_data(weekly["by_day"], accent)
        genres = data["genres"]
        child_widgets = []
        for i in range(self.genres_card_layout.count()):
            item = self.genres_card_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), GenreRow):
                child_widgets.append(item.widget())
        if not genres:
            for w in child_widgets: w.hide()
            if not getattr(self, '_genres_empty_container', None):
                self._genres_empty_container = QWidget()
                empty_layout = QVBoxLayout(self._genres_empty_container)
                empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_layout.setContentsMargins(0, 16, 0, 16)
                empty_layout.setSpacing(12)
                lbl = BodyLabel(tr("Sin datos de género"))
                lbl.setStyleSheet("color: #888888; font-size: 13px;")
                empty_layout.addWidget(lbl, 0, Qt.AlignmentFlag.AlignCenter)
                from qfluentwidgets import PrimaryPushButton
                btn = PrimaryPushButton(tr("Descubrir"))
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(self.explore_clicked.emit)
                empty_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
                self.genres_card_layout.addWidget(self._genres_empty_container)
            self._genres_empty_container.show()
            return
        if getattr(self, '_genres_empty_container', None):
            self._genres_empty_container.hide()
        for i, item in enumerate(genres):
            genre_name = item["genre"]
            if genre_name in ("Desconocido", "Artista Desconocido", "Álbum Desconocido"):
                genre_name = tr(genre_name)
            if i < len(child_widgets):
                row = child_widgets[i]
                row.update_data(genre_name, item["pct"], accent)
                row.show()
            else:
                row = GenreRow(genre_name, item["pct"], accent, self.genres_card)
                self.genres_card_layout.addWidget(row)
        for i in range(len(genres), len(child_widgets)):
            child_widgets[i].hide()