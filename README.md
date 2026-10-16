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
- **Arcade launcher:** open the game selection from the panel. Play Orbital,
  Velodrift or Lumen using the same live power feed.
- **Shared connection:** one background process supplies both the desktop
  widget and the browser. The browser needs no Bluetooth permissions.
- **Automatic startup and reconnect:** a systemd user service starts at login
  and retries the connection when the monitor is unavailable.

### Current status

An early, working personal project, tested with a real BikeErg on Omarchy.
The bar and stats panel are functional. Orbital includes Arcade, Chill and
Interval modes, enemy waves, upgrades, a charged special attack and demo mode.
Velodrift and Lumen share the keyboard arcade menu and settings. The local
dashboard records workouts, shows calendar totals and compares periods.
More game concepts live in [IDEAS.md](IDEAS.md).
Planned improvements are tracked in [TODO.md](TODO.md).

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

**Configure your monitor before starting the service.** Copy the neutral
example to a private file outside the repository, then replace its sample
Bluetooth address with your PM5's address. The optional `device` label is shown
in the widget.

```bash
mkdir -p ~/.config/bikeerg
cp config.example.json ~/.config/bikeerg/config.json
chmod 600 ~/.config/bikeerg/config.json
${EDITOR:-nano} ~/.config/bikeerg/config.json
```

The service reads `~/.config/bikeerg/config.json`, or the path in
`BIKEERG_CONFIG` when set. Local monitor identifiers do not need edits in Git.

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
5. Select **Öppna spel** to launch the arcade, or **Träningslogg / dashboard** for history.

The interface is currently in Swedish. The game can also be opened directly:

