#!/usr/bin/env python3
"""
screen.py - Idea screener scorecard for NEPSE symbols.
Ranks candidates via quality, valuation, growth, dividends, technicals, liquidity, catalysts, and risk.
"""

import sys
import json
from pathlib import Path

def score_stock(symbol, data):
    weights = {
        'quality': 0.20,
        'valuation': 0.15,
        'growth': 0.15,
        'dividends': 0.15,
        'technicals': 0.10,
        'liquidity': 0.15,
        'catalysts': 0.10
    }
    raw_score = sum(data.get(k, 5.0) * w for k, w in weights.items())
    final_score = max(0.0, raw_score - data.get('risk_penalty', 0.0))
    return round(final_score, 2)

def screen_candidates(candidates_dict):
    scored = []
    for sym, d in candidates_dict.items():
        s = score_stock(sym, d)
        scored.append({'symbol': sym, 'score': s, 'details': d})
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored

if __name__ == '__main__':
    print('screen.py ready')
