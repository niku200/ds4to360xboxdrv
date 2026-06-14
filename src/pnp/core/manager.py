import json
import os
import logging
from gi.repository import GObject, GLib
from pnp.core.controller import Controller
from pnp.core.device_monitor import DeviceMonitor
from pnp.services.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class ControllerManager(GObject.Object):
    __gsignals__ = {
        'controller-list-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    STATUS_FILE = "/run/pnp/status.json"

    def __init__(self, write_status=False):
        GObject.Object.__init__(self)
        self.controllers = {} # path -> Controller object
        self.config_manager = ConfigManager()
        self.monitor = DeviceMonitor()
        self.monitor.connect('controller-added', self._on_controller_added)
        self.monitor.connect('controller-removed', self._on_controller_removed)

        self.steam_paused = False
        self.game_active = False
        self.write_status = write_status

    def start(self):
        self.monitor.start()
        self._update_status_file()
        GLib.timeout_add(5000, self._check_controller_processes)

    def _check_controller_processes(self):
        changed = False
        for path, controller in list(self.controllers.items()):
            if controller.is_active:
                evsieve_died = controller.evsieve_proc and not controller.evsieve_proc.is_running()
                xboxdrv_died = controller.xboxdrv_proc and not controller.xboxdrv_proc.is_running()
                if evsieve_died or xboxdrv_died:
                    # Throttled restart log
                    msg = f"Controller processes for {controller.name} died unexpectedly. Restarting."
                    if not hasattr(self, '_last_warn') or self._last_warn != msg:
                        logger.warning(msg)
                        if evsieve_died:
                            err = controller.evsieve_proc.get_stderr()
                            if err: logger.error(f"evsieve error: {err.strip()}")
                        if xboxdrv_died:
                            err = controller.xboxdrv_proc.get_stderr()
                            if err: logger.error(f"xboxdrv error: {err.strip()}")
                        self._last_warn = msg
                    controller.stop()
                    if not self.steam_paused:
                        controller.start()
                    changed = True
        if changed:
            self._update_status_file()
        return True

    def _on_controller_added(self, monitor, path, name, serial):
        if path not in self.controllers:
            # config is now a dictionary
            config = self.config_manager.get_controller_config(serial)
            controller = Controller(path, name, serial, config=config)
            self.controllers[path] = controller
            if not self.steam_paused:
                controller.start()
            self.emit('controller-list-changed')
            self._update_status_file()

    def _on_controller_removed(self, monitor, path):
        if path in self.controllers:
            self.controllers[path].stop()
            del self.controllers[path]
            self.emit('controller-list-changed')
            self._update_status_file()

    def set_steam_paused(self, paused):
        if self.steam_paused == paused:
            return

        self.steam_paused = paused
        logger.info(f"Steam pause state: {paused}")
        self._evaluate_state()

    def set_game_active(self, active):
        if self.game_active == active:
            return

        self.game_active = active
        logger.info(f"Game active state: {active}")
        self._evaluate_state()

    def _evaluate_state(self):
        """
        Logic:
        - If Steam is running AND a Game is active:
          Steam Input SHOULD be in control. Pause PNP.
        - If Steam is running BUT NO Game is active:
          Steam might be just sitting there. PNP stays active for desktop/launcher use.
        - If Steam is NOT running:
          PNP stays active.
        """
        should_pause = self.steam_paused and self.game_active

        # Exception: User might want PNP even if Steam is running if they
        # haven't configured Steam Input. But default is to trust Steam.

        logger.info(f"Evaluating state: Steam={self.steam_paused}, Game={self.game_active} -> Pause={should_pause}")

        for controller in self.controllers.values():
            if should_pause:
                controller.stop()
            else:
                controller.start()
        self._update_status_file()

    def stop_all(self):
        for controller in self.controllers.values():
            controller.stop()
        self._update_status_file()

    def _update_status_file(self):
        if not self.write_status:
            return

        data = {
            "active": any(c.is_active for c in self.controllers.values()),
            "steam_blocking": self.steam_paused,
            "game_active": self.game_active,
            "controllers": [c.name for c in self.controllers.values() if c.is_active]
        }

        try:
            os.makedirs(os.path.dirname(self.STATUS_FILE), exist_ok=True)
            with open(self.STATUS_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to write status file: {e}")
