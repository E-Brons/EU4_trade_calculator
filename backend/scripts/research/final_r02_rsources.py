"""R02 final, test 8: who could have reduced_trade_penalty_on_non_main_tradenode > 0?
Sources in the game files of EU4 v1.37.5.0 (grep over common/, see the final document): event modifiers nov_rus_asian_market_access (0.1),
spa_victory_netherlands_modifier (0.25), hsn_trading_network (0.1), TIM_western_markets (0.33); static modifier gbr_emperor_of_india_overlord_bonus
(0.25); China decree increase_trade_cooperation_decree (0.25); great projects itchan_kala, nizwa_fort, panama_canal; advisor skill_scaled_modifier
(0.05, flag hun_trader_scaling_bonus_flag).  Count the names in the raw gamestate text of every save, and print the country blocks that hold them.
Usage: .venv/bin/python scripts/research/final_r02_rsources.py"""
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, "scripts/research")
import common
from app.trade import corpus, savefile

NAMES = ["nov_rus_asian_market_access", "spa_victory_netherlands_modifier", "hsn_trading_network", "TIM_western_markets",
         "gbr_emperor_of_india", "increase_trade_cooperation_decree", "itchan_kala", "nizwa_fort", "panama_canal",
         "hun_trader_scaling_bonus_flag", "reduced_trade_penalty_on_non_main_tradenode"]
hits = defaultdict(dict)
for e in common.entries():
    if e["id"] in ("U01", "U02"):
        continue
    with tempfile.TemporaryDirectory() as tmp:
        txt = savefile.read_save_text(corpus.locate(e, Path(tmp))).gamestate
    for n in NAMES:
        k = txt.count(n)
        if k:
            hits[n][e["id"]] = k
    print(e["id"], "scanned", flush=True) if e["id"] in ("S79", "U06") else None
for n in NAMES:
    print(n, "->", dict(hits[n]) if hits[n] else "not present in any save")
