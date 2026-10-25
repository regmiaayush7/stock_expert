# NEPSE Expert Investor (`nepse-expert`)

Senior disciplined investor and analyst skill for the Nepal Stock Exchange (NEPSE). Designed for Claude Code and Claude Desktop.

## Features

- **Portfolio Screenshot Parser**: Reads MeroShare, TMS, and broker screenshots, echoes holdings for confirmation, and prevents hallucinated numbers.
- **Live Data & Caching**: Pulls price, volume, financials, dividends, and corporate actions with offline fallbacks and source cross-checking (`fetch_data.py`).
- **Corporate Action Price Adjustment**: Automatically adjusts historical prices for bonus shares, right shares, and cash dividends to prevent false crashes/breakouts (`adjust_prices.py`).
- **Technical Indicators**: RSI, MACD, Moving Averages, ATR, OBV, and Relative Strength tuned for NEPSE's 10% daily price band (`indicators.py`).
- **Tax & Cost Engine**: Computes capital gains tax by holding period (short vs. long term), broker commissions, SEBON fee, DP charge, and net-of-tax break-even prices (`costs.py`).
- **Sector Playbooks & Valuation**: Deep fundamental playbooks for Commercial Banks, Hydropower, Insurance, Microfinance, and Mutual Funds, plus DCF, DDM, and PBV-ROE valuation models.
- **Idea Screener & Backtesting**: Ranked scorecard screener (`screen.py`), rule backtester with market frictions (`backtest.py`), calibration scoring (`calibrate.py`), floorsheet/broker concentration analysis (`floorsheet.py`), primary market TERP calculator (`primary.py`), and forecasting/ensemble modules (`forecast.py`, `ensemble.py`).

## Repository Structure

```
nepse-expert/
  SKILL.md                      # Trigger description + workflow router
  references/                   # Sector playbooks, tax rules, decision protocol
    market-structure-and-rules.md
    fundamental-analysis-by-sector.md
    technical-analysis.md
    quant-and-forecasting.md
    macro-and-liquidity.md
    news-and-event-calendar.md
    portfolio-and-risk.md
    tax-and-costs.md
    behaviour-and-manipulation.md
    data-sources.md
    output-templates.md
    decision-protocol.md
    valuation-and-cost-of-capital.md
    accounting-and-governance.md
  scripts/                      # Python stdlib + requests modules
    parse_portfolio.py
    fetch_data.py
    adjust_prices.py
    indicators.py
    costs.py
    screen.py
    backtest.py
    calibrate.py
    floorsheet.py
    primary.py
    forecast.py
    ensemble.py
    tests/                      # 97 unit tests
  data/                         # symbol maps, rate tables, cache
  user_profile.md               # investor risk profile and horizon
  evals/                        # test cases and decision logs
```

## Installation & Usage

1. **Install in Claude Code / Claude Skills**:
   Copy the `nepse-expert/` folder into your `.claude/skills/` directory (e.g. `C:\Users\YourUser\.claude\skills\nepse-expert`).
2. **Usage**:
   In Claude, invoke `/nepse-expert` or attach a portfolio screenshot and ask:
   > *"Analyze my portfolio screenshot and tell me what to hold, add, trim or exit."*
   > *"Run a deep dive on NABIL."*
   > *"What is the tax on selling shares held for 400 days?"*
