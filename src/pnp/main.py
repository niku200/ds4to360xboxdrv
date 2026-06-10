import sys
import os
import argparse
import logging

def main():
    parser = argparse.ArgumentParser(description="PNP (PS NOT PS) – PlayStation to Xbox controller emulator")
    parser.add_argument('--headless', action='store_true', help="Run in headless mode (backend only)")
    parser.add_argument('--debug', action='store_true', help="Enable debug logging")

    # We only parse known args to allow passing other args to GTK/Backend if needed
    args, unknown = parser.parse_known_args()

    log_level = logging.DEBUG if args.debug else logging.INFO

    if args.debug:
        os.environ["DEBUG"] = "1"

    # Custom color formatter for terminal
    class ColorFormatter(logging.Formatter):
        GREY = "\x1b[38;20m"
        CYAN = "\x1b[36;20m"
        YELLOW = "\x1b[33;20m"
        RED = "\x1b[31;20m"
        BOLD_RED = "\x1b[31;1m"
        RESET = "\x1b[0m"
        FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        FORMATS = {
            logging.DEBUG: CYAN + FORMAT + RESET,
            logging.INFO: GREY + FORMAT + RESET,
            logging.WARNING: YELLOW + FORMAT + RESET,
            logging.ERROR: RED + FORMAT + RESET,
            logging.CRITICAL: BOLD_RED + FORMAT + RESET
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter())

    # Set up logging globally before importing other pnp modules
    logging.basicConfig(
        level=log_level,
        handlers=[handler],
        force=True
    )

    # Deferred imports to ensure logging is configured first
    if args.headless or "pnp-backend" in sys.argv[0]:
        from pnp.backend import main as backend_main
        sys.argv = [sys.argv[0]] + unknown
        backend_main()
    else:
        from pnp.gui import main as gui_main
        sys.argv = [sys.argv[0]] + unknown
        gui_main()

if __name__ == "__main__":
    main()
