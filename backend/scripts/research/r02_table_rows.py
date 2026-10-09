"""R02 Q1/Q3: locate the goal-table rows in the corpus, give class and same-class baseline, and the embargo state of the tag."""
import sys, os, collections, pickle, re
sys.path.insert(0, os.path.dirname(__file__))
import common
rows = pickle.loads((common.CACHE / 'r01_rows2.pkl').read_bytes())
goal = """AYU malacca 0.679
BLG genua 0.794
BRA lubeck 0.804
BRI champagne 0.833
C02 carribean_trade 0.897
C04 chesapeake_bay 0.916
CSH beijing 0.656
CSH yumen 0.653
DEC comorin_cape 0.72
DEC gujarat 0.72
DLH lahore 0.821
DLH gujarat 0.688
FRA genua 0.523
GEN champagne 0.887
GEN venice 0.858
GZI zanzibar 0.639
KON ivory_coast 0.478
LAN venice 0.638
MAL ivory_coast 0.736
MNG ganges_delta 0.785
MOR ivory_coast 0.389
PAP genua 0.463
RUS baltic_sea 0.631
SON ivory_coast 0.545
SPA genua 1.069
SPA english_channel 0.7
SUN malacca 0.703
SWI genua 0.645
TUR ragusa 0.761
TUR venice 0.92""".splitlines()
masters = {}
def master(s):
    if s not in masters: masters[s] = pickle.loads((common.CACHE / f'master_{s}.pkl').read_bytes())
    return masters[s]
foreign = collections.defaultdict(set); dom = collections.defaultdict(set)
for r in rows:
    if r['coll'] and not r['cap']: continue
    (dom if (r['ishome'] or r['top']) else foreign)[(r['save'], r['tag'])].add(r['md'])
out = []
for line in goal:
    tag, node, md = line.split(); md = float(md)
    hits = [r for r in rows if r['tag'] == tag and r['node'] == node and abs(r['md'] - md) < 0.0006 and r['coll'] and not r['cap']]
    for r in hits[:1]:
        k = (r['save'], tag)
        emb = master(r['save'])['countries'].get(tag, {}).get('trade_embargoed_by')
        f = sorted(foreign[k]); d = sorted(dom[k])
        out.append((tag, node, r['save'], md, 'top' if r['top'] else 'foreign-class', emb, f[:3], d[:3]))
for o in out: print(o)
print('found', len(out), 'of', len(goal))
