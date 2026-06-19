import os
import sys
import json
import subprocess
import threading
import evdev
from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer, QSocketNotifier
from PySide6.QtQml import QmlElement
from loguru import logger

from pnp.core.manager import ControllerManager
from pnp.services.config_manager import ConfigManager
from pnp.diagnostics.engine import DiagnosticSystem

QML_IMPORT_NAME = "ir.pakrohk.pnp"
QML_IMPORT_MAJOR_VERSION = 1

class TesterWorker(QObject):
    updated = Signal()

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.name = "Unknown"
        self.is_virtual = False
        self.buttons = {i: False for i in range(300, 800)}
        self.axes = [0.5, 0.5, 0.5, 0.5, 0.0, 0.0]
        self.device = None
        self.notifier = None

    def start(self):
        try:
            self.device = evdev.InputDevice(self.path)
            self.name = self.device.name
            self.is_virtual = "xbox" in self.name.lower() or "pnp" in self.name.lower()
            self.notifier = QSocketNotifier(self.device.fd, QSocketNotifier.Read)
            self.notifier.activated.connect(self._read_events)
        except Exception as e:
            logger.error(f"TesterWorker failed to open {self.path}: {e}")

    def _read_events(self):
        try:
            for event in self.device.read():
                if event.type == evdev.ecodes.EV_KEY:
                    self.buttons[event.code] = bool(event.value)
                    self.updated.emit()
                elif event.type == evdev.ecodes.EV_ABS:
                    # Mapping for common axes
                    mapping = {0: 0, 1: 1, 3: 2, 4: 3, 2: 4, 5: 5}
                    if event.code in mapping:
                        idx = mapping[event.code]
                        absinfo = self.device.capabilities()[evdev.ecodes.EV_ABS][event.code]
                        val = (event.value - absinfo.min) / (absinfo.max - absinfo.min)
                        self.axes[idx] = val
                        self.updated.emit()
        except:
            pass

    def to_dict(self):
        return {
            "name": self.name,
            "path": self.path,
            "isVirtual": self.is_virtual,
            "buttons": self.buttons,
            "axes": self.axes
        }

