import sys
import subprocess
from ds4to360.gui.main_window import Application
from ds4to360.core.manager import ControllerManager

def is_service_active():
    try:
        res = subprocess.run(["systemctl", "is-active", "ds4-xboxdrv.service"], capture_output=True, text=True)
        return res.stdout.strip() == "active"
    except:
        return False

def main():
    if is_service_active():
        print("Service is active. GUI running in observer mode.")
        manager = None
    else:
        manager = ControllerManager()
        manager.start()

    app = Application(manager)
    return app.run(sys.argv)

if __name__ == "__main__":
    main()
