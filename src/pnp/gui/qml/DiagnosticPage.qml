import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    id: diagnosticPage

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        RowLayout {
            width: parent.width
            ColumnLayout {
                Label {
                    text: "System Diagnostics"
                    font.pixelSize: 24
                    font.bold: true
                }
                Label {
                    text: "Identify and resolve configuration conflicts for Steam Input."
                    font.pixelSize: 14
                    opacity: 0.7
                }
            }
            Item { Layout.fillWidth: true }
            Button {
                text: "🔍 Run Scan"
                highlighted: true
                onClicked: backend.runDiagnostics()
            }
        }

        ListView {
            id: diagList
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: backend.diagnosticIssues
            spacing: 15
            clip: true

            delegate: Frame {
                width: parent.width
                padding: 15

                background: Rectangle {
                    color: modelData.severity === "critical" ? "#442222" :
                           modelData.severity === "warning" ? "#443322" : "#2A2A2A"
                    radius: 8
                    border.color: modelData.severity === "critical" ? "#FF5555" :
                                  modelData.severity === "warning" ? "#FFB86C" : "#555"
                }

                RowLayout {
                    width: parent.width
                    spacing: 15

                    Label {
                        text: modelData.severity === "critical" ? "🔴" :
                              modelData.severity === "warning" ? "🟠" : "🔵"
                        font.pixelSize: 24
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Label {
                            text: modelData.title
                            font.bold: true
                            font.pixelSize: 16
                        }
                        Label {
                            text: modelData.description
                            font.pixelSize: 13
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                            opacity: 0.8
                        }
                    }

                    Button {
                        text: "🔧 Fix Now"
                        onClicked: {
                            diagMessageDialog.issueId = modelData.id
                            diagMessageDialog.open()
                        }
                    }
                }
            }

            placeholderText: "No issues detected. Your system is correctly configured for PNP."
            Label {
                anchors.centerIn: parent
                visible: diagList.count === 0
                text: diagList.placeholderText
                font.italic: true
                opacity: 0.5
            }
        }
    }

    Dialog {
        id: diagMessageDialog
        property string issueId: ""
        title: "Administrative Privileges Required"
        standardButtons: Dialog.Ok | Dialog.Cancel
        anchors.centerIn: parent
        modal: true

        ColumnLayout {
            spacing: 10
            Label {
                text: "Applying this fix requires administrative privileges."
                font.bold: true
            }
            Label {
                text: "A system dialog will ask for your password to authorize the change."
                wrapMode: Text.WordWrap
                Layout.preferredWidth: 300
            }
        }

        onAccepted: backend.applyDiagnosticFix(issueId)
    }

    Connections {
        target: backend
        function onFixCompleted(success, message) {
            toast.show(success ? "Fix applied successfully!" : "Failed to apply fix: " + message)
        }
    }
}