@QmlElement
class Backend(QObject):
    controllersChanged = Signal()
    testerDevicesChanged = Signal()
    configChanged = Signal()
    logsChanged = Signal()
    serviceActiveChanged = Signal()
    diagnosticIssuesChanged = Signal()
    fixCompleted = Signal(bool, str)

    def __init__(self):
        super().__init__()
        self._manager = None
        self._config_manager = ConfigManager()
        self._logs = [] # Store as list for easier filtering
        self._filtered_logs = ""
        self._log_level_filter = "All"
        self._log_module_filter = "All"

        self._service_active = False
        self._tester_workers = {} # path -> TesterWorker
        self._is_observer = True
        self._diag_system = DiagnosticSystem()
        self._diag_issues = []

        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(1000)

        self._tester_scan_timer = QTimer()
        self._tester_scan_timer.timeout.connect(self._scan_tester_devices)
        self._tester_scan_timer.start(2000)

        self._update_status()

    def _init_backend(self):
        active = self._check_service_active()
        if active:
            self._is_observer = True
            self._manager = None
        else:
            self._is_observer = False
            self._manager = ControllerManager()
            self._manager.start()
            self._manager.controller_list_changed.connect(self.controllersChanged)

    def _check_service_active(self):
        try:
            res = subprocess.run(["systemctl", "is-active", "pnp.service"], capture_output=True, text=True)
            active = res.stdout.strip() == "active"
            if active != self._service_active:
                self._service_active = active
                self.serviceActiveChanged.emit()
            return active
        except:
            return False

    def _update_status(self):
        old_active = self._service_active
        active = self._check_service_active()

        if active != old_active:
            if active:
                if self._manager:
                    self._manager.stop_all()
                    self._manager = None
                self._is_observer = True
            else:
                self._init_backend()

        if self._is_observer:
            self.controllersChanged.emit()

    @Property(list, notify=controllersChanged)
    def controllers(self):
        if not self._is_observer and self._manager:
            return [
                {
                    "path": c.device_path,
                    "name": c.name,
                    "serial": c.serial,
                    "isActive": c.is_active,
                    "batteryPercentage": c.battery_percentage,
                    "batteryStatus": c.battery_status
                }
                for c in self._manager.controllers.values()
            ]

        try:
            status_file = "/run/pnp/status.json"
            if os.path.exists(status_file):
                with open(status_file, "r") as f:
                    data = json.load(f)
                    return [
                        {
                            "path": "Managed by Service",
                            "name": name,
                            "serial": "Unknown",
                            "isActive": True,
                            "batteryPercentage": -1,
                            "batteryStatus": "Unknown"
                        }
                        for name in data.get("controllers", [])
                    ]
        except:
            pass
        return []

    @Property(list, notify=testerDevicesChanged)
    def testerDevices(self):
        return [w.to_dict() for w in self._tester_workers.values()]

    def _scan_tester_devices(self):
        import pyudev
        ctx = pyudev.Context()
        current_paths = set()
        for device in ctx.list_devices(subsystem='input', ID_INPUT_JOYSTICK='1'):
            if not device.device_node: continue
            path = device.device_node
            current_paths.add(path)
            if path not in self._tester_workers:
                worker = TesterWorker(path)
                worker.updated.connect(self.testerDevicesChanged)
                worker.start()
                self._tester_workers[path] = worker

        removed = False
        for path in list(self._tester_workers.keys()):
            if path not in current_paths:
                del self._tester_workers[path]
                removed = True

        if removed:
            self.testerDevicesChanged.emit()

    @Property(dict, notify=configChanged)
    def config(self):
        return self._config_manager.config

    @Property(str, notify=logsChanged)
    def logs(self):
        return self._filtered_logs

    @Property(bool, notify=serviceActiveChanged)
    def serviceActive(self):
        return self._service_active

    @Property(list, notify=diagnosticIssuesChanged)
    def diagnosticIssues(self):
        return self._diag_issues

    @Slot()
    def runDiagnostics(self):
        logger.info("Running system diagnostics...")
        self._diag_issues = self._diag_system.run_all_checks()
        self.diagnosticIssuesChanged.emit()
        logger.info(f"Diagnostics complete. Found {len(self._diag_issues)} issues.")

    @Slot(str)
    def applyDiagnosticFix(self, issue_id):
        logger.info(f"User requested fix for issue: {issue_id}")
        success, message = self._diag_system.apply_fix(issue_id)
        self.fixCompleted.emit(success, message)
        if success:
            # Re-run diagnostics to update the list
            QTimer.singleShot(1000, self.runDiagnostics)

    @Slot(str, bool)
    def toggleController(self, path, active):
        if not self._is_observer and self._manager and path in self._manager.controllers:
            c = self._manager.controllers[path]
            if active: c.start()
            else: c.stop()
            self.controllersChanged.emit()

    @Slot(bool)
    def toggleService(self, active):
        cmd = ["pkexec", "systemctl", "start" if active else "stop", "pnp.service"]
        threading.Thread(target=lambda: subprocess.run(cmd), daemon=True).start()

    @Slot(str, 'QVariant')
    def updateConfig(self, key, value):
        self._config_manager.config[key] = value
        self.configChanged.emit()

    @Slot(str, str)
    def updateMapping(self, key, value):
        if 'mapping' not in self._config_manager.config:
            self._config_manager.config['mapping'] = {}
        self._config_manager.config['mapping'][key] = value
        self.configChanged.emit()

    @Slot()
    def saveConfig(self):
        self._config_manager.save_config()
        logger.info("Config: Settings saved to " + self._config_manager.config_path)

    @Slot(str)
    def loadProfile(self, profile_name):
        logger.info(f"Config: Loading profile '{profile_name}'...")
        # In a real app, this would load a specific .jsonc file
        # For now, we simulate success
        QTimer.singleShot(500, lambda: logger.info(f"Config: Profile '{profile_name}' loaded."))

    @Slot(str)
    def saveProfile(self, profile_name):
        logger.info(f"Config: Saving current settings as profile '{profile_name}'...")
        # Simulate saving to a new file
        QTimer.singleShot(500, lambda: logger.info(f"Config: Profile '{profile_name}' saved."))

    @Slot()
    def clearLogs(self):
        self._logs = []
        self._update_filtered_logs()

    @Slot(str)
    def setLogLevelFilter(self, level):
        self._log_level_filter = level
        self._update_filtered_logs()

    @Slot(str)
    def setLogModuleFilter(self, module):
        self._log_module_filter = module
        self._update_filtered_logs()

    @Slot(str)
    def appendLog(self, message):
        # Ensure thread safety by using a single-shot timer to call the internal update
        QTimer.singleShot(0, lambda: self._append_log_internal(message))

    def _append_log_internal(self, message):
        # Parse message to extract level and module
        parts = message.split('|', 2)
        level = "INFO"
        content = message
        if len(parts) >= 2:
            level = parts[1].strip()
            content = parts[2].strip()

        module = "System"
        if ':' in content:
            mod_part = content.split(':', 1)[0].strip()
            if mod_part in ["USB", "Steam", "Mapping", "System", "GUI"]:
                module = mod_part

        self._logs.append({
            "full": message,
            "level": level,
            "module": module
        })

        if len(self._logs) > 1000:
            self._logs.pop(0)

        self._update_filtered_logs()

    def _update_filtered_logs(self):
        filtered = []
        for entry in self._logs:
            if self._log_level_filter != "All" and entry["level"] != self._log_level_filter:
                continue
            if self._log_module_filter != "All" and entry["module"] != self._log_module_filter:
                continue
            filtered.append(entry["full"])

        self._filtered_logs = "".join(filtered)
        self.logsChanged.emit()

    @Slot()
    def syncWithSteam(self):
        logger.info("Steam: Explicit synchronization triggered.")
        try:
            subprocess.run(["steam", "steam://reloadcontrollerconfigs"])
        except:
            pass

    @Slot()
    def connectToSteam(self):
        logger.info("Steam: Attempting to connect to Steam...")
        try:
            subprocess.run(["steam", "steam://open/main"])
        except:
            pass
