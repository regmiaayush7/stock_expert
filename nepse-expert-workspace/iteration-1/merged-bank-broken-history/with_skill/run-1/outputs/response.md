**GBIME 5-year return: -14.7% on price (about -3.1% a year), 24 Oct 2021 to 16 Oct 2026, bonus-adjusted. Including cash dividends it is roughly -4% (about -0.9% a year). The 5-year number is solid. Anything before 2020 is not.**

Both figures are gross: before capital gains tax and brokerage, no reinvestment. This is a data answer, not a hold/sell call.

### The numbers
| Basis | Start (24 Oct 2021) | End (16 Oct 2026) | Return |
|---|---|---|---|
| Raw chart, no adjustment | Rs 374.0 | Rs 254.0 | -32.1% (false: ignores 5 bonus issues, 25.6% more shares) |
| Bonus-adjusted price | Rs 297.9 | Rs 254.0 | **-14.7%** |
| Plus cash dividends, net of 5% withholding | | | about -4.3% (unverified, see below) |

The dividend line is my hand calculation. It uses the ShareSansar dividend table (Rs 3.5, 10.6, 8, 0, 8, 6 on the shares held at each book closure). That table is a single source, so the line is unverified. Bonus-share tax is not netted.

The start date matters a lot. Oct 2021 sits near the 2020-22 peak (adjusted high Rs 320.7 on 1 Feb 2022, low Rs 156.8 on 8 May 2024). Six months earlier gives -25.5%, six months later -6.4%, and three years gives +34.8%. Don't read "-14.7%" as the stock's character.

### Can you trust the data?
- **Last price Rs 254.0, session 16 Oct 2026**: Merolagani, NepseAlpha and ShareSansar all agree. Fetched 24 Oct 2026 22:34 NPT (BS 2083-07-07). There were no sessions after 16 Oct. The tool labels that "market quiet or closed", not a dead stock.
- **The 5-year window checks out.** My bonus-adjusted series, Merolagani's adjusted series and NepseAlpha's adjusted series all give -14.7%. They match bar by bar within 0.4% across 1,014 sessions.
- **No bonus issue is missing recently.** 357,710,597 shares after the 2023 merger x 1% x 5.5% x 4% bonus = 396.4 million. Merolagani lists 396,404,869.
- **Pre-2020 is unverified.** Merolagani's adjusted series sits 3.6% to 6.6% below the other two there. I can't tell which is right, so ignore pre-2020 levels. The tool flags the whole series `unverified` for this reason. A rough bonus-adjusted figure from the last bar before the 2019 halt (4 Jul 2019) is +39% over 7.3 years, but treat it as unverified.
- **Not official data.** nepalstock.com's API refused an unauthenticated call (401), so everything comes from aggregators.

### Why the chart looks weird: two mergers, not one
GBIME is the surviving bank in both and kept its ticker. Its holders just kept their shares, so the price series is valid. But each merger left a hole in the trading record:

| No bars | Cause |
|---|---|
| 5 Jul 2019 to 19 Jan 2020 (200 days) | Janata Bank Nepal merger, swap 100:85. Trading halted Asadh 22 2076; last trade Rs 295 on 4 Jul 2019. Resumed 20 Jan 2020 with an open range of Rs 252.47 ([ShareSansar](https://www.sharesansar.com/newsdetail/trading-in-stocks-of-global-ime-bank-resumes-from-tomorrow-after-a-successful-merger-with-janata-bank-open-price-range-is-set-at-rs-25247)) |
| 16 Jun 2022 to 6 Dec 2022 (175 days) | Bank of Kathmandu merger. GBIME and BOKL transactions suspended 16 Jun 2022 ([ShareSansar notice](https://www.sharesansar.com/eventdetail/transactions-suspended-of-global-ime-bank-limited-gbime-bank-of-kathmandu-limited-bokl-2022-06-16)). I could not read a stated resumption date; all three sources show bars again from 7 Dec 2022 |
| 9 Jan to 21 Feb 2023 | Final integration from Poush 25 2079 (9 Jan 2023), 15-day halt under SEBON rules ([ShareSansar](https://www.sharesansar.com/newsdetail/due-to-final-merger-procedure-with-bank-of-kathmandu-share-trading-of-global-ime-bank-limited-to-be-halted-for-15-days-from-poush-25-2023-01-06)). Swap 1:1, 112,614,336 extra shares listed ([ShareSansar](https://www.sharesansar.com/newsdetail/after-merging-with-bokl-1126-crore-units-additional-shares-of-global-ime-bank-listed-in-nepse-for-trading-2023-02-20)). Bars resume 22 Feb 2023 |

All three price sources show the same gaps, so these are real halts, not missing data. (There are also Mar-Jun 2020 gaps, probably the COVID lockdown. I did not verify that.)

What you see on the chart:
- **Straight lines across months of no trading.** The Nov 2019 and Nov 2022 bonus and dividend dates fall inside the halts, so each lands as one big move on the first bar back. Raw: -6.1% on 20 Jan 2020 and -11.9% on 7 Dec 2022. Adjusted: +5.9% and -9.3%. Those bars hold months of price change plus the Rs 12.75 and Rs 10.6 cash dividends, which the adjustment does not remove. They are not crashes.
- **A thin first print.** 20 Jan 2020 traded only 929 shares, range Rs 245 to 277, so the candle spikes.
- **Yearly 10-16% bonus issues before 2020** make an unadjusted chart show a 10-13% "crash" every winter.
- **Your chart reaches back further than 5 years.** A true 5-year window starts in Oct 2021. If you see 2019, it is a 7-year or "max" view. The Bank of Kathmandu gap (2022-23) is the one inside your 5 years.

The company under the chart changed too. Shares outstanding went from roughly 118 million to 190 million (Janata) to 358 million (BOKL), per ShareSansar's figures, and the first two are partly model-derived. Pre-2020 EPS, book value per share and market cap are not comparable with today. The merged banks' own old histories are not in this chart either. `symbol_map.csv` has no verified rows, so nothing is chained.

### Not checked
Why Merolagani differs pre-2020. The exact 2022 resumption date. Any sector KPIs (NPL, NIM). Whether the Rs 254 level is cheap or dear: that needs the full protocol (peers, hurdle rate, scenarios). If you hold GBIME, send kitta, WACC and purchase date and I'll run net-of-tax and give a proper call.

Decision support, not licensed advice. You make the decision.
