import os
import sys
import logging
def register_file_associations():
    if sys.platform != 'win32':
        return False
    import winreg
    import ctypes
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen:
        app_path = sys.executable
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        ico_path = os.path.abspath(os.path.join(base_dir, 'resources', 'app', 'audio_file.ico'))
        if not os.path.exists(ico_path):
            ico_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), 'appdata', 'resources', 'app', 'audio_file.ico'))
    else:
        app_path = os.path.abspath(sys.argv[0])
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ico_path = os.path.join(base_dir, 'resources', 'app', 'audio_file.ico')
    if not os.path.exists(ico_path):
        logging.warning(f"File Association: No se encontro el icono personalizado en {ico_path}. Se usara el de la app.")
        ico_path = app_path
    prog_id = "AiikoMusic.AudioFile"
    prog_id_desc = "Aiiko Music Audio File"
    extensions = ['.mp3', '.flac', '.wav', '.ogg', '.m4a']
    if is_frozen:
        command = f'"{app_path}" "%1"'
    else:
        command = f'"{sys.executable}" "{app_path}" "%1"'
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{prog_id}") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, prog_id_desc)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{prog_id}\DefaultIcon") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, f'"{ico_path}",0')
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{prog_id}\shell\open\command") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, command)
        for ext in extensions:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{ext}") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, prog_id)
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000
        ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
        logging.info("Asociacion de archivos registrada con exito en HKCU.")
        return True
    except Exception as e:
        logging.error(f"Error registrando asociacion de archivos: {e}")
        return False