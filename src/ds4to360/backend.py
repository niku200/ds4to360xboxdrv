import logging
import sys
import shutil
from gi.repository import GLib
from ds4to360.core.manager import ControllerManager
from ds4to360.services.steam_detector import SteamDetector

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
        self.steam_detector = SteamDetector()
        self.steam_detector.connect('steam-status-changed', self._on_steam_status_changed)

        self.loop = GLib.MainLoop()

    def _on_steam_status_changed(self, detector, running):
        self.manager.set_steam_paused(running)

    def check_dependencies(self):
        missing = []
        if not shutil.which('xboxdrv'):
            missing.append('xboxdrv')
        if not shutil.which('evsieve'):
            missing.append('evsieve')
        return missing

    def run(self):
        missing = self.check_dependencies()
        if missing:
            logger.error(f"Missing system dependencies: {', '.join(missing)}. Exiting.")
            return

        logger.info("Starting ds4to360 backend service...")
        self.manager.start()
        self.steam_detector.start()
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
        self.loop.quit()

def main():
    service = BackendService()
    service.run()

if __name__ == "__main__":
    main()
