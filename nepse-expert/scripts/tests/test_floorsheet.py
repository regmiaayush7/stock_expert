#!/usr/bin/env python3
"""
test_floorsheet.py - unit tests for floorsheet broker concentration analysis.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import floorsheet

class TestFloorsheet(unittest.TestCase):
    def test_concentration_warning(self):
        trades = [
            {'buyer_broker': '34', 'seller_broker': '58', 'qty': 5000, 'price': 400},
            {'buyer_broker': '34', 'seller_broker': '12', 'qty': 4500, 'price': 401}
        ]
        res = floorsheet.analyze_floorsheet(trades)
        self.assertIsNotNone(res['warning'])
        self.assertGreater(res['max_buyer_share'], 0.40)

    def test_normal_floorsheet(self):
        trades = [
            {'buyer_broker': '1', 'seller_broker': '2', 'qty': 100, 'price': 400},
            {'buyer_broker': '3', 'seller_broker': '4', 'qty': 100, 'price': 401}
        ]
        res = floorsheet.analyze_floorsheet(trades)
        self.assertIsNone(res['warning'])

if __name__ == '__main__':
    unittest.main()
