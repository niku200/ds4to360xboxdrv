#!/bin/bash

# --- Uninstaller Introduction ---
echo "----------------------------------------------------"
echo "--- DualShock 4 to Xbox 360 Controller Uninstaller ---"
echo "----------------------------------------------------"
echo ""
echo "This script will remove all files and configurations installed by install.sh."
echo "----------------------------------------------------"

# --- Configuration Variables ---
UDEV_RULES_DIR="/etc/udev/rules.d"
SYSTEMD_SERVICE_DIR="/etc/systemd/system"
LOCAL_BIN_DIR="/usr/local/bin"

SCRIPT_NAME="ds4-xboxdrv.sh"
SERVICE_NAME="ds4-xboxdrv.service"
UDEV_RULE_NAME="99-ds4-xboxdrv.rules"

# --- Main Script Execution ---

# Check if script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run with sudo. Please run: sudo ./uninstall.sh"
    exit 1
fi

echo "Stopping and disabling the service..."
systemctl stop "$SERVICE_NAME"
systemctl disable "$SERVICE_NAME"
if [ $? -eq 0 ]; then
    echo "Service '$SERVICE_NAME' stopped and disabled."
else
    echo "Warning: Could not stop or disable service '$SERVICE_NAME'. It might not be running or enabled."
fi

echo "Removing systemd service file: $SYSTEMD_SERVICE_DIR/$SERVICE_NAME"
rm -f "$SYSTEMD_SERVICE_DIR/$SERVICE_NAME"
if [ $? -eq 0 ]; then
    echo "Successfully removed service file."
else
    echo "Warning: Could not remove service file. It might not exist."
fi

echo "Removing udev rules file: $UDEV_RULES_DIR/$UDEV_RULE_NAME"
rm -f "$UDEV_RULES_DIR/$UDEV_RULE_NAME"
if [ $? -eq 0 ]; then
    echo "Successfully removed udev rules file."
else
    echo "Warning: Could not remove udev rules file. It might not exist."
fi

echo "Removing main script: $LOCAL_BIN_DIR/$SCRIPT_NAME"
rm -f "$LOCAL_BIN_DIR/$SCRIPT_NAME"
if [ $? -eq 0 ]; then
    echo "Successfully removed script file."
else
    echo "Warning: Could not remove script file. It might not exist."
fi

echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Reloading udev rules..."
udevadm control --reload-rules

echo "Uninstallation complete."
echo ""
echo "--- Additional Cleanup (Manual) ---"
echo "This script does NOT uninstall 'xboxdrv' or 'evsieve' packages."
echo "If you wish to remove them, please do so manually using your package manager:"
echo "  For Fedora/Nobara (dnf): sudo dnf remove xboxdrv evsieve"
echo "  For Debian/Ubuntu (apt): sudo apt remove xboxdrv evsieve"
echo "  For Arch Linux (pacman): sudo pacman -Rns xboxdrv evsieve"
echo "  (and potentially 'sudo dnf copr disable ksefon/xboxdrv' if you enabled the COPR repo)"
echo "------------------------------------------"
