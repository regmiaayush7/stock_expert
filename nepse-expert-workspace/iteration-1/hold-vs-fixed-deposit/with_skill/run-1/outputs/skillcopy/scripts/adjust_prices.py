#!/usr/bin/env python3
"""Adjust a raw NEPSE price series for bonus, right and (optionally) cash dividends, then reconcile it
against the sources' own adjusted series. Stdlib only.

  adjust_prices.py SYMBOL [--cash] [--refresh]

Conventions, checked on 2026-10-24 against Merolagani (isAdjust=1) and NepseAlpha:
  bonus b%               P -> P / (1 + b/100)
  right n:m at price K   P -> (n*P + m*K) / (n + m)   (theoretical ex-rights price of each bar; n held, m new)
  cash c% of Rs 100 par  P -> P - c   only with --cash. Neither source removes cash dividends, so the default matches them.
Ex-bar = first bar dated on or after the book-closure date (right shares: final_date).
Unadjusted NEPSE history shows false crashes (a 33% bonus is a 25% "drop"), so indicators must use this output.
Renamed or merged symbols are chained through data/symbol_map.csv so one series spans the break.
"""
import argparse, json, re, statistics, sys

import fetch_data as fd

TOL_PCT = 1.5          # my close vs the source-adjusted close; the sources round and differ slightly per event
BAND_CHANGE = "2026-04-20"  # daily limit raised from 10% to 15% (Securities Trading Operation Fourth Amendment); verify live


def band_pct(date):
    """Largest one-day move the exchange allowed on `date`. A bigger adjusted move on an ex-bar means a missed adjustment."""
    return 15.0 if date >= BAND_CHANGE else 10.0
SESSIONS = {"1m": 21, "3m": 63, "6m": 126, "12m": 250}
MAP = fd.ROOT / "data" / "symbol_map.csv"


def events_from(actions, cash=False):
    ev = []
    for r in actions["dividends"]:
        d, b, c = r.get("bookclose_date"), fd.num(r.get("bonus_share")) or 0.0, fd.num(r.get("cash_dividend")) or 0.0
        if d and (b or (cash and c)):
            ev.append({"kind": "dividend", "date": d, "bonus_pct": b, "cash_rs": c if cash else 0.0})
    for r in actions["rights"]:
        d, k = r.get("final_date"), fd.num(r.get("issue_price"))
        m = re.fullmatch(r"\s*([\d.]+)\s*:\s*([\d.]+)\s*", r.get("ratio_value") or "")
        if d and k and m:
            ev.append({"kind": "right", "date": d, "n": float(m[1]), "m": float(m[2]), "price": k})
    return sorted(ev, key=lambda e: e["date"])


def apply_event(p, e):
    if e["kind"] == "right":
        return (e["n"] * p + e["m"] * e["price"]) / (e["n"] + e["m"])
    return (p - e["cash_rs"]) / (1 + e["bonus_pct"] / 100)


def ex_index(dates, event_date):
    return next((i for i, d in enumerate(dates) if d >= event_date), None)


def adjust(raw, events):
    """raw {date: [o,h,l,c,v]} -> same shape with o,h,l,c adjusted. An event needs a bar before its ex-bar and one
    on or after the closure date; events outside the series are skipped (run() lists future ones as pending)."""
    dates = sorted(raw)
    exs = [(i, e) for e in events if (i := ex_index(dates, e["date"])) is not None and i > 0]
    out = {}
    for j, d in enumerate(dates):
        px = raw[d][:4]
        for i, e in exs:  # events are date-sorted: the earliest event after this bar goes first
            if j < i:
                px = [apply_event(p, e) for p in px]
        out[d] = [round(p, 4) for p in px] + [raw[d][4]]
    return out


def read_map():
    """symbol_map.csv: old_symbol,new_symbol,effective_date_ad,reason,swap_ratio,source,last_verified"""
    if not MAP.exists():
        return []
    lines = [ln for ln in MAP.read_text(encoding="utf-8").splitlines() if ln.strip()]
    head = lines[0].split(",")
    return [dict(zip(head, ln.split(","))) for ln in lines[1:]]


def build(sym, rows, load_raw, load_events, seen=frozenset()):
    """Adjusted series for sym with predecessor history (rename or merger) prepended. Predecessor bars are adjusted
    for the predecessor's own events, divided by swap_ratio (new shares per old share), and stop before effective_date."""
    raw = dict(load_raw(sym))
    for r in rows:
        if r["new_symbol"] == sym and r["old_symbol"] not in seen:
            ratio = float(r.get("swap_ratio") or 1)
            for d, b in build(r["old_symbol"], rows, load_raw, load_events, seen | {sym}).items():
                if d < r["effective_date_ad"]:
                    raw.setdefault(d, [x / ratio for x in b[:4]] + [b[4] * ratio])
    return adjust(raw, load_events(sym))


