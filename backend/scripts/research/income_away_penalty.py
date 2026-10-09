"""Income/R02: the away-collection factor across eras. For every country collecting away (collector entry, no
has_capital), ratio = its max_demand there / its modal max_demand at foreign nodes where it does not collect.
R02 final: factor 0.5 (TRADE_NON_CAPITAL_OFFICE); reduced_trade_penalty_on_non_main_tradenode should raise it.
Vanilla observation saves only. Run from backend/: PYTHONPATH=. .venv/bin/python scripts/research/income_away_penalty.py"""
from collections import Counter, defaultdict
from app.trade import corpus

ents = [e for e in corpus.selected() if "/vanilla/" in e.get("zip", "") and "/obs-" in e.get("zip", "")]
ratio = defaultdict(Counter)
for entry, world in corpus.iter_worlds(ents):
    era = world.inputs.date[:3] + "x"
    dem = defaultdict(list); away = []
    for (node, tag), e in world.inputs.entries.items():
        md = world.inputs.multipliers.get((node, tag))
        if md is None:
            continue
        if e.collecting and not e.has_capital:
            away.append((tag, node, md))
        elif not e.collecting and not e.has_capital:
            dem[tag].append(round(md, 3))
    for tag, node, md in away:
        if dem[tag]:
            base = Counter(dem[tag]).most_common(1)[0][0]
            if base:
                ratio[era][round(md / base, 2)] += 1
for era in sorted(ratio):
    n = sum(ratio[era].values())
    print(era, n, "away collectors; ratio to the country's foreign class:", ratio[era].most_common(8))
