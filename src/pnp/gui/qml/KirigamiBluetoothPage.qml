import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.Page {
    id: kirigamiPage
    title: "Bluetooth Management"

    actions: [
        Kirigami.Action {
            text: "Scan for Devices"
            icon.name: "view-refresh"
            onTriggered: {
                bluetoothPage.scannedDevices = []
                backend.scanBluetoothDevices()
            }
        },
        Kirigami.Action {
            text: "Reset Stack"
            icon.name: "view-restore"
            onTriggered: resetDialog.open()
        }
    ]

    ColumnLayout {
        anchors.fill: parent
        spacing: Kirigami.Units.largeSpacing

        Kirigami.FormLayout {
            Layout.fillWidth: true
            Label {
                Kirigami.FormData.label: "Information:"
                text: "Advanced Bluetooth troubleshooting and controller pairing."
                opacity: 0.7
            }
        }

        Kirigami.InlineMessage {
            id: statusMessage
            Layout.fillWidth: true
            visible: text !== ""
            text: ""
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            ListView {
                id: deviceList
                SplitView.preferredWidth: 350
                model: bluetoothPage.scannedDevices
                clip: true
                spacing: Kirigami.Units.smallSpacing

                delegate: Kirigami.AbstractListItem {
                    contentItem: RowLayout {
                        ColumnLayout {
                            Layout.fillWidth: true
                            Label {
                                text: modelData.name
                                font.bold: true
                                color: Kirigami.Theme.textColor
                            }
                            Label {
                                text: modelData.mac
                                font.pixelSize: Kirigami.Units.gridUnit * 0.6
                                opacity: 0.6
                            }
                        }
                        Button {
                            text: "Pair"
                            onClicked: backend.pairBluetoothDevice(modelData.mac)
                        }
                        Button {
                            icon.name: "edit-clear"
                            onClicked: backend.clearBluetoothCache(modelData.mac)
                        }
                    }
                }

                Kirigami.PlaceholderMessage {
                    anchors.centerIn: parent
                    text: "No devices found"
                    visible: deviceList.count === 0
                    icon.name: "bluetooth"
                }
            }

            ColumnLayout {
                Label { text: "Live Monitor:"; font.bold: true }
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    TextArea {
                        id: logs
                        readOnly: true
                        font.family: "Monospace"
                        font.pixelSize: 10
                        color: Kirigami.Theme.positiveTextColor
                        background: Rectangle {
                            color: Kirigami.Theme.backgroundColor
                            opacity: 0.3
                        }
                        onTextChanged: cursorPosition = text.length
                    }
                }
            }
        }
    }

    Dialog {
        id: resetDialog
        title: "Reset Stack"
        standardButtons: Dialog.Ok | Dialog.Cancel
        onAccepted: backend.applyDiagnosticFix("bluetooth_inactive")
    }

    Connections {
        target: backend
        function onBluetoothLogReceived(message, prefix) {
            logs.append(prefix + " " + message)
            if (message.includes("Pairing SM [")) {
                statusMessage.text = message
                statusMessage.type = message.includes("FAIL") ? Kirigami.MessageType.Error : Kirigami.MessageType.Information
            }
        }
        function onBluetoothScanFinished(devices) {
            bluetoothPage.scannedDevices = devices
        }
    }
}
