import tempfile
import unittest
from datetime import datetime
from pathlib import Path
import os
import sqlite3
import time
from history import History

class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.h = History(Path(self.temp.name)/'workouts.sqlite3')
    def tearDown(self):
        self.temp.cleanup()
    def tick(self, now, watts=100, elapsed=1, connected=True):
        self.h.tick({'connected':connected,'last_sample':now,'metrics':{'power_w':watts,'cadence_rpm':50 if watts else 0,'elapsed_s':elapsed,'speed_kmh':36 if watts else 0}},now)
    def test_logs_statistics_and_closes_after_idle(self):
        self.tick(100,100,1); self.tick(101,200,2)
        s=self.h.list()[0]
        self.assertEqual(s['duration_s'],1)
        self.assertEqual(s['distance_m'],10)
        self.assertEqual(s['avg_power'],150)
        self.assertEqual(s['max_power'],200)
        self.tick(192,0,3)
        self.assertIsNotNone(self.h.list()[0]['ended'])
        self.assertEqual(len(self.h.detail(s['id'])['points']),2)
    def test_monitor_reset_starts_new_session(self):
        self.tick(100,100,100);self.tick(101,100,1)
        self.assertEqual(len(self.h.list()),2)
    def test_disconnect_does_not_add_unknown_time(self):
        self.tick(100);self.tick(101,connected=False);self.tick(150,elapsed=2)
        self.assertEqual(self.h.list()[0]['duration_s'],0)
    def test_idle_does_not_start_workout(self):
        self.tick(100,0)
        self.assertEqual(self.h.list(),[])
    def test_restart_finalizes_incomplete_session(self):
        self.tick(100); h=History(self.h.path)
        self.assertEqual(h.list()[0]['ended'],100)
    def test_expired_ftms_fields_do_not_extend_motion_or_distance(self):
        base={'connected':True,'metrics':{'power_w':100,'cadence_rpm':50,'speed_kmh':20,'distance_m':100},
              'metric_times':{'power_w':100,'cadence_rpm':100,'speed_kmh':100,'distance_m':100}}
        self.h.tick(base,100)
        for t in range(101,161):
            base['metrics']['power_w']=0
            base['metric_times']['power_w']=t
            self.h.tick(base,t)
        s=self.h.list()[0]
        self.assertEqual(s['distance_m'],0)
        self.assertEqual(s['samples'],61)
        self.h.tick(base,195)
        self.assertIsNotNone(self.h.list()[0]['ended'])
    def test_pm5_distance_and_calories_use_counter_deltas(self):
        state={'connected':True,'metrics':{'power_w':100,'cadence_rpm':50,'speed_kmh':36,
               'distance_m':100,'calories_kcal':20},'metric_times':{key:100 for key in
               ('power_w','cadence_rpm','speed_kmh','distance_m','calories_kcal')}}
        self.h.tick(state,100)
        state['metrics'].update(distance_m=105,calories_kcal=21)
        state['metric_times'].update({key:101 for key in state['metric_times']})
        self.h.tick(state,101)
        self.h.tick(state,102)  # Same counter notification must not be counted twice.
        s=self.h.list()[0]
        self.assertEqual(s['distance_m'],5)
        self.assertEqual(s['calories_kcal'],1)
    def test_fast_reconnect_does_not_count_unknown_counter_jump(self):
        state={'connected':True,'connection_seq':1,
               'metrics':{'power_w':100,'distance_m':100,'calories_kcal':20},
               'metric_times':{'power_w':100,'distance_m':100,'calories_kcal':100}}
        self.h.tick(state,100)
        state['connection_seq']=2
        state['metrics'].update(distance_m=120,calories_kcal=25)
        state['metric_times']={key:101 for key in state['metric_times']}
        self.h.tick(state,101)
        s=self.h.list()[0]
        self.assertEqual(s['distance_m'],0)
        self.assertEqual(s['calories_kcal'],0)
        self.assertEqual(s['duration_s'],0)
    def test_overview_counts_more_than_list_limit(self):
        started=datetime(2026,10,15,12).timestamp()
        with sqlite3.connect(self.h.path) as db:
            db.executemany('INSERT INTO sessions(started,ended,duration_s,distance_m) VALUES (?,?,?,?)',
                           [(started+i,started+i+60,60,100) for i in range(205)])
        self.assertEqual(len(self.h.list()),200)
        overview=self.h.overview('month','2026-10')
        self.assertEqual(overview['current']['sessions'],205)
        self.assertEqual(overview['current']['distance_m'],20500)
        self.assertEqual(overview['current']['calories_kcal'],None)
        self.assertEqual(overview['start'],'2026-10-01')
        self.assertEqual(overview['end_exclusive'],'2026-11-01')
    def test_detail_preserves_peaks_and_gaps_while_downsampling(self):
        self.tick(100)
        session=self.h.list()[0]['id']
        with sqlite3.connect(self.h.path) as db:
            db.executemany('INSERT INTO samples(session_id,t,power,cadence) VALUES (?,?,?,?)',
                           [(session,100+i+(10 if i>=2500 else 0),999 if i==1234 else 100,50)
                            for i in range(5000)])
        points=self.h.detail(session)['points']
        self.assertLess(len(points),1250)
        self.assertIn(999,[p['power'] for p in points])
        self.assertTrue(any(p['gap'] for p in points))
    def test_old_database_migrates_without_inventing_calories(self):
        other=Path(self.temp.name)/'old.sqlite3'
        with sqlite3.connect(other) as db:
            db.execute('CREATE TABLE sessions (id INTEGER PRIMARY KEY, started REAL NOT NULL, ended REAL, duration_s REAL DEFAULT 0, distance_m REAL DEFAULT 0, avg_power REAL DEFAULT 0, max_power REAL DEFAULT 0, avg_cadence REAL DEFAULT 0, samples INTEGER DEFAULT 0)')
            db.execute('CREATE TABLE samples (session_id INTEGER NOT NULL,t REAL NOT NULL,power REAL,cadence REAL,heart_rate REAL,speed REAL)')
            db.execute('INSERT INTO sessions(started,ended,samples) VALUES (100,101,2)')
        migrated=History(other).list()[0]
        self.assertIsNone(migrated['calories_kcal'])
        self.assertEqual(migrated['power_samples'],2)
    def test_calendar_boundaries_follow_local_daylight_saving(self):
        previous=os.environ.get('TZ')
        try:
            os.environ['TZ']='Europe/Stockholm';time.tzset()
            overview=self.h.overview('week','2026-W13')
            self.assertEqual((overview['start'],overview['end_exclusive']),('2026-03-23','2026-03-30'))
            seconds=datetime(2026,3,30).timestamp()-datetime(2026,3,23).timestamp()
            self.assertEqual(seconds,7*86400-3600)
        finally:
            if previous is None: os.environ.pop('TZ',None)
            else: os.environ['TZ']=previous
            time.tzset()
