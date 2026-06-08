import os
import configparser
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "/etc/pnp/pnp.conf"
LEGACY_CONFIG_PATH = "/etc/ds4to360.conf"
USER_CONFIG_DIR = os.path.expanduser("~/.config/pnp/controllers/")

class ConfigManager:
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.load_defaults()
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        elif os.path.exists(LEGACY_CONFIG_PATH):
            self.config.read(LEGACY_CONFIG_PATH)

    def load_defaults(self):
        if 'settings' not in self.config:
            self.config['settings'] = {}
        self.config['settings']['rumble_gain'] = '15%'
        self.config['settings']['steam_conflict_check'] = 'true'

        if 'mapping' not in self.config:
            self.config['mapping'] = {}
        self.config['mapping']['axismap'] = '-y1=y1,-y2=y2'
        self.config['mapping']['absmap'] = 'ABS_HAT0X=dpad_x,ABS_HAT0Y=dpad_y,ABS_X=X1,ABS_Y=Y1,ABS_RX=X2,ABS_RY=Y2,ABS_Z=LT,ABS_RZ=RT'
        self.config['mapping']['keymap'] = 'BTN_SOUTH=A,BTN_EAST=B,BTN_NORTH=Y,BTN_WEST=X,BTN_START=start,BTN_MODE=guide,BTN_SELECT=back,BTN_TL=LB,BTN_TR=RB,BTN_TL2=LT,BTN_TR2=RT,BTN_THUMBL=TL,BTN_THUMBR=TR'

    def get_controller_config(self, serial):
        # Look for per-controller config
        path = os.path.join(USER_CONFIG_DIR, f"{serial}.conf")
        if os.path.exists(path):
            c_config = configparser.ConfigParser()
            c_config.read(path)
            return c_config
        return self.config

    def save_global_config(self, settings_dict, mapping_dict):
        self.config['settings'].update(settings_dict)
        self.config['mapping'].update(mapping_dict)

        # We handle saving in the GUI using pkexec,
        # but this method might be called by the backend (unlikely for global config).
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as f:
                self.config.write(f)
        except Exception as e:
            logger.error(f"Failed to save global config: {e}")
