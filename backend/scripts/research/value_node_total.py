"""Value/flow (2026-10-08), R10: node `total` vs the sum of the entries' `val` (all clean dataset saves, integer
thousandths). Classifies the differences. Run from backend/: .venv/bin/python scripts/research/value_node_total.py"""
from __future__ import annotations

import re
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TAG = re.compile(r"\n\t\t([A-Z0-9]{3})=\{(.*?)\n\t\t\}", re.S)
c = Counter(); ex = []
for z in sorted((ROOT / "datasets").glob("eu4/1.37.5/vanilla/*/*/U*.zip")):
    t = zipfile.ZipFile(z).read(zipfile.ZipFile(z).namelist()[0]).decode("latin-1")
    tr = t.index("\ntrade={"); te = t.index("\n}\n", tr)
    for m in re.finditer(r'\n\t\tdefinitions="(\w+)"', t[tr:te]):
        s = tr + m.start(); e = t.find("\n\t}", s); b = t[s:e]
        tot = re.search(r"\n\t\ttotal=([-\d.]+)", b)
        if not tot:
            continue
        vals = [round(float(v) * 1000) for _tag, body in TAG.findall(b) for v in re.findall(r"\n\t\t\tval=([-\d.]+)", body)]
        neg = sum(1 for v in vals if v < 0)
        d = round(float(tot.group(1)) * 1000) - sum(vals)
        c["nodes"] += 1
        if d == 0:
            c["total == sum(val)"] += 1
        else:
            k = "differs, " + ("< 0.01" if abs(d) <= 10 else "larger")
            c[k] += 1
            if len(ex) < 6 and abs(d) > 10:
                ex.append((z.name[:22], m.group(1), "total", tot.group(1), "sum val", sum(vals) / 1000, "diff", d / 1000))
print(dict(c))
for x in ex:
    print(x)


def explain():
    """Candidates for total - sum(val) > 0: sum(t_in), sum(t_out), power of countries in top_power without an entry,
    sum of max_pow*max_demand of entries that store no val."""
    hit = Counter()
    for z in sorted((ROOT / "datasets").glob("eu4/1.37.5/vanilla/*/*/U*.zip")):
        t = zipfile.ZipFile(z).read(zipfile.ZipFile(z).namelist()[0]).decode("latin-1")
        tr = t.index("\ntrade={"); te = t.index("\n}\n", tr)
        for m in re.finditer(r'\n\t\tdefinitions="(\w+)"', t[tr:te]):
            s = tr + m.start(); e = t.find("\n\t}", s); b = t[s:e]
            tot = re.search(r"\n\t\ttotal=([-\d.]+)", b)
            if not tot:
                continue
            ents = TAG.findall(b)
            f = lambda body, k: float(x.group(1)) if (x := re.search(rf"\n\t\t\t{k}=([-\d.]+)", body)) else 0.0
            sv = sum(round(f(bd, "val") * 1000) for _t, bd in ents)
            d = round(float(tot.group(1)) * 1000) - sv
            if d == 0:
                continue
            hit["nodes with d>0"] += 1
            tin = sum(round(f(bd, "t_in") * 1000) for _t, bd in ents)
            tout = sum(round(f(bd, "t_out") * 1000) for _t, bd in ents)
            noval = sum(round(f(bd, "max_pow") * f(bd, "max_demand") * 1000) for _t, bd in ents if "\n\t\t\tval=" not in bd and f(bd, "max_pow") > 0)
            tp = re.search(r"\n\t\ttop_power=\{([^}]*)\}", b); tpv = re.search(r"\n\t\ttop_power_values=\{([^}]*)\}", b)
            present = {tg for tg, _ in ents}
            ghost = 0
            if tp and tpv:
                for tg, v in zip(tp.group(1).split(), tpv.group(1).split()):
                    if tg.strip('"') not in present:
                        ghost += round(float(v) * 1000)
            for name, v in (("= sum t_in", tin), ("= sum t_out", tout), ("= no-val entries power", noval), ("= top_power without entry", ghost)):
                hit[name] += abs(v - d) <= 2
            if abs(tin - d) > 2 and abs(noval - d) > 2 and abs(ghost - d) > 2 and hit["examples"] < 5:
                hit["examples"] += 1; print("unexplained", z.name[:20], m.group(1), d, "t_in", tin, "t_out", tout, "noval", noval, "ghost", ghost)
    print(dict(hit))


if __name__ == "__main__":
    explain()
