import evdev
from evdev import ecodes as e
from loguru import logger


class VirtualController:
    """
    Native uinput implementation of an Xbox 360 controller using python-evdev.
    Replaces the external xboxdrv dependency.
    """
    def __init__(self, name="Xbox 360 Wireless Receiver (PNP)"):
        self.name = name
        self.device = None

        # Define Xbox 360 controller capabilities
        self.cap = {
            e.EV_KEY: [
                e.BTN_SOUTH, e.BTN_EAST, e.BTN_NORTH, e.BTN_WEST,  # A, B, X, Y
                e.BTN_TL, e.BTN_TR,  # LB, RB
                e.BTN_SELECT, e.BTN_START, e.BTN_MODE,  # Back, Start, Guide
                e.BTN_THUMBL, e.BTN_THUMBR,  # Thumb L, Thumb R
            ],
            e.EV_ABS: [
                (e.ABS_X, evdev.AbsInfo(value=0, min=-32768, max=32767,
                                        fuzz=16, flat=128, resolution=0)),
                (e.ABS_Y, evdev.AbsInfo(value=0, min=-32768, max=32767,
                                        fuzz=16, flat=128, resolution=0)),
                (e.ABS_Z, evdev.AbsInfo(value=0, min=0, max=255,
                                        fuzz=0, flat=0, resolution=0)),  # LT
                (e.ABS_RX, evdev.AbsInfo(value=0, min=-32768, max=32767,
                                         fuzz=16, flat=128, resolution=0)),
                (e.ABS_RY, evdev.AbsInfo(value=0, min=-32768, max=32767,
                                         fuzz=16, flat=128, resolution=0)),
                (e.ABS_RZ, evdev.AbsInfo(value=0, min=0, max=255,
                                         fuzz=0, flat=0, resolution=0)),  # RT
                (e.ABS_HAT0X, evdev.AbsInfo(value=0, min=-1, max=1,
                                            fuzz=0, flat=0, resolution=0)),
                (e.ABS_HAT0Y, evdev.AbsInfo(value=0, min=-1, max=1,
                                            fuzz=0, flat=0, resolution=0)),
            ]
        }

    def start(self):
        try:
            self.device = evdev.UInput(
                self.cap, name=self.name, vendor=0x045e,
                product=0x02a1, version=0x0110
            )
            logger.info(f"Created virtual controller: {self.name}")
        except Exception as err:
            logger.error(f"Failed to create uinput device: {err}")
            raise

    def emit(self, ev_type, code, value, syn=True):
        if self.device:
            self.device.write(ev_type, code, value)
            if syn:
                self.device.syn()

    def stop(self):
        if self.device:
            self.device.close()
            self.device = None
            logger.info(f"Stopped virtual controller: {self.name}")
