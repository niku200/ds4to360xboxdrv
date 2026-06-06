# DualShock 4 to Xbox 360 Controller Mapper for Linux (v5.0.0)

Modernized and enhanced version of `ds4to360xboxdrv`. This utility emulates an Xbox 360 controller using Sony DualShock 3, 4, and DualSense controllers, providing seamless integration with Linux games.

## ✨ New in v5.0.0

*   **Modern GTK GUI:** Built with GTK4 and Libadwaita for real-time monitoring and easy configuration.
*   **Python Backend:** Robust logic with auto-resume support and Steam conflict detection.
*   **Security Hardening:** systemd service utilizes `DynamicUser` and strict isolation features.
*   **Broad Compatibility:** Pre-configured for multiple DS4, DualSense, and DS3 models.
*   **AUR Support:** Official PKGBUILD included for Arch Linux users.

## 🚀 Installation

### Arch Linux (AUR)
Install using your favorite AUR helper:
```bash
paru -S ds4to360xboxdrv
```

### Manual Installation
On other distributions, use the provided installation script:
```bash
sudo ./install.sh
```
*Note: The script will attempt to install dependencies (`xboxdrv`, `python-gobject`, `gtk4`, `libadwaita`). `evsieve` is recommended for better device grabbing.*

## 🎮 Usage
1.  Launch **"DS4 to Xbox 360"** from your application menu or run `ds4to360-gui`.
2.  Connect your controller via USB or Bluetooth.
3.  The service will automatically detect the controller and start emulation.
4.  If Steam is running, emulation will pause to avoid conflicts (configurable in settings).

## ⚙️ Configuration
The application can be configured via the GUI's **Configuration** tab. You can adjust:
*   **Rumble Gain:** Strength of force feedback.
*   **Steam Conflict Check:** Whether to pause when Steam is active.
*   **Input Mapping:** Custom `xboxdrv` mappings for axes, buttons, and absolute events.

Manual configuration is stored in `/etc/ds4to360.conf`.

## 🗑️ Uninstallation
To remove the application and its configuration:
```bash
sudo ./uninstall.sh
```
This will stop and disable the service, remove udev rules, binaries, and desktop entries, and reload system daemons.

## 📄 License
This project is licensed under the MIT License.
