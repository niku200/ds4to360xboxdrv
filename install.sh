#!/bin/sh

# --- Thanks & Introduction ---
echo "----------------------------------------------------"
echo "---       PNP – PS NOT PS Controller Mapper      ---"
echo "---               Version 5.2.0                  ---"
echo "----------------------------------------------------"

# --- Configuration Variables ---
UDEV_RULES_DIR="/etc/udev/rules.d"
SYSTEMD_SERVICE_DIR="/etc/systemd/system"
SHARE_DIR="/usr/share/pnp"
CONFIG_DIR="/etc/pnp"
CONFIG_PATH="/etc/pnp/pnp.conf"

# --- Functions ---

identify_distro_and_install_deps() {
    echo "Checking for system dependencies..."

    if command -v pacman > /dev/null 2>&1; then
        sudo pacman -S --noconfirm --needed xboxdrv evsieve python-gobject gtk4 libadwaita python-evdev python-pyudev
    elif command -v dnf > /dev/null 2>&1; then
        sudo dnf install -y xboxdrv evsieve python3-gobject gtk4 libadwaita python3-evdev python3-pyudev python3-virtualenv
    elif command -v apt > /dev/null 2>&1; then
        sudo apt update
        sudo apt install -y xboxdrv evsieve python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-evdev python3-pyudev python3-venv
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
cp -r src/pnp "$SHARE_DIR/"
cp pyproject.toml "$SHARE_DIR/"

# Create a virtual environment to avoid PEP 668 issues on modern distros (Debian 12+, Fedora, etc)
echo "Setting up Python virtual environment..."
python3 -m venv --system-site-packages "$SHARE_DIR/venv"
"$SHARE_DIR/venv/bin/pip" install --upgrade pip
"$SHARE_DIR/venv/bin/pip" install -e "$SHARE_DIR"

# Create robust wrapper scripts
echo "Installing wrapper scripts..."
cat <<EOF > /usr/bin/pnp-gui
#!/bin/sh
export PYTHONPATH="$SHARE_DIR:\$PYTHONPATH"
exec "$SHARE_DIR/venv/bin/python3" -m pnp.main "\$@"
EOF
chmod 755 /usr/bin/pnp-gui

cat <<EOF > /usr/bin/pnp-backend
#!/bin/sh
export PYTHONPATH="$SHARE_DIR:\$PYTHONPATH"
exec "$SHARE_DIR/venv/bin/python3" -m pnp.main --headless "\$@"
EOF
chmod 755 /usr/bin/pnp-backend

# Install system components
echo "Installing system components..."
cp pnp.service "$SYSTEMD_SERVICE_DIR/"

cp 99-pnp.rules "$UDEV_RULES_DIR/"
cp pnp.desktop "/usr/share/applications/"

mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_PATH" ]; then
    cp pnp.conf.example "$CONFIG_PATH"
fi

echo "Reloading daemons..."
systemctl daemon-reload
udevadm control --reload-rules
udevadm trigger

echo "Enabling service..."
systemctl enable pnp.service

echo "----------------------------------------------------"
echo "Installation complete. Launch the GUI with 'pnp-gui'."
echo "----------------------------------------------------"
