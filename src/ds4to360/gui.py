import sys
import shutil
import logging
from gi.repository import Gtk, Adw, GLib, Gio
from ds4to360.gui.main_window import Application
from ds4to360.core.manager import ControllerManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/tmp/ds4to360-gui.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def is_service_active():
    try:
        res = subprocess.run(["systemctl", "is-active", "ds4-xboxdrv.service"], capture_output=True, text=True)
        return res.stdout.strip() == "active"
    except:
        return False

def check_dependencies():
    missing = []
    if not shutil.which('xboxdrv'):
        missing.append('xboxdrv')
    if not shutil.which('evsieve'):
        missing.append('evsieve')
    return missing

def main():
    missing = check_dependencies()
    if missing:
        print(f"Error: Missing system dependencies: {', '.join(missing)}")
        # We can't show a Gtk dialog yet because no app is running,
        # but the Application class will handle it in do_activate.

    try:
        import subprocess # Needed for is_service_active
        if is_service_active():
            logger.info("Service is active. GUI running in observer mode.")
            manager = None
        else:
            manager = ControllerManager()
            manager.start()

        app = Application(manager)
        app.missing_deps = missing
        return app.run(sys.argv)
    except Exception as e:
        logger.critical(f"Unhandled exception in GUI: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    main()
