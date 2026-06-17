import os
import re
from PySide6.QtCore import QObject, Signal, QTimer
from loguru import logger

class GameDetector(QObject):
    game_activity_detected = Signal(bool)

    GAME_LIBS = [
        'libSDL2-',
        'libSDL-',
        'libopenal.so',
        'libGL.so',
        'libvulkan.so',
        'libwine.so',
    ]

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
        super().__init__()
        self.interval_ms = interval_ms
        self.is_game_detected = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_activity)

    def start(self):
        self.timer.start(self.interval_ms)
        logger.info("Non-Steam game detector started.")

    def _check_activity(self):
        detected = self._scan_procs()

        if detected != self.is_game_detected:
            self.is_game_detected = detected
            logger.info(f"Non-Steam game activity: {'Detected' if detected else 'None'}")
            self.game_activity_detected.emit(detected)

    def _scan_procs(self):
        try:
            pids = [d for d in os.listdir('/proc') if d.isdigit()]
            my_uid = os.getuid()

            for pid in pids:
                pid_int = int(pid)
                if pid_int == os.getpid() or pid_int < 100:
                    continue

                try:
                    stat_info = os.stat(f'/proc/{pid}')
                    if stat_info.st_uid != my_uid and my_uid != 0:
                        continue

                    with open(f'/proc/{pid}/comm', 'r') as f:
                        comm = f.read().strip()
                        if any(ignore in comm for ignore in self.IGNORE_PROCS):
                            continue

                    with open(f'/proc/{pid}/maps', 'r') as f:
                        for line in f:
                            if any(lib in line for lib in self.GAME_LIBS):
                                if any(x in line for x in ['Games', 'SteamLibrary', 'lutris', 'heroic', 'wine']):
                                     return True
                except (PermissionError, FileNotFoundError):
                    continue
        except Exception as e:
            logger.error(f"Error in GameDetector scan: {e}")

        return False

    def stop(self):
        self.timer.stop()
