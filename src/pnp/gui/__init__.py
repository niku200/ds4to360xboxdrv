import sys
import os
import re
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from loguru import logger
from pnp.gui.backend import Backend
from pnp.gui.tray import TrayManager


class LogSink:
    def __init__(self, backend):
        self.backend = backend

    def write(self, message):
        # Remove ANSI color codes if any
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_msg = ansi_escape.sub('', message)
        self.backend.appendLog(clean_msg)


def main():
    # Ensure src directory is in sys.path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Use QApplication instead of QGuiApplication for QSystemTrayIcon support
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("PNP")
    app.setOrganizationName("pakrohk")
    app.setApplicationVersion("5.2.0")

    engine = QQmlApplicationEngine()

    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)

    # Tray Management
    tray = TrayManager(app)
    tray.show_window_requested.connect(
        lambda: engine.rootObjects()[0].show() if engine.rootObjects() else None
    )
    tray.quit_requested.connect(app.quit)
    tray.start()

    # Configure Loguru
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
               "- <level>{message}</level>"
    )

    log_sink = LogSink(backend)
    logger.add(
        log_sink.write,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}\n"
    )

    qml_file = os.path.join(os.path.dirname(__file__), "qml", "main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
