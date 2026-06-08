# PNP – PS NOT PS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AUR version](https://img.shields.io/aur/version/pnp.svg)](https://aur.archlinux.org/packages/pnp/)

**PNP (PS NOT PS)** is a modernized PlayStation to Xbox controller emulator for Linux. It allows you to use your DualShock 4, DualShock 3, or DualSense (PS5) controllers in any game or application that expects an Xbox 360 controller.

## Overview

PNP bridges the gap between PlayStation hardware and the Linux input system by creating a virtual Xbox 360 controller. It uses `evsieve` for robust device grabbing and `xboxdrv` for high-performance emulation. Whether you're playing via Steam, Lutris, or standalone games, PNP ensures your PlayStation controller "just works."

## Features

- **X11 & Wayland Support**: Fully compatible with both display servers, including explicit support for KDE Plasma 5 (Wayland).
- **Multi-Controller Support**: Simultaneously map multiple PlayStation controllers to unique Xbox 360 instances.
- **Hotplug Support**: Automatically detects and maps controllers when they are connected (USB or Bluetooth).
- **Modern GUI**: A beautiful GTK4/Libadwaita interface for monitoring status, logs, and adjusting settings.
- **Steam Auto-Pause**: Automatically pauses emulation when Steam is running to prevent input double-detection (Steam has its own PS controller support).
- **Systemd Integration**: Runs as a background service for seamless "set and forget" operation.
- **Exclusive Access**: Uses `evsieve --grab` to hide the original PlayStation device from games, avoiding "double input" issues.
- **Custom Mapping**: Fine-tune axis and button translations globally or per-controller.
- **Reliability**: Built-in watchdog monitor that automatically restarts backend processes if they fail.

## Requirements

The following system dependencies are required:

- `xboxdrv`: The core Xbox 360 controller emulator.
- `evsieve`: Used for device grabbing and event routing.
- `python3`: Minimum version 3.10.
- `gtk4` & `libadwaita`: For the graphical user interface.
- `systemd`: For service management.
- `python3-evdev` & `python3-pyudev`: Python bindings for input and device monitoring.

### Installation of Dependencies

**Debian/Ubuntu**:
```bash
sudo apt update
sudo apt install xboxdrv evsieve python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-evdev python3-venv
```

**Fedora**:
```bash
sudo dnf install xboxdrv evsieve python3-gobject gtk4 libadwaita python3-evdev
```

**Arch Linux**:
```bash
sudo pacman -S xboxdrv evsieve python-gobject gtk4 libadwaita python-evdev
```

## Installation

### From AUR (Arch Linux)
If you are on Arch Linux, you can install PNP from the AUR:
```bash
# Using an AUR helper like yay
yay -S pnp

# Or manually
git clone https://aur.archlinux.org/pnp.git
cd pnp
makepkg -si
```

## Display server compatibility
PNP is designed to work across different Linux display servers:
- **X11**: Fully supported on all desktop environments.
- **Wayland**: Supported on GNOME and KDE Plasma (5.27+ recommended).
  - On **KDE Plasma Wayland**, the GUI automatically optimizes its backend for the best experience.
  - If you encounter issues where the window is invisible on Plasma, try setting `GDK_BACKEND=x11 pnp-gui` as a temporary workaround.

