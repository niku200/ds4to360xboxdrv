# Bluetooth UI Redesign Research Summary

## KDE Human Interface Guidelines (HIG) Applied
- **Direct Manipulation**: Action buttons ("Pair", "Connect", "Clear") are placed directly next to the relevant device.
- **Visual Feedback**: Real-time logging and pairing state machine progress provide immediate feedback on system operations.
- **Platform Integration**: Utilizing system-native theme engine (Kvantum/Breeze) and standard layouts to ensure the app feels "at home" on KDE Plasma.

## Kirigami Design Principles Applied
- **Content is King**: Minimized chrome to focus on the device list and live event logs.
- **Theming**: Strict adherence to `Kirigami.Theme` for all colors to support both light and dark modes dynamically.
- **Layouts**: Used `Kirigami.FormLayout` for structured management tasks and `Kirigami.PlaceholderMessage` for empty states.
- **Spacing**: Standardized spacing using `Kirigami.Units` (`gridUnit`, `smallSpacing`, `largeSpacing`).
- **Monospace Logs**: Monospace font used for log output to ensure technical readability (BlueZ/Journal events).
