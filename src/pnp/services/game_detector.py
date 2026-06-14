import os
import logging
import re
from gi.repository import GLib, GObject

logger = logging.getLogger(__name__)

class GameDetector(GObject.Object):
    """
    Detects non-Steam games by looking for common game libraries
    and execution patterns in /proc.
    """
    __gsignals__ = {
        'game-activity-detected': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    # Libraries common in games
    GAME_LIBS = [
        'libSDL2-',
        'libSDL-',
        'libopenal.so',
        'libGL.so',
        'libvulkan.so',
        'libwine.so', # Wine/Proton
    ]

    # Processes to ignore (browsers, etc. that might use GL)
    IGNORE_PROCS = [
        'firefox',
        'chrome',
        'chromium',
        'electron',
        'gnome-shell',
        'Xorg',
        'wayland',
        'pnp',
    ]

    def __init__(self, interval_ms=2000):
        GObject.Object.__init__(self)
        self.interval_ms = interval_ms
        self.is_game_detected = False
        self._timeout_id = None

    def start(self):
        self._timeout_id = GLib.timeout_add(self.interval_ms, self._check_activity)
        logger.info("Non-Steam game detector started.")

    def _check_activity(self):
        detected = self._scan_procs()

        if detected != self.is_game_detected:
            self.is_game_detected = detected
            logger.info(f"Non-Steam game activity: {'Detected' if detected else 'None'}")
            self.emit('game-activity-detected', detected)

        return True

    def _scan_procs(self):
        try:
            # Get list of PIDs and filter early
            pids = [d for d in os.listdir('/proc') if d.isdigit()]
            my_uid = os.getuid()

            for pid in pids:
                pid_int = int(pid)
                if pid_int == os.getpid() or pid_int < 100:
                    continue

                try:
                    # Optimization: Only check processes owned by current user
                    stat_info = os.stat(f'/proc/{pid}')
                    if stat_info.st_uid != my_uid and my_uid != 0:
                        continue

                    # Check comm (process name)
                    with open(f'/proc/{pid}/comm', 'r') as f:
                        comm = f.read().strip()
                        if any(ignore in comm for ignore in self.IGNORE_PROCS):
                            continue

                    # Check maps for game libraries
                    with open(f'/proc/{pid}/maps', 'r') as f:
                        for line in f:
                            if any(lib in line for lib in self.GAME_LIBS):
                                # Additional heuristic: is it in a common game directory?
                                if any(x in line for x in ['Games', 'SteamLibrary', 'lutris', 'heroic', 'wine']):
                                     return True
                                # If it's a standalone executable in home dir using SDL/GL
                                if '/home/' in line and '.so' not in line and ' ' not in line:
                                    # This might be the executable itself
                                    pass
                except (PermissionError, FileNotFoundError):
                    continue
        except Exception as e:
            logger.error(f"Error in GameDetector scan: {e}")

        return False

    def stop(self):
        if self._timeout_id:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None
