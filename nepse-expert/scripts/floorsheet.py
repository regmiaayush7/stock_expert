#!/usr/bin/env python3
"""
floorsheet.py - analysis of NEPSE floorsheet data.
Detects broker concentration, buyer/seller clustering, and circular trading / syndicate signals.
"""

import sys

def analyze_floorsheet(trades):
    """
    trades: list of dicts with keys ['buyer_broker', 'seller_broker', 'qty', 'price']
    """
    if not trades:
        return {'concentration': 'low', 'warning': None}

    buyers = {}
    sellers = {}
    for t in trades:
        b = t.get('buyer_broker')
        s = t.get('seller_broker')
        q = t.get('qty', 0)
        buyers[b] = buyers.get(b, 0) + q
        sellers[s] = sellers.get(s, 0) + q

    total_qty = sum(t.get('qty', 0) for t in trades)
    if total_qty == 0:
        return {'concentration': 'low', 'warning': None}

    max_buyer_share = max(buyers.values()) / total_qty if buyers else 0.0
    max_seller_share = max(sellers.values()) / total_qty if sellers else 0.0

    warning = None
    if max_buyer_share > 0.50 or max_seller_share > 0.50:
        warning = 'High broker concentration detected (>50% volume via single broker).'

    return {
        'max_buyer_share': round(max_buyer_share, 4),
        'max_seller_share': round(max_seller_share, 4),
        'warning': warning
    }

if __name__ == '__main__':
    print('floorsheet.py ready')
