"""Extracts trade-relevant data from an EU4 `.eu4` save file.

A real `.eu4` is a zip containing `gamestate`, `meta`, and `ai`; Ironman
saves have those members in Paradox's binary format and need melting
first (see `rakaly.py`). We also accept an already-melted flat text file
(not zipped) as produced by pdx.tools' "Melt" button -- meta and gamestate
end up concatenated into one document there, which this module handles
the same way it handles a real save's `gamestate` (the fields we need,
`player=`/`trade={...}`, are present either way).

`gamestate` is huge (tens of MB once melted), so rather than running the
full Clausewitz tokenizer over the whole file we scan for the byte range
of just the top-level `trade={...}` block and tokenize only that.

FIELD NAMES BELOW ARE VERIFIED against a real melted 1.37.5 save (see
`scripts/inspect_save.py`), not guessed. Two things about the format that
shaped this module:

- Inside `node={...}`, each country present is a sub-block keyed directly
  by its 3-letter tag (`TUR={...}`, `PIR={...}`, colonial nations like
  `C08={...}`) -- NOT a repeated `country={tag=...}` block as an earlier
  version of this module assumed. We detect these by key shape
  (`^[A-Z0-9]{2,4}$` and a dict value) rather than an allowlist, since new
  tags (colonial nations, custom nations) aren't enumerable in advance.
- Whether a country's merchant *collects* or *steers* isn't stored as an
  explicit enum: `has_trader=yes` marks a merchant present, and `type=1`
  additionally present means it's set to Steer; `has_trader=yes` with no
  `type` means Collect. `power_fraction`/`money` are only present for
  collectors (money is that node's realized ducats/month for that
  country -- useful to sanity-check the whole pipeline against the
  in-game ledger).
- The save does *not* record which specific outgoing link a country's
  merchant steers to, only an aggregate per-link `steer_power` at the
  *node* level (repeated once per outgoing link, in the same order as the
  node's `outgoing` edges in `data/tradenodes.json`). We use that
  aggregate as relative weights to split each node's total "other
  countries are steering this much" across its specific links --
  reasonable for nodes with one outgoing link (the common case, and
  exact), approximate for nodes with several.
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from app.parsing import rakaly
from app.parsing.clausewitz import as_list, parse

_COUNTRY_TAG_RE = re.compile(r"^[A-Z0-9]{2,4}$")


@dataclass
class ParsedCountryInNode:
    tag: str
    province_power: float = 0.0
    ship_power: float = 0.0
    light_ships: int = 0
    has_capital: bool = False
    has_trader: bool = False
    is_steering: bool = False  # has_trader and a Steer action (see module docstring)
    money: float = 0.0  # realized ducats/month from this node, if collecting
    val: float = 0.0  # power-weighted share of the node's WHOLE value (retained + forwarded)
    value_share: float = 0.0  # this country's share of the RETAINED value specifically (per-country `total`);
    # `money = value_share * (1 + trade_efficiency + merchant_present_bonus)` -- see the
    # back-solve below and engine/simulate.py's module docstring. Do not confuse with `val`,
    # which spans the whole node (retained+forwarded) and is a different, larger quantity.
    add: float = 0.0  # per-country steering-bookkeeping field; refuted as a trade_efficiency
    # proxy (only ever appears on steering entries, never collectors) -- kept for completeness
    # but not used for anything. See suggested_trade_efficiency's real derivation below instead.
    raw: dict = field(default_factory=dict)

    @property
    def power(self) -> float:
        return self.province_power + self.ship_power


@dataclass
class ParsedNode:
    node_id: str
    local_value: float = 0.0
    total_value: float = 0.0
    steer_power_weights: list[float] = field(default_factory=list)  # per outgoing link, save order
    countries: list[ParsedCountryInNode] = field(default_factory=list)


@dataclass
class ParsedSave:
    player_tag: str
    nodes: dict[str, ParsedNode] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    suggested_trade_efficiency: float | None = None
    actual_current_income: float = 0.0


def load_save(path: str | Path, rakaly_path: Path | None = None) -> ParsedSave:
    zpath = Path(path)

    if zipfile.is_zipfile(zpath):
        with zipfile.ZipFile(zpath) as zf:
            names = set(zf.namelist())
            if "gamestate" not in names:
                raise ValueError(f"{zpath.name} doesn't look like an EU4 save (no 'gamestate' member)")
            gamestate_raw = zf.read("gamestate")
            meta_raw = zf.read("meta") if "meta" in names else gamestate_raw

        if rakaly.is_binary(gamestate_raw):
            # Binary Ironman save: melt automatically, with zero manual
            # steps for whoever's uploading (see rakaly.melt_ironman_save
            # for the pdx.tools-automation-then-rakaly-CLI order of
            # attempts). The result is one merged meta+gamestate document,
            # same shape as an already-melted flat text file, so both text
            # vars below point at it.
            melted = rakaly.melt_ironman_save(zpath.read_bytes(), gamestate_raw, rakaly_path)
            merged_text = rakaly.ensure_text(melted, rakaly_path).decode("utf-8", errors="replace")
            gamestate_text = meta_text = merged_text
        else:
            gamestate_text = rakaly.ensure_text(gamestate_raw, rakaly_path).decode("utf-8", errors="replace")
            meta_text = rakaly.ensure_text(meta_raw, rakaly_path).decode("utf-8", errors="replace")
    else:
        # Not a zip: treat as an already-melted flat text document (e.g.
        # pdx.tools' "Melt" output), which has both meta and gamestate
        # fields in one file.
        text = zpath.read_text(encoding="utf-8", errors="replace")
        gamestate_text = text
        meta_text = text

    warnings: list[str] = []
    player_tag = _extract_scalar(meta_text, "player") or _extract_scalar(gamestate_text, "player")
    if not player_tag:
        raise ValueError("Could not find the player's country tag in the save")

    trade_block_text = extract_top_level_block(gamestate_text, "trade")
    if trade_block_text is None:
        warnings.append("No top-level 'trade' block found in gamestate; falling back to manual entry.")
        return ParsedSave(player_tag=player_tag, nodes={}, warnings=warnings)

    trade_tree = parse(trade_block_text[1:-1])
    nodes: dict[str, ParsedNode] = {}
    for node_body in as_list(trade_tree.get("node")):
        node_id = node_body.get("definitions")
        if not node_id:
            continue
        parsed = ParsedNode(
            node_id=node_id,
            local_value=_as_float(node_body.get("local_value")),
            total_value=_as_float(node_body.get("total")),
            steer_power_weights=[_as_float(v) for v in as_list(node_body.get("steer_power"))],
        )
        for key, value in node_body.items():
            if not (_COUNTRY_TAG_RE.match(key) and isinstance(value, dict)):
                continue
            has_trader = bool(value.get("has_trader"))
            parsed.countries.append(
                ParsedCountryInNode(
                    tag=key,
                    province_power=_as_float(value.get("province_power")),
                    ship_power=_as_float(value.get("ship_power")),
                    light_ships=int(_as_float(value.get("light_ship"))),
                    has_capital=bool(value.get("has_capital")),
                    has_trader=has_trader,
                    is_steering=has_trader and "type" in value,
                    money=_as_float(value.get("money")),
                    val=_as_float(value.get("val")),
                    value_share=_as_float(value.get("total")),
                    add=_as_float(value.get("add")),
                    raw=value,
                )
            )
        nodes[node_id] = parsed

    if not nodes:
        warnings.append(
            "Parsed a 'trade' block but found no nodes in it -- the parsing "
            "logic in save.py likely needs adjusting for this game version. "
            "Falling back to manual entry."
        )

    # Back-solve trade_efficiency from the nodes where the player actually
    # collects: `money = value_share * (1 + trade_efficiency + merchant_bonus)`
    # (see engine/simulate.py's module docstring for how that formula was
    # derived and verified). `value_share` (the per-country `total` field --
    # NOT `val`, which spans the whole node rather than just the retained
    # portion; verified against 3 real collecting nodes, all converging on
    # trade_efficiency ~= 0.75 for this save once the right field is used)
    # is the player's own share of the node's retained value -- exact, not
    # reconstructed. An earlier version of this function used the
    # per-country `add` field as a trade_efficiency proxy; that's refuted
    # (it only ever appears on entries that are *steering*, never on
    # collectors) and is no longer used for anything.
    MERCHANT_PRESENT_BONUS = 0.1  # TRADE_MERCHANT_PRESENT; keep in sync with engine/model.py Params default
    implied_efficiencies = []
    for node in nodes.values():
        player = next((c for c in node.countries if c.tag == player_tag), None)
        if player and player.money > 0 and player.value_share > 0:
            merchant_bonus = MERCHANT_PRESENT_BONUS if player.has_trader else 0.0
            implied_efficiencies.append(player.money / player.value_share - 1 - merchant_bonus)
    suggested_trade_efficiency = (
        sum(implied_efficiencies) / len(implied_efficiencies) if implied_efficiencies else None
    )

    # Exact ground truth for "current income": the save already computed
    # this (money is that node's realized ducats/month for the player).
    # Summing it directly is more accurate than re-deriving it through
    # simulate()'s formula, which is necessarily an estimate (see
    # engine/simulate.py's module docstring) -- reserve that estimate for
    # allocations the player hasn't actually tried, where no ground truth
    # can exist.
    actual_current_income = sum(
        c.money for node in nodes.values() for c in node.countries if c.tag == player_tag
    )

    return ParsedSave(
        player_tag=str(player_tag),
        nodes=nodes,
        warnings=warnings,
        suggested_trade_efficiency=suggested_trade_efficiency,
        actual_current_income=actual_current_income,
    )


def build_node_states_from_save(
    parsed: ParsedSave,
    graph,
) -> tuple[dict[str, "NodeState"], dict[str, "NodeAllocation"], str | None]:
    """Turns a `ParsedSave` into the engine's `NodeState`/`NodeAllocation`
    inputs, from the player's point of view. `graph` is the loaded
    `TradeGraph` (see `parsing/tradenodes.py`), used to place each node's
    aggregate steer power onto its specific outgoing links.

    APPROXIMATION (see module docstring): the save only gives us an
    aggregate steer weight per link at the node level, not per country, so
    if the player is one of several countries steering from a node, their
    own contribution can't be cleanly subtracted out of "other countries'"
    total for that link. The player's own steer *target* similarly isn't
    stored for nodes with more than one outgoing link -- defaults to the
    first outgoing link there. Both are safe to leave as-is (mirrors the
    game's actual current state) but are editable in the UI before
    optimizing.
    """
    from app.engine.model import MerchantAction, NodeAllocation, NodeState

    node_states: dict[str, NodeState] = {}
    current_allocation: dict[str, NodeAllocation] = {}
    home_node: str | None = None

    for node_id, node in parsed.nodes.items():
        player = next((c for c in node.countries if c.tag == parsed.player_tag), None)
        is_home = bool(player and player.has_capital)
        if is_home:
            home_node = node_id

        other_collect = 0.0
        other_passive = 0.0
        other_steer_total = 0.0
        for c in node.countries:
            if c.tag == parsed.player_tag:
                continue
            if c.has_capital or (c.has_trader and not c.is_steering):
                other_collect += c.val if c.val else c.power
            elif c.is_steering:
                other_steer_total += c.val if c.val else c.power
            else:
                other_passive += c.power

        outgoing = graph.outgoing(node_id) if node_id in graph else ()
        other_steer_power = _distribute_steer_weights(other_steer_total, node.steer_power_weights, outgoing)

        node_states[node_id] = NodeState(
            node_id=node_id,
            local_value=node.local_value,
            is_home=is_home,
            player_base_power=player.power if player else 0.0,
            other_collect_power=other_collect,
            other_steer_power=other_steer_power,
            other_passive_power=other_passive,
        )

        if player:
            if not player.has_trader:
                action = MerchantAction.NONE
            elif player.is_steering:
                action = MerchantAction.STEER
            else:
                action = MerchantAction.COLLECT
            steer_target = outgoing[0] if (action == MerchantAction.STEER and outgoing) else None
            current_allocation[node_id] = NodeAllocation(
                merchant_action=action,
                steer_target=steer_target,
                light_ships=player.light_ships,
            )

    return node_states, current_allocation, home_node


def _distribute_steer_weights(total: float, weights: list[float], outgoing: tuple[str, ...]) -> dict[str, float]:
    if not outgoing or total <= 0:
        return {}
    if weights and len(weights) == len(outgoing) and sum(weights) > 0:
        return {t: total * (w / sum(weights)) for t, w in zip(outgoing, weights)}
    return {t: total / len(outgoing) for t in outgoing}


def _as_float(value) -> float:
    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _extract_scalar(text: str, key: str) -> str | None:
    match = re.search(rf'(?m)^\s*{re.escape(key)}\s*=\s*"?([^"\n]+?)"?\s*$', text)
    return match.group(1) if match else None


def extract_top_level_block(text: str, key: str) -> str | None:
    """Finds `key={ ... }` at brace-depth 0 and returns the block including
    its braces, without tokenizing the rest of the (potentially huge)
    document. Returns None if the key isn't found at the top level."""
    marker = None
    i = 0
    n = len(text)
    depth = 0
    in_quotes = False
    while i < n:
        c = text[i]
        if in_quotes:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_quotes = False
            i += 1
            continue
        if c == '"':
            in_quotes = True
            i += 1
            continue
        if c == "{":
            depth += 1
            i += 1
            continue
        if c == "}":
            depth -= 1
            i += 1
            continue
        if depth == 0 and marker is None:
            # Are we at the start of "<key>" possibly preceded by whitespace/newline?
            if (
                text.startswith(key, i)
                and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_"))
                and (i + len(key) >= n or not (text[i + len(key)].isalnum() or text[i + len(key)] == "_"))
            ):
                after = i + len(key)
                j = after
                while j < n and text[j] in " \t":
                    j += 1
                if j < n and text[j] == "=":
                    j += 1
                    while j < n and text[j] in " \t":
                        j += 1
                    if j < n and text[j] == "{":
                        start = j
                        block_depth = 0
                        k = j
                        in_q = False
                        while k < n:
                            ck = text[k]
                            if in_q:
                                if ck == "\\":
                                    k += 2
                                    continue
                                if ck == '"':
                                    in_q = False
                                k += 1
                                continue
                            if ck == '"':
                                in_q = True
                            elif ck == "{":
                                block_depth += 1
                            elif ck == "}":
                                block_depth -= 1
                                if block_depth == 0:
                                    return text[start : k + 1]
                            k += 1
        i += 1
    return None
