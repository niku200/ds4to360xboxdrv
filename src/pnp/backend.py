import logging
import sys
import shutil
import os
import re
from gi.repository import GLib
from pnp.core.manager import ControllerManager
from pnp.services.steam_detector import SteamDetector
from pnp.services.game_detector import GameDetector
from pnp.services.profile_downloader import ProfileDownloader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackendService:
    def __init__(self):
        self.manager = ControllerManager(write_status=True)

        # Get polling interval from config
        interval = int(self.manager.config_manager.config.get('settings', 'polling_interval_ms', fallback='2000'))

        self.steam_detector = SteamDetector(interval_ms=interval)
        self.steam_detector.connect('steam-status-changed', self._on_steam_status_changed)
        self.steam_detector.connect('game-status-changed', self._update_combined_game_status)

        self.game_detector = GameDetector(interval_ms=interval)
        self.game_detector.connect('game-activity-detected', self._update_combined_game_status)

        self.profile_downloader = ProfileDownloader()

        self.loop = GLib.MainLoop()

    def _on_steam_status_changed(self, detector, running):
        self.manager.set_steam_paused(running)

    def _update_combined_game_status(self, detector, active):
        # Combine status from both detectors to avoid flapping
        # Logic:
        # 1. Steam MUST be running.
        # 2. Any detector finds a game process.
        # 3. Steam Input is engaged (virtual device detected).
        # IF SteamRunning AND (SteamGame OR NonSteamGame) AND SteamInputEngaged -> Pause PNP.

        steam_running = self.steam_detector.is_steam_running
        game_present = self.steam_detector.is_game_active or self.game_detector.is_game_detected
        steam_input_ready = self.steam_detector.steam_input_active

        should_handover = steam_running and game_present and steam_input_ready

        logger.debug(f"Handover eval: Steam={steam_running}, Game={game_present}, SI_Ready={steam_input_ready} -> Handover={should_handover}")
        self.manager.set_game_active(should_handover)

        # Profile Downloader Integration
        if game_present and steam_running:
            # We don't have the path here easily from signals,
            # but we can try to detect it if the detector provides more info.
            # For now, trigger a generic check.
            GLib.idle_add(self._trigger_profile_check)

    def _trigger_profile_check(self):
        # Search for a running game and try to find its AppID
        try:
            for pid in os.listdir('/proc'):
                if not pid.isdigit(): continue
                try:
                    with open(f'/proc/{pid}/environ', 'rb') as f:
                        env = f.read(4096)
                        if b'SteamAppId=' in env:
                            # Found a Steam game!
                            match = re.search(b'SteamAppId=(\d+)', env)
                            if match:
                                appid = match.group(1).decode()
                                config = self.profile_downloader.get_best_config(appid)
                                if config:
                                    self.profile_downloader.apply_config(appid, config)
                                    self.profile_downloader.trigger_steam_reload()
                                return False # Stop search
                except: continue
        except: pass
        return False

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
        try:
            self.loop.run()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.critical(f"Critical error in backend service: {e}", exc_info=True)

    def stop(self):
        logger.info("Stopping backend service...")
        self.manager.stop_all()
        self.steam_detector.stop()
        self.game_detector.stop()
        self.loop.quit()

def main():
    service = BackendService()
    service.run()

if __name__ == "__main__":
    main()
