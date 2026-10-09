import sys, json
sys.path.insert(0, "scripts/research")
import u06_load as L
order = ["S79","S80","U03","U04","U05","U06"]
for s in order:
    t = L.tur(s)
    print(s, L.meta_date(s), "tech", t.get("technology"), "inst", t.get("institutions"), "merch", len([m for m in (t.get("merchants") or {}).get("envoy", [])]) if isinstance(t.get("merchants"), dict) else t.get("merchants"),
          "mercantilism", t.get("mercantilism"), "idea_groups", t.get("active_idea_groups"), "gov_reform_prog", t.get("government_reform_progress"),
          "estimated_income", t.get("estimated_monthly_income"), "trade_mission", t.get("trade_mission"), "nps", t.get("num_ships_protecting_trade"))
print()
for s in order:
    t = L.tur(s)
    print(s, "reforms", t.get("government"), {k: t.get(k) for k in ("government_rank","government_name")}, "keys with modifier/policy:", [k for k in t if "modif" in k or "polic" in k or "reform" in k])
