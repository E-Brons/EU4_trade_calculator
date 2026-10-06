"""Save file -> World (inputs, decisions, recorded results).

Reads variables only: type conversion and renaming, no game arithmetic, no back-solving, no defaults that hide a missing
variable (an absent key is simply absent). Keys the variable registry does not know are counted in World.unmapped_keys.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from app.parsing.clausewitz import as_list, parse
from app.trade import savefile
from app.trade.types import (
    Action,
    Decisions,
    EntryInput,
    EntryRecorded,
    Modifier,
    NodeDecision,
    NodeInput,
    NodeRecorded,
    Recorded,
    World,
    WorldInputs,
)
from app.trade.variables import ENTRY_KEYS, NODE_KEYS

_TAG = re.compile(r"^[A-Z0-9]{2,4}$")


def _f(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _pairs(value) -> tuple[tuple[str, float], ...]:
    return tuple((str(k), float(v)) for k, v in value.items()) if isinstance(value, dict) else ()


def _modifiers(value) -> tuple[Modifier, ...]:
    return tuple(
        Modifier(str(m.get("key")), _f(m.get("duration"), 0.0), _f(m.get("power"), 0.0), _f(m.get("power_modifier"), 0.0))
        for m in as_list(value)
        if isinstance(m, dict)
    )


def _game_version(meta: str) -> str:
    block = savefile.extract_top_level_block(meta, "savegame_version") or ""
    parts = [re.search(rf"{k}\s*=\s*(\d+)", block) for k in ("first", "second", "third")]
    return ".".join(m.group(1) for m in parts) if all(parts) else "unknown"


def _mods(meta: str) -> tuple[str, ...]:
    block = savefile.extract_top_level_block(meta, "mods_enabled_names") or ""
    return tuple(re.findall(r'(?<![A-Za-z_])name="([^"]*)"', block))


def _dlcs(meta: str) -> tuple[str, ...]:
    block = savefile.extract_top_level_block(meta, "dlc_enabled") or ""
    return tuple(re.findall(r'"([^"]*)"', block))


def extract_world(path: str | Path, save_id: str = "", graph=None) -> World:
    """`graph` (TradeGraph) is only used to turn a steering link index into a target node id."""
    text = savefile.read_save_text(path)
    player = savefile.extract_scalar(text.meta, "player") or savefile.extract_scalar(text.gamestate, "player")
    if not player:
        raise ValueError("Could not find the player's country tag in the save")
    date = savefile.extract_scalar(text.meta, "date") or savefile.extract_scalar(text.gamestate, "date") or ""

    block = savefile.extract_top_level_block(text.gamestate, "trade")
    if block is None:
        raise ValueError("No top-level 'trade' block in the save")
    tree = parse(block[1:-1])
    unmapped: Counter[str] = Counter({f"trade.{k}": 1 for k in tree if k != "node"})

    raw_nodes = [n for n in as_list(tree.get("node")) if isinstance(n, dict) and n.get("definitions")]
    node_order = tuple(n["definitions"] for n in raw_nodes)

    nodes: dict[str, NodeInput] = {}
    entries: dict[tuple[str, str], EntryInput] = {}
    multipliers: dict[tuple[str, str], float] = {}
    rec_nodes: dict[str, NodeRecorded] = {}
    rec_entries: dict[tuple[str, str], EntryRecorded] = {}
    decisions = Decisions()

    for n in raw_nodes:
        nid = n["definitions"]
        for key in n:
            if not (_TAG.match(key) and isinstance(n[key], dict)) and key not in NODE_KEYS:
                unmapped[f"node.{key}"] += 1
        nodes[nid] = NodeInput(nid, _f(n.get("local_value"), 0.0), bool(n.get("trade_company_region")))
        rec_nodes[nid] = NodeRecorded(
            current=_f(n.get("current")),
            outgoing=_f(n.get("outgoing")),
            value_added_outgoing=_f(n.get("value_added_outgoing")),
            retention=_f(n.get("retention")),
            retain_power=_f(n.get("retain_power")),
            pull_power=_f(n.get("pull_power")),
            total=_f(n.get("total")),
            steer_weights=tuple(float(x) for x in as_list(n.get("steer_power"))),
            incoming=tuple(
                (node_order[int(i["from"]) - 1] if 0 < int(i["from"]) <= len(node_order) else f"#{i['from']}", float(i["value"]), float(i.get("add", 0.0)))
                for i in as_list(n.get("incoming"))
                if isinstance(i, dict)
            ),
            num_collectors=int(n["num_collectors"]) if "num_collectors" in n else None,
            num_collectors_including_pirates=int(n["num_collectors_including_pirates"]) if "num_collectors_including_pirates" in n else None,
            collector_power=_f(n.get("collector_power")),
            collector_power_including_pirates=_f(n.get("collector_power_including_pirates")),
        )
        outgoing = graph.outgoing(nid) if graph is not None and nid in graph else ()
        for tag, c in n.items():
            if not (_TAG.match(tag) and isinstance(c, dict)):
                continue
            for key in c:
                if key not in ENTRY_KEYS:
                    unmapped[f"entry.{key}"] += 1
            if "max_demand" in c:
                multipliers[(nid, tag)] = float(c["max_demand"])
            if not (set(c) - {"max_demand"}):
                continue
            has_trader = bool(c.get("has_trader"))
            steering = "type" in c
            steer_link = int(_f(c.get("steer_power"), 0.0))
            e = EntryInput(
                tag=tag, node=nid,
                province_power=_f(c.get("province_power"), 0.0),
                ship_power=_f(c.get("ship_power"), 0.0),
                light_ships=int(_f(c.get("light_ship"), 0)),
                has_capital=bool(c.get("has_capital")),
                has_trader=has_trader,
                steering=steering,
                steer_link=steer_link,
                collecting="total" in c,
                add=_f(c.get("add")),
                t_in=_f(c.get("t_in"), 0.0),
                t_out=_f(c.get("t_out"), 0.0),
                modifiers=_modifiers(c.get("modifier")),
                transfers_to=_pairs(c.get("t_to")),
                transfers_from=_pairs(c.get("t_from")),
            )
            entries[(nid, tag)] = e
            rec_entries[(nid, tag)] = EntryRecorded(
                prev=_f(c.get("prev")), max_pow=_f(c.get("max_pow")), max_demand=_f(c.get("max_demand")), val=_f(c.get("val")),
                potential=_f(c.get("potential")), already_sent=_f(c.get("already_sent")), money=_f(c.get("money")),
                share_total=_f(c.get("total")), power_fraction=_f(c.get("power_fraction")),
            )
            # Decision rule (extraction fact, edge case EC-P07): a merchant that neither steers nor is marked collecting has no recorded action.
            if not has_trader:
                action = Action.NONE
            elif steering:
                action = Action.STEER
            elif e.has_capital or e.collecting:
                action = Action.COLLECT
            else:
                action = Action.NONE
            target = outgoing[steer_link] if (action == Action.STEER and steer_link < len(outgoing)) else None
            if action != Action.NONE or e.light_ships:
                decisions.by_entry[(tag, nid)] = NodeDecision(action, target, e.light_ships)

    version = _game_version(text.meta)
    inputs = WorldInputs(
        game_version=version, date=date, player=player, nodes=nodes, entries=entries, node_order=node_order,
        multipliers=multipliers, decisions=decisions, ironman=text.ironman, mods=_mods(text.meta), dlcs=_dlcs(text.meta),
    )
    return World(inputs=inputs, recorded=Recorded(entries=rec_entries, nodes=rec_nodes), save_id=save_id, unmapped_keys=dict(unmapped))
