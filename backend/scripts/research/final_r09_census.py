"""R09 final: census of every key in the trade block (node, entry, incoming link, modifier, t_from/t_to) and of the
trade-related country keys, over all 86 corpus entries. Counts are per corpus entry (U01/U02 included) and per 84 distinct saves."""
import sys, collections, re
sys.path.insert(0, "scripts/research")
import final_r09_load as L

node_keys = collections.Counter(); node_keys_d = collections.Counter()
ent_keys = collections.Counter(); ent_keys_d = collections.Counter()
inc_keys = collections.Counter(); mod_keys = collections.Counter(); tf_types = collections.Counter()
ent_total = collections.Counter(); tags_other = collections.Counter()
nnodes = 0
for sid in L.IDS:
    d = sid not in L.DUP
    for n in L.nodes(sid):
        nnodes += 1
        for k, v in n.items():
            if L.TAG.match(k) and isinstance(v, dict):
                ent_total["entries"] += 1
                for kk, vv in v.items():
                    ent_keys[kk] += 1
                    if d: ent_keys_d[kk] += 1
                    if kk == "modifier":
                        for m in L.lst(vv):
                            for mk in m: mod_keys[mk] += 1
                    if kk in ("t_from", "t_to"):
                        tf_types[(kk, type(vv).__name__)] += 1
            else:
                node_keys[k] += 1
                if d: node_keys_d[k] += 1
                if k == "incoming":
                    for inc in L.lst(v):
                        for ik in inc: inc_keys[ik] += 1
            if not L.TAG.match(k) and isinstance(v, dict) and k != "incoming":
                tags_other[k] += 1
print("corpus entries", len(L.IDS), "distinct", len(L.DISTINCT), "nodes", nnodes)
print("NODE KEYS (86 entries | 84 distinct)")
for k, c in sorted(node_keys.items(), key=lambda x: -x[1]): print(f"  {k:40s} {c:6d} {node_keys_d[k]:6d}")
print("ENTRY KEYS, total entries", ent_total["entries"])
for k, c in sorted(ent_keys.items(), key=lambda x: -x[1]): print(f"  {k:40s} {c:8d} {ent_keys_d[k]:8d}")
print("INCOMING KEYS", dict(inc_keys)); print("MODIFIER KEYS", dict(mod_keys)); print("t_from/t_to types", dict(tf_types))
print("non-tag dict keys at node level", dict(tags_other))
