# BikeErg for Omarchy

**Your Concept2 BikeErg, in your desktop bar.**

Live watts and workout time beside your clock, a click-to-open stats panel, and
a browser game powered by your pedalling. Built for Omarchy's Quickshell desktop
and a Concept2 PM5 connected over Bluetooth.

## What it does

- **Live bar widget:** power in watts and elapsed workout time, directly to the
  right of the clock in the center section.
- **Connection-aware visibility:** appears when the PM5 is connected and hides
  when disconnected. You don't have to be pedalling for it to remain visible.
- **Workout details:** click the widget for power, cadence, speed, distance,
  calories, averages and other standard metrics supplied by the monitor.
- **Browser game launcher:** open **Frirull** from the panel. Your power moves a
  bicycle through a scrolling landscape.
- **Shared connection:** one background process supplies both the desktop
  widget and the browser. The browser needs no Bluetooth permissions.
- **Automatic startup and reconnect:** a systemd user service starts at login
  and retries the connection when the monitor is unavailable.

### Current status

An early, working personal project, tested with a real BikeErg on Omarchy.
The bar and stats panel are functional. The game currently provides a minimal
free-ride prototype; routes, objectives and progression are the next development
step.

## Requirements

| Component | Requirement |
| --- | --- |
| Desktop | Omarchy with the Quickshell shell and plugin commands |
| Bike | Concept2 BikeErg with a Bluetooth-capable PM5 |
| Bluetooth | Working Linux Bluetooth adapter and BlueZ |
| Tools | `git`, `uv`, and systemd user services |
| Browser | A modern browser supporting Canvas and JavaScript |

Other Concept2 ergs, older PM5 firmware and other Linux desktops have not been
validated. The widget relies on Omarchy's UI components.

## Install

```bash
git clone https://github.com/hhammarstrand/omarchy-bikeerg.git \
  ~/.config/omarchy/plugins/hhammarstrand.bikeerg
cd ~/.config/omarchy/plugins/hhammarstrand.bikeerg
```

**Configure your monitor before starting the service:** edit `ADDRESS` in
`bridge.py` to match your PM5's Bluetooth address. The current default is the
maintainer's own monitor. The `device` label in the initial state is also a
personal default and can be changed independently.

To find the address, wake the PM5, select **Connect**, then scan:

```bash
bluetoothctl --timeout 15 scan le
bluetoothctl devices
```

Look for a device named `PM5 …`. If another app is using its Bluetooth app
connection, disconnect that app first.

Run the installer from the plugin directory:

```bash
./install.sh
```

The installer creates a dedicated Python environment under
`~/.local/share/bikeerg/venv`, installs the pinned dependencies, installs and starts
`bikeerg.service`, enables the plugin, and places it immediately after the clock.
It does not require sudo. If a plugin directory already exists, preserve that
copy before cloning.

## Use

1. Wake the PM5 and select **Connect**.
2. Wait for the BikeErg widget to appear beside the clock.
3. Start pedalling to see live watts and the PM5's workout time.
4. Click the widget to open the stats panel.
5. Select **Öppna spel** to launch the browser game.

The interface is currently in Swedish. The game can also be opened directly:

**[Open Frirull](http://127.0.0.1:18765/game)** ·
**[Inspect live JSON](http://127.0.0.1:18765/api/state)**

These links work on the computer running the bridge.

### Understanding the numbers

Time and distance in the desktop panel come from the **PM5 workout**, not from
how long the app has been open. Reset or start a workout on the PM5 to begin a
new workout there.

Game distance is a separate, simplified simulation based on watts. It does not
match the PM5's distance. The **Börja om** button resets the game only.

A dash in the panel means that a metric is unavailable. Heart rate requires a
compatible sensor connected to the PM5. Values may stop updating when the
monitor stops transmitting; stale data is marked accordingly.

## How it works

```text
Concept2 PM5
    │ Bluetooth LE notifications
    ▼
bridge.py — systemd user service
    ├── $XDG_RUNTIME_DIR/bikeerg.json ──► Omarchy widget and stats panel
    └── http://127.0.0.1:18765
          ├── /game       ────────────► Browser game
          └── /api/state  ────────────► Live JSON
```

The bridge reads the standard **Fitness Machine / Indoor Bike Data** and
**Cycling Power** characteristics. It does not implement the complete proprietary
Concept2 CSAFE interface, so the panel is not an exhaustive view of everything
stored inside the monitor.

It only reads training notifications: it does not change workouts or control
resistance. The BikeErg's damper is adjusted manually.

The HTTP server binds to loopback only and does not enable CORS. No account,
cloud service or Concept2 Logbook credentials are required. The bridge stores
current runtime state, not workout history.

## Manage and troubleshoot

```bash
# Check the service and recent errors
systemctl --user status bikeerg
journalctl --user -u bikeerg -n 50 --no-pager

# Restart after changing the Bluetooth address or bridge code
systemctl --user restart bikeerg

# Inspect current data
curl http://127.0.0.1:18765/api/state
```

| Symptom | What to check |
| --- | --- |
| Widget is hidden | It only appears while connected. Wake the PM5, select Connect, and check the service logs and configured address. |
| Connected but no watts | Start pedalling; check `/api/state` for `last_sample` and the received packets. |
| No heart rate | Connect a compatible heart-rate sensor to the PM5. |
| Game cannot connect | Check that `bikeerg.service` is running and port 18765 is available. |
| Widget changes don't appear | Run `omarchy-shell shell rescanPlugins`; if necessary, `omarchy restart shell`. |

### Update

```bash
cd ~/.config/omarchy/plugins/hhammarstrand.bikeerg
git pull --ff-only
./install.sh
systemctl --user restart bikeerg
```

Keep track of local edits to `bridge.py` before pulling updates.

### Disable or remove

```bash
omarchy plugin disable hhammarstrand.bikeerg
systemctl --user disable --now bikeerg
```

To remove it completely, also remove the plugin directory, the dedicated
`~/.local/share/bikeerg` environment and
`~/.config/systemd/user/bikeerg.service`, then run
`systemctl --user daemon-reload`.

## Development

| File | Purpose |
| --- | --- |
| `manifest.json` | Omarchy plugin metadata |
| `Widget.qml` | Bar widget, popup and browser launcher |
| `bridge.py` | BLE connection, FTMS decoding, runtime state and HTTP server |
| `game.html` | Self-contained browser game prototype |
| `systemd/bikeerg.service` | User service template |
| `install.sh` | Local installation and bar placement |
| `tests/test_bridge.py` | Packet decoding and truncated-packet checks |

Run the checks from the repository root:

```bash
~/.local/share/bikeerg/venv/bin/python -m unittest discover -s tests
bash -n install.sh
git diff --check
```

Real-device validation has covered power, cadence, workout time, distance,
speed and calories. The panel and game have also been visually checked.
Reconnection across every monitor/adapter combination has not been tested.

## References

- [Concept2 software development and PM5 specifications](https://www.concept2.com/support/software-development)
- [Omarchy](https://omarchy.org/)
- [Bleak](https://github.com/hbldh/bleak)

This is an independent project, not an official Concept2 or Omarchy product.
