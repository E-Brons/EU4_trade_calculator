"""Classify every save of the datasets (first run 2026-10-06 over the old 110-save fixture manifest (docs/research/data_audit.md): timing, the player's own merchants and
fleets on the way, AI traffic on the way, version, mods -> keep / delete. One-off for the data redesign (2026-10-06)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.parsing.tradenodes import load_trade_graph  # noqa: E402
from app.trade import corpus, quality, savefile  # noqa: E402
from app.trade.extract import extract_world  # noqa: E402


def main() -> None:
    graph = load_trade_graph()
    rows = []
    for e in corpus.manifest():
        with tempfile.TemporaryDirectory() as tmp:
            path = corpus.locate(e, Path(tmp))
            w = extract_world(path, e["id"], graph=graph)
            q = quality.classify(w.inputs)
            ai = quality.ai_in_transit(savefile.read_save_text(path).gamestate, w.inputs.player, w.inputs.node_order)
        verdict = "KEEP" if q.clean else "delete"
        rows.append((e["id"], w.inputs.player, w.inputs.date, w.inputs.start_date, q.timing, q.own_merchants_in_transit,
                     q.own_fleets_in_transit, ai["ai_merchants_in_transit"], ai["ai_fleets_in_transit"], ai["ai_fleet_targets"], q.game_version, q.mods_key, verdict))
        print(*rows[-1], sep=" | ", flush=True)
    out = Path(__file__).resolve().parents[2] / "docs" / "research" / "data_audit_current.md"   # data_audit.md keeps the 2026-10-06 removal record
    head = ["id", "player", "date", "start", "timing", "own merchants en route", "own fleets en route", "AI merchants en route",
            "AI fleets en route", "AI fleet targets", "version", "mods", "verdict"]
    keep = sum(r[-1] == "KEEP" for r in rows)
    lines = ["# Data audit of the old fixture saves (2026-10-06)", "",
             "Classifier: `backend/app/trade/quality.py` (R12 final: trade is computed on the 1st; clean = a save from the 1st after the",
             "game's first computation, with none of the player's own merchants or fleets on the way, on the supported game version).",
             "AI traffic on the way is allowed and listed; it is absent from both the trade entries and the computed values.",
             "Envoy `action` 1 = merchant on the way (action-2 envoys equal the country's `has_trader` entries in 1,947 of 1,950 country-saves).",
             "Script: `backend/scripts/data_audit.py`.", "", f"**{keep} of {len(rows)} saves are clean.**", "",
             "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}: {keep} of {len(rows)} clean")


if __name__ == "__main__":
    main()
