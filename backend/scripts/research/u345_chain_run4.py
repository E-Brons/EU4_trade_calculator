"""Step 4: exact telescoping decomposition of the change of TUR's money at each common collecting node into
(ship-caused via replay) + (other gross: local, other incoming) + (other retention) + (other power fraction) + (efficiency x).
M = gross * retention * power_fraction * x (continuous, x = money/share recorded). Also node-level Delta(pull/retain) vs TUR's own change."""
import sys
sys.path.insert(0, 'scripts/research')
import u345_ships_load as L
from u345_chain_engine import Save, f, cont_delta
E = {e['id']: e for e in L.OLD + L.NEW}


def run(a, b, verbose=True):
    A, B = Save(E[a]), Save(E[b])
    changes = {}
    for nid in set(A.order) & set(B.order):
        ea, eb = A.entry(nid, 'TUR'), B.entry(nid, 'TUR')
        if ea is None or eb is None: continue
        dsp = f(eb, 'ship_power') - f(ea, 'ship_power')
        if abs(dsp) >= 0.0005: changes[(nid, 'TUR')] = dsp * f(ea, 'max_demand')
    vals = A.replay(changes); pred = cont_delta(A, vals, 'TUR', changes)
    print(f"\n== {a} -> {b}: ship-only replay of {len(changes)} TUR ship changes; decomposition of dMoney(TUR) per common collecting node")
    print("   node             actual  | ship-caused  other-local other-incoming  other-retention  other-pf  dX(eff) | sum-check")
    rows = []
    for c in sorted(set(A.collect_nodes('TUR')) & set(B.collect_nodes('TUR'))):
        ea, eb = A.entry(c, 'TUR'), B.entry(c, 'TUR')
        va, vb = A.node_vals(c), B.node_vals(c)
        xa = f(ea, 'money') / f(ea, 'total'); xb = f(eb, 'money') / f(eb, 'total')
        pfa = A.eff(ea) / va['retain']; pfb = B.eff(eb) / vb['retain']
        MA = va['gross'] * va['ret'] * pfa * xa; MB = vb['gross'] * vb['ret'] * pfb * xb
        vs = vals.get(c)
        g1 = vs['gross'] if vs else va['gross']; r1 = vs['ret'] if vs else va['ret']
        pf1 = pfa + (pred[c]['d_pf'] if c in pred else 0.0)
        M1 = g1 * r1 * pf1 * xa
        dloc = vb['local'] - va['local']; dg_other = vb['gross'] - g1
        g_loc = va['gross'] + (vs['gross'] - va['gross'] if vs else 0) + dloc
        M2a = g_loc * r1 * pf1 * xa                      # local change
        M2 = vb['gross'] * r1 * pf1 * xa                 # + other incoming
        M3 = vb['gross'] * vb['ret'] * pf1 * xa
        M4 = vb['gross'] * vb['ret'] * pfb * xa
        M5 = MB
        parts = (M1 - MA, M2a - M1, M2 - M2a, M3 - M2, M4 - M3, M5 - M4)
        rec = f(eb, 'money') - f(ea, 'money')
        print(f"   {c:<16} {rec:+8.3f} | {parts[0]:+9.3f} {parts[1]:+11.3f} {parts[2]:+14.3f} {parts[3]:+16.3f} {parts[4]:+10.3f} {parts[5]:+9.3f} | model {MB-MA:+.3f} vs recorded {rec:+.3f}")
        rows.append((c, rec, parts))
    return rows


if __name__ == '__main__':
    for a, b in (('U03', 'U04'), ('U04', 'U05'), ('U03', 'U05'), ('S79', 'S80')):
        run(a, b)
    # node-level pull/retain: TUR's own change vs recorded change (pair U03->U04)
    for a, b in (('U03', 'U04'), ('U04', 'U05')):
        A, B = Save(E[a]), Save(E[b])
        print(f"\n== {a}->{b}: ship nodes, recorded change of pull/retain vs TUR's own change of effective power there (other = everyone else)")
        for nid in sorted(set(A.order) & set(B.order)):
            ea, eb = A.entry(nid, 'TUR'), B.entry(nid, 'TUR')
            if not ea or not eb or abs(f(eb, 'ship_power') - f(ea, 'ship_power')) < 0.0005: continue
            if A.membership(nid, 'TUR') != B.membership(nid, 'TUR'): print(f"   {nid}: role changed {A.membership(nid,'TUR')}->{B.membership(nid,'TUR')}"); continue
            va, vb = A.node_vals(nid), B.node_vals(nid); m = A.membership(nid, 'TUR')
            key = 'retain' if m == 'collect' else 'pull'
            d_tur = B.eff(eb) - A.eff(ea); d_ship = (f(eb, 'ship_power') - f(ea, 'ship_power')) * f(ea, 'max_demand')
            d_rec = vb[key] - va[key]
            print(f"   {nid:<16} role {m:<7} d{key} recorded {d_rec:+9.3f} | TUR own d_eff {d_tur:+9.3f} (ship-only {d_ship:+9.3f}) | others {d_rec-d_tur:+9.3f}")
