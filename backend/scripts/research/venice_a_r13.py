"""Venice series R13: (1) province_power == sum of province trade_power over controlled provinces (per save); (2) when does a province's trade_power / development change?"""
import sys, collections
sys.path.insert(0, "scripts/research")
import venice_load as V
from final_r12_common import entries_of, m3

def provs(p):
    P = V.load(p, "provinces"); out = {}
    for k, v in P.items():
        if isinstance(v, dict) and 'trade' in v and 'trade_power' in v:
            out[k] = v
    return out

def sums(pr):
    s = collections.defaultdict(int)
    for v in pr.values():
        c = v.get('controller')
        if c: s[(v['trade'], c)] += m3(v['trade_power'])
    return s

if __name__ == '__main__':
    prev = None
    for p in V.files():
        pr = provs(p); S = sums(pr); ok = bad = 0; ex = []
        for n in V.nodes(p):
            for t, e in entries_of(n).items():
                if 'province_power' in e:
                    d = m3(e['province_power']) - S.get((n['definitions'], t), 0)
                    if d == 0: ok += 1
                    else: bad += 1; ex.append((n['definitions'], t, d))
        ch = ''
        if prev:
            ch = f" | provinces with trade_power changed vs prev: {sum(1 for k,v in pr.items() if k in prev and prev[k]['trade_power'] != v['trade_power'])} of {len(pr)}"
        print(p.stem[6:], f"province_power == controlled-province sum: {ok}/{ok+bad}", ex[:3], ch)
        prev = pr
