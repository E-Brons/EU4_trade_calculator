"""Idea-group names vs f for every ship-owning country (leaderless), S79/S80/U03-U05: does a national idea group separate f != 1 exactly?"""
import sys, pickle
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from collections import defaultdict, Counter
E = {e['id']: e for e in L.OLD + L.NEW}
rows = pickle.load(open('/tmp/eu4research/cache/u345_f_rows.pkl', 'rb'))
def leader(x): return any(f['leader'] for f in x['fleets'])
status = {}
for x in rows:
    k = (x['sid'], x['tag'])
    s = status.setdefault(k, {'leader': False, 'odd': False})
    s['leader'] |= leader(x); s['odd'] |= (x['f'] != 1.0 and not leader(x))
groups = defaultdict(lambda: Counter())
for (sid, tag), s in status.items():
    if s['leader']: continue
    c = common.block(E[sid], 'countries')[tag]
    for g in (c.get('active_idea_groups') or {}):
        groups[g]['f!=1' if s['odd'] else 'f=1'] += 1
print('leaderless (save,country) pairs:', sum(1 for s in status.values() if not s['leader']))
print('idea groups occurring with f != 1:', {g: dict(c) for g, c in groups.items() if c['f!=1']})
print('groups with ANY f!=1 and ZERO f=1 (perfectly separating in that direction):', sorted(g for g, c in groups.items() if c['f!=1'] and not c['f=1']))
print('all national-looking groups seen (not in generic list) with f=1 counts:', {g: dict(c) for g, c in groups.items() if g.endswith('_ideas') and g.split('_')[0] not in ('administrative','economic','offensive','defensive','quality','quantity','spy','humanist','religious','influence','innovativeness','exploration','maritime','trade','expansion','aristocracy','infrastructure','naval','diplomatic')})
