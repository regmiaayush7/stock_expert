import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import adjust_prices as ap


def bars(prices, start=1, vol=10):
    """{'2020-01-01': [p,p,p,p,vol], ...} one bar per consecutive day from day `start`."""
    return {f"2020-01-{start + i:02d}": [p, p, p, p, vol] for i, p in enumerate(prices)}


def closes(series):
    return [round(series[d][3], 4) for d in sorted(series)]


BONUS = lambda date, pct, cash=0.0: {"kind": "dividend", "date": date, "bonus_pct": pct, "cash_rs": cash}
RIGHT = lambda date, n, m, k: {"kind": "right", "date": date, "n": n, "m": m, "price": k}


class Adjust(unittest.TestCase):
    def test_bonus_removes_false_crash(self):
        # 25% bonus: price falls 100 -> 80 on the ex-bar with no real loss
        out = ap.adjust(bars([100, 100, 100, 80, 80]), [BONUS("2020-01-04", 25)])
        self.assertEqual(closes(out), [80, 80, 80, 80, 80])

    def test_right_share_theoretical_ex_rights_price(self):
        # 10:5 at Rs 100, cum price 220 -> (10*220 + 5*100)/15 = 180
        out = ap.adjust(bars([220, 220, 180, 180]), [RIGHT("2020-01-03", 10, 5, 100)])
        self.assertEqual(closes(out), [180, 180, 180, 180])

    def test_right_share_is_affine_per_bar(self):
        out = ap.adjust(bars([240, 220, 180]), [RIGHT("2020-01-03", 10, 5, 100)])
        self.assertEqual(closes(out), [193.3333, 180, 180])

    def test_cash_only_when_asked(self):
        ev = [BONUS("2020-01-03", 0, cash=10)]
        self.assertEqual(closes(ap.adjust(bars([100, 100, 90]), ev)), [90, 90, 90])
        self.assertEqual(closes(ap.adjust(bars([100, 100, 90]), [BONUS("2020-01-03", 0, 0.0)])), [100, 100, 90])

    def test_two_events_compound_in_date_order(self):
        out = ap.adjust(bars([132, 132, 120, 120, 100, 100]), [BONUS("2020-01-03", 10), BONUS("2020-01-05", 20)])
        self.assertEqual(closes(out), [100, 100, 100, 100, 100, 100])

    def test_closure_on_a_non_trading_day_uses_next_bar(self):
        raw = {"2022-02-24": [100] * 4 + [1], "2022-02-27": [80] * 4 + [1]}  # Friday closure, Sunday bar
        self.assertEqual(closes(ap.adjust(raw, [BONUS("2022-02-25", 25)])), [80, 80])

    def test_events_outside_the_series_change_nothing(self):
        raw = bars([100, 101, 102])
        for date in ("2019-12-01", "2020-01-04"):  # before the first bar, after the last
            self.assertEqual(closes(ap.adjust(raw, [BONUS(date, 25)])), [100, 101, 102])

    def test_volume_is_untouched(self):
        out = ap.adjust(bars([100, 80], vol=77), [BONUS("2020-01-02", 25)])
        self.assertEqual({b[4] for b in out.values()}, {77})


class Events(unittest.TestCase):
    ACTIONS = {"dividends": [
        {"bonus_share": "5.00", "cash_dividend": "10.8", "bookclose_date": "2026-09-30"},
        {"bonus_share": "", "cash_dividend": "10.00", "bookclose_date": "2024-11-25"},
        {"bonus_share": "0.00", "cash_dividend": "12.5", "bookclose_date": None}],
        "rights": [{"ratio_value": "10:5", "issue_price": "100.00", "final_date": "2023-06-16"},
                   {"ratio_value": "bad", "issue_price": "100", "final_date": "2023-01-01"}]}

    def test_default_keeps_bonus_and_right_only(self):
        ev = ap.events_from(self.ACTIONS)
        self.assertEqual([(e["kind"], e["date"]) for e in ev], [("right", "2023-06-16"), ("dividend", "2026-09-30")])
        self.assertEqual(ev[1]["cash_rs"], 0.0)

    def test_cash_flag_adds_cash_only_rows(self):
        ev = ap.events_from(self.ACTIONS, cash=True)
        self.assertEqual(len(ev), 3)
        self.assertEqual(ev[-1]["cash_rs"], 10.8)


