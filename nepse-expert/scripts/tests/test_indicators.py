#!/usr/bin/env python3
"""
test_indicators.py - unit tests for technical indicators.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import indicators

class TestIndicators(unittest.TestCase):
    def test_sma(self):
        data = [10, 20, 30, 40, 50]
        res = indicators.sma(data, 3)
        self.assertEqual(res, [None, None, 20.0, 30.0, 40.0])

    def test_rsi(self):
        data = [44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28]
        res = indicators.rsi(data, 14)
        self.assertEqual(len(res), len(data))
        self.assertIsNotNone(res[-1])

    def test_obv(self):
        closes = [100, 105, 102, 108]
        volumes = [1000, 2000, 1500, 3000]
        res = indicators.obv(closes, volumes)
        self.assertEqual(res, [1000, 3000, 1500, 4500])

if __name__ == '__main__':
    unittest.main()
