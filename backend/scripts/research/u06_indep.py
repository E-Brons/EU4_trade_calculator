"""Independent recomputation of the headline U06 numbers: trade data via app.trade.extract.extract_world (not the raw-tree loader
used by u06_*.py), country-level values via regex on the melted text."""
import re, sys
from pathlib import Path
sys.path.insert(0, ".")
from app.parsing.tradenodes import load_trade_graph
from app.trade.extract import extract_world
FIX = Path("tests/fixtures/saves")
F = {"U03": "U03_TUR.1691.01.09.eu4", "U04": "U04_TUR.1691.11.01.eu4", "U05": "U05_TUR.1693.04.15.eu4", "U06": "U06_TUR.1696.03.25.eu4"}
g = load_trade_graph()
tur_text = {}
for sid, fn in F.items():
    w = extract_world(FIX / fn, sid, graph=g)
    txt = (FIX / fn).read_text(encoding="utf-8", errors="replace")
    i = txt.index("\ncountries={")
    j = txt.index("\n\tTUR={", i)
    blk = txt[j: j + 400000]
    tech = re.search(r"technology=\{\s*adm_tech=(\d+)\s*dip_tech=(\d+)\s*mil_tech=(\d+)", blk).groups()
    nenv = len(re.findall(r"type=1\b", re.search(r"\n\t\tmerchants=\{(.*?)\n\t\t\}", blk, re.S).group(1)))
    coll = [(n, e) for (n, t), e in w.inputs.entries.items() if t == "TUR" and e.collecting]
    rec = w.recorded.entries
    xs = {n: round(rec[(n, "TUR")].money / rec[(n, "TUR")].share_total - 1, 2) for n, e in coll}
    money = round(sum(rec[(n, "TUR")].money for n, e in coll), 3)
    tot = round(sum(rec[(n, "TUR")].share_total for n, e in coll), 3)
    print(sid, w.inputs.date, "tech(adm,dip,mil)=", tech, "merchant entries (type=1)=", nenv, "| TUR collecting X:", xs, "| sum money", money, "sum share", tot, "ships", sum(e.light_ships for (n, t), e in w.inputs.entries.items() if t == "TUR"))
    tur_text[sid] = w
# max_demand of TUR at nodes without any TUR action (passive) for U05 vs U06
A, B = tur_text["U05"].inputs.multipliers, tur_text["U06"].inputs.multipliers
for n in ("constantinople", "hormuz", "basra", "aleppo", "alexandria", "malacca", "philippines", "crimea", "genua", "ragusa"):
    print(n, A[(n, "TUR")], "->", B[(n, "TUR")], "ratio", round(B[(n, "TUR")] / A[(n, "TUR")], 4))
