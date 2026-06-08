import os
import logging
import time
from gi.repository import GObject
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

        evsieve_link = f"/dev/input/evsieve_{os.path.basename(self.device_path)}"

        self.evsieve_proc = ProcessRunner(
            f"evsieve-{self.serial}",
            ["evsieve", "--input", self.device_path, "--grab", "--output", f"create-link={evsieve_link}"]
        )
        self.evsieve_proc.start()

        # Wait for the virtual device link to be created
        retries = 10
        while retries > 0 and not os.path.exists(evsieve_link):
            time.sleep(0.2)
            retries -= 1

        if not os.path.exists(evsieve_link):
            logger.error(f"Timed out waiting for evsieve link: {evsieve_link}")
            self.evsieve_proc.stop()
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

        self.is_active = True
        self.emit('status-changed', True)

    def stop(self):
        if not self.is_active:
            return

        if self.xboxdrv_proc:
            self.xboxdrv_proc.stop()
        if self.evsieve_proc:
            self.evsieve_proc.stop()

        # Clean up link if exists
        evsieve_link = f"/dev/input/evsieve_{os.path.basename(self.device_path)}"
        if os.path.exists(evsieve_link):
            try:
                os.remove(evsieve_link)
            except:
                pass

        self.is_active = False
        self.emit('status-changed', False)
