"""Value/flow (2026-10-08), R10: pirate power in a node. Nodes with pirates carry collector_power_including_pirates /
num_collectors_including_pirates instead of collector_power / num_collectors. Test:
  pirates = total - sum(val);  retain_power == sum(collector effective power) + pirates;  num_collectors_including_pirates
  == collectors + 1. Run from backend/: .venv/bin/python scripts/research/value_pirates.py"""
from __future__ import annotations

import re
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TAG = re.compile(r"\n\t\t([A-Z0-9]{3})=\{(.*?)\n\t\t\}", re.S)
c = Counter(); ex = []


def f(body, k):
    x = re.search(rf"\n\t+{k}=([-\d.]+)", body)
    return round(float(x.group(1)) * 1000) if x else 0


for z in sorted((ROOT / "datasets").glob("eu4/1.37.5/vanilla/*/*/U*.zip")):
    t = zipfile.ZipFile(z).read(zipfile.ZipFile(z).namelist()[0]).decode("latin-1")
    tr = t.index("\ntrade={"); te = t.index("\n}\n", tr)
    for m in re.finditer(r'\n\t\tdefinitions="(\w+)"', t[tr:te]):
        s = tr + m.start(); e = t.find("\n\t}", s); b = t[s:e]
        node_part = TAG.sub("", b)
        has_pir = "collector_power_including_pirates=" in node_part
        ents = TAG.findall(b)
        sv = sum(f(bd, "val") for _t, bd in ents)
        tot = f(node_part, "total")
        if not has_pir:
            c["nodes without pirate keys"] += 1; c["  of them total == sum(val)"] += (tot == sv) or "total=" not in node_part; continue
        c["nodes with pirate keys"] += 1
        pir = tot - sv
        c["  pirates = total - sum(val) > 0"] += pir > 0
        coll = [bd for _t, bd in ents if "\n\t\t\ttotal=" in bd or "has_capital=yes" in bd]
        eff = sum(f(bd, "val") - f(bd, "t_out") + f(bd, "t_in") for bd in coll)
        rp = f(node_part, "retain_power"); cpp = f(node_part, "collector_power_including_pirates")
        c["  retain_power == sum collector eff + pirates"] += abs(rp - (eff + pir)) <= 2
        c["  retain_power == collector_power_including_pirates"] += rp == cpp
        ncp = re.search(r"\n\t\tnum_collectors_including_pirates=(\d+)", node_part)
        c["  num_collectors_including_pirates == collectors + 1"] += bool(ncp) and int(ncp.group(1)) == len(coll) + 1
        if len(ex) < 4:
            ex.append((z.name[:20], m.group(1), "pirates", pir / 1000, "retain", rp / 1000, "collector eff", eff / 1000, "n", ncp.group(1) if ncp else None, len(coll)))
print(dict(c))
for x in ex:
    print(x)
