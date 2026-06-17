import os
import time
import evdev
from evdev import ecodes as e
from PySide6.QtCore import QObject, Signal, QTimer, QSocketNotifier
from loguru import logger
from pnp.services.process_runner import ProcessRunner
from pnp.core.virtual_controller import VirtualController

class Controller(QObject):
    status_changed = Signal(bool)
    battery_changed = Signal(int, str)

    def __init__(self, device_path: str, name: str, serial: str = None, config=None):
        super().__init__()
        self.device_path = device_path
        self.name = name
        self.serial = serial or "unknown"
        self.config = config
        self.evsieve_proc = None
        self.v_controller = None
        self.is_active = False

        self.battery_percentage = -1
        self.battery_status = "Unknown"
        self.battery_device_path = None

        self.battery_timer = QTimer()
        self.battery_timer.timeout.connect(self._update_battery)

        self.notifier = None

        # Initialize battery tracking
        QTimer.singleShot(0, self._find_battery_device)
        self.battery_timer.start(60000)

    def _find_battery_device(self):
        import pyudev
        context = pyudev.Context()
        try:
            device = pyudev.Devices.from_device_file(context, self.device_path)
            hid_parent = None
            for parent in device.traverse():
                if parent.subsystem == 'hid':
                    hid_parent = parent
                    break

            if hid_parent:
                for child in context.list_devices(subsystem='power_supply'):
                    if hid_parent.device_path in child.device_path:
                        self.battery_device_path = child.sys_path
                        self._update_battery()
                        break
        except Exception as e:
            logger.debug(f"Could not find battery device for {self.name}: {e}")

    def _update_battery(self):
        if not self.battery_device_path or not os.path.exists(self.battery_device_path):
            if not self.battery_device_path:
                self._find_battery_device()
            return

        try:
            cap_path = os.path.join(self.battery_device_path, "capacity")
            stat_path = os.path.join(self.battery_device_path, "status")

            if os.path.exists(cap_path):
                with open(cap_path, "r") as f:
                    self.battery_percentage = int(f.read().strip())

            if os.path.exists(stat_path):
                with open(stat_path, "r") as f:
                    self.battery_status = f.read().strip()

            self.battery_changed.emit(self.battery_percentage, self.battery_status)
        except Exception as e:
            logger.debug(f"Error updating battery for {self.name}: {e}")

    def start(self):
        if self.is_active:
            return

        self.is_active = True
        self.status_changed.emit(True)

        link_id = f"{self.serial}_{os.path.basename(self.device_path)}"
        evsieve_link = f"/dev/input/evsieve_{link_id}"

        if os.path.lexists(evsieve_link):
            try:
                os.remove(evsieve_link)
            except Exception as e:
                logger.debug(f"Failed to remove stale link {evsieve_link}: {e}")

        self.evsieve_proc = ProcessRunner(
            f"evsieve-{self.serial}",
            ["evsieve", "--input", self.device_path, "grab", "--output", f"create-link={evsieve_link}"]
        )
        self.evsieve_proc.start()

        self._retry_count = 50
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(lambda: self._check_evsieve_link(evsieve_link))
        self._check_timer.start(200)

    def _check_evsieve_link(self, evsieve_link):
        if not self.is_active:
            self._check_timer.stop()
            return

        if os.path.exists(evsieve_link):
            self._check_timer.stop()
            self._start_virtual_mapping(evsieve_link)
            return

        self._retry_count -= 1
        if self._retry_count <= 0:
            logger.error(f"Timed out waiting for evsieve link: {evsieve_link}")
            self._check_timer.stop()
            self.stop()

    def _start_virtual_mapping(self, evsieve_link):
        if not self.is_active:
            return

        self.v_controller = VirtualController(name=f"Xbox 360 (PNP-{self.serial})")
        self.v_controller.start()

        try:
            self.bridge_device = evdev.InputDevice(evsieve_link)
            self.notifier = QSocketNotifier(self.bridge_device.fd, QSocketNotifier.Read)
            self.notifier.activated.connect(self._on_evdev_data)
        except Exception as e:
            logger.error(f"Failed to open evsieve link for bridging: {e}")
            # Retry after a bit
            QTimer.singleShot(500, lambda: self._start_virtual_mapping(evsieve_link))

    def _on_evdev_data(self):
        if not self.is_active or not self.v_controller:
            return

        try:
            for event in self.bridge_device.read():
                if event.type == e.EV_SYN:
                    self.v_controller.emit(event.type, event.code, event.value, syn=True)
                    continue

                if event.type == e.EV_KEY:
                    self._map_button(event.code, event.value)
                elif event.type == e.EV_ABS:
                    self._map_axis(event.code, event.value)

        except Exception as e:
            logger.error(f"Error in bridge data: {e}")
            self.stop()

    def _map_button(self, code, value):
        mapping = {
            e.BTN_SOUTH: e.BTN_SOUTH, # Cross -> A
            e.BTN_EAST: e.BTN_EAST,   # Circle -> B
            e.BTN_NORTH: e.BTN_NORTH, # Triangle -> Y
            e.BTN_WEST: e.BTN_WEST,   # Square -> X
            e.BTN_TL: e.BTN_TL,       # L1 -> LB
            e.BTN_TR: e.BTN_TR,       # R1 -> RB
            e.BTN_SELECT: e.BTN_SELECT, # Share -> Back
            e.BTN_START: e.BTN_START,   # Options -> Start
            e.BTN_MODE: e.BTN_MODE,     # PS Button -> Guide
            e.BTN_THUMBL: e.BTN_THUMBL, # L3
            e.BTN_THUMBR: e.BTN_THUMBR, # R3
        }

        if code in mapping:
            self.v_controller.emit(e.EV_KEY, mapping[code], value, syn=False)

    def _map_axis(self, code, value):
        abs_info = self.bridge_device.capabilities().get(e.EV_ABS, {}).get(code)
        if not abs_info:
            return

        src_min, src_max = abs_info.min, abs_info.max
        src_range = src_max - src_min if src_max > src_min else 1

        if code in [e.ABS_X, e.ABS_Y, e.ABS_RX, e.ABS_RY]:
            normalized = (value - src_min) / src_range
            scaled = int((normalized * 65535) - 32768)
            scaled = max(-32768, min(32767, scaled))
            self.v_controller.emit(e.EV_ABS, code, scaled, syn=False)

        elif code in [e.ABS_Z, e.ABS_RZ]:
            normalized = (value - src_min) / src_range
            scaled = int(normalized * 255)
            self.v_controller.emit(e.EV_ABS, code, scaled, syn=False)

        elif code in [e.ABS_HAT0X, e.ABS_HAT0Y]:
            self.v_controller.emit(e.EV_ABS, code, value, syn=False)

    def stop(self):
        if not self.is_active:
            self._cleanup()
            return

        self.is_active = False
        self._cleanup()
        self.status_changed.emit(False)

    def _cleanup(self):
        self.battery_timer.stop()
        if self.notifier:
            self.notifier.setEnabled(False)
            self.notifier = None

        if self.v_controller:
            self.v_controller.stop()
            self.v_controller = None
        if self.evsieve_proc:
            self.evsieve_proc.stop()
            self.evsieve_proc = None

        link_id = f"{self.serial}_{os.path.basename(self.device_path)}"
        evsieve_link = f"/dev/input/evsieve_{link_id}"
        if os.path.lexists(evsieve_link):
            try:
                os.remove(evsieve_link)
            except Exception as e:
                logger.debug(f"Failed to remove link {evsieve_link}: {e}")
