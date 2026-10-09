"""Verifier (independent): R10 C-03 counts on num_collectors_including_pirates / PIR entries / cape_of_good_hope."""
import sys, re, collections
sys.path.insert(0, 'scripts/research')
import common
C = collections.Counter(); nototal = collections.Counter(); keysets = collections.Counter()
for e in common.entries():
    for n in common.nodes(e):
        C['nodes'] += 1
        pir = n.get('PIR')
        C['PIR present'] += isinstance(pir, dict)
        if isinstance(pir, dict): keysets[tuple(sorted(pir))] += 1
        if 'total' not in n: nototal[n['definitions']] += 1
        if 'num_collectors_including_pirates' in n and 'num_collectors' in n:
            C['ncp-nc=%s' % (n['num_collectors_including_pirates'] - n['num_collectors'])] += 1
            C['cpp==cp'] += abs(n.get('collector_power_including_pirates', 0) - n.get('collector_power', 0)) < 1e-9
            C['pair exists'] += 1
        else:
            C['pair absent'] += 1
            C['absent & no total'] += 'total' not in n
print(dict(C)); print(keysets); print(nototal)
