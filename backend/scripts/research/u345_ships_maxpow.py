"""Is ship_power fully inside max_pow?  residual = max_pow - province_power - ship_power - prev - 5*capital - sum(modifier.power);
per country the residual on merchant entries should be a constant R (R06); test it on entries WITH ships vs entries without."""
import sys
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from collections import Counter, defaultdict
A = common.as_list

def f(c, k): 
    try: return float(c.get(k, 0) or 0)
    except (TypeError, ValueError): return 0.0

def rows(e):
    for n in common.nodes(e):
        for tag, c in n.items():
            if not (isinstance(c, dict) and 'max_pow' in c): continue
            mods = sum(f(m, 'power') for m in A(c.get('modifier')) if isinstance(m, dict))
            res = f(c, 'max_pow') - f(c, 'province_power') - f(c, 'ship_power') - f(c, 'prev') - 5 * bool(c.get('has_capital')) - mods
            yield n['definitions'], tag, c, round(res, 3)

if __name__ == '__main__':
    for e in L.OLD + L.NEW:
        byc = defaultdict(list)
        allrows = list(rows(e))
        for nd, tag, c, res in allrows:
            if 'ship_power' not in c:
                byc[(tag, bool(c.get('has_trader')))].append(res)
        R = {k: Counter(v).most_common(1)[0][0] for k, v in byc.items()}   # modal residual of entries without ships
        ok = bad_ship = n_ship = 0; bad = []
        ships_in_country_with_R = 0
        for nd, tag, c, res in allrows:
            if 'ship_power' not in c: continue
            key = (tag, bool(c.get('has_trader')))
            if key not in R: continue
            n_ship += 1
            if abs(res - R[key]) <= 0.0025: ok += 1
            else: bad.append((nd, tag, res, R[key], f(c, 'ship_power'), f(c, 'light_ship')))
        # alternative: ship_power NOT inside max_pow => residual_alt = res + ship_power should equal R
        alt_ok = sum(1 for nd, tag, c, res in allrows if 'ship_power' in c and (tag, bool(c.get('has_trader'))) in R and abs(res + f(c, 'ship_power') - R[(tag, bool(c.get('has_trader')))]) <= 0.0025)
        print(f"== {e['id']} {e['date']}: ship entries with a country reference R: {n_ship}; residual == R (ship_power fully inside max_pow): {ok}; alt (ship_power not inside): {alt_ok}; mismatches {len(bad)}")
        for b in bad[:12]: print('    MISMATCH', b)
