#!/usr/bin/env python3
"""Sale costs, capital gains tax, net result, break-even and sell-now-vs-wait for one NEPSE holding.
Stdlib only. Money uses Decimal, rounded half-up to paisa. Rates live in data/rates.json (each with sources and a
verification date); none are hard-coded here.

  costs.py sell --kitta 100 --wacc 500 --price 547 [--buy-date 2025-01-14|BS date] [--sell-date YYYY-MM-DD]
  costs.py rates

Assumptions the output repeats every time:
  * WACC is the user's all-in cost per share as shown by MeroShare, so buy-side charges are not added again.
  * Taxable gain = gross proceeds - WACC x kitta. Selling costs are NOT deducted (sources do not say they are), which
    can only overstate tax; `tax_if_sale_costs_deductible` shows the other bound.
  * Commission is the full slab rate (a ceiling; a broker may charge less). DP charge is counted once, on the sale.
  * One purchase lot. With several lots the 365-day test applies per lot: ask which lots are sold.
Exit 0 ok, 1 rates older than max_age_days (result is unverified), 2 bad input.
"""
import argparse, datetime as dt, json, sys
from decimal import ROUND_HALF_UP, Decimal as D
from pathlib import Path

from parse_portfolio import to_ad

RATES = Path(__file__).resolve().parent.parent / "data" / "rates.json"
NPT = dt.timezone(dt.timedelta(hours=5, minutes=45))
PAISA = D("0.01")


def q(x):
    return D(x).quantize(PAISA, rounding=ROUND_HALF_UP)


def load_rates(path=RATES):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rate_period(rates, sell_date):
    periods = rates["cgt_resident_individual_listed_securities"]["periods"]
    return max((p for p in periods if p["from"] <= sell_date.isoformat()), key=lambda p: p["from"])


def commission(value, rates):
    c = rates["broker_commission"]
    pct = next(s["pct"] for s in c["slabs"] if s["up_to"] is None or value <= s["up_to"])
    return max(q(value * D(str(pct)) / 100), D(c["minimum_npr"]))


def sale_costs(value, rates):
    return {"commission": commission(value, rates),
            "sebon_fee": q(value * D(str(rates["sebon_fee_pct"]["value"])) / 100),
            "dp_charge": D(rates["dp_charge_npr"]["value"])}


def net_sale(kitta, wacc, price, tax_pct, rates):
    value = q(D(kitta) * D(str(price)))
    cost = q(D(kitta) * D(str(wacc)))
    fees = sale_costs(value, rates)
    fee_total = sum(fees.values())
    gain = max(value - cost, D(0))
    tax = q(gain * D(str(tax_pct)) / 100)
    net = value - fee_total - tax
    return {"gross_proceeds": value, **fees, "cost_basis": cost, "taxable_gain": gain, "cgt": tax,
            "tax_if_sale_costs_deductible": q(max(gain - fee_total, D(0)) * D(str(tax_pct)) / 100),
            "net_proceeds": net, "net_pl": net - cost}


def first_tick(ok, lo, hi, tick):
    """Smallest price on the tick grid in [lo, hi] with ok(price) true; ok must be monotone (false then true)."""
    a, b = int(lo / tick), int(hi / tick) + 1
    if not ok(b * tick):
        return None
    while a < b:
        m = (a + b) // 2
        a, b = (a, m) if ok(m * tick) else (m + 1, b)
    return a * tick


