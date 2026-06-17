import sys
import os
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QTimer
from loguru import logger
from pnp.gui.backend import Backend

class LogSink:
    def __init__(self, backend):
        self.backend = backend

    def write(self, message):
        # Remove ANSI color codes if any
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_msg = ansi_escape.sub('', message)
        self.backend.appendLog(clean_msg)

def main():
    # Ensure src directory is in sys.path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    app = QGuiApplication(sys.argv)
    app.setApplicationName("PNP")
    app.setOrganizationName("pakrohk")
    app.setApplicationVersion("5.2.0")

    engine = QQmlApplicationEngine()

    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)

    # Configure Loguru
    logger.remove() # Remove default handler
    logger.add(sys.stderr, colorize=True, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

    log_sink = LogSink(backend)
    logger.add(log_sink.write, format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}\n")

    qml_file = os.path.join(os.path.dirname(__file__), "qml", "main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
