"""R04: fraction of the transfer (t_out = f x (val - 0.1)) per giver over the whole corpus (S01-S80, U01-U06) and the Venice series, with the giver's subject_type from the diplomacy block."""
import sys, re, tempfile, collections
from pathlib import Path
sys.path.insert(0, "scripts/research")
import common, venice_load as V
from app.trade import corpus
from final_r12_common import entries_of

def givers(nodes):
    g = collections.defaultdict(list)
    for n in nodes:
        for t, e in entries_of(n).items():
            if 't_out' in e and 'val' in e and e['val'] > 0.1:
                g[t].append(round(e['t_out'] / (e['val'] - 0.1), 3) if e['val'] - 0.1 > 0 else None)
    return g

def subject_types(text, tags):
    out = {}
    for m in re.finditer(r'dependency=\{\s*first="([A-Z0-9]+)"\s*second="([A-Z0-9]+)"(.*?)\}', text, re.S):
        if m.group(2) in tags:
            st = re.search(r'subject_type="([^"]+)"', m.group(3))
            out[m.group(2)] = (m.group(1), st.group(1) if st else None)
    return out

def report(name, nodes, loader):
    g = givers(nodes)
    if not g: return None
    text = loader()
    st = subject_types(text, set(g))
    return name, {t: (sorted(set(v)), st.get(t)) for t, v in g.items()}

if __name__ == '__main__':
    res = collections.Counter(); seen = {}
    for e in common.entries():
        if e['id'] in ('U01', 'U02'): continue
        nodes = common.nodes(e)
        if not any('t_out' in x for n in nodes for x in entries_of(n).values()): continue
        def load(e=e):
            with tempfile.TemporaryDirectory() as tmp:
                return Path(corpus.locate(e, Path(tmp))).read_text(encoding='utf-8', errors='replace')
        r = report(e['id'], nodes, load)
        if r:
            for t, (fr, st) in r[1].items():
                res[(tuple(fr), st[1] if st else None)] += 1; seen.setdefault((tuple(fr), st[1] if st else None), []).append((e['id'], t))
    for p in V.files():
        nodes = V.nodes(p)
        r = report(p.stem, nodes, lambda p=p: p.read_text(encoding='utf-8', errors='replace'))
        if r:
            for t, (fr, st) in r[1].items():
                res[(tuple(fr), st[1] if st else None)] += 1; seen.setdefault((tuple(fr), st[1] if st else None), []).append((p.stem[6:], t))
    for k, v in sorted(res.items(), key=lambda x: -x[1]): print(v, 'giver-saves  ratios', k[0][:4], 'subject_type', k[1], seen[k][:3])
