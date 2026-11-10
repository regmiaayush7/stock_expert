#!/usr/bin/env python3
"""
forecast.py - baseline forecasting models and regime detection for NEPSE.
Implements naive, moving average, mean reversion, and momentum baselines.
"""

import sys

def forecast_naive(series, horizon=5):
    if not series:
        return []
    last = series[-1]
    return [last] * horizon

def forecast_momentum(series, horizon=5, window=10):
    if len(series) < window:
        return forecast_naive(series, horizon)
    recent_return = (series[-1] - series[-window]) / series[-window]
    last = series[-1]
    return [round(last * (1 + recent_return * (i / window)), 2) for i in range(1, horizon + 1)]

if __name__ == '__main__':
    print('forecast.py ready')
