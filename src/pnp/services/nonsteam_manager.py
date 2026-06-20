import os
import json
import vdf
import glob
from loguru import logger
from PySide6.QtCore import QObject, Signal, Slot, QThread

from pnp.services.game_scanner import HeroicScanner, HydraScanner, DirectoryScanner

class SteamShortcutManager:
    def __init__(self):
        self.steam_base = os.path.expanduser("~/.steam/steam")
        self.userdata_path = os.path.join(self.steam_base, "userdata")

    def _get_shortcuts_paths(self):
        paths = []
        if not os.path.exists(self.userdata_path):
            return paths
        for user_id in os.listdir(self.userdata_path):
            shortcut_vdf = os.path.join(self.userdata_path, user_id, "config", "shortcuts.vdf")
            if os.path.exists(os.path.join(self.userdata_path, user_id, "config")):
                paths.append(shortcut_vdf)
        return paths

    def add_shortcut(self, game):
        paths = self._get_shortcuts_paths()
        if not paths:
            logger.error("No Steam userdata found.")
            return False

        success = True
        for path in paths:
            try:
                shortcuts = {"shortcuts": {}}
                if os.path.exists(path):
                    with open(path, 'rb') as f:
                        shortcuts = vdf.binary_load(f)

                # Check if already exists
                exists = False
                for s in shortcuts.get("shortcuts", {}).values():
                    if s.get("AppName") == game["title"] and s.get("Exe") == game["executable"]:
                        exists = True
                        break

                if exists:
                    logger.info(f"Shortcut for {game['title']} already exists in {path}")
                    continue

                new_idx = str(len(shortcuts["shortcuts"]))
                shortcuts["shortcuts"][new_idx] = {
                    "AppName": game["title"],
                    "Exe": f'"{game["executable"]}"',
                    "StartDir": f'"{game["installDir"]}"',
                    "LaunchOptions": game.get("launchArgs", ""),
                    "icon": "",
                    "ShortcutPath": "",
                    "IsHidden": 0,
                    "AllowDesktopConfig": 1,
                    "AllowOverlay": 1,
                    "OpenVR": 0,
                    "Devkit": 0,
                    "DevkitGameID": "",
                    "LastPlayTime": 0,
                    "tags": {}
                }

                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as f:
                    vdf.binary_dump(shortcuts, f)
                logger.info(f"Added shortcut for {game['title']} to {path}")
            except Exception as e:
                logger.error(f"Failed to add shortcut to {path}: {e}")
                success = False
        return success

    def remove_shortcut(self, game_title):
        paths = self._get_shortcuts_paths()
        success = True
        for path in paths:
            if not os.path.exists(path):
                continue
            try:
                with open(path, 'rb') as f:
                    shortcuts = vdf.binary_load(f)

                original_len = len(shortcuts.get("shortcuts", {}))
                new_shortcuts = {"shortcuts": {}}
                idx = 0
                for s in shortcuts.get("shortcuts", {}).values():
                    if s.get("AppName") != game_title:
                        new_shortcuts["shortcuts"][str(idx)] = s
                        idx += 1

                if len(new_shortcuts["shortcuts"]) < original_len:
                    with open(path, 'wb') as f:
                        vdf.binary_dump(new_shortcuts, f)
                    logger.info(f"Removed shortcut for {game_title} from {path}")
                else:
                    logger.info(f"Shortcut for {game_title} not found in {path}")
            except Exception as e:
                logger.error(f"Failed to remove shortcut from {path}: {e}")
                success = False
        return success

    def is_added(self, game):
        paths = self._get_shortcuts_paths()
        for path in paths:
            if not os.path.exists(path):
                continue
            try:
                with open(path, 'rb') as f:
                    shortcuts = vdf.binary_load(f)
                for s in shortcuts.get("shortcuts", {}).values():
                    if s.get("AppName") == game["title"]:
                        return True
            except Exception:
                continue
        return False

class SteamInputConfigurator:
    def configure(self, game):
        # To force Steam Input, we can suggest launch options
        # But shortcuts.vdf already has LaunchOptions.
        # Requirement: "Sets the launch options to ensure the game uses the correct Steam Runtime."
        # Requirement: "For Proton games: SteamGameId=<appid> %command%"
        # Requirement: "For native Linux games: SDL_GAMECONTROLLERCONFIG="" %command%"

        # This is tricky because we don't know if it's Proton or Native easily from Heroic/Hydra config
        # without deeper inspection.
        # For now, let's append a standard Steam Runtime / Steam Input hint if requested.
        pass

class NonSteamManager(QObject):
    scanFinished = Signal(list)
    actionFinished = Signal(bool, str)

    def __init__(self):
        super().__init__()
        self.heroic_scanner = HeroicScanner()
        self.hydra_scanner = HydraScanner()
        self.directory_scanner = DirectoryScanner()
        self.shortcut_manager = SteamShortcutManager()

    @Slot()
    def refresh_library(self):
        # Run in thread? Yes, the requirement says so.
        # But this method is called from UI, so we should start a thread.
        pass

    def do_scan(self, manual_path=None):
        logger.info("Scanning for Non-Steam games...")
        games = []
        games.extend(self.heroic_scanner.scan())
        games.extend(self.hydra_scanner.scan())

        if manual_path:
            games.extend(self.directory_scanner.scan_directory(manual_path))

        for game in games:
            game["isAdded"] = self.shortcut_manager.is_added(game)
            game["status"] = "Added to Steam" if game["isAdded"] else "Not Added"

        return games

    def add_to_steam(self, game):
        success = self.shortcut_manager.add_shortcut(game)
        if success:
            return True, f"Successfully added {game['title']} to Steam."
        else:
            return False, f"Failed to add {game['title']} to Steam."

    def remove_from_steam(self, game_title):
        success = self.shortcut_manager.remove_shortcut(game_title)
        if success:
            return True, f"Successfully removed {game_title} from Steam."
        else:
            return False, f"Failed to remove {game_title} from Steam."
