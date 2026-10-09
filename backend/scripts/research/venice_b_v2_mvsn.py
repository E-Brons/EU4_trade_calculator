"""SECOND PASS (raw text): R07 M vs N natural experiment, same table as venice_b_30_mvsn.py but with regex-extracted entries."""
import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_b_v2_raw as R
by = {p.stem[6:]: p for p in R.files()}
TICKS = ['1444_12_01', '1445_01_01', '1445_02_01', '1445_03_01', '1445_04_01', '1445_05_01', '1445_06_01', '1445_07_02']

def home(tag):
    d = {}
    for name, (ents, seg, w) in R.nodes(by[tag]).items():
        for c, e in ents.items():
            if 'has_capital' in e and 'money' in e and 'total' in e and float(e['total']) > 0.05 and float(e['money']) != 0:
                d[c] = ('has_trader' in e, float(e['money']) / float(e['total']), name)
    return d

tab = collections.defaultdict(collections.Counter)
prev = home(TICKS[0])
for t in TICKS[1:]:
    cur = home(t)
    for c in set(cur) & set(prev):
        if cur[c][2] != prev[c][2]: continue
        tab[(prev[c][0], cur[c][0])][round((cur[c][1] - prev[c][1]) * 20) / 20] += 1
    prev = cur
for k, v in sorted(tab.items()): print(k, sum(v.values()), dict(sorted(v.items())))
