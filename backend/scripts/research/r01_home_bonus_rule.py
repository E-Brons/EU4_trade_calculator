"""R01/R09: which merchants count for transfer_home_bonus? Cross-section over all clean saves (no experiment needed):
for every country compare its stored transfer_home_bonus with 0.1 x the count under candidate rules.
Run from backend/: .venv/bin/python scripts/research/r01_home_bonus_rule.py"""
import re
from collections import Counter, defaultdict
from app.trade import corpus, game_data, savefile

g = game_data.graph()
into = defaultdict(set)
for n in g.nodes():
    for t in g.outgoing(n):
        into[t].add(n)


def thb_by_country(path_text):
    out = {}
    c0 = path_text.index("\ncountries={")
    for m in re.finditer(r"\n\t([A-Z0-9]{3})=\{", path_text[c0:]):
        s = c0 + m.start(); e = path_text.find("\n\t}", s)
        h = re.search(r"\n\t\ttransfer_home_bonus=([\d.]+)", path_text[s:e])
        out[m.group(1)] = float(h.group(1)) if h else 0.0
    return out


rules = {
    "A steerers anywhere": lambda p: p["steer_all"],
    "B steerers in nodes linked directly into home": lambda p: p["steer_into"],
    "C steerers steering TO home": lambda p: p["steer_to_home"],
    "D B + home merchant": lambda p: p["steer_into"] + p["home_m"],
    "E C + home merchant": lambda p: p["steer_to_home"] + p["home_m"],
    "F all merchants (steer+collect, home incl.)": lambda p: p["steer_all"] + p["collect_all"],
}
hits = Counter(); n = 0; zero_with_away = Counter(); misses = defaultdict(list)
for entry, world in corpus.iter_worlds(corpus.selected()):
    text = savefile.read_save_text(corpus.locate(entry, None) if False else None) if False else None
    per = defaultdict(lambda: dict(steer_all=0, steer_into=0, steer_to_home=0, home_m=0, collect_all=0, away=0, home=None))
    for (node, tag), e in world.inputs.entries.items():
        if e.has_capital:
            per[tag]["home"] = node
    for (node, tag), e in world.inputs.entries.items():
        p = per[tag]; home = p["home"]
        if not e.has_trader or home is None:
            continue
        if e.steering:
            p["steer_all"] += 1
            if home in into and node in into[home]:
                p["steer_into"] += 1
            tg = g.outgoing(node)
            if e.steer_link is not None and e.steer_link < len(tg) and tg[e.steer_link] == home:
                p["steer_to_home"] += 1
        elif node == home:
            p["home_m"] += 1
        else:
            p["collect_all"] += 1; p["away"] += 1
    thb = world.inputs.transfer_home_bonus if hasattr(world.inputs, "transfer_home_bonus") else None
    if thb is None:
        break
    for tag, p in per.items():
        if p["home"] is None or tag not in thb:
            continue
        n += 1
        for name, f in rules.items():
            pred = 0.0 if p["away"] else round(0.1 * f(p), 3)
            if abs(pred - thb[tag]) < 1e-6:
                hits[name] += 1
            elif len(misses[name]) < 3:
                misses[name].append((entry["id"], tag, thb[tag], pred, dict(p)))
print("countries", n)
for name in rules:
    print(f"{hits[name]:6d} / {n}  {name}")