### From .deb Package (Debian/Ubuntu)
1. Download the latest `.deb` package from the [Releases](https://github.com/Pakrohk/pnp/releases) page, or find it in `dist-packages/` if you built it yourself.
2. Install it using `dpkg`:
   ```bash
   sudo dpkg -i dist-packages/pnp_5.2.0_amd64.deb
   sudo apt install -f  # Fix any missing dependencies
   ```

### From .rpm Package (Fedora/openSUSE)
1. Download the latest `.rpm` package from the [Releases](https://github.com/Pakrohk/pnp/releases) page, or find it in `dist-packages/` if you built it yourself.
2. Install it using `dnf`:
   ```bash
   sudo dnf install dist-packages/pnp-5.2.0-1.x86_64.rpm
   ```

### From Source
1. Clone the repository:
   ```bash
   git clone https://github.com/Pakrohk/pnp.git
   cd pnp
   ```
2. (Optional) Use [Rye](https://rye-up.com/) for development:
   ```bash
   rye sync
   rye build
   ```
3. Use the included installation script:
   ```bash
   sudo ./install.sh
   ```

## Building Packages Yourself
PNP includes a script to build native packages for multiple distributions using native tools or Docker. The script automatically prepares a local source tarball so that packages can be built even before the code is pushed to GitHub:
```bash
./build-all-packages.sh --all
# Or with docker
./build-all-packages.sh --docker --all
```
This will generate DEB, RPM, and Arch packages in the `dist-packages/` directory.

## Configuration

PNP looks for its global configuration at `/etc/pnp/pnp.conf`. You can also create per-controller profiles in `~/.config/pnp/controllers/[serial].conf`.

### Example `pnp.conf`:
```ini
[settings]
rumble_gain = 15%
steam_conflict_check = true

[mapping]
axismap = -y1=y1,-y2=y2
absmap = ABS_HAT0X=dpad_x,ABS_HAT0Y=dpad_y,ABS_X=X1,ABS_Y=Y1,ABS_RX=X2,ABS_RY=Y2,ABS_Z=LT,ABS_RZ=RT
keymap = BTN_SOUTH=A,BTN_EAST=B,BTN_NORTH=Y,BTN_WEST=X,BTN_START=start,BTN_MODE=guide,BTN_SELECT=back,BTN_TL=LB,BTN_TR=RB,BTN_TL2=LT,BTN_TR2=RT,BTN_THUMBL=TL,BTN_THUMBR=TR
```

## Usage

### Starting the GUI
Launch the management interface from your application menu or via terminal:
```bash
pnp-gui
```

### Managing the Service
PNP runs as a system service. You can manage it with `systemctl`:
```bash
# Start the service
sudo systemctl start pnp

# Enable start on boot
sudo systemctl enable pnp

# Check status
sudo systemctl status pnp

# View logs
journalctl -u pnp.service -f
```

## Troubleshooting

- **Controller not detected**:
  - Ensure the controller is paired correctly via Bluetooth or connected via USB.
  - Run `sudo udevadm trigger` to force udev to re-process the device.
  - Check `dmesg` to see if the kernel sees the device.
- **`xboxdrv` not found**: Ensure `xboxdrv` is installed and available in your PATH.
- **GUI won't start**:
  - Run `pnp-gui` from a terminal to see any traceback or error messages.
  - Verify you have `gtk4` and `libadwaita` installed.
- **Steam interference**: PNP is designed to pause when Steam is running. If you find inputs are still doubling, try manually stopping PNP with `sudo systemctl stop pnp` while playing on Steam.
- **Network issues during build**: If `rye build` fails due to network issues, try setting a different `INDEX_URL` or verify your internet connection.

## Uninstall
To remove PNP and all its configuration:
```bash
sudo ./uninstall.sh
# or if installed via package manager:
sudo apt remove pnp
sudo dnf remove pnp
sudo pacman -R pnp
```

## Contributing
We welcome contributions!
1. Set up your development environment with [Rye](https://rye-up.com/): `rye sync`.
2. Run from source for testing: `PYTHONPATH=src python3 -m pnp.gui`.
3. Submit a Pull Request with your improvements.

## License
PNP is released under the **MIT License**.

## Acknowledgements
PNP is a collaborative effort. We would like to thank the original authors and all contributors who made this project possible:
- **niku200**: For the original `ds4to360` concept and implementation.
- **Jules**: For significant architecture improvements, multi-controller support, and rebranding.
- **pakrohk**: For project maintenance, GTK4 modernization, and packaging.
- And all other contributors who provided bug reports and suggestions.
