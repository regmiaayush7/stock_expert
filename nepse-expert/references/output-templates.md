# Output templates

Plain tone. No hype, no guaranteed returns, no fake precision: round prices to the paisa only where the tools did, otherwise to whole rupees, and quote percentages to one decimal. Every number that came from a fetch carries a source and a date. Write in English; keep Nepali terms (kitta, WACC, book closure) as the user uses them. Dates in AD with Bikram Sambat in brackets where the fetch gave one.

State once per answer, in one line at the end, that this is decision support and not licensed advice, and that the user decides. Do not repeat it per holding.

## 1. Holdings echo (before any analysis)

Show `table_markdown` from `parse_portfolio.py parse`, then ask in one message: "Are these quantities and costs right? Any rows I should drop or add? Purchase dates for [symbols with none]?" Then stop. Do not fetch or analyse until the user says yes or sends corrections.

## 2. Per-holding card

Keep to about 35 lines. Fill every field or write "not available in v0" with the reason.

```
### SYMBOL — Sector — VERDICT   (confidence: low|medium|high · horizon: N months)
Data: price Rs X, last session YYYY-MM-DD, verified by [sources]; fetched YYYY-MM-DD HH:MM NPT (BS ....)

| Kitta | WACC | Last price | Value | Weight | Gross P/L | Net P/L if sold today (after costs and tax) |

Thesis: two sentences.
- Fundamental view: EPS (period), P/E, PBV, dividend and bonus record, governance flags found or "none found in what was searched".
- Technical view (v0, limited): returns 1/3/6/12m on adjusted prices, position in 250-session range. No indicators in v0.
- Valuation vs peers: table of 3-5 peers (P/E, PBV, 12m return), how peers were chosen.
- Liquidity and exit: ADV, days traded in 30 sessions, days to exit at 10% of ADV, circuit risk note.
- Events, next 30/90 days: dated list; rumours marked unverified.

Key levels (adjusted prices): add zone ... · trim zone ... · invalidation ... and the thesis fact that breaks it.
Entry/exit plan: staggered, limit orders, size, review date.

| Scenario | Price at horizon | Probability | Trigger |
| Bull / Base / Bear |

Expected return vs hurdle: hold X% a year (range) vs sell-now Y% a year (hurdle source and date). Margin: Z points → clears / does not clear.
Net of tax if sold today: Rs ..., break-even price Rs ..., [wait comparison: ...].
Score: factor scores and weights (decision-protocol step 9).
Strongest argument against this verdict: ... and why it loses (or wins).
What would change my call: ...
Bias flag: ... (or none)
Logged: yes, probability p, review date D.
```

## 3. "Cannot give a verdict" card

Use when step 1 of the protocol fails. Do not log it. No price view, no soft hint.

```
### SYMBOL — no verdict
What failed: (price not verified by two sources | stale last trade | adjustment unverified | no EPS | rates stale | symbol merged/renamed without history)
What I have: the numbers that were fetched, labelled unverified, with sources and times.
What I need: (a pasted quote | a TMS or NepseAlpha export | confirmation the stock is tradable | the purchase date)
```

## 4. Portfolio summary

Sections in this order:
1. **Totals**: total value, cash, cost, gross P/L, net P/L if everything were sold today, costs-and-tax drag (from `parse_portfolio.py summary`).
2. **Table**: the summary table (weights include cash so they add to 100 percent).
3. **Concentration and liquidity**: top 1 and top 3 weights, sector weights, share of the portfolio that can be sold within 5 days at 10 percent of average daily volume, every ILLIQUID or slow-exit flag.
4. **Biggest risks**, ranked: one line each, with the number behind it.
5. **Prioritised action list**: numbered, what to do first, why, and in what size (percent of portfolio and rupees), with sequencing (what to sell before what to buy, and which orders to stagger). Tie each action to a per-holding verdict. If the honest answer is "no action", say that.
6. **New ideas**: v0 has no screener. Offer only diversification gaps (a sector the portfolio lacks), name at most three symbols, and show for each: the fetched data with date, why it was picked, and "not screened; run the per-holding protocol before acting". Never promote an illiquid or manipulated-looking stock without a warning.
7. **What could make this analysis wrong**: at least three specific items (stale or unverified prices, tax rates that changed, peer set chosen by judgment, no flows or macro data, one-source facts).
8. **Data-quality warnings**: every flag from `summary` and from the fetches, verbatim.
9. The one-line disclaimer.

### v0 portfolio limits (judgment defaults for an aggressive long-term investor with no margin; not tested on NEPSE data)

| Limit | Default | Where it lives |
|---|---|---|
| Single stock | 20 percent of the portfolio | `LIMITS` in `parse_portfolio.py` |
| Single sector | 40 percent | same |
| Cash floor | 5 percent | same |
| Safe share of average daily volume per day | 10 percent | same |
| Slow exit / illiquid | more than 5 / more than 20 days | same |

The user's profile overrides these: pass `"limits"` in the summary input. Move them into `portfolio-and-risk.md` in v1.

## 5. Questions that v0 cannot fully serve

When the request is a market pulse, a screener, an IPO or right-share evaluation, or a news-impact trace, say at the top that v0 has no dedicated module for it, then do what the data rules allow: search the web in Nepali and English, cite and date every fact, give scenarios not a point forecast, cap confidence at medium (low for an IPO or anything with no verified data), and say what the later module would add.
