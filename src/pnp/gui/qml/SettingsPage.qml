import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    id: settingsPage

    ScrollView {
        anchors.fill: parent
        contentWidth: parent.width

        ColumnLayout {
            width: parent.width - 40
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.margins: 20
            spacing: 30

            Label {
                text: "Settings"
                font.pixelSize: 24
                font.bold: true
            }

            GroupBox {
                title: "Steam Integration"
                Layout.fillWidth: true
                ColumnLayout {
                    width: parent.width
                    spacing: 15

                    RowLayout {
                        width: parent.width
                        ColumnLayout {
                            Label { text: "Steam Conflict Prevention"; font.bold: true }
                            Label { text: "Pause emulation when Steam is running"; font.pixelSize: 12; opacity: 0.7 }
                        }
                        Item { Layout.fillWidth: true }
                        Switch {
                            checked: backend.config.steam_handover_enabled
                            onToggled: backend.updateConfig("steam_handover_enabled", checked)
                        }
                    }

                    RowLayout {
                        spacing: 10
                        Button {
                            text: "🔗 Connect to Steam"
                            Layout.fillWidth: true
                            onClicked: backend.connectToSteam()
                        }
                        Button {
                            text: "🔄 Sync with Steam"
                            Layout.fillWidth: true
                            onClicked: backend.syncWithSteam()
                        }
                    }
                }
            }

            GroupBox {
                title: "General Settings"
                Layout.fillWidth: true
                ColumnLayout {
                    width: parent.width

                    RowLayout {
                        width: parent.width
                        ColumnLayout {
                            Label { text: "Theme"; font.bold: true }
                            Label { text: "Switch between Light and Dark mode"; font.pixelSize: 12; opacity: 0.7 }
                        }
                        Item { Layout.fillWidth: true }
                        Switch {
                            checked: true // Hardcoded for now as Material.Dark is set in main.qml
                            text: "Dark Mode"
                            enabled: false
                        }
                    }

                    Separator {}

                    RowLayout {
                        width: parent.width
                        ColumnLayout {
                            Label { text: "Rumble Gain"; font.bold: true }
                            Label { text: "Global force feedback strength"; font.pixelSize: 12; opacity: 0.7 }
                        }
                        Item { Layout.fillWidth: true }
                        TextField {
                            text: backend.config.rumble_gain
                            onEditingFinished: backend.updateConfig("rumble_gain", text)
                        }
                    }
                }
            }

            GroupBox {
                title: "System Service"
                Layout.fillWidth: true
                RowLayout {
                    width: parent.width
                    ColumnLayout {
                        Label { text: "Background Service"; font.bold: true }
                        Label { text: "Manage the system-wide PNP service"; font.pixelSize: 12; opacity: 0.7 }
                    }
                    Item { Layout.fillWidth: true }
                    Switch {
                        checked: backend.serviceActive
                        onToggled: backend.toggleService(checked)
                    }
                }
            }

            GroupBox {
                title: "Global Mapping"
                Layout.fillWidth: true
                ColumnLayout {
                    width: parent.width
                    spacing: 15

                    Repeater {
                        model: [
                            { label: "Axis Map", key: "axismap", value: backend.config.mapping.axismap },
                            { label: "Absolute Map", key: "absmap", value: backend.config.mapping.absmap },
                            { label: "Key Map", key: "keymap", value: backend.config.mapping.keymap }
                        ]
                        ColumnLayout {
                            width: parent.width
                            Label { text: modelData.label; font.bold: true }
                            TextField {
                                Layout.fillWidth: true
                                text: modelData.value
                                onEditingFinished: backend.updateMapping(modelData.key, text)
                            }
                        }
                    }
                }
            }

            Button {
                text: "Save & Apply"
                Layout.alignment: Qt.AlignHCenter
                highlighted: true
                onClicked: backend.saveConfig()
            }
        }
    }

    component Separator: Rectangle {
        Layout.fillWidth: true
        height: 1
        color: "white"
        opacity: 0.1
    }
}
