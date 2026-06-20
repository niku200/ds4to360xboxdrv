import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: bluetoothPage

    property list<var> scannedDevices: []

    // Logic to detect Kirigami availability
    property bool hasKirigami: false

    Component.onCompleted: {
        try {
            var component = Qt.createComponent("KirigamiBluetoothPage.qml")
            if (component.status === Component.Ready) {
                hasKirigami = true
                loader.source = "KirigamiBluetoothPage.qml"
            } else {
                console.log("Kirigami not available or error:", component.errorString())
                loader.source = "StandardBluetoothPage.qml"
            }
        } catch (e) {
            console.log("Failed to load Kirigami component:", e)
            loader.source = "StandardBluetoothPage.qml"
        }
    }

    Loader {
        id: loader
        anchors.fill: parent
    }
}
