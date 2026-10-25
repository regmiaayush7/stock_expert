import datetime as dt, json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import fetch_data as fd

D = "2026-10-16"


class CrossCheck(unittest.TestCase):
    def test_all_agree(self):
        r = fd.cross_check({"a": (D, 547.0), "b": (D, 547), "c": (D, 547.0)})
        self.assertTrue(r["verified"]); self.assertEqual(r["outliers"], [])

    def test_corrupted_source_is_flagged_not_averaged(self):
        r = fd.cross_check({"a": (D, 547.0), "b": (D, 601.7), "c": (D, 547.0)})
        self.assertTrue(r["verified"]); self.assertEqual(r["outliers"], ["b"]); self.assertEqual(r["agree"], ["a", "c"])

    def test_stale_date_is_an_outlier(self):
        r = fd.cross_check({"a": (D, 547.0), "b": ("2026-10-15", 546.0), "c": (D, 547.0)})
        self.assertEqual(r["outliers"], ["b"])

    def test_two_sources_disagree_is_unverified(self):
        r = fd.cross_check({"a": (D, 547.0), "b": (D, 560.0)})
        self.assertFalse(r["verified"]); self.assertEqual(r["agree"], [])

    def test_single_source_is_unverified(self):
        self.assertFalse(fd.cross_check({"a": (D, 547.0)})["verified"])


class Freshness(unittest.TestCase):
    d = dt.date.fromisoformat

    def test_symbol_behind_market(self):
        self.assertTrue(fd.stale_label(self.d("2026-09-01"), self.d("2026-10-24"), self.d("2026-10-16")).startswith("STALE"))

    def test_market_closed(self):
        self.assertTrue(fd.stale_label(self.d("2026-10-16"), self.d("2026-10-24"), self.d("2026-10-16")).startswith("Market quiet"))

    def test_fresh(self):
        self.assertEqual(fd.stale_label(self.d("2026-10-16"), self.d("2026-10-18"), self.d("2026-10-16")), "fresh")


class Parsers(unittest.TestCase):
    MERO = """<tr><th class="td-icon"><span>#</span></th><th>Junk</th></tr>
    <tr><th style="w">Sector
    </th><td class="x">  Hydro Power </td></tr>
    <tr><th>Market Price</th><td><strong><span>259.70</span></strong></td></tr>
    <tr><th>EPS</th><td>-0.93 <span>(FY:082-083, Q:4)</span></td></tr>
    <tr><th>Sector</th><td>SHOULD NOT OVERWRITE</td></tr>"""
    SS = """As on: <span
 class="text-org">2026-10-16</span> <span class="text-org">Ltp:</span>
 547.00</span> <span class="text-org">52 Week High-Low :
 </span>581.00 - 485.00 <h4>Sector: <span class="text-org">Commercial Bank</span></h4>
 <td class="text-bold">Listed Shares</td> <td class="text-bold">
 284,098,483.00 units</td> <td class="text-bold">Paid Up</td> <td class="text-bold">
 Rs.
 100.00</td>"""

    def test_mero_page(self):
        r = fd.mero_page(self.MERO)
        self.assertEqual((r["sector"], r["market_price"], r["eps"], r["eps_period"]), ("Hydro Power", 259.7, -0.93, "FY:082-083, Q:4"))

    def test_ss_page(self):
        r = fd.ss_page(self.SS)
        self.assertEqual((r["as_on"], r["ltp"], r["listed_shares"], r["paid_up_per_share"], r["sector"]),
                         ("2026-10-16", 547.0, 284098483.0, 100.0, "Commercial Bank"))

    def test_udf_bars_uses_utc_date_and_rejects_empty(self):
        j = {"t": [1760906694], "o": [1], "h": [2], "l": [0.5], "c": [1.5], "v": [10]}
        self.assertEqual(fd.udf_bars(j), {"2025-10-19": [1, 2, 0.5, 1.5, 10]})
        with self.assertRaises(fd.FetchError):
            fd.udf_bars({"s": "no_data"})


class Cache(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = fd.CACHE
        fd.CACHE = Path(self.tmp.name)

    def tearDown(self):
        fd.CACHE = self.old
        self.tmp.cleanup()

    @staticmethod
    def down():
        raise fd.FetchError("offline")

    def test_offline_with_cache_returns_stale_cache(self):
        fd.cached("price", "X", lambda: {"v": 1})
        data, _, origin = fd.cached("price", "X", self.down, refresh=True)
        self.assertEqual((data, origin), ({"v": 1}, "stale-cache"))

    def test_offline_without_cache_raises_instead_of_guessing(self):
        with self.assertRaises(fd.FetchError):
            fd.cached("price", "Y", self.down)

    def test_corrupt_cache_file_is_treated_as_missing(self):
        (Path(self.tmp.name) / "price_C.json").write_text('{"epoch": 1, "da', encoding="utf-8")  # half-written by a parallel run
        data, _, origin = fd.cached("price", "C", lambda: {"v": 3})
        self.assertEqual((data, origin), ({"v": 3}, "live"))
        with self.assertRaises(fd.FetchError):
            (Path(self.tmp.name) / "price_D.json").write_text("not json", encoding="utf-8")
            fd.cached("price", "D", self.down)

    def test_fresh_cache_skips_network(self):
        fd.cached("price", "Z", lambda: {"v": 2})
        data, _, origin = fd.cached("price", "Z", self.down)
        self.assertEqual((data, origin), ({"v": 2}, "cache"))


if __name__ == "__main__":
    unittest.main()
