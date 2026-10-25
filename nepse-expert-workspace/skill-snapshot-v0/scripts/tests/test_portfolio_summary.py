import csv, datetime as dt, os, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import parse_portfolio as pp

TODAY = dt.date(2026, 10, 24)


def h(sym, sector, kitta, wacc, ltp, adv, buy="2025-01-14", src="verified"):
    return {"symbol": sym, "sector": sector, "kitta": kitta, "wacc": wacc, "ltp": ltp, "adv_shares": adv,
            "purchase_date": buy, "ltp_source": src}


# values: A 50,000  B 60,000  C 250,000  D 80,000  E 20,000 = 460,000; cash 20,000; total 480,000
DOC = {"cash": 20000, "holdings": [
    h("NABIL", "Commercial Banks", 100, 400, 500, 1000),
    h("NICA", "Commercial Banks", 200, 350, 300, 5000),
    h("NHPC", "Hydro Power", 1000, 200, 250, 50000),
    h("UPPER", "Hydro Power", 400, 250, 200, 100),
    h("SHL", "Hotels And Tourism", 50, 400, 400, 100)]}


class Summary(unittest.TestCase):
    def setUp(self):
        self.s = pp.summarise(DOC, TODAY)
        self.by = {r["symbol"]: r for r in self.s["holdings"]}

    def test_totals_match_hand_calculation(self):
        t = self.s["totals"]
        self.assertEqual((t["invested_value"], t["cash"], t["total_value"]), (460000, 20000, 480000))
        self.assertEqual((t["cost"], t["gross_pl"]), (430000, 30000))  # +10,000 -10,000 +50,000 -20,000 +0
        self.assertEqual((t["top1_pct"], t["top3_pct"], t["cash_pct"]), (52.08, 81.25, 4.17))  # 52.083 + 16.667 + 12.5

    def test_weights_with_cash_sum_to_100(self):
        w = sum(r["weight_pct"] for r in self.s["holdings"]) + self.s["totals"]["cash_pct"]
        self.assertAlmostEqual(w, 100, delta=0.1)
        self.assertAlmostEqual(sum(self.s["sectors_pct_of_total"].values()) + self.s["totals"]["cash_pct"], 100, delta=0.1)

    def test_days_to_exit(self):
        self.assertEqual(self.by["NABIL"]["days_to_exit"], 1.0)    # 100 / (10% x 1,000)
        self.assertEqual(self.by["UPPER"]["days_to_exit"], 40.0)   # 400 / (10% x 100)
        self.assertEqual(self.by["NHPC"]["days_to_exit"], 0.2)

    def test_liquid_within_five_days(self):
        # NABIL 50,000 + NICA 60,000 + NHPC 250,000 + UPPER min(80,000, 5 x 10% x 100 x 200 = 10,000) + SHL 20,000 = 390,000 of 460,000
        self.assertEqual(self.s["totals"]["liquid_within_5_days_pct_of_invested"], 84.8)

    def test_illiquid_holding_triggers_warning(self):
        self.assertTrue(any(w.startswith("UPPER: ILLIQUID") for w in self.s["warnings"]))
        self.assertFalse(any(w.startswith("NABIL: ILLIQUID") for w in self.s["warnings"]))

    def test_concentration_warnings(self):
        text = " | ".join(self.s["warnings"])
        self.assertIn("NHPC: concentration: 52.1%", text)
        self.assertIn("sector concentration: Hydro Power is 68.8%", text)  # (250,000 + 80,000) / 480,000
        self.assertIn("cash is 4.2%", text)

    def test_loss_has_no_tax_and_gain_is_taxed(self):
        self.assertLess(self.by["NABIL"]["net_pl"], self.by["NABIL"]["gross_pl"])     # taxed gain pays costs and CGT
        self.assertLess(self.by["NICA"]["net_pl"], self.by["NICA"]["gross_pl"])       # a loss still pays selling costs
        self.assertAlmostEqual(self.by["NICA"]["net_pl"], -10000 - 198 - 9 - 25, delta=0.01)  # 60,000 x 0.33% = 198; x 0.015% = 9; DP 25

    def test_unverified_price_is_flagged(self):
        d = {"holdings": [h("NABIL", "Commercial Banks", 100, 400, 500, 1000, src="screen")]}
        s = pp.summarise(d, TODAY)
        self.assertTrue(any("not verified live" in w for w in s["warnings"]))

    def test_missing_volume_and_date_are_flagged_not_guessed(self):
        d = {"holdings": [h("NABIL", "Commercial Banks", 100, 400, 500, None, buy=None)]}
        w = " | ".join(pp.summarise(d, TODAY)["warnings"])
        self.assertIn("no volume data", w)
        self.assertIn("short-term tax rate assumed", w)

    def test_rejects_incomplete_or_fractional_holdings(self):
        for bad in ({"holdings": []}, {"holdings": [h("NABIL", "x", None, 400, 500, 1)]},
                    {"holdings": [h("NABIL", "x", 10.5, 400, 500, 1)]}, {"holdings": [h("", "x", 10, 400, 500, 1)]}):
            with self.assertRaises(ValueError):
                pp.summarise(bad, TODAY)

    def test_limits_can_be_overridden(self):
        s = pp.summarise({**DOC, "limits": {"single_stock_max_pct": 60}}, TODAY)
        self.assertFalse(any("NHPC: concentration" in w for w in s["warnings"]))


