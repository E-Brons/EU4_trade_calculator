"""Independent check of the R06 claims (extras decomposition, merchant term R = 2 + 5a + 15b in the played saves)."""
import sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
from common import as_list

PLAYED = {'S79', 'S80', 'U01', 'U02'}
def q(x): return int(round(float(x) * 1000))
def tags(n): return {t: c for t, c in n.items() if isinstance(c, dict) and t.upper() == t and len(t) <= 4}
def klass(c):
    a = 'home' if c.get('has_capital') else 'collect-away' if 'total' in c else 'steer' if 'type' in c else 'passive'
    return a + ('+merchant' if c.get('has_trader') else '')
def mods(c): return [m for m in as_list(c.get('modifier')) if isinstance(m, dict)]

table = collections.defaultdict(collections.Counter); resid_out = 0; nE = 0
resid_entries = []   # (sid, node, tag, cls, residual_thousandths, has_trader)
recalled = []; modkeys = collections.defaultdict(collections.Counter)
for e in common.entries():
    sid = e['id']
    for n in common.nodes(e):
        for tag, c in tags(n).items():
            if 'max_pow' not in c: continue
            nE += 1
            ex = q(c['max_pow']) - q(c.get('province_power', 0)) - q(c.get('ship_power', 0)) - q(c.get('prev', 0))
            cl = klass(c); table[cl][ex / 1000] += 1
            mp = sum(q(m.get('power', 0)) for m in mods(c))
            r = ex - 5000 * bool(c.get('has_capital')) - mp
            resid_entries.append((sid, n['definitions'], tag, cl, r, bool(c.get('has_trader'))))
            if sid not in PLAYED and r != 0: resid_out += 1
            for m in mods(c):
                modkeys[m.get('key')][(cl, m.get('power'))] += 1
                if m.get('key') == 'merchant_recalled': recalled.append((m.get('power'), m.get('duration'), sid))
print('entries with max_pow', nE)
for cl, cn in sorted(table.items()): print(cl, sum(cn.values()), cn.most_common(8))
print('nonzero residual (after 5*capital and modifier powers) outside played saves:', resid_out)
print('merchant_recalled occurrences', len(recalled), 'powers', set(p for p, d, s in recalled), 'duration min/max', min(d for p, d, s in recalled), max(d for p, d, s in recalled), 'in played only', all(s in PLAYED for p, d, s in recalled))
for k, v in sorted(modkeys.items(), key=lambda kv: -sum(kv[1].values()))[:10]: print(k, sum(v.values()), dict(v))

# per country-save residual among merchant entries
by = collections.defaultdict(list)
for sid, node, tag, cl, r, ht in resid_entries:
    if ht: by[(sid, tag)].append((node, cl, r / 1000))
nz = {k: v for k, v in by.items() if any(x[2] for x in v)}
print('country-saves with merchants', len(by), 'with nonzero residual', len(nz), 'all in played:', all(k[0] in PLAYED for k in nz))
single = sum(1 for k, v in nz.items() if len(set(x[2] for x in v)) == 1)
print('single-valued', single, 'of', len(nz), 'values', collections.Counter(next(iter(set(x[2] for x in v))) for k, v in nz.items() if len(set(x[2] for x in v)) == 1))
print('multi-valued', [(k, sorted(set(x[2] for x in v))) for k, v in nz.items() if len(set(x[2] for x in v)) > 1])
# entries without has_trader that still carry a residual
print('no-has_trader entries with residual != 0:', [(s, n, t, cl, r / 1000) for s, n, t, cl, r, ht in resid_entries if not ht and r != 0])

# the rule R = 2 + 5*[mercantile/pious reform] + 15*[trade_ideas>=5]
REF = {'mercantilistic_approach_reform', 'pious_merchants_reform'}
def pred_R(cb, tag):
    c = cb.get(tag, {})
    g = c.get('government'); reforms = set(g.get('reform_stack', {}).get('reforms', []) or []) if isinstance(g, dict) else set()
    ideas = c.get('active_idea_groups') or {}
    return 2 + 5 * bool(reforms & REF) + 15 * ((ideas.get('trade_ideas') or 0) >= 5)
fit = collections.Counter(); bad = []
for e in common.entries():
    sid = e['id']
    if sid not in PLAYED: continue
    cb = common.block(e, 'countries')
    for (s, tag), v in by.items():
        if s != sid: continue
        p = pred_R(cb, tag); vals = sorted(set(x[2] for x in v))
        ok = vals == [float(p)]
        fit[(sid, ok)] += 1
        if not ok: bad.append((sid, tag, vals, p))
print('rule fit per country-save (merchant countries) in played saves:', dict(fit)); print(bad)
# entry-level reproduction of extras in the played saves
ok = tot = 0; snap_bad = 0; snap_n = 0
for e in common.entries():
    sid = e['id']; cb = common.block(e, 'countries') if sid in PLAYED else None
    for sid_, node, tag, cl, r, ht in resid_entries if False else []: pass
# recompute entry-level with R
cache = {}
for sid, node, tag, cl, r, ht in resid_entries:
    if sid in PLAYED:
        if sid not in cache: cache[sid] = common.block([x for x in common.entries() if x['id'] == sid][0], 'countries')
        R = pred_R(cache[sid], tag) * 1000 if ht else 0
        tot += 1; ok += (r == R)
    else:
        snap_n += 1; snap_bad += (r != 0)
print('played entries reproduced with R(country)*[has_trader]:', ok, 'of', tot, '; snapshot entries not reproduced with R=0:', snap_bad, 'of', snap_n)

# snapshot prediction of R>0
cnt = collections.Counter()
for sid in ('S14', 'S42', 'S67', 'S78'):
    cb = common.block([x for x in common.entries() if x['id'] == sid][0], 'countries')
    for (s, tag), v in by.items():
        if s == sid: cnt[(sid, pred_R(cb, tag))] += 1
print('snapshots: country-saves with merchants by rule-predicted R (observed R always 0):', sorted(cnt.items()), 'sum', sum(cnt.values()))

# feature-search counts (S80, S79): +5 countries vs reforms
for sid in ('S80', 'S79'):
    cb = common.block([x for x in common.entries() if x['id'] == sid][0], 'countries')
    pos = [k[1] for k, v in by.items() if k[0] == sid and len(set(x[2] for x in v)) == 1 and next(iter(set(x[2] for x in v))) in (7.0, 22.0)]
    neg = [k[1] for k, v in by.items() if k[0] == sid and len(set(x[2] for x in v)) == 1 and next(iter(set(x[2] for x in v))) not in (7.0, 22.0)]
    rf = lambda t: set((cb[t].get('government') or {}).get('reform_stack', {}).get('reforms', []) or [])
    for name in sorted(REF):
        print(sid, name, 'pos hit', sum(name in rf(t) for t in pos), 'of', len(pos), ' neg hit (false positives)', sum(name in rf(t) for t in neg), 'of', len(neg))
    print(sid, 'positives without either reform:', [t for t in pos if not (rf(t) & REF)])
