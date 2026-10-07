"""E23: on which days does province trade_power change? Saves every 2nd day 1444.12.03..12.31 (one run from the base),
plus the base 1444.12.01. Prints, per consecutive pair, how many provinces changed trade_power, the owners most
affected, and VEN transfer_home_bonus per save. Run from tools/EU4-game-automation/experiments."""
import re
from collections import Counter
from pathlib import Path

files = [Path("out/E00/base_1444.12.01.eu4")] + sorted(Path("out/E23").glob("d_*.eu4"))
PROV = re.compile(r"\n\t(-\d+)=\{(.*?)\n\t\}", re.S)


def load(p):
    t = p.read_text(encoding="latin-1")
    date = re.search(r"\ndate=([\d.]+)", t).group(1)
    i = t.index("\nprovinces={")
    j = t.index("\n}\n", i)  # end of the top-level provinces block
    tp, owner = {}, {}
    parts = re.split(r"\n(-\d+)=\{", t[i:j])  # province keys sit at column 0
    for key, b in zip(parts[1::2], parts[2::2]):
        a = re.search(r"\n\t\ttrade_power=([\d.]+)", b)
        o = re.search(r'\n\t\towner="(\w+)"', b)
        if a:
            tp[key] = a.group(1); owner[key] = o.group(1) if o else "-"
    c = t.index("\n\tVEN={", t.index("\ncountries={"))
    thb = re.search(r"\n\t\ttransfer_home_bonus=([\d.]+)", t[c:c + 300000])
    return date, tp, owner, thb.group(1) if thb else None


prev = None
for p in files:
    date, tp, owner, thb = load(p)
    if prev:
        pdate, ptp, _, _ = prev
        ch = [k for k in tp if k in ptp and tp[k] != ptp[k]]
        own = Counter(owner[k] for k in ch).most_common(4)
        print(f"{pdate} -> {date}: {len(ch):4d} of {len(tp)} provinces changed trade_power; top owners {own}; VEN thb {thb}")
    else:
        print(f"{date}: {len(tp)} provinces with trade_power; VEN thb {thb}")
    prev = (date, tp, owner, thb)
