"""Power analysis 1g: prev with ship power propagation from ship_power_propagation modifiers.
Rule tested: each downstream node contributes fx((province_power + spp * ship_power) / 5) if that reaches the
threshold 2; spp = 0.25 if the country has >= 4 maritime ideas (grand_navy, common/ideas/00_basic_ideas.txt) else 0.
Run from backend/: .venv/bin/python scripts/research/power_prop_maritime.py"""
import io, re, sys, zipfile
from collections import Counter
from pathlib import Path
sys.path.insert(0, ".")
from app.trade import corpus, calc, game_data
g = game_data.graph(); fx = calc.rule_fx


def spp_by_country(path):
    raw = open(path, "rb").read()
    if raw[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(raw)); raw = z.read(z.namelist()[0])
    t = raw.decode("latin-1"); c0 = t.index("\ncountries={"); out = {}
    for m in re.finditer(r"\n\t([A-Z0-9]{3})=\{", t[c0:]):
        s = c0 + m.start(); e = t.find("\n\t}", s); b = t[s:e]
        ig = re.search(r"\n\t\tactive_idea_groups=\{(.*?)\n\t\t\}", b, re.S)
        mar = re.search(r"maritime_ideas=(\d+)", ig.group(1)) if ig else None
        out[m.group(1)] = 0.25 if mar and int(mar.group(1)) >= 4 else 0.0
    return out


res = Counter(); left = Counter(); ex = []; nsaves = 0
for entry in corpus.selected():
    for _e, world in corpus.iter_worlds([entry]):
        nsaves += 1
        spp = spp_by_country(corpus.locate(entry, Path("/tmp/locx")))
        inp, rec = world.inputs, world.recorded
        era = "1444-45" if inp.date < "1450" else "later"
        for (node, tag), r in rec.entries.items():
            downs = g.outgoing(node) if node in g else []
            es = [inp.entries.get((d, tag)) for d in downs]
            got = r.prev or 0.0
            base = sum(fx(e.province_power / 5) for e in es if e and e.province_power / 5 >= 2)
            f = spp.get(tag, 0.0)
            new = sum(fx(v / 5) for v in (e.province_power + f * e.ship_power for e in es if e) if v / 5 >= 2)
            ok = lambda x: abs(x - got) <= max(0.002, 0.05 * abs(got))
            ex_ = lambda x: abs(x - got) <= 0.0005
            res[(era, "checks")] += 1
            res[(era, "base within 5%")] += ok(base); res[(era, "maritime within 5%")] += ok(new)
            res[(era, "base exact")] += ex_(base); res[(era, "maritime exact")] += ex_(new)
            if not ok(new):
                kind = "rec 0, pred > 0" if got == 0 else ("rec > pred" if got > new else "rec < pred")
                left[(era, kind)] += 1
                if len(ex) < 10: ex.append((entry["id"], inp.date, node, tag, round(new, 3), got, f))
print("saves", nsaves)
for k in sorted(res): print(k, res[k])
print(left)
for x in ex: print(x)
