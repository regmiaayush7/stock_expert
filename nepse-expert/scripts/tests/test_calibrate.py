#!/usr/bin/env python3
"""
test_calibrate.py - unit tests for calibration scoring.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import calibrate

class TestCalibrate(unittest.TestCase):
    def test_missing_log(self):
        res = calibrate.evaluate_calibration('nonexistent.csv')
        self.assertEqual(res['total_calls'], 0)

if __name__ == '__main__':
    unittest.main()
