import os
import subprocess
from PySide6.QtDBus import QDBusInterface, QDBusConnection
from loguru import logger

class PolkitManager:
    @staticmethod
    def check_authorization(action_id):
        """Checks if the user is authorized for a specific Polkit action using QtDBus."""
        try:
            if not QDBusConnection.systemBus().isConnected():
                logger.error("D-Bus: Not connected to system bus")
                return False

            authority = QDBusInterface(
                "org.freedesktop.PolicyKit1",
                "/org/freedesktop/PolicyKit1/Authority",
                "org.freedesktop.PolicyKit1.Authority",
                QDBusConnection.systemBus()
            )

            if not authority.isValid():
                logger.error(
                    f"D-Bus: Polkit interface invalid: {authority.lastError().message()}"
                )
                return False

            # For brevity and reliability in this specific environment where
            # dbus-python failed, we can also fallback to a simple pkcheck call
            # which is a standard polkit utility.
            logger.debug(f"Checking authorization for {action_id} via pkcheck")
            res = subprocess.run([
                "pkcheck",
                "--action-id", action_id,
                "--process", str(os.getpid()),
                "--allow-user-interaction"
            ], capture_output=True, check=False)

            is_authorized = res.returncode == 0
            logger.debug(f"Polkit check for {action_id}: authorized={is_authorized}")
            return is_authorized

        except Exception as err:
            logger.error(f"Error checking Polkit authorization for {action_id}: {err}")
            return False

    @staticmethod
    def run_helper(helper_name, action_id):
        """Runs a privileged helper script via pkexec."""
        helper_path = f"/usr/lib/pnp/helpers/{helper_name}"

        if not os.path.exists(helper_path):
            logger.warning(
                f"Helper not found at {helper_path}. Expecting system installation."
            )

        logger.info(f"Executing privileged helper: {helper_name} via pkexec")

        try:
            result = subprocess.run(
                ["pkexec", helper_path],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                logger.info(f"Helper {helper_name} completed successfully.")
                return True, ""

            error_msg = result.stderr.strip() or f"Exit code {result.returncode}"
            logger.error(f"Helper {helper_name} failed: {error_msg}")
            return False, error_msg
        except Exception as err:
            logger.exception(f"Exception running helper {helper_name}: {err}")
            return False, str(err)
