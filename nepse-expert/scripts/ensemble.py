#!/usr/bin/env python3
"""
ensemble.py - averages independent methods and reports model disagreement as uncertainty.
"""

import sys

def combine_forecasts(forecast_lists):
    """
    forecast_lists: list of lists of floats (each list is a method's horizon predictions)
    """
    if not forecast_lists:
        return [], []

    horizon = len(forecast_lists[0])
    means = []
    spreads = []

    for h in range(horizon):
        vals = [f[h] for f in forecast_lists if len(f) > h]
        if not vals:
            means.append(0.0)
            spreads.append(0.0)
            continue
        mean_val = sum(vals) / len(vals)
        spread = max(vals) - min(vals)
        means.append(round(mean_val, 2))
        spreads.append(round(spread, 2))

    return means, spreads

if __name__ == '__main__':
    print('ensemble.py ready')
