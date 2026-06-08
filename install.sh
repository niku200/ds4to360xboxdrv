#!/bin/bash

# --- Thanks & Introduction ---
echo "----------------------------------------------------"
echo "--- DualShock 4 to Xbox 360 Controller Installer ---"
echo "---               Version 5.1.0                  ---"
echo "----------------------------------------------------"

# --- Configuration Variables ---
UDEV_RULES_DIR="/etc/udev/rules.d"
SYSTEMD_SERVICE_DIR="/etc/systemd/system"
SHARE_DIR="/usr/share/ds4to360"
CONFIG_DIR="/etc/ds4to360"
CONFIG_PATH="/etc/ds4to360/ds4to360.conf"

# --- Functions ---

identify_distro_and_install_deps() {
    echo "Checking for system dependencies..."

    if command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm --needed xboxdrv evsieve python-gobject gtk4 libadwaita python-evdev
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y xboxdrv evsieve python3-gobject gtk4 libadwaita python3-evdev python3-virtualenv
    elif command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y xboxdrv evsieve python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-evdev python3-venv
    else
        echo "Please manually install: xboxdrv, evsieve, python-gobject, gtk4, libadwaita, python-evdev"
    fi
}

# --- Main Script Execution ---

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run with sudo."
    exit 1
fi

identify_distro_and_install_deps

echo "Setting up application directory: $SHARE_DIR"
mkdir -p "$SHARE_DIR"
cp -r src/ds4to360 "$SHARE_DIR/"

# Create a virtual environment to avoid PEP 668 issues on modern distros (Debian 12+, Fedora, etc)
echo "Setting up Python virtual environment..."
python3 -m venv --system-site-packages "$SHARE_DIR/venv"
"$SHARE_DIR/venv/bin/pip" install --upgrade pip
"$SHARE_DIR/venv/bin/pip" install evdev

# Create robust wrapper scripts
echo "Installing wrapper scripts..."
cat <<EOF > /usr/bin/ds4to360-gui
#!/bin/bash
export PYTHONPATH="\$PYTHONPATH:$SHARE_DIR"
exec "$SHARE_DIR/venv/bin/python3" -m ds4to360.gui "\$@"
EOF
chmod +x /usr/bin/ds4to360-gui

cat <<EOF > /usr/bin/ds4to360-backend
#!/bin/bash
export PYTHONPATH="\$PYTHONPATH:$SHARE_DIR"
exec "$SHARE_DIR/venv/bin/python3" -m ds4to360.backend "\$@"
EOF
chmod +x /usr/bin/ds4to360-backend

# Install system components
echo "Installing system components..."
cp ds4-xboxdrv.service "$SYSTEMD_SERVICE_DIR/"
# Service file already uses /usr/bin/ds4to360-backend

cp 99-ds4-xboxdrv.rules "$UDEV_RULES_DIR/"
cp ds4to360-gui.desktop "/usr/share/applications/"

mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_PATH" ]; then
    cp ds4to360.conf.example "$CONFIG_PATH"
fi

echo "Reloading daemons..."
systemctl daemon-reload
udevadm control --reload-rules
udevadm trigger

echo "Enabling service..."
systemctl enable ds4-xboxdrv.service

echo "----------------------------------------------------"
echo "Installation complete. Launch the GUI with 'ds4to360-gui'."
echo "----------------------------------------------------"
