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
        try:
            self.process = subprocess.Popen(
                ["bluetoothctl", "monitor"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
        except Exception as e:
            logger.error(f"Failed to start bluetoothctl monitor: {e}")

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

    def pair_device(self, mac_address):
        """Pair with a Bluetooth device with full logging"""
        logger.info(f"Attempting to pair with {mac_address}")

        try:
            # Start pairing
            result = subprocess.run(
                ["bluetoothctl", "pair", mac_address],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(f"Pairing initiated with {mac_address}")
                # Trust the device after pairing
                subprocess.run(["bluetoothctl", "trust", mac_address], capture_output=True)
                return True
            else:
                logger.error(f"Pairing failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Pairing exception: {e}")
            return False

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
