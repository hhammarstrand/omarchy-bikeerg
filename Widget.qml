import QtQuick
import Quickshell
import Quickshell.Io
import qs.Ui
import qs.Commons

Panel {
    id: root
    moduleName: "hhammarstrand.bikeerg"
    ipcTarget: "hhammarstrand.bikeerg"
    property var data: ({})
    property double now: Date.now() / 1000
    readonly property bool fresh: data.connected === true && now - (data.last_sample || 0) < 5
    readonly property var metrics: data.metrics || ({})
    visible: data.connected === true && now - (data.updated || 0) < 5
    implicitWidth: visible ? button.implicitWidth : 0
    implicitHeight: button.implicitHeight
    function metricFresh(key) {
        var stamp = data.metric_times ? data.metric_times[key] : data.last_sample
        return data.connected === true && stamp !== undefined && now - stamp >= 0 && now - stamp < 5
    }
    function duration(value, key) {
        if (value === undefined || value === null || value === 65535 || !metricFresh(key)) return "—"
        var s = Math.floor(value)
        return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0")
    }
    function val(key, suffix, digits) {
        var v = metrics[key]
        return !metricFresh(key) || v === undefined || v === null || v === 65535 || v === 255 && key === "calories_per_minute" || (key === "heart_rate_bpm" && (v === 0 || v === 255)) ? "—" : Number(v).toFixed(digits || 0) + suffix
    }
    readonly property var rows: [
        ["Tid · PM5", duration(metrics.elapsed_s, "elapsed_s")],
        ["Effekt", val("power_w", " W")],
        ["Snitteffekt", val("average_power_w", " W")],
        ["Kadens", val("cadence_rpm", " rpm")],
        ["Snittkadens", val("average_cadence_rpm", " rpm")],
        ["Hastighet", val("speed_kmh", " km/h", 1)],
        ["Snitthastighet", val("average_speed_kmh", " km/h", 1)],
        ["Distans", val("distance_m", " m")],
        ["Kalorier", val("calories_kcal", " kcal")],
        ["Kalorier / timme", val("calories_per_hour", " kcal/h")],
        ["Kalorier / minut", val("calories_per_minute", " kcal/min")],
        ["Puls", val("heart_rate_bpm", " bpm")],
        ["Motståndsnivå", val("resistance", "")],
        ["MET", val("metabolic_equivalent", "", 1)],
        ["Återstående tid", duration(metrics.remaining_s, "remaining_s")]
    ]
    FileView {
        id: status
        path: Quickshell.env("XDG_RUNTIME_DIR") + "/bikeerg.json"
        printErrors: false
        watchChanges: true
        onFileChanged: reload()
        onLoaded: { try { root.data = JSON.parse(text()) } catch(e) { root.data = ({}) } }
        onLoadFailed: root.data = ({})
    }
    Timer { interval: 1000; running: true; repeat: true; triggeredOnStart: true; onTriggered: { root.now = Date.now()/1000; status.reload() } }
    WidgetButton {
        id: button
        parent: root
        anchors.fill: parent
        bar: root.bar
        text: root.fresh ? "󰄶 " + root.val("power_w", " W") + " · " + root.duration(root.metrics.elapsed_s, "elapsed_s") : "󰄶 BikeErg"
        dimmed: !root.fresh
        tooltipText: "BikeErg · klicka för detaljer"
        onPressed: root.toggle()
    }
    KeyboardPanel {
        id: popup
        anchorItem: button
        owner: root
        bar: root.bar
        open: root.opened
        focusTarget: keys
        contentWidth: popup.fittedContentWidth(Style.space(380))
        contentHeight: popup.fittedContentHeight(column.implicitHeight)
        PanelKeyCatcher {
            id: keys
            anchors.fill: parent
            onCloseRequested: root.close()
            Column {
                id: column
                width: parent.width
                spacing: Style.space(8)
                Text { text: "BikeErg"; color: root.barForeground; font.pixelSize: Style.font.title; font.bold: true }
                Text { width: parent.width; text: root.data.device || "PM5"; color: root.barForeground; opacity: 0.6; font.pixelSize: Style.font.caption }
                Text { width: parent.width; text: root.fresh ? "Livedata" : (root.data.status || "Bryggan är inte igång") + (root.data.connected ? " · väntar på data" : ""); color: root.barForeground; font.pixelSize: Style.font.caption; wrapMode: Text.Wrap }
                PanelSeparator { foreground: root.barForeground }
                Repeater {
                    model: root.rows
                    Row {
                        required property var modelData
                        width: column.width
                        Text { width: parent.width * 0.60; text: modelData[0]; color: root.barForeground; opacity: 0.65; font.pixelSize: Style.font.bodySmall }
                        Text { width: parent.width * 0.40; text: modelData[1]; horizontalAlignment: Text.AlignRight; color: root.barForeground; font.pixelSize: Style.font.bodySmall }
                    }
                }
                Text { width: parent.width; text: "— = värdet saknas eller har slutat uppdateras från PM5."; wrapMode: Text.Wrap; color: root.barForeground; opacity: 0.5; font.pixelSize: Style.font.caption }
                Button {
                    width: parent.width
                    text: "Öppna spel ↗"
                    foreground: root.barForeground
                    focusable: true
                    onClicked: { Qt.openUrlExternally("http://127.0.0.1:18765/game"); root.close() }
                }
                Button {
                    width: parent.width
                    text: "Träningslogg / dashboard ↗"
                    foreground: root.barForeground
                    focusable: true
                    onClicked: { Qt.openUrlExternally("http://127.0.0.1:18765/dashboard"); root.close() }
                }
            }
        }
    }
}
