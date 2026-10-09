"""Step 3: natural experiments. For each save pair, replay ONLY the TUR ship changes on save A (weights/ratios fixed) and compare
with the recorded change of TUR's money at every collecting node; split the difference into first-order confounder terms."""
import sys
sys.path.insert(0, 'scripts/research')
import u345_ships_load as L
from u345_chain_engine import Save, f, cont_delta
from app.trade import calc
E = {e['id']: e for e in L.OLD + L.NEW}


def tur_ships(S):
    return {nid: S.entry(nid, 'TUR') for nid in S.order if S.entry(nid, 'TUR') and 'ship_power' in S.entry(nid, 'TUR')}


def pair(a, b):
    A, B = Save(E[a]), Save(E[b])
    ca, cb = A.collect_nodes('TUR'), B.collect_nodes('TUR')
    print(f"\n===== {a} ({E[a]['date']}) -> {b} ({E[b]['date']}); TUR collects A={sorted(ca)} B={sorted(cb)}")
    sa, sb = tur_ships(A), tur_ships(B)
    changes, roles, info = {}, {}, []
    for nid in sorted(set(A.order) & set(B.order)):
        ea, eb = A.entry(nid, 'TUR'), B.entry(nid, 'TUR')
        if ea is None or eb is None: continue
        dsp = f(eb, 'ship_power') - f(ea, 'ship_power')
        if abs(dsp) < 0.0005: continue
        md = f(ea, 'max_demand')
        d_ship = dsp * md
        d_own = B.eff(eb) - A.eff(ea)
        same_role = A.membership(nid, 'TUR') == B.membership(nid, 'TUR')
        changes[(nid, 'TUR')] = d_ship
        info.append((nid, int(f(ea, 'light_ship')), int(f(eb, 'light_ship')), dsp, d_ship, d_own, A.membership(nid, 'TUR'), B.membership(nid, 'TUR')))
    for r in info:
        print(f"   ship change {r[0]:<16} ships {r[1]:>3}->{r[2]:>3} d_ship_power {r[3]:+8.3f}  d_eff(ship only, md_A) {r[4]:+8.3f}  d_eff(actual TUR) {r[5]:+8.3f}  role {r[6]}->{r[7]}")
    if not changes: return
    only_collect_same = all(r[6] == r[7] for r in info)
    vals = A.replay(changes)
    pred = cont_delta(A, vals, 'TUR', changes)
    # actual money of TUR per collecting node (common nodes where TUR collects in both)
    print("   node               pred_dMoney(ships only)  actual_dMoney   residual | dGross_total dGross_ship | dRet  dRet_ship | dPF dPF_ship | dX | dLocal")
    tp = ta = 0.0
    for c in sorted(set(ca) & set(cb)):
        ea, eb = A.entry(c, 'TUR'), B.entry(c, 'TUR')
        va, vb = A.node_vals(c), B.node_vals(c)
        xa = f(ea, 'money') / f(ea, 'total') if f(ea, 'total') > 0 else 0.0
        xb = f(eb, 'money') / f(eb, 'total') if f(eb, 'total') > 0 else 0.0
        actual = f(eb, 'money') - f(ea, 'money')
        p = pred.get(c, {}).get('d_money', 0.0)
        vs = vals.get(c)
        dg_ship = (vs['gross'] - va['gross']) if vs else 0.0
        dr_ship = (vs['ret'] - va['ret']) if vs else 0.0
        dpf_ship = pred.get(c, {}).get('d_pf', 0.0)
        pfa = f(ea, 'power_fraction'); pfb = f(eb, 'power_fraction')
        tp += p; ta += actual
        print(f"   {c:<18} {p:+10.3f} {actual:+14.3f} {actual-p:+10.3f} | {vb['gross']-va['gross']:+9.3f} {dg_ship:+9.3f} | {vb['ret']-va['ret']:+7.4f} {dr_ship:+7.4f} | {pfb-pfa:+7.4f} {dpf_ship:+7.4f} | {xb-xa:+6.3f} | {vb['local']-va['local']:+8.3f}")
    print(f"   TOTAL over common collecting nodes: predicted(ships only) {tp:+.3f}, actual {ta:+.3f}")
    # chain at each ship node: node-level recorded vs predicted
    print("   node-level at ship nodes (A -> B recorded | ship-only prediction):")
    for r in info:
        nid = r[0]
        va, vb, vp = A.node_vals(nid), B.node_vals(nid), vals.get(nid)
        oth_eff = 0.0
        print(f"     {nid:<16} retain {va['retain']:.1f}->{vb['retain']:.1f} (pred {vp['retain']:.1f}) pull {va['pull']:.1f}->{vb['pull']:.1f} (pred {vp['pull']:.1f}) retention {va['ret']:.4f}->{vb['ret']:.4f} (pred {vp['ret']:.4f}) "
              f"current {va['cur']:.3f}->{vb['cur']:.3f} (pred {vp['cur']:.3f}) outgoing {va['out']:.3f}->{vb['out']:.3f} (pred {vp['out']:.3f}) gross {va['gross']:.3f}->{vb['gross']:.3f} local {va['local']:.3f}->{vb['local']:.3f}")


if __name__ == '__main__':
    for a, b in (('S79', 'S80'), ('U03', 'U04'), ('U04', 'U05'), ('U03', 'U05')):
        pair(a, b)
