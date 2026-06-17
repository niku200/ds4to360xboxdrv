import logging
import sys
import shutil
import os
import re
from PySide6.QtCore import QCoreApplication, QTimer
from loguru import logger
from pnp.core.manager import ControllerManager
from pnp.services.steam_detector import SteamDetector
from pnp.services.game_detector import GameDetector
from pnp.services.profile_downloader import ProfileDownloader

class BackendService:
    def __init__(self):
        self.manager = ControllerManager(write_status=True)

        interval = self.manager.config_manager.config.get('poll_interval_ms', 2000)

        self.steam_detector = SteamDetector(interval_ms=interval)
        self.steam_detector.steam_status_changed.connect(self._on_steam_status_changed)
        self.steam_detector.game_status_changed.connect(self._update_combined_game_status)

        self.game_detector = GameDetector(interval_ms=interval)
        self.game_detector.game_activity_detected.connect(self._update_combined_game_status)

        self.profile_downloader = ProfileDownloader()

    def _on_steam_status_changed(self, running):
        self.manager.set_steam_paused(running)

    def _update_combined_game_status(self, active):
        handover_enabled = self.manager.config_manager.config.get('steam_handover_enabled', True)

        steam_running = self.steam_detector.is_steam_running
        game_present = self.steam_detector.is_game_active or self.game_detector.is_game_detected
        steam_input_ready = self.steam_detector.steam_input_active

        should_handover = handover_enabled and steam_running and game_present and steam_input_ready

        logger.debug(f"Handover eval: Steam={steam_running}, Game={game_present}, SI_Ready={steam_input_ready} -> Handover={should_handover}")
        self.manager.set_game_active(should_handover)

        downloader_enabled = self.manager.config_manager.config.get('profile_downloader_enabled', True)
        if downloader_enabled and game_present and steam_running:
            QTimer.singleShot(0, self._trigger_profile_check)

    def _trigger_profile_check(self):
        try:
            for pid in os.listdir('/proc'):
                if not pid.isdigit(): continue
                try:
                    with open(f'/proc/{pid}/environ', 'rb') as f:
                        env = f.read(4096)
                        if b'SteamAppId=' in env:
                            match = re.search(rb'SteamAppId=(\d+)', env)
                            if match:
                                appid = match.group(1).decode()
                                config = self.profile_downloader.get_best_config(appid)
                                if config:
                                    self.profile_downloader.apply_config(appid, config)
                                    self.profile_downloader.trigger_steam_reload()
                                return
                except: continue
        except: pass

    def check_dependencies(self):
        missing = []
        if not shutil.which('evsieve'):
            missing.append('evsieve')
        try:
            import pyudev
        except ImportError:
            missing.append('python-pyudev')
        return missing

    def run(self):
        missing = self.check_dependencies()
        if missing:
            logger.error(f"Missing system dependencies: {', '.join(missing)}. Exiting.")
            return

        logger.info("Starting pnp backend service...")
        self.manager.start()
        self.steam_detector.start()
        self.game_detector.start()

    def stop(self):
        logger.info("Stopping backend service...")
        self.manager.stop_all()
        self.steam_detector.stop()
        self.game_detector.stop()

def main():
    app = QCoreApplication(sys.argv)
    service = BackendService()
    service.run()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
