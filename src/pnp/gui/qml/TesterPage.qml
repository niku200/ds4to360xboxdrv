import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    id: testerPage

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        Label {
            text: "Input Tester"
            font.pixelSize: 24
            font.bold: true
        }

        Label {
            text: "Monitoring active virtual controllers..."
            font.pixelSize: 14
            opacity: 0.7
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: backend.testerDevices
            spacing: 20
            clip: true

            delegate: Frame {
                width: parent.width
                padding: 20

                ColumnLayout {
                    width: parent.width
                    spacing: 20

                    RowLayout {
                        width: parent.width
                        Label {
                            text: modelData.name
                            font.bold: true
                        }
                        Label {
                            text: modelData.path
                            font.pixelSize: 12
                            opacity: 0.6
                            Layout.fillWidth: true
                        }
                        Rectangle {
                            width: 60
                            height: 24
                            radius: 12
                            color: modelData.isVirtual ? "#2196F3" : "#4CAF50"
                            Label {
                                anchors.centerIn: parent
                                text: modelData.isVirtual ? "Virtual" : "Physical"
                                color: "white"
                                font.pixelSize: 10
                                font.bold: true
                            }
                        }
                    }

                    GridLayout {
                        columns: 2
                        columnSpacing: 30
                        rowSpacing: 20
                        Layout.alignment: Qt.AlignHCenter

                        // Simple Visualizer Grid
                        Grid {
                            columns: 3
                            spacing: 10

                            // D-Pad
                            Item { width: 32; height: 32 }
                            TesterButton { text: "U"; active: modelData.buttons[706] }
                            Item { width: 32; height: 32 }
                            TesterButton { text: "L"; active: modelData.buttons[704] }
                            TesterButton { text: "D"; active: modelData.buttons[707] }
                            TesterButton { text: "R"; active: modelData.buttons[705] }
                        }

                        Grid {
                            columns: 3
                            spacing: 10
                            // Action Buttons
                            Item { width: 32; height: 32 }
                            TesterButton { text: "Y"; active: modelData.buttons[308]; accentColor: "#F4D03F" }
                            Item { width: 32; height: 32 }
                            TesterButton { text: "X"; active: modelData.buttons[307]; accentColor: "#3498DB" }
                            TesterButton { text: "A"; active: modelData.buttons[304]; accentColor: "#2ECC71" }
                            TesterButton { text: "B"; active: modelData.buttons[305]; accentColor: "#E74C3C" }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Repeater {
                            model: [
                                { label: "LX", value: modelData.axes[0] },
                                { label: "LY", value: modelData.axes[1] },
                                { label: "RX", value: modelData.axes[2] },
                                { label: "RY", value: modelData.axes[3] },
                                { label: "LT", value: modelData.axes[4] },
                                { label: "RT", value: modelData.axes[5] }
                            ]
                            RowLayout {
                                Label { text: modelData.label; width: 30 }
                                ProgressBar {
                                    Layout.fillWidth: true
                                    value: modelData.value
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    component TesterButton: Rectangle {
        property string text: ""
        property bool active: false
        property color accentColor: "#4CAF50"

        width: 32
        height: 32
        radius: 16
        color: active ? accentColor : "#333"
        border.color: "white"
        border.width: 1
        opacity: active ? 1.0 : 0.3

        Label {
            anchors.centerIn: parent
            text: parent.text
            font.bold: true
            color: "white"
        }

        Behavior on opacity { NumberAnimation { duration: 50 } }
        Behavior on color { ColorAnimation { duration: 50 } }
    }
}
