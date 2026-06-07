# DualShock 4 to Xbox 360 Controller Mapper for Linux (v5.1.0)

Modernized and enhanced version of `ds4to360xboxdrv`. This utility emulates an Xbox 360 controller using Sony DualShock 3, 4, and DualSense controllers, providing seamless integration with Linux games.

## ✨ New in v5.1.0

*   **Rye Support:** Now managed with [Rye](https://rye-up.com/) for better Python dependency management.
*   **Multi-Controller Support:** Simultaneously map multiple Sony controllers to multiple virtual Xbox 360 controllers.
*   **Enhanced GTK4/Libadwaita GUI:** Modern, responsive UI with real-time status and logs.
*   **Python-evdev Backend:** More reliable and faster controller detection.
*   **Steam Conflict Detection:** Automatically pauses mapping when Steam is running to prevent double-input.

## 🚀 Installation

### Distribution Packages

The project provides native packages for major Linux distributions. These packages handle all system dependencies and configuration automatically.

#### Arch Linux
You can build the package using the provided `PKGBUILD`:
```bash
makepkg -si
```

#### Debian / Ubuntu
To build a `.deb` package:
```bash
sudo apt install debhelper python3-all python3-installer
# If rye is installed and on PATH:
dpkg-buildpackage -us -uc -b
sudo apt install ./dist/packages/ds4to360xboxdrv_*.deb
```

#### Fedora / RHEL
To build an `.rpm` package:
```bash
rpmbuild -ba ds4to360xboxdrv.spec
```

### Building from Source (using Rye)

If you prefer to build the project manually or contribute to development:

1.  **Install Rye:** Follow instructions at [rye.astral.sh](https://rye.astral.sh/).
2.  **Clone and Build:**
    ```bash
    git clone https://github.com/Pakrohk/ds4to360xboxdrv
    cd ds4to360xboxdrv
    rye build --wheel
    ```
3.  **Install the Wheel:**
    ```bash
    pip install dist/*.whl
    ```
4.  **Run Development Version:**
    ```bash
    rye sync
    rye run ds4to360-gui
    ```

### Legacy Manual Installation
On distributions where native packages are not yet ready, use the provided installation script:
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