def reconcile(raw, mine, ref, events, label):
    dates = sorted(set(raw) & set(mine) & set(ref))
    if not dates:
        return {"vs": label, "error": "no overlapping dates"}
    err = {d: abs(mine[d][3] / ref[d][3] - 1) * 100 for d in dates}
    roll = {d: statistics.median(err[x] for x in dates[max(0, k - 4):k + 1]) for k, d in enumerate(dates)}
    bad = [d for d in dates if roll[d] > TOL_PCT]
    ex_bad = []
    for e in events:
        i = ex_index(dates, e["date"])
        if i and any(err[x] > TOL_PCT for x in dates[max(0, i - 1):i + 1]):
            ex_bad.append(e["date"])
    return {"vs": label, "bars": len(dates), "agreement_pct": round(100 * (1 - len(bad) / len(dates)), 1),
            "max_err_pct": round(max(err.values()), 2),
            "latest_disagreement": bad[-1] if bad else None,  # an event the source knows and we do not lies at or after this bar
            "ex_bar_disagrees_for_events_dated": ex_bad}


def summary(adj):
    dates = sorted(adj)
    last = adj[dates[-1]][3]
    ret = {k: round((last / adj[dates[-n - 1]][3] - 1) * 100, 1) for k, n in SESSIONS.items() if len(dates) > n}
    yr = dates[-250:]
    hi, lo = max(adj[d][1] for d in yr), min(adj[d][2] for d in yr)
    fwd = sorted((adj[dates[i + 250]][3] / adj[dates[i]][3] - 1) * 100 for i in range(len(dates) - 250))
    base = ({"windows": len(fwd), "p10": round(fwd[len(fwd) // 10], 1), "median": round(fwd[len(fwd) // 2], 1),
             "p90": round(fwd[len(fwd) * 9 // 10], 1),
             "caveat": "this stock's own 250-session returns on bonus-adjusted prices, overlapping windows, one sample that includes the 2020-22 boom and fall; a rough base rate, not a tested setup base rate and not a forecast"}
            if len(fwd) >= 250 else None)
    return {"returns_pct": ret, "own_history_12m_return_distribution_pct": base,
            "range_250_sessions": {"high": round(hi, 2), "low": round(lo, 2),
                                   "position_0_to_1": round((last - lo) / (hi - lo), 3) if hi > lo else None},
            "note": "v0 technical view: returns and range only; indicators arrive in v1"}


def false_crash_check(raw, adj, events):
    dates = sorted(raw)
    out = []
    for e in events:
        i = ex_index(dates, e["date"])
        if i:
            r = (raw[dates[i]][3] / raw[dates[i - 1]][3] - 1) * 100
            a = (adj[dates[i]][3] / adj[dates[i - 1]][3] - 1) * 100
            out.append({"ex_bar": dates[i], "raw_return_pct": round(r, 1), "adjusted_return_pct": round(a, 1),
                        "residual_crash": abs(a) > band_pct(dates[i])})
    return out


def run(sym, cash=False, refresh=False):
    bars, _, origin = fd.get_bars(sym, refresh)
    raw = bars["mero_raw"]
    acts = {}
    events_for = lambda s: events_from(acts.setdefault(s, fd.actions_report(s, refresh)), cash)
    rows = read_map()
    adj = build(sym, rows, lambda s: raw if s == sym else fd.get_bars(s, refresh)[0]["mero_raw"], events_for)
    events, dates = events_for(sym), sorted(raw)
    used, pending = [], []
    for e in events:
        i = ex_index(dates, e["date"])
        if i is None:
            pending.append(e)
        elif i > 0:
            used.append(dict(e, ex_bar=dates[i]))
    recs = [reconcile(raw, adj, bars["mero_adj"], used, "merolagani_adjusted")]
    if bars.get("alpha_adj"):
        recs.append(reconcile(raw, adj, bars["alpha_adj"], used, "nepsealpha_adjusted"))
    notes = ["cash dividends removed: this series will NOT match either source, which ignore cash"] if cash else []
    for r in recs:
        if r.get("latest_disagreement") and not cash:
            notes.append(f"{r['vs']}: disagrees through {r['latest_disagreement']}; an adjustment event may be missing from the action list")
    fc = false_crash_check(raw, adj, used)
    ok = (not cash and all(r.get("agreement_pct", 0) >= 95 for r in recs)
          and not any(c["residual_crash"] for c in fc) and origin != "stale-cache")
    path = fd.CACHE / f"adjusted_{sym}.json"
    fd.atomic_write(path, json.dumps(adj))
    return {"symbol": sym, "block": "adjusted_prices", "status": "ok" if ok else "unverified",
            "basis": "bonus and right adjusted" + ("; cash removed" if cash else "; cash dividends not removed"),
            "bars": len(adj), "first": min(adj), "last": max(adj), "chained_from": [r["old_symbol"] for r in rows if r["new_symbol"] == sym],
            "events_applied": used, "events_pending_after_last_bar": pending,
            "reconciliation": recs, "false_crash_check": fc, "summary": summary(adj), "notes": notes,
            "adjusted_bars_file": str(path), "origin": origin,
            "sources": ["sharesansar.com company-dividend and company-rightshare", "merolagani.com chart (raw, adjusted)", "nepsealpha.com history"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbol")
    ap.add_argument("--cash", action="store_true", help="also remove cash dividends (total-return view)")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    try:
        rep = run(a.symbol.upper(), a.cash, a.refresh)
    except fd.FetchError as e:
        print(json.dumps({"status": "error", "error": str(e),
                          "fallback": "No adjusted series. Do not compute indicators from raw prices; ask for a pasted series or give no technical view."}, indent=2))
        return 2
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    return 0 if rep["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
