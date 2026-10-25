import sys, json
sys.path.insert(0, r"C:\Users\HP\.claude\skills\nepse-expert\scripts")
import fetch_data as f
sym = sys.argv[1]
_, cid, tok = f.ss_open(sym)
rows = []
start = 0
while True:
    r = f.http("POST", "https://www.sharesansar.com/company-price-history",
               data={"draw": 1, "start": start, "length": 50, "company": cid},
               headers={"X-CSRF-Token": tok, "X-Requested-With": "XMLHttpRequest",
                        "Referer": f"https://www.sharesansar.com/company/{sym.lower()}"})
    j = r.json()
    d = j.get("data", [])
    if not d: break
    rows += d
    start += len(d)
    if rows[-1]["published_date"] < "2019-05-01": break
print(len(rows), "total", j.get("recordsTotal"), file=sys.stderr)
json.dump(rows, open(sys.argv[2], "w"))
print(rows[0]["published_date"], rows[-1]["published_date"])
