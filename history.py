"""Private local workout storage; no network/cloud synchronization."""
from contextlib import contextmanager
from datetime import date, datetime, timedelta
import math
import os
from pathlib import Path
import re
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
        self.last_connection = None
        self.last_distance = self.last_distance_stamp = None
        self.last_calories = self.last_calorie_stamp = None
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY, started REAL NOT NULL, ended REAL,
                    duration_s REAL DEFAULT 0, distance_m REAL DEFAULT 0,
                    avg_power REAL DEFAULT 0, max_power REAL DEFAULT 0,
                    avg_cadence REAL DEFAULT 0, samples INTEGER DEFAULT 0,
                    power_samples INTEGER DEFAULT 0, cadence_samples INTEGER DEFAULT 0,
                    calories_kcal REAL
                );
                CREATE TABLE IF NOT EXISTS samples (
                    session_id INTEGER NOT NULL, t REAL NOT NULL,
                    power REAL, cadence REAL, heart_rate REAL, speed REAL
                );
                CREATE INDEX IF NOT EXISTS sample_session ON samples(session_id, t);
                CREATE INDEX IF NOT EXISTS session_started ON sessions(started);
            ''')
            columns = {row['name'] for row in db.execute('PRAGMA table_info(sessions)')}
            for name, definition in [('power_samples', 'INTEGER DEFAULT 0'),
                                     ('cadence_samples', 'INTEGER DEFAULT 0'),
                                     ('calories_kcal', 'REAL')]:
                if name not in columns:
                    db.execute(f'ALTER TABLE sessions ADD COLUMN {name} {definition}')
                    if name != 'calories_kcal':
                        db.execute(f'UPDATE sessions SET {name}=samples')
            db.execute('UPDATE sessions SET ended = COALESCE((SELECT MAX(t) FROM samples WHERE session_id=sessions.id), started) WHERE ended IS NULL')
        self.path.chmod(0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def finish(self, now):
        if self.active is not None:
            with self.connect() as db:
                db.execute('UPDATE sessions SET ended=? WHERE id=?', (self.last_tick or now, self.active))
        self.active = None
        self.last_tick = None
        self.last_elapsed = None
        self.last_distance = self.last_distance_stamp = None
        self.last_calories = self.last_calorie_stamp = None

    @staticmethod
    def metric(state, key, now):
        times = state.get('metric_times')
        stamp = times.get(key) if times is not None else state.get('last_sample')
        if not state.get('connected') or stamp is None or not 0 <= now - stamp < 5:
            return None, None
        return state.get('metrics', {}).get(key), stamp

    def tick(self, state, now=None):
        now = time.time() if now is None else now
        with self.lock:
            connection = state.get('connection_seq')
            if connection is not None and connection != self.last_connection:
                self.last_connection = connection
                self.last_tick = None
                self.last_distance = self.last_distance_stamp = None
                self.last_calories = self.last_calorie_stamp = None
            raw_power, _ = self.metric(state, 'power_w', now)
            raw_cadence, _ = self.metric(state, 'cadence_rpm', now)
            watts = max(0, raw_power) if isinstance(raw_power, (int, float)) else None
            cadence = max(0, raw_cadence) if isinstance(raw_cadence, (int, float)) else None
            fresh = watts is not None or cadence is not None
            moving = (watts or 0) > 0 or (cadence or 0) > 0
            elapsed, _ = self.metric(state, 'elapsed_s', now)
            reset = elapsed is not None and self.last_elapsed is not None and elapsed < self.last_elapsed
            if reset or (self.active is not None and now - self.last_motion >= 90):
                self.finish(now)
            if not fresh:
                self.last_tick = None
                self.last_distance = self.last_distance_stamp = None
                self.last_calories = self.last_calorie_stamp = None
                return
            if self.active is None:
                if not moving:
                    return
                with self.connect() as db:
                    self.active = db.execute('INSERT INTO sessions(started) VALUES (?)', (now,)).lastrowid
            if moving:
                self.last_motion = now
            dt = min(2, max(0, now - self.last_tick)) if self.last_tick is not None else 0
            self.last_tick = now
            if elapsed is not None:
                self.last_elapsed = elapsed

            distance, distance_stamp = self.metric(state, 'distance_m', now)
            speed, _ = self.metric(state, 'speed_kmh', now)
            distance_delta = 0.0
            if isinstance(distance, (int, float)) and 0 <= distance < 16777215:
                if self.last_distance is not None and distance_stamp != self.last_distance_stamp:
                    delta = distance - self.last_distance
                    seconds = max(1, distance_stamp - self.last_distance_stamp)
                    if 0 <= delta <= 25 * seconds:
                        distance_delta = delta
                self.last_distance = distance
                self.last_distance_stamp = distance_stamp
            else:
                self.last_distance = self.last_distance_stamp = None
                if isinstance(speed, (int, float)) and speed >= 0:
                    distance_delta = speed / 3.6 * dt

            calories, calorie_stamp = self.metric(state, 'calories_kcal', now)
            calorie_delta = None
            if isinstance(calories, (int, float)) and 0 <= calories < 65535:
                calorie_delta = 0.0
                if self.last_calories is not None and calorie_stamp != self.last_calorie_stamp:
                    delta = calories - self.last_calories
                    if 0 <= delta <= 100:
                        calorie_delta = delta
                self.last_calories = calories
                self.last_calorie_stamp = calorie_stamp
            else:
                self.last_calories = self.last_calorie_stamp = None

            pulse, _ = self.metric(state, 'heart_rate_bpm', now)
            with self.connect() as db:
                db.execute('INSERT INTO samples(session_id,t,power,cadence,heart_rate,speed) VALUES (?,?,?,?,?,?)',
                           (self.active, now, watts, cadence, pulse, speed))
                db.execute('''UPDATE sessions SET
                    duration_s=duration_s+?, distance_m=distance_m+?,
                    avg_power=CASE WHEN ? IS NULL THEN avg_power ELSE (avg_power*power_samples+?)/(power_samples+1) END,
                    power_samples=power_samples+CASE WHEN ? IS NULL THEN 0 ELSE 1 END,
                    avg_cadence=CASE WHEN ? IS NULL THEN avg_cadence ELSE (avg_cadence*cadence_samples+?)/(cadence_samples+1) END,
                    cadence_samples=cadence_samples+CASE WHEN ? IS NULL THEN 0 ELSE 1 END,
                    max_power=MAX(max_power,COALESCE(?,0)), samples=samples+1,
                    calories_kcal=CASE WHEN ? IS NULL THEN calories_kcal ELSE COALESCE(calories_kcal,0)+? END
                    WHERE id=?''',
                    (dt, distance_delta, watts, watts, watts, cadence, cadence, cadence,
                     watts, calorie_delta, calorie_delta, self.active))

    def list(self):
        with self.lock, self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM sessions ORDER BY started DESC LIMIT 200')]

    @staticmethod
    def downsample(points, limit=1200):
        if not points:
            return []
        gaps = {i for i in range(1, len(points)) if points[i]['t'] - points[i-1]['t'] > 3}
        if len(points) <= limit:
            indexes = range(len(points))
        else:
            selected = {0, len(points)-1} | gaps | {i-1 for i in gaps}
            size = math.ceil(len(points) / max(1, limit // 6))
            for start in range(0, len(points), size):
                chunk = range(start, min(len(points), start + size))
                selected.update((chunk.start, chunk.stop-1,
                                 min(chunk, key=lambda i: points[i]['power'] or 0),
                                 max(chunk, key=lambda i: points[i]['power'] or 0),
                                 min(chunk, key=lambda i: points[i]['cadence'] or 0),
                                 max(chunk, key=lambda i: points[i]['cadence'] or 0)))
            indexes = sorted(selected)
        return [{**dict(points[i]), 'gap': i in gaps} for i in indexes]

    def detail(self, session_id):
        with self.lock, self.connect() as db:
            row = db.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone()
            if row is None:
                return None
            result = dict(row)
            points = db.execute('SELECT t,power,cadence,heart_rate,speed FROM samples WHERE session_id=? ORDER BY t', (session_id,)).fetchall()
            result['points'] = self.downsample(points)
            result['points_total'] = len(points)
            return result

    @staticmethod
    def totals(rows):
        known = [row['calories_kcal'] for row in rows if row['calories_kcal'] is not None]
        return {'sessions': len(rows),
                'duration_s': sum(row['duration_s'] for row in rows),
                'distance_m': sum(row['distance_m'] for row in rows),
                'max_power': max((row['max_power'] for row in rows), default=0),
                'calories_kcal': sum(known) if known else None,
                'calorie_coverage': len(known)}

    def overview(self, period='week', anchor=''):
        """Whole-history aggregates. Sessions belong to their local start date."""
        today = date.today()
        if period == 'week':
            if anchor:
                match = re.fullmatch(r'(\d{4})-W(\d{2})', anchor)
                if not match:
                    raise ValueError('Invalid week')
                start = date.fromisocalendar(int(match[1]), int(match[2]), 1)
            else:
                start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=7)
            previous_start = start - timedelta(days=7)
            bounds = [start + timedelta(days=i) for i in range(8)]
            previous_bounds = [previous_start + timedelta(days=i) for i in range(8)]
            title = f'Vecka {start.isocalendar().week}, {start.isocalendar().year}'
        elif period == 'month':
            if anchor and not re.fullmatch(r'\d{4}-\d{2}', anchor):
                raise ValueError('Invalid month')
            start = date.fromisoformat((anchor or today.strftime('%Y-%m')) + '-01')
            end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
            previous_start = date(start.year - (start.month == 1), (start.month - 2) % 12 + 1, 1)
            bounds = [start + timedelta(days=i) for i in range((end-start).days+1)]
            previous_bounds = [previous_start + timedelta(days=i) for i in range((start-previous_start).days+1)]
            title = ('januari','februari','mars','april','maj','juni','juli','augusti','september','oktober','november','december')[start.month-1] + f' {start.year}'
        elif period == 'year':
            if anchor and not re.fullmatch(r'\d{4}', anchor):
                raise ValueError('Invalid year')
            year = int(anchor or today.year)
            start, end, previous_start = date(year,1,1), date(year+1,1,1), date(year-1,1,1)
            bounds = [date(year + (month == 13), (month-1) % 12 + 1, 1) for month in range(1,14)]
            previous_bounds = [date(year-1 + (month == 13), (month-1) % 12 + 1, 1) for month in range(1,14)]
            title = str(year)
        elif period == 'lifetime':
            if anchor:
                raise ValueError('Lifetime has no anchor')
            with self.lock, self.connect() as db:
                first = db.execute('SELECT MIN(started) AS started FROM sessions').fetchone()['started']
            year = datetime.fromtimestamp(first).year if first is not None else today.year
            start, end, previous_start = date(year,1,1), date(today.year+1,1,1), None
            bounds = [date(y,1,1) for y in range(year,today.year+2)]
            previous_bounds = []
            title = 'Hela historiken'
        else:
            raise ValueError('Invalid period')

        timestamp = lambda day: datetime.combine(day, datetime.min.time()).timestamp()
        start_ts, end_ts = timestamp(start), timestamp(end)
        previous_ts = timestamp(previous_start) if previous_start else None
        with self.lock, self.connect() as db:
            current = db.execute('SELECT * FROM sessions WHERE started>=? AND started<? ORDER BY started', (start_ts,end_ts)).fetchall()
            previous = db.execute('SELECT * FROM sessions WHERE started>=? AND started<? ORDER BY started', (previous_ts,start_ts)).fetchall() if previous_ts is not None else []

        def buckets(rows, edges):
            result = []
            for low, high in zip(edges, edges[1:]):
                group = [row for row in rows if timestamp(low) <= row['started'] < timestamp(high)]
                result.append({'label':low.isoformat(), **self.totals(group)})
            return result

        return {'period':period, 'title':title, 'start':start.isoformat(),
                'end_exclusive':end.isoformat(), 'timezone':datetime.now().astimezone().tzname(),
                'current':self.totals(current),
                'previous':self.totals(previous) if previous_ts is not None else None,
                'bins':buckets(current,bounds), 'previous_bins':buckets(previous,previous_bounds),
                'attribution':'Pass räknas till det lokala datum då de började.'}
