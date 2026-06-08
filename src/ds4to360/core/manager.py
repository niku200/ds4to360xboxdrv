import json
import os
import logging
from gi.repository import GObject
from ds4to360.core.controller import Controller
from ds4to360.core.device_monitor import DeviceMonitor
from ds4to360.services.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class ControllerManager(GObject.Object):
    __gsignals__ = {
        'controller-list-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    STATUS_FILE = "/run/ds4to360/status.json"

    def __init__(self, write_status=False):
        GObject.Object.__init__(self)
        self.controllers = {} # path -> Controller object
        self.config_manager = ConfigManager()
        self.monitor = DeviceMonitor()
        self.monitor.connect('controller-added', self._on_controller_added)
        self.monitor.connect('controller-removed', self._on_controller_removed)

        self.steam_paused = False
        self.write_status = write_status

    def start(self):
        self.monitor.start()
        self._update_status_file()

    def _on_controller_added(self, monitor, path, name, serial):
        if path not in self.controllers:
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

        for controller in self.controllers.values():
            if paused:
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
            "controllers": [c.name for c in self.controllers.values() if c.is_active]
        }

        try:
            os.makedirs(os.path.dirname(self.STATUS_FILE), exist_ok=True)
            with open(self.STATUS_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to write status file: {e}")
