"""Independent verification (R09 Q4 country-level fields)."""
import sys, re, collections
sys.path.insert(0, 'scripts/research')
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
PLAYED = {'S79', 'S80', 'U01', 'U02'}
C = collections.Counter(); F = collections.defaultdict(list)
def aslist(x): return x if isinstance(x, list) else ([] if x is None else [x])
for e in common.entries():
    sid = e['id']; ns = common.nodes(e); cs = common.block(e, 'countries'); pr = common.block(e, 'provinces')
    cs = {t: c for t, c in cs.items() if isinstance(c, dict)}
    capnode = {}; traders = collections.Counter(); ships = collections.Counter(); tfrom = collections.defaultdict(set); tto = collections.defaultdict(set)
    steer_home = collections.Counter(); collect_away = collections.Counter(); pernodeents = {}
    for n in ns:
        for t, v in n.items():
            if not (TAG.match(t) and isinstance(v, dict)): continue
            if v.get('has_capital'): capnode[t] = n['definitions']
            if v.get('has_trader'): traders[t] += 1
            ships[t] += int(v.get('light_ship', 0) or 0)
            for x in aslist(v.get('t_from')) if not isinstance(v.get('t_from'), dict) else [v['t_from']]:
                pass
            for key, store in (('t_from', tfrom), ('t_to', tto)):
                tv = v.get(key)
                if isinstance(tv, dict): store[t].update(tv.keys())
    # home-node steering/collect-away counts for transfer_home_bonus
    for n in ns:
        for t, v in n.items():
            if not (TAG.match(t) and isinstance(v, dict)): continue
            if v.get('has_trader') and 'type' in v and capnode.get(t) == n['definitions']: pass
    # steering into the home node: merchant steers from another node into home node? approximate by "has_trader with type key at node whose steer target is home" needs graph; test the 362 claim by weaker conditions separately
    for t, c in cs.items():
        C['country_saves'] += 1
        if 'traded' in c: C['traded_present'] += 1
        if 'mercantilism' in c: C['merc_present'] += 1; C['merc_min'] = min(C['merc_min'] or 99, c['mercantilism']) if C['merc_min'] else c['mercantilism']; C['merc_max'] = max(C['merc_max'], c['mercantilism'])
        if 'traded_bonus' in c: C['traded_bonus'] += 1
        if 'trade_mission' in c: C['trade_mission'] += 1
        if 'transfer_home_bonus' in c:
            if sid in PLAYED: C['thb_played_present'] += 1; C['thb_played_nonzero'] += c['transfer_home_bonus'] != 0
            else: C['thb_start_nonzero'] += c['transfer_home_bonus'] != 0; C['thb_start_present'] += 1
        if t in capnode:
            C['has_capital_cs'] += 1
            pid = str(-int(c['trade_port'])) if 'trade_port' in c else None
            C['trade_port==capital'] += c.get('trade_port') == c.get('capital')
            C['node(trade_port)==has_capital_node'] += pid in pr and pr[pid].get('trade') == capnode[t]
            # envoys
            env = aslist(c.get('merchants', {}).get('envoy')) if isinstance(c.get('merchants'), dict) else []
            a2 = sum(1 for x in env if x.get('action') == 2)
            C['envoy_action2==has_trader_nodes'] += a2 == traders[t]
            C['envoys>=traders'] += len(env) >= traders[t]
        env = aslist(c.get('merchants', {}).get('envoy')) if isinstance(c.get('merchants'), dict) else []
        for x in env:
            C['envoy_total'] += 1; C['envoy_type1'] += x.get('type') == 1
            C['envoy_action2'] += x.get('action') == 2; C['envoy_action1'] += x.get('action') == 1; C['envoy_noaction'] += 'action' not in x
        if 'trade_embargoes' in c or 'trade_embargoed_by' in c or 'num_of_trade_embargos' in c:
            C['embargo_cs_' + sid] += 1
            if 'num_of_trade_embargos' in c: C['num_emb==len'] += c['num_of_trade_embargos'] == len(aslist(c.get('trade_embargoes'))); C['num_emb_present'] += 1
        for b in aslist(c.get('trade_embargoed_by')):
            C['emb_by_pairs'] += 1; C['emb_by_recip'] += t in aslist(cs.get(b, {}).get('trade_embargoes'))
        for b in aslist(c.get('trade_embargoes')):
            C['emb_pairs'] += 1; C['emb_recip'] += t in aslist(cs.get(b, {}).get('trade_embargoed_by'))
        if 'transfer_trade_power_from' in c:
            C['ttp_from_cs'] += 1; C['ttp_from_saves_' + sid] += 1
            ok = set(aslist(c['transfer_trade_power_from'])) == tfrom[t]; C['ttp_from_match'] += ok
            if not ok: F['from'].append((sid, t, aslist(c['transfer_trade_power_from']), sorted(tfrom[t])))
        if 'transfer_trade_power_to' in c:
            C['ttp_to_cs'] += 1; C['ttp_to_saves_' + sid] += 1
            ok = set(aslist(c['transfer_trade_power_to'])) == tto[t]; C['ttp_to_match'] += ok
            if not ok: F['to'].append((sid, t, aslist(c['transfer_trade_power_to']), sorted(tto[t])))
        if 'num_ships_protecting_trade' in c:
            C['nsp'] += 1; ok = c['num_ships_protecting_trade'] == ships[t]; C['nsp_match'] += ok
            if not ok: F['nsp'].append((sid, t, c['num_ships_protecting_trade'], ships[t]))
print({k: v for k, v in sorted(C.items()) if not k.startswith(('embargo_cs_', 'ttp_from_saves_', 'ttp_to_saves_'))})
print('embargo fields per save', {k[len('embargo_cs_'):]: v for k, v in C.items() if k.startswith('embargo_cs_')})
print('ttp_from saves', len([k for k in C if k.startswith('ttp_from_saves_')]), 'ttp_to saves', len([k for k in C if k.startswith('ttp_to_saves_')]), 'either', len({k.split('_')[-1] for k in C if k.startswith(('ttp_from_saves_', 'ttp_to_saves_'))}))
for k, v in F.items(): print('FAIL', k, len(v), v[:14])
print('nsp fails by save', collections.Counter(x[0] for x in F['nsp']))
