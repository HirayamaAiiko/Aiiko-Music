import sys
import os
import time
import json
import logging
from config import SETTINGS_FILE
from core.single_instance import SingleInstanceManager
from core.language_manager import lang_manager, tr
from settings_manager import settings
class AppBootstrapper:
    def __init__(self):
        self.app_start_time = time.time()
        self.app_root = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.ext_filepath = None
        self.ext_action = None
        self.fast_audio_engine = None
        self.splash = None
        self.app_instance = None
        self.instance_mgr = None
    def _parse_arguments(self, argv):
        args = argv[1:]
        if not args: return None, None
        action = "play"
        filepath = None
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == '--play':
                action = "play"
                if i + 1 < len(args): filepath = args[i + 1]; i += 1
            elif arg in ('--enqueue', '--enqueue-end'):
                action = "enqueue-end"
                if i + 1 < len(args): filepath = args[i + 1]; i += 1
            elif arg == '--play-next':
                action = "play-next"
                if i + 1 < len(args): filepath = args[i + 1]; i += 1
            elif not arg.startswith('-'):
                filepath = arg
            i += 1
        if filepath:
            filepath = os.path.abspath(filepath)
            if os.path.isfile(filepath): return filepath, action
        return None, None
    def _set_high_priority(self):
        if sys.platform == 'win32':
            try:
                import psutil
                p = psutil.Process(os.getpid())
                p.nice(psutil.HIGH_PRIORITY_CLASS)
                logging.info("Prioridad de proceso elevada a HIGH_PRIORITY_CLASS para proteger el audio de cortes.")
            except Exception as e:
                logging.warning(f"No se pudo elevar la prioridad del proceso: {e}")
    def _setup_excepthook(self):
        def my_excepthook(type, value, tback):
            import traceback
            try:
                logging.error(f"Uncaught exception:\n{''.join(traceback.format_exception(type, value, tback))}")
            except:
                pass
            sys.__excepthook__(type, value, tback)
        sys.excepthook = my_excepthook
    def _configure_ui_scaling(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    if 'ui_scale' in d:
                        if d['ui_scale'] != 100:
                            os.environ["QT_SCALE_FACTOR"] = str(d['ui_scale'] / 100.0)
                        else:
                            os.environ.pop("QT_SCALE_FACTOR", None)
        except Exception:
            pass
    def run_pre_app_initialization(self):
        self._setup_excepthook()
        self._configure_ui_scaling()
        from PyQt6.QtWidgets import QApplication
        self._set_high_priority()
        self.app_instance = QApplication.instance()
        if not self.app_instance:
            self.app_instance = QApplication(sys.argv)
        self.ext_filepath, self.ext_action = self._parse_arguments(sys.argv)
        self.instance_mgr = SingleInstanceManager()
        is_restart = '--restart' in sys.argv
        if is_restart:
            sys.argv.remove('--restart')
        started = False
        if is_restart:
            for _ in range(40):
                if self.instance_mgr.try_start():
                    started = True
                    break
                time.sleep(0.1)
        if not started and not self.instance_mgr.try_start():
            if self.ext_filepath:
                self.instance_mgr.send_to_running_instance(self.ext_filepath, self.ext_action or "play")
            sys.exit(0)
        if self.ext_filepath:
            if self.ext_filepath.lower().endswith('.aiiko'):
                logging.info("Archivo .aiiko detectado en el inicio, omitiendo fast-play.")
            else:
                try:
                    from player_engine import AudioEngine
                    self.fast_audio_engine = AudioEngine()
                    self.fast_audio_engine.initialize()
                    self.fast_audio_engine.play_file(self.ext_filepath)
                except Exception as e:
                    pass
        lang_manager.load_language(settings.get('language', 'es'))
    def show_splash_screen(self):
        if settings.get('splash_enabled', True):
            from UI.splash_screen import SplashScreen
            self.splash = SplashScreen()
            self.splash.show()
            self.app_instance.processEvents()
    def update_splash(self, progress, text=""):
        if self.splash:
            self.splash.set_progress(progress, text)
            self.app_instance.processEvents()
    def close_splash(self, main_window):
        if self.splash:
            self.splash.finish(main_window)
            self.splash = None
    def register_aumid(self):
        if sys.platform == 'win32':
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Aiiko Music')
                import threading
                def _create_aumid_shortcut():
                    try:
                        import win32com.client
                        from win32com.propsys import propsys, pscon
                        from win32com.shell import shellcon
                        import pythoncom
                        pythoncom.CoInitialize()
                        shell = win32com.client.Dispatch("WScript.Shell")
                        programs_path = shell.SpecialFolders("Programs")
                        shortcut_path = os.path.join(programs_path, "Aiiko Music.lnk")
                        needs_update = True
                        if os.path.exists(shortcut_path):
                            try:
                                existing_shortcut = shell.CreateShortcut(shortcut_path)
                                if existing_shortcut.TargetPath == sys.executable:
                                    needs_update = False
                            except:
                                pass
                        if needs_update or not os.path.exists(shortcut_path):
                            FILE_ATTRIBUTE_NORMAL = 0x80
                            shortcut = shell.CreateShortcut(shortcut_path)
                            shortcut.TargetPath = sys.executable
                            shortcut.WorkingDirectory = os.path.dirname(sys.executable)
                            shortcut.IconLocation = sys.executable
                            shortcut.Save()
                            import pythoncom
                            from win32com.shell import shell
                            from win32com.propsys import propsys, pscon
                            pk = propsys.PSGetPropertyKeyFromName("System.AppUserModel.ID")
                            ps = propsys.SHGetPropertyStoreFromParsingName(shortcut_path, None, shellcon.GPS_READWRITE, propsys.IID_IPropertyStore)
                            prop = propsys.PROPVARIANTType("Aiiko Music")
                            ps.SetValue(pk, prop)
                            ps.Commit()
                    except Exception as e:
                        logging.warning(f"No se pudo crear el acceso directo AUMID: {e}")
                threading.Thread(target=_create_aumid_shortcut, daemon=True).start()
            except Exception as e:
                logging.warning(f"No se pudo configurar AppUserModelID: {e}")
    def setup_app_environment(self):
        from PyQt6.QtCore import qInstallMessageHandler, QtMsgType, Qt
        from PyQt6.QtGui import QPalette, QColor, QFontDatabase, QFont
        import glob
        def qt_message_handler(mode, context, message):
            if "OpenType support missing for" in message: return
            if "QFont::setPointSize: Point size <= 0" in message: return
            if mode == QtMsgType.QtWarningMsg: logging.warning(f"Qt: {message}")
            elif mode == QtMsgType.QtCriticalMsg: logging.error(f"Qt Critical: {message}")
            elif mode == QtMsgType.QtFatalMsg: logging.critical(f"Qt Fatal: {message}")
        qInstallMessageHandler(qt_message_handler)
        self.app_instance.setApplicationName("Aiiko Music")
        self.app_instance.setApplicationDisplayName("Aiiko Music")
        dark_palette = self.app_instance.palette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor("#141414"))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor("#141414"))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        self.app_instance.setPalette(dark_palette)
        font_dir = os.path.join(self.app_root, 'resources', 'fonts')
        font_family = None
        if os.path.exists(font_dir):
            for font_file in glob.glob(os.path.join(font_dir, '*.ttf')):
                font_id = QFontDatabase.addApplicationFont(font_file)
                if font_id != -1 and not font_family:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families: font_family = families[0]
        if font_family:
            custom_font = QFont(font_family)
            custom_font.setPixelSize(14)
            self.app_instance.setFont(custom_font)
            try:
                from qfluentwidgets import qconfig
                qconfig.set(qconfig.fontFamilies, [font_family, "Segoe UI"])
            except Exception:
                pass
            logging.info(f"Fuente global aplicada exitosamente: {font_family}")
        else:
            logging.warning("No se encontró ninguna font_family válida en resources/fonts")
    def setup_cleanup(self, player):
        def global_cleanup():
            logging.info("Ejecutando limpieza global de recursos antes de salir...")
            try:
                if getattr(player, 'library_manager', None): player.library_manager.stop_all()
                if getattr(player, 'audio_engine', None): 
                    player.audio_engine.stop()
                    if hasattr(player.audio_engine, 'cleanup'):
                        player.audio_engine.cleanup()
                if getattr(player, 'system_manager', None):
                    try: player.system_manager.cleanup()
                    except Exception: pass
                if getattr(player, 'remote_server', None):
                    try: player.remote_server.stop()
                    except Exception: pass
                if getattr(player, 'image_loader', None):
                    try: 
                        player.image_loader.running = False
                        player.image_loader.wait(500)
                    except Exception: pass
            except Exception: pass
            if self.instance_mgr: self.instance_mgr.shutdown()
        self.app_instance.aboutToQuit.connect(global_cleanup)