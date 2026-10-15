# BikeErg for Omarchy

Local bar plugin for PM5 431575390 (FE:B5:DD:E6:C6:F8).

- Widget.qml: live watts and PM5 workout elapsed time; click for FTMS metrics and game launcher.
- bridge.py: read-only Bluetooth notifications, automatic reconnect, atomic runtime JSON.
- game.html: minimal cycling landscape prototype driven by live watts.
- ~/.config/systemd/user/bikeerg.service: starts bridge at login.
- Python environment: ~/.local/share/bikeerg/venv (bleak 3.0.2).

Local endpoint: http://127.0.0.1:18765/game and /api/state. Bound to loopback, no CORS.
Runtime state: $XDG_RUNTIME_DIR/bikeerg.json. No workout history is stored.

The panel exposes standard Indoor Bike Data fields provided by the PM5, not the full proprietary CSAFE command set. Missing data is marked with a dash; heart rate requires a sensor. Time and distance come from the PM5 workout, rather than counting the app's runtime. Browser game distance is simulated separately.

Commands:

    systemctl --user restart bikeerg
    journalctl --user -u bikeerg -n 30
    omarchy plugin disable hhammarstrand.bikeerg
    systemctl --user disable --now bikeerg

To use a different monitor, edit ADDRESS in bridge.py and restart the service.

## Installation

Requires Omarchy with Quickshell plugins, Linux/BlueZ, Bluetooth and `uv`.

```bash
git clone https://github.com/hhammarstrand/omarchy-bikeerg.git ~/.config/omarchy/plugins/hhammarstrand.bikeerg
cd ~/.config/omarchy/plugins/hhammarstrand.bikeerg
./install.sh
```

If this directory already exists, preserve it before cloning. The repository is
currently private, so cloning requires GitHub access.

On the PM5, choose **Connect**. The widget sits immediately to the right of the
clock in the center section, and is only visible while the PM5 is connected.
The background bridge starts at login and retries when the monitor disconnects.
It does not change workouts or resistance.

## Development and validation

```bash
~/.local/share/bikeerg/venv/bin/python -m unittest discover -s tests
bash -n install.sh
```

Validated with the real BikeErg: power, cadence, elapsed workout time, distance,
speed and calories. The panel and browser game were also visually checked.
Missing optional metrics display a dash. This is an initial local prototype;
the game currently provides a scrolling landscape rather than objectives.