def analyse(kitta, wacc, price, sell_date, buy_date=None, rates=None, today=None):
    rates = rates or load_rates()
    today = today or dt.datetime.now(NPT).date()
    tick = D(str(rates["price_tick_npr"]["value"]))
    price, wacc = D(str(price)), D(str(wacc))
    period = rate_period(rates, sell_date)
    days = (sell_date - buy_date).days if buy_date else None
    if days is None:
        tax_pct, term = period["short_pct"], "unknown: purchase date missing, short-term (higher) rate assumed"
    else:
        long_term = days > 365
        tax_pct, term = (period["long_pct"], "long") if long_term else (period["short_pct"], "short")
    res = net_sale(kitta, wacc, price, tax_pct, rates)
    be = first_tick(lambda p: net_sale(kitta, wacc, p, tax_pct, rates)["net_pl"] >= 0, wacc / 2, wacc * 3, tick)
    out = {"inputs": {"kitta": kitta, "wacc": float(wacc), "price": float(price), "sell_date": sell_date.isoformat(),
                      "buy_date": buy_date.isoformat() if buy_date else None, "days_held": days},
           "cgt_rate_pct": tax_pct, "term": term, "rate_period_from": period["from"],
           **{k: float(v) for k, v in res.items()},
           "net_pl_pct_of_cost": float(q(res["net_pl"] / res["cost_basis"] * 100)),
           "break_even_price_net_of_costs_and_tax": float(be) if be else None}
    if days is not None and days <= 365:
        long_from = buy_date + dt.timedelta(days=366)
        target = res["net_proceeds"]
        floor = first_tick(lambda p: net_sale(kitta, wacc, p, period["long_pct"], rates)["net_proceeds"] >= target,
                           price / 4, price, tick) if res["taxable_gain"] > 0 else None
        out["wait_comparison"] = {
            "long_term_from": long_from.isoformat(), "days_to_wait": (long_from - sell_date).days,
            "tax_saving_if_price_unchanged": float(res["cgt"] - net_sale(kitta, wacc, price, period["long_pct"], rates)["cgt"]),
            "waiting_beats_selling_now_if_price_on_that_date_is_at_least": float(floor) if floor else None,
            "max_fall_pct_to_still_break_even": float(q((price - floor) / price * 100)) if floor else None,
            "caveat": "Assumes today's long-term rate still applies then (it changed twice between July and September 2026) and ignores dividends, "
                      "book closures and the return you could earn on the cash meanwhile; weigh those against the hurdle rate."}
    age = (today - dt.date.fromisoformat(rates["last_verified"])).days
    stale = age > rates["max_age_days"]
    out["rates_verified"] = {"date": rates["last_verified"], "age_days": age, "stale": stale,
                             "status": rates["verification_status"]}
    out["assumptions"] = ["WACC is the all-in cost per share from the screen", "selling costs not deducted from the taxable gain "
                          "(see tax_if_sale_costs_deductible)", "commission at full slab rate (a ceiling)", "DP charge once, on the sale",
                          "single purchase lot", "price tick from rates.json (unverified)"]
    out["status"] = "unverified" if stale else "ok"
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sell")
    s.add_argument("--kitta", type=int, required=True)
    s.add_argument("--wacc", type=float, required=True)
    s.add_argument("--price", type=float, required=True)
    s.add_argument("--buy-date")
    s.add_argument("--sell-date")
    sub.add_parser("rates")
    a = ap.parse_args(argv)
    try:
        rates = load_rates()
        if a.cmd == "rates":
            print(json.dumps(rates, indent=2, ensure_ascii=False))
            return 0
        if a.kitta <= 0 or a.wacc <= 0 or a.price <= 0:
            raise ValueError("kitta, wacc and price must be above zero")
        sell = dt.date.fromisoformat(to_ad(a.sell_date)[0]) if a.sell_date else dt.datetime.now(NPT).date()
        buy = None
        if a.buy_date:
            iso, problem = to_ad(a.buy_date)
            if problem:
                raise ValueError(problem)
            buy = dt.date.fromisoformat(iso)
            if buy > sell:
                raise ValueError("buy date is after sell date")
        out = analyse(a.kitta, a.wacc, a.price, sell, buy, rates)
    except (ValueError, OSError, TypeError) as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        return 2
    print(json.dumps(out, indent=2))
    return 0 if out["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
