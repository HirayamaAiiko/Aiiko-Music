from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
from PyQt6.QtCore import Qt
from UI.welcome_view.components import make_label, LangCard, TEXT_WHITE, TEXT_DIM
from settings_manager import settings
from core.language_manager import tr
from qfluentwidgets import SearchLineEdit
class PageLang(QWidget):
    def __init__(self, overlay, parent=None):
        super().__init__(parent)
        self.overlay = overlay
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.container = QWidget()
        self.container.setFixedWidth(600)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(16)
        title_style = f"font-size: 28px; font-weight: 800; color: {TEXT_WHITE.name()};"
        desc_style = f"font-size: 15px; color: {TEXT_DIM.name()};"
        self.title_lbl = make_label(tr("Elige tu idioma"), title_style)
        self.desc_lbl = make_label(tr("Selecciona el idioma principal para la interfaz de Aiiko Music."), desc_style)
        self.desc_lbl.setContentsMargins(0, 0, 0, 16)
        self.container_layout.addWidget(self.title_lbl)
        self.container_layout.addWidget(self.desc_lbl)
        from core.language_manager import lang_manager
        langs = lang_manager.get_available_languages()
        def _sort_key(item):
            code = item[0]
            if code == 'en': return 0
            if code == 'es': return 1
            return 2
        sorted_langs = sorted(langs.items(), key=_sort_key)
        self.search_box = SearchLineEdit(self)
        from PyQt6.QtCore import QSize
        self.search_box.searchButton.setIconSize(QSize(14, 14))
        self.search_box.clearButton.setIconSize(QSize(14, 14))
        self.search_box.setPlaceholderText(tr("Buscar idioma..."))
        self.search_box.setFixedHeight(36)
        self.search_box.textChanged.connect(self._on_search)
        self.container_layout.addWidget(self.search_box)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; } QWidget#LangScrollContent { background: transparent; }")
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("LangScrollContent")
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(4)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards = []
        for code, name in sorted_langs:
            card = LangCard(code, name)
            card.clicked.connect(self._on_card_clicked)
            self.cards.append(card)
            self.cards_layout.addWidget(card)
        self.scroll.setWidget(self.scroll_content)
        self.container_layout.addWidget(self.scroll, 1)
        self.main_layout.addWidget(self.container)
        self.update_dynamic_colors(self.overlay._current_accent)
        self._is_initializing = True
        current_lang = settings.get('language', 'es')
        self._on_card_clicked(current_lang)
        self._is_initializing = False
    def _on_card_clicked(self, code):
        for c in self.cards:
            c.set_selected(c.code == code, self.overlay._current_accent)
        if not getattr(self, '_is_initializing', False):
            settings.set('language', code)
            settings.save()
            from core.language_manager import lang_manager
            lang_manager.load_language(code)
            self.overlay.retranslate_ui()
            self.overlay._language_changed = (code != getattr(self.overlay, '_original_language', 'es'))
    def update_dynamic_colors(self, hex_c):
        current_code = settings.get('language', 'es')
        for c in self.cards:
            c.set_selected(c.code == current_code, hex_c)
    def _on_search(self, text):
        query = text.lower()
        for card in self.cards:
            match = query in card.lbl.text().lower()
            card.setVisible(match)
    def retranslate_ui(self):
        self.title_lbl.setText(tr("Elige tu idioma"))
        self.desc_lbl.setText(tr("Selecciona el idioma principal para la interfaz de Aiiko Music."))
        self.search_box.setPlaceholderText(tr("Buscar idioma..."))
