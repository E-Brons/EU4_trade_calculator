import sys, collections, re
sys.path.insert(0,'scripts/research')
import venice_load as V, venice_diff as D

def cls(k):
    parts = k.split('/')
    node, rest = parts[0], parts[1:]
    if len(rest) >= 2 and re.fullmatch(r'[A-Z][A-Z0-9]{2}', rest[0]):
        return 'entry.' + re.sub(r'\[\d+\]', '[]', rest[1])
    return 'node.' + re.sub(r'\[\d+\]', '[]', rest[0])

if __name__ == '__main__':
    fs = V.files(); prev = None
    for p in fs:
        cur = D.nodeflat(p)
        if prev:
            diff = [k for k in set(cur) | set(prev[1]) if cur.get(k) != prev[1].get(k)]
            c = collections.Counter(cls(k) for k in diff)
            tick = p.stem.endswith(('_01',)) and p.stem[6:].split('_')[2] == '01'
            print(f"{prev[0]} -> {p.stem[6:]} {'[TICK]' if tick else ''} {len(diff)}: {dict(c.most_common(14))}")
        prev = (p.stem[6:], cur)
