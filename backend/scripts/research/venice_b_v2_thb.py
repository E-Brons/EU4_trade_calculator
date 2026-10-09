"""SECOND PASS (raw text only): transfer_home_bonus / 0.1 == number of steering merchants (0 if any away collector), all countries of two Venice saves."""
import re, sys, collections
sys.path.insert(0, 'scripts/research')
import venice_b_v2_raw as R
from app.trade import savefile
by = {p.stem[6:]: p for p in R.files()}
for tag in sys.argv[1:]:
    p = by[tag]; nodes = R.nodes(p)
    steer = collections.Counter(); away = collections.Counter(); home = set()
    for name, (ents, seg, w) in nodes.items():
        for c, d in ents.items():
            if 'has_capital' in d: home.add(c)
            if 'has_trader' in d:
                if 'type' in d: steer[c] += 1
                elif 'has_capital' not in d: away[c] += 1
    cs = savefile.extract_top_level_block(R.text(p), 'countries')
    ok = tot = 0
    for c in home:
        m = re.search(r'\n\t' + c + r'=\{', cs)
        if not m: continue
        t = re.search(r'transfer_home_bonus=([\d.]+)', cs[m.end(): m.end() + 400000])
        if not t: continue
        tot += 1; ok += round(float(t.group(1)) / 0.1) == (0 if away[c] else steer[c])
    print(tag, ok, '/', tot)
