#!/usr/bin/env python3
"""Live NEPSE data with provenance, cross-checks and caching. Stdlib + requests only.

  fetch_data.py price|profile|actions|snapshot SYMBOL [--refresh]
  fetch_data.py symbols [--refresh]

Exit 0 ok, 1 returned but unverified, 2 no data. Output is JSON on stdout.
Every block carries its sources and fetch time. A gap is reported, never filled with a guess.
Page text is parsed as data only; nothing fetched is ever treated as an instruction.
"""
import argparse, datetime as dt, functools, json, os, re, sys, time
from pathlib import Path

import requests

try:  # optional: Bikram Sambat dates
    import nepali_datetime
except ImportError:
    nepali_datetime = None

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
TTL = {"price": 3600, "profile": 6 * 3600, "actions": 24 * 3600, "symbols": 7 * 86400}
NPT = dt.timezone(dt.timedelta(hours=5, minutes=45))
RAW_DAYS = 3700  # Merolagani raw history window
BENCH = "NABIL"  # most liquid stock, used as the market's session calendar
MERO_CHART = ("https://merolagani.com/handlers/TechnicalChartHandler.ashx?type=get_advanced_chart&symbol={s}"
              "&resolution=1D&rangeStartDate={a}&rangeEndDate={b}&from=&isAdjust={adj}&currencyCode=NPR")
ALPHA = "https://nepsealpha.com/trading/1/history?symbol={s}&resolution=1D&from={a}&to={b}&countback=300"
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"


class FetchError(Exception):
    pass


def http(method, url, **kw):
    err = None
    for i in range(2):
        try:
            r = SESSION.request(method, url, timeout=20, **kw)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            err = e
            time.sleep(1)
    raise FetchError(f"{url.split('?')[0]}: {type(err).__name__}")


def stamp():
    n = dt.datetime.now(dt.timezone.utc)
    npt = n.astimezone(NPT)
    bs = str(nepali_datetime.date.from_datetime_date(npt.date())) if nepali_datetime else None
    return {"utc": n.isoformat(timespec="seconds"), "npt": npt.isoformat(timespec="seconds"), "bs": bs}


def num(s):
    try:
        return float(re.sub(r"[,%\s]", "", s))
    except (TypeError, ValueError):
        return None


