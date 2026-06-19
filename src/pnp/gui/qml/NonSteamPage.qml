import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    id: nonSteamPage

    property var selectedGame: null

    Component.onCompleted: backend.refreshNonSteamGames()

    RowLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        // Left Panel - Game List
        ColumnLayout {
            Layout.fillHeight: true
            Layout.preferredWidth: 350
            spacing: 15

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                TextField {
                    id: searchBar
                    Layout.fillWidth: true
                    placeholderText: "🔍 Search games..."
                }
                Button {
                    text: "⚙️"
                    flat: true
                    onClicked: settingsDialog.open()
                }
            }

            ListView {
                id: gameList
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: searchBar.text === "" ? backend.nonSteamGames : backend.nonSteamGames.filter(game => game.title.toLowerCase().includes(searchBar.text.toLowerCase()))
                clip: true
                spacing: 8

                delegate: ItemDelegate {
                    width: gameList.width
                    height: 60
                    highlighted: ListView.isCurrentItem

                    onClicked: {
                        gameList.currentIndex = index
                        nonSteamPage.selectedGame = modelData
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 15

                        Label {
                            text: modelData.source === "Heroic" ? "🚀" : "🐉"
                            font.pixelSize: 24
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                text: modelData.title
                                font.bold: true
                                elide: Text.ElideRight
                            }
                            Label {
                                text: modelData.source
                                font.pixelSize: 10
                                opacity: 0.6
                            }
                        }

                        Rectangle {
                            width: 80
                            height: 20
                            radius: 10
                            color: modelData.isAdded ? "#4CAF50" : "#555"
                            Label {
                                anchors.centerIn: parent
                                text: modelData.isAdded ? "Added" : "Not Added"
                                font.pixelSize: 9
                                font.bold: true
                                color: "white"
                            }
                        }
                    }
                }
            }

            Button {
                text: "🔄 Refresh Library"
                Layout.fillWidth: true
                onClicked: backend.refreshNonSteamGames()
            }
        }

        // Right Panel - Game Details
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 20
            visible: selectedGame !== null

            Label {
                text: selectedGame ? selectedGame.title : ""
                font.pixelSize: 28
                font.bold: true
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            GridLayout {
                columns: 2
                columnSpacing: 20
                rowSpacing: 10

                Label { text: "Source:"; opacity: 0.6 }
                Label { text: selectedGame ? selectedGame.source : "" }

                Label { text: "Install Dir:"; opacity: 0.6 }
                Label {
                    text: selectedGame ? selectedGame.installDir : ""
                    elide: Text.ElideMiddle
                    Layout.preferredWidth: 300
                }

                Label { text: "Executable:"; opacity: 0.6 }
                Label {
                    text: selectedGame ? selectedGame.executable : ""
                    elide: Text.ElideMiddle
                    Layout.preferredWidth: 300
                }
            }

            Item { Layout.fillHeight: true }

            RowLayout {
                spacing: 15
                Button {
                    text: "🚀 Add to Steam & Configure"
                    highlighted: true
                    enabled: selectedGame && !selectedGame.isAdded
                    onClicked: backend.addNonSteamGame(selectedGame)
                }

                Button {
                    text: "🗑️ Remove from Steam"
                    enabled: selectedGame && selectedGame.isAdded
                    onClicked: backend.removeNonSteamGame(selectedGame.title)
                }
            }
        }

        // Empty State for Right Panel
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: selectedGame === null

            Label {
                anchors.centerIn: parent
                text: "Select a game to view details"
                opacity: 0.4
                font.pixelSize: 18
            }
        }
    }

    Dialog {
        id: settingsDialog
        title: "Non-Steam Settings"
        standardButtons: Dialog.Ok | Dialog.Cancel
        anchors.centerIn: parent

        ColumnLayout {
            spacing: 15
            Label { text: "Paths Configuration"; font.bold: true }

            TextField {
                id: heroicPath
                Layout.fillWidth: true
                placeholderText: "Heroic Games Directory"
                text: backend.config.heroic_games_dir || "~/Games/Heroic"
            }

            TextField {
                id: hydraPath
                Layout.fillWidth: true
                placeholderText: "Hydra Games Directory"
                text: backend.config.hydra_games_dir || "~/Games/Hydra"
            }
        }

        onAccepted: {
            backend.updateConfig("heroic_games_dir", heroicPath.text)
            backend.updateConfig("hydra_games_dir", hydraPath.text)
            backend.saveConfig()
            backend.refreshNonSteamGames()
        }
    }
}
