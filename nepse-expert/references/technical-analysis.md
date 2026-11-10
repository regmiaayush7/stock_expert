# Technical Analysis on Adjusted Prices (`technical-analysis.md`)

## Core Rule
**Always adjust price history for bonus, right shares, and cash dividends before computing any indicator.** Unadjusted NEPSE charts create false crashes and false breakouts.

## Indicator Customisation for NEPSE (Daily Price Limit)
The limit is 15 percent since 2026-04-20 and was 10 percent before (`market-structure-and-rules.md`; verify live). Volatility, ATR and stop distances from before that date come from the 10 percent regime: do not pool the two periods without saying so.
- **RSI (14)**: Measures momentum. Under a daily price limit, extreme momentum can sustain longer; overbought (>70) and oversold (<30) thresholds should be confirmed by volume and breadth.
- **MACD (12, 26, 9)**: Trend-following momentum. Crossovers are filtered through volume expansion.
- **Moving Averages (SMA/EMA 20, 50, 200)**: Primary trend filters. 50-day and 200-day MAs define medium and long-term regimes.
- **ATR (14)**: Average True Range measures volatility, essential for stop-loss placement given the daily price limit.
- **OBV (On-Balance Volume)**: Accumulation/distribution confirmation via volume flow.
- **Relative Strength**: Stock performance relative to the NEPSE Index or its specific sector index.
