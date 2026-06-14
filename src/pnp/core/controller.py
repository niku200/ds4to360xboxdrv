import os
import logging
import time
import evdev
from evdev import ecodes as e
from gi.repository import GObject, GLib
from pnp.services.process_runner import ProcessRunner
from pnp.core.virtual_controller import VirtualController

logger = logging.getLogger(__name__)

class Controller(GObject.Object):
    __gsignals__ = {
        'status-changed': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
        'battery-changed': (GObject.SignalFlags.RUN_FIRST, None, (int, str)),
    }

    def __init__(self, device_path: str, name: str, serial: str = None, config=None):
        GObject.Object.__init__(self)
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
        self.battery_timer_id = None

        # Initialize battery tracking
        GLib.idle_add(self._find_battery_device)
        self.battery_timer_id = GLib.timeout_add_seconds(60, self._update_battery)

    def _find_battery_device(self):
        import pyudev
        context = pyudev.Context()
        try:
            # Find the udev device for the input path
            device = pyudev.Devices.from_device_file(context, self.device_path)
            # Find the HID parent which usually owns the battery device
            hid_parent = None
            for parent in device.traverse():
                if parent.subsystem == 'hid':
                    hid_parent = parent
                    break

            if hid_parent:
                # Look for a power_supply child of this HID device
                for child in context.list_devices(subsystem='power_supply'):
                    if hid_parent.device_path in child.device_path:
                        self.battery_device_path = child.sys_path
                        self._update_battery()
                        break
        except Exception as e:
            logger.debug(f"Could not find battery device for {self.name}: {e}")

    def _update_battery(self):
        if not self.battery_device_path or not os.path.exists(self.battery_device_path):
            # Try to re-find it if it was lost (e.g. bluetooth reconnection)
            if not self.battery_device_path:
                self._find_battery_device()
            return True

        try:
            cap_path = os.path.join(self.battery_device_path, "capacity")
            stat_path = os.path.join(self.battery_device_path, "status")

            if os.path.exists(cap_path):
                with open(cap_path, "r") as f:
                    self.battery_percentage = int(f.read().strip())

            if os.path.exists(stat_path):
                with open(stat_path, "r") as f:
                    self.battery_status = f.read().strip()

            self.emit('battery-changed', self.battery_percentage, self.battery_status)
        except Exception as e:
            logger.debug(f"Error updating battery for {self.name}: {e}")

        return True

    def start(self):
        if self.is_active:
            return

        self.is_active = True
        self.emit('status-changed', True)

        # Use a unique name for the evsieve link to avoid collisions if multiple controllers
        # have similar base device names (unlikely but possible).
        # Also include serial if available.
        link_id = f"{self.serial}_{os.path.basename(self.device_path)}"
        evsieve_link = f"/dev/input/evsieve_{link_id}"

        # Ensure the link doesn't exist before starting evsieve
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

        # Wait for the virtual device link to be created asynchronously
        # Increase timeout to 10 seconds (50 retries * 200ms) for slow systems
        self._retry_count = 50
        GLib.timeout_add(200, self._check_evsieve_link, evsieve_link)

    def _check_evsieve_link(self, evsieve_link):
        if not self.is_active:
            return False

        if os.path.exists(evsieve_link):
            self._start_virtual_mapping(evsieve_link)
            return False # Stop timeout

        self._retry_count -= 1
        if self._retry_count <= 0:
            logger.error(f"Timed out waiting for evsieve link: {evsieve_link}")
            self.stop()
            return False

        return True # Continue timeout

    def _start_virtual_mapping(self, evsieve_link):
        if not self.is_active:
            return

        # Initialize native virtual controller
        self.v_controller = VirtualController(name=f"Xbox 360 (PNP-{self.serial})")
        self.v_controller.start()

        # We still use evsieve to read the grabbed device and pipe it to our virtual controller
        # However, for now, we'll implement a simple python-evdev loop to bridge them.
        # Ideally, we'd want evsieve to output directly to our uinput,
        # but bridging in Python allows finer control.
        GLib.idle_add(self._bridge_loop, evsieve_link)

    def _bridge_loop(self, evsieve_link):
        if not self.is_active or not self.v_controller:
            return False

        try:
            device = evdev.InputDevice(evsieve_link)
            # Use non-blocking read or a separate thread for performance
            # For simplicity in this refactor, we'll use a GLib-friendly approach
            GLib.io_add_watch(device.fd, GLib.IO_IN, self._on_evdev_data, device)
            return False # Stop idle call
        except Exception as e:
            logger.error(f"Failed to open evsieve link for bridging: {e}")
            return True # Retry

    def _on_evdev_data(self, source, condition, device):
        if not self.is_active or not self.v_controller:
            return False

        try:
            for event in device.read():
                if event.type == e.EV_SYN:
                    self.v_controller.emit(event.type, event.code, event.value, syn=True)
                    continue

                # Mapping Logic: PlayStation -> Xbox 360 (Buffered)
                if event.type == e.EV_KEY:
                    self._map_button(event.code, event.value)
                elif event.type == e.EV_ABS:
                    self._map_axis(event.code, event.value, device)

            return True
        except Exception as e:
            logger.error(f"Error in bridge data: {e}")
            return False

    def _map_button(self, code, value):
        # Default mapping: PlayStation -> Xbox 360
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

        # Override with config if present
        if self.config and 'mapping' in self.config:
            # Note: This is simplified. In a real scenario, we'd parse the 'keymap' string
            pass

        if code in mapping:
            self.v_controller.emit(e.EV_KEY, mapping[code], value, syn=False)

    def _map_axis(self, code, value, device):
        # Maps and SCALES PlayStation axes to Xbox 360 axes
        abs_info = device.capabilities().get(e.EV_ABS, {}).get(code)
        if not abs_info:
            return

        # Dynamic Scaling Logic
        src_min, src_max = abs_info.min, abs_info.max
        src_range = src_max - src_min if src_max > src_min else 1

        if code in [e.ABS_X, e.ABS_Y, e.ABS_RX, e.ABS_RY]:
            # Stick scaling to -32768..32767
            normalized = (value - src_min) / src_range
            scaled = int((normalized * 65535) - 32768)
            scaled = max(-32768, min(32767, scaled))
            self.v_controller.emit(e.EV_ABS, code, scaled, syn=False)

        elif code in [e.ABS_Z, e.ABS_RZ]:
            # Triggers scaling to 0..255
            normalized = (value - src_min) / src_range
            scaled = int(normalized * 255)
            self.v_controller.emit(e.EV_ABS, code, scaled, syn=False)

        elif code in [e.ABS_HAT0X, e.ABS_HAT0Y]:
            # D-Pad: -1, 0, 1 (Usually doesn't need scaling)
            self.v_controller.emit(e.EV_ABS, code, value, syn=False)

    def stop(self):
        if not self.is_active:
            # Still try to clean up just in case
            self._cleanup()
            return

        self.is_active = False
        self._cleanup()
        self.emit('status-changed', False)

    def _cleanup(self):
        if self.battery_timer_id:
            GLib.source_remove(self.battery_timer_id)
            self.battery_timer_id = None

        if self.v_controller:
            self.v_controller.stop()
            self.v_controller = None
        if self.evsieve_proc:
            self.evsieve_proc.stop()
            self.evsieve_proc = None

        # Clean up link if exists
        link_id = f"{self.serial}_{os.path.basename(self.device_path)}"
        evsieve_link = f"/dev/input/evsieve_{link_id}"
        if os.path.lexists(evsieve_link):
            try:
                os.remove(evsieve_link)
            except Exception as e:
                logger.debug(f"Failed to remove link {evsieve_link}: {e}")
