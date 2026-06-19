# 🎮 PNP (PS NOT PS) — PlayStation to Xbox Controller Emulator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/platform-linux-lightgrey.svg)](https://www.kernel.org/)
[![UI: PySide6](https://img.shields.io/badge/UI-PySide6%20%2F%20QML-41cd52.svg)](https://www.qt.io/qt-for-python)

**PNP (PS NOT PS)** is a high-performance, lightweight PlayStation controller assistant for Linux. It transforms your DualShock 3, DualShock 4, and DualSense controllers into virtual Xbox 360 devices, providing a "set and forget" solution for playing games on Linux while maintaining intelligent integration with Steam.

---

## ✨ Features

- **🚀 Native Xbox 360 Emulation**: Built-in `uinput` implementation for low-latency, high-performance virtual controllers. No legacy dependencies like `xboxdrv` required.
- **🤝 Intelligent Steam Handover**: PNP automatically detects when a game is running under Steam Input and pauses itself. This prevents "double input" and lets you use community Steam Input profiles seamlessly.
- **🎨 Modern UI/UX**: Completely redesigned frontend using **PySide6** and **Qt Quick (QML)** for a smooth, responsive, and visually stunning experience.
- **🎮 Stealth Mode**: Uses `evsieve` to **grab** (hide) the physical PlayStation controller from the system. Games only see the virtual Xbox 360 device.
- **🔥 Non-Steam Game Power**: Use the `pnp-steam-run` wrapper to force Steam Input features (Gyro, Touchpad, Community Layouts) on *any* standalone executable or emulator.
- **🔋 Battery Tracking**: Real-time monitoring of controller battery levels and charging status directly in the GUI.
- **🔍 Visual Input Tester**: A beautiful, real-time visualizer to verify your button mappings and stick accuracy at 60Hz.
- **🛡️ Diagnostic System**: Built-in system health checks with one-click automated recovery via Polkit.
- **📜 Professional Logging**: Integrated with **Loguru** for real-time, color-coded logging in both terminal and GUI.
- **⚙️ XDG & JSONC**: Fully compliant with Linux filesystem standards. Easy-to-edit configuration using JSON with comments (JSONC).
- **🛠️ Systemd Integration**: Runs as a background service so your controllers "just work" the moment you plug them in or connect via Bluetooth.

---

## 📥 Installation

### 1. Dependencies
PNP requires the following system components:
- **Core**: `python3 (>= 3.10)`, `evsieve`
- **Python Libs**: `PySide6`, `loguru`, `evdev`, `pyudev`, `requests`, `pyxdg`, `commentjson`

### 2. Distro-Specific Commands

#### Arch Linux (AUR)
```bash
# Using your favourite AUR helper
yay -S pnp
```

#### Debian / Ubuntu / Mint
```bash
sudo apt update
sudo apt install evsieve python3-evdev python3-pyudev python3-requests
# Download the latest .deb from releases and run:
sudo apt install ./pnp_5.2.0_amd64.deb
```

#### Fedora
```bash
sudo dnf install evsieve python3-evdev python3-pyudev python3-requests
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

## 🖥️ GUI Overview

- **Monitor Tab**: Toggle individual controllers, see connected devices, and monitor battery levels in real-time.
- **Tester Tab**: A high-performance real-time visualizer for buttons, sticks, and triggers.
- **Settings Tab**: Configure handover behavior, rumble strength, system service, and custom mappings.
- **Logs Tab**: Professional log viewer with real-time updates from the background service and GUI.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

**PNP (PS NOT PS)** — *PlayStation controllers, at home on Linux.*
