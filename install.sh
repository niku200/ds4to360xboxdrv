#!/bin/bash

# --- Thanks & Introduction ---
echo "----------------------------------------------------"
echo "--- DualShock 4 to Xbox 360 Controller Installer ---"
echo "----------------------------------------------------"
echo ""
echo "If you find this script useful, please consider thanking the creator, Niku,"
echo "on X (formerly Twitter) at https://x.com/Niku200"
echo "and Gemini (the AI assistant) for their help in creating this solution!"
echo ""
echo "This script will install the necessary files and configure your system"
echo "to map your DualShock 4 controller to an Xbox 360 controller."
echo ""
echo "----------------------------------------------------"

# --- Configuration Variables ---
# These are the target system directories for installation
UDEV_RULES_DIR="/etc/udev/rules.d"
SYSTEMD_SERVICE_DIR="/etc/systemd/system"
LOCAL_BIN_DIR="/usr/local/bin"

SCRIPT_NAME="ds4-xboxdrv.sh"
SERVICE_NAME="ds4-xboxdrv.service"
UDEV_RULE_NAME="99-ds4-xboxdrv.rules"

# --- Functions ---

# Function to check for essential system commands (not xboxdrv, which is handled separately)
check_essential_commands() {
    local missing_commands=()
    for cmd in "$@"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_commands+=("$cmd")
        fi
    done
    if [ ${#missing_commands[@]} -gt 0 ]; then
        echo "Error: The following essential commands are not found: ${missing_commands[*]}" >&2
        echo "These are usually part of a base system installation. Please ensure your system is complete." >&2
        exit 1
    fi
}

# Function to identify distribution and offer to install xboxdrv
identify_distro_and_install_xboxdrv() {
    echo "Checking for 'xboxdrv'..."
    if ! command -v xboxdrv &> /dev/null; then
        echo "xboxdrv is NOT installed, but it is REQUIRED for this setup to work."
        echo "Attempting to install it using your distribution's package manager."

        local install_cmd=""
        if command -v apt &> /dev/null; then
            install_cmd="sudo apt update && sudo apt install -y xboxdrv"
        elif command -v dnf &> /dev/null; then
            install_cmd="sudo dnf install -y xboxdrv"
        elif command -v pacman &> /dev/null; then
            install_cmd="sudo pacman -S --noconfirm xboxdrv"
        elif command -v zypper &> /dev/null; then
            install_cmd="sudo zypper install -y xboxdrv"
        else
            echo "Warning: Could not determine your distribution's package manager."
            echo "Please manually install 'xboxdrv' using your system's package manager (e.g., yum, emerge, etc.)."
            read -p "Press Enter to continue, but remember the service will NOT function without xboxdrv."
            return # Exit this function, continue with the rest of the script
        fi

        echo ""
        read -p "Do you want to install 'xboxdrv' now? (y/N): " choice
        case "$choice" in
            y|Y )
                echo "Executing: $install_cmd"
                eval "$install_cmd" # Using eval to run the constructed command
                if [ $? -ne 0 ]; then
                    echo "Error: Failed to install xboxdrv. Please try to install it manually." >&2
                    read -p "Press Enter to continue (service will not work without xboxdrv)."
                else
                    echo "xboxdrv installed successfully."
                fi
                ;;
            * )
                echo "Skipping xboxdrv installation. The service will NOT function correctly without it."
                read -p "Press Enter to continue with the installation setup anyway (service will not work without xboxdrv)."
                ;;
        esac
    else
        echo "xboxdrv is already installed. Great!"
    fi
}

# Function to get the real username of the user who called sudo
get_real_username() {
    if [ -n "$SUDO_USER" ]; then
        echo "$SUDO_USER"
    else
        # Fallback if SUDO_USER is not set (e.g., direct root login, which is not recommended)
        echo "$USER"
    fi
}

# --- Main Script Execution ---

# Check if script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run with sudo. Please run: sudo ./install.sh"
    exit 1
fi

