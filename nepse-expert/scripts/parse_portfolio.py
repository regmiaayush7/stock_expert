#!/usr/bin/env python3
"""Holdings handling for the nepse-expert skill. Stdlib only.

  parse_portfolio.py parse ROWS.json|-      validate rows read from a screenshot; echo-ready table; list what is unreadable
  parse_portfolio.py summary HOLDINGS.json|-  portfolio totals, weights, concentration, days to exit, net-of-tax result
  parse_portfolio.py log --symbol ... --verdict ...   append one verdict to the decision log

parse input (null = unreadable on the image; never guess a value):
  {"source_app": "MeroShare|TMS|broker app|sheet|unknown",
   "rows": [{"symbol": "NABIL", "kitta": 100, "wacc": 600.0, "ltp": 547.0, "pl": -5300.0,
             "value": 54700.0, "purchase_date": "2025-01-14", "note": "free text"}]}
Only those keys are kept. Long digit strings (account, BOID, phone), emails and any other field are dropped,
so no personal identifier reaches the table, the log or memory.

summary input, after the user confirmed the table and live prices were fetched:
  {"cash": 20000, "limits": {optional overrides of LIMITS},
   "holdings": [{"symbol": "NABIL", "sector": "Commercial Banks", "kitta": 100, "wacc": 400, "ltp": 500,
                 "ltp_source": "verified|screen", "adv_shares": 1000, "purchase_date": "2025-01-14"}]}

The decision log is evals/decision_log.csv, or the file named by the NEPSE_DECISION_LOG environment variable
(set it for tests and evals so they never touch the real log).
Exit 0 all clean, 1 some rows need the user, 2 input unusable or rejected.
"""
import argparse, csv, datetime as dt, difflib, json, os, re, sys
from pathlib import Path

# v0 defaults for an aggressive long-term investor with no margin. Judgment calls, not tested on NEPSE data: tune in v1.
LIMITS = {"single_stock_max_pct": 20.0, "sector_max_pct": 40.0, "cash_min_pct": 5.0,
          "max_share_of_adv": 0.10,   # sell at most 10 percent of a stock's average daily volume per day
          "exit_days_warn": 5, "exit_days_severe": 20, "liquid_within_days": 5}
LOG_FIELDS = ("date_ad", "symbol", "verdict", "confidence", "horizon", "review_date", "resolution_rule",
              "probability", "reference_price", "data_timestamp", "data_status", "outcome")
VERDICTS = ("Accumulate", "Hold", "Trim", "Exit", "Avoid", "Watch")
KEEP = ("symbol", "kitta", "wacc", "ltp", "pl", "value", "purchase_date", "note")
NEEDED = ("symbol", "kitta", "wacc")  # without these no cost, weight or P/L can be stated
ID_PATTERNS = (re.compile(r"\d{8,}"), re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), re.compile(r"\+?\d[\d\s-]{8,}\d"))


def scrub(value):
    """Return (clean_value, n_removed) with identifier-like text replaced."""
    if not isinstance(value, str):
        return value, 0
    n = 0
    for p in ID_PATTERNS:
        value, k = p.subn("[removed]", value)
        n += k
    return value, n


def number(x):
    """float or None. Accepts 1,234.50 and '1234'; rejects letters (an O read as a zero is unreadable, not 100)."""
    if isinstance(x, bool) or x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).replace(",", "").replace("Rs.", "").replace("Rs", "").strip())
    except ValueError:
        return None


def to_ad(s):
    """ISO date text to an AD ISO date. A year of 2060 or more is Bikram Sambat and is converted. Returns (date, problem)."""
    m = re.fullmatch(r"\s*(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\s*", str(s))
    if not m:
        return None, f"purchase date '{s}' is not YYYY-MM-DD"
    y, mo, d = map(int, m.groups())
    try:
        if y >= 2060:  # BS: the earliest NEPSE history is about 2000 AD = 2057 BS, and AD 2060 is far in the future
            import nepali_datetime
            return nepali_datetime.date(y, mo, d).to_datetime_date().isoformat(), None
        return dt.date(y, mo, d).isoformat(), None
    except ImportError:
        return None, f"purchase date {s} looks like Bikram Sambat and the nepali_datetime package is missing: ask for the AD date"
    except ValueError:
        return None, f"purchase date '{s}' is not a real date"


