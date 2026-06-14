import subprocess
import logging
import os
from gi.repository import GLib, GObject

logger = logging.getLogger(__name__)

class SteamDetector(GObject.Object):
    __gsignals__ = {
        'steam-status-changed': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
        'game-status-changed': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self, interval_ms=2000):
        GObject.Object.__init__(self)
        self.interval_ms = interval_ms
        self.is_steam_running = False
        self.is_game_active = False
        self.steam_input_active = False
        self._timeout_id = None

    def start(self):
        self._timeout_id = GLib.timeout_add(self.interval_ms, self._check_status)
        logger.info("Steam/Game detector started.")

    def _check_status(self):
        steam_running = self._is_steam_process_running()
        game_active = self._is_any_game_running()
        steam_input_active = self._is_steam_input_engaged()

        if steam_running != self.is_steam_running:
            self.is_steam_running = steam_running
            logger.info(f"Steam status changed: {'Running' if steam_running else 'Stopped'}")
            self.emit('steam-status-changed', steam_running)

        if game_active != self.is_game_active or steam_input_active != self.steam_input_active:
            self.is_game_active = game_active
            self.steam_input_active = steam_input_active
            logger.info(f"Game activity: {game_active}, Steam Input: {steam_input_active}")
            # We emit game-status-changed only if Steam Input is actually handling it,
            # or if we want the manager to know about the game regardless.
            # Let's emit the "effective" status: game is active AND steam input is engaged.
            self.emit('game-status-changed', game_active and steam_input_active)

        return True # Keep timeout running

    def _is_steam_process_running(self):
        try:
            # Check for steam process
            subprocess.check_output(["pgrep", "-x", "steam"])
            return True
        except subprocess.CalledProcessError:
            return False
        except Exception as e:
            logger.error(f"Error checking steam process: {e}")
            return False

    def _is_steam_input_engaged(self):
        """
        Checks if Steam Input has created a virtual controller.
        Robust check: looks for ANY uinput device that is NOT PNP's.
        """
        try:
            import pyudev
            context = pyudev.Context()
            for device in context.list_devices(subsystem='input'):
                # Only interested in virtual devices (uinput)
                if device.get('ID_BUS') in ['usb', 'bluetooth']:
                    continue

                # If it's a joystick/evdev device
                if not device.get('ID_INPUT_JOYSTICK'):
                    continue

                # Heuristic: Is it PNP?
                is_pnp = False
                name = device.get('NAME', '').lower()
                if 'pnp' in name or 'xbox 360 (pnp' in name:
                    is_pnp = True

                # Check properties and parents for 'pnp'
                for parent in device.traverse():
                    p_name = parent.get('NAME', '').lower()
                    if 'pnp' in p_name:
                        is_pnp = True
                        break

                if not is_pnp:
                    # If it's a virtual joystick not created by us,
                    # assume it's Steam Input or another mapper we should yield to.
                    logger.debug(f"Detected external virtual controller: {name}")
                    return True
        except Exception as e:
            logger.error(f"Error checking for Steam Input device: {e}")
        return False

    def _is_any_game_running(self):
        """
        Detects if a game is running by looking for SteamAppId in environment
        or gameoverlayrenderer.so in memory maps.
        """
        try:
            my_uid = os.getuid()
            for pid in os.listdir('/proc'):
                if not pid.isdigit():
                    continue

                # Skip our own process and common system processes
                if int(pid) == os.getpid() or int(pid) < 100:
                    continue

                try:
                    # Optimization: Only check our own user's processes
                    if os.stat(f'/proc/{pid}').st_uid != my_uid and my_uid != 0:
                        continue

                    # Method 1: Check environment for SteamAppId
                    with open(f'/proc/{pid}/environ', 'rb') as f:
                        # Use a reasonable read size to avoid hanging on weird files
                        env_data = f.read(4096)
                        if b'SteamAppId=' in env_data:
                            return True

                    # Method 2: Check maps for Steam Overlay
                    # This is useful for non-Steam games launched via Steam
                    with open(f'/proc/{pid}/maps', 'r') as f:
                        # We only need to check a few lines usually
                        for line in f:
                            if 'gameoverlayrenderer.so' in line:
                                return True
                except (PermissionError, FileNotFoundError):
                    continue
        except Exception as e:
            logger.error(f"Error scanning /proc for games: {e}")

        return False

    def stop(self):
        if self._timeout_id:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None
