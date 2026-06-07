# DualShock 4 to Xbox 360 Controller Mapper for Linux (v5.1.0)

Modernized and enhanced version of `ds4to360xboxdrv`. This utility emulates an Xbox 360 controller using Sony DualShock 3, 4, and DualSense controllers, providing seamless integration with Linux games.

## ✨ New in v5.1.0

*   **Rye Support:** Now managed with [Rye](https://rye-up.com/) for better Python dependency management.
*   **Multi-Controller Support:** Simultaneously map multiple Sony controllers to multiple virtual Xbox 360 controllers.
*   **Enhanced GTK4/Libadwaita GUI:** Modern, responsive UI with real-time status and logs.
*   **Python-evdev Backend:** More reliable and faster controller detection.
*   **Steam Conflict Detection:** Automatically pauses mapping when Steam is running to prevent double-input.

## 🚀 Installation

### Development (using Rye)
If you have Rye installed:
```bash
rye sync
rye run ds4to360-gui
```

### Manual Installation
On most distributions, use the provided installation script:
```bash
sudo ./install.sh
```
*Note: The script will install system dependencies (`xboxdrv`, `evsieve`, `python-gobject`, `gtk4`, `libadwaita`).*

## 🎮 Usage
1.  Launch **"DS4 to Xbox 360"** from your application menu or run `ds4to360-gui`.
2.  Connect your controller via USB or Bluetooth.
3.  The service will automatically detect the controller and start emulation.

## ⚙️ Configuration
The application can be configured via the GUI's **Settings** tab.
Manual configuration is stored in `/etc/ds4to360.conf`.

## 🗑️ Uninstallation
To remove the application:
```bash
sudo ./uninstall.sh
```

## 📄 License
This project is licensed under the MIT License.
