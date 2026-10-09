"""Venice's own max_demand across the series vs transfer_home_bonus and merchant state."""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_load as V
for i,p in enumerate(V.files()):
    ns=V.nodes(p); c=V.load(p,'countries')['VEN']
    md={n['definitions']:n['VEN'].get('max_demand') for n in ns if isinstance(n.get('VEN'),dict)}
    cnt=collections.Counter(md.values())
    merch=[n['definitions'] for n in ns if isinstance(n.get('VEN'),dict) and 'has_trader' in n['VEN']]
    print(f"U{7+i:02d} {p.stem[6:]} bonus={c.get('transfer_home_bonus')} md@venice={md.get('venice')} md@alex={md.get('alexandria')} md@ragusa={md.get('ragusa')} classes={dict(cnt)} merchants={merch}")
