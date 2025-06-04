# DualShock 4 to Xbox 360 Controller Mapper for Linux

This project provides a simple, systemd-integrated solution to use your Sony DualShock 4 (PS4) controller on Linux as a standard Xbox 360 controller. This is particularly useful for games and applications that natively support Xbox controllers but may not fully support DualShock 4 controllers out-of-the-box.

## ✨ Features

<<<<<<< HEAD
* **Automatic Detection:** Uses a `udev` rule to automatically detect your DualShock 4 controller when connected[cite: 1].
* **Systemd Integration:** Runs `xboxdrv` as a systemd service, ensuring it starts reliably in the background[cite: 2].
* **Xbox 360 Emulation:** Maps DualShock 4 inputs to mimic an Xbox 360 controller using `xboxdrv`[cite: 3].
* **Automatic Device Grabbing with `evsieve`:** Utilizes `evsieve` to grab exclusive control of the controller input, preventing conflicts with other applications (like Steam's own input handling) and then passes events to `xboxdrv`[cite: 3].
* **Easy Installation & Uninstallation:** `install.sh` automates setup, including dependency checks and configuration, and `uninstall.sh` reverts changes.

## ⚠️ Prerequisites

* **A Linux Distribution:** Tested on Arch-based (CachyOS) and Fedora/Nobara, but designed to be compatible with most systemd-based Linux distributions.
* **`xboxdrv`:** This is the core utility. The `install.sh` script will prompt you to install it if it's missing and attempt to do so using your distribution's package manager or recommend COPR for Fedora users.
* **`evsieve`:** This utility is crucial for grabbing the device input. The `install.sh` script will also prompt you to install it if missing.
=======
* **Automatic Detection:** Uses a `udev` rule to automatically detect your DualShock 4 controller when connected.
* **Systemd Integration:** Runs `xboxdrv` as a systemd service, ensuring it starts reliably in the background.
* **Xbox 360 Emulation:** Maps DualShock 4 inputs to mimic an Xbox 360 controller using `xboxdrv`.
* **Automatic Device Grabbing:** Ensures `xboxdrv` takes exclusive control of the controller input, preventing conflicts with other applications.
* **Easy Installation:** An `install.sh` script automates the setup process, including dependency checks and configuration.

## ⚠️ Prerequisites

* **A Linux Distribution:** Tested on Arch-based (CachyOS) but designed to be compatible with most systemd-based Linux distributions.
* **`xboxdrv`:** This is the core utility. The `install.sh` script will prompt you to install it if it's missing and attempt to do so using your distribution's package manager.
>>>>>>> c84ad29ad3b8b4e757a4aa22a096ee2c7598cb55
* **`systemd`:** Your system must use `systemd` as its init system (most modern distributions do).
* **`udev`:** For device detection and rule triggering.

## 🚀 Installation

Follow these steps to install the controller mapping solution on your system:

1.  **Download the project files:**
    If you're getting this from a GitHub repository, clone it using Git:
    ```bash
    git clone [https://github.com/YourUsername/ps4-to-xboxdrv.git](https://github.com/YourUsername/ps4-to-xboxdrv.git) # Replace with your actual repository URL
    cd ps4-to-xboxdrv
    ```
<<<<<<< HEAD
    Alternatively, if you received the files in a ZIP archive, simply extract them to a desired location (e.g., `/run/media/niku/9A2EDA072ED9DBF7/Desc linux/V4/`) and navigate into the extracted directory in your terminal.

2.  **Make installer executable:**
    ```bash
    chmod +x install.sh
    ```

3.  **Run the installer script:**
    In the project directory, execute the `install.sh` script with `sudo`:
    ```bash
    sudo ./install.sh
    ```
4.  **Follow the on-screen prompts:**
    * The script will first greet you and ask for your `sudo` password[cite: 56].
    * It will check if `evsieve` and `xboxdrv` are installed and offer to install them for you if they are missing (using your distribution's package manager like `apt`, `dnf`, `pacman`, or `zypper`)[cite: 56]. For Fedora/Nobara users, it will specifically recommend and offer to enable the COPR repository for `xboxdrv` for a more up-to-date installation[cite: 56].
    * It will then copy the necessary scripts, service files, and udev rules to their proper system locations[cite: 56].
    * It automatically configures the systemd service to run under your current username[cite: 56].

5.  **Important Post-Installation Steps:**
    * **User Group Membership:** Ensure that the user under which you want `xboxdrv` to run (your username) is part of the `input` group. This is crucial for `xboxdrv` and `evsieve` to have the necessary permissions to read from and grab input devices.
        * You can check your groups with: `groups your_username` (replace `your_username` with your actual username)[cite: 92].
        * If `input` is not listed, add yourself to the group: `sudo usermod -aG input your_username` [cite: 92]
        * **After adding, you MUST log out and log back in (or reboot) for group changes to take effect!** [cite: 93]
    * **Activate Service:** Disconnect your DualShock 4 controller if it's plugged in, then reconnect it. The `udev` rule should detect it and automatically start the `ds4-xboxdrv.service`[cite: 94].
=======
    Alternatively, if you received the files in a ZIP archive, simply extract them to a desired location and navigate into the extracted `ps4-to-xboxdrv` directory in your terminal.

2.  **Run the installer script:**
    In the `ps4-to-xboxdrv` directory, execute the `install.sh` script with `sudo`:
    ```bash
    sudo ./install.sh
    ```
3.  **Follow the on-screen prompts:**
    * The script will first greet you and ask for your `sudo` password.
    * It will check if `xboxdrv` is installed and offer to install it for you if it's missing (using your distribution's package manager like `apt`, `dnf`, `pacman`, or `zypper`).
    * It will then copy the necessary scripts, service files, and udev rules to their proper system locations.
    * It automatically configures the systemd service to run under your current username.

4.  **Important Post-Installation Steps:**
    * **User Group Membership:** Ensure that the user under which you want `xboxdrv` to run (your username) is part of the `input` group. This is crucial for `xboxdrv` to have the necessary permissions to read from and grab input devices.
        * You can check your groups with: `groups your_username` (replace `your_username` with your actual username).
        * If `input` is not listed, add yourself to the group: `sudo usermod -aG input your_username`
        * **After adding, you MUST log out and log back in (or reboot) for group changes to take effect!**
    * **Activate Service:** Disconnect your DualShock 4 controller if it's plugged in, then reconnect it. The `udev` rule should detect it and automatically start the `ds4-xboxdrv.service`.
>>>>>>> c84ad29ad3b8b4e757a4aa22a096ee2c7598cb55

## ✅ Testing Your Device

After successful installation and reconnecting your controller:

1.  **Check Service Status:**
    Confirm the `ds4-xboxdrv.service` is active and running:
    ```bash
    systemctl status ds4-xboxdrv.service
    ```
    It should show `Active: active (running)`.

2.  **Monitor Service Logs:**
<<<<<<< HEAD
    To see real-time output and check for any errors from the `xboxdrv` and `evsieve` processes:
=======
    To see real-time output and check for any errors from the `xboxdrv` process:
>>>>>>> c84ad29ad3b8b4e757a4aa22a096ee2c7598cb55
    ```bash
    journalctl -fu ds4-xboxdrv.service
    ```

3.  **Test Controller Input:**
<<<<<<< HEAD
    * **Graphical Tool:** Install a joystick testing utility like `jstest-gtk` (e.g., `sudo apt install jstest-gtk` or `sudo pacman -S jstest-gtk`). Launch `jstest-gtk` and look for a device typically named "Microsoft X-Box 360 pad" (or similar). Select it and test all buttons and axes. Your original "Wireless Controller" (DualShock 4) device should ideally no longer show input when you press buttons, as `evsieve` has successfully grabbed it.
    * **In-Game Testing:** Launch any game that supports Xbox 360 controllers and verify that your DualShock 4 is now recognized and functions correctly.

## 🗑️ Uninstallation

To remove all installed files and configurations, run the `uninstall.sh` script with `sudo`:

1.  **Make uninstaller executable:**
    ```bash
    chmod +x uninstall.sh
    ```
2.  **Run the uninstaller script:**
    ```bash
    sudo ./uninstall.sh
    ```
    This script will stop and disable the systemd service, and remove the installed files. It will **not** uninstall `xboxdrv` or `evsieve` packages themselves. Instructions for manual removal of those packages will be provided by the uninstaller.

## ⚠️ Troubleshooting & Adding Unsupported Devices

If you encounter issues, always start by checking the service logs: `journalctl -fu ds4-xboxdrv.service`. Look for error messages related to device grabbing, permissions, or `xboxdrv`/`evsieve` startup.

If your PlayStation controller (e.g., a newer DualSense model not yet included) is not being detected or mapped, you might need to add its Vendor ID (VID) and Product ID (PID) to the `99-ds4-xboxdrv.rules` file and the `ds4-xboxdrv.sh` script.

**To find your device's Vendor ID and Product ID:**

1.  Plug in your controller.
2.  Open a terminal and run the following command:
    ```bash
    cat /proc/bus/input/devices
    ```
3.  Look for a section related to your controller. It usually has `Name="Sony Interactive Entertainment Wireless Controller"` or similar. Identify the line starting with `I:` followed by `Bus=`, `Vendor=`, `Product=`, and `Version=`.
    Example: `I: Bus=0005 Vendor=054c Product=0ce6 Version=0100`
    In this example:
    * `Vendor=054c` (This is the `idVendor`)
    * `Product=0ce6` (This is the `idProduct`)

**If you find your device's VID and PID and it's not already in the scripts:**

1.  **Locate and send the `99-ds4-xboxdrv.rules` file:** This file is in `/etc/udev/rules.d/99-ds4-xboxdrv.rules` after installation, or in your project directory.
2.  **Locate and send the `ds4-xboxdrv.sh` script:** This file is in `/usr/local/bin/ds4-xboxdrv.sh` after installation, or in your project directory.
3.  **Provide the `idVendor` and `idProduct` you found.**
4.  **Describe the issue you're facing** (e.g., "controller not detected", "buttons not working").

Please share this information with Gemini (the AI assistant) or Niku (@Niku200 on X) so the scripts can be updated to support more devices!
=======
    * **Graphical Tool:** Install a joystick testing utility like `jstest-gtk` (e.g., `sudo apt install jstest-gtk` or `sudo pacman -S jstest-gtk`). Launch `jstest-gtk` and look for a device typically named "Microsoft X-Box 360 pad" (or similar). Select it and test all buttons and axes. Your original "Wireless Controller" (DualShock 4) device should ideally no longer show input when you press buttons, as `xboxdrv` has successfully grabbed it.
    * **In-Game Testing:** Launch any game that supports Xbox 360 controllers and verify that your DualShock 4 is now recognized and functions correctly.

## ⚠️ Troubleshooting

If you encounter issues, always start by checking the service logs: `journalctl -fu ds4-xboxdrv.service`. Look for error messages related to device grabbing, permissions, or `xboxdrv` startup.
>>>>>>> c84ad29ad3b8b4e757a4aa22a096ee2c7598cb55

## 🙏 Credits

This solution was made possible with the help of:

<<<<<<< HEAD
* **Niku (@Niku200 on X):** For conceiving and testing the core solution[cite: 57].
* **Gemini (AI Assistant):** For assistance in scripting, debugging, and preparing documentation[cite: 57].
=======
* **Niku (@Niku200 on X):** For conceiving and testing the core solution.
* **Gemini (AI Assistant):** For assistance in scripting, debugging, and preparing documentation.
>>>>>>> c84ad29ad3b8b4e757a4aa22a096ee2c7598cb55

## 📄 License

This project is open-source and available under the [MIT License](https://opensource.org/licenses/MIT).