def check_row(i, raw, known):
    row, flags, unreadable, removed = {}, [], [], 0
    for k in KEEP:
        v, n = scrub(raw.get(k)) if k in ("symbol", "note") else (raw.get(k), 0)  # numbers and dates are not free text
        removed += n
        row[k] = v
    sym = (row["symbol"] or "").strip().upper() if isinstance(row["symbol"], str) else None
    row["symbol"] = sym or None
    if not sym:
        unreadable.append("symbol")
    elif known is not None and sym not in known:
        near = difflib.get_close_matches(sym, known, n=3, cutoff=0.6)
        flags.append(f"symbol {sym} not on the exchange list" + (f"; did you mean {', '.join(near)}?" if near else ""))
    for k in ("kitta", "wacc", "ltp", "pl", "value"):
        raw_v, row[k] = row[k], number(row[k])
        if row[k] is None:
            if raw_v is not None:
                flags.append(f"{k} '{raw_v}' is not a number")
            if k in NEEDED or raw_v is not None:
                unreadable.append(k)
    k = row["kitta"]
    if k is not None and (k <= 0 or k != int(k)):
        flags.append(f"kitta {k} is not a positive whole number")
        row["kitta"] = None
        unreadable.append("kitta")
    elif k is not None:
        row["kitta"] = int(k)
    for f in ("wacc", "ltp"):
        if row[f] is not None and row[f] <= 0:
            flags.append(f"{f} {row[f]} must be above zero")
            row[f], unreadable = None, unreadable + [f]
    if None not in (row["kitta"], row["wacc"], row["ltp"], row["pl"]):
        calc = (row["ltp"] - row["wacc"]) * row["kitta"]
        tol = max(1.0, 0.005 * row["wacc"] * row["kitta"])
        if abs(calc - row["pl"]) > tol:
            flags.append(f"P/L on screen {row['pl']:,.2f} differs from (LTP - WACC) x kitta = {calc:,.2f}: a number was misread, or the app's P/L is after costs or tax")
    if None not in (row["kitta"], row["ltp"], row["value"]) and abs(row["kitta"] * row["ltp"] - row["value"]) > max(1.0, 0.002 * row["value"]):
        flags.append(f"value on screen {row['value']:,.2f} differs from kitta x LTP = {row['kitta'] * row['ltp']:,.2f}")
    if row["purchase_date"] is None:
        flags.append("no purchase date: needed for the 365-day tax comparison, ask")
    else:
        row["purchase_date"], msg = to_ad(row["purchase_date"])
        if msg:
            flags.append(msg)
            unreadable.append("purchase_date")
    if removed:
        flags.append(f"{removed} identifier-like text item(s) removed")
    needs_user = bool(unreadable) or any(not f.startswith(("no purchase date", f"{removed} identifier")) for f in flags)
    return {"n": i, **row, "unreadable": sorted(set(unreadable)), "flags": flags, "needs_user": needs_user}


