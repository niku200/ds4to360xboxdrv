import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    id: gameLibraryPage

    Component.onCompleted: backend.refreshSteamGames()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        RowLayout {
            width: parent.width
            ColumnLayout {
                Label {
                    text: "Steam Game Library"
                    font.pixelSize: 24
                    font.bold: true
                }
                Label {
                    text: "Manage Steam Input profiles for your games."
                    font.pixelSize: 14
                    opacity: 0.7
                }
            }
            Item { Layout.fillWidth: true }
            Button {
                text: "🔄 Refresh"
                onClicked: backend.refreshSteamGames()
            }
        }

        ListView {
            id: gameList
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: backend.steamGames
            spacing: 10
            clip: true

            delegate: Frame {
                width: parent ? parent.width : 0
                padding: 15

                background: Rectangle {
                    color: "#2A2A2A"
                    radius: 8
                    border.color: "#444"
                }

                RowLayout {
                    width: parent.width
                    spacing: 15

                    ColumnLayout {
                        Layout.fillWidth: true
                        Label {
                            text: modelData.name
                            font.bold: true
                            font.pixelSize: 16
                        }
                        Label {
                            text: "AppID: " + modelData.appid
                            font.pixelSize: 12
                            opacity: 0.6
                        }
                    }

                    Rectangle {
                        width: 100
                        height: 24
                        radius: 12
                        color: modelData.applied ? "#4CAF50" : "#555"
                        visible: modelData.applied
                        Label {
                            anchors.centerIn: parent
                            text: "Profile Applied"
                            color: "white"
                            font.pixelSize: 10
                            font.bold: true
                        }
                    }

                    Button {
                        text: modelData.applied ? "Update Profile" : "Download Profile"
                        onClicked: backend.downloadGameProfile(modelData.appid)
                    }
                }
            }
        }
    }
}
