"""SECOND PASS for R08: (a) add = a/rank (controlled, raw-text extraction, different code path), (b) raw line diff of the trade block U25 vs U26, (c) solve VEN's weight contribution."""
import sys, difflib, collections
sys.path.insert(0, 'scripts/research')
import venice_b_v2_raw as R
by = {p.stem[6:]: p for p in R.files()}

def steer_groups(p):
    g = collections.defaultdict(list)
    for name, (ents, seg, w) in R.nodes(p).items():
        for c, d in ents.items():
            if 'add' in d and 'val' in d:
                g[(name, int(d.get('steer_power', 0)))].append((float(d['val']), c, float(d['add'])))
    return {k: sorted(v, reverse=True) for k, v in g.items()}

def pair(t0, t1, keys):
    g0, g1 = steer_groups(by[t0]), steer_groups(by[t1])
    ok = tot = 0
    for k in keys:
        a = {c: (i + 1, add) for i, (v, c, add) in enumerate(g0[k])}
        b = {c: (i + 1, add) for i, (v, c, add) in enumerate(g1[k])}
        for c in a:
            if c == 'VEN' or c not in b: continue
            r0, a0 = a[c]; r1, a1 = b[c]
            # products add*rank must agree up to the 3-decimal truncation of both adds
            lo0, hi0 = a0 * r0, (a0 + 0.001) * r0
            lo1, hi1 = a1 * r1, (a1 + 0.001) * r1
            tot += 1; ok += (lo0 <= hi1 and lo1 <= hi0)
    return ok, tot

keys = [('alexandria', 1), ('ragusa', 1), ('wien', 0)]
print('(a) product add*rank unchanged when VEN leaves/joins:', [(t0, t1, pair(t0, t1, k)) for t0, t1, k in (
    ('1445_03_01', '1445_04_01', keys), ('1445_04_01', '1445_05_01', keys[1:2]), ('1445_05_01', '1445_06_01', keys[:1]), ('1445_06_01', '1445_07_02', keys[2:3]))])

a = R.tradeblock(by['1445_03_01']).split('\n'); b = R.tradeblock(by['1445_03_31']).split('\n')
d = [l for l in difflib.unified_diff(a, b, lineterm='', n=0) if l[:1] in '+-' and l[:3] not in ('+++', '---')]
print('(b) raw trade-block line diff U25 -> U26:', len(d), 'changed lines'); print('   ', [l.strip() for l in d])

print('(c) VEN effective contribution X (others plain val):')
for t in ('1444_12_01', '1445_03_01', '1445_05_01', '1445_06_01', '1445_07_02'):
    nodes = R.nodes(by[t])
    for name in ('alexandria', 'ragusa', 'wien'):
        ents, seg, w = nodes[name]
        ws = [float(x) for x in w.strip('{}').split()]
        if 'type' not in ents['VEN']: continue
        vl = int(ents['VEN'].get('steer_power', 0))
        S = [0.0] * len(ws)
        for c, dd in ents.items():
            if c != 'VEN' and 'type' in dd and int(dd.get('steer_power', 0)) < len(S):
                S[int(dd.get('steer_power', 0))] += float(dd['val'])
        T = sum(S); wl = ws[vl]; X = (wl * T - S[vl]) / (1 - wl)
        print(f'   {t} {name}: X={X:.2f} VEN val={ents["VEN"]["val"]} X/val={X / float(ents["VEN"]["val"]):.3f}')