def parse(doc, known=None):
    rows = doc.get("rows") if isinstance(doc, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError('input needs {"rows": [ ... ]} with at least one row')
    out = [check_row(i, r, known) for i, r in enumerate(rows, 1) if isinstance(r, dict)]
    syms = [r["symbol"] for r in out if r["symbol"]]
    for s in {s for s in syms if syms.count(s) > 1}:
        for r in out:
            if r["symbol"] == s:
                r["flags"].append(f"{s} appears {syms.count(s)} times: two lots, two accounts or a double read? Not merged")
                r["needs_user"] = True
    ready = [r for r in out if not r["unreadable"] and all(r[k] is not None for k in NEEDED)]
    return {"source_app": scrub(doc.get("source_app", "unknown"))[0], "rows": out,
            "totals_ready_rows": {"count": len(ready), "cost": round(sum(r["kitta"] * r["wacc"] for r in ready), 2),
                                  "value_at_screen_ltp": round(sum(r["kitta"] * r["ltp"] for r in ready if r["ltp"]), 2),
                                  "note": "screen prices may be stale; live prices are fetched after you confirm"},
            "symbol_list_checked": known is not None, "confirmed": False,
            "next": "Show table_markdown to the user and wait for an explicit yes or corrections. Do not analyse before that."}


def table_markdown(rep):
    fmt = lambda v, d=2: "?" if v is None else f"{v:,.{d}f}"
    lines = ["| # | Symbol | Kitta | WACC (Rs) | LTP on screen (Rs) | P/L on screen (Rs) | Needs you |", "|---|---|---|---|---|---|---|"]
    for r in rep["rows"]:
        need = "; ".join(([f"unreadable: {', '.join(r['unreadable'])}"] if r["unreadable"] else []) + r["flags"]) if r["needs_user"] else ""
        lines.append(f"| {r['n']} | {r['symbol'] or '?'} | {fmt(r['kitta'], 0)} | {fmt(r['wacc'])} | {fmt(r['ltp'])} | {fmt(r['pl'])} | {need} |")
    return "\n".join(lines)


def summarise(doc, today=None):
    """Totals, weights, concentration, liquidity and net-of-cost-and-tax result for confirmed holdings with live prices."""
    import costs  # lazy: costs imports this module for to_ad
    today = today or dt.datetime.now(costs.NPT).date()
    rates = costs.load_rates()
    lim = {**LIMITS, **(doc.get("limits") or {})}
    hs = doc.get("holdings")
    if not isinstance(hs, list) or not hs:
        raise ValueError('input needs {"holdings": [ ... ]} with at least one holding')
    cash = number(doc.get("cash")) or 0.0
    rows, warns = [], []
    for h in hs:
        sym = str(h.get("symbol") or "").strip().upper()
        k, w, p = number(h.get("kitta")), number(h.get("wacc")), number(h.get("ltp"))
        if not sym or None in (k, w, p) or min(k, w, p) <= 0 or k != int(k):
            raise ValueError(f"holding {sym or '?'}: symbol, whole kitta, wacc and ltp must be present and above zero (run parse and get the user's confirmation first)")
        adv = number(h.get("adv_shares"))
        buy = None
        if h.get("purchase_date"):
            iso, problem = to_ad(h["purchase_date"])
            buy = dt.date.fromisoformat(iso) if not problem else None
        res = costs.analyse(int(k), w, p, today, buy, rates, today=today)
        flags = []
        if h.get("ltp_source") != "verified":
            flags.append("price not verified live: do not give a verdict on this holding")
        if buy is None:
            flags.append("no usable purchase date: short-term tax rate assumed")
        days = k / (lim["max_share_of_adv"] * adv) if adv and adv > 0 else None
        if days is None:
            flags.append("no volume data: days to exit unknown")
        elif days > lim["exit_days_severe"]:
            flags.append(f"ILLIQUID: about {days:.0f} days to exit at {lim['max_share_of_adv']:.0%} of average daily volume")
        elif days > lim["exit_days_warn"]:
            flags.append(f"slow exit: about {days:.0f} days at {lim['max_share_of_adv']:.0%} of average daily volume")
        rows.append({"symbol": sym, "sector": h.get("sector") or "Unknown", "kitta": int(k), "wacc": w, "ltp": p,
                     "ltp_source": h.get("ltp_source") or "screen", "value": k * p, "cost": k * w, "gross_pl": k * (p - w),
                     "net_pl": res["net_pl"], "net_proceeds": res["net_proceeds"], "term": res["term"], "days_to_exit": days,
                     "exitable_per_day": lim["max_share_of_adv"] * (adv or 0) * p, "flags": flags})
    invested = sum(r["value"] for r in rows)
    total = invested + cash
    for r in rows:
        r["weight_pct"] = r["value"] / total * 100
        if r["weight_pct"] > lim["single_stock_max_pct"]:
            r["flags"].append(f"concentration: {r['weight_pct']:.1f}% of the portfolio (limit {lim['single_stock_max_pct']:.0f}%)")
    sectors = {}
    for r in rows:
        sectors[r["sector"]] = sectors.get(r["sector"], 0.0) + r["value"] / total * 100
    for name, wt in sectors.items():
        if wt > lim["sector_max_pct"]:
            warns.append(f"sector concentration: {name} is {wt:.1f}% of the portfolio (limit {lim['sector_max_pct']:.0f}%)")
    cash_pct = cash / total * 100
    if cash_pct < lim["cash_min_pct"]:
        warns.append(f"cash is {cash_pct:.1f}% of the portfolio (floor {lim['cash_min_pct']:.0f}%): no room to buy or to meet an emergency without selling")
    n = lim["liquid_within_days"]
    liquid = sum(min(r["value"], n * r["exitable_per_day"]) for r in rows)
    weights = sorted((r["weight_pct"] for r in rows), reverse=True)
    for r in rows:
        warns += [f"{r['symbol']}: {f}" for f in r["flags"]]
    gross, net = sum(r["gross_pl"] for r in rows), sum(r["net_pl"] for r in rows)
    out = {"as_of": today.isoformat(), "limits_used": lim,
           "totals": {"invested_value": round(invested, 2), "cash": round(cash, 2), "total_value": round(total, 2),
                      "cost": round(sum(r["cost"] for r in rows), 2), "gross_pl": round(gross, 2),
                      "net_pl_if_all_sold_today": round(net, 2), "costs_and_tax_drag": round(gross - net, 2),
                      "cash_pct": round(cash_pct, 2), "top1_pct": round(weights[0], 2), "top3_pct": round(sum(weights[:3]), 2),
                      f"liquid_within_{n}_days_pct_of_invested": round(liquid / invested * 100, 1),
                      "note": "net result sums holdings one by one; loss relief across holdings is not assumed (see tax-and-costs.md)"},
           "sectors_pct_of_total": {k: round(v, 2) for k, v in sorted(sectors.items(), key=lambda kv: -kv[1])},
           "holdings": [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items() if k != "exitable_per_day"} for r in rows],
           "warnings": warns}
    out["table_markdown"] = summary_markdown(out)
    return out


