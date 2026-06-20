import subprocess
import threading
import time
from queue import Queue
from loguru import logger
from PySide6.QtCore import QObject, Signal, Slot

class BluetoothScanner(QObject):
    logReceived = Signal(str, str)  # message, prefix
    scanFinished = Signal(str)

    def __init__(self):
        super().__init__()
        self.process = None
        self.journal_process = None
        self.running = False
        self.callbacks = []

    def start_monitoring(self):
        """Start monitoring Bluetooth events with full logging"""
        if self.running:
            return

        self.running = True

        # 1. Enable Bluetooth power (if not already on)
        try:
            subprocess.run(["bluetoothctl", "power", "on"],
                           capture_output=True, check=False)
        except Exception as e:
            logger.error(f"Failed to power on Bluetooth: {e}")

        # 2. Start bluetoothctl monitor for real-time events
        # Note: BlueZ 5.77+ moved 'monitor' to a submenu or requires 'on'
        # We try 'monitor on' first, then fallback to entering the menu and 'on'
        # or just 'monitor' for very old versions.
        try:
            # Check version
            ver_res = subprocess.run(["bluetoothctl", "--version"], capture_output=True, text=True)
            version = ver_res.stdout.strip()
            logger.debug(f"BlueZ version: {version}")

            cmd = ["bluetoothctl", "monitor", "on"]
            if version and version >= "5.77":
                 # In new versions, it might need to be run as: bluetoothctl monitor on
                 pass

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            # Check if it failed immediately (invalid command)
            time.sleep(0.5)
            if self.process.poll() is not None:
                 raise Exception("Command failed immediately")

        except Exception as e:
            logger.debug(f"Failed to start bluetoothctl monitor with primary command: {e}. Trying fallback.")
            try:
                # Fallback to standard monitor (old BlueZ)
                self.process = subprocess.Popen(
                    ["bluetoothctl", "monitor"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
            except Exception as e2:
                logger.error(f"Failed to start bluetoothctl monitor fallback: {e2}")

        # 3. Start journalctl monitoring for BlueZ logs
        try:
            self.journal_process = subprocess.Popen(
                ["journalctl", "-u", "bluetooth", "-f", "-o", "cat"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
        except Exception as e:
            logger.error(f"Failed to start journalctl monitor: {e}")

        # 4. Start threads to read both outputs
        if self.process:
            threading.Thread(target=self._read_stdout, args=(self.process, "[BLUETOOTHCTL]"), daemon=True).start()
        if self.journal_process:
            threading.Thread(target=self._read_stdout, args=(self.journal_process, "[JOURNAL]"), daemon=True).start()

        logger.info("Bluetooth monitoring started")

    def _read_stdout(self, process, prefix):
        """Read stdout from subprocess and log it"""
        for line in process.stdout:
            if not self.running:
                break
            line = line.strip()
            if line:
                # Handle 'Invalid command' response from bluetoothctl
                if "Invalid command" in line and "monitor" in line:
                    logger.warning("bluetoothctl monitor failed. Version mismatch.")
                    self.logReceived.emit("FAILED to start monitor. Try manual: bluetoothctl monitor on", prefix)
                    continue

                logger.debug(f"{prefix} {line}")
                self.logReceived.emit(line, prefix)
                for callback in self.callbacks:
                    try:
                        callback(line, prefix)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")

    def scan_devices(self, timeout=10):
        """Scan for nearby Bluetooth devices in a separate thread"""
        def _do_scan():
            logger.info("Starting Bluetooth scan...")

            try:
                # Start scan
                subprocess.Popen(["bluetoothctl", "scan", "on"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)

                # Wait for devices to appear
                time.sleep(timeout)

                # Stop scan
                subprocess.run(["bluetoothctl", "scan", "off"], capture_output=True)

                # Get device list
                devices = subprocess.run(
                    ["bluetoothctl", "devices"],
                    capture_output=True,
                    text=True
                )

                logger.info(f"Scan complete. Found {len(devices.stdout.splitlines())} devices.")
                self.scanFinished.emit(devices.stdout)
            except Exception as e:
                logger.error(f"Bluetooth scan failed: {e}")
                self.scanFinished.emit("")

        threading.Thread(target=_do_scan, daemon=True).start()

    def get_device_info(self, mac_address):
        """Get detailed information about a specific device"""
        try:
            result = subprocess.run(
                ["bluetoothctl", "info", mac_address],
                capture_output=True,
                text=True
            )
            logger.debug(f"Device info for {mac_address}: {result.stdout}")
            return result.stdout
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return ""

    def _log_sm(self, message):
        prefix = "[SM]"
        logger.debug(f"{prefix} {message}")
        self.logReceived.emit(message, prefix)

    def pair_device(self, mac_address):
        """Pair with a Bluetooth device using a robust state machine"""
        self._log_sm(f"Starting pairing state machine for {mac_address}")

        try:
            # 0. Pre-checks: Service and Modules
            self._ensure_bt_service()
            self._ensure_bt_modules()

            # 1. Power On
            self._log_sm("Pairing SM [1/6]: Powering on...")
            subprocess.run(["bluetoothctl", "power", "on"], capture_output=True, check=False)

            # 2. Agent
            self._log_sm("Pairing SM [2/6]: Enabling agent...")
            subprocess.run(["bluetoothctl", "agent", "on"], capture_output=True, check=False)
            subprocess.run(["bluetoothctl", "default-agent"], capture_output=True, check=False)

            # 3. Clean start if needed
            # We don't remove /var/lib/bluetooth here as it needs root/polkit,
            # but we remove from bluetoothctl
            self._log_sm(f"Pairing SM [3/6]: Removing existing device {mac_address} if any...")
            subprocess.run(["bluetoothctl", "remove", mac_address], capture_output=True, check=False)

            # 4. Pair
            self._log_sm(f"Pairing SM [4/6]: Attempting to pair with {mac_address}")
            result = subprocess.run(
                ["bluetoothctl", "pair", mac_address],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                err_msg = result.stderr.strip() or result.stdout.strip()
                self._log_sm(f"Pairing SM [FAIL]: Pairing failed: {err_msg}")

                # Heuristic for SDP error or Host is down
                if "Protocol error" in err_msg or "Host is down" in err_msg:
                    logger.warning("Detected SDP or connection protocol error. Suggesting cache clear via Polkit.")

                return False

            # 5. Trust
            self._log_sm(f"Pairing SM [5/6]: Trusting {mac_address}")
            subprocess.run(["bluetoothctl", "trust", mac_address], capture_output=True, check=False)

            # 6. Connect
            self._log_sm(f"Pairing SM [6/6]: Connecting to {mac_address}")
            conn_result = subprocess.run(
                ["bluetoothctl", "connect", mac_address],
                capture_output=True,
                text=True,
                timeout=20
            )

            if conn_result.returncode == 0:
                self._log_sm(f"Pairing SM [SUCCESS]: {mac_address} is paired, trusted, and connected.")
                return True
            else:
                self._log_sm(f"Pairing SM [PARTIAL]: Paired/Trusted, but connection failed: {conn_result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self._log_sm(f"Pairing SM [TIMEOUT]: Operation timed out for {mac_address}")
            return False
        except Exception as e:
            self._log_sm(f"Pairing SM [ERROR]: Unexpected exception: {e}")
            logger.exception(e)
            return False

    def _ensure_bt_service(self):
        """Checks if bluetooth service is active"""
        try:
            res = subprocess.run(["systemctl", "is-active", "bluetooth"], capture_output=True, text=True)
            if res.stdout.strip() != 'active':
                logger.warning("Bluetooth service not active. PNP diagnostics will offer fix.")
        except Exception:
            pass

    def _ensure_bt_modules(self):
        """Check for required kernel modules"""
        modules = ['btusb', 'hidp', 'hid_generic']
        for mod in modules:
            try:
                res = subprocess.run(f"lsmod | grep {mod}", shell=True, capture_output=True)
                if res.returncode != 0:
                    logger.warning(f"Kernel module {mod} might not be loaded. This can cause HID issues.")
            except Exception:
                pass

    def connect_device(self, mac_address):
        """Connect to a paired Bluetooth device"""
        logger.info(f"Connecting to {mac_address}")
        try:
            result = subprocess.run(
                ["bluetoothctl", "connect", mac_address],
                capture_output=True,
                text=True,
                timeout=20
            )

            if result.returncode == 0:
                logger.info(f"Connected to {mac_address}")
                return True
            else:
                logger.error(f"Connection failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Connection exception: {e}")
            return False

    def stop_monitoring(self):
        """Stop all monitoring processes"""
        self.running = False
        if self.process:
            self.process.terminate()
        if self.journal_process:
            self.journal_process.terminate()
        logger.info("Bluetooth monitoring stopped")

    def add_callback(self, callback):
        """Add callback function to receive log lines in real-time"""
        self.callbacks.append(callback)
