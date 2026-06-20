import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    id: standardPage

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        RowLayout {
            width: parent.width
            ColumnLayout {
                Label {
                    text: "Bluetooth Management (Standard Mode)"
                    font.pixelSize: 24
                    font.bold: true
                }
                Label {
                    text: "Kirigami not found. Using basic interface."
                    font.pixelSize: 12
                    opacity: 0.7
                }
            }
            Item { Layout.fillWidth: true }
            RowLayout {
                spacing: 10
                Button {
                    text: "🔍 Scan"
                    onClicked: backend.scanBluetoothDevices()
                }
                Button {
                    text: "🔄 Reset Stack"
                    onClicked: resetDialog.open()
                }
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            ListView {
                id: deviceList
                SplitView.preferredWidth: 300
                model: bluetoothPage.scannedDevices
                clip: true
                spacing: 5
                delegate: ItemDelegate {
                    width: parent.width
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        ColumnLayout {
                            Layout.fillWidth: true
                            Label { text: modelData.name; font.bold: true }
                            Label { text: modelData.mac; font.pixelSize: 10; opacity: 0.6 }
                        }
                        Button {
                            text: "Pair"
                            onClicked: backend.pairBluetoothDevice(modelData.mac)
                        }
                        Button {
                            text: "🧹"
                            flat: true
                            onClicked: backend.clearBluetoothCache(modelData.mac)
                        }
                    }
                }
            }

            ColumnLayout {
                Label { text: "Logs:"; font.bold: true }
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    TextArea {
                        id: logs
                        readOnly: true
                        font.family: "Monospace"
                        font.pixelSize: 10
                        color: "#00FF00"
                        background: Rectangle { color: "#111" }
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
        }
        function onBluetoothScanFinished(devices) {
            bluetoothPage.scannedDevices = devices
        }
    }
}
