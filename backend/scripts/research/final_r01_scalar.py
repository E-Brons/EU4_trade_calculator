"""R01 final, part 1: md presence, home-node definition, country-wide scalar (ordinary nodes), steering is not penalised.
Independent code: raw keys only. Run from backend/: .venv/bin/python scripts/research/final_r01_scalar.py"""
import collections
import final_r01_lib as L

ALL = L.all_saves()
DIS = L.distinct(ALL)

# --- 0. census
n_entries = n_md = n_nodes = 0
for sid, s in DIS:
    for nid, n in s["nodes"].items():
        n_nodes += 1
        for t, e in n["e"].items():
            n_entries += 1
            n_md += e["md"] is not None
print(f"[0] distinct saves {len(DIS)} (86 manifest entries); nodes {n_nodes}; non-PIR (country,node) entries {n_entries}; with max_demand {n_md}")
# val = max_pow*md within 0.5% (or exact trunc)
bad = tot = 0
for sid, s in DIS:
    for nid, n in s["nodes"].items():
        for t, e in n["e"].items():
            if e["val"] is None or e["mp"] is None or e["md"] is None:
                continue
            tot += 1
            if abs(e["mp"] * e["md"] - e["val"]) > 0.002 * max(1.0, e["val"]) * 0.5 + 0.0015 * e["mp"]:
                bad += 1
print(f"[0b] entries with val, max_pow, max_demand: {tot}; |max_pow*md - val| > md-rounding allowance: {bad}")

# --- 0c. every real country (any entry with md) has md at all 80 nodes; stubs without md
stub = collections.Counter(); full = partial = 0
for sid, s in DIS:
    per = collections.Counter()
    tags = set()
    for n in s["nodes"].values():
        for t, e in n["e"].items():
            tags.add(t); per[t] += e["md"] is not None
    for t in tags:
        if per[t] == 0:
            stub[t] += 1
        elif per[t] == len(s["nodes"]):
            full += 1
        else:
            partial += 1
print(f"[0c] (save,tag) with md at all {len(s['nodes'])} nodes: {full}; with md at some nodes only: {partial}; tags with no md at all (stubs): {len(stub)} tags {sorted(stub)[:3]}..{sorted(stub)[-1]}, saves {max(stub.values())}")

# --- 1. home node definition (only tags that have an entry with md in the save)
same = diff = nohome = 0
dif_list = []
for sid, s in DIS:
    real = {t for n in s["nodes"].values() for t, e in n["e"].items() if e["md"] is not None}
    for t in sorted(real):
        h = L.home_node(s, t); p = L.port_node(s, t)
        if h is None and p is None:
            nohome += 1
        elif h == p:
            same += 1
        else:
            diff += 1; dif_list.append((sid, t, h, p))
print(f"[1] (save,country) with has_capital node == trade_port node: {same}; both absent {nohome}; different {diff} {dif_list[:10]}")

# --- 2. scalar over ordinary nodes
# group (save, tag): ordinary = not home, not top-province node, not away-collecting; country not embargoed
groups = {}
excl_emb = 0
for sid, s in DIS:
    tags = set()
    for n in s["nodes"].values():
        tags |= set(n["e"])
    for t in sorted(tags):
        if not any(n["e"].get(t) and n["e"][t]["md"] is not None for n in s["nodes"].values()):
            continue
        embargoed = bool(s["c"].get(t, {}).get("emb_by"))
        vals = collections.Counter()
        steer_rows = 0
        for nid, n in s["nodes"].items():
            e = n["e"].get(t)
            if e is None or e["md"] is None:
                continue
            if e["cap"] or n["top"] == t or L.is_away(e):
                continue
            vals[e["md"]] += 1
            steer_rows += e["steer"]
        if embargoed:
            excl_emb += 1
            continue
        groups[(sid, t)] = (vals, steer_rows)
one = [k for k, (v, _) in groups.items() if len(v) == 1]
multi = [(k, dict(v)) for k, (v, _) in groups.items() if len(v) > 1]
empty = [k for k, (v, _) in groups.items() if len(v) == 0]
print(f"[2] non-embargoed (save,country) groups {len(groups)} (embargoed groups skipped: {excl_emb}); single value: {len(one)}; several values: {len(multi)}; no ordinary node: {len(empty)}")
for k, v in multi:
    vs = sorted(v)
    print("     exception", k, "values", vs[:8], "n", len(vs))
# steering rows inside the single-valued groups (steering is not penalised)
st_rows = sum(groups[k][1] for k in one)
print(f"[2b] steering (`type`) rows inside the single-valued groups: {st_rows}")
# how many groups include an ordinary-node count >= 2 (so single-valued is non-trivial)
nontriv = sum(1 for k in one if sum(groups[k][0].values()) >= 2)
print(f"[2c] single-valued groups with >= 2 ordinary nodes: {nontriv}")
# the same for the 84 incl copies (85/86 entries)
one_all = multi_all = 0
for sid, s in ALL:
    pass
