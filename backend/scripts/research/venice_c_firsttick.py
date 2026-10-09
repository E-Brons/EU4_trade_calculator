"""R01: first-tick jump of the foreign-class scalar of GEN, NOV, HSA, RAG, PSK (+0.2/+0.2/+0.1/+0.1/+0.1): what do they share?"""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_load as V, venice_c_lib as L
F=V.files()
def merch(ns):
    d=collections.defaultdict(lambda: collections.Counter())
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k) and e.get('has_trader'):
                kind='steer' if 'type' in e else ('home_collect' if e.get('has_capital') else 'away_collect')
                d[k][kind]+=1
    return d
m8,m9,m10=merch(V.nodes(F[1])),merch(V.nodes(F[2])),merch(V.nodes(F[3]))
for t in ['GEN','NOV','HSA','RAG','PSK','VEN']:
    print(t,'U08',dict(m8[t]),'U09',dict(m9[t]),'U10',dict(m10[t]))
# jump vs number of collecting merchants over all countries (U09 -> U10)
from venice_c_tick_scalar import mode_md
