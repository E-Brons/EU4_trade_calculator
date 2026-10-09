"""Independent check of: TUR actions per node (Q1), home merchant in U05, gulf_of_aden/crimea ratio, embargoer power, TUR changes U04->U05."""
import sys
sys.path.insert(0, ".")
import ver2_b_lib as L

SAVES = ["S79", "S80", "U03", "U04", "U05"]
data = dict(L.saves(set(SAVES)))
for sid in SAVES:
    s = data[sid]
    tur_nodes = {nid: n["e"]["TUR"] for nid, n in s["nodes"].items() if "TUR" in n["e"]}
    home = L.home_node(s, "TUR")
    merch = {nid: e for nid, e in tur_nodes.items() if e["trader"]}
    def kind(nid, e):
        if not e["trader"]:
            return "home(no merchant)" if e["cap"] else None
        if e["steer"]:
            return "steer"
        if e["cap"]:
            return "home+merchant(collect)" if e["collect"] else "home+merchant"
        return "collect-away" if e["collect"] else "merchant-no-action"
    acts = {}
    for nid, e in tur_nodes.items():
        k = kind(nid, e)
        if k:
            acts.setdefault(k, []).append(nid)
    print(f"{sid}: home={home} (trade_port {s['c']['TUR']['port']}) merchants={len(merch)} home collects={tur_nodes[home]['collect']}")
    for k, v in sorted(acts.items()):
        print(f"   {k:24s} {sorted(v)}")

print()
print("gulf_of_aden / crimea (TUR):")
for sid in SAVES:
    s = data[sid]
    g, c = s["nodes"]["gulf_of_aden"]["e"]["TUR"], s["nodes"]["crimea"]["e"]["TUR"]
    emb = s["c"]["TUR"]["emb_by"]
    def embp(nid):
        return {t: round(L.own_power(s["nodes"][nid]["e"][t]), 1) for t in emb if t in s["nodes"][nid]["e"] and L.own_power(s["nodes"][nid]["e"][t]) > 0}
    def embp2(nid):  # alternative own power: province_power + ship_power
        return {t: round(s["nodes"][nid]["e"][t]["pp"] + s["nodes"][nid]["e"][t]["sp"], 1) for t in emb if t in s["nodes"][nid]["e"] and (s["nodes"][nid]["e"][t]["pp"] + s["nodes"][nid]["e"][t]["sp"]) > 0}
    print(f"  {sid}: gulf md={g['md']} ({'steer' if g['steer'] else 'away' if g['collect'] else 'other'}; top={s['nodes']['gulf_of_aden']['top']}) crimea md={c['md']} ({'steer' if c['steer'] else 'other'}; top={s['nodes']['crimea']['top']}) ratio={g['md']/c['md']:.4f}  embargoers with power: gulf {embp('gulf_of_aden')} crimea {embp('crimea')} | alt gulf {embp2('gulf_of_aden')} crimea {embp2('crimea')}")
print("crimea jump U04->U05:", data["U05"]["nodes"]["crimea"]["e"]["TUR"]["md"] / data["U04"]["nodes"]["crimea"]["e"]["TUR"]["md"])

print()
print("domestic (top province = TUR) vs foreign (top province != TUR, no embargoer power), TUR passive/steer entries:")
for sid in SAVES:
    s = data[sid]; emb = s["c"]["TUR"]["emb_by"]
    dom, frn = {}, {}
    for nid, n in s["nodes"].items():
        e = n["e"].get("TUR")
        if not e or e["collect"] or e["md"] is None:
            continue
        clean = all(L.own_power(n["e"][t]) <= 0 for t in emb if t in n["e"])
        (dom if n["top"] == "TUR" or e["cap"] else frn).setdefault(e["md"], []).append((nid, clean))
    print(f"  {sid}: domestic values {{{', '.join(f'{k}:{len(v)}n/{sum(c for _, c in v)}clean' for k, v in sorted(dom.items()))}}}  foreign values {{{', '.join(f'{k}:{len(v)}n/{sum(c for _, c in v)}clean' for k, v in sorted(frn.items()) if k not in (1.0,) )[:400]}}}")

print()
print("TUR country-level changes:")
for a, b in [("U03", "U04"), ("U04", "U05")]:
    A, B = data[a]["c"]["TUR"], data[b]["c"]["TUR"]
    for k in ("ideas", "reforms", "tech", "merc", "n60", "estates"):
        print(f"  {a}->{b} {k}: {'same' if A[k] == B[k] else f'CHANGED {A[k]} -> {B[k]}'}")
    print(f"  {a}->{b} modifiers added {sorted(B['modkeys'] - A['modkeys'])} removed {sorted(A['modkeys'] - B['modkeys'])}")
