# Tax and costs

Last verified: 2026-10-24. Numbers live in `data/rates.json` (each with sources and a date) and are applied by `scripts/costs.py`. If this file and `rates.json` ever differ, `rates.json` wins. Never do tax or fee arithmetic by hand.

## Why memory is not enough

Capital gains tax on listed shares for resident individuals changed twice between July and September 2026 (see the `periods` list in `rates.json`): a higher schedule from Shrawan 1, 2083 (17 July 2026), then a Cabinet cut published in the Nepal Gazette on Asoj 5 or 6, 2083 (21 or 22 September 2026). Reports even disagreed on the new numbers (3.5 vs 3.75 percent; the 3.75 figure is in nearly every source and is the one used). Any rate you remember is a hint to check, not a fact.

## How to use

1. Collect kitta, WACC (the figure on the user's screen), price (the verified last price, or the limit price the user is considering) and the purchase date (AD or BS; ask if the screenshot has none).
2. Run `python scripts/costs.py sell --kitta N --wacc W --price P --buy-date D`.
3. Report from its output: gross proceeds, commission, SEBON fee, DP charge, CGT, net proceeds, **net result if sold today**, the **break-even price** after costs and tax, and (when the holding is still short term) the **sell-now-versus-wait** line.
4. Read `rates_verified` first. If `stale` is true, or the question depends on a rule that may have moved (a budget, a Cabinet decision, a SEBON circular), re-verify before answering (below). Say the result is unverified until then.
5. Print the assumptions the output lists. They are part of the answer.

## Rules in force (verify live, see `rates.json` for the numbers)

- **CGT**: resident individual, SEBON-listed shares. Short-term rate if held 365 days or less, long-term if held more than 365 days. Withheld at settlement and treated as final. Institutions pay 10 percent.
- **Broker commission**: slab by trade value, applied to the whole amount (not in bands), Rs 10 minimum, a ceiling set by SEBON that a broker may undercut. **SEBON fee**: 0.015 percent, buy and sell. **DP charge**: Rs 25 per scrip per settlement.
- **Cash dividend**: 5 percent final withholding by the company. **Bonus shares**: not taxed to the holder at issue; they lower the average cost (WACC), which raises the taxable gain on a later sale.
- **IPO, FPO and right shares taken from the issue**: no commission, SEBON fee or DP charge.

## Open points (carry these into the answer, do not hide them)

- The 21-point plan also promised netting profits against losses. One source says it was not in force on 20 October 2026. Until confirmed, assume each profitable sale is taxed on its own and losses on other holdings give no tax relief.
- Trade date or settlement date decides the rate: not stated by the news reports. Near a rate change, say so.
- Cost basis of bonus shares (zero or Rs 100 par) and whether selling costs reduce the taxable gain are not settled by the sources. `costs.py` uses the screen WACC and taxes the gross gain, and prints the lower tax that would apply if costs were deductible.
- One advisory site says annual gains above Rs 40 lakh need a return and tax clearance. Single source.
- With several purchase lots the 365-day test applies per lot. Ask which lots would be sold, or state that the result is a single-lot approximation.

## How to re-verify

Search English and Nepali (for example `capital gains tax shares Nepal 2083`, `पूँजीगत लाभकर सेयर`), prefer Nepal Gazette, IRD, SEBON, CDSC and Ministry of Finance pages, then ShareSansar, Kathmandu Post, myRepublica, Onlinekhabar. Take a figure as verified only when at least two independent sources agree and an official or news-agency source names the date. As of the last check the official sites were unreachable, so every figure rests on secondary sources; `rates.json` says so. After checking, edit `rates.json` (add a period or slab, update `last_verified`) and run `python -m unittest discover -s scripts/tests`; the tests encode the figures and will tell you what moved.

## What to tell the user

- Lead with the net-of-tax number, not the screen P/L. The screen P/L ignores costs and tax.
- Your cost price does not change whether the stock is a good hold from here; tax and what else the cash could earn do. If the user is anchoring on cost ("I will sell when I break even"), name that bias and show the forward-looking comparison instead.
- The tax saving from waiting for the long-term rate is small next to ordinary price moves (about 1.25 percentage points of the gain at the current schedule). Show the price fall that wipes it out; do not let it drive the decision alone.
- Not covered in v0: other income, loss set-off, multi-lot FIFO, dividends received during a wait, transaction costs of buying a replacement.
