#!/bin/bash

echo "----------------------------------------------------"
echo "--- PNP – PS NOT PS Controller Uninstaller ---"
echo "----------------------------------------------------"

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run with sudo."
    exit 1
fi

SERVICE_NAME="pnp.service"

echo "Stopping and disabling service..."
systemctl stop "$SERVICE_NAME" 2>/dev/null
systemctl disable "$SERVICE_NAME" 2>/dev/null

echo "Removing files..."
rm -f /usr/lib/systemd/system/$SERVICE_NAME
rm -f /etc/systemd/system/$SERVICE_NAME
rm -f /etc/udev/rules.d/99-pnp.rules
rm -f /usr/share/applications/pnp.desktop
rm -f /usr/bin/pnp-gui
rm -f /usr/bin/pnp-backend
rm -rf /usr/share/pnp

echo "Reloading daemons..."
systemctl daemon-reload
udevadm control --reload-rules

echo ""
echo "Uninstallation complete."
echo "Note: Dependencies (xboxdrv, evsieve, etc.) were not removed."
