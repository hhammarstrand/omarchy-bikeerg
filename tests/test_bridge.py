import unittest
from bridge import indoor


class IndoorBikeDataTests(unittest.TestCase):
    def test_real_pm5_energy_packet(self):
        self.assertEqual(indoor(bytes.fromhex('000117082b001202ff')), {
            'speed_kmh': 20.71,
            'calories_kcal': 43,
            'calories_per_hour': 530,
            'calories_per_minute': 255,
        })

    def test_split_packet_without_instant_speed(self):
        self.assertEqual(indoor(bytes.fromhex('450064009cff')), {
            'cadence_rpm': 50.0, 'power_w': -100,
        })

    def test_truncated_field(self):
        with self.assertRaises(ValueError):
            indoor(bytes.fromhex('4000'))
