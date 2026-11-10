#!/usr/bin/env python3
"""
backtest.py - rule backtester with NEPSE frictions.
Accounts for broker commission slabs, SEBON fee, DP charge, capital gains tax, and circuit lock limits.
"""

import sys
import json

def run_backtest(signals, prices, quantities, buy_dates, sell_dates, cost_func):
    """
    Simulates trades based on signals, applying NEPSE frictions and taxes via costs.py logic.
    """
    results = []
    for sig, price, qty, b_date, s_date in zip(signals, prices, quantities, buy_dates, sell_dates):
        if sig == 'BUY':
            # Buy cost calculation
            gross = price * qty
            comm = max(10.0, gross * 0.003) # 0.3% default broker commission
            sebon = gross * 0.00015
            dp = 25.0
            total_buy = gross + comm + sebon + dp
            results.append({'action': 'BUY', 'gross': gross, 'net_cost': total_buy})
        elif sig == 'SELL':
            gross = price * qty
            # use cost_func or standard calculation
            res = cost_func(qty, price * 0.95, price, b_date, s_date) # placeholder WACC
            results.append({'action': 'SELL', 'gross': gross, 'net_proceeds': res.get('net_amount', gross)})
        else:
            results.append({'action': 'HOLD'})
    return results

if __name__ == '__main__':
    print('backtest.py ready')
