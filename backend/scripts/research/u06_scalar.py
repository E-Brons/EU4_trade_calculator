import sys
sys.path.insert(0, "scripts/research")
import u06_load as L
order = ["S79","S80","U03","U04","U05","U06"]
keys = ["prestige","current_power_projection","mercantilism","absolutism","legitimacy","government_rank","army_tradition","navy_tradition","inflation","great_power_score","average_autonomy","development","num_ships_protecting_trade","trade_mission","treasury"]
md = {}
for s in order:
    for n in L.nodes(s):
        if n["definitions"] == "hormuz" and isinstance(n.get("TUR"), dict):
            md[s] = float(n["TUR"]["max_demand"])
print("save  md_hormuz |", " ".join(k[:12].rjust(12) for k in keys))
for s in order:
    t = L.tur(s)
    print(s, str(md[s]).ljust(8), "|", " ".join(str(t.get(k))[:12].rjust(12) for k in keys))
