#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import signal
import configparser
import json
import shutil
import logging
import threading
from typing import Optional, Tuple, Dict, Any

try:
    import evdev
except ImportError:
    evdev = None

# Constants
CONFIG_PATH = "/etc/ds4to360.conf"
DEFAULT_CONFIG = {
    'controllers': {
        # PS4
        '054c:05c4': 'DualShock 4',
        '054c:09cc': 'DualShock 4',
        '054c:0ba0': 'DualShock 4 (USB)',
        '054c:0da6': 'DualShock 4 (USB)',
        # PS5
        '054c:0ce6': 'DualSense',
        '054c:0df2': 'DualSense Edge',
        # PS3
        '054c:0268': 'DualShock 3'
    },
    'settings': {
        'rumble_gain': '15%',
        'check_interval': '2',
        'steam_conflict_check': 'true'
    },
    'mapping': {
        'axismap': '-y1=y1,-y2=y2',
        'absmap': 'ABS_HAT0X=dpad_x,ABS_HAT0Y=dpad_y,ABS_X=X1,ABS_Y=Y1,ABS_RX=X2,ABS_RY=Y2,ABS_Z=LT,ABS_RZ=RT',
        'keymap': 'BTN_SOUTH=A,BTN_EAST=B,BTN_NORTH=Y,BTN_WEST=X,BTN_START=start,BTN_MODE=guide,BTN_SELECT=back,BTN_TL=LB,BTN_TR=RB,BTN_TL2=LT,BTN_TR2=RT,BTN_THUMBL=TL,BTN_THUMBR=TR'
    }
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ds4to360-backend")

class ControllerInstance:
    def __init__(self, path: str, vid: str, pid: str, name: str, config: configparser.ConfigParser):
        self.path = path
        self.vid = vid
        self.pid = pid
        self.name = name
        self.config = config
        self.evsieve_proc = None
        self.xboxdrv_proc = None
        self.virtual_link = f"/dev/input/evsieve_{os.path.basename(path)}"
        self.active = False

    def start(self):
        evsieve_bin = shutil.which("evsieve")
        xboxdrv_bin = shutil.which("xboxdrv")

        if not xboxdrv_bin:
            logger.error("xboxdrv not found!")
            return False

        try:
            input_device = self.path
            if evsieve_bin:
                logger.info(f"Starting evsieve for {self.name} at {self.path}")
                self.evsieve_proc = subprocess.Popen([
                    evsieve_bin, "--input", self.path, "grab", "ff",
                    "--output", f"create-link={self.virtual_link}", f"name=Evsieve {self.name} Virtual"
                ])

                for _ in range(20):
                    if os.path.islink(self.virtual_link): break
                    time.sleep(0.1)

                if os.path.islink(self.virtual_link):
                    input_device = os.path.realpath(self.virtual_link)
                else:
                    logger.warning(f"evsieve link failed for {self.path}, falling back")

            rumble = self.config.get('settings', 'rumble_gain', fallback='15%')
            axismap = self.config.get('mapping', 'axismap', fallback=DEFAULT_CONFIG['mapping']['axismap'])
            absmap = self.config.get('mapping', 'absmap', fallback=DEFAULT_CONFIG['mapping']['absmap'])
            keymap = self.config.get('mapping', 'keymap', fallback=DEFAULT_CONFIG['mapping']['keymap'])

            xboxdrv_cmd = [
                xboxdrv_bin,
                "--evdev", input_device,
                "--mimic-xpad",
                "--silent", "--quiet",
                "--force-feedback",
                "--rumble-gain", rumble,
                "--axismap", axismap,
                "--evdev-absmap", absmap,
                "--evdev-keymap", keymap,
                "--no-dbus"
            ]

            logger.info(f"Starting xboxdrv for {self.name}")
            self.xboxdrv_proc = subprocess.Popen(xboxdrv_cmd)
            self.active = True
            return True
        except Exception as e:
            logger.error(f"Failed to start mapping for {self.name}: {e}")
            self.stop()
            return False

    def stop(self):
        self.active = False
        for proc in [self.xboxdrv_proc, self.evsieve_proc]:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=1)
                except:
                    if proc: proc.kill()

        if os.path.islink(self.virtual_link):
            try: os.remove(self.virtual_link)
            except: pass

        self.xboxdrv_proc = None
        self.evsieve_proc = None

    def is_healthy(self):
        if not self.active: return False
        if self.xboxdrv_proc and self.xboxdrv_proc.poll() is not None: return False
        if self.evsieve_proc and self.evsieve_proc.poll() is not None: return False
        return True

