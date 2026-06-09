import os
import logging
import time
from gi.repository import GObject, GLib
from pnp.services.process_runner import ProcessRunner

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
        self.xboxdrv_proc = None
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

        evsieve_link = f"/dev/input/evsieve_{os.path.basename(self.device_path)}"

        self.evsieve_proc = ProcessRunner(
            f"evsieve-{self.serial}",
            ["evsieve", "--input", self.device_path, "--grab", "--output", f"create-link={evsieve_link}"]
        )
        self.evsieve_proc.start()

        # Wait for the virtual device link to be created asynchronously
        self._retry_count = 25
        GLib.timeout_add(200, self._check_evsieve_link, evsieve_link)

    def _check_evsieve_link(self, evsieve_link):
        if not self.is_active:
            return False

        if os.path.exists(evsieve_link):
            self._start_xboxdrv(evsieve_link)
            return False # Stop timeout

        self._retry_count -= 1
        if self._retry_count <= 0:
            logger.error(f"Timed out waiting for evsieve link: {evsieve_link}")
            self.stop()
            return False

        return True # Continue timeout

    def _start_xboxdrv(self, evsieve_link):
        if not self.is_active:
            return

        # Get mapping from config
        axismap = self.config.get('mapping', 'axismap', fallback='-y1=y1,-y2=y2')
        absmap = self.config.get('mapping', 'absmap', fallback='ABS_X=x1,ABS_Y=y1,ABS_RX=x2,ABS_RY=y2,ABS_Z=lt,ABS_RZ=rt,ABS_HAT0X=dpad_x,ABS_HAT0Y=dpad_y')
        keymap = self.config.get('mapping', 'keymap', fallback='BTN_SOUTH=a,BTN_EAST=b,BTN_NORTH=x,BTN_WEST=y,BTN_TL=lb,BTN_TR=rb,BTN_TL2=lt,BTN_TR2=rt,BTN_THUMBL=tl,BTN_THUMBR=tr,BTN_SELECT=back,BTN_START=start,BTN_MODE=guide')

        xboxdrv_cmd = [
            "xboxdrv", "--evdev", evsieve_link,
            "--mimic-xpad", "--silent",
            "--axismap", axismap,
            "--evdev-absmap", absmap,
            "--evdev-keymap", keymap
        ]

        self.xboxdrv_proc = ProcessRunner(f"xboxdrv-{self.serial}", xboxdrv_cmd)
        self.xboxdrv_proc.start()

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

        if self.xboxdrv_proc:
            self.xboxdrv_proc.stop()
            self.xboxdrv_proc = None
        if self.evsieve_proc:
            self.evsieve_proc.stop()
            self.evsieve_proc = None

        # Clean up link if exists
        evsieve_link = f"/dev/input/evsieve_{os.path.basename(self.device_path)}"
        if os.path.exists(evsieve_link):
            try:
                os.remove(evsieve_link)
            except Exception as e:
                logger.debug(f"Failed to remove link {evsieve_link}: {e}")
