"""R02 final, test 4: what `has_capital` marks, and colonial nations.
Facts tested over all 86 manifest entries (84 distinct saves):
 (a) every entry with key has_capital sits at the node of the country's trade_port province (node from data/tradenodes.json member_provinces)
 (b) every collecting entry (key total) at the node of trade_port has has_capital; every collecting entry without has_capital is away from it
 (c) node(capital) vs node(trade_port) in every country that has both (do they ever differ?)
 (d) the away collectors: do they have a trade_port node, a has_capital entry elsewhere?
 (e) colonial nations (tags C00-C99): with / without has_capital entry; away entries of colonial nations
Usage: .venv/bin/python scripts/research/final_r02_capital.py"""
import re
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import final_r02_lib as L

c = Counter()
ex = defaultdict(list)
col_rows = []
for sid, s in L.all_saves():
    cap_nodes = defaultdict(set)
    away = defaultdict(list)
    collect_at_port_without_cap = []
    for nid, n in s["nodes"].items():
        for tag, e in n["e"].items():
            pn = L.port_node(s, tag)
            if e["cap"]:
                cap_nodes[tag].add(nid)
                c["entries with has_capital"] += 1
                if nid == pn:
                    c["  ... at node(trade_port)"] += 1
                else:
                    ex["cap not at port"].append((sid, nid, tag, pn))
            if e["coll"] and nid == pn and not e["cap"]:
                ex["collecting at port node without has_capital"].append((sid, nid, tag))
            if e["coll"] and not e["cap"]:
                away[tag].append(nid)
                c["away entries"] += 1
                if nid == pn:
                    ex["away at port node"].append((sid, nid, tag))
                if pn is None:
                    c["away entries of a country without resolvable trade_port node"] += 1
                    ex["away, no port node"].append((sid, nid, tag))
    seen = defaultdict(lambda: [0, 0])   # tag -> [entries with val>0 or a merchant flag, entries with has_capital]
    for nid, n in s["nodes"].items():
        for tag, e in n["e"].items():
            if tag != "PIR" and (e["val"] or e["trader"] or e["steer"] or e["coll"]):
                seen[tag][0] += 1
            if e["cap"]:
                seen[tag][1] += 1
    for tag, (powered, ncap) in seen.items():
        if powered:
            c["country-saves (not PIR) with power or a merchant at some node"] += 1
            c["  ... with exactly one has_capital entry"] += int(ncap == 1)
            if ncap != 1:
                ex["powered country without exactly one has_capital"].append((sid, tag, ncap))
    for tag, cc in s["c"].items():
        pn, cn = L.port_node(s, tag), L.capital_node(s, tag)
        if pn is not None and cn is not None:
            c["country-saves with capital and trade_port nodes"] += 1
            if pn != cn:
                c["  ... capital node != trade_port node"] += 1
                ex["capital!=port"].append((sid, tag, cn, pn))
        if tag in cap_nodes:
            c["country-saves with a has_capital entry"] += 1
            if cap_nodes[tag] != {pn}:
                ex["country cap node set != {port node}"].append((sid, tag, sorted(cap_nodes[tag]), pn))
            if cn is not None and cap_nodes[tag] != {cn}:
                ex["country cap node set != {capital node}"].append((sid, tag, sorted(cap_nodes[tag]), cn))
        if tag in away:
            c["country-saves with away collectors"] += 1
            c["   ... of which have a has_capital entry"] += int(tag in cap_nodes)
            c["   ... of which have no has_capital entry"] += int(tag not in cap_nodes)
        if re.fullmatch(r"C\d\d", tag) and any(tag in n["e"] for n in s["nodes"].values()):
            has = tag in cap_nodes
            c["colonial-nation country-saves (with node entries): has_capital entry" if has else "colonial-nation country-saves (with node entries): no has_capital entry"] += 1
            if tag in away:
                c["colonial country-saves with away collectors"] += 1
            col_rows.append((sid, tag, has, pn, cn, tag in away))
for k, v in c.items():
    print(f"{v:>8}  {k}")
for k, v in ex.items():
    print(f"EXCEPTIONS [{k}]: {len(v)}", v[:8])
nocap = [r for r in col_rows if not r[2]]
print("colonial country-saves without has_capital entry:", len(nocap), " of them with a resolvable trade_port node:", sum(1 for r in nocap if r[3] is not None),
      " with away collectors:", sum(1 for r in nocap if r[5]))
