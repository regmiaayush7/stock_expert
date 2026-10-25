import datetime as dt, sys, unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import costs

R = costs.load_rates()
d = dt.date.fromisoformat
TODAY = d("2026-10-24")  # inside the rates' verification window


def run(price, buy, sell="2026-10-24", kitta=100, wacc=500):
    return costs.analyse(kitta, wacc, price, d(sell), d(buy) if buy else None, R, today=TODAY)


class Commission(unittest.TestCase):
    def test_slab_edges_belong_to_the_lower_slab(self):
        self.assertEqual(costs.commission(D(50000), R), D("180.00"))     # 0.36% at exactly 50,000
        self.assertEqual(costs.commission(D("50000.01"), R), D("165.00"))  # 0.33% above it, whole amount
        self.assertEqual(costs.commission(D(500000), R), D("1650.00"))
        self.assertEqual(costs.commission(D(500001), R), D("1550.00"))     # 0.31% on the whole amount (500,001 x 0.0031)

    def test_minimum_commission(self):
        self.assertEqual(costs.commission(D(100), R), D("10.00"))

    def test_top_slab(self):
        self.assertEqual(costs.commission(D(20000000), R), D("48000.00"))


class RatePeriods(unittest.TestCase):
    def pick(self, day):
        p = costs.rate_period(R, d(day))
        return p["long_pct"], p["short_pct"]

    def test_periods_by_sale_date(self):
        self.assertEqual(self.pick("2025-08-01"), (5.0, 7.5))
        self.assertEqual(self.pick("2026-07-16"), (5.0, 7.5))
        self.assertEqual(self.pick("2026-07-17"), (7.5, 10.0))
        self.assertEqual(self.pick("2026-09-21"), (7.5, 10.0))
        self.assertEqual(self.pick("2026-09-22"), (3.75, 5.0))
        self.assertEqual(self.pick("2026-10-24"), (3.75, 5.0))


class SellLongTermGain(unittest.TestCase):
    """100 kitta, WACC 500, sold at 547: value 54,700 in the 0.33% slab."""

    def test_hand_computed_figures(self):
        r = run(547, "2025-01-14")
        self.assertEqual((r["term"], r["cgt_rate_pct"]), ("long", 3.75))
        self.assertEqual(r["gross_proceeds"], 54700.00)
        self.assertEqual(r["commission"], 180.51)    # 54,700 x 0.0033
        self.assertEqual(r["sebon_fee"], 8.21)       # 8.205 rounds half up
        self.assertEqual(r["dp_charge"], 25.0)
        self.assertEqual(r["taxable_gain"], 4700.00)
        self.assertEqual(r["cgt"], 176.25)           # 4,700 x 3.75%
        self.assertEqual(r["net_proceeds"], 54310.03)
        self.assertEqual(r["net_pl"], 4310.03)
        self.assertEqual(r["tax_if_sale_costs_deductible"], 168.24)  # (4,700 - 213.72) x 3.75% = 168.2355
        self.assertNotIn("wait_comparison", r)

    def test_break_even_is_the_first_tick_with_non_negative_net(self):
        r = run(547, "2025-01-14")
        be = D(str(r["break_even_price_net_of_costs_and_tax"]))
        self.assertEqual(be, D("502.1"))
        n = lambda p: costs.net_sale(100, D(500), p, 3.75, R)["net_pl"]
        self.assertGreaterEqual(n(be), 0)
        self.assertLess(n(be - D("0.1")), 0)


class SellShortTermGain(unittest.TestCase):
    def test_short_rate_and_wait_comparison(self):
        r = run(547, "2026-03-01")
        self.assertEqual((r["term"], r["cgt_rate_pct"]), ("short", 5.0))
        self.assertEqual(r["cgt"], 235.00)
        self.assertEqual(r["net_proceeds"], 54251.28)
        w = r["wait_comparison"]
        self.assertEqual(w["long_term_from"], "2027-03-02")
        self.assertEqual(w["tax_saving_if_price_unchanged"], 58.75)  # 4,700 x (5% - 3.75%)
        floor = D(str(w["waiting_beats_selling_now_if_price_on_that_date_is_at_least"]))
        long_net = lambda p: costs.net_sale(100, D(500), p, 3.75, R)["net_proceeds"]
        self.assertGreaterEqual(long_net(floor), D("54251.28"))
        self.assertLess(long_net(floor - D("0.1")), D("54251.28"))
        self.assertLess(w["max_fall_pct_to_still_break_even"], 0.25)  # the tax saving is worth only a tiny price move

    def test_day_count_365_is_short_366_is_long(self):
        self.assertEqual(run(547, "2025-10-24")["term"], "short")   # exactly 365 days
        self.assertEqual(run(547, "2025-10-23")["term"], "long")    # 366 days


class SellAtALoss(unittest.TestCase):
    def test_no_tax_and_negative_result(self):
        r = run(450, "2026-03-01")
        self.assertEqual((r["cgt"], r["taxable_gain"]), (0.0, 0.0))
        self.assertEqual(r["net_proceeds"], 44806.25)  # 45,000 - 162.00 - 6.75 - 25
        self.assertEqual(r["net_pl"], -5193.75)
        self.assertEqual(r["wait_comparison"]["waiting_beats_selling_now_if_price_on_that_date_is_at_least"], None)


class Guards(unittest.TestCase):
    def test_missing_buy_date_uses_the_higher_rate_and_says_so(self):
        r = run(547, None)
        self.assertEqual(r["cgt_rate_pct"], 5.0)
        self.assertIn("unknown", r["term"])

    def test_stale_rates_downgrade_status(self):
        r = costs.analyse(100, 500, 547, d("2026-10-24"), d("2025-01-14"), R, today=d("2026-12-31"))
        self.assertEqual(r["status"], "unverified")
        self.assertTrue(r["rates_verified"]["stale"])

    def test_fresh_rates_are_ok(self):
        self.assertEqual(run(547, "2025-01-14")["status"], "ok")

    def test_old_sale_date_uses_old_rates(self):
        r = costs.analyse(100, 500, 547, d("2026-08-01"), d("2025-01-14"), R, today=TODAY)
        self.assertEqual(r["cgt_rate_pct"], 7.5)

    def test_cli_rejects_bad_input(self):
        self.assertEqual(costs.main(["sell", "--kitta", "0", "--wacc", "500", "--price", "547"]), 2)
        self.assertEqual(costs.main(["sell", "--kitta", "1", "--wacc", "5", "--price", "5", "--buy-date", "2030-01-01",
                                     "--sell-date", "2026-10-24"]), 2)


if __name__ == "__main__":
    unittest.main()
