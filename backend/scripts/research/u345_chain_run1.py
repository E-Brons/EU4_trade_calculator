"""Step 1: engine identity checks and the marginal money of one frigate at every TUR node with ships (weights fixed)."""
import sys
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from u345_chain_engine import Save, f
E = {e['id']: e for e in L.OLD + L.NEW}
if __name__ == '__main__':
    for sid in ('S79', 'S80', 'U03', 'U04', 'U05'):
        S = Save(E[sid])
        bad = 0; mx = 0.0; n = 0
        for nid in S.order:
            v = S.node_vals(nid)
            if v['gross'] <= 0: continue
            n += 1
            d = abs(v['gross'] * v['ret'] - v['cur']); mx = max(mx, d); bad += d > 0.0025 * max(1, v['gross'] * 0.001 + 1)
        print(f"{sid}: nodes with gross>0 {n}; |gross*retention-current| max {mx:.4f}; >0.0035: {bad}")
        # TUR nodes with ships
        tur = {nid: S.entry(nid, 'TUR') for nid in S.order if S.entry(nid, 'TUR')}
        for nid, c in tur.items():
            ls = int(f(c, 'light_ship'))
            if ls == 0: continue
            md = f(c, 'max_demand'); m = S.membership(nid, 'TUR')
            d_eff = 3.5 * md   # one frigate, f=1 (TUR f=1.0 in every TUR entry)
            ch = {(nid, 'TUR'): d_eff}
            vals = S.replay(ch); mon = S.collector_money(vals, 'TUR', ch)
            tot = sum(x['money'] - x['rec_money'] for x in mon.values())
            parts = ', '.join(f"{k}:{x['money']-x['rec_money']:+.4f}" for k, x in sorted(mon.items(), key=lambda kv: -abs(kv[1]['money']-kv[1]['rec_money'])) if abs(x['money']-x['rec_money']) > 0.00005)
            print(f"   {nid:<18} ships {ls:>3} role {str(m):<7} md {md:.3f} d_eff/frigate {d_eff:.3f} -> dMoney(TUR) {tot:+.4f} [{parts}]")
