#!/usr/bin/env python3
"""
test_screen.py - unit tests for idea screener.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import screen

class TestScreen(unittest.TestCase):
    def test_score_stock(self):
        d = {
            'quality': 8.0,
            'valuation': 7.0,
            'growth': 6.0,
            'dividends': 8.0,
            'technicals': 6.0,
            'liquidity': 9.0,
            'catalysts': 7.0,
            'risk_penalty': 1.0
        }
        score = screen.score_stock('NABIL', d)
        self.assertTrue(0 <= score <= 10)
        self.assertAlmostEqual(score, 6.4, places=2)

    def test_screening_sorts_correctly(self):
        cands = {
            'LOW': {'quality': 3.0, 'valuation': 3.0, 'growth': 3.0, 'dividends': 3.0, 'technicals': 3.0, 'liquidity': 3.0, 'catalysts': 3.0, 'risk_penalty': 0.0},
            'HIGH': {'quality': 9.0, 'valuation': 9.0, 'growth': 9.0, 'dividends': 9.0, 'technicals': 9.0, 'liquidity': 9.0, 'catalysts': 9.0, 'risk_penalty': 0.0}
        }
        res = screen.screen_candidates(cands)
        self.assertEqual(res[0]['symbol'], 'HIGH')
        self.assertEqual(res[1]['symbol'], 'LOW')

if __name__ == '__main__':
    unittest.main()
