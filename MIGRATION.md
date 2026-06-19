# PNP Migration Guide: GTK4 to PySide6/QML

This document outlines the major architectural changes made during the migration of PNP from GTK4/Libadwaita to PySide6 and Qt Quick (QML).

## 1. Architectural Overview

The project has moved from a GObject-based architecture to a Qt-based one. This ensures better cross-platform compatibility and a more responsive, animated UI.

| Component | Legacy (GTK4) | New (PySide6/QML) |
|-----------|---------------|-------------------|
| **Base Class** | `GObject.Object` | `QObject` |
| **Signals** | `__gsignals__` | `QtCore.Signal` |
| **Timers** | `GLib.timeout_add` | `QtCore.QTimer` |
| **IO Watch** | `GLib.io_add_watch` | `QtCore.QSocketNotifier` |
| **UI Definition** | Python code (imperative) | QML (declarative) |
| **Logging** | `logging` | `loguru` |

## 2. Backend Changes

### Core Logic refactor
- `DeviceMonitor`, `Controller`, and `ControllerManager` now inherit from `QObject`.
- Communication between backend components and the UI is handled through Qt Signals and Slots.
- `QSocketNotifier` is used to monitor `evdev` file descriptors and `udev` events without blocking the event loop.

### Process Management
- Background processes (like `evsieve`) are still managed via `subprocess`, but their lifecycles are more tightly integrated with Qt's event loop.

## 3. Frontend Changes

### QML Architecture
- The UI is now defined in `.qml` files located in `src/pnp/gui/qml/`.
- `main.qml` serves as the primary entry point, using a `StackLayout` for tab navigation.
- Pages:
    - `MonitorPage.qml`: Controller management and battery status.
    - `TesterPage.qml`: Real-time input visualization.
    - `SettingsPage.qml`: Configuration and service management.
    - `GameLibraryPage.qml`: Steam Input profile management.
    - `NonSteamPage.qml`: Heroic/Hydra games integration.
    - `LogPage.qml`: System logs.

### Python-QML Bridge
- The `Backend` class in `src/pnp/gui/backend.py` is exposed to QML via `engine.rootContext().setContextProperty("backend", backend)`.
- QML uses property bindings to automatically update when backend state changes.

## 4. Dependency Changes

- **Removed**: `PyGObject`, `gtk4`, `libadwaita`.
- **Added**: `PySide6`, `loguru`.

## 5. Entry Points

- `pnp-gui` and `pnp-backend` still work as expected but now initialize a `QGuiApplication` or `QCoreApplication` respectively.
- The `--debug` flag now enables verbose logging via `loguru`.