class Log(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "log.csv"
        self.ok = {"symbol": "nabil", "verdict": "Hold", "confidence": "medium", "horizon": "12 months", "review_date": "2027-10-24",
                   "resolution_rule": "adjusted close on review date at least 600", "probability": 0.55, "reference_price": 547.0,
                   "data_timestamp": "2026-10-24T11:58:06+00:00", "data_status": "ok", "confirmations": 2, "date_ad": "2026-10-24"}

    def tearDown(self):
        self.tmp.cleanup()

    def rows(self):
        return list(csv.DictReader(open(self.path, encoding="utf-8")))

    def test_appends_with_header_once(self):
        pp.log_row(self.ok, self.path)
        pp.log_row({**self.ok, "symbol": "NHPC"}, self.path)
        r = self.rows()
        self.assertEqual([x["symbol"] for x in r], ["NABIL", "NHPC"])
        self.assertEqual(tuple(r[0].keys()), pp.LOG_FIELDS)
        self.assertEqual(r[0]["outcome"], "")

    def test_refuses_unverified_data(self):
        with self.assertRaisesRegex(ValueError, "unverified"):
            pp.log_row({**self.ok, "data_status": "unverified"}, self.path)
        self.assertFalse(self.path.exists())

    def test_high_confidence_needs_three_confirmations(self):
        with self.assertRaisesRegex(ValueError, "3 independent"):
            pp.log_row({**self.ok, "confidence": "high", "confirmations": 2}, self.path)
        pp.log_row({**self.ok, "confidence": "high", "confirmations": 3}, self.path)
        self.assertEqual(self.rows()[0]["confidence"], "high")

    def test_rejects_bad_fields(self):
        for patch in ({"verdict": "Buy"}, {"confidence": "certain"}, {"probability": 1.2}, {"reference_price": 0},
                      {"review_date": "2026-10-24"}, {"review_date": "next year"}, {"resolution_rule": " "}):
            with self.assertRaises(ValueError, msg=str(patch)):
                pp.log_row({**self.ok, **patch}, self.path)

    def test_identifiers_are_scrubbed_from_free_text(self):
        pp.log_row({**self.ok, "resolution_rule": "acct 0123456789012345 above 600"}, self.path)
        self.assertNotIn("0123456789012345", self.path.read_text(encoding="utf-8"))

    def test_refuses_a_log_with_a_different_header(self):
        self.path.write_text("a,b,c\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "different header"):
            pp.log_row(self.ok, self.path)

    def test_env_var_redirects_the_log(self):
        os.environ["NEPSE_DECISION_LOG"] = str(self.path)
        try:
            self.assertEqual(pp.log_path(), self.path)
        finally:
            del os.environ["NEPSE_DECISION_LOG"]


if __name__ == "__main__":
    unittest.main()
