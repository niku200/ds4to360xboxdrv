# 🎮 PNP (PS NOT PS) — PlayStation to Xbox Controller Emulator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/platform-linux-lightgrey.svg)](https://www.kernel.org/)
[![Gtk 4](https://img.shields.io/badge/UI-Gtk4%20%2F%20Libadwaita-7b8bb1.svg)](https://www.gtk.org/)

**PNP (PS NOT PS)** is a high-performance, lightweight PlayStation controller assistant for Linux. It transforms your DualShock 3, DualShock 4, and DualSense controllers into virtual Xbox 360 devices, providing a "set and forget" solution for playing games on Linux while maintaining intelligent integration with Steam.

---

## ✨ Features

- **🚀 Native Xbox 360 Emulation**: Built-in `uinput` implementation for low-latency, high-performance virtual controllers. No legacy dependencies like `xboxdrv` required.
- **🤝 Intelligent Steam Handover**: PNP automatically detects when a game is running under Steam Input and pauses itself. This prevents "double input" and lets you use community Steam Input profiles seamlessly.
- **🎮 Stealth Mode**: Uses `evsieve` to **grab** (hide) the physical PlayStation controller from the system. Games only see the virtual Xbox 360 device.
- **🔥 Non-Steam Game Power**: Use the `pnp-steam-run` wrapper to force Steam Input features (Gyro, Touchpad, Community Layouts) on *any* standalone executable or emulator.
- **📦 Profile Downloader**: Automatically identifies games via AppID and attempts to fetch and apply matching Steam Input community configurations.
- **🔋 Battery Tracking**: Real-time monitoring of controller battery levels and charging status directly in the GUI and system tray.
- **🔍 Visual Input Tester**: A beautiful, real-time visualizer to verify your button mappings and stick accuracy at 60Hz.
- **⚙️ XDG & JSONC**: Fully compliant with Linux filesystem standards. Easy-to-edit configuration using JSON with comments (JSONC).
- **🛠️ Systemd Integration**: Runs as a background service so your controllers "just work" the moment you plug them in or connect via Bluetooth.

---

## 🛠️ How it Works

PNP operates as a bridge between your physical hardware and the Linux input subsystem:
1. **Detection**: `udev` detects a PlayStation controller.
2. **Grabbing**: `evsieve` takes exclusive control of the physical device (hiding it from games).
3. **Emulation**: PNP creates a virtual Xbox 360 device using `uinput`.
4. **Mapping**: Inputs are scaled and translated from Sony's format to standard Xbox 360 axes and buttons.
5. **Yielding**: If Steam Input starts managing a game, PNP releases the "grab" to let Steam take over.

---

## 📥 Installation

### 1. Dependencies
PNP requires the following system components:
- **Core**: `python3 (>= 3.10)`, `evsieve`
- **Python Libs**: `evdev`, `pyudev`, `requests`, `pyxdg`, `commentjson`
- **GUI**: `gtk4`, `libadwaita`, `python-gobject`

### 2. Distro-Specific Commands

#### Arch Linux (AUR)
```bash
# Using your favourite AUR helper
yay -S pnp
```

#### Debian / Ubuntu / Mint
```bash
sudo apt update
sudo apt install evsieve python3-evdev python3-pyudev python3-requests python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
# Download the latest .deb from releases and run:
sudo apt install ./pnp_5.2.0_amd64.deb
```

#### Fedora
```bash
sudo dnf install evsieve python3-evdev python3-pyudev python3-requests python3-gobject gtk4 libadwaita
# Download the latest .rpm from releases and run:
sudo dnf install ./pnp-5.2.0.rpm
```

### 3. udev Rules
To ensure the service can manage controllers without root permissions, install the provided udev rules:
```bash
sudo cp 99-pnp.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

---

## 🚀 Quick Start

### Enable Background Service
For a "set and forget" experience, enable the PNP user service:
```bash
systemctl --user enable --now pnp.service
```

### Launch the Management GUI
Monitor controllers, test inputs, and change settings:
```bash
pnp-gui
```

---

## ⚙️ Configuration

The configuration file is located at `~/.config/pnp/config.jsonc`. It supports comments for easy documentation.

### Global Settings
| Option | Default | Description |
|--------|---------|-------------|
| `poll_interval_ms` | `2000` | Frequency for scanning active games/processes. |
| `steam_handover_enabled` | `true` | Automatically pause PNP when Steam Input is active. |
| `profile_downloader_enabled` | `true` | Automatically fetch community configs for games. |
| `rumble_gain` | `15%` | Adjust the global vibration strength. |

### Custom Mapping
You can customize how buttons and axes are translated. The default mapping covers standard PS4/PS5 to Xbox layouts.
```jsonc
"mapping": {
    "axismap": "-y1=y1,-y2=y2",
    "absmap": "ABS_X=x1,ABS_Y=y1,ABS_RX=x2,ABS_RY=y2,ABS_Z=lt,ABS_RZ=rt",
    "keymap": "BTN_SOUTH=a,BTN_EAST=b,BTN_NORTH=x,BTN_WEST=y,..."
}
```

---

## 🎮 Steam Integration

### Automatic Handover
PNP is designed to coexist with Steam. It monitors for the following conditions to yield control:
1. Steam is running.
2. A game process is detected (via `SteamAppId` or library heuristics).
3. A non-PNP virtual controller (Steam Input) is detected.

### pnp-steam-run (The Secret Weapon)
Want to use Steam Input features (like Gyro-to-Mouse) for a non-Steam game or emulator?
```bash
pnp-steam-run /path/to/your/game
```
This script forces Steam Input to engage by spoofing a Steam environment, allowing PNP to yield control to Steam's powerful configurator.

---

## ⌨️ Command Line Interface

PNP offers several CLI commands for headless management:

- `pnp start`: Start the background service.
- `pnp stop`: Stop the background service.
- `pnp status`: Show service status and active controllers.
- `pnp pause`: Manually pause emulation.
- `pnp resume`: Resume emulation.
- `pnp --headless`: Run the backend service in the current terminal.
- `pnp --debug`: Enable verbose logging for troubleshooting.

---

## 🖥️ GUI Overview

- **Status Tab**: Toggle the system service, see connected controllers, and view battery levels.
- **Settings Tab**: Configure handover behavior, rumble strength, and custom mappings.
- **Tester Tab**: A real-time visualizer for buttons, sticks (with deadzones), and triggers.
- **Logs Tab**: Live view of the systemd journal for PNP, color-coded for errors and warnings.

---

## ❓ Troubleshooting

- **Controller not detected**: Ensure your user is in the `input` group: `sudo usermod -aG input $USER` (then log out and back in).
- **Double Input in Games**: Ensure PNP is running. If it's stopped, the game might see both the physical and virtual devices.
- **Steam Handover issues**: Verify `steam_handover_enabled` is `true` in your config.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

**PNP (PS NOT PS)** — *PlayStation controllers, at home on Linux.*
