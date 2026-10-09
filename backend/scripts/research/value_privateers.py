"""Value/flow (2026-10-08), R10: privateers in the node block. pirate power = collector_power_including_pirates -
collector_power; does it enter retention (retain/(retain+pull)) or the collectors' shares (power_fraction)?
Run from backend/: .venv/bin/python scripts/research/value_privateers.py"""
from __future__ import annotations

import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
c = Counter(); ex = []
for z in sorted((ROOT / "datasets").glob("eu4/1.37.5/vanilla/*/*/U*.zip")):
    t = zipfile.ZipFile(z).read(zipfile.ZipFile(z).namelist()[0]).decode("latin-1")
    tr = t.index("\ntrade={"); te = t.index("\n}\n", tr)
    for m in re.finditer(r'\n\t\tdefinitions="(\w+)"', t[tr:te]):
        s = tr + m.start(); e = t.find("\n\t}", s); b = t[s:e]
        head = b.split("\n\t\t", 1)[1] if False else b
        g = lambda k: (float(x.group(1)) if (x := re.search(rf"\n\t\t{k}=([-\d.]+)", b)) else None)
        cp, cpp, rp, pp, ret = g("collector_power"), g("collector_power_including_pirates"), g("retain_power"), g("pull_power"), g("retention")
        nc, ncp = g("num_collectors"), g("num_collectors_including_pirates")
        if cp is None or cpp is None:
            continue
        c["nodes"] += 1
        pir = round(cpp - cp, 3)
        if pir <= 0:
            continue
        c["nodes with pirate power"] += 1
        c[f"extra collectors {int((ncp or 0) - (nc or 0))}"] += 1
        if rp is not None and pp is not None and ret is not None:
            r1 = rp / (rp + pp) if rp + pp else 1.0
            r2 = rp / (rp + pp + pir) if rp + pp + pir else 1.0
            r3 = (rp + pir) / (rp + pp + pir) if rp + pp + pir else 1.0
            c["retention = retain/(retain+pull)"] += abs(r1 - ret) < 0.0011
            c["retention = retain/(retain+pull+pirates)"] += abs(r2 - ret) < 0.0011
            c["retention = (retain+pirates)/(retain+pull+pirates)"] += abs(r3 - ret) < 0.0011
        # shares: sum of power_fraction of collectors
        pfs = [float(x) for x in re.findall(r"\n\t\t\tpower_fraction=([\d.]+)", b)]
        if pfs:
            c["collector power_fraction sums < 0.99 (pirates take a share)"] += sum(pfs) < 0.99
            if len(ex) < 4:
                ex.append((z.name[:20], m.group(1), "pirates", pir, "collector_power", cp, "sum pf", round(sum(pfs), 3), "pirate share", round(pir / cpp, 3)))
print(dict(c))
for x in ex:
    print(x)
