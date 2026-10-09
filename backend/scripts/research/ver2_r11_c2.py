import sys
sys.path.insert(0, 'scripts/research')
import ver2_r11_c as C
from collections import Counter, defaultdict
data = {s: C.load(s) for s in C.SAVES}
def run(clsf, name):
    tot = ok = alt = 0; bad = []
    for s in C.SAVES:
        byc = defaultdict(lambda: defaultdict(list))
        for (tag, node), x in data[s].items():
            if x['light'] == 0: byc[tag][clsf(x)].append(round(x['mp'] - x['pp'] - x['prev'] - x['cap'] - x['mods'], 3))
        for (tag, node), x in data[s].items():
            if x['light'] == 0 or not byc[tag].get(clsf(x)): continue
            R = Counter(byc[tag][clsf(x)]).most_common(1)[0][0]
            r = x['mp'] - x['pp'] - x['prev'] - x['cap'] - x['mods']
            tot += 1
            if abs(r - x['sp'] - R) <= 0.0025: ok += 1
            else: bad.append((s, tag, node, round(r - x['sp'] - R, 3)))
            if abs(r - R) <= 0.0025: alt += 1
    print(name, 'tot', tot, 'ok', ok, 'alt', alt, 'bad', bad[:8])
run(lambda x: x['cls'], 'class=(trader,steer,collect)')
run(lambda x: x['cls'][0], 'class=has_trader')
run(lambda x: 0, 'class=none (country only)')
run(lambda x: (x['cls'][0], x['cls'][2]), 'class=(trader,collect)')
