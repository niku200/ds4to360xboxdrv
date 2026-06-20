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
                Button {
                    text: "🔄 Reset Stack"
                    flat: true
                    onClicked: resetDialog.open()
                }
            }
        }

        // Progress Indicator
        Rectangle {
            Layout.fillWidth: true
            height: 30
            color: "#333"
            radius: 4
            visible: pairingProgress.text !== ""
            RowLayout {
                anchors.fill: parent
                anchors.margins: 5
                BusyIndicator {
                    running: true
                    Layout.preferredWidth: 20
                    Layout.preferredHeight: 20
                }
                Label {
                    id: pairingProgress
                    text: ""
                    font.pixelSize: 12
                    font.italic: true
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
                        Button {
                            text: "🧹 Clear"
                            flat: true
                            onClicked: backend.clearBluetoothCache(modelData.mac)
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

    Dialog {
        id: resetDialog
        title: "Reset Bluetooth Stack"
        standardButtons: Dialog.Ok | Dialog.Cancel
        anchors.centerIn: parent
        modal: true
        ColumnLayout {
            spacing: 10
            Label {
                text: "This will reload Bluetooth kernel modules and restart the service."
                font.bold: true
                wrapMode: Text.WordWrap
                Layout.preferredWidth: 300
            }
            Label {
                text: "This can help fix HID protocol and SDP record errors."
                font.pixelSize: 12
                opacity: 0.8
            }
        }
        onAccepted: {
            pairingProgress.text = "Resetting Bluetooth stack..."
            backend.applyDiagnosticFix("bluetooth_inactive") // Re-use fix-bluetooth helper
        }
    }

    Connections {
        target: backend
        function onBluetoothLogReceived(message, prefix) {
            bluetoothLogs.append(prefix + " " + message)

            // Extract SM progress from logs
            if (message.includes("Pairing SM [")) {
                pairingProgress.text = message
            } else if (message.includes("Pairing SM [SUCCESS]")) {
                pairingProgress.text = ""
                toast.show("Bluetooth pairing successful!")
            } else if (message.includes("Pairing SM [FAIL]") || message.includes("Pairing SM [ERROR]")) {
                pairingProgress.text = ""
                toast.show("Pairing failed. Check logs for details.")
            }
        }
        function onBluetoothScanFinished(devices) {
            bluetoothPage.scannedDevices = devices
        }
        function onFixCompleted(success, message) {
            if (pairingProgress.text === "Resetting Bluetooth stack...") {
                pairingProgress.text = ""
                if (success) toast.show("Bluetooth stack reset complete.")
                else toast.show("Failed to reset stack: " + message)
            }
        }
    }
}
