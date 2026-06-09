import sys
import argparse
import logging
from pnp.gui import main as gui_main
from pnp.backend import main as backend_main

def main():
    parser = argparse.ArgumentParser(description="PNP (PS NOT PS) – PlayStation to Xbox controller emulator")
    parser.add_argument('--headless', action='store_true', help="Run in headless mode (backend only)")
    parser.add_argument('--debug', action='store_true', help="Enable debug logging")

    # We only parse known args to allow passing other args to GTK/Backend if needed
    args, unknown = parser.parse_known_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.getLogger().setLevel(log_level)

    if args.headless:
        # Headless mode: run the backend service
        # We need to strip our own args before passing to backend_main if it expected sys.argv
        sys.argv = [sys.argv[0]] + unknown
        backend_main()
    else:
        # GUI mode (default)
        sys.argv = [sys.argv[0]] + unknown
        gui_main()

if __name__ == "__main__":
    main()
