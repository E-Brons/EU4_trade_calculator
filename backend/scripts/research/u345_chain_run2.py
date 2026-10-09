"""Step 2: marginal money per frigate (continuous), and whole-fleet removal, at every TUR node with ships, weights fixed."""
import sys
sys.path.insert(0, 'scripts/research')
import u345_ships_load as L
from u345_chain_engine import Save, f, cont_delta
E = {e['id']: e for e in L.OLD + L.NEW}
if __name__ == '__main__':
    for sid in ('S79', 'S80', 'U03', 'U04', 'U05'):
        S = Save(E[sid])
        print('==', sid, E[sid]['date'], 'TUR collects at', sorted(S.collect_nodes('TUR')))
        for nid in S.order:
            c = S.entry(nid, 'TUR')
            if not c or int(f(c, 'light_ship')) == 0: continue
            ls = int(f(c, 'light_ship')); md = f(c, 'max_demand'); role = S.membership(nid, 'TUR'); steer = 'type' in c
            res = []
            for label, d in (('+1 frigate', 3.5 * md), (f'-all {ls}', -f(c, 'ship_power') * md)):
                ch = {(nid, 'TUR'): d}
                vals = S.replay(ch); cd = cont_delta(S, vals, 'TUR', ch)
                tot = sum(x['d_money'] for x in cd.values())
                where = ', '.join(f"{k}:{x['d_money']:+.3f}" for k, x in sorted(cd.items(), key=lambda kv: -abs(kv[1]['d_money'])) if abs(x['d_money']) > 0.0005)
                res.append(f"{label}: dMoney {tot:+.4f} [{where}]")
            print(f"   {nid:<16} ships {ls:>3} role {str(role):<7}{' STEER' if steer else ''} md {md:.3f} val {f(c,'val'):8.1f} money_here {f(c,'money'):7.3f} | " + ' | '.join(res))
