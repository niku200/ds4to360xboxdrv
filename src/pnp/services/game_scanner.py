import os
import json
import glob
from loguru import logger

class HeroicScanner:
    def __init__(self, heroic_games_dir=None):
        self.native_config_dir = os.path.expanduser("~/.config/heroic/GamesConfig")
        self.flatpak_config_dir = os.path.expanduser("~/.var/app/com.heroicgameslauncher.hgl/config/heroic/GamesConfig")
        self.games_dir = heroic_games_dir or os.path.expanduser("~/Games/Heroic")

    def scan(self):
        games = []
        configs = []

        # Scan native configs
        if os.path.exists(self.native_config_dir):
            configs.extend(glob.glob(os.path.join(self.native_config_dir, "*.json")))

        # Scan flatpak configs
        if os.path.exists(self.flatpak_config_dir):
            configs.extend(glob.glob(os.path.join(self.flatpak_config_dir, "*.json")))

        if not configs:
            logger.warning("No Heroic configuration files found.")

        for config_file in configs:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    game = {
                        "id": data.get("appName"),
                        "title": data.get("title"),
                        "installDir": data.get("installDir"),
                        "executable": data.get("executable"),
                        "launchArgs": data.get("launchArgs", ""),
                        "source": "Heroic",
                        "icon": "heroic"
                    }
                    if game["title"] and game["executable"]:
                        games.append(game)
            except Exception as e:
                logger.error(f"Error parsing Heroic config {config_file}: {e}")
        return games

class HydraScanner:
    def __init__(self, hydra_games_dir=None):
        self.config_dir = os.path.expanduser("~/.config/hydralauncher")
        self.games_dir = hydra_games_dir or os.path.expanduser("~/.local/share/hydra/games")

    def scan(self):
        games = []
        manifest_path = os.path.join(self.config_dir, "games.json")
        if not os.path.exists(manifest_path):
            logger.warning(f"Hydra manifest not found at {manifest_path}.")
            return games

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        game = {
                            "id": item.get("id") or item.get("name"),
                            "title": item.get("name"),
                            "installDir": item.get("installPath"),
                            "executable": item.get("executablePath"),
                            "launchArgs": item.get("launchOptions", ""),
                            "source": "Hydra",
                            "icon": "hydra"
                        }
                        if game["title"] and game["executable"]:
                            games.append(game)
        except Exception as e:
            logger.error(f"Error parsing Hydra manifest: {e}")
        return games

class DirectoryScanner:
    @staticmethod
    def scan_directory(path):
        """Simple directory scanner for executables"""
        games = []
        if not os.path.exists(path):
            return games

        # Search for .exe and ELF files
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".exe") or (os.access(os.path.join(root, file), os.X_OK) and "." not in file):
                    # Heuristic: limit depth or look for common game patterns
                    if root.count(os.sep) - path.count(os.sep) > 2:
                        continue

                    games.append({
                        "id": file,
                        "title": file,
                        "installDir": root,
                        "executable": os.path.join(root, file),
                        "launchArgs": "",
                        "source": "Manual",
                        "icon": "folder"
                    })
        return games
