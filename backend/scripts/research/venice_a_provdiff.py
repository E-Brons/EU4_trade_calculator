import sys, collections
sys.path.insert(0, "scripts/research")
import venice_load as V, venice_diff as D
import venice_a_r13 as R
fs = {p.stem[6:]: p for p in V.files()}
def cmp(a, b):
    A = R.provs(fs[a]); B = R.provs(fs[b])
    ch = [k for k in A if k in B and A[k]['trade_power'] != B[k]['trade_power']]
    cnt = collections.Counter()
    for k in ch:
        fa, fb = D.flat(A[k]), D.flat(B[k])
        for kk in set(fa) | set(fb):
            if fa.get(kk) != fb.get(kk) and not kk.startswith('/history'): cnt[kk.split('[')[0]] += 1
    allc = collections.Counter()
    for k in A:
        if k in B:
            fa, fb = D.flat(A[k]), D.flat(B[k])
            for kk in set(fa) | set(fb):
                if fa.get(kk) != fb.get(kk) and not kk.startswith('/history'): allc[kk.split('[')[0]] += 1
    print(a, '->', b, 'tp changed', len(ch), '| fields changed among those:', dict(cnt.most_common(8)), '| all provinces, any field:', dict(allc.most_common(8)))
for a, b in [('1445_01_01', '1445_01_02'), ('1444_12_01', '1444_12_02'), ('1445_02_01', '1445_02_03'), ('1445_02_28', '1445_03_01'), ('1445_03_01', '1445_03_31'), ('1445_05_01', '1445_06_01')]:
    cmp(a, b)
