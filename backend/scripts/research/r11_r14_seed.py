"""R14 Q5: multiplayer_random_seed / multiplayer_random_count per save; U01/U02 vs S80/S79 trade block equality."""
import sys,re,pickle; sys.path.insert(0,'scripts/research')
import common
from collections import Counter
rows=[]
for e in common.entries():
    t=common._text(e).gamestate
    seed=re.search(r'(?m)^multiplayer_random_seed=(\d+)',t); cnt=re.search(r'(?m)^multiplayer_random_count=(\d+)',t)
    rows.append((e['id'],e['tag'],e['date'],seed and int(seed.group(1)),cnt and int(cnt.group(1))))
for r in rows: print(*r)
print('distinct seeds',len({r[3] for r in rows}),'of',len(rows))
by=Counter(r[2] for r in rows if r[2]=='1444.11.11'); print('1444.11.11 saves',dict(by))
print('1444 start saves distinct seeds:',len({r[3] for r in rows if r[2]=='1444.11.11'}),' distinct counts:',len({r[4] for r in rows if r[2]=='1444.11.11'}))
tr={e['id']:common.block(e,'trade') for e in common.entries() if e['id'] in('S79','S80','U01','U02')}
print('trade block U02==S79:',tr['U02']==tr['S79'],' U01==S80:',tr['U01']==tr['S80'])
