import json
import os
from PySide6.QtCore import QObject, Signal, QTimer
from loguru import logger
from pnp.core.controller import Controller
from pnp.core.device_monitor import DeviceMonitor
from pnp.services.config_manager import ConfigManager


class ControllerManager(QObject):
    controller_list_changed = Signal()

    STATUS_FILE = "/run/pnp/status.json"

    def __init__(self, write_status=False):
        super().__init__()
        self.controllers = {}  # path -> Controller object
        self.config_manager = ConfigManager()
        self.monitor = DeviceMonitor()
        self.monitor.controller_added.connect(self._on_controller_added)
        self.monitor.controller_removed.connect(self._on_controller_removed)

        self.steam_paused = False
        self.game_active = False
        self.write_status = write_status

        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_controller_processes)

    def start(self):
        self.monitor.start()
        self._update_status_file()
        self.check_timer.start(5000)

    def _check_controller_processes(self):
        changed = False
        for controller in list(self.controllers.values()):
            if controller.is_active:
                evsieve_died = (controller.evsieve_proc and
                                not controller.evsieve_proc.is_running())
                if evsieve_died:
                    logger.warning(
                        f"Controller processes for {controller.name} died "
                        f"unexpectedly. Restarting."
                    )
                    err = controller.evsieve_proc.get_stderr()
                    if err:
                        logger.error(f"evsieve error: {err.strip()}")

                    controller.stop()
                    if not self.steam_paused:
                        controller.start()
                    changed = True
        if changed:
            self._update_status_file()

    def _on_controller_added(self, path, name, serial):
        if path not in self.controllers:
            config = self.config_manager.get_controller_config(serial)
            controller = Controller(path, name, serial, config=config)
            self.controllers[path] = controller
            if not self.steam_paused:
                controller.start()
            self.controller_list_changed.emit()
            self._update_status_file()

    def _on_controller_removed(self, path):
        if path in self.controllers:
            self.controllers[path].stop()
            del self.controllers[path]
            self.controller_list_changed.emit()
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
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR",
                                     f"/run/user/{os.getuid()}")
        manual_pause = os.path.exists(
            os.path.join(runtime_dir, "pnp", "manual_pause")
        )

        should_pause = manual_pause or (self.steam_paused and self.game_active)

        logger.info(
            f"Evaluating state: ManualPause={manual_pause}, "
            f"Steam={self.steam_paused}, Game={self.game_active} -> "
            f"Pause={should_pause}"
        )

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
            "controllers": [
                c.name for c in self.controllers.values() if c.is_active
            ]
        }

        try:
            os.makedirs(os.path.dirname(self.STATUS_FILE), exist_ok=True)
            with open(self.STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as err:
            logger.error(f"Failed to write status file: {err}")
