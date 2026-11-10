#!/usr/bin/env python3
"""
test_backtest.py - unit tests for backtest engine.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import backtest

class TestBacktest(unittest.TestCase):
    def test_backtest_buy_sell(self):
        signals = ['BUY', 'SELL']
        prices = [500, 600]
        quantities = [100, 100]
        buy_dates = ['2025-01-01', '2025-01-01']
        sell_dates = ['2025-01-01', '2026-02-01']
        dummy_cost = lambda q, w, p, b, s: {'net_amount': 58000.0}
        res = backtest.run_backtest(signals, prices, quantities, buy_dates, sell_dates, dummy_cost)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]['action'], 'BUY')
        self.assertEqual(res[1]['action'], 'SELL')

if __name__ == '__main__':
    unittest.main()
