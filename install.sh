#!/bin/bash

# --- Thanks & Introduction ---
echo "----------------------------------------------------"
echo "--- DualShock 4 to Xbox 360 Controller Installer ---"
echo "----------------------------------------------------"
echo ""
echo "If you find this script useful, please consider thanking the creator, Niku,"
echo "on X (formerly Twitter) at https://x.com/Niku200"
echo "and Gemini (the AI assistant) for their help in creating this solution!" [cite: 57]
echo ""
echo "This script will install the necessary files and configure your system"
echo "to map your DualShock 4 controller to an Xbox 360 controller." [cite: 58]
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

# Function to check for essential system commands (not xboxdrv/evsieve, which are handled separately)
check_essential_commands() {
    local missing_commands=()
    for cmd in "$@"; do # [cite: 59]
        if ! command -v "$cmd" &> /dev/null; then # [cite: 60]
            missing_commands+=("$cmd")
        fi
    done
    if [ ${#missing_commands[@]} -gt 0 ]; then # [cite: 61]
        echo "Error: The following essential commands are not found: ${missing_commands[*]}" >&2
        echo "These are usually part of a base system installation. Please ensure your system is complete." [cite: 62] >&2
        exit 1
    fi
}

# Function to identify distribution and offer to install xboxdrv and evsieve
identify_distro_and_install_deps() {
    echo "Checking for 'xboxdrv' and 'evsieve'..."
    local xboxdrv_installed=false
    local evsieve_installed=false

    if command -v xboxdrv &> /dev/null; then # [cite: 63]
        echo "xboxdrv is already installed. Great!" [cite: 81]
        xboxdrv_installed=true
    fi

    if command -v evsieve &> /dev/null; then
        echo "evsieve is already installed. Great!"
        evsieve_installed=true
    fi

    if ! $xboxdrv_installed || ! $evsieve_installed; then
        echo "Some required dependencies (xboxdrv or evsieve) are NOT installed, but they are REQUIRED for this setup to work." [cite: 64]
        echo "Attempting to install them using your distribution's package manager." [cite: 65]
        local install_cmd_xboxdrv=""
        local install_cmd_evsieve=""
        local distro_type=""

        if command -v apt &> /dev/null; then # [cite: 66]
            distro_type="deb"
            install_cmd_xboxdrv="sudo apt update && sudo apt install -y xboxdrv"
            install_cmd_evsieve="sudo apt install -y evsieve" # Assuming evsieve is in apt repos
        elif command -v dnf &> /dev/null; then # [cite: 67]
            distro_type="rpm"
            install_cmd_xboxdrv="sudo dnf install -y xboxdrv" # Placeholder for Fedora if not using COPR
            install_cmd_evsieve="sudo dnf install -y evsieve"
        elif command -v pacman &> /dev/null; then # [cite: 68]
            distro_type="arch"
            install_cmd_xboxdrv="sudo pacman -S --noconfirm xboxdrv"
            install_cmd_evsieve="sudo pacman -S --noconfirm evsieve"
        elif command -v zypper &> /dev/null; then # [cite: 69]
            distro_type="suse"
            install_cmd_xboxdrv="sudo zypper install -y xboxdrv"
            install_cmd_evsieve="sudo zypper install -y evsieve"
        else
            echo "Warning: Could not determine your distribution's package manager." [cite: 70]
            echo "Please manually install 'xboxdrv' and 'evsieve' using your system's package manager (e.g., yum, emerge, etc.)." [cite: 71]
            read -p "Press Enter to continue, but remember the service will NOT function without them." [cite: 72]
            return # Exit this function, continue with the rest of the script
        fi

        echo ""
        read -p "Do you want to install missing dependencies (xboxdrv, evsieve) now? (y/N): " choice
        case "$choice" in
            y|Y )
                # Install evsieve first
                if ! $evsieve_installed; then
                    echo "Executing: $install_cmd_evsieve"
                    eval "$install_cmd_evsieve"
                    if [ $? -ne 0 ]; then
                        echo "Error: Failed to install evsieve. Please try to install it manually." >&2
                        read -p "Press Enter to continue (service will not work without evsieve)."
                    else
                        echo "evsieve installed successfully."
                    fi
                fi

                # Install xboxdrv
                if ! $xboxdrv_installed; then
                    if [ "$distro_type" = "rpm" ]; then
                        echo ""
                        echo "On Fedora/Nobara, it is highly recommended to install xboxdrv from the COPR repository."
                        echo "This typically provides a more up-to-date and reliable package."
                        read -p "Do you want to enable the COPR repository and install xboxdrv from there? (y/N): " copr_choice
                        case "$copr_choice" in
                            y|Y )
                                echo "Adding COPR repository 'ksefon/xboxdrv'..."
                                sudo dnf copr enable ksefon/xboxdrv -y
                                if [ $? -ne 0 ]; then
                                    echo "Warning: Failed to enable COPR repository. Attempting standard dnf install."
                                    eval "$install_cmd_xboxdrv"
                                else
                                    echo "Installing xboxdrv from COPR..."
                                    sudo dnf install -y xboxdrv
                                    if [ $? -ne 0 ]; then
                                        echo "Error: Failed to install xboxdrv from COPR. Please try manually or check COPR setup." >&2
                                        read -p "Press Enter to continue (service will not work without xboxdrv)."
                                    else
                                        echo "xboxdrv installed successfully from COPR."
                                    fi
                                fi
                                ;;
                            * )
                                echo "Skipping COPR. Attempting standard dnf install of xboxdrv (if available)."
                                eval "$install_cmd_xboxdrv"
                                if [ $? -ne 0 ]; then
                                    echo "Error: Failed to install xboxdrv via standard dnf. Please install it manually." >&2
                                    read -p "Press Enter to continue (service will not work without xboxdrv)."
                                else
                                    echo "xboxdrv installed successfully via standard dnf."
                                fi
                                ;;
                        esac
                    else
                        echo "Executing: $install_cmd_xboxdrv" [cite: 73]
                        eval "$install_cmd_xboxdrv" # Using eval to run the constructed command
                        if [ $? -ne 0 ]; then # [cite: 74]
                            echo "Error: Failed to install xboxdrv. Please try to install it manually." [cite: 75] >&2
                            read -p "Press Enter to continue (service will not work without xboxdrv)." [cite: 76]
                        else
                            echo "xboxdrv installed successfully." [cite: 77]
                        fi
                    fi
                fi
                ;;
            * )
                echo "Skipping dependency installation. The service will NOT function correctly without them." [cite: 79]
                read -p "Press Enter to continue with the installation setup anyway (service will not work without dependencies)."
                ;; # [cite: 80]
        esac
    fi
}

