#!/usr/bin/env python3
"""
test_forecast.py - unit tests for forecasting module.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import forecast

class TestForecast(unittest.TestCase):
    def test_naive(self):
        series = [100, 102, 105]
        res = forecast.forecast_naive(series, 3)
        self.assertEqual(res, [105, 105, 105])

    def test_momentum(self):
        series = [100, 105, 110]
        res = forecast.forecast_momentum(series, 2, 2)
        self.assertEqual(len(res), 2)

if __name__ == '__main__':
    unittest.main()