def summary_markdown(o):
    lines = ["| Symbol | Sector | Kitta | WACC | LTP | Value | Weight | Gross P/L | Net P/L after costs and tax | Days to exit |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in o["holdings"]:
        d = "?" if r["days_to_exit"] is None else f"{r['days_to_exit']:.1f}"
        lines.append(f"| {r['symbol']} | {r['sector']} | {r['kitta']:,} | {r['wacc']:,.2f} | {r['ltp']:,.2f} | {r['value']:,.0f} | "
                     f"{r['weight_pct']:.1f}% | {r['gross_pl']:,.0f} | {r['net_pl']:,.0f} | {d} |")
    return "\n".join(lines)


def log_path():
    return Path(os.environ.get("NEPSE_DECISION_LOG") or Path(__file__).resolve().parent.parent / "evals" / "decision_log.csv")


def log_row(a, path=None):
    """Validate and append one verdict. Raises ValueError with the reason when the row must not be logged."""
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=45))).date()
    date_ad = a.get("date_ad") or today.isoformat()
    if a["verdict"] not in VERDICTS:
        raise ValueError(f"verdict must be one of {', '.join(VERDICTS)}")
    if a["confidence"] not in ("low", "medium", "high"):
        raise ValueError("confidence must be low, medium or high")
    if a["data_status"] != "ok":
        raise ValueError("data status is not ok: no verdict may be given or logged on unverified data")
    if a["confidence"] == "high" and a["confirmations"] < 3:
        raise ValueError("high confidence needs at least 3 independent confirmations (fundamentals, valuation, trend, flows, macro); use medium")
    if not 0 <= a["probability"] <= 1:
        raise ValueError("probability must be between 0 and 1")
    if a["reference_price"] <= 0:
        raise ValueError("reference price must be above zero")
    for k in ("horizon", "resolution_rule", "data_timestamp", "symbol"):
        if not str(a[k]).strip():
            raise ValueError(f"{k} is required")
    try:
        review = dt.date.fromisoformat(a["review_date"])
        log_day = dt.date.fromisoformat(date_ad)
    except (TypeError, ValueError):
        raise ValueError("dates must be YYYY-MM-DD (AD)")
    if review <= log_day:
        raise ValueError("review date must be after the log date")
    row = {"date_ad": date_ad, "symbol": a["symbol"].upper(), "verdict": a["verdict"], "confidence": a["confidence"],
           "horizon": scrub(a["horizon"])[0], "review_date": a["review_date"], "resolution_rule": scrub(a["resolution_rule"])[0],
           "probability": a["probability"], "reference_price": a["reference_price"], "data_timestamp": a["data_timestamp"],
           "data_status": a["data_status"], "outcome": ""}
    path = Path(path) if path else log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    has_rows = path.exists() and path.stat().st_size > 0
    if has_rows and tuple(path.read_text(encoding="utf-8").splitlines()[0].split(",")) != LOG_FIELDS:
        raise ValueError(f"{path} has a different header; refusing to append so columns do not shift")
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS, lineterminator="\n")
        if not has_rows:
            w.writeheader()
        w.writerow(row)
    return row


