from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from qfluentwidgets import LineEdit, BodyLabel, ComboBox, FluentIcon as FIF
from core.language_manager import tr
from UI.lyrics_editor.components import OutlineButton
class SearchPanel(QWidget):
    search_requested = pyqtSignal(str, str)                
    result_selected = pyqtSignal(int)
    def __init__(self, initial_title="", initial_artist="", accent_color="#1DB954", parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        self.initial_title = initial_title
        self.initial_artist = initial_artist
        self.init_ui()
    def init_ui(self):
        search_layout = QHBoxLayout(self)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(12)
        title_v = QVBoxLayout()
        title_v.setSpacing(6)
        lbl_in_t = BodyLabel(tr("Título de la canción"))
        lbl_in_t.setStyleSheet("color: #888; font-size: 12px;")
        self.input_title = LineEdit()
        self.input_title.setText(self.initial_title)
        title_v.addWidget(lbl_in_t)
        title_v.addWidget(self.input_title)
        artist_v = QVBoxLayout()
        artist_v.setSpacing(6)
        lbl_in_a = BodyLabel(tr("Artista"))
        lbl_in_a.setStyleSheet("color: #888; font-size: 12px;")
        self.input_artist = LineEdit()
        self.input_artist.setText(self.initial_artist)
        artist_v.addWidget(lbl_in_a)
        artist_v.addWidget(self.input_artist)
        btn_search_v = QVBoxLayout()
        btn_search_v.addStretch()
        self.btn_search = OutlineButton(tr("Buscar en Internet"), self.accent_color, hover_bg_alpha=12)
        self.btn_search.setIcon(FIF.SEARCH.icon(color=self.accent_color))
        self.btn_search.setFixedHeight(33)
        self.btn_search.clicked.connect(self._on_search_clicked)
        btn_search_v.addWidget(self.btn_search)
        search_layout.addLayout(title_v, 2)
        search_layout.addLayout(artist_v, 2)
        search_layout.addLayout(btn_search_v, 1)
    def set_loading(self, is_loading):
        self.btn_search.setText(tr("Buscando...") if is_loading else tr("Buscar en Internet"))
        self.btn_search.setEnabled(not is_loading)
    def _on_search_clicked(self):
        self.search_requested.emit(self.input_title.text().strip(), self.input_artist.text().strip())
    def setup_results_ui(self):
        pass
