#!/bin/bash

# --- Thanks & Introduction ---
echo "----------------------------------------------------"
echo "--- DualShock 4 to Xbox 360 Controller Installer ---"
echo "---               Version 5.0.0                  ---"
echo "----------------------------------------------------"

# --- Configuration Variables ---
UDEV_RULES_DIR="/etc/udev/rules.d"
SYSTEMD_SERVICE_DIR="/etc/systemd/system"
SHARE_DIR="/usr/share/ds4to360"
CONFIG_PATH="/etc/ds4to360.conf"

# --- Functions ---

identify_distro_and_install_deps() {
    echo "Checking for 'xboxdrv' and 'evsieve'..."
    local xboxdrv_installed=$(command -v xboxdrv &> /dev/null && echo true || echo false)
    local evsieve_installed=$(command -v evsieve &> /dev/null && echo true || echo false)

    if [ "$xboxdrv_installed" = "false" ] || [ "$evsieve_installed" = "false" ]; then
        echo "Missing dependencies. Attempting to install..."
        if command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm xboxdrv evsieve python-gobject gtk4 libadwaita
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y xboxdrv evsieve python3-gobject gtk4 libadwaita
        elif command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y xboxdrv evsieve python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
        else
            echo "Please manually install: xboxdrv, evsieve, python-gobject, gtk4, libadwaita"
        fi
    fi
}

# --- Main Script Execution ---

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run with sudo."
    exit 1
fi

identify_distro_and_install_deps

mkdir -p "$SHARE_DIR"
cp src/backend.py "$SHARE_DIR/"
cp src/gui.py "$SHARE_DIR/"
chmod +x "$SHARE_DIR/gui.py"

ln -sf "$SHARE_DIR/gui.py" "/usr/bin/ds4to360-gui"

cp ds4-xboxdrv.service "$SYSTEMD_SERVICE_DIR/"
cp 99-ds4-xboxdrv.rules "$UDEV_RULES_DIR/"
cp ds4to360-gui.desktop "/usr/share/applications/"

if [ ! -f "$CONFIG_PATH" ]; then
    cp ds4to360.conf.example "$CONFIG_PATH"
fi

systemctl daemon-reload
udevadm control --reload-rules
udevadm trigger

echo "Installation complete. Launch the GUI with 'ds4to360-gui'."
