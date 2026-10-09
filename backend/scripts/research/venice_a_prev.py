"""Venice series: `prev` rule (sum over links B->D with province_power_D >= 10 of trunc3(pp/5)), with and without the weight>0 gate, per save."""
import sys, json
from decimal import Decimal as Dc, ROUND_DOWN
from pathlib import Path
sys.path.insert(0, "scripts/research")
import venice_load as V
from final_r12_common import OUT, lst, entries_of

def d5(p): return float((Dc(repr(float(p))) / 5).quantize(Dc('0.001'), rounding=ROUND_DOWN))

def run(p, thr=10.0):
    ns = {n['definitions']: n for n in V.nodes(p)}
    ent = {k: entries_of(n) for k, n in ns.items()}
    res = dict(cand=0, gated_ok=0, plain_ok=0, zero_w_links=0, fail_both=[], exact10=0, at_boundary=[])
    for B, tg in ent.items():
        w = [float(x) for x in lst(ns[B].get('steer_power'))]
        for tag, c in tg.items():
            if 'max_pow' not in c: continue
            res['cand'] += 1
            plain = gated = 0.0
            for i, D_ in enumerate(OUT.get(B, [])):
                d = ent.get(D_, {}).get(tag)
                if not d: continue
                pp = d.get('province_power', 0)
                if pp == 10.0: res['exact10'] += 1
                if 9.9 <= pp <= 10.1: res['at_boundary'].append((B, D_, tag, pp, c.get('prev', 0)))
                if pp >= thr:
                    plain += d5(pp)
                    if i < len(w) and w[i] > 0: gated += d5(pp)
                    if i < len(w) and w[i] == 0: res['zero_w_links'] += 1
            rec = c.get('prev', 0.0)
            res['plain_ok'] += abs(plain - rec) < 0.0005
            res['gated_ok'] += abs(gated - rec) < 0.0005
            if abs(plain - rec) >= 0.0005 and abs(gated - rec) >= 0.0005: res['fail_both'].append((B, tag, rec, round(plain, 3), round(gated, 3)))
    return res

if __name__ == '__main__':
    for p in V.files():
        r = run(p)
        print(p.stem[6:], f"candidates {r['cand']} plain_ok {r['plain_ok']} gated_ok {r['gated_ok']} zero-weight propagating-links {r['zero_w_links']} exact10 {r['exact10']} fail_both {len(r['fail_both'])}", r['fail_both'][:3], 'boundary', r['at_boundary'][:3])
