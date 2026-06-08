import os
import logging
import time
from gi.repository import GObject, GLib
from ds4to360.services.process_runner import ProcessRunner

logger = logging.getLogger(__name__)

class Controller(GObject.Object):
    __gsignals__ = {
        'status-changed': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self, device_path, name, serial=None, config=None):
        GObject.Object.__init__(self)
        self.device_path = device_path
        self.name = name
        self.serial = serial or "unknown"
        self.config = config
        self.evsieve_proc = None
        self.xboxdrv_proc = None
        self.is_active = False

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
        self._retry_count = 15
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
        absmap = self.config.get('mapping', 'absmap', fallback='ABS_X=x1,ABS_Y=y1,ABS_Z=x2,ABS_RZ=y2,ABS_HAT0X=dpad_x,ABS_HAT0Y=dpad_y')
        keymap = self.config.get('mapping', 'keymap', fallback='BTN_SOUTH=a,BTN_EAST=b,BTN_NORTH=x,BTN_WEST=y,BTN_TL=lb,BTN_TR=rb,BTN_THUMBL=tl,BTN_THUMBR=tr,BTN_SELECT=back,BTN_START=start,BTN_MODE=guide')

        xboxdrv_cmd = [
            "xboxdrv", "--evdev", evsieve_link,
            "--mimic-xpad", "--silent",
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
