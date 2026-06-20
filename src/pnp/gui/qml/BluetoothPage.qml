import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    id: bluetoothPage

    property list<var> scannedDevices: []

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        RowLayout {
            width: parent.width
            ColumnLayout {
                Label {
                    text: "Bluetooth Management"
                    font.pixelSize: 24
                    font.bold: true
                }
                Label {
                    text: "Troubleshoot and manage controller pairing."
                    font.pixelSize: 14
                    opacity: 0.7
                }
            }
            Item { Layout.fillWidth: true }
            RowLayout {
                spacing: 10
                Button {
                    text: "🔍 Scan"
                    onClicked: {
                        scannedDevices = []
                        backend.scanBluetoothDevices()
                    }
                }
                Button {
                    id: monitorButton
                    property bool active: false
                    text: active ? "🛑 Stop Monitor" : "📟 Start Monitor"
                    onClicked: {
                        active = !active
                        if (active) backend.startBluetoothMonitoring()
                        else backend.stopBluetoothMonitoring()
                    }
                }
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            // Left: Device List
            ListView {
                id: deviceList
                SplitView.preferredWidth: 350
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
                            text: "Connect"
                            onClicked: backend.connectBluetoothDevice(modelData.mac)
                        }
                    }
                }

                Label {
                    anchors.centerIn: parent
                    text: "No devices found. Click Scan."
                    visible: deviceList.count === 0
                    opacity: 0.5
                }
            }

            // Right: Logs
            ColumnLayout {
                Label { text: "Live Events (bluetoothctl + journalctl)"; font.bold: true }
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    TextArea {
                        id: bluetoothLogs
                        readOnly: true
                        font.family: "Monospace"
                        font.pixelSize: 11
                        color: "#00FF00"
                        background: Rectangle { color: "#111" }
                    }
                }
            }
        }
    }

    Connections {
        target: backend
        function onBluetoothLogReceived(message, prefix) {
            bluetoothLogs.append(prefix + " " + message)
        }
        function onBluetoothScanFinished(devices) {
            bluetoothPage.scannedDevices = devices
        }
    }
}
