import sys
from core.app_bootstrapper import AppBootstrapper
if __name__ == "__main__":
    bootstrapper = AppBootstrapper()
    bootstrapper.run_pre_app_initialization()
    bootstrapper.setup_app_environment()
    bootstrapper.show_splash_screen()
    bootstrapper.update_splash(10)
    bootstrapper.update_splash(35)
    from UI.main_window import MusicPlayer
    bootstrapper.update_splash(80)
    player = MusicPlayer(bootstrapper)
    if bootstrapper.instance_mgr:
        from PyQt6.QtCore import Qt
        bootstrapper.instance_mgr.file_received.connect(
            player.handle_external_file,
            Qt.ConnectionType.QueuedConnection
        )
    bootstrapper.update_splash(95)
    bootstrapper.setup_cleanup(player)
    bootstrapper.close_splash(player)
    bootstrapper.register_aumid()
    sys.exit(bootstrapper.app_instance.exec())