def load_json(arg):
    return json.load(sys.stdin if arg == "-" else open(arg, encoding="utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse")
    p.add_argument("file")
    p.add_argument("--no-symbol-check", action="store_true", help="skip the exchange symbol list (offline)")
    sm = sub.add_parser("summary")
    sm.add_argument("file")
    lg = sub.add_parser("log")
    lg.add_argument("--symbol", required=True)
    lg.add_argument("--verdict", required=True)
    lg.add_argument("--confidence", required=True)
    lg.add_argument("--horizon", required=True, help="for example '12 months'")
    lg.add_argument("--review-date", required=True, help="AD date when the call is scored")
    lg.add_argument("--rule", required=True, help="resolution rule: what outcome counts as the call being right")
    lg.add_argument("--probability", type=float, required=True, help="your probability that the rule resolves true, 0 to 1")
    lg.add_argument("--price", type=float, required=True, help="reference price at the time of the call")
    lg.add_argument("--data-timestamp", required=True)
    lg.add_argument("--data-status", default="unverified", help="must be ok")
    lg.add_argument("--confirmations", type=int, default=0, help="independent confirming signals, for the high-confidence cap")
    lg.add_argument("--date")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "summary":
            print(json.dumps(summarise(load_json(a.file)), indent=2, ensure_ascii=False))
            return 0
        if a.cmd == "log":
            row = log_row({"symbol": a.symbol, "verdict": a.verdict, "confidence": a.confidence, "horizon": a.horizon,
                           "review_date": a.review_date, "resolution_rule": a.rule, "probability": a.probability,
                           "reference_price": a.price, "data_timestamp": a.data_timestamp, "data_status": a.data_status,
                           "confirmations": a.confirmations, "date_ad": a.date})
            print(json.dumps({"status": "logged", "path": str(log_path()), "row": row}, indent=2))
            return 0
        doc = load_json(a.file)
        known = None
        if not a.no_symbol_check:
            try:
                import fetch_data
                known = {s["symbol"] for s in fetch_data.symbols_report()["symbols"]}
            except Exception as e:  # network down: say so, do not pretend the symbols were checked
                print(f"symbol list unavailable ({type(e).__name__}); symbols not validated", file=sys.stderr)
        rep = parse(doc, known)
    except (ValueError, OSError) as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        return 2
    rep["table_markdown"] = table_markdown(rep)
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    return 1 if any(r["needs_user"] for r in rep["rows"]) else 0


if __name__ == "__main__":
    sys.exit(main())
