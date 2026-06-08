import os
import sys
import shutil
import logging
import subprocess

# Wayland / X11 compatibility fixes
wayland_display = os.environ.get('WAYLAND_DISPLAY')
is_plasma = 'plasma' in os.environ.get('XDG_CURRENT_DESKTOP', '').lower()

if wayland_display and is_plasma and not os.environ.get('GDK_BACKEND'):
    # Try Wayland first – GTK4 works well on Plasma 5.27+
    os.environ['GDK_BACKEND'] = 'wayland'

# Disable GDK internal scaling overrides to let the compositor handle it
os.environ['GDK_DPI_SCALE'] = '1'
os.environ['GDK_SCALE'] = '1'

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
from pnp.gui.main_window import Application
from pnp.core.manager import ControllerManager

# Configure logging
# For GUI, logging to stderr is usually enough as it can be captured if run from terminal
# or viewed in journal if launched via desktop entry (sometimes).
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def is_service_active():
    try:
        res = subprocess.run(["systemctl", "is-active", "pnp.service"], capture_output=True, text=True)
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
