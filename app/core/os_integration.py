import sys
import os
import logging
SUPPORTED_EXTENSIONS = ('.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac')
SUPPORTED_DATA_EXTENSIONS = ('.aiiko',)
PROG_ID = 'AiikoMusic.Player'
APP_NAME = 'Aiiko Music'
def _get_exe_path() -> str:
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(sys.argv[0])
def register_file_associations(exe_path: str = None):
    import sys
    if sys.platform != 'win32':
        return False
    if not exe_path:
        exe_path = _get_exe_path()
    try:
        import winreg
        prog_key_path = f'Software\\Classes\\{PROG_ID}'
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, prog_key_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, '', 0, winreg.REG_SZ, 'Aiiko Music Audio File')
            winreg.SetValueEx(key, 'FriendlyTypeName', 0, winreg.REG_SZ, 'Aiiko Music Audio File')
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, f'{prog_key_path}\\DefaultIcon', 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, '', 0, winreg.REG_SZ, f'"{exe_path}",0')
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, f'{prog_key_path}\\shell\\open\\command', 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, '', 0, winreg.REG_SZ, f'"{exe_path}" "%1"')
        from config import RESOURCES_DIR
        filetypes_dir = os.path.join(RESOURCES_DIR, 'filetypes')
        ALL_EXTENSIONS = SUPPORTED_EXTENSIONS + SUPPORTED_DATA_EXTENSIONS
        for ext in ALL_EXTENSIONS:
            ext_upper = ext[1:].upper()
            ext_prog_id = f'{PROG_ID}.{ext_upper}'
            if ext in SUPPORTED_DATA_EXTENSIONS:
                friendly_name = f'Aiiko Music Backup File'
            else:
                friendly_name = f'Aiiko Music {ext_upper} Audio File'
            ext_prog_key_path = f'Software\\Classes\\{ext_prog_id}'
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, ext_prog_key_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, '', 0, winreg.REG_SZ, friendly_name)
                winreg.SetValueEx(key, 'FriendlyTypeName', 0, winreg.REG_SZ, friendly_name)
            specific_icon_path = os.path.join(filetypes_dir, f'aiiko_filetype_{ext[1:].lower()}.ico')
            if os.path.exists(specific_icon_path):
                icon_string = f'"{specific_icon_path}",0'
            else:
                icon_string = f'"{exe_path}",0'
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, f'{ext_prog_key_path}\\DefaultIcon', 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, '', 0, winreg.REG_SZ, icon_string)
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, f'{ext_prog_key_path}\\shell\\open\\command', 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, '', 0, winreg.REG_SZ, f'"{exe_path}" "%1"')
            openwith_key_path = f'Software\\Classes\\{ext}\\OpenWithProgids'
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, openwith_key_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, ext_prog_id, 0, winreg.REG_SZ, '')
        import ctypes
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        toast_key = 'Software\\Microsoft\\Windows\\CurrentVersion\\ApplicationAssociationToasts'
        try:
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, toast_key, 0, winreg.KEY_WRITE) as key:
                for ext in ALL_EXTENSIONS:
                    ext_upper = ext[1:].upper()
                    ext_prog_id = f'{PROG_ID}.{ext_upper}'
                    winreg.SetValueEx(key, f'{ext_prog_id}{ext}', 0, winreg.REG_DWORD, 0)
        except Exception:
            pass
        app_reg_key = f'Software\\{APP_NAME}\\Capabilities'
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, app_reg_key, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, 'ApplicationName', 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, 'ApplicationDescription', 0, winreg.REG_SZ, 'Reproductor de música con motor BASS y gapless playback')
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, f'{app_reg_key}\\FileAssociations', 0, winreg.KEY_WRITE) as key:
            for ext in ALL_EXTENSIONS:
                ext_upper = ext[1:].upper()
                ext_prog_id = f'{PROG_ID}.{ext_upper}'
                winreg.SetValueEx(key, ext, 0, winreg.REG_SZ, ext_prog_id)
        reg_apps_key = 'Software\\RegisteredApplications'
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, reg_apps_key, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'Software\\{APP_NAME}\\Capabilities')
        logging.info(f"OS Integration: Asociaciones de archivo registradas para {len(SUPPORTED_EXTENSIONS)} extensiones.")
        return True
    except Exception as e:
        logging.error(f"OS Integration: Error registrando asociaciones: {e}")
        return False
def register_context_menu(exe_path: str = None):
    if sys.platform != 'win32':
        return False
    if not exe_path:
        exe_path = _get_exe_path()
    try:
        import winreg
        from core.language_manager import tr
        for ext in SUPPORTED_EXTENSIONS:
            ext_key_base = f'Software\\Classes\\SystemFileAssociations\\{ext}'
            play_key = f'{ext_key_base}\\shell\\AiikoPlay'
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, play_key, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, '', 0, winreg.REG_SZ, tr('Reproducir con Aiiko Music'))
                winreg.SetValueEx(key, 'Icon', 0, winreg.REG_SZ, f'"{exe_path}",0')
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, f'{play_key}\\command', 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, '', 0, winreg.REG_SZ, f'"{exe_path}" --play "%1"')
            play_next_key = f'{ext_key_base}\\shell\\AiikoPlayNext'
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, play_next_key, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, '', 0, winreg.REG_SZ, tr('Añadir a continuación'))
                winreg.SetValueEx(key, 'Icon', 0, winreg.REG_SZ, f'"{exe_path}",0')
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, f'{play_next_key}\\command', 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, '', 0, winreg.REG_SZ, f'"{exe_path}" --play-next "%1"')
            enqueue_end_key = f'{ext_key_base}\\shell\\AiikoEnqueueEnd'
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, enqueue_end_key, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, '', 0, winreg.REG_SZ, tr('Añadir al final'))
                winreg.SetValueEx(key, 'Icon', 0, winreg.REG_SZ, f'"{exe_path}",0')
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, f'{enqueue_end_key}\\command', 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, '', 0, winreg.REG_SZ, f'"{exe_path}" --enqueue-end "%1"')
        logging.info("OS Integration: Menú contextual registrado correctamente.")
        return True
    except Exception as e:
        logging.error(f"OS Integration: Error registrando menú contextual: {e}")
        return False
