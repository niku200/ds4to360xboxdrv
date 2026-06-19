import sys
import os
import argparse
from loguru import logger


def handle_cli_command(command):
    import subprocess
    if command == 'start':
        subprocess.run(["systemctl", "--user", "start", "pnp.service"],
                       check=False)
    elif command == 'stop':
        subprocess.run(["systemctl", "--user", "stop", "pnp.service"],
                       check=False)
    elif command == 'pause':
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR",
                                     f"/run/user/{os.getuid()}")
        pnp_run = os.path.join(runtime_dir, "pnp")
        os.makedirs(pnp_run, exist_ok=True)
        with open(os.path.join(pnp_run, "manual_pause"), "w",
                  encoding="utf-8") as f:
            f.write("1")
        print("PNP paused manually.")
    elif command == 'resume':
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR",
                                     f"/run/user/{os.getuid()}")
        flag = os.path.join(runtime_dir, "pnp", "manual_pause")
        if os.path.exists(flag):
            os.remove(flag)
        print("PNP resumed.")
    elif command == 'status':
        subprocess.run(["systemctl", "--user", "status", "pnp.service"],
                       check=False)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    parser = argparse.ArgumentParser(
        description="PNP (PS NOT PS) – PlayStation to Xbox controller emulator"
    )
    parser.add_argument('--headless', action='store_true',
                        help="Run in headless mode (backend only)")
    parser.add_argument('--debug', action='store_true',
                        help="Enable debug logging")
    parser.add_argument(
        'command', nargs='?',
        choices=['start', 'stop', 'pause', 'resume', 'status'],
        help="Service command"
    )

    args, unknown = parser.parse_known_args()

    if args.command:
        handle_cli_command(args.command)
        return

    # Configure Loguru
    log_level = "DEBUG" if args.debug else "INFO"
    logger.remove()
    logger.add(
        sys.stderr,
        level=log_level,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
               "- <level>{message}</level>"
    )

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
