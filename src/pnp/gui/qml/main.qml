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
                text: "⚙️ Settings"
            }
            TabButton {
                text: "📜 Logs"
            }
        }
    }
}
