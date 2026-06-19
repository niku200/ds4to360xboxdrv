import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material

ApplicationWindow {
    id: window
    visible: true
    width: 900
    height: 700
    title: "PNP – PS NOT PS"

    Material.theme: Material.Dark
    Material.accent: Material.LightBlue

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        StackLayout {
            id: stackLayout
            currentIndex: tabBar.currentIndex
            Layout.fillWidth: true
            Layout.fillHeight: true

            MonitorPage {}
            TesterPage {}
            DiagnosticPage {}
            SettingsPage {}
            LogPage {}
        }

        TabBar {
            id: tabBar
            Layout.fillWidth: true
            currentIndex: 0

            TabButton {
                text: "📺 Monitor"
            }
            TabButton {
                text: "🎮 Tester"
            }
            TabButton {
                text: "🔍 Diags"
            }
            TabButton {
                text: "⚙️ Settings"
            }
            TabButton {
                text: "📜 Logs"
            }
        }
    }

    // Simple Toast Component
    Item {
        id: toast
        property string message: ""
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 80
        width: toastLabel.width + 40
        height: 40
        opacity: 0
        visible: opacity > 0

        Rectangle {
            anchors.fill: parent
            color: "#333"
            radius: 20
            border.color: "#555"
        }

        Label {
            id: toastLabel
            anchors.centerIn: parent
            text: toast.message
            color: "white"
        }

        function show(msg) {
            message = msg
            toastAnim.restart()
        }

        SequentialAnimation on opacity {
            id: toastAnim
            NumberAnimation { to: 1; duration: 200 }
            PauseAnimation { duration: 3000 }
            NumberAnimation { to: 0; duration: 500 }
        }
    }
}
