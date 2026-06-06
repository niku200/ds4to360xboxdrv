#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import signal
import configparser
import json
import re
import shutil

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
        'check_interval': '5',
        'steam_conflict_check': 'true'
    },
    'mapping': {
        'axismap': '-y1=y1,-y2=y2',
        'absmap': 'ABS_HAT0X=dpad_x,ABS_HAT0Y=dpad_y,ABS_X=X1,ABS_Y=Y1,ABS_RX=X2,ABS_RY=Y2,ABS_Z=LT,ABS_RZ=RT',
        'keymap': 'BTN_SOUTH=A,BTN_EAST=B,BTN_NORTH=Y,BTN_WEST=X,BTN_START=start,BTN_MODE=guide,BTN_SELECT=back,BTN_TL=LB,BTN_TR=RB,BTN_TL2=LT,BTN_TR2=RT,BTN_THUMBL=TL,BTN_THUMBR=TR'
    }
}

class Backend:
    def __init__(self):
        self.config = self.load_config()
        self.running = True
        self.current_evsieve = None
        self.current_xboxdrv = None
        self.current_device = None
        self.current_device_name = None
        self.virtual_link = "/dev/input/evsieve_ds4"

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_PATH):
            config.read(CONFIG_PATH)
        else:
            config.read_dict(DEFAULT_CONFIG)
        return config

    def get_supported_devices(self):
        if 'controllers' in self.config:
            return self.config['controllers']
        return DEFAULT_CONFIG['controllers']

    def find_controller(self):
        supported = self.get_supported_devices()
        try:
            with open("/proc/bus/input/devices", "r") as f:
                content = f.read()
                sections = content.split("\n\n")
                for section in sections:
                    lines = section.split("\n")
                    vid = None
                    pid = None
                    event = None
                    is_js = False
                    for line in lines:
                        if line.startswith("I:"):
                            match_v = re.search(r"Vendor=([0-9a-fA-F]+)", line)
                            match_p = re.search(r"Product=([0-9a-fA-F]+)", line)
                            if match_v: vid = match_v.group(1).lower()
                            if match_p: pid = match_p.group(1).lower()
                        if line.startswith("H:"):
                            if "js" in line:
                                is_js = True
                            match_e = re.search(r"event\d+", line)
                            if match_e:
                                event = match_e.group(0)

                    if vid and pid and event and is_js:
                        key = f"{vid}:{pid}"
                        if key in supported:
                            return event, vid, pid, supported[key]
        except Exception as e:
            self.log(f"Error reading devices: {e}")
        return None

    def is_steam_running(self):
        if self.config.getboolean('settings', 'steam_conflict_check', fallback=True):
            try:
                # Check more processes for Steam
                for proc in ["steam", "steamwebhelper", "steam.sh"]:
                    if subprocess.run(["pgrep", "-x", proc], capture_output=True).returncode == 0:
                        return True
            except:
                pass
        return False

    def log(self, message):
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")
        sys.stdout.flush()

    def update_status(self, active, device=None, steam_blocking=False):
        status = {
            "active": active,
            "device": device,
            "steam_blocking": steam_blocking,
            "timestamp": time.time()
        }
        runtime_dir = os.environ.get("RUNTIME_DIRECTORY", "/run/ds4to360")
        if not os.path.exists(runtime_dir):
            try:
                os.makedirs(runtime_dir, exist_ok=True)
            except:
                return

        try:
            status_file = os.path.join(runtime_dir, "status.json")
            with open(status_file + ".tmp", "w") as f:
                json.dump(status, f)
            os.rename(status_file + ".tmp", status_file)
        except Exception as e:
            self.log(f"Failed to update status file: {e}")

    def cleanup(self):
        if self.current_xboxdrv:
            self.log("Terminating xboxdrv")
            self.current_xboxdrv.terminate()
            try:
                self.current_xboxdrv.wait(timeout=2)
            except:
                self.current_xboxdrv.kill()
            self.current_xboxdrv = None

        if self.current_evsieve:
            self.log("Terminating evsieve")
            self.current_evsieve.terminate()
            try:
                self.current_evsieve.wait(timeout=2)
            except:
                self.current_evsieve.kill()
            self.current_evsieve = None

        if os.path.islink(self.virtual_link):
            try:
                os.remove(self.virtual_link)
            except:
                pass

        self.current_device = None
        self.current_device_name = None
        self.update_status(False)

    def start_mapping(self, event, vid, pid, name):
        evdev_path = f"/dev/input/{event}"
        self.log(f"Starting mapping for {name} ({vid}:{pid}) at {evdev_path}...")

        evsieve_bin = shutil.which("evsieve")
        xboxdrv_bin = shutil.which("xboxdrv")

        if not xboxdrv_bin:
            self.log("Error: xboxdrv not found")
            return

        try:
            # Decide if we use evsieve
            use_evsieve = evsieve_bin is not None
            input_device = evdev_path

            if use_evsieve:
                self.log("Using evsieve for device grabbing")
                self.current_evsieve = subprocess.Popen([
                    evsieve_bin, "--input", evdev_path, "grab", "ff",
                    "--output", f"create-link={self.virtual_link}", "name=Evsieve DS4 Virtual"
                ])

                for _ in range(20):
                    if os.path.islink(self.virtual_link): break
                    time.sleep(0.5)
                else:
                    self.log("Failed to create evsieve virtual link, falling back to direct evdev")
                    self.current_evsieve.terminate()
                    self.current_evsieve = None
                    use_evsieve = False

                if use_evsieve:
                    input_device = os.path.realpath(self.virtual_link)

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

            self.current_xboxdrv = subprocess.Popen(xboxdrv_cmd)
            self.log("xboxdrv started")
            self.current_device = f"{vid}:{pid}:{event}"
            self.current_device_name = name
            self.update_status(True, device=name)

        except Exception as e:
            self.log(f"Error starting mapping: {e}")
            self.cleanup()

    def run(self):
        self.log("Backend started")
        while self.running:
            self.config = self.load_config()
            check_interval = self.config.getint('settings', 'check_interval', fallback=5)

            res = self.find_controller()
            steam_running = self.is_steam_running()

            if res:
                event, vid, pid, name = res
                device_id = f"{vid}:{pid}:{event}"

                if steam_running:
                    if self.current_device:
                        self.log("Steam detected, pausing mapping...")
                        self.cleanup()
                    self.update_status(False, steam_blocking=True)
                elif device_id != self.current_device:
                    if self.current_device:
                        self.log("Device changed, restarting mapping...")
                        self.cleanup()
                    self.start_mapping(event, vid, pid, name)
                else:
                    # Auto-resume or Health check
                    if not self.current_xboxdrv:
                        self.log("Resuming mapping (Steam closed or device back)...")
                        self.start_mapping(event, vid, pid, name)
                    elif (self.current_evsieve and self.current_evsieve.poll() is not None) or \
                       (self.current_xboxdrv and self.current_xboxdrv.poll() is not None):
                        self.log("Process died, restarting...")
                        self.cleanup()
                        self.start_mapping(event, vid, pid, name)
            else:
                if self.current_device:
                    self.log("Controller disconnected.")
                    self.cleanup()
                self.update_status(False, steam_blocking=steam_running)

            time.sleep(check_interval)

if __name__ == "__main__":
    backend = Backend()
    def signal_handler(sig, frame):
        backend.cleanup()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    backend.run()
