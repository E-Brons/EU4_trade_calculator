"""R02 final, test 5: within-country switches. A node where a country starts (or stops) collecting away between two
consecutive saves of the Ottoman campaign (S79 -> S80 -> U03 -> U04 -> U05 [-> U06]).
normalized ratio = (md_B / md_A) / median over the country's CONTROL nodes of (md_B / md_A), control = same country, not away in
either save, no has_capital, same class in both saves, no embargoer with own power at the node in either save (>= 5 needed).
Expected: 0.5 when a country starts to collect away, 2.0 when it stops. Usage: .venv/bin/python scripts/research/final_r02_switch.py"""
import statistics
import sys
sys.path.insert(0, "scripts/research")
import final_r02_lib as L

PAIRS = [("S79", "S80"), ("S80", "U03"), ("U03", "U04"), ("U04", "U05"), ("U05", "U06")]
data = dict(L.all_saves())


def klass(s, nid, tag):
    return "dom" if (s["nodes"][nid]["top"] == tag or nid == L.port_node(s, tag)) else "for"


def kind(e):
    return "away" if L.is_away(e) else "steer" if e["steer"] else "merchant" if e["trader"] else "passive"


rows = []
for a, b in PAIRS:
    A, B = data[a], data[b]
    for tag in A["c"]:
        if tag not in B["c"] or tag == "PIR":
            continue
        ctrl, sw = [], []
        for nid in B["nodes"]:
            ea, eb = A["nodes"].get(nid, {"e": {}})["e"].get(tag), B["nodes"][nid]["e"].get(tag)
            if not ea or not eb or not ea["md"] or not eb["md"]:
                continue
            if L.is_away(ea) != L.is_away(eb):
                sw.append((nid, ea, eb))
            elif not L.is_away(ea) and not ea["cap"] and not eb["cap"] and klass(A, nid, tag) == klass(B, nid, tag) \
                    and not L.embargo_active(A, nid, tag) and not L.embargo_active(B, nid, tag):
                ctrl.append(eb["md"] / ea["md"])
        if not sw:
            continue
        med = statistics.median(ctrl) if len(ctrl) >= 5 else None
        tight = (sum(1 for x in ctrl if abs(x / med - 1) <= 0.005) / len(ctrl)) if med else None
        for nid, ea, eb in sw:
            emb = L.embargo_active(A, nid, tag) or L.embargo_active(B, nid, tag)
            chg = klass(A, nid, tag) != klass(B, nid, tag) or (nid == L.port_node(A, tag)) != (nid == L.port_node(B, tag))
            if chg:
                emb = "class/home changed" if not emb else "embargo + class/home changed"
            r = (eb["md"] / ea["md"]) / med if med else None
            rows.append(dict(pair=f"{a}->{b}", tag=tag, node=nid, change=f"{kind(ea)}->{kind(eb)}", mdA=ea["md"], mdB=eb["md"],
                             ctrl=None if med is None else round(med, 4), nctrl=len(ctrl), tight=None if tight is None else round(tight, 2),
                             emb=emb, ratio=None if r is None else round(r, 4), enter=L.is_away(eb)))
for r in rows:
    print(r["pair"], r["tag"], r["node"], r["change"], "md", r["mdA"], "->", r["mdB"], "ctrl", r["ctrl"], "(n=%d, tight=%s)" % (r["nctrl"], r["tight"]),
          (r["emb"] if isinstance(r["emb"], str) else "embargo-touched") if r["emb"] else "clean", "ratio", r["ratio"])
for label, sel, target in (("ENTERING away", True, 0.5), ("LEAVING away", False, 2.0)):
    rs = [r for r in rows if r["enter"] == sel]
    main = [r for r in rs if not r["pair"].endswith("U06")]
    print(f"\n{label}: {len(rs)} switches ({len(main)} in S79..U05)")
    for name, grp in (("S79..U05", main), ("all incl. U05->U06", rs)):
        ok = [r for r in grp if r["ratio"] is not None and abs(r["ratio"] / target - 1) <= 0.03]
        ok_clean = [r for r in ok if not r["emb"]]
        clean = [r for r in grp if not r["emb"] and r["ratio"] is not None]
        print(f"  {name}: {len(grp)} switches; within 3% of {target}: {len(ok)}; clean switches (no embargoer power at the node, class and home status unchanged): {len(clean)}, of which within 3%: {len(ok_clean)};"
              f" no control (<5 nodes): {sum(1 for r in grp if r['ratio'] is None)}")
        bad = [r for r in grp if r not in ok]
        for r in bad:
            print("     off:", r["pair"], r["tag"], r["node"], r["change"], r["ratio"], (r["emb"] if isinstance(r["emb"], str) else "embargo-touched") if r["emb"] else "clean", "tight", r["tight"])
