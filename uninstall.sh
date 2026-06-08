#!/bin/bash

echo "----------------------------------------------------"
echo "--- DualShock 4 to Xbox 360 Controller Uninstaller ---"
echo "----------------------------------------------------"

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run with sudo."
    exit 1
fi

SERVICE_NAME="ds4-xboxdrv.service"

echo "Stopping and disabling service..."
systemctl stop "$SERVICE_NAME" 2>/dev/null
systemctl disable "$SERVICE_NAME" 2>/dev/null

echo "Removing files..."
rm -f /usr/lib/systemd/system/$SERVICE_NAME
rm -f /etc/systemd/system/$SERVICE_NAME
rm -f /etc/udev/rules.d/99-ds4-xboxdrv.rules
rm -f /usr/share/applications/ds4to360-gui.desktop
rm -f /usr/bin/ds4to360-gui
rm -f /usr/bin/ds4to360-backend
rm -rf /usr/share/ds4to360

echo "Reloading daemons..."
systemctl daemon-reload
udevadm control --reload-rules

echo ""
echo "Uninstallation complete."
echo "Note: Dependencies (xboxdrv, evsieve, etc.) were not removed."
