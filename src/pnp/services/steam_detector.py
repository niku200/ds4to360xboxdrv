import subprocess
import os
from PySide6.QtCore import QObject, Signal, QTimer
from loguru import logger


class SteamDetector(QObject):
    steam_status_changed = Signal(bool)
    game_status_changed = Signal(bool)

    def __init__(self, interval_ms=2000):
        super().__init__()
        self.interval_ms = interval_ms
        self.is_steam_running = False
        self.is_game_active = False
        self.steam_input_active = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_status)

    def start(self):
        self.timer.start(self.interval_ms)
        logger.info("Steam/Game detector started.")

    def _check_status(self):
        steam_running = self._is_steam_process_running()
        game_active = self._is_any_game_running()
        steam_input_active = self._is_steam_input_engaged()

        if steam_running != self.is_steam_running:
            self.is_steam_running = steam_running
            logger.info(
                f"Steam status changed: {'Running' if steam_running else 'Stopped'}"
            )
            self.steam_status_changed.emit(steam_running)

        if (game_active != self.is_game_active or
                steam_input_active != self.steam_input_active):
            self.is_game_active = game_active
            self.steam_input_active = steam_input_active
            logger.info(
                f"Game activity: {game_active}, Steam Input: {steam_input_active}"
            )
            self.game_status_changed.emit(game_active and steam_input_active)

    def _is_steam_process_running(self):
        try:
            subprocess.check_output(["pgrep", "-x", "steam"])
            return True
        except subprocess.CalledProcessError:
            return False
        except Exception as err:
            logger.error(f"Error checking steam process: {err}")
            return False

    def _is_steam_input_engaged(self):
        try:
            import pyudev
            context = pyudev.Context()
            for device in context.list_devices(subsystem='input'):
                if device.get('ID_BUS') in ['usb', 'bluetooth']:
                    continue

                if not device.get('ID_INPUT_JOYSTICK'):
                    continue

                is_pnp = False
                name = device.get('NAME', '').lower()
                if 'pnp' in name or 'xbox 360 (pnp' in name:
                    is_pnp = True

                for parent in device.traverse():
                    p_name = parent.get('NAME', '').lower()
                    if 'pnp' in p_name:
                        is_pnp = True
                        break

                if not is_pnp:
                    logger.debug(f"Detected external virtual controller: {name}")
                    return True
        except Exception as err:
            logger.error(f"Error checking for Steam Input device: {err}")
        return False

    def _is_any_game_running(self):
        try:
            my_uid = os.getuid()
            for pid in os.listdir('/proc'):
                if not pid.isdigit():
                    continue

                if int(pid) == os.getpid() or int(pid) < 100:
                    continue

                try:
                    if os.stat(f'/proc/{pid}').st_uid != my_uid and my_uid != 0:
                        continue

                    with open(f'/proc/{pid}/environ', 'rb') as f:
                        env_data = f.read(4096)
                        if b'SteamAppId=' in env_data:
                            return True

                    with open(f'/proc/{pid}/maps', 'r', encoding="utf-8") as f:
                        for line in f:
                            if 'gameoverlayrenderer.so' in line:
                                return True
                except (PermissionError, FileNotFoundError):
                    continue
        except Exception as err:
            logger.error(f"Error scanning /proc for games: {err}")

        return False

    def stop(self):
        self.timer.stop()
