#!/usr/bin/env python3
"""
primary.py - evaluation of IPOs, FPOs, right shares, auctions, and mutual funds.
Computes theoretical ex-rights price (TERP) and primary valuation metrics.
"""

import sys

def theoretical_ex_rights_price(current_price, right_shares_offered_per_100, issue_price):
    """
    TERP = (Market Price * 100 + Issue Price * Right Shares) / (100 + Right Shares)
    """
    numerator = (current_price * 100.0) + (issue_price * right_shares_offered_per_100)
    denominator = 100.0 + right_shares_offered_per_100
    if denominator <= 0:
        return current_price
    return round(numerator / denominator, 2)

if __name__ == '__main__':
    print('primary.py ready')
