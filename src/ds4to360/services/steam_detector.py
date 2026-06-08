import subprocess
import logging
from gi.repository import GLib, GObject

logger = logging.getLogger(__name__)

class SteamDetector(GObject.Object):
    __gsignals__ = {
        'steam-status-changed': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self, interval_ms=2000):
        GObject.Object.__init__(self)
        self.interval_ms = interval_ms
        self.is_steam_running = False
        self._timeout_id = None

    def start(self):
        self._timeout_id = GLib.timeout_add(self.interval_ms, self._check_steam)
        logger.info("Steam detector started.")

    def _check_steam(self):
        try:
            # Check for steam process
            subprocess.check_output(["pgrep", "-x", "steam"])
            running = True
        except subprocess.CalledProcessError:
            running = False
        except Exception as e:
            logger.error(f"Error checking steam status: {e}")
            running = False

        if running != self.is_steam_running:
            self.is_steam_running = running
            logger.info(f"Steam status changed: {'Running' if running else 'Stopped'}")
            self.emit('steam-status-changed', running)

        return True # Keep timeout running

    def stop(self):
        if self._timeout_id:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None
