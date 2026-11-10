#!/usr/bin/env python3
"""
indicators.py - technical indicators on adjusted price series for NEPSE.
Computes SMA, EMA, RSI, MACD, ATR, OBV, and Relative Strength.
"""

import sys
import json
from pathlib import Path

def sma(series, period):
    if len(series) < period:
        return [None] * len(series)
    res = [None] * (period - 1)
    for i in range(period - 1, len(series)):
        val = sum(series[i - period + 1 : i + 1]) / period
        res.append(val)
    return res

def ema(series, period):
    if len(series) < period:
        return [None] * len(series)
    res = [None] * (period - 1)
    multiplier = 2 / (period + 1)
    # Start EMA with SMA
    init_sma = sum(series[:period]) / period
    curr = init_sma
    res.append(curr)
    for i in range(period, len(series)):
        curr = (series[i] - curr) * multiplier + curr
        res.append(curr)
    return res

def rsi(closes, period=14):
    if len(closes) < period + 1:
        return [None] * len(closes)
    res = [None] * period
    gains, losses = [], []
    for i in range(1, period + 1):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        res.append(100.0)
    else:
        rs = avg_gain / avg_loss
        res.append(100 - (100 / (1 + rs)))

    for i in range(period + 1, len(closes)):
        diff = closes[i] - closes[i-1]
        gain = max(diff, 0)
        loss = max(-diff, 0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        if avg_loss == 0:
            res.append(100.0)
        else:
            rs = avg_gain / avg_loss
            res.append(100 - (100 / (1 + rs)))
    return res

def macd(closes, fast=12, slow=26, signal=9):
    fast_ema = ema(closes, fast)
    slow_ema = ema(closes, slow)
    macd_line = []
    for f, s in zip(fast_ema, slow_ema):
        if f is None or s is None:
            macd_line.append(None)
        else:
            macd_line.append(f - s)
    valid_macd = [m for m in macd_line if m is not None]
    sig_line_valid = ema(valid_macd, signal) if valid_macd else []

    # pad signal line
    pad_count = len(macd_line) - len(sig_line_valid)
    signal_line = [None] * pad_count + sig_line_valid

    histogram = []
    for m, s in zip(macd_line, signal_line):
        if m is None or s is None:
            histogram.append(None)
        else:
            histogram.append(m - s)
    return {'macd': macd_line, 'signal': signal_line, 'histogram': histogram}

def atr(highs, lows, closes, period=14):
    if len(closes) < 2:
        return [None] * len(closes)
    trs = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    return sma(trs, period)

def obv(closes, volumes):
    if not closes or not volumes:
        return []
    res = [volumes[0]]
    for i in range(1, len(closes)):
        if closes[i] > closes[i-1]:
            res.append(res[-1] + volumes[i])
        elif closes[i] < closes[i-1]:
            res.append(res[-1] - volumes[i])
        else:
            res.append(res[-1])
    return res

def relative_strength(stock_closes, index_closes, period=30):
    if len(stock_closes) != len(index_closes):
        return []
    ratio = [s / i if i != 0 else None for s, i in zip(stock_closes, index_closes)]
    return sma([r for r in ratio if r is not None], period)

def analyze(series_data):
    closes = [b['close'] for b in series_data]
    highs = [b.get('high', b['close']) for b in series_data]
    lows = [b.get('low', b['close']) for b in series_data]
    volumes = [b.get('volume', 1000) for b in series_data]

    return {
        'sma_20': sma(closes, 20),
        'ema_20': ema(closes, 20),
        'rsi_14': rsi(closes, 14),
        'macd': macd(closes),
        'atr_14': atr(highs, lows, closes, 14),
        'obv': obv(closes, volumes)
    }

if __name__ == '__main__':
    print('indicators.py ready')
