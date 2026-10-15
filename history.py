"""Private local workout storage; no network/cloud synchronization."""
import os
from pathlib import Path
import sqlite3
import threading
import time


class History:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'bikeerg/workouts.sqlite3'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.active = None
        self.last_motion = 0
        self.last_tick = None
        self.last_elapsed = None
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY, started REAL NOT NULL, ended REAL,
                    duration_s REAL DEFAULT 0, distance_m REAL DEFAULT 0,
                    avg_power REAL DEFAULT 0, max_power REAL DEFAULT 0,
                    avg_cadence REAL DEFAULT 0, samples INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS samples (
                    session_id INTEGER NOT NULL, t REAL NOT NULL,
                    power REAL, cadence REAL, heart_rate REAL, speed REAL
                );
                CREATE INDEX IF NOT EXISTS sample_session ON samples(session_id, t);
            ''')
            # A killed service must not leave an apparently running workout.
            db.execute('UPDATE sessions SET ended = COALESCE((SELECT MAX(t) FROM samples WHERE session_id=sessions.id), started) WHERE ended IS NULL')
        self.path.chmod(0o600)

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def finish(self, now):
        if self.active is not None:
            with self.connect() as db:
                db.execute('UPDATE sessions SET ended=? WHERE id=?', (self.last_tick or now, self.active))
        self.active = None
        self.last_tick = None
        self.last_elapsed = None

    def tick(self, state, now=None):
        now = time.time() if now is None else now
        with self.lock:
            fresh = state.get('connected') and now-state.get('last_sample', 0) < 5
            m = state.get('metrics', {})
            watts = max(0, m.get('power_w', 0)) if fresh else 0
            cadence = max(0, m.get('cadence_rpm', 0)) if fresh else 0
            moving = fresh and (watts > 0 or cadence > 0)
            elapsed = m.get('elapsed_s') if fresh else None
            reset = elapsed is not None and self.last_elapsed is not None and elapsed < self.last_elapsed
            if reset or (self.active is not None and now-self.last_motion >= 90):
                self.finish(now)
            if not fresh:
                # Don't count an unknown interval as recorded exercise.
                self.last_tick = None
                return
            if self.active is None:
                if not moving: return
                with self.connect() as db:
                    self.active = db.execute('INSERT INTO sessions(started) VALUES (?)', (now,)).lastrowid
            if moving: self.last_motion = now
            dt = min(2, max(0, now-self.last_tick)) if self.last_tick else 0
            self.last_tick = now
            self.last_elapsed = elapsed
            speed = max(0, m.get('speed_kmh', 0))
            with self.connect() as db:
                db.execute('INSERT INTO samples VALUES (?,?,?,?,?,?)', (self.active, now, watts, cadence, m.get('heart_rate_bpm'), speed))
                db.execute('''UPDATE sessions SET duration_s=duration_s+?, distance_m=distance_m+?,
                    avg_power=(avg_power*samples+?)/(samples+1),
                    avg_cadence=(avg_cadence*samples+?)/(samples+1),
                    max_power=MAX(max_power,?), samples=samples+1 WHERE id=?''',
                    (dt, speed/3.6*dt, watts, cadence, watts, self.active))

    def list(self):
        with self.lock, self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM sessions ORDER BY started DESC LIMIT 200')]

    def detail(self, session_id):
        with self.lock, self.connect() as db:
            row = db.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone()
            if row is None: return None
            result = dict(row)
            result['points'] = [dict(r) for r in db.execute('SELECT t,power,cadence,heart_rate,speed FROM samples WHERE session_id=? ORDER BY t', (session_id,))]
            return result
