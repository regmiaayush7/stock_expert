#!/usr/bin/env python3
"""
test_ensemble.py - unit tests for ensemble combination.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ensemble

class TestEnsemble(unittest.TestCase):
    def test_combine(self):
        f1 = [100, 105, 110]
        f2 = [102, 104, 108]
        means, spreads = ensemble.combine_forecasts([f1, f2])
        self.assertEqual(means, [101.0, 104.5, 109.0])
        self.assertEqual(spreads, [2.0, 1.0, 2.0])

if __name__ == '__main__':
    unittest.main()