**[Open the arcade](http://127.0.0.1:18765/game)** ·
**[Workout dashboard](http://127.0.0.1:18765/dashboard)** ·
**[Inspect live JSON](http://127.0.0.1:18765/api/state)**

These links work on the computer running the bridge.

### Understanding the numbers

Time and distance in the desktop panel come from the **PM5 workout**, not from
how long the app has been open. Reset or start a workout on the PM5 to begin a
new workout there.

### Choose a game

The arcade opens with three game cards. Use arrows and Enter, or click a card.
Each game has target watts, difficulty, Arcade, Chill and Interval modes, plus a
clearly marked demo slider. **Arkaden** returns to game selection; **Spelmeny**
opens settings for the selected game. Scores are stored separately per game,
mode, difficulty and demo/live input.

| Game | Pedalling | Keyboard | Objective |
| --- | --- | --- | --- |
| Orbital | Controls firing cadence and special charging | Left/right; Space for twin shots | Clear enemy waves |
| Velodrift | Accelerates smoothly; target watts reaches maximum speed | Left/right steers the kart | Complete three laps, pass checkpoints in order, collect coins |
| Lumen | Controls lift; about 65% target holds altitude | Left/right moves the craft | Travel 3 km through the cave and collect crystals |

**Velodrift:** higher watts above target never increase maximum speed. Grass
slows the kart and collisions with traffic reduce speed. Chill is free driving;
Interval rests for 20 seconds after each lap. Difficulty changes traffic speed.

**Lumen:** more power makes the craft rise; less power makes it descend. Cave
width depends on difficulty. Arcade gives three shields, Chill has no game over,
and Interval provides 20 seconds of rest every 500 metres.

Game distances and speeds are simulated and separate from PM5 workout data.
These are early playable prototypes with one kart circuit and a procedural cave.

### Fullscreen

The fullscreen button expands the **entire page**, keeping the same header,
sidebar, controls, menus and responsive layout as windowed mode. There is no
separate fullscreen-only scene or hidden stats panel. P / Escape and menu arrows
continue to work; the browser may use Escape to exit fullscreen first.

### Orbital controls and modes

- **Left/right arrow keys:** move the ship horizontally, as in Space Invaders.
- **Pedalling:** automatic fire. Fire rate rises steeply near target watts:
  `shots/s = (0.2 + 9.8 × min(watts / target, 1)^4) × upgrade_multiplier`.
  At zero watts there is no fire. Before upgrades: 50% target gives 0.8 shots/s,
  75% gives 3.3, and target watts gives 10. More watts above target adds no fire rate.
- **Space:** activate ten seconds of twin shots when energy reaches 100%.
  Each volley fires two parallel projectiles instead of one; the firing cadence
  still depends on watts, and enemies are not cleared automatically. The timer
  freezes while paused or choosing an upgrade; charging resumes when it expires. A pulsing golden
  ring around the ship, an in-game label and a highlighted button signal readiness.
  An in-game special-energy bar shows progress in fullscreen too. A full charge
  takes eight seconds at target watts, or sixteen seconds at half target watts.
- **Menus:** Up/down selects a highlighted option, left/right changes settings
  (mode, target watts, difficulty) or moves between actions, Enter confirms, and
  Escape returns/resumes. Settings are available inside the fullscreen menu too.
- **P / Escape:** pause or resume. Switching windows or losing fresh PM5 data pauses
  the action; resume explicitly when ready. When starting a new game before
  the first tramptag, it waits and starts automatically when a positive watt
  reading arrives from the PM5.
- **Arcade:** enemy waves and a limited number of shields.
- **Chill:** no game over; enemies can be cleared at your own pace.
- **Interval:** 20 seconds of recovery after each completed wave and upgrade choice.
- **Demo:** simulated watts with a slider; clearly labelled and kept separate from
  live-game records. It does not generate workout data.

A power HUD inside the playfield shows current / target watts and a progress bar,
including in fullscreen. The bar fills at target watts; the number still shows
actual watts above target.

Target watts and enemy difficulty are separate settings, applied on a new game.
Records and preferences are stored in browser localStorage. Closing the tab ends
an unfinished game. Game upgrades are selected between waves.

### Private workout dashboard

The bridge logs a workout automatically when it receives fresh pedalling data.
After 90 seconds without movement or fresh data, the session closes. A reset of
the PM5 elapsed-time counter also starts a new session. Restarting the service
finalizes any previously open session.

Open `/dashboard` for week, month, year and lifetime totals with a comparison
to the previous period. Choose calendar week, month or year. Totals cover the
entire local history; the pass list shows the latest 200. A pass belongs to the
local date on which it started. The selected pass shows power/cadence charts,
average/maximum watts and PM5 calories when available.
Logging begins when the bridge receives data; earlier parts of a workout cannot
be recovered. Recorded time includes short connected pauses; unknown time during
an interruption is excluded. New passes use PM5 cumulative distance deltas when
available and fresh speed as a fallback. Older recorded totals are not rewritten.
PM5 calorie deltas are recorded from the first reading in a session; older passes
and intervals without calorie data are shown as missing, not estimated. The
dashboard's optional beer/chocolate/banana comparisons show their kcal assumptions.

**Workout history is private local data**, stored outside this repository:

```text
$XDG_DATA_HOME/bikeerg/workouts.sqlite3
# Default: ~/.local/share/bikeerg/workouts.sqlite3
```

The database is created with owner-only file permissions. `.gitignore` also
excludes databases, `data/`, `workouts/`, and `exports/` as a backstop. No workout
database or real workout exports belong in a commit. To back up your history,
stop `bikeerg.service` and copy this database to a private location, then start
the service again. The dashboard is available only on the local computer.
On a computer with multiple local OS users, the localhost HTTP API has no
per-user authentication; another local user could query workout history.

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
          ├── /game         ──────────► Three-game arcade
          ├── /dashboard    ──────────► Workout dashboard
          ├── /api/sessions ──────────► Local workout history
          ├── /api/overview ──────────► Calendar totals and comparison
          └── /api/state    ──────────► Live JSON
```

The bridge reads the standard **Fitness Machine / Indoor Bike Data** and
**Cycling Power** characteristics. It does not implement the complete proprietary
Concept2 CSAFE interface, so the panel is not an exhaustive view of everything
stored inside the monitor.

It only reads training notifications: it does not change workouts or control
resistance. The BikeErg's damper is adjusted manually.

The HTTP server binds to loopback only and does not enable CORS. No account,
cloud service or Concept2 Logbook credentials are required. The bridge writes current runtime state and a separate private local workout database.
The dashboard reads workout history locally; nothing is sent to GitHub.

## Manage and troubleshoot

```bash
# Check the service and recent errors
systemctl --user status bikeerg
journalctl --user -u bikeerg -n 50 --no-pager

# Restart after changing private config or bridge code
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

The private monitor config remains outside the repository when you pull updates.

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
| `config.example.json` | Neutral template for the private PM5 configuration |
| `game.html` | Shared arcade, Orbital, Velodrift and Lumen |
| `dashboard.html` | Local workout history and charts |
| `history.py` | SQLite session recording and queries |
| `IDEAS.md` | Game and dashboard idea bank |
| `systemd/bikeerg.service` | User service template |
| `install.sh` | Local installation and bar placement |
| `tests/test_bridge.py` | Packet decoding and truncated-packet checks |
| `tests/test_history.py` | Recording, migration, counter and calendar tests |

Run the checks from the repository root:

```bash
~/.local/share/bikeerg/venv/bin/python -m unittest discover -s tests
bash -n install.sh
git diff --check
# Browser integration checks (requires Chromium and the local bridge):
uv run --with playwright python tests/browser_check.py
uv run --with playwright python tests/browser_autofire.py
uv run --with playwright python tests/browser_menu_special.py
uv run --with playwright python tests/browser_arcade.py
uv run --with playwright python tests/browser_dashboard.py
uv run --with playwright python tests/browser_review_fixes.py
```

Earlier real-device validation covered power, cadence, workout time, distance,
speed and calories. The latest counter, reconnect and multi-game behavior is
covered by synthetic tests; a complete live PM5 ride after these changes remains
to be checked. Reconnection across every monitor/adapter combination has not
been tested.

## References

- [Concept2 software development and PM5 specifications](https://www.concept2.com/support/software-development)
- [Omarchy](https://omarchy.org/)
- [Bleak](https://github.com/hbldh/bleak)

This is an independent project, not an official Concept2 or Omarchy product.