# Function to get the real username of the user who called sudo
get_real_username() {
    if [ -n "$SUDO_USER" ]; then # [cite: 82]
        echo "$SUDO_USER"
    else
        # Fallback if SUDO_USER is not set (e.g., direct root login, which is not recommended)
        echo "$USER"
    fi
}

# --- Main Script Execution ---

# Check if script is run as root
if [ "$(id -u)" -ne 0 ]; then # [cite: 83]
    echo "This script must be run with sudo. Please run: sudo ./install.sh"
    exit 1
fi

# Check for essential system commands
check_essential_commands "systemctl" "udevadm" "awk" "pgrep" "sed" "mktemp" "id" "readlink" "rm" "cp" "chmod"

# Attempt to install xboxdrv and evsieve if they are missing
identify_distro_and_install_deps

REAL_USER=$(get_real_username)
echo "Configuring service for user: '$REAL_USER'"

# Determine the directory where this install.sh script is located
# This is crucial for finding the other service files.
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd) # [cite: 84]

echo "Source directory for installation files: $SCRIPT_DIR"

# 1. Copy the main script to /usr/local/bin/
echo "Copying $SCRIPT_NAME to $LOCAL_BIN_DIR/..."
cp "$SCRIPT_DIR/$SCRIPT_NAME" "$LOCAL_BIN_DIR/"
chmod +x "$LOCAL_BIN_DIR/$SCRIPT_NAME"
if [ $? -eq 0 ]; then # [cite: 85]
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
sed "s/^Group=niku/Group=${REAL_USER}/" > "$SERVICE_TEMP_FILE" # [cite: 86]

cp "$SERVICE_TEMP_FILE" "$SYSTEMD_SERVICE_DIR/$SERVICE_NAME"
rm "$SERVICE_TEMP_FILE" # Clean up temporary file
if [ $? -eq 0 ]; then # [cite: 87]
    echo "Successfully copied: $SYSTEMD_SERVICE_DIR/$SERVICE_NAME (configured for user '$REAL_USER')"
else
    echo "Error: Failed to copy $SYSTEMD_SERVICE_DIR/$SERVICE_NAME" >&2
    exit 1
fi

# 3. Copy the udev rules file
echo "Copying $UDEV_RULE_NAME to $UDEV_RULES_DIR/..."
cp "$SCRIPT_DIR/$UDEV_RULE_NAME" "$UDEV_RULES_DIR/"
if [ $? -eq 0 ]; then # [cite: 88]
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
if [ $? -eq 0 ]; then # [cite: 89]
    echo "Service enabled." [cite: 90]
else
    echo "Warning: Failed to enable service. You might need to troubleshoot manually." [cite: 91] >&2
fi

# 5. Reload udev rules and trigger
echo "Reloading udev rules and triggering for existing devices..."
udevadm control --reload-rules
udevadm trigger # This will make udev re-evaluate connected devices and potentially start the service

echo ""
echo "--- Important Post-Installation Steps ---"
echo "1. **User Group Membership:** Ensure the user '$REAL_USER' is part of the 'input' group." [cite: 92]
echo "   You can check with:   groups $REAL_USER"
echo "   If not, add them with: sudo usermod -aG input $REAL_USER"
echo "   After adding, you MUST log out and log back in for the group change to take effect!" [cite: 93]
echo "2. **Activate Service:** Disconnect and reconnect your DualShock 4 controller to start the service." [cite: 94]
echo "   You can check the service status with: systemctl status $SERVICE_NAME"
echo "   View live logs with: journalctl -fu $SERVICE_NAME"
echo ""
echo "Installation process complete. Thank you!" [cite: 95]
echo "------------------------------------------"