def set_as_default(exe_path: str = None):
    if sys.platform != 'win32':
        return False
    if not exe_path:
        exe_path = _get_exe_path()
    register_file_associations(exe_path)
    try:
        import subprocess
        subprocess.Popen(['cmd', '/c', 'start', 'ms-settings:defaultapps'], 
                        creationflags=0x08000000)                    
        logging.info("OS Integration: Panel de aplicaciones predeterminadas abierto.")
        return True
    except Exception as e:
        logging.error(f"OS Integration: Error abriendo panel de defaults: {e}")
        return False
def unregister_all():
    if sys.platform != 'win32':
        return False
    try:
        import winreg
        def _delete_key_recursive(root, path):
            try:
                with winreg.OpenKeyEx(root, path, 0, winreg.KEY_READ) as key:
                    while True:
                        try:
                            subkey = winreg.EnumKey(key, 0)
                            _delete_key_recursive(root, f'{path}\\{subkey}')
                        except OSError:
                            break
                winreg.DeleteKey(root, path)
            except FileNotFoundError:
                pass
            except Exception as e:
                logging.debug(f"OS Integration: No se pudo eliminar {path}: {e}")
        _delete_key_recursive(winreg.HKEY_CURRENT_USER, f'Software\\Classes\\{PROG_ID}')
        _delete_key_recursive(winreg.HKEY_CURRENT_USER, 'Software\\Classes\\AiikoMusic.AudioFile')
        ALL_EXTENSIONS = SUPPORTED_EXTENSIONS + SUPPORTED_DATA_EXTENSIONS
        for ext in ALL_EXTENSIONS:
            ext_upper = ext[1:].upper()
            ext_prog_id = f'{PROG_ID}.{ext_upper}'
            _delete_key_recursive(winreg.HKEY_CURRENT_USER, f'Software\\Classes\\{ext_prog_id}')
            try:
                ext_key_path = f'Software\\Classes\\{ext}\\OpenWithProgids'
                with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, ext_key_path, 0, winreg.KEY_WRITE) as key:
                    try:
                        winreg.DeleteValue(key, ext_prog_id)
                    except FileNotFoundError:
                        pass
                    try:
                        winreg.DeleteValue(key, PROG_ID)
                    except FileNotFoundError:
                        pass
            except FileNotFoundError:
                pass
        for ext in SUPPORTED_EXTENSIONS:
            ext_key_base = f'Software\\Classes\\SystemFileAssociations\\{ext}\\shell'
            _delete_key_recursive(winreg.HKEY_CURRENT_USER, f'{ext_key_base}\\AiikoPlay')
            _delete_key_recursive(winreg.HKEY_CURRENT_USER, f'{ext_key_base}\\AiikoEnqueue')
            _delete_key_recursive(winreg.HKEY_CURRENT_USER, f'{ext_key_base}\\AiikoPlayNext')
            _delete_key_recursive(winreg.HKEY_CURRENT_USER, f'{ext_key_base}\\AiikoEnqueueEnd')
        _delete_key_recursive(winreg.HKEY_CURRENT_USER, f'Software\\{APP_NAME}')
        try:
            with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, 'Software\\RegisteredApplications', 0, winreg.KEY_WRITE) as key:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        except FileNotFoundError:
            pass
        try:
            toast_key = 'Software\\Microsoft\\Windows\\CurrentVersion\\ApplicationAssociationToasts'
            with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, toast_key, 0, winreg.KEY_WRITE) as key:
                ALL_EXTENSIONS = SUPPORTED_EXTENSIONS + SUPPORTED_DATA_EXTENSIONS
                for ext in ALL_EXTENSIONS:
                    ext_upper = ext[1:].upper()
                    ext_prog_id = f'{PROG_ID}.{ext_upper}'
                    try:
                        winreg.DeleteValue(key, f'{ext_prog_id}{ext}')
                    except FileNotFoundError:
                        pass
                    try:
                        winreg.DeleteValue(key, f'{PROG_ID}{ext}')
                    except FileNotFoundError:
                        pass
        except FileNotFoundError:
            pass
        logging.info("OS Integration: Todas las claves del registro han sido eliminadas.")
        return True
    except Exception as e:
        logging.error(f"OS Integration: Error desregistrando: {e}")
        return False
def is_registered() -> bool:
    if sys.platform != 'win32':
        return False
    try:
        import winreg
        winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, f'Software\\Classes\\{PROG_ID}', 0, winreg.KEY_READ)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False