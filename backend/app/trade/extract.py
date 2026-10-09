"""Save file -> World (inputs, decisions, recorded results).

Reads variables only: type conversion and renaming, no game arithmetic, no back-solving, no defaults that hide a missing
variable (an absent key is simply absent). Keys the variable registry does not know are counted in World.unmapped_keys.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from app.parsing.clausewitz import as_list, parse
from app.trade import savefile
from app.trade.types import (
    Action,
    CountryInput,
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


@dataclass(frozen=True)
class _PlayerAssets:
    merchants_in_transit: int = 0
    fleets_in_transit: int = 0
    merchants: int = 0
    light_ships: int = 0
    light_ship_types: tuple[tuple[str, int], ...] = ()


def _player_assets(gamestate: str, player: str) -> _PlayerAssets:
    """Player's merchants (all envoys; on the way = action 1, action 2 = at its node, equal to the country's has_trader
    entries in 1,947 of 1,950 country-saves), protect-trade fleets without `on_my_way` (not yet counted, R11), the
    light-ship count (`num_subunits_type_and_cat.light_ship.normal`) and the light ships per unit type in its navies."""
    block = savefile.extract_nested_block(gamestate, "countries", player)
    if block is None:
        return _PlayerAssets()
    country = parse(block[1:-1])
    merchants = country.get("merchants")
    envoys = as_list(merchants.get("envoy")) if isinstance(merchants, dict) else []
    moving = sum(1 for v in envoys if isinstance(v, dict) and v.get("action") == 1)
    fleets = 0
    types: Counter[str] = Counter()
    for fleet in as_list(country.get("navy")):
        if not isinstance(fleet, dict):
            continue
        mission = fleet.get("mission")
        protect = mission.get("protect_mission") if isinstance(mission, dict) else None
        if isinstance(protect, dict) and "on_my_way" not in protect:
            fleets += 1
        types.update(str(ship["type"]) for ship in as_list(fleet.get("ship")) if isinstance(ship, dict) and "type" in ship)
    subunits = country.get("num_subunits_type_and_cat")
    light = subunits.get("light_ship") if isinstance(subunits, dict) else None
    return _PlayerAssets(moving, fleets, len([v for v in envoys if isinstance(v, dict)]),
                         int(_f(light.get("normal"), 0)) if isinstance(light, dict) else 0, tuple(sorted(types.items())))


COUNTRY_KEYS = ("active_idea_groups", "active_policy", "government", "active_age_ability", "modifier", "navy_tradition",
                "blockaded_percent")


def _countries(gamestate: str, tags: set[str]) -> dict[str, CountryInput]:
    """The variables of each country that select its country-scope modifiers (CountryInput)."""
    spans = savefile.country_spans(gamestate)
    out: dict[str, CountryInput] = {}
    for tag in sorted(tags & set(spans)):
        c = parse(savefile.block_fields(gamestate, spans[tag], COUNTRY_KEYS))
        groups = c.get("active_idea_groups")
        reforms = ((c.get("government") or {}).get("reform_stack") or {}).get("reforms") if isinstance(c.get("government"), dict) else None
        out[tag] = CountryInput(
            tag=tag,
            idea_groups=tuple((str(g), int(_f(n, 0))) for g, n in groups.items()) if isinstance(groups, dict) else (),
            policies=tuple(str(p["policy"]) for p in as_list(c.get("active_policy")) if isinstance(p, dict) and "policy" in p),
            reforms=tuple(str(r) for r in as_list(reforms)),
            age_abilities=tuple(str(a) for a in as_list(c.get("active_age_ability"))),
            modifiers=tuple(str(m["modifier"]) for m in as_list(c.get("modifier")) if isinstance(m, dict) and "modifier" in m),
            navy_tradition=_f(c.get("navy_tradition"), 0.0),
            blockaded_percent=_f(c.get("blockaded_percent"), 0.0),
        )
    return out


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
        nodes[nid] = NodeInput(nid, _f(n.get("local_value"), 0.0), bool(n.get("trade_company_region")),
                               tuple(float(x) for x in as_list(n.get("steer_power"))))
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
    start_date = savefile.extract_scalar(text.meta, "start_date") or savefile.extract_scalar(text.gamestate, "start_date") or ""
    assets = _player_assets(text.gamestate, player)
    inputs = WorldInputs(
        game_version=version, date=date, player=player, nodes=nodes, entries=entries, node_order=node_order,
        multipliers=multipliers, decisions=decisions, ironman=text.ironman, mods=_mods(text.meta), dlcs=_dlcs(text.meta),
        start_date=start_date, own_merchants_in_transit=assets.merchants_in_transit, own_fleets_in_transit=assets.fleets_in_transit,
        player_merchants=assets.merchants, player_light_ships=assets.light_ships, player_ship_types=assets.light_ship_types,
        countries=_countries(text.gamestate, {tag for _n, tag in entries}),
    )
    return World(inputs=inputs, recorded=Recorded(entries=rec_entries, nodes=rec_nodes), save_id=save_id, unmapped_keys=dict(unmapped))
