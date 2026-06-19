import os
from loguru import logger

class GameDetector:
    def __init__(self):
        # Libraries common in games
        self.game_libs = [
            'libSDL2-',
            'libSDL-',
            'libopenal.so',
            'libGL.so',
            'libvulkan.so',
            'libwine.so',
        ]

        # Processes to ignore (browsers, etc. that might use GL)
        self.ignore_procs = [
            'firefox',
            'chrome',
            'chromium',
            'electron',
            'gnome-shell',
            'Xorg',
            'wayland',
            'pnp',
        ]

    def scan_procs(self):
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
                    with open(f'/proc/{pid}/comm', 'r', encoding="utf-8") as f:
                        comm = f.read().strip()
                        if any(ignore in comm for ignore in self.ignore_procs):
                            continue

                    # Check maps for game libraries
                    with open(f'/proc/{pid}/maps', 'r', encoding="utf-8") as f:
                        for line in f:
                            if any(lib in line for lib in self.game_libs):
                                # Additional heuristic:
                                # is it in a common game directory?
                                if any(x in line for x in [
                                    'Games', 'SteamLibrary', 'lutris',
                                    'heroic', 'wine'
                                ]):
                                    return True
                except (PermissionError, FileNotFoundError):
                    continue
        except Exception as err:
            logger.error(f"Error in GameDetector scan: {err}")

        return False
