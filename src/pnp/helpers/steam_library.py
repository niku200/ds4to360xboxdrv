import os
import re

def parse_vdf(content):
    # Very simple VDF parser for libraryfolders.vdf
    # Example: "path" "/home/user/.steam/steam"
    paths = re.findall(r'"path"\s+"([^"]+)"', content)
    return paths

def parse_acf(content):
    # Very simple ACF parser for appmanifest_*.acf
    # Example: "appid" "440", "name" "Team Fortress 2"
    appid = re.search(r'"appid"\s+"([^"]+)"', content)
    name = re.search(r'"name"\s+"([^"]+)"', content)
    if appid and name:
        return {"appid": appid.group(1), "name": name.group(1)}
    return None

def get_steam_games():
    steam_root = os.path.expanduser("~/.steam/steam")
    library_folders_vdf = os.path.join(steam_root, "steamapps/libraryfolders.vdf")

    if not os.path.exists(library_folders_vdf):
        return []

    with open(library_folders_vdf, "r", encoding="utf-8") as f:
        content = f.read()

    library_paths = parse_vdf(content)
    # Ensure root is included
    if steam_root not in library_paths:
        library_paths.append(steam_root)

    games = []
    for path in library_paths:
        steamapps_path = os.path.join(path, "steamapps")
        if not os.path.exists(steamapps_path):
            continue

        for acf_file in os.listdir(steamapps_path):
            if acf_file.startswith("appmanifest_") and acf_file.endswith(".acf"):
                with open(os.path.join(steamapps_path, acf_file), "r", encoding="utf-8") as f:
                    game_info = parse_acf(f.read())
                    if game_info:
                        games.append(game_info)

    # Sort games by name
    games.sort(key=lambda x: x["name"])
    return games
