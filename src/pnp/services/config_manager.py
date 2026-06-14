import os
import shutil
import logging
import commentjson
from xdg import BaseDirectory

logger = logging.getLogger(__name__)

# XDG Paths
CONFIG_HOME = BaseDirectory.save_config_path('pnp')
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_HOME, "config.jsonc")

# Legacy Paths for Migration
LEGACY_SYSTEM_CONFIG = "/etc/pnp/pnp.conf"
LEGACY_USER_CONFIG = os.path.expanduser("~/.pnp/pnp.conf")

class ConfigManager:
    def __init__(self, config_path=None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = {}
        self.load_defaults()
        self._migrate_legacy_config()
        self.load_config()

    def load_defaults(self):
        self.config = {
            "poll_interval_ms": 2000,
            "steam_handover_enabled": True,
            "profile_downloader_enabled": True,
            "log_level": "INFO",
            "rumble_gain": "15%",
            "mapping": {
                "axismap": "-y1=y1,-y2=y2",
                "absmap": "ABS_X=x1,ABS_Y=y1,ABS_RX=x2,ABS_RY=y2,ABS_Z=lt,ABS_RZ=rt,ABS_HAT0X=dpad_x,ABS_HAT0Y=dpad_y",
                "keymap": "BTN_SOUTH=a,BTN_EAST=b,BTN_NORTH=x,BTN_WEST=y,BTN_TL=lb,BTN_TR=rb,BTN_TL2=lt,BTN_TR2=rt,BTN_THUMBL=tl,BTN_THUMBR=tr,BTN_SELECT=back,BTN_START=start,BTN_MODE=guide"
            }
        }

    def load_config(self):
        if not os.path.exists(self.config_path):
            self.save_config()
            return

        try:
            with open(self.config_path, "r") as f:
                loaded_config = commentjson.load(f)
                # Deep merge or update
                self.config.update(loaded_config)
            logger.info(f"Loaded config from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")

    def save_config(self):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as f:
                commentjson.dump(self.config, f, indent=4)
            logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _migrate_legacy_config(self):
        """
        Migrates old .conf (INI) files to new JSONC format.
        """
        if os.path.exists(self.config_path):
            return

        legacy_path = None
        if os.path.exists(LEGACY_USER_CONFIG):
            legacy_path = LEGACY_USER_CONFIG
        elif os.path.exists(LEGACY_SYSTEM_CONFIG):
            legacy_path = LEGACY_SYSTEM_CONFIG

        if legacy_path:
            logger.info(f"Migrating legacy config from {legacy_path}...")
            try:
                import configparser
                parser = configparser.ConfigParser(interpolation=None, delimiters=('=',))
                parser.read(legacy_path)

                # Simple migration of known keys
                if 'settings' in parser:
                    s = parser['settings']
                    self.config["poll_interval_ms"] = int(s.get('polling_interval_ms', 2000))
                    self.config["rumble_gain"] = s.get('rumble_gain', '15%')

                if 'mapping' in parser:
                    m = parser['mapping']
                    self.config['mapping']['axismap'] = m.get('axismap', self.config['mapping']['axismap'])
                    self.config['mapping']['absmap'] = m.get('absmap', self.config['mapping']['absmap'])
                    self.config['mapping']['keymap'] = m.get('keymap', self.config['mapping']['keymap'])

                self.save_config()
                logger.info("Migration successful.")
            except Exception as e:
                logger.error(f"Migration failed: {e}")

    def get_controller_config(self, serial):
        # We could support per-controller JSONC in XDG_CONFIG_HOME/pnp/controllers/
        return self.config
