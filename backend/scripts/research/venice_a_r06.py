"""Venice series R06: (1) R = residual extras per country at tick saves vs the formula 2 + 5*reform; (2) non-tick saves keep the last tick's extras."""
import sys, collections
sys.path.insert(0, "scripts/research")
import venice_load as V
from final_r12_common import entries_of, lst

REFORMS = ('mercantilistic_approach_reform', 'pious_merchants_reform')

def resid(e):
    return round(e['max_pow'] - e.get('province_power', 0) - e.get('ship_power', 0) - e.get('prev', 0) - 5 * bool(e.get('has_capital')), 3)

def per_country(p):
    """{tag: set(residuals of entries with has_trader and no node modifier)}"""
    out = collections.defaultdict(set)
    for n in V.nodes(p):
        for t, e in entries_of(n).items():
            if 'max_pow' in e and e.get('has_trader') and 'modifier' not in e: out[t].add(resid(e))
    return out

if __name__ == '__main__':
    fs = V.files(); ticks = ['1444_11_11', '1444_12_01', '1445_01_01', '1445_02_01', '1445_03_01', '1445_04_01', '1445_05_01', '1445_06_01', '1445_07_02']
    for p in fs:
        s = p.stem[6:]
        if s not in ticks: continue
        C = V.load(p, 'countries'); pc = per_country(p); ok = bad = 0; badl = []
        for tag, rs in pc.items():
            c = C.get(tag)
            if not isinstance(c, dict): continue
            refs = lst(((c.get('government') or {}).get('reform_stack') or {}).get('reforms'))
            pred = 2 + 5 * any(r in REFORMS for r in refs)
            if rs == {pred}: ok += 1
            else: bad += 1; badl.append((tag, sorted(rs), pred))
        print(s, 'countries with merchants', ok + bad, 'R == 2+5*reform:', ok, 'other:', badl[:6])
