from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog
from qfluentwidgets import FluentIcon as FIF, RoundMenu, Action
from settings_manager import settings
from UI.lyrics_editor import LyricsEditorDialog
from core.language_manager import tr
class LyricsUIController:
    def __init__(self, main_window):
        self.mw = main_window
        import threading
        threading.Thread(target=self._preload_modules, daemon=True).start()
    def _preload_modules(self):
        try:
            from UI.dialogs.custom_timer_dialog import CustomTimerDialog
        except Exception:
            pass
    def toggle_lyrics_translation(self):
        mw = self.mw
        if not hasattr(mw, 'lyrics_manager') or not mw.lyrics_manager:
            return
        if not hasattr(mw.lyrics_manager, 'display_mode'):
            mw.lyrics_manager.display_mode = 'original'
        accent = mw.ACCENT_COLORS.get(settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954')
        if mw.lyrics_manager.display_mode == 'original':
            mw.lyrics_manager.display_mode = 'dual'
            mw.playback_ui_controller.update_tool_btn_state(mw.btn_translate_lyrics, "translate_lyrics.svg", FIF.LANGUAGE, accent)
            mw.btn_translate_lyrics.setToolTip(tr("Mostrando Traducción"))
        elif mw.lyrics_manager.display_mode == 'dual':
            mw.lyrics_manager.display_mode = 'translated'
            mw.playback_ui_controller.update_tool_btn_state(mw.btn_translate_lyrics, "translate_lyrics.svg", FIF.LANGUAGE, '#FFB900')
            mw.btn_translate_lyrics.setToolTip(tr("Solo Traducción"))
        else:
            mw.lyrics_manager.display_mode = 'original'
            mw.playback_ui_controller.update_tool_btn_state(mw.btn_translate_lyrics, "translate_lyrics.svg", FIF.LANGUAGE, '#FFFFFF')
            mw.btn_translate_lyrics.setToolTip(tr("Traducir Letras"))
        mw.lyrics_manager.update_display()
    def toggle_lyrics(self):
        mw = self.mw
        mw.show_lyrics = not mw.show_lyrics
        settings.set('now_playing_lyrics_visible', mw.show_lyrics)
        mw.lyrics_panel.setVisible(mw.show_lyrics)
        if mw.show_lyrics:
            accent = mw.ACCENT_COLORS.get(settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954')
            mw.playback_ui_controller.update_tool_btn_state(mw.btn_lyrics_toggle, "hide_lyrics.svg", FIF.ALIGNMENT, accent)
            mw.btn_lyrics_toggle.setToolTip(tr("Ocultar Letras"))
        else:
            mw.playback_ui_controller.update_tool_btn_state(mw.btn_lyrics_toggle, "hide_lyrics.svg", FIF.ALIGNMENT, '#FFFFFF')
            mw.btn_lyrics_toggle.setToolTip(tr("Mostrar Letras"))
    def open_lyrics_editor(self):
        mw = self.mw
        if mw.queue.current_index < 0 or not mw.queue.tracks:
            return
        track = mw.queue.tracks[mw.queue.current_index]
        editor = LyricsEditorDialog(track, mw)
        if editor.exec() == QDialog.DialogCode.Accepted:
            if mw.lyrics_manager:
                mw.lyrics_manager.load(track)
    def show_timer_menu(self):
        mw = self.mw
        menu = RoundMenu(parent=mw)
        active_preset = mw.sleep_timer_controller.get_active_preset() if hasattr(mw, 'sleep_timer_controller') else None
        from config import ICON_TIMER
        from PyQt6.QtGui import QIcon, QPixmap
        from PyQt6.QtCore import Qt
        empty_pix = QPixmap(16, 16)
        empty_pix.fill(Qt.GlobalColor.transparent)
        empty_icon = QIcon(empty_pix)
        def add_preset(text, preset_id, func):
            act = Action(tr(text))
            if active_preset == preset_id:
                accent = mw.ACCENT_COLORS.get(settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954')
                act.setIcon(FIF.ACCEPT.icon(color=accent))
            else:
                act.setIcon(empty_icon)
            act.triggered.connect(func)
            menu.addAction(act)
        add_preset("Apagar en 5 min", "time_5", lambda: mw.sleep_timer_controller.set_time_timer(5))
        add_preset("Apagar en 15 min", "time_15", lambda: mw.sleep_timer_controller.set_time_timer(15))
        add_preset("Apagar tras 1 Canción", "song_1", lambda: mw.sleep_timer_controller.set_song_timer(1))
        add_preset("Apagar tras 5 Canciones", "song_5", lambda: mw.sleep_timer_controller.set_song_timer(5))
        is_custom_active = active_preset and active_preset not in ["time_5", "time_15", "song_1", "song_5"]
        if is_custom_active:
            if active_preset.startswith("time_"):
                val = active_preset.split("_")[1]
                custom_text = f"Apagar en {val} min (Personalizado)"
            else:
                val = active_preset.split("_")[1]
                custom_text = f"Apagar tras {val} Canciones (Personalizado)"
            act_custom = Action(tr(custom_text))
            accent = mw.ACCENT_COLORS.get(settings.get('app_accent_name', 'Teal (AIIKO)'), '#1DB954')
            act_custom.setIcon(FIF.ACCEPT.icon(color=accent))
            act_custom.triggered.connect(self._show_custom_timer)
            menu.addAction(act_custom)
        else:
            act_custom = Action(tr("Personalizado..."), triggered=self._show_custom_timer)
            act_custom.setIcon(empty_icon)
            menu.addAction(act_custom)
        menu.addSeparator()
        act_disable = Action(tr("Desactivar"))
        act_disable.setIcon(empty_icon)
        act_disable.triggered.connect(mw.sleep_timer_controller.clear_timer)
        menu.addAction(act_disable)
        pos = mw.btn_timer.mapToGlobal(mw.btn_timer.rect().bottomLeft())
        menu.exec(pos)
    def _show_custom_timer(self):
        from PyQt6.QtCore import QTimer
        def _do_open():
            from UI.dialogs.custom_timer_dialog import CustomTimerDialog
            dialog = CustomTimerDialog(self.mw)
            if dialog.exec():
                mode, value = dialog.get_result()
                if mode == "time":
                    self.mw.sleep_timer_controller.set_time_timer(value)
                elif mode == "song":
                    self.mw.sleep_timer_controller.set_song_timer(value)
        QTimer.singleShot(100, _do_open)