class Backend:
    def __init__(self):
        self.config = self.load_config()
        self.running = True
        self.controllers: Dict[str, ControllerInstance] = {}
        self.lock = threading.Lock()

        if evdev is None:
            logger.warning("python-evdev not found. Limited functionality.")

    def load_config(self):
        config = configparser.ConfigParser()
        config.read_dict(DEFAULT_CONFIG)
        if os.path.exists(CONFIG_PATH):
            config.read(CONFIG_PATH)
        return config

    def get_supported_devices(self):
        if 'controllers' in self.config:
            return {k.lower(): v for k, v in self.config['controllers'].items()}
        return {k.lower(): v for k, v in DEFAULT_CONFIG['controllers'].items()}

    def find_controllers(self) -> Dict[str, Tuple[str, str, str]]:
        supported = self.get_supported_devices()
        found = {}

        if evdev:
            for path in evdev.list_devices():
                try:
                    device = evdev.InputDevice(path)
                    vid = f"{device.info.vendor:04x}"
                    pid = f"{device.info.product:04x}"
                    key = f"{vid}:{pid}".lower()
                    if key in supported and evdev.ecodes.EV_KEY in device.capabilities():
                        found[path] = (vid, pid, supported[key])
                except: continue
        else:
            # Fallback proc parsing
            try:
                with open("/proc/bus/input/devices", "r") as f:
                    sections = f.read().split("\n\n")
                    for section in sections:
                        vid, pid, event = None, None, None
                        for line in section.split("\n"):
                            if line.startswith("I:"):
                                if 'Vendor=' in line: vid = line.split('Vendor=')[1].split()[0].lower()
                                if 'Product=' in line: pid = line.split('Product=')[1].split()[0].lower()
                            if line.startswith("H:"):
                                if "event" in line:
                                    for p in line.split():
                                        if p.startswith("event"): event = p
                        if vid and pid and event:
                            key = f"{vid}:{pid}"
                            if key in supported:
                                found[f"/dev/input/{event}"] = (vid, pid, supported[key])
            except Exception as e: logger.error(f"Scan error: {e}")
        return found

    def is_steam_running(self):
        if not self.config.getboolean('settings', 'steam_conflict_check', fallback=True):
            return False
        for proc_name in ["steam", "steamwebhelper"]:
            try:
                if subprocess.run(["pgrep", "-x", proc_name], capture_output=True).returncode == 0:
                    return True
            except: pass
        return False

    def update_status_file(self):
        active_controllers = [c.name for c in self.controllers.values() if c.active]
        steam_blocking = self.is_steam_running()

        status = {
            "active": len(active_controllers) > 0,
            "controllers": active_controllers,
            "device": active_controllers[0] if active_controllers else None,
            "count": len(active_controllers),
            "steam_blocking": steam_blocking,
            "timestamp": time.time()
        }

        runtime_dir = os.environ.get("RUNTIME_DIRECTORY", "/run/ds4to360")
        os.makedirs(runtime_dir, exist_ok=True)
        try:
            status_file = os.path.join(runtime_dir, "status.json")
            with open(status_file + ".tmp", "w") as f:
                json.dump(status, f)
            os.rename(status_file + ".tmp", status_file)
        except Exception as e:
            logger.error(f"Status update failed: {e}")

    def run(self):
        logger.info("Backend multi-controller service started")
        while self.running:
            try:
                self.config = self.load_config()
                interval = self.config.getint('settings', 'check_interval', fallback=2)

                steam = self.is_steam_running()
                found = self.find_controllers()

                with self.lock:
                    # Clean up old
                    to_remove = []
                    for path, instance in self.controllers.items():
                        if path not in found or steam or not instance.is_healthy():
                            logger.info(f"Stopping instance for {path}")
                            instance.stop()
                            to_remove.append(path)
                    for path in to_remove: del self.controllers[path]

                    # Start new
                    if not steam:
                        for path, (vid, pid, name) in found.items():
                            if path not in self.controllers:
                                instance = ControllerInstance(path, vid, pid, name, self.config)
                                if instance.start():
                                    self.controllers[path] = instance

                self.update_status_file()
            except Exception as e:
                logger.error(f"Loop error: {e}")

            time.sleep(interval)

    def cleanup_all(self):
        with self.lock:
            for instance in self.controllers.values():
                instance.stop()
            self.controllers.clear()
            self.update_status_file()

def main():
    backend = Backend()
    def handler(sig, frame):
        backend.running = False
        backend.cleanup_all()
        sys.exit(0)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    backend.run()

if __name__ == "__main__":
    main()