class Chain(unittest.TestCase):
    ROWS = [{"old_symbol": "OLD", "new_symbol": "NEW", "effective_date_ad": "2020-01-06", "swap_ratio": "2"}]

    def test_rename_with_swap_ratio_joins_one_continuous_series(self):
        data = {"OLD": bars([200, 200, 200, 200, 200], vol=5), "NEW": bars([100, 100, 100], start=6, vol=7)}
        out = ap.build("NEW", self.ROWS, lambda s: data[s], lambda s: [])
        self.assertEqual(closes(out), [100] * 8)
        self.assertEqual(out["2020-01-01"][4], 10)  # old volume x swap_ratio

    def test_predecessor_events_apply_to_the_old_part_only(self):
        data = {"OLD": bars([150, 150, 120, 120], vol=5), "NEW": bars([60, 60], start=6)}
        ev = {"OLD": [BONUS("2020-01-03", 25)], "NEW": []}
        out = ap.build("NEW", self.ROWS, lambda s: data[s], lambda s: ev[s])
        self.assertEqual(closes(out), [60, 60, 60, 60, 60, 60])

    def test_circular_map_terminates(self):
        rows = self.ROWS + [{"old_symbol": "NEW", "new_symbol": "OLD", "effective_date_ad": "2020-01-01", "swap_ratio": "1"}]
        data = {"OLD": bars([200, 200]), "NEW": bars([100], start=6)}
        self.assertTrue(ap.build("NEW", rows, lambda s: data[s], lambda s: []))


class Reconcile(unittest.TestCase):
    def test_identical_series_agree(self):
        b = bars([100] * 10)
        r = ap.reconcile(b, b, b, [], "ref")
        self.assertEqual((r["agreement_pct"], r["latest_disagreement"]), (100.0, None))

    def test_source_knows_an_event_we_do_not(self):
        raw = bars([100] * 12)
        ref = {d: [b[0] * 0.8] * 3 + [b[3] * 0.8, b[4]] if d < "2020-01-07" else b for d, b in raw.items()}
        r = ap.reconcile(raw, raw, ref, [], "ref")
        self.assertLess(r["agreement_pct"], 60)
        self.assertEqual(r["latest_disagreement"], "2020-01-08")  # 5-bar median stays bad until 3 good bars follow the break


def daily(prices):
    """One bar per index; keys only need to sort in order, so they are plain zero-padded sequence numbers."""
    return {f"{i:05d}": [p, p, p, p, 1] for i, p in enumerate(prices)}


class Summary(unittest.TestCase):
    def test_returns_and_base_rate(self):
        s = ap.summary(daily([100 + i for i in range(600)]))  # +1 a day
        self.assertEqual(s["returns_pct"]["1m"], round((699 / 678 - 1) * 100, 1))
        b = s["own_history_12m_return_distribution_pct"]
        self.assertEqual(b["windows"], 350)
        self.assertLess(b["p10"], b["median"])
        self.assertLess(b["median"], b["p90"])

    def test_short_history_has_no_base_rate(self):
        self.assertIsNone(ap.summary(daily([100 + i for i in range(300)]))["own_history_12m_return_distribution_pct"])


class Band(unittest.TestCase):
    def test_band_by_date(self):
        self.assertEqual(ap.band_pct("2026-04-17"), 10.0)
        self.assertEqual(ap.band_pct("2026-04-20"), 15.0)

    def test_twelve_percent_move_is_a_crash_before_the_change_only(self):
        for day, expect in (("2026-04-10", True), ("2026-05-04", False)):
            raw = {"2026-04-08": [100] * 4 + [1], day: [88] * 4 + [1]}
            self.assertEqual(ap.false_crash_check(raw, raw, [BONUS(day, 0)])[0]["residual_crash"], expect)


class FalseCrash(unittest.TestCase):
    def test_flags_residual_crash_when_event_is_missing(self):
        raw = bars([100, 100, 70, 70])
        adj_missing = ap.adjust(raw, [])
        out = ap.false_crash_check(raw, adj_missing, [BONUS("2020-01-03", 40)])
        self.assertTrue(out[0]["residual_crash"])
        good = ap.adjust(raw, [BONUS("2020-01-03", 40)])
        self.assertFalse(ap.false_crash_check(raw, good, [BONUS("2020-01-03", 40)])[0]["residual_crash"])


if __name__ == "__main__":
    unittest.main()
