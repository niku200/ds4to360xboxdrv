import pyudev
import pyudev.glib
import logging
from gi.repository import GObject, GLib

logger = logging.getLogger(__name__)

class DeviceMonitor(GObject.Object):
    __gsignals__ = {
        'controller-added': (GObject.SignalFlags.RUN_FIRST, None, (str, str, str)), # path, name, serial
        'controller-removed': (GObject.SignalFlags.RUN_FIRST, None, (str,)), # path
    }

    SONY_VENDORS = ["054c", "054C"] # Sony Interactive Entertainment

    def __init__(self):
        GObject.Object.__init__(self)
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='input')

        self.observer = None

    def start(self):
        # Initial scan
        for device in self.context.list_devices(subsystem='input', ID_INPUT_JOYSTICK='1'):
            if self._is_sony_controller(device):
                self._add_device(device)

        # Start monitoring
        self.observer = pyudev.glib.MonitorObserver(self.monitor)
        self.observer.connect('device-event', self._on_device_event)
        self.monitor.start()
        logger.info("Device monitor started.")

    def _is_sony_controller(self, device):
        vendor = device.get('ID_VENDOR_ID')
        return vendor in self.SONY_VENDORS and device.get('ID_INPUT_JOYSTICK') == '1' and device.device_node and "event" in device.device_node

    def _on_device_event(self, observer, device):
        action = device.action
        if action == 'add' and self._is_sony_controller(device):
            self._add_device(device)
        elif action == 'remove' and self._is_sony_controller(device):
            self._remove_device(device)

    def _add_device(self, device):
        path = device.device_node
        name = device.get('ID_MODEL', 'Unknown Sony Controller')
        serial = device.get('ID_SERIAL_SHORT', '0000')
        logger.info(f"Controller added: {name} at {path}")
        self.emit('controller-added', path, name, serial)

    def _remove_device(self, device):
        path = device.device_node
        logger.info(f"Controller removed: {path}")
        self.emit('controller-removed', path)
