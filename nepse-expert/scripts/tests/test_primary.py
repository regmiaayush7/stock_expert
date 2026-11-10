#!/usr/bin/env python3
"""
test_primary.py - unit tests for primary market / right share TERP calculations.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import primary

class TestPrimary(unittest.TestCase):
    def test_terp(self):
        # Current price 300, 50% right share (50 per 100) at par value 100
        terp = primary.theoretical_ex_rights_price(300.0, 50.0, 100.0)
        expected = (300.0 * 100.0 + 100.0 * 50.0) / 150.0
        self.assertAlmostEqual(terp, expected, places=2)

if __name__ == '__main__':
    unittest.main()
