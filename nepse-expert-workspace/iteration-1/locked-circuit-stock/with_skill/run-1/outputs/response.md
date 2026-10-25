## Circuit limit

As of 2026-10-24 (verify on TMS): **15 percent a day, up or down**, for a single stock. It was 10 percent until 2026-04-20. Sources: [ShareSansar 2026-04-20](https://www.sharesansar.com/newsdetail/nepse-new-rules-alert-stock-limits-upgraded-to-15-starting-today-market-to-suspend-at-8-index-change-2026-04-20) and [ShareSansar 2026-04-12](https://www.sharesansar.com/newsdetail/nepse-introduces-key-trading-reforms-to-enhance-market-efficiency-2026-04-12). I searched for a later change and found none. Many guides still print 10 percent: they are out of date.

The sources do not say what the 15 percent is measured from. Previous close is the usual reading, so floor = previous close x 0.85. Do not rely on my arithmetic: TMS shows the exact lower-circuit price for today.

Three floor days in a row at 15 percent each means the price is at 0.85 x 0.85 x 0.85 = 0.614 of where it started: down 38.6 percent. A fourth day takes it to 0.522. That is why a lock on the old 10 percent rule was bad and a lock now is worse.

## How to get out

You cannot sell below the floor. The floor is the lowest price the exchange accepts, so you cannot cut your price to find a buyer. Your levers are timing and queue position.

1. Put a sell order at today's floor price, before 11:00 NPT, and leave it. A pre-open order (10:30 to 10:45, no execution) joins the book. Sell only as many kitta as you decide to sell, not more.
2. Do not cancel and re-enter during the day. In most order books a new order goes to the back of the queue. I did not verify NEPSE's matching rule this session: ask your broker whether it is price-time priority.
3. Expect partial fills. With no buyers, a few kitta may trade on one day and the rest the next. Check the order status each day.
4. Do not average down to "fix" a WACC of 180. Do not follow tips or Telegram offers to "buy your locked shares" outside the exchange. I did not verify off-market transfer rules; ask your DP or CDSC before agreeing to anything off the exchange.
5. Find out why it is locked. Company news (loss, plant damage, audit issue, PPA problem, weak Q1 result)? Or only this stock, with other hydros fine? Check the hydropower index and a few peer hydros today. Context only, not the cause for your stock: on 2026-08-26 hydro stocks fell on Rasuwa flood damage news ([ShareSansar](https://www.sharesansar.com/newsdetail/nepse-sheds-3592-points-as-flood-damage-raises-uncertainty-in-hydropower-sector-2026-08-26)). I found no October 2026 report of a sector-wide hydro lock.

## What a sale costs you (Rs, 5000 kitta, WACC 180, cost Rs 900,000)

The price is unknown to me, so these prices are examples, not the market. From `costs.py`, rates verified 2026-10-24 from secondary sources only.

| Sale price | Gross | Costs (commission, SEBON, DP) | Capital gains tax | Net proceeds | Net result |
|---|---|---|---|---|---|
| 150 | 750,000 | 2,462.5 | 0 | 747,537.5 | -152,462.5 (-16.9%) |
| 120 | 600,000 | 1,975 | 0 | 598,025 | -301,975 (-33.6%) |
| 90 | 450,000 | 1,577.5 | 0 | 448,422.5 | -451,577.5 (-50.2%) |

- Selling below WACC means no capital gains tax. Costs are about 0.4 percent. The price is the real cost, not tax or fees.
- Break-even is Rs 180.7. A realised loss gives no tax relief as far as I can confirm: loss set-off was promised but one source says it was not in force on 2026-10-20.
- Purchase date was not given, so the tool assumed the short-term rate. It does not matter below Rs 180. It would matter above.

## No verdict on this stock yet

### Ticker not given: no verdict
What failed: I have no symbol, so no price was fetched or verified by two sources. If there were no trades in 3 days, the "last price" on screen may be 3 days old and the real bid may be lower.
What I have: the rule, the mechanics and the cost table above. Nothing about the company.
What I need:
1. The ticker.
2. Last traded price and today's lower-circuit price from TMS. And whether any kitta traded in the last 3 days (volume).
3. Purchase date.
4. Is this money you may need within a year, and what share of your portfolio is it? Your profile has no risk capacity or goals on file.

Then I can run the live data, liquidity and days-to-exit check, peers, and give hold versus sell with scenarios and the case against.

## One question to ask yourself

WACC 180 is gone: the market does not know or care. The forward question is: at today's floor price, with this cash in hand, would I buy this stock? If no, the sell order is the answer, and each locked day without it costs you. If yes, you do not need to sell. Either way, do not wait for "back to 180" (anchoring on cost).

Decision support, not licensed advice. You decide. I cannot place trades and you should never share a TMS or MeroShare password or OTP.

Not checked: NEPSE queue rule, off-market transfer rules, the stock itself (no ticker). Risk: the 15 percent rule and the tax rates rest on news sources, not on the official circular.
