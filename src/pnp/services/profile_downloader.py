import os
import logging
import requests
import re
import glob
from gi.repository import GLib

logger = logging.getLogger(__name__)

class ProfileDownloader:
    """
    Automatically detects Steam AppIDs and manages controller configurations.
    """
    def __init__(self):
        self.steam_root = os.path.expanduser("~/.steam/steam")
        self.userdata_path = os.path.join(self.steam_root, "userdata")

    def detect_appid(self, game_path):
        """
        Attempts to detect the Steam AppID for a given game path.
        """
        if not game_path:
            return None

        # Method A: Check for steam_appid.txt
        game_dir = os.path.dirname(os.path.abspath(game_path))
        appid_file = os.path.join(game_dir, "steam_appid.txt")
        if os.path.exists(appid_file):
            try:
                with open(appid_file, "r") as f:
                    appid = f.read().strip()
                    if appid.isdigit():
                        logger.info(f"Detected AppID {appid} via steam_appid.txt")
                        return appid
            except Exception as e:
                logger.error(f"Error reading steam_appid.txt: {e}")

        # Method B: Search for .acf files in common Steam libraries
        # (Simplified for this refactor)

        return None

    def get_best_config(self, appid):
        """
        Attempts to find the best configuration for the given AppID.
        Prioritizes local templates or official configs if found.
        """
        if not appid:
            return None

        # Search for official configs in Steam's local shared directory
        # Path: steamapps/common/Steam Controller Configs/<ID>/config/<APPID>/
        search_pattern = os.path.join(
            self.steam_root, "steamapps", "common", "Steam Controller Configs", "*", "config", appid, "*.vdf"
        )
        configs = glob.glob(search_pattern)

        if configs:
            logger.info(f"Found local official config for AppID {appid}: {configs[0]}")
            try:
                with open(configs[0], "r") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading local config: {e}")

        # Fallback: Check for generic community templates in Steam's controller_base
        template_path = os.path.join(self.steam_root, "controller_base", "templates", "controller_ps4.vdf")
        if os.path.exists(template_path):
            logger.info(f"Using generic PS4 template for AppID {appid}")
            try:
                with open(template_path, "r") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading template: {e}")

        return None

    def apply_config(self, appid, config_vdf_content):
        """
        Writes the VDF configuration to the Steam userdata directory.
        """
        if not appid or not config_vdf_content:
            return False

        try:
            # Find the Steam UserID (usually the only directory in userdata/)
            user_dirs = [d for d in os.listdir(self.userdata_path) if d.isdigit()]
            if not user_dirs:
                logger.error("Could not find Steam userdata directory.")
                return False

            for user_id in user_dirs:
                config_dir = os.path.join(
                    self.userdata_path, user_id, "config", "controller_configs", "apps", appid
                )
                os.makedirs(config_dir, exist_ok=True)

                # Apply as a generic template or specific game config
                # Usually named like 'controller_ps4.vdf' or similar
                target_file = os.path.join(config_dir, "pnp_autoset.vdf")
                with open(target_file, "w") as f:
                    f.write(config_vdf_content)

                logger.info(f"Applied Steam Input config for AppID {appid} to user {user_id}")

            return True
        except Exception as e:
            logger.error(f"Failed to apply Steam Input config: {e}")
            return False

    def trigger_steam_reload(self):
        """
        Triggers Steam to reload configs.
        Opening a steam:// URI is one way to nudge it.
        """
        try:
            import subprocess
            subprocess.run(["steam", "steam://reloadcontrollerconfigs"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except:
            pass