# Check for essential system commands (not xboxdrv, which is handled by its own function)
check_essential_commands "systemctl" "udevadm" "awk" "pgrep" "sed" "mktemp" "id"

# Attempt to install xboxdrv if it's missing
identify_distro_and_install_xboxdrv

REAL_USER=$(get_real_username)
echo "Configuring service for user: '$REAL_USER'"

# Determine the directory where this install.sh script is located
# This is crucial for finding the other service files.
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

echo "Source directory for installation files: $SCRIPT_DIR"

# 1. Copy the main script to /usr/local/bin/
echo "Copying $SCRIPT_NAME to $LOCAL_BIN_DIR/..."
cp "$SCRIPT_DIR/$SCRIPT_NAME" "$LOCAL_BIN_DIR/"
chmod +x "$LOCAL_BIN_DIR/$SCRIPT_NAME"
if [ $? -eq 0 ]; then
    echo "Successfully copied and made executable: $LOCAL_BIN_DIR/$SCRIPT_NAME"
else
    echo "Error: Failed to copy or set permissions for $LOCAL_BIN_DIR/$SCRIPT_NAME" >&2
    exit 1
fi

# 2. Dynamically modify and copy the systemd service file
echo "Modifying and copying $SERVICE_NAME to $SYSTEMD_SERVICE_DIR/..."
SERVICE_TEMP_FILE=$(mktemp)
# Replace 'User=niku' and 'Group=niku' with the actual username
sed "s/^User=niku/User=${REAL_USER}/" "$SCRIPT_DIR/$SERVICE_NAME" | \
sed "s/^Group=niku/Group=${REAL_USER}/" > "$SERVICE_TEMP_FILE"

cp "$SERVICE_TEMP_FILE" "$SYSTEMD_SERVICE_DIR/$SERVICE_NAME"
rm "$SERVICE_TEMP_FILE" # Clean up temporary file
if [ $? -eq 0 ]; then
    echo "Successfully copied: $SYSTEMD_SERVICE_DIR/$SERVICE_NAME (configured for user '$REAL_USER')"
else
    echo "Error: Failed to copy $SYSTEMD_SERVICE_DIR/$SERVICE_NAME" >&2
    exit 1
fi

# 3. Copy the udev rules file
echo "Copying $UDEV_RULE_NAME to $UDEV_RULES_DIR/..."
cp "$SCRIPT_DIR/$UDEV_RULE_NAME" "$UDEV_RULES_DIR/"
if [ $? -eq 0 ]; then
    echo "Successfully copied: $UDEV_RULES_DIR/$UDEV_RULE_NAME"
else
    echo "Error: Failed to copy $UDEV_RULES_DIR/$UDEV_RULE_NAME" >&2
    exit 1
fi

# 4. Reload systemd daemon and enable the service
echo "Reloading systemd daemon..."
systemctl daemon-reload
echo "Enabling $SERVICE_NAME to start on boot..."
systemctl enable "$SERVICE_NAME"
if [ $? -eq 0 ]; then
    echo "Service enabled."
else
    echo "Warning: Failed to enable service. You might need to troubleshoot manually." >&2
fi

# 5. Reload udev rules and trigger
echo "Reloading udev rules and triggering for existing devices..."
udevadm control --reload-rules
udevadm trigger # This will make udev re-evaluate connected devices and potentially start the service

echo ""
echo "--- Important Post-Installation Steps ---"
echo "1. **User Group Membership:** Ensure the user '$REAL_USER' is part of the 'input' group."
echo "   You can check with:   groups $REAL_USER"
echo "   If not, add them with: sudo usermod -aG input $REAL_USER"
echo "   After adding, you MUST log out and log back in for the group change to take effect!"
echo "2. **Activate Service:** Disconnect and reconnect your DualShock 4 controller to start the service."
echo "   You can check the service status with: systemctl status $SERVICE_NAME"
echo "   View live logs with: journalctl -fu $SERVICE_NAME"
echo ""
echo "Installation process complete. Thank you!"
echo "------------------------------------------"