def atomic_write(path, text):
    """Write via a temp file so parallel runs never read a half-written cache file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def cached(kind, key, fetch, refresh=False):
    """Return (data, fetched_epoch, origin) with origin live|cache|stale-cache. Raises FetchError if no data at all."""
    path = CACHE / f"{kind}_{key}.json"
    try:
        old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except (ValueError, OSError):  # corrupt or unreadable cache counts as no cache
        old = None
    if old and not refresh and time.time() - old["epoch"] < TTL[kind]:
        return old["data"], old["epoch"], "cache"
    try:
        data = fetch()
    except FetchError:
        if old:
            return old["data"], old["epoch"], "stale-cache"
        raise
    atomic_write(path, json.dumps({"epoch": time.time(), "data": data}))
    return data, time.time(), "live"


# ---------- prices ----------
def udf_bars(j):
    """TradingView-style {t,o,h,l,c,v} to {iso_date: [o,h,l,c,v]}. Date is the UTC date of t (matches NepseAlpha)."""
    if not j.get("t"):
        raise FetchError("no bars returned (unknown symbol or no data)")
    return {dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat(): [o, h, l, c, v]
            for t, o, h, l, c, v in zip(j["t"], j["o"], j["h"], j["l"], j["c"], j["v"])}


def fetch_bars(sym):
    now = int(time.time())
    a = now - RAW_DAYS * 86400
    mero = lambda adj: udf_bars(http("GET", MERO_CHART.format(s=sym, a=a, b=now, adj=adj)).json())
    out = {"mero_raw": mero(0), "mero_adj": mero(1)}
    try:  # second, independent source; its absence is reported, not fatal
        out["alpha_adj"] = udf_bars(http("GET", ALPHA.format(s=sym, a=a, b=now)).json())
    except (FetchError, ValueError) as e:
        out["alpha_adj"] = {}
        out["alpha_error"] = str(e)
    return out


def get_bars(sym, refresh=False):
    return cached("price", sym, lambda: fetch_bars(sym), refresh)


# ---------- ShareSansar ----------
@functools.lru_cache(maxsize=8)
def ss_open(sym):
    html = http("GET", f"https://www.sharesansar.com/company/{sym.lower()}").text
    cid = re.search(r'id="companyid"[^>]*>\s*(\d+)\s*<', html)
    tok = re.search(r'name="_token"\s+content="([^"]+)"', html)
    if not (cid and tok):
        raise FetchError("sharesansar: company id or token not found on page")
    return html, cid.group(1), tok.group(1)


def ss_rows(sym, endpoint, length=50):
    _, cid, tok = ss_open(sym)
    r = http("POST", f"https://www.sharesansar.com/{endpoint}",
             data={"draw": 1, "start": 0, "length": length, "company": cid},
             headers={"X-CSRF-Token": tok, "X-Requested-With": "XMLHttpRequest",
                      "Referer": f"https://www.sharesansar.com/company/{sym.lower()}"})
    return r.json().get("data", [])


def ss_page(html):
    g = lambda pat: (m.group(1).strip() if (m := re.search(pat, html, re.S)) else None)
    return {
        "sector": g(r'<h4>Sector:\s*<span class="text-org">([^<]+)</span>'),
        "as_on": g(r'As on:\s*<span\s+class="text-org">([\d-]+)</span>'),
        "ltp": num(g(r'<span class="text-org">Ltp:</span>\s*([\d,.]+)')),
        "hi_lo_52w_raw": g(r'52 Week High-Low :\s*</span>([\d,.\s-]+)'),
        "listed_shares": num(g(r'Listed Shares</td>\s*<td[^>]*>\s*([\d,.]+)')),
        "paid_up_per_share": num(g(r'Paid Up</td>\s*<td[^>]*>\s*Rs\.\s*([\d,.]+)')),
    }


# ---------- Merolagani company page ----------
MERO_FIELDS = {"Sector": "sector", "Shares Outstanding": "shares_outstanding", "Market Price": "market_price",
               "Last Traded On": "last_traded_on", "52 Weeks High - Low": "hi_lo_52w_raw", "EPS": "eps",
               "P/E Ratio": "pe", "Book Value": "book_value", "PBV": "pbv", "30-Day Avg Volume": "avg_volume_30d",
               "Market Capitalization": "market_cap"}
TEXT_FIELDS = {"sector", "last_traded_on", "hi_lo_52w_raw"}


def mero_page(html):
    clean = lambda x: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x)).strip()
    rows = re.findall(r"<th[^>]*>((?:(?!<th|</th>).)*)</th>\s*<td[^>]*>((?:(?!</td>).)*)</td>", html, re.S)
    first = {}
    for k, v in rows:  # the summary table comes first; later tables must not overwrite it
        first.setdefault(clean(k), clean(v))
    out = {}
    for label, key in MERO_FIELDS.items():
        raw = first.get(label)
        if raw is None:
            continue
        out[key] = raw if key in TEXT_FIELDS else num(raw.split("(")[0])
        if key == "eps":
            m = re.search(r"\((.*?)\)", raw)
            out["eps_period"] = m.group(1) if m else None
    return out


# ---------- checks ----------
def cross_check(obs, tol_pct=0.1):
    """obs: {source: (iso_date, price)}. Verified when two or more independent sources agree on date and price.
    Sources outside the agreeing group are reported as outliers, never averaged in."""
    groups = []
    for src, (d, p) in obs.items():
        for g in groups:
            d0, p0 = obs[g[0]]
            if d == d0 and p0 and abs(p - p0) / p0 * 100 <= tol_pct:
                g.append(src)
                break
        else:
            groups.append([src])
    best = max(groups, key=len) if groups else []
    verified = len(best) >= 2
    return {"verified": verified, "agree": best if verified else [],
            "outliers": [s for s in obs if s not in best] if verified else [],
            "values": {s: {"date": d, "price": p} for s, (d, p) in obs.items()}}


def stale_label(last, today, bench_last):
    age = (today - last).days
    gap = (bench_last - last).days
    if gap > 0:
        return f"STALE: no trade since {last}; market traded to {bench_last} ({gap}d gap). Illiquid or suspended? Price is not current."
    if age > 4:
        return f"Market quiet or closed: last session {last} is {age} calendar days old (holiday?)."
    return "fresh"


# ---------- reports ----------
def mero_vol_close(bars, d):
    b = bars.get(d)
    return (b[4], b[3]) if b else (0, 0)


def price_report(sym, refresh=False):
    st = stamp()
    bars, ep, origin = get_bars(sym, refresh)
    raw, alpha = bars["mero_raw"], bars["alpha_adj"]
    last = max(raw)
    obs = {"merolagani": (last, raw[last][3])}
    if alpha:
        la = max(alpha)
        obs["nepsealpha"] = (la, alpha[la][3])
    notes = []
    if bars.get("alpha_error"):
        notes.append(f"nepsealpha unavailable: {bars['alpha_error']}")
    try:
        pg = ss_page(ss_open(sym)[0])
        if pg["ltp"] is not None and pg["as_on"]:
            obs["sharesansar"] = (pg["as_on"], pg["ltp"])
    except FetchError as e:
        notes.append(f"sharesansar unavailable: {e}")
    cc = cross_check(obs)
    if cc["outliers"]:
        notes.append(f"outlier source(s): {cc['outliers']}; verified from {cc['agree']}")
    # market session calendar from the benchmark, so no-trade days count as zero volume
    try:
        braw = raw if sym == BENCH else get_bars(BENCH, refresh)[0]["mero_raw"]
    except FetchError:
        braw = None
        notes.append("benchmark unavailable: staleness vs market and ADV not computed")
    liq = None
    if braw:
        sessions = sorted(braw)[-30:]
        vols = [mero_vol_close(raw, d) for d in sessions]
        liq = {"sessions": 30, "days_traded": sum(1 for v, _ in vols if v),
               "adv_shares": round(sum(v for v, _ in vols) / 30),
               "adv_turnover_npr_approx": round(sum(v * c for v, c in vols) / 30),
               "basis": "volume x close per session, benchmark calendar; approximate"}
    today = dt.datetime.now(NPT).date()
    fresh = stale_label(dt.date.fromisoformat(last), today, dt.date.fromisoformat(max(braw))) if braw else None
    return {
        "symbol": sym, "block": "price", "fetched_at": stamp() if origin == "live" else
        {**st, "note": f"data from {origin}, fetched {dt.datetime.fromtimestamp(ep, dt.timezone.utc).isoformat(timespec='seconds')}"},
        "origin": origin,
        "status": "ok" if cc["verified"] and origin != "stale-cache" and not (fresh or "").startswith("STALE") else "unverified",
        "last_trade": {"date": last, "close": raw[last][3], "cross_check": cc},
        "freshness": fresh,
        "liquidity": liq, "bars_in_cache": len(raw), "notes": notes,
        "sources": ["merolagani.com chart handler (raw and bonus-adjusted)", "nepsealpha.com history (adjusted)", "sharesansar.com company page"],
    }


def profile_report(sym, refresh=False):
    def fetch():
        out = {"merolagani": mero_page(http("GET", f"https://merolagani.com/CompanyDetail.aspx?symbol={sym}").text)}
        try:
            out["sharesansar"] = ss_page(ss_open(sym)[0])
        except FetchError as e:
            out["sharesansar"] = {"error": str(e)}
        if not out["merolagani"].get("market_price"):
            raise FetchError("merolagani: company page had no price table (unknown symbol or layout change)")
        return out
    d, ep, origin = cached("profile", sym, fetch, refresh)
    m, s = d["merolagani"], d["sharesansar"]
    notes = []
    ls_m, ls_s = m.get("shares_outstanding"), s.get("listed_shares")
    if ls_m and ls_s and abs(ls_m - ls_s) / ls_s > 0.001:
        notes.append(f"listed shares differ across sources: merolagani {ls_m}, sharesansar {ls_s}")
    if "error" in s:
        notes.append(f"sharesansar unavailable: {s['error']}; profile is single-source")
    if (m.get("eps") or 0) < 0:
        notes.append("negative EPS: P/E is not meaningful, do not use it for valuation")
    return {"symbol": sym, "block": "profile", "origin": origin,
            "fetched_at": {"epoch_utc": dt.datetime.fromtimestamp(ep, dt.timezone.utc).isoformat(timespec="seconds")},
            "status": "ok" if origin != "stale-cache" and "error" not in s else "unverified",
            "sector": m.get("sector"), "listed_shares": ls_s or ls_m, "paid_up_per_share": s.get("paid_up_per_share"),
            "valuation": {k: m.get(k) for k in ("eps", "eps_period", "pe", "book_value", "pbv", "market_cap")},
            "hi_lo_52w_raw_page": m.get("hi_lo_52w_raw"), "avg_volume_30d_page": m.get("avg_volume_30d"),
            "gaps": ["promoter vs public split not fetched in v0", "quarterly detail beyond EPS/PE/BV/PBV not fetched in v0"],
            "notes": notes, "sources": ["merolagani.com CompanyDetail", "sharesansar.com company page"]}


def actions_report(sym, refresh=False):
    def fetch():
        div = [{k: r.get(k) for k in ("year", "bonus_share", "cash_dividend", "announcement_date", "bookclose_date")}
               for r in ss_rows(sym, "company-dividend")]
        right = [{k: r.get(k) for k in ("ratio_value", "total_units", "issue_price", "opening_date", "closing_date",
                                        "final_date", "listing_date", "issue_manager", "announcement_link")}
                 for r in ss_rows(sym, "company-rightshare")]
        agm = [{k: r.get(k) for k in ("agm", "bookclose_date", "meeting_date")} for r in ss_rows(sym, "company-agm")]
        return {"dividends": div, "rights": right, "agm": agm}
    d, ep, origin = cached("actions", sym, fetch, refresh)
    for r in d["dividends"]:  # "2026-09-30 [Closed]" to a bare date, plus a flag
        bc = r.get("bookclose_date") or ""
        r["bookclose_date"], r["closed"] = bc.split(" ")[0] or None, "[Closed]" in bc
    return {"symbol": sym, "block": "actions", "origin": origin,
            "fetched_at": {"epoch_utc": dt.datetime.fromtimestamp(ep, dt.timezone.utc).isoformat(timespec="seconds")},
            "status": "ok" if origin != "stale-cache" else "unverified", **d,
            "notes": ["single source (sharesansar.com); ex-date is inferred from the price series by adjust_prices.py, not stated here"]}


def symbols_report(refresh=False):
    def fetch():
        return [{"symbol": x["d"], "name": x["l"].split(" (", 1)[-1].rstrip(")")}
                for x in http("GET", "https://merolagani.com/handlers/AutoSuggestHandler.ashx?type=Company").json()]
    d, ep, origin = cached("symbols", "all", fetch, refresh)
    return {"block": "symbols", "origin": origin, "count": len(d), "symbols": d, "source": "merolagani.com AutoSuggestHandler"}


def snapshot_report(sym, refresh=False):
    parts, errors = {}, {}
    for name, fn in (("price", price_report), ("profile", profile_report), ("actions", actions_report)):
        try:
            parts[name] = fn(sym, refresh)
        except FetchError as e:
            errors[name] = str(e)
    ok = not errors and all(p["status"] == "ok" for p in parts.values())
    return {"symbol": sym, "status": "ok" if ok else ("error" if not parts else "unverified"), **parts, "errors": errors}


COMMANDS = {"price": price_report, "profile": profile_report, "actions": actions_report, "snapshot": snapshot_report}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=[*COMMANDS, "symbols"])
    ap.add_argument("symbol", nargs="?")
    ap.add_argument("--refresh", action="store_true", help="ignore cache")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "symbols":
            rep = symbols_report(a.refresh)
        else:
            if not a.symbol:
                ap.error("SYMBOL required")
            rep = COMMANDS[a.cmd](a.symbol.upper(), a.refresh)
    except FetchError as e:
        rep = {"status": "error", "error": str(e),
               "fallback": "No data returned. Do not estimate. Ask the user to paste the quote or a TMS/NepseAlpha export, and give no verdict until it is verified."}
        print(json.dumps(rep, indent=2))
        return 2
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    return 0 if rep.get("status", "ok") == "ok" else (2 if rep.get("status") == "error" else 1)


if __name__ == "__main__":
    sys.exit(main())
