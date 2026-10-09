"""R02 final: colonial-nation tags (C00-C17) with a trade_port: do they have a has_capital entry, and what do the ones without have?"""
import re, sys
from collections import Counter
sys.path.insert(0, "scripts/research")
import common
cnt = Counter()
for e in common.entries():
    if e["id"] in ("U01", "U02"):
        continue
    countries = common.block(e, "countries")
    rows = {}
    for nd in common.nodes(e):
        for tag, en in nd.items():
            if isinstance(en, dict) and re.fullmatch(r"C\d\d", tag) and "max_demand" in en:
                rows.setdefault(tag, []).append(en)
    for tag, c in countries.items():
        if not (re.fullmatch(r"C\d\d", tag) and isinstance(c, dict) and "trade_port" in c):
            continue
        es = rows.get(tag, [])
        hc = any(x.get("has_capital") for x in es)
        active = any(set(x) - {"max_demand"} for x in es)   # some data beyond the bare multiplier
        cnt[("has_capital entry" if hc else "no has_capital entry", "has data entries" if active else "only bare max_demand stubs or none")] += 1
        if not hc and active:
            cnt["no_hc_but_active_examples"] += 1
print(dict(cnt))
