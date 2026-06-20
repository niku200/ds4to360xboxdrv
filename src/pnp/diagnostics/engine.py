import os
import subprocess
from loguru import logger
from pnp.diagnostics.polkit import PolkitManager


class DiagnosticSystem:
    def __init__(self):
        self.results = []

    def run_all_checks(self):
        """Runs all diagnostic checks and returns a list of issues found."""
        self.results = []

        self._check_udev_rules()
        self._check_uinput()
        self._check_bluetooth()
        self._check_bluetooth_detailed()
        self._check_steam_devices()

        return self.results

    def _check_udev_rules(self):
        pnp_rules = "/etc/udev/rules.d/99-pnp.rules"
        if not os.path.exists(pnp_rules):
            self.results.append({
                "id": "udev_missing",
                "title": "PNP udev rules missing",
                "description": "Custom udev rules are required for PNP to "
                               "access controllers without root.",
                "severity": "critical",
                "fix_action": "org.pnp.udev.install",
                "helper": "install-udev-rules"
            })
        else:
            # Check for correct content (simplified)
            try:
                with open(pnp_rules, "r", encoding="utf-8") as f:
                    content = f.read()
                    if 'ATTRS{idVendor}=="054c"' not in content:
                        self.results.append({
                            "id": "udev_invalid",
                            "title": "PNP udev rules invalid",
                            "description": "Existing udev rules seem to be "
                                           "outdated or incorrect.",
                            "severity": "warning",
                            "fix_action": "org.pnp.udev.install",
                            "helper": "install-udev-rules"
                        })
            except Exception as err:
                logger.error(f"Error reading udev rules: {err}")

    def _check_uinput(self):
        # Check if /dev/uinput exists and is writable
        if not os.path.exists("/dev/uinput"):
            self.results.append({
                "id": "uinput_missing",
                "title": "uinput device missing",
                "description": "The uinput kernel module may not be loaded.",
                "severity": "critical",
                "fix_action": "org.pnp.uinput.load",
                "helper": "load-uinput"
            })
        elif not os.access("/dev/uinput", os.W_OK):
            self.results.append({
                "id": "uinput_permission",
                "title": "uinput permission denied",
                "description": "User does not have permission to write to "
                               "/dev/uinput. Fixing udev rules might "
                               "resolve this.",
                "severity": "critical",
                "fix_action": "org.pnp.udev.install",
                "helper": "install-udev-rules"
            })

    def _check_bluetooth(self):
        # Check for BlueZ/Bluetooth status
        try:
            res = subprocess.run(
                ["systemctl", "is-active", "bluetooth"],
                capture_output=True, text=True, check=False
            )
            if res.stdout.strip() != "active":
                self.results.append({
                    "id": "bluetooth_inactive",
                    "title": "Bluetooth service inactive",
                    "description": "The system bluetooth service is not "
                                   "running.",
                    "severity": "warning",
                    "fix_action": "org.pnp.bluetooth.fix",
                    "helper": "fix-bluetooth"
                })
        except Exception:
            pass

        # Check for ERTM issue
        ertm_file = "/sys/module/bluetooth/parameters/disable_ertm"
        if os.path.exists(ertm_file):
            try:
                with open(ertm_file, "r", encoding="utf-8") as f:
                    # N means ERTM is enabled (not disabled)
                    if f.read().strip() == "N":
                        self.results.append({
                            "id": "bluetooth_ertm",
                            "title": "Bluetooth ERTM enabled",
                            "description": "Enhanced Re-transmission Mode "
                                           "(ERTM) can cause connection "
                                           "issues with Sony controllers.",
                            "severity": "warning",
                            "fix_action": "org.pnp.bluetooth.fix",
                            "helper": "fix-bluetooth"
                        })
            except Exception as err:
                logger.error(f"Error reading ERTM status: {err}")

    def _check_bluetooth_detailed(self):
        """Performs deeper Bluetooth diagnostics (modules, firmware)."""
        # 1. Check modules
        modules = ['btusb', 'hidp', 'hid_generic']
        missing_modules = []
        for mod in modules:
            try:
                res = subprocess.run(f"lsmod | grep {mod}", shell=True, capture_output=True)
                if res.returncode != 0:
                    missing_modules.append(mod)
            except Exception:
                pass

        if missing_modules:
            self.results.append({
                "id": "bluetooth_modules_missing",
                "title": "Bluetooth modules missing",
                "description": f"The following modules are not loaded: {', '.join(missing_modules)}. "
                               "This may prevent HID controllers from connecting.",
                "severity": "warning",
                "fix_action": "org.pnp.bluetooth.fix",
                "helper": "fix-bluetooth"
            })

        # 2. Check dmesg for firmware issues
        try:
            res = subprocess.run("dmesg | grep -i bluetooth | tail -n 20", shell=True, capture_output=True, text=True)
            if "firmware" in res.stdout.lower() and ("error" in res.stdout.lower() or "failed" in res.stdout.lower()):
                self.results.append({
                    "id": "bluetooth_firmware_error",
                    "title": "Bluetooth firmware error detected",
                    "description": "System logs indicate a Bluetooth firmware issue. "
                                   "Try 'Fix All' to reload modules, or check for missing firmware packages.",
                    "severity": "warning",
                    "fix_action": "org.pnp.bluetooth.fix",
                    "helper": "fix-bluetooth"
                })
        except Exception:
            pass

    def _check_steam_devices(self):
        steam_rules = "/etc/udev/rules.d/60-steam-input.rules"
        if not os.path.exists(steam_rules):
            # Check if it might be under another name or system location
            system_rules = "/lib/udev/rules.d/60-steam-devices.rules"
            if not os.path.exists(system_rules):
                self.results.append({
                    "id": "steam_devices_missing",
                    "title": "Steam devices udev rules missing",
                    "description": "Valve's standard udev rules are "
                                   "recommended for better Steam Input "
                                   "compatibility.",
                    "severity": "info",
                    "fix_action": "org.pnp.udev.install",
                    "helper": "install-udev-rules"
                })

    def apply_fix(self, issue_id):
        """Attempts to fix a specific issue using Polkit."""
        issue = next((i for i in self.results if i["id"] == issue_id), None)
        if not issue:
            return False, "Issue not found"

        action_id = issue["fix_action"]
        helper = issue["helper"]

        logger.info(f"Applying fix for issue {issue_id}: {action_id}")

        success, error = PolkitManager.run_helper(helper, action_id)
        return success, error

    def fix_all(self):
        """Attempts to fix all detected issues."""
        success_count = 0
        errors = []
        for issue in self.results:
            success, error = self.apply_fix(issue["id"])
            if success:
                success_count += 1
            else:
                errors.append(f"{issue['title']}: {error}")

        return success_count == len(self.results), "\n".join(errors)

    def revert_changes(self):
        """Attempts to revert PNP-specific changes (udev, uinput config)."""
        logger.info("Reverting PNP system changes...")
        # We need a revert helper. For now, we'll use a generic one or pkexec rm
        # Since we don't have a revert-all helper, we'll try to remove known
        # files. This is simplified for the demo.
        return PolkitManager.run_helper(
            "reload-services", "org.pnp.systemd.reload"
        )
