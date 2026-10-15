import tempfile
import unittest
from pathlib import Path
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
