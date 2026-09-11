import os
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QPixmap, QDesktopServices, QCursor, QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QFrame, QSizePolicy
from qfluentwidgets import TitleLabel, SubtitleLabel, CaptionLabel, BodyLabel, PushButton, FluentIcon as FIF, MessageBoxBase, IconWidget, TransparentToolButton, SmoothScrollArea
import platform
from config import APP_NAME, APP_VERSION, ICON_FILE
from .base_settings_tab import BaseSettingsTab
from core.language_manager import tr
class ChangelogDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Changelog", self)
        self.textBrowser = QTextBrowser(self)
        self.textBrowser.setReadOnly(True)
        self.textBrowser.setOpenExternalLinks(True)
        self.textBrowser.setMinimumSize(600, 500)
        self.textBrowser.setStyleSheet(
            "QTextBrowser { background: rgba(0, 0, 0, 0.15); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 10px; color: rgba(255, 255, 255, 0.85); font-size: 13px; }"
        )
        content = ""
        try:
            if os.path.exists('CHANGELOG.md'):
                with open('CHANGELOG.md', 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = "No se encontró el archivo CHANGELOG.md."
        except Exception as e:
            content = f"Error al cargar changelog: {e}"
        self.textBrowser.setMarkdown(content)
        self.cancelButton.hide()
        self.yesButton.setText(tr("Cerrar"))
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.textBrowser)
class ThirdPartyDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(tr("Componentes de Terceros"), self)
        self.scroll = SmoothScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll.setMinimumSize(500, 380)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(0)
        lay.setContentsMargins(4, 4, 4, 4)
        terceros = [
            ("BASS Audio Library", "Un4seen Developments", tr("Motor de audio para reproducción, ecualización y procesamiento en tiempo real.")),
            ("PyQt6", "Riverbank Computing", tr("Binding de Python para el framework Qt, base de la interfaz gráfica.")),
            ("PyQt-Fluent-Widgets", "zhiyiYo", tr("Componentes visuales con estilo Fluent Design.")),
            ("Mutagen", "Quod Libet", tr("Lectura y manipulación de metadatos en archivos de audio.")),
            ("SQLite", "D. Richard Hipp", tr("Base de datos relacional integrada para la biblioteca musical.")),
            ("LRCLib API", "tranxuanthang", tr("Búsqueda y descarga automática de letras sincronizadas.")),
            ("Deezer API", "Deezer S.A.", tr("Obtención automática de carátulas en alta resolución.")),
            ("Discord Rich Presence", "Discord Inc.", tr("Actividad de reproducción en tiempo real en Discord.")),
            ("Last.fm API", "Last.fm Ltd.", tr("Scrobbling e historial de escucha."))
        ]
        for i, (name, author, desc) in enumerate(terceros):
            row = QWidget()
            row_l = QVBoxLayout(row)
            row_l.setContentsMargins(12, 10, 12, 10)
            row_l.setSpacing(2)
            header = QHBoxLayout()
            header.setSpacing(0)
            lbl_name = QLabel(f"<b>{name}</b>")
            lbl_name.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.92); background: transparent;")
            lbl_sep = QLabel("  ·  ")
            lbl_sep.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.3); background: transparent;")
            lbl_author = QLabel(author)
            lbl_author.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.45); background: transparent;")
            header.addWidget(lbl_name)
            header.addWidget(lbl_sep)
            header.addWidget(lbl_author)
            header.addStretch()
            lbl_desc = QLabel(desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.5); background: transparent;")
            row_l.addLayout(header)
            row_l.addWidget(lbl_desc)
            lay.addWidget(row)
            if i < len(terceros) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet("color: rgba(255,255,255,0.06);")
                sep.setFixedHeight(1)
                lay.addWidget(sep)
        lay.addStretch()
        self.scroll.setWidget(content)
        self.cancelButton.hide()
        self.yesButton.setText(tr("Cerrar"))
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.scroll)
class LinkRow(QFrame):
    clicked = pyqtSignal()
    def __init__(self, icon_name, title, subtitle, accent, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(56)
        self._icon_name = icon_name
        self._accent = accent
        self._state = "default"
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(16)
        self.icon_widget = IconWidget()
        self.icon_widget.setFixedSize(20, 20)
        self._update_icon()
        lay.addWidget(self.icon_widget, 0, Qt.AlignmentFlag.AlignVCenter)
        text_lay = QVBoxLayout()
        text_lay.setSpacing(2)
        text_lay.setContentsMargins(0, 8, 0, 8)
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: rgba(255,255,255,0.95); font-size: 13px; font-weight: 500; background: transparent;")
        self.lbl_sub = QLabel(subtitle)
        self.lbl_sub.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 11px; background: transparent;")
        text_lay.addWidget(self.lbl_title)
        text_lay.addWidget(self.lbl_sub)
        text_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lay.addLayout(text_lay, 1)
        self.arrow_widget = IconWidget(FIF.SHARE.icon(color=QColor(self._accent)))
        self.arrow_widget.setFixedSize(14, 14)
        lay.addWidget(self.arrow_widget, 0, Qt.AlignmentFlag.AlignVCenter)
    def set_accent(self, accent):
        self._accent = accent
        self._update_icon()
        self.arrow_widget.setIcon(FIF.SHARE.icon(color=QColor(self._accent)))
    def _update_icon(self):
        if isinstance(self._icon_name, str):
            from PyQt6.QtGui import QIcon, QPainter, QColor
            from config import APP_ROOT
            import os
            path = os.path.join(APP_ROOT, 'resources', 'buttons', 'services', f'{self._icon_name}.svg')
            if os.path.exists(path):
                pix = QIcon(path).pixmap(20, 20)
                p = QPainter(pix)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                p.fillRect(pix.rect(), QColor(self._accent))
                p.end()
                self.icon_widget.setIcon(QIcon(pix))
        else:
            from PyQt6.QtGui import QColor
            self.icon_widget.setIcon(self._icon_name.icon(color=QColor(self._accent)))
    def enterEvent(self, e):
        self._state = "hover"
        self.update()
        super().enterEvent(e)
    def leaveEvent(self, e):
        self._state = "default"
        self.update()
        super().leaveEvent(e)
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._state = "pressed"
            self.update()
        super().mousePressEvent(e)
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._state = "hover"
            self.update()
            self.clicked.emit()
        super().mouseReleaseEvent(e)
    def paintEvent(self, e):
        from PyQt6.QtGui import QPainter, QColor
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._state == "hover":
            painter.setBrush(QColor(255, 255, 255, 10))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), 8, 8)
        elif self._state == "pressed":
            painter.setBrush(QColor(255, 255, 255, 5))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), 8, 8)
class DiagnosticLedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self._state = 'green'
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.led_indicator = QWidget()
        self.led_indicator.setFixedSize(10, 10)
        self.lbl_text = QLabel("GP")
        self.lbl_text.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 11px; font-family: monospace; font-weight: bold; letter-spacing: 1px;")
        self.lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.led_indicator, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self.lbl_text, 0, Qt.AlignmentFlag.AlignHCenter)
        self.led_indicator.paintEvent = self._paint_led
    def set_state(self, state):
        self._state = state
        self.led_indicator.update()
    def _paint_led(self, e):
        from PyQt6.QtGui import QPainter, QColor, QRadialGradient
        painter = QPainter(self.led_indicator)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.led_indicator.rect()
        if self._state == 'green':
            color = QColor(34, 197, 94)
        elif self._state == 'yellow':
            color = QColor(234, 179, 8)
        else:      
            color = QColor(239, 68, 68)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect.adjusted(1, 1, -1, -1))
        cx = float(rect.center().x())
        cy = float(rect.center().y())
        grad = QRadialGradient(cx, cy, rect.width()/2)
        grad.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 100))
        grad.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
        painter.setBrush(grad)
        painter.drawEllipse(rect)
class AboutTab(BaseSettingsTab):
    def __init__(self, player, parent=None):
        super().__init__(player, parent)
        accent = self._accent
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        lay.setContentsMargins(0, 30, 0, 30)
        lay.setSpacing(0)
        top_section = QWidget()
        top_lay = QHBoxLayout(top_section)
        top_lay.setSpacing(40)
        top_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_widget = QWidget()
        header_lay = QHBoxLayout(header_widget)
        header_lay.setContentsMargins(0, 0, 0, 0)
        header_lay.setSpacing(24)
        logo_lay = QVBoxLayout()
        logo_lay.setSpacing(6)
        logo_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lay.addWidget(self.icon_label)
        self.diag_led = DiagnosticLedWidget()
        logo_lay.addWidget(self.diag_led, 0, Qt.AlignmentFlag.AlignHCenter)
        header_lay.addLayout(logo_lay)
        self._update_logo()
        info_lay = QVBoxLayout()
        info_lay.setSpacing(6)
        info_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.name_lbl = QLabel(f"<span style='color: #14B8A6;'>Aiiko</span> <span style='color: white;'>Music</span>")
        self.name_lbl.setStyleSheet("font-size: 32px; font-weight: 700; background: transparent;")
        self.name_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        info_lay.addWidget(self.name_lbl)
        version_lbl = QLabel(f"Versión {APP_VERSION}")
        version_lbl.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 13px; font-weight: 500; background: transparent;")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        info_lay.addWidget(version_lbl)
        desc_lbl = QLabel(tr("Reproductor de música local para Windows"))
        desc_lbl.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 13px; background: transparent;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        info_lay.addWidget(desc_lbl)
        header_lay.addLayout(info_lay)
        self.left_col = QWidget()
        left_col_lay = QVBoxLayout(self.left_col)
        left_col_lay.setContentsMargins(0, 0, 0, 0)
        left_col_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_col_lay.addWidget(header_widget)
        self.icons_container = QWidget()
        icons_lay = QHBoxLayout(self.icons_container)
        icons_lay.setContentsMargins(0, 20, 0, 0)
        icons_lay.setSpacing(15)
        icons_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        from qfluentwidgets import ToolButton, TransparentToolButton
        self.btn_web = TransparentToolButton(FIF.GLOBE.icon(color=QColor(accent)))
        self.btn_web.setToolTip("Sitio web")
        self.btn_web.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://hirayamaaiiko.github.io/Aiiko-Music/")))
        self.btn_git = TransparentToolButton(FIF.GITHUB.icon(color=QColor(accent)))
        self.btn_git.setToolTip("GitHub")
        self.btn_git.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/HirayamaAiiko/Aiiko-Music")))
        self.btn_cl = TransparentToolButton(FIF.DOCUMENT.icon(color=QColor(accent)))
        self.btn_cl.setToolTip("Changelog")
        self.btn_cl.clicked.connect(self._show_changelog)
        self.btn_discord = TransparentToolButton(FIF.CHAT.icon(color=QColor(accent)))
        self.btn_discord.setToolTip("Discord")
        self.btn_discord.setEnabled(False)                               
        self._update_discord_icon()
        icons_lay.addWidget(self.btn_web)
        icons_lay.addWidget(self.btn_git)
        icons_lay.addWidget(self.btn_cl)
        icons_lay.addWidget(self.btn_discord)
        self.icons_container.hide()
        left_col_lay.addWidget(self.icons_container)
        top_lay.addWidget(self.left_col, 0, Qt.AlignmentFlag.AlignVCenter)
        self.v_line = QFrame()
        self.v_line.setFrameShape(QFrame.Shape.VLine)
        self.v_line.setStyleSheet("background-color: rgba(255,255,255,0.06); border: none;")
        self.v_line.setFixedWidth(1)
        self.v_line.setMinimumHeight(100)
        top_lay.addWidget(self.v_line, 0, Qt.AlignmentFlag.AlignVCenter)
        self.links_container = QWidget()
        from PyQt6.QtWidgets import QGridLayout
        links_lay = QGridLayout(self.links_container)
        links_lay.setContentsMargins(0, 0, 0, 0)
        links_lay.setSpacing(10)
        self.c1 = LinkRow(FIF.GLOBE, "Sitio web", "hirayamaaiiko.github.io", accent)
        self.c1.setFixedWidth(240)
        self.c1.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://hirayamaaiiko.github.io/Aiiko-Music/")))
        self.c2 = LinkRow(FIF.GITHUB, "GitHub", "Código Fuente", accent)
        self.c2.setFixedWidth(240)
        self.c2.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/HirayamaAiiko/Aiiko-Music")))
        self.c3 = LinkRow(FIF.DOCUMENT, "Changelog", "Registro de versiones", accent)
        self.c3.setFixedWidth(240)
        self.c3.clicked.connect(self._show_changelog)
        self.c4 = LinkRow("discord", "Discord", "Próximamente", accent)
        self.c4.setFixedWidth(240)
        self.c4.setEnabled(False)                               
        self.link_cards = [self.c1, self.c2, self.c3, self.c4]
        links_lay.addWidget(self.c1, 0, 0)
        links_lay.addWidget(self.c2, 0, 1)
        links_lay.addWidget(self.c3, 1, 0)
        links_lay.addWidget(self.c4, 1, 1)
        top_lay.addWidget(self.links_container, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(top_section, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(40)
        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setMaximumWidth(800)
        div2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        div2.setStyleSheet("background-color: rgba(255,255,255,0.06); border: none;")
        lay.addWidget(div2, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(32)
        self.footer_text1 = QLabel(f"Hecho por <span style='color: {accent};'>Hirayama Aiiko</span>")
        self.footer_text1.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 13px;")
        self.footer_text1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.footer_text1, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(16)
        self.heart = IconWidget(FIF.HEART.icon(color=QColor(accent)))
        self.heart.setFixedSize(20, 20)
        lay.addWidget(self.heart, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(16)
        self.footer_text2 = QLabel(f"© 2026 Hirayama Aiiko.<br>Aiiko Music es software libre bajo licencia <span style='color: {accent};'>GPLv3</span>.")
        self.footer_text2.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 12px; line-height: 1.5;")
        self.footer_text2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.footer_text2, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(16)
        self.footer_third_party = QLabel(f"<a href='#terceros' style='color: {accent}; text-decoration: none; font-weight: 500;'>Agradecimientos de Terceros</a>")
        self.footer_third_party.setStyleSheet("font-size: 13px; background: transparent;")
        self.footer_third_party.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_third_party.linkActivated.connect(self._show_third_party)
        self.footer_third_party.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self.footer_third_party, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch()
        self.main_layout.addWidget(container)
        if hasattr(self.player, 'audio_engine') and self.player.audio_engine:
            self.player.audio_engine.track_load_failed.connect(self._set_led_red)
            self.player.audio_engine.error_occurred.connect(self._set_led_red)
    def _set_led_red(self, *args):
        if hasattr(self, 'diag_led'):
            self.diag_led.set_state('red')
    def showEvent(self, e):
        super().showEvent(e)
        from settings_manager import settings
        if hasattr(self, 'diag_led'):
            if self.diag_led._state != 'red':
                if settings.get('crossfade_enabled', False):
                    self.diag_led.set_state('yellow')
                else:
                    self.diag_led.set_state('green')
    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'v_line') and hasattr(self, 'links_container') and hasattr(self, 'icons_container'):
            if self.width() < 800:
                self.v_line.hide()
                self.links_container.hide()
                self.icons_container.show()
            else:
                self.v_line.show()
                self.links_container.show()
                self.icons_container.hide()
    def refresh_theme(self):
        super().refresh_theme()
        accent = self._accent
        if hasattr(self, 'name_lbl'):
            self.name_lbl.setText(f"<span style='color: #14B8A6;'>Aiiko</span> <span style='color: white;'>Music</span>")
        if hasattr(self, 'footer_text1'):
            self.footer_text1.setText(f"Hecho por <span style='color: {accent};'>Hirayama Aiiko</span>")
        if hasattr(self, 'footer_text2'):
            self.footer_text2.setText(f"© 2026 Hirayama Aiiko.<br>Aiiko Music es software libre bajo licencia <span style='color: {accent};'>GPLv3</span>.")
        if hasattr(self, 'footer_third_party'):
            self.footer_third_party.setText(f"<a href='#terceros' style='color: {accent}; text-decoration: none; font-weight: 500;'>Agradecimientos de Terceros</a>")
        if hasattr(self, 'heart'):
            self.heart.setIcon(FIF.HEART.icon(color=QColor(accent)))
        if hasattr(self, 'link_cards'):
            for card in self.link_cards:
                card.set_accent(accent)
        if hasattr(self, 'btn_web'):
            self.btn_web.setIcon(FIF.GLOBE.icon(color=QColor(accent)))
        if hasattr(self, 'btn_git'):
            self.btn_git.setIcon(FIF.GITHUB.icon(color=QColor(accent)))
        if hasattr(self, 'btn_cl'):
            self.btn_cl.setIcon(FIF.DOCUMENT.icon(color=QColor(accent)))
        if hasattr(self, 'btn_discord'):
            self._update_discord_icon()
        if hasattr(self, 'icon_label'):
            self._update_logo()
    def _update_discord_icon(self):
        from PyQt6.QtGui import QIcon, QPainter, QColor
        import os
        from config import APP_ROOT
        discord_path = os.path.join(APP_ROOT, 'resources', 'buttons', 'services', 'discord.svg')
        if os.path.exists(discord_path):
            pix = QIcon(discord_path).pixmap(20, 20)
            p = QPainter(pix)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            p.fillRect(pix.rect(), QColor(self._accent))
            p.end()
            self.btn_discord.setIcon(QIcon(pix))
    def _update_logo(self):
        from config import APP_ROOT
        from PyQt6.QtSvg import QSvgRenderer
        from PyQt6.QtGui import QPainter, QPixmap
        import os
        logo_svg = os.path.join(APP_ROOT, "resources", "app", "logo_full.svg")
        def _fallback():
            if os.path.exists(ICON_FILE):
                self.icon_label.setPixmap(QPixmap(ICON_FILE).scaled(130, 130, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        if os.path.exists(logo_svg):
            svg = QSvgRenderer(logo_svg)
            if svg.isValid():
                pix = QPixmap(130, 130)
                pix.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pix)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                svg.render(painter)
                painter.end()
                self.icon_label.setPixmap(pix)
            else:
                _fallback()
        else:
            _fallback()
    def _show_changelog(self):
        w = ChangelogDialog(self.window())
        w.exec()
    def _show_third_party(self):
        w = ThirdPartyDialog(self.window())
        w.exec()