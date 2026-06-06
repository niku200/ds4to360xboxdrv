# DualShock 4 to Xbox 360 Controller Mapper for Linux (v5.0.0)

Modernized and enhanced version of `ds4to360xboxdrv`.

## ✨ New in v5.0.0

* **Modern GTK GUI:** Built with GTK4 and Libadwaita for easy management and monitoring.
* **Python Backend:** Improved stability and configurability.
* **Security Hardening:** systemd service runs with least privilege and security restrictions.
* **AUR Support:** PKGBUILD included for Arch Linux users.

## 🚀 Installation

### Arch Linux (AUR)
```bash
# Example using paru
paru -S ds4to360xboxdrv
```

### Manual Installation
```bash
sudo ./install.sh
```

## 🎮 Usage
Launch "DS4 to Xbox 360" from your application menu or run `ds4to360-gui`.
The service will automatically start when a supported controller is connected.

## ⚙️ Configuration
Settings can be modified via the GUI or by editing `/etc/ds4to360.conf`.
