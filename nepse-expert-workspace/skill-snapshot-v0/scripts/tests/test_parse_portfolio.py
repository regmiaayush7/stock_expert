import json, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import parse_portfolio as pp

KNOWN = {"NABIL", "NHPC", "NICA", "UPPER", "SHL"}
D = "2025-01-14"


def row(sym, kitta, wacc, ltp, pl, **kw):
    return {"symbol": sym, "kitta": kitta, "wacc": wacc, "ltp": ltp, "pl": pl, "purchase_date": D, **kw}


class Clean(unittest.TestCase):
    def test_consistent_rows_need_nothing(self):
        doc = {"source_app": "TMS", "rows": [row("NABIL", 100, 500.0, 547.0, 4700.0), row("nhpc", 200, 250.0, 259.7, 1940.0)]}
        rep = pp.parse(doc, KNOWN)
        self.assertFalse(any(r["needs_user"] for r in rep["rows"]))
        self.assertEqual(rep["rows"][1]["symbol"], "NHPC")
        self.assertEqual(rep["totals_ready_rows"], {"count": 2, "cost": 100000.0, "value_at_screen_ltp": 106640.0,
                                                    "note": rep["totals_ready_rows"]["note"]})
        self.assertFalse(rep["confirmed"])  # the confirmation gate is never pre-filled

    def test_table_has_a_row_per_holding(self):
        rep = pp.parse({"rows": [row("NABIL", 100, 500.0, 547.0, 4700.0)]}, KNOWN)
        self.assertEqual(len(pp.table_markdown(rep).splitlines()), 3)


class Cropped(unittest.TestCase):
    def test_missing_cost_is_listed_not_invented(self):
        rep = pp.parse({"rows": [row("NABIL", 100, None, 547.0, None)]}, KNOWN)
        r = rep["rows"][0]
        self.assertEqual(r["unreadable"], ["wacc"])
        self.assertTrue(r["needs_user"])
        self.assertEqual(rep["totals_ready_rows"]["count"], 0)

    def test_truncated_symbol_gets_a_suggestion_only(self):
        r = pp.parse({"rows": [row("NHP", 10, 100.0, 120.0, 200.0)]}, KNOWN)["rows"][0]
        self.assertTrue(r["needs_user"])
        self.assertIn("NHPC", " ".join(r["flags"]))
        self.assertEqual(r["symbol"], "NHP")  # never silently replaced

    def test_row_with_nothing_readable(self):
        r = pp.parse({"rows": [{"symbol": None, "kitta": None, "wacc": None}]}, KNOWN)["rows"][0]
        self.assertEqual(r["unreadable"], ["kitta", "symbol", "wacc"])


class Blurry(unittest.TestCase):
    def test_letter_in_number_is_unreadable(self):
        r = pp.parse({"rows": [row("NABIL", "1O0", 500.0, 547.0, 4700.0)]}, KNOWN)["rows"][0]
        self.assertIn("kitta", r["unreadable"])
        self.assertIsNone(r["kitta"])

    def test_misread_digit_breaks_the_pl_check(self):
        r = pp.parse({"rows": [row("NABIL", 100, 500.0, 54.7, 4700.0)]}, KNOWN)["rows"][0]
        self.assertTrue(any("P/L on screen" in f for f in r["flags"]))
        self.assertTrue(r["needs_user"])

    def test_identifiers_never_reach_the_output(self):
        doc = {"source_app": "MeroShare 0123456789012345",
               "rows": [row("NABIL", 100, 500.0, 547.0, 4700.0, note="acct 0123456789012345 mail a.b@mail.com ph +977 9841234567")]}
        out = json.dumps(pp.parse(doc, KNOWN))
        for leak in ("0123456789012345", "a.b@mail.com", "9841234567"):
            self.assertNotIn(leak, out)
        self.assertIn("[removed]", out)

    def test_unknown_keys_are_dropped(self):
        rep = pp.parse({"rows": [dict(row("NABIL", 100, 500.0, 547.0, 4700.0), owner="Some Name", boid="1234")]}, KNOWN)
        self.assertNotIn("owner", rep["rows"][0]); self.assertNotIn("boid", rep["rows"][0])


class Shape(unittest.TestCase):
    def test_duplicate_symbol_is_flagged_not_merged(self):
        rep = pp.parse({"rows": [row("NABIL", 100, 500.0, 547.0, 4700.0), row("NABIL", 50, 520.0, 547.0, 1350.0)]}, KNOWN)
        self.assertEqual(len(rep["rows"]), 2)
        self.assertTrue(all(r["needs_user"] for r in rep["rows"]))

    def test_fractional_and_negative_kitta(self):
        for bad in (10.5, -3, 0):
            r = pp.parse({"rows": [row("NABIL", bad, 500.0, 547.0, None)]}, KNOWN)["rows"][0]
            self.assertIn("kitta", r["unreadable"])

    def test_thousands_separator_and_rs_prefix(self):
        r = pp.parse({"rows": [row("NABIL", "1,000", "Rs. 500.00", "547", "47,000")]}, KNOWN)["rows"][0]
        self.assertEqual((r["kitta"], r["wacc"], r["ltp"], r["pl"]), (1000, 500.0, 547.0, 47000.0))
        self.assertFalse(r["needs_user"])

    def test_missing_purchase_date_is_info_not_a_blocker(self):
        r = pp.parse({"rows": [dict(row("NABIL", 100, 500.0, 547.0, 4700.0), purchase_date=None)]}, KNOWN)["rows"][0]
        self.assertFalse(r["needs_user"])
        self.assertTrue(any("purchase date" in f for f in r["flags"]))

    def test_bad_date_blocks(self):
        r = pp.parse({"rows": [dict(row("NABIL", 100, 500.0, 547.0, 4700.0), purchase_date="14/01/25")]}, KNOWN)["rows"][0]
        self.assertTrue(r["needs_user"])

    def test_bikram_sambat_date_is_converted(self):
        try:
            import nepali_datetime  # noqa: F401
        except ImportError:
            self.skipTest("nepali_datetime not installed")
        r = pp.parse({"rows": [dict(row("NABIL", 100, 500.0, 547.0, 4700.0), purchase_date="2082-05-12")]}, KNOWN)["rows"][0]
        self.assertTrue(r["purchase_date"].startswith("2025-"), r["purchase_date"])

    def test_empty_input_is_rejected(self):
        for bad in ({}, {"rows": []}, []):
            with self.assertRaises(ValueError):
                pp.parse(bad, KNOWN)

    def test_offline_symbol_check_is_declared(self):
        self.assertFalse(pp.parse({"rows": [row("NABIL", 100, 500.0, 547.0, 4700.0)]}, None)["symbol_list_checked"])


if __name__ == "__main__":
    unittest.main()
