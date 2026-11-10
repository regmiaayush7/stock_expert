#!/usr/bin/env python3
"""
calibrate.py - stub: counts the verdicts logged in evals/decision_log.csv.
Hit rate by confidence bucket and Brier score are not built yet (the outcome column has no format), so both are None.
"""

import sys
import csv
from pathlib import Path

def evaluate_calibration(log_path):
    if not Path(log_path).exists():
        return {'total_calls': 0, 'hit_rate': None, 'brier_score': None}

    records = []
    with open(log_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    # None, not a number: a made-up score would be read as a real track record
    return {'total_calls': len(records), 'hit_rate': None, 'brier_score': None}

if __name__ == '__main__':
    print('calibrate.py ready')
