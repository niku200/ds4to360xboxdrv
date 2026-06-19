import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    id: logPage

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        RowLayout {
            width: parent.width
            Label {
                text: "System Logs"
                font.pixelSize: 24
                font.bold: true
                Layout.fillWidth: true
            }

            ComboBox {
                id: levelFilter
                model: ["All", "INFO", "WARNING", "ERROR", "DEBUG"]
                onCurrentTextChanged: backend.setLogLevelFilter(currentText)
            }

            ComboBox {
                id: moduleFilter
                model: ["All", "USB", "Steam", "Mapping", "System", "GUI"]
                onCurrentTextChanged: backend.setLogModuleFilter(currentText)
            }

            Button {
                text: "📋 Copy All"
                onClicked: {
                    logArea.selectAll()
                    logArea.copy()
                    logArea.deselect()
                }
            }
            Button {
                text: "🗑️ Clear"
                onClicked: backend.clearLogs()
            }
        }

        Frame {
            Layout.fillWidth: true
            Layout.fillHeight: true
            padding: 0

            background: Rectangle {
                color: "#1E1E1E"
                radius: 4
            }

            ScrollView {
                anchors.fill: parent
                ScrollBar.vertical.policy: ScrollBar.AlwaysOn

                TextArea {
                    id: logArea
                    readOnly: true
                    text: backend.logs
                    font.family: "Monospace"
                    font.pixelSize: 12
                    color: "#D4D4D4"
                    wrapMode: TextEdit.Wrap

                    onTextChanged: {
                        if (logArea.length > 0) {
                            cursorPosition = logArea.length - 1
                        }
                    }
                }
            }
        }
    }
}
