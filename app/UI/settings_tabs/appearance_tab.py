from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QGridLayout, QColorDialog
from PyQt6.QtGui import QPainter, QColor, QConicalGradient, QCursor, QPen
from qfluentwidgets import ComboBox, SwitchButton, FluentIcon as FIF
from settings_manager import settings
import theme_manager
from .base_settings_tab import BaseSettingsTab
from core.language_manager import tr
class _ColorCircle(QWidget):
    clicked = pyqtSignal(str, str)
    custom_clicked = pyqtSignal()
    def __init__(self, name, hex_color, is_multicolor=False, parent=None):
        super().__init__(parent)
        self._name = name
        self._hex = hex_color
        self._is_multicolor = is_multicolor
        self._selected = False
        self._hover = False
        self.setFixedSize(36, 36)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip(tr(name))
    def set_selected(self, s):
        self._selected = s
        self.update()
    def enterEvent(self, e):
        self._hover = True
        self.update()
    def leaveEvent(self, e):
        self._hover = False
        self.update()
    def mousePressEvent(self, e):
        if self._is_multicolor:
            self.custom_clicked.emit()
        else:
            self.clicked.emit(self._name, self._hex)
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = 28 if (self._selected or self._hover) else 22
        off = (36 - size) // 2
        if self._is_multicolor:
            grad = QConicalGradient(18, 18, 0)
            grad.setColorAt(0.0, QColor(255, 0, 0))
            grad.setColorAt(0.16, QColor(255, 255, 0))
            grad.setColorAt(0.33, QColor(0, 255, 0))
            grad.setColorAt(0.5, QColor(0, 255, 255))
            grad.setColorAt(0.66, QColor(0, 0, 255))
            grad.setColorAt(0.83, QColor(255, 0, 255))
            grad.setColorAt(1.0, QColor(255, 0, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(grad)
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(self._hex))
        p.drawEllipse(off, off, size, size)
        if self._selected:
            p.setPen(QPen(QColor(255,255,255,200), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(off-3, off-3, size+6, size+6)
        p.end()
class _AccentSelectorWidget(QWidget):
    accent_changed = pyqtSignal(str)
    def __init__(self, current, parent=None):
        super().__init__(parent)
        lo = QHBoxLayout(self)
        lo.setContentsMargins(0, 0, 0, 0)
        grid = QGridLayout()
        grid.setSpacing(8)
        self._circles = []
        names = ["Color del Sistema"] + [n for n in theme_manager.get_accent_names() if n != "Color del Sistema"]
        row, col = 0, 0
        for name in names:
            hex_c = theme_manager.get_accent_hex(name)
            circle = _ColorCircle(name, hex_c)
            circle.set_selected(name == current)
            circle.clicked.connect(self._on_accent_picked)
            self._circles.append(circle)
            grid.addWidget(circle, row, col)
            col += 1
            if col > 6:
                col = 0
                row += 1
        lo.addLayout(grid)
        lo.addStretch()
    def _update_selection(self, selected_name):
        for c in self._circles:
            c.set_selected(c._name == selected_name)
    def _on_accent_picked(self, name, hex_c):
        self._update_selection(name)
        self.accent_changed.emit(name)
class AppearanceTab(BaseSettingsTab):
    def __init__(self, player, parent=None):
        super().__init__(player, parent)
        card1, cl1 = self._create_card(tr("Tema y Colores"), FIF.PALETTE)
        player.combo_theme = ComboBox()
        player.combo_theme.addItems(theme_manager.get_theme_names())
        player.combo_theme.setCurrentText(settings.get('app_theme', 'Oscuro (Dark)'))
        player.combo_theme.currentTextChanged.connect(player.theme_controller.change_theme)
        self._setting_row(cl1, tr("Tema de la Aplicación"),
                          tr("Selecciona el esquema de colores de fondo del reproductor."), player.combo_theme)
        player.accent_selector = _AccentSelectorWidget(settings.get('app_accent_name', 'Cian'))
        from PyQt6.QtCore import QTimer
        player.accent_selector.accent_changed.connect(
            lambda name: QTimer.singleShot(100, lambda n=name: player.theme_controller.change_accent(n))
        )
        self._setting_row(cl1, tr("Color de Acento"),
                          tr("Color principal de botones, sliders y elementos de selección."), player.accent_selector)
        player.switch_gradient = SwitchButton()
        player.switch_gradient.setChecked(settings.get('gradient_enabled', True))
        player.switch_gradient.checkedChanged.connect(player.theme_controller.change_gradient_state)
        self._setting_row(cl1, tr("Resplandor de Fondo"),
                          tr("Muestra un sutil gradiente del color de acento en la ventana principal."),
                          player.switch_gradient)
        player.switch_mini_player_glow = SwitchButton()
        player.switch_mini_player_glow.setChecked(settings.get('mini_player_glow', True))
        def _on_mini_glow_changed(checked):
            settings.set('mini_player_glow', checked)
            settings.save()
            if hasattr(player, '_controls_glow'):
                player._controls_glow.update()
        player.switch_mini_player_glow.checkedChanged.connect(_on_mini_glow_changed)
        self._setting_row(cl1, tr("Resplandor de Controles"),
                          tr("Muestra un aura de luz radial detrás de los controles de la barra de reproducción."),
                          player.switch_mini_player_glow, add_separator=False)
        self.main_layout.addWidget(card1)
        self.main_layout.addSpacing(16)
        card2, cl2 = self._create_card(tr("Interfaz"), FIF.SPEED_OFF)
        player.switch_square_covers = SwitchButton()
        player.switch_square_covers.setChecked(settings.get('square_covers', False))
        def _on_square_covers_changed(checked):
            settings.set('square_covers', checked)
            settings.save()
            player.theme_controller.apply_theme(full_refresh=False)
            player.image_cache.clear()
            player._needs_model_refresh = True
            if hasattr(player, 'queue') and player.queue.tracks and 0 <= player.queue.current_index < len(player.queue.tracks):
                track = player.queue.tracks[player.queue.current_index]
                if hasattr(player, 'playback_ui_controller'):
                    player.playback_ui_controller.update_metadata_ui(track)
            if hasattr(player, 'full_cover') and hasattr(player.full_cover, 'update_cover_style'):
                player.full_cover.update_cover_style()
            if hasattr(player, 'fullscreen_view') and hasattr(player.fullscreen_view, 'cover'):
                if hasattr(player.fullscreen_view.cover, 'update_cover_style'):
                    player.fullscreen_view.cover.update_cover_style()
            try:
                if hasattr(player, 'page_library'):
                    if hasattr(player.page_library, 'list_view_songs'): player.page_library.list_view_songs.viewport().update()
                    if hasattr(player.page_library, 'grid_view_albums'): player.page_library.grid_view_albums.viewport().update()
                if hasattr(player, 'page_playlists'):
                    if hasattr(player.page_playlists, 'grid_view'): player.page_playlists.grid_view.viewport().update()
                    if hasattr(player.page_playlists, 'detail_page'): player.page_playlists.detail_page.update()
            except Exception as e:
                import logging
                logging.debug(f"Error forzando repaint: {e}")
        player.switch_square_covers.checkedChanged.connect(_on_square_covers_changed)
        self._setting_row(cl2, tr("Carátulas Cuadradas"),
                          tr("Desactiva los bordes redondeados en las carátulas de las canciones, álbumes y playlists."),
                          player.switch_square_covers)
        player.combo_scale = ComboBox()
        scales = ["80%", "90%", "100%", "110%", "125%", "150%", "175%", "200%"]
        player.combo_scale.addItems(scales)
        current_scale = str(settings.get('ui_scale', 100)) + "%"
        if current_scale in scales:
            player.combo_scale.setCurrentText(current_scale)
        else:
            player.combo_scale.setCurrentText("100%")
        def _on_scale_changed(text):
            val = int(text.replace("%", ""))
            if val != settings.get('ui_scale', 100):
                settings.set('ui_scale', val)
                settings.save()
                from qfluentwidgets import MessageBox
                import sys, subprocess
                from PyQt6.QtWidgets import QApplication
                w = MessageBox(
                    tr("Reiniciar aplicación"),
                    tr("Para aplicar el nuevo tamaño de la interfaz, es necesario reiniciar la aplicación. ¿Deseas reiniciar ahora?"),
                    self.window()
                )
                w.yesButton.setText(tr("Reiniciar ahora"))
                w.cancelButton.setText(tr("Más tarde"))
                if w.exec():
                    if getattr(sys, 'frozen', False):
                        subprocess.Popen([sys.executable, '--restart'])
                    else:
                        subprocess.Popen([sys.executable] + sys.argv + ['--restart'])
                    QApplication.quit()
        player.combo_scale.currentTextChanged.connect(_on_scale_changed)
        self._setting_row(cl2, tr("Escala de la Interfaz"),
                          tr("Ajusta el tamaño global de la aplicación. Requiere reinicio."), player.combo_scale)
        player.switch_page_anim = SwitchButton()
        player.switch_page_anim.setChecked(settings.get('enable_page_animations', True))
        player.switch_page_anim.checkedChanged.connect(
            lambda checked: (settings.set('enable_page_animations', checked), settings.save())
        )
        self._setting_row(cl2, tr("Animación de transición por desvanecimiento"),
                          tr("Transición de desvanecimiento al cambiar de vista en el reproductor."),
                          player.switch_page_anim)
        player.switch_splash = SwitchButton()
        player.switch_splash.setChecked(settings.get('splash_enabled', True))
        player.switch_splash.checkedChanged.connect(
            lambda checked: settings.set('splash_enabled', checked)
        )
        self._setting_row(cl2, tr("Pantalla de Inicio"),
                          tr("Muestra una pantalla animada con el logo al abrir la aplicación."),
                          player.switch_splash)
        player.switch_dev_welcome = SwitchButton()
        player.switch_dev_welcome.setChecked(settings.get('dev_welcome_always', False))
        player.switch_dev_welcome.checkedChanged.connect(
            lambda checked: (settings.set('dev_welcome_always', checked), settings.save())
        )
        self._setting_row(cl2, tr("Bienvenida al Inicio (Dev)"),
                          tr("Fuerza el panel de bienvenida en cada inicio. Solo para desarrollo."),
                          player.switch_dev_welcome)
        def _update_floating_buttons(checked, key):
            settings.set(key, checked)
            settings.save()
            if hasattr(player, 'page_library') and hasattr(player.page_library, 'songs_tab'):
                if hasattr(player.page_library.songs_tab, 'refresh_floating_buttons'):
                    player.page_library.songs_tab.refresh_floating_buttons()
            if hasattr(player, 'page_favorites'):
                if hasattr(player.page_favorites, 'refresh_floating_buttons'):
                    player.page_favorites.refresh_floating_buttons()
            if hasattr(player, 'page_playlists') and hasattr(player.page_playlists, 'detail_page'):
                if hasattr(player.page_playlists.detail_page, 'refresh_floating_buttons'):
                    player.page_playlists.detail_page.refresh_floating_buttons()
        player.switch_scroll_top = SwitchButton()
        player.switch_scroll_top.setChecked(settings.get('show_scroll_to_top', True))
        player.switch_scroll_top.checkedChanged.connect(lambda c: _update_floating_buttons(c, 'show_scroll_to_top'))
        self._setting_row(cl2, tr("Botón Flotante: Subir al inicio"),
                          tr("Muestra un botón para regresar rápidamente al tope de las listas largas."),
                          player.switch_scroll_top)
        player.switch_locate_track = SwitchButton()
        player.switch_locate_track.setChecked(settings.get('show_locate_track', False))
        player.switch_locate_track.checkedChanged.connect(lambda c: _update_floating_buttons(c, 'show_locate_track'))
        self._setting_row(cl2, tr("Botón Flotante: Ubicar pista"),
                          tr("Muestra un botón dinámico para localizar la canción actual en la lista."),
                          player.switch_locate_track, add_separator=False)
        self.main_layout.addWidget(card2)
        self.main_layout.addSpacing(16)
        card_visual, cl_visual = self._create_card(tr("Experiencia Visual"), FIF.BRUSH)
        player.switch_dynamic_bg = SwitchButton()
        player.switch_dynamic_bg.setChecked(settings.get('dynamic_bg_enabled', True))
        player.switch_dynamic_bg.checkedChanged.connect(player.settings_sync.toggle_dynamic_bg)
        self._setting_row(cl_visual, tr("Colores Dinámicos"),
                          tr("Gradiente inmersivo con los colores de la carátula en el reproductor."),
                          player.switch_dynamic_bg)
        player.switch_smooth_lyrics = SwitchButton()
        player.switch_smooth_lyrics.setChecked(settings.get('smooth_lyrics', True))
        player.switch_smooth_lyrics.checkedChanged.connect(player.settings_ui_controller.toggle_smooth_lyrics)
        self._setting_row(cl_visual, tr("Karaoke Suave"),
                          tr("Anima suavemente el scroll de letras sincronizadas."),
                          player.switch_smooth_lyrics, add_separator=False)
        self.main_layout.addWidget(card_visual)
        self.main_layout.addSpacing(16)
        self.main_layout.addStretch()
