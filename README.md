# PNP (PS NOT PS)

PNP is a high-performance, lightweight PlayStation controller assistant for Linux. It maps DualShock 3, DualShock 4, and DualSense controllers to virtual Xbox 360 devices, while intelligently integrating with Steam Input to provide a seamless gaming experience.

## Features

- **Native Xbox 360 Emulation**: Uses `evdev.uinput` to create high-performance virtual controllers without external dependencies like `xboxdrv`.
- **Steam Input Handover**: Automatically detects when Steam is running a game and yields control to Steam Input, avoiding "double input" and allowing you to use community controller profiles.
- **Non-Steam Game Support**: Effortlessly play standalone games, emulators, or games from other launchers (Heroic, Lutris) with full Steam Input features using the `pnp-steam-run` wrapper.
- **Smart Game Detection**: Monitors the system for active games using advanced heuristics (scanning for SDL/Vulkan/GL libraries and Steam AppIDs).
- **Profile Downloader**: Automatically identifies games and attempts to apply matching Steam Input community configurations.
- **XDG Compliant**: Follows modern Linux filesystem standards. Config is stored in `~/.config/pnp/config.jsonc`.
- **JSONC Support**: Configuration uses JSON with comments, making it easy to understand and modify.
- **Input Tester**: Built-in visualizer to verify your virtual controller mapping and inputs in real-time.
- **Systemd Integration**: Runs as a background user service for a "set and forget" experience.

## Installation

### Dependencies

Ensure you have the following installed:
- `python3` (>= 3.10)
- `evsieve`
- `python-evdev`
- `python-pyudev`
- `python-commentjson`
- `python-pyxdg`
- `python-requests`
- `gtk4` & `libadwaita` (for GUI)

### Arch Linux
```bash
yay -S pnp
```

### Debian/Ubuntu
```bash
sudo apt install evsieve python3-evdev python3-pyudev python3-requests python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
# Then install pnp via the provided .deb or source
```

## Configuration

PNP uses a JSONC configuration file located at `~/.config/pnp/config.jsonc`.

### Key Options

| Option | Default | Description |
|--------|---------|-------------|
| `poll_interval_ms` | `2000` | How often to scan for new games/controllers. |
| `steam_handover_enabled` | `true` | Yield control to Steam Input when a game is detected. |
| `profile_downloader_enabled` | `true` | Automatically fetch game-specific configs. |
| `rumble_gain` | `15%` | Global vibration strength. |

## Usage

### Background Operation
To run PNP automatically on login:
```bash
systemctl --user enable --now pnp.service
```

### Launching Non-Steam Games
To force Steam Input features (like Gyro or community layouts) on any standalone executable:
```bash
pnp-steam-run /path/to/game.exe
```

### GUI Management
Launch the management interface to monitor controllers, view logs, or test inputs:
```bash
pnp-gui
```

## Troubleshooting

- **No controllers detected**: Ensure your controller is connected via USB or Bluetooth and that your user is in the `input` group.
- **Steam Input not engaging**: Make sure Steam is running. For non-Steam games, always use the `pnp-steam-run` wrapper.
- **Input Double-Detection**: Ensure PNP is running. It uses `evsieve` to grab the physical device, hiding it from games while its virtual counterpart is active.

## License

PNP is released under the **MIT License**.
