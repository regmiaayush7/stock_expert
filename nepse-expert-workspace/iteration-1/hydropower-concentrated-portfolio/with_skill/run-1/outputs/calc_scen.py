import sys, datetime as dt, json
sys.path.insert(0, r"C:\Users\HP\Desktop\Stock_Agent\nepse-expert-workspace\iteration-1\hydropower-concentrated-portfolio\with_skill\run-1\outputs\skillcopy\scripts")
import costs
rates = costs.load_rates()
today = dt.date(2026,10,24); hz = dt.date(2027,10,24); buy = dt.date(2025,10,23)
H = 0.083  # hurdle: 4.55% top FD less 5% tax (~4.3%) + 4 pt premium; partly unverified
H_ = {
 "NHPC":  (2000,210,259.7,[(330,.25),(255,.45),(170,.30)],0.0),
 "UPPER": (1500,240,193.0,[(235,.25),(195,.45),(150,.30)],0.0),
 "CHCL":  (500,300,336.7,[(420,.20),(340,.45),(250,.35)],2.0*0.95),
 "AKJCL": (1000,330,346.0,[(430,.25),(340,.45),(250,.30)],0.0),
 "NABIL": (300,520,547.0,[(640,.25),(565,.50),(480,.25)],10.8*0.95),
 "NICA":  (200,350,320.9,[(400,.20),(320,.50),(260,.30)],0.0),
}
out = {}
for s,(k,w,p,sc,div) in H_.items():
    now = costs.analyse(k,w,p,today,buy,rates,today=today)
    net_now_ps = float(now["net_proceeds"])/k
    ev_net = 0; rows=[]
    for price,pr in sc:
        r = costs.analyse(k,w,price,hz,buy,rates,today=hz)
        nps = float(r["net_proceeds"])/k
        ev_net += pr*nps
        rows.append((price,pr,round(nps,1)))
    hold = ev_net + div
    sell_now = net_now_ps*(1+H)
    hold_ret = (hold/net_now_ps-1)*100
    ev_gross = sum(pr*price for price,pr in sc)
    out[s] = dict(net_now_ps=round(net_now_ps,2), ev_gross=round(ev_gross,1), ev_net=round(ev_net,1), div_ps=round(div,2),
                  hold_value=round(hold,1), sell_now_compounded=round(sell_now,1), hold_ret_pct=round(hold_ret,1),
                  gap_pts=round(hold_ret - H*100,1), rows=rows, be=now["break_even_price_net_of_costs_and_tax"],
                  net_pl=now["net_pl"], cgt=now["cgt"], net_proceeds=now["net_proceeds"])
    print(s, json.dumps(out[s]))
# trim sizes
for s,k,w,p in [("NHPC",800,210,259.7),("AKJCL",100,330,346.0),("UPPER",500,240,193.0),("CHCL",150,300,336.7),("NICA",200,350,320.9),("NHPC",2000,210,259.7)]:
    r = costs.analyse(k,w,p,today,buy,rates,today=today)
    print("TRIM",s,k,"gross",r["gross_proceeds"],"comm",r["commission"],"sebon",r["sebon_fee"],"dp",r["dp_charge"],"cgt",r["cgt"],"net",r["net_proceeds"],"be",r["break_even_price_net_of_costs_and_tax"])
