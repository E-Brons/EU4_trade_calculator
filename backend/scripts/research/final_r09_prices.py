"""R09 final: extract the top-level change_price block (current_price per good, in block order) of every corpus save
with a regex (own code), and warm the provinces cache of the saves that lack one. Output: /tmp/eu4research/final_r09/change_price.json"""
import sys, re, json, os
sys.path.insert(0, "scripts/research")
import final_r09_load as L
from app.trade import savefile
out = "/tmp/eu4research/final_r09/change_price.json"
cp = json.load(open(out)) if os.path.exists(out) else {}
for sid in L.IDS:
    if sid not in cp:
        t = common_text = L.common._text(L.ENT[sid])
        raw = savefile.extract_top_level_block(t.gamestate, "change_price")
        items = re.findall(r"(\w+)=\{\s*(?:[^{}]*?)current_price=(-?[0-9.]+)", raw)
        # keys inside a good block are not nested braces: take key names at depth 1 by a small scanner
        goods, depth, i, cur = [], 0, 0, ""
        body = raw[1:-1]
        names = []
        for m in re.finditer(r"([A-Za-z_0-9]+)=\{|\}", body):
            if m.group(0) == "}":
                depth -= 1
            else:
                if depth == 0: names.append((m.group(1), m.end()))
                depth += 1
        res = []
        for k, (name, pos) in enumerate(names):
            end = names[k + 1][1] - len(names[k + 1][0]) - 2 if k + 1 < len(names) else len(body)
            m = re.search(r"current_price=(-?[0-9.]+)", body[pos:end])
            res.append((name, float(m.group(1)) if m else None))
        cp[sid] = res
        json.dump(cp, open(out, "w"))
        print(sid, len(res), flush=True)
# provinces for all saves
for sid in L.IDS:
    L.provinces(sid); print("prov", sid, flush=True)
