import pyudev
from PySide6.QtCore import QObject, Signal, QSocketNotifier
from loguru import logger


class DeviceMonitor(QObject):
    controller_added = Signal(str, str, str)  # path, name, serial
    controller_removed = Signal(str)  # path

    SONY_VENDORS = ["054c", "054C"]  # Sony Interactive Entertainment

    def __init__(self):
        super().__init__()
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='input')

        self.notifier = None

    def start(self):
        # Initial scan
        for device in self.context.list_devices(
            subsystem='input', ID_INPUT_JOYSTICK='1'
        ):
            if self._is_supported_controller(device):
                self._add_device(device)

        # Start monitoring using QSocketNotifier
        self.monitor.start()
        self.notifier = QSocketNotifier(
            self.monitor.fileno(), QSocketNotifier.Read
        )
        self.notifier.activated.connect(self._on_monitor_event)
        logger.info("Device monitor started.")

    def _is_supported_controller(self, device):
        # Check if it's a joystick
        if device.get('ID_INPUT_JOYSTICK') != '1':
            return False

        # Avoid recursive detection: ignore virtual/emulated devices
        bus = device.get('ID_BUS')
        is_physical = bus in ['usb', 'bluetooth']

        model_name = device.get('ID_MODEL', '').lower()
        is_emulated = ('evsieve' in model_name or 'xbox' in model_name or
                       'pnp' in model_name)

        if not is_physical or is_emulated:
            return False

        if not device.device_node or "event" not in device.device_node:
            return False

        # Support common vendors or any joystick
        vendor = device.get('ID_VENDOR_ID', '').lower()
        # Sony: 054c, Xbox: 045e, Nintendo: 057e, Logitech: 046d
        supported_vendors = ["054c", "045e", "057e", "046d"]

        if vendor in supported_vendors:
            return True

        # Fallback for generic controllers
        logger.debug(f"Generic controller detected: {model_name} (Vendor: {vendor})")
        return True

    def _on_monitor_event(self):
        device = self.monitor.poll()
        if device is None:
            return

        action = device.action
        if action == 'add' and self._is_supported_controller(device):
            self._add_device(device)
        elif action == 'remove' and self._is_supported_controller(device):
            self._remove_device(device)

    def _add_device(self, device):
        path = device.device_node
        name = device.get('ID_MODEL') or device.get('ID_NAME') or 'Unknown Controller'
        serial = device.get('ID_SERIAL_SHORT', '0000')

        logger.info(f"Controller added: {name} at {path}")
        self.controller_added.emit(path, name, serial)

    def _remove_device(self, device):
        path = device.device_node
        logger.info(f"Controller removed: {path}")
        self.controller_removed.emit(path)
