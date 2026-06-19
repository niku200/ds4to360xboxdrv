from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, Signal
from loguru import logger


class TrayManager(QObject):
    show_window_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray_icon = QSystemTrayIcon(parent)

        # Use an emoji or standard icon as fallback
        # In production, we'd use a real SVG/PNG icon file
        self.tray_icon.setIcon(QIcon.fromTheme("input-gaming-symbolic"))
        self.tray_icon.setToolTip("PNP – PS NOT PS")

        menu = QMenu()

        show_action = QAction("Open PNP", self)
        show_action.triggered.connect(self.show_window_requested.emit)
        menu.addAction(show_action)

        menu.addSeparator()

        quit_action = QAction("Quit Application", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_activated)

    def start(self):
        self.tray_icon.show()
        logger.info("System tray initialized.")

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_window_requested.emit()

    def show_message(self, title, message):
        self.tray_icon.showMessage(title, message)
