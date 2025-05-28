# DualShock 4 to Xbox 360 Controller Mapper for Linux

This project provides a simple, systemd-integrated solution to use your Sony DualShock 4 (PS4) controller on Linux as a standard Xbox 360 controller. This is particularly useful for games and applications that natively support Xbox controllers but may not fully support DualShock 4 controllers out-of-the-box.

## ✨ Features

* **Automatic Detection:** Uses a `udev` rule to automatically detect your DualShock 4 controller when connected.
* **Systemd Integration:** Runs `xboxdrv` as a systemd service, ensuring it starts reliably in the background.
* **Xbox 360 Emulation:** Maps DualShock 4 inputs to mimic an Xbox 360 controller using `xboxdrv`.
* **Automatic Device Grabbing:** Ensures `xboxdrv` takes exclusive control of the controller input, preventing conflicts with other applications.
* **Easy Installation:** An `install.sh` script automates the setup process, including dependency checks and configuration.

## ⚠️ Prerequisites

* **A Linux Distribution:** Tested on Arch-based (CachyOS) but designed to be compatible with most systemd-based Linux distributions.
* **`xboxdrv`:** This is the core utility. The `install.sh` script will prompt you to install it if it's missing and attempt to do so using your distribution's package manager.
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

## ✅ Testing Your Device

After successful installation and reconnecting your controller:

1.  **Check Service Status:**
    Confirm the `ds4-xboxdrv.service` is active and running:
    ```bash
    systemctl status ds4-xboxdrv.service
    ```
    It should show `Active: active (running)`.

2.  **Monitor Service Logs:**
    To see real-time output and check for any errors from the `xboxdrv` process:
    ```bash
    journalctl -fu ds4-xboxdrv.service
    ```

3.  **Test Controller Input:**
    * **Graphical Tool:** Install a joystick testing utility like `jstest-gtk` (e.g., `sudo apt install jstest-gtk` or `sudo pacman -S jstest-gtk`). Launch `jstest-gtk` and look for a device typically named "Microsoft X-Box 360 pad" (or similar). Select it and test all buttons and axes. Your original "Wireless Controller" (DualShock 4) device should ideally no longer show input when you press buttons, as `xboxdrv` has successfully grabbed it.
    * **In-Game Testing:** Launch any game that supports Xbox 360 controllers and verify that your DualShock 4 is now recognized and functions correctly.

## ⚠️ Troubleshooting

If you encounter issues, always start by checking the service logs: `journalctl -fu ds4-xboxdrv.service`. Look for error messages related to device grabbing, permissions, or `xboxdrv` startup.

## 🙏 Credits

This solution was made possible with the help of:

* **Niku (@Niku200 on X):** For conceiving and testing the core solution.
* **Gemini (AI Assistant):** For assistance in scripting, debugging, and preparing documentation.

## 📄 License

This project is open-source and available under the [MIT License](https://opensource.org/licenses/MIT).
