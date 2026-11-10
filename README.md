# NEPSE Expert Investor (`nepse-expert`)

Decision-support skill for the Nepal Stock Exchange (NEPSE), for Claude Code and Claude Desktop. It reads a portfolio, fetches live data and gives a verdict with scenarios. It never places trades or takes credentials.

**Status (10 Nov 2026): only version 0 is built.** The scripts and reference files added for versions 1 to 3 are stubs, and `SKILL.md` does not use them.

## What works (version 0)

- **Portfolio parser** (`parse_portfolio.py`): checks the rows Claude reads from a MeroShare, TMS or broker screenshot, strips identifiers, echoes the holdings for confirmation, builds the portfolio summary and writes the decision log.
- **Live data and caching** (`fetch_data.py`): price, volume, EPS, dividends and book closure, with source cross-checks, timestamps and a cache fallback.
- **Corporate-action price adjustment** (`adjust_prices.py`): adjusts price history for bonus and right shares, and cash dividends on request, so a book closure does not look like a crash.
- **Tax and cost engine** (`costs.py`): capital gains tax by holding period, broker commission, SEBON fee, DP charge and the net-of-tax break-even price, from `data/rates.json`.

## Not built yet (stub files)

| File | What is there | What is missing |
|---|---|---|
| `indicators.py` | SMA, EMA, RSI, MACD, ATR, OBV and relative strength functions | A command line, input from `adjust_prices.py`, tests beyond SMA, RSI and OBV |
| `screen.py` | Weighted sum of scores passed in by the caller | Any data fetch; a stock with no data gets an average score |
| `backtest.py` | Cost of single trades with a hardcoded 0.3 percent commission | Price history, positions, `data/rates.json`, results |
| `calibrate.py` | Count of logged verdicts | Hit rate and Brier score (returned as `None`) |
| `floorsheet.py` | Largest single-broker share of volume | Floorsheet fetch, circular-trading checks |
| `primary.py` | Theoretical ex-rights price | IPO, FPO, auction and mutual fund analysis |
| `forecast.py`, `ensemble.py` | Naive and momentum forecasts, their mean and range | A backtest that shows they beat a naive baseline after costs |

Six reference files (`fundamental-analysis-by-sector.md`, `technical-analysis.md`, `macro-and-liquidity.md`, `news-and-event-calendar.md`, `valuation-and-cost-of-capital.md`, `accounting-and-governance.md`) are short lists of metrics with no thresholds or worked examples yet.

## Repository structure

```
nepse-expert/                   # the skill
  SKILL.md                      # version 0 rules and workflow router
  references/                   # 5 version 0 files and the 6 stubs above
  scripts/                      # 4 version 0 scripts and the 8 stubs above
    tests/                      # 97 unit tests, 84 of them on version 0
  data/                         # rates.json (tax and cost rates), symbol_map.csv
  evals/                        # 17 eval cases and decision_log.csv
  user_profile.md               # investor risk profile and horizon
nepse-expert-workspace/         # version 0 snapshot and the iteration-1 eval runs (not graded yet)
tasks/                          # plan.md and todo.md
NEPSE_SKILL_BUILD_PROMPT.md     # the build spec
```

## Installation and usage

1. Copy the `nepse-expert/` folder into your skills directory (for example `C:\Users\YourUser\.claude\skills\nepse-expert`). Edit the skill here, then copy it again, so the two stay the same.
2. In Claude, invoke `/nepse-expert`, or attach a portfolio screenshot and ask:
   > *"Analyze my portfolio screenshot and tell me what to hold, add, trim or exit."*
   > *"Run a deep dive on NABIL."*
   > *"What is the tax on selling shares held for 400 days?"*
3. Run the tests from `nepse-expert/`: `python -m unittest discover -s scripts/tests`.
