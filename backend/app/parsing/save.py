"""Extracts trade-relevant data from an EU4 `.eu4` save file.

A real `.eu4` is a zip containing `gamestate`, `meta`, and `ai`; Ironman
saves have those members in Paradox's binary format and need melting
first (see `ironman_melt.py`). We also accept an already-melted flat text file
(not zipped) as produced by pdx.tools' "Melt" button -- meta and gamestate
end up concatenated into one document there, which this module handles
the same way it handles a real save's `gamestate` (the fields we need,
`player=`/`trade={...}`, are present either way).

`gamestate` is huge (tens of MB once melted), so rather than running the
full Clausewitz tokenizer over the whole file we scan for the byte range
of just the top-level `trade={...}` block and tokenize only that.

Field names and the formula they feed are verified against 50 real,
non-Ironman saves, not guessed -- see docs/implementation.md's "Trade
simulation" and "Save parsing" sections for what each field means and the
confirmed relationships between them. Two parsing-specific things worth
knowing: countries in a node are sub-blocks keyed directly by tag
(`TUR={...}`), detected by key shape rather than an allowlist since
colonial/custom tags aren't enumerable in advance; and steering weight is
only given as a node-level aggregate per outgoing link, not per country
(see `_distribute_steer_weights`).
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from app.parsing import ironman_melt
from app.parsing.clausewitz import as_list, parse

_COUNTRY_TAG_RE = re.compile(r"^[A-Z0-9]{2,4}$")

# Params defaults duplicated here (see engine/model.py) so _player_base_power
# can back out the player's own recorded merchant/ship contribution from
# `val` without importing engine.model at parse time -- keep in sync.
_MERCHANT_POWER_DEFAULT = 2.0
_CAPITAL_MERCHANT_POWER_DEFAULT = 5.0
_POWER_PER_LIGHT_SHIP_DEFAULT = 3.0
_HOME_POWER_BONUS_DEFAULT = 0.1


@dataclass
class ParsedCountryInNode:
    tag: str
    province_power: float = 0.0
    ship_power: float = 0.0
    light_ships: int = 0
    has_capital: bool = False
    has_trader: bool = False
    is_steering: bool = False  # has_trader and a Steer action
    steer_link_index: int = 0  # save's own `steer_power` field: which of the node's outgoing
    # links (0-indexed, same order as ParsedNode.steer_power_weights/graph.outgoing) this
    # country steers to. Absent (default 0) means the first link -- CONFIRMED against a real
    # save: a country with no `steer_power` key always lines up with the node's dominant
    # weight landing on outgoing[0].
    is_collecting: bool = False  # `total` key present on this entry -- the authoritative
    # "actually retains ducats here" signal, CONFIRMED against a real mid-game save: a merchant
    # explicitly Collecting away from the capital gets this (plus nonzero `money`); `has_trader`
    # alone does not -- a save taken before any trade tick has run can have has_trader=True at
    # an away node (a scripted/historical merchant placement) with no `total`/`money` yet, since
    # nothing has been computed there. has_capital always collects regardless of this flag.
    money: float = 0.0  # realized ducats/month from this node, if collecting
    val: float = 0.0  # power-weighted share of the node's WHOLE value (retained + forwarded)
    value_share: float = 0.0  # this country's share of the RETAINED value (per-country `total`
    # field) -- populated whenever is_collecting is True (has_capital, or an away merchant that's
    # actually realized a Collect result). See docs/implementation.md's "Trade simulation"
    # section for the confirmed formula relating this to `val`/`money`.
    add: float = 0.0  # per-country steering-bookkeeping field, refuted as a trade_efficiency
    # proxy -- kept for completeness, not used for anything.
    max_demand: float = 1.0  # save's `max_demand` field -- CONFIRMED (889/889 entries, S80):
    # val == max(max_pow, 0) * max_demand exactly. Needed to undo the demand scaling when
    # back-solving this country's own pre-ships/merchant power baseline (see
    # `_player_base_power`) -- subtracting a raw (un-scaled) ship/merchant bonus directly from
    # `val` mixes two different unit scales whenever max_demand != 1, which is most of the time.
    t_in: float = 0.0  # save's `t_in` field: trade power TRANSFERRED to this country from
    # another (e.g. a subject sending a cut of its own power to its overlord's collection here).
    t_out: float = 0.0  # save's `t_out` field: this country's own power sent away the same way.
    # CONFIRMED on S80's comorin_cape (80 node-countries, exact to <0.001): neither t_in nor
    # t_out is part of `val`/`max_pow` (those are fully explained by province/ship/prev/modifier/
    # merchant-bonus alone) -- but `retain_power`/`pull_power`/`money` all need `val + t_in -
    # t_out` in place of bare `val` for EVERY country, not just collectors: a transfer moves
    # power from the sender's role-bucket (retain if collecting, else pull) to the receiver's,
    # with total power conserved. A transfer between two non-collectors (or two collectors)
    # nets to zero change in the retain/pull split, which is why earlier spot-checks against
    # home/passive/steer entries with no transfers never surfaced this.
    max_pow: float = 0.0  # save's own `max_pow` field -- CONFIRMED (889/889 S80 entries, to
    # <0.01): `max_pow = province_power + ship_power + prev + sum(modifier[].power) +
    # merchant_bonus`, where `merchant_bonus` is a discrete, NOT fully identified schedule
    # (observed values: 0 passive, 2/5/7/12/17/22/27 with a merchant -- the spread looks
    # nation-dependent, e.g. a flat "+X Merchant trade power" national idea, not a single
    # universal constant). Read directly rather than reconstructed from guessed constants --
    # see `_player_base_power`, which backs `merchant_bonus` out exactly as whatever's left
    # once every other real, parsed term is subtracted, instead of assuming a fixed value.
    prev: float = 0.0  # save's own `prev` field -- CONFIRMED (S80, 466/496 non-zero cases):
    # `prev == 0.2 * sum(province_power of this country at directly-downstream nodes)`. Ships
    # do NOT propagate into it (confirmed: differs by country/node, not by this node's own
    # ship count), so it's treated as fixed input, not something `_player_base_power` re-derives.
    raw: dict = field(default_factory=dict)

    @property
    def net_power(self) -> float:
        """This country's true power for retain/pull/share purposes: `val` (or raw `power` when
        there's no `val` to work with at all) adjusted for transfers in/out. See `t_in`/`t_out`."""
        base = self.val if self.val else self.power
        return base + self.t_in - self.t_out if self.val else base

    @property
    def modifier_power(self) -> float:
        """Sum of every `modifier[].power` on this entry (embargoes, war exhaustion, etc.) --
        one of the real, parsed terms `max_pow` decomposes into. See `max_pow`."""
        return sum(_as_float(m.get("power")) for m in as_list(self.raw.get("modifier")) if isinstance(m, dict))

    @property
    def power(self) -> float:
        return self.province_power + self.ship_power


@dataclass
class ParsedNode:
    node_id: str
    local_value: float = 0.0
    total_value: float = 0.0  # save's `total` field: a trade-power-weighted "reach" metric, NOT
    # a ducat figure -- see docs/implementation.md. Used only for the val-sum/retention identity
    # checks in test_real_saves.py, never as a stand-in for ducat value.
    current_value: float = 0.0  # save's `current` field: the node's RETAINED (post-forward)
    # ducat value -- see docs/implementation.md's confirmed formula.
    retention: float = 0.0  # save-reported fraction of gross value retained in-node
    retain_power: float = 0.0  # save's `retain_power` field -- see docs/implementation.md
    pull_power: float = 0.0  # save's `pull_power` field -- see docs/implementation.md
    incoming_sum: float = 0.0  # sum of the save's own `incoming[].value`, read directly rather
    # than accumulated via our own graph traversal (avoids compounding upstream error)
    steer_power_weights: list[float] = field(default_factory=list)  # per outgoing link, save order
    countries: list[ParsedCountryInNode] = field(default_factory=list)


@dataclass
class ParsedSave:
    player_tag: str
    date: str | None = None  # save's in-game date (e.g. "1444.11.11"), for matching test fixtures
    nodes: dict[str, ParsedNode] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    suggested_trade_efficiency: float | None = None
    actual_current_income: float = 0.0
    suggested_max_merchants: int | None = None  # len(countries.<TAG>.merchants.envoy) -- currently
    # DEPLOYED merchants, not the country's merchant cap (that cap isn't stored anywhere in the
    # save; it's computed from tech/ideas). Still a far better starting point than a fixed guess.
    suggested_max_light_ships: int | None = None  # countries.<TAG>.num_subunits_type_and_cat.light_ship.normal
    suggested_power_per_light_ship: float | None = None  # weighted-mean real trade_power across the
    # player's actual light_ship fleet mix (see LIGHT_SHIP_TRADE_POWER) -- None if the save has no
    # recognized light_ship-type ships at all (e.g. a save with zero light ships).


MERCHANT_PRESENT_BONUS = 0.1  # TRADE_MERCHANT_PRESENT; keep in sync with engine/model.py Params default


def suggested_trade_efficiency_for(nodes: dict[str, ParsedNode], tag: str) -> float | None:
    """Back-solves trade_efficiency from every node `tag` collects at --
    see docs/implementation.md's "Trade simulation" section for the formula.
    Takes an arbitrary tag (not just the save's own player) so tests can
    validate the formula by treating any country in the save as "the
    player" -- see tests/test_formula_vs_save.py."""
    implied = []
    for node in nodes.values():
        country = next((c for c in node.countries if c.tag == tag), None)
        if country and country.money > 0 and country.value_share > 0:
            merchant_bonus = MERCHANT_PRESENT_BONUS if country.has_trader else 0.0
            implied.append(country.money / country.value_share - 1 - merchant_bonus)
    return sum(implied) / len(implied) if implied else None


def load_save(path: str | Path) -> ParsedSave:
    zpath = Path(path)

    if zipfile.is_zipfile(zpath):
        with zipfile.ZipFile(zpath) as zf:
            names = set(zf.namelist())
            if "gamestate" not in names:
                raise ValueError(f"{zpath.name} doesn't look like an EU4 save (no 'gamestate' member)")
            gamestate_raw = zf.read("gamestate")
            meta_raw = zf.read("meta") if "meta" in names else gamestate_raw

        if ironman_melt.is_binary(gamestate_raw):
            # Binary Ironman save: melt automatically, with zero manual
            # steps for whoever's uploading (see
            # ironman_melt.melt_ironman_save for the in-process-then-
            # separate-worker order of attempts). The result is one
            # merged meta+gamestate document, same shape as an
            # already-melted flat text file, so both text vars below
            # point at it.
            melted = ironman_melt.melt_ironman_save(zpath.read_bytes())
            merged_text = ironman_melt.ensure_text(melted).decode("utf-8", errors="replace")
            gamestate_text = meta_text = merged_text
        else:
            gamestate_text = ironman_melt.ensure_text(gamestate_raw).decode("utf-8", errors="replace")
            meta_text = ironman_melt.ensure_text(meta_raw).decode("utf-8", errors="replace")
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
    date = _extract_scalar(meta_text, "date") or _extract_scalar(gamestate_text, "date")
    max_merchants, max_light_ships, power_per_light_ship = _extract_player_military(gamestate_text, str(player_tag))

    trade_block_text = extract_top_level_block(gamestate_text, "trade")
    if trade_block_text is None:
        warnings.append("No top-level 'trade' block found in gamestate; falling back to manual entry.")
        return ParsedSave(
            player_tag=player_tag,
            date=date,
            nodes={},
            warnings=warnings,
            suggested_max_merchants=max_merchants,
            suggested_max_light_ships=max_light_ships,
            suggested_power_per_light_ship=power_per_light_ship,
        )

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
            current_value=_as_float(node_body.get("current")),
            retention=_as_float(node_body.get("retention")),
            retain_power=_as_float(node_body.get("retain_power")),
            pull_power=_as_float(node_body.get("pull_power")),
            incoming_sum=sum(
                _as_float(x.get("value")) for x in as_list(node_body.get("incoming")) if isinstance(x, dict)
            ),
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
                    steer_link_index=int(_as_float(value.get("steer_power"))),
                    is_collecting="total" in value,
                    money=_as_float(value.get("money")),
                    val=_as_float(value.get("val")),
                    value_share=_as_float(value.get("total")),
                    add=_as_float(value.get("add")),
                    max_demand=_as_float(value.get("max_demand")) or 1.0,
                    t_in=_as_float(value.get("t_in")),
                    t_out=_as_float(value.get("t_out")),
                    max_pow=_as_float(value.get("max_pow")),
                    prev=_as_float(value.get("prev")),
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

    suggested_trade_efficiency = suggested_trade_efficiency_for(nodes, str(player_tag))

    # The save already computed this exactly (money = realized ducats/month
    # per node); summing it directly beats re-deriving it through
    # simulate()'s necessarily-approximate hypothetical-mode estimate.
    actual_current_income = sum(
        c.money for node in nodes.values() for c in node.countries if c.tag == player_tag
    )

    return ParsedSave(
        player_tag=str(player_tag),
        date=date,
        nodes=nodes,
        warnings=warnings,
        suggested_trade_efficiency=suggested_trade_efficiency,
        actual_current_income=actual_current_income,
        suggested_max_merchants=max_merchants,
        suggested_max_light_ships=max_light_ships,
        suggested_power_per_light_ship=power_per_light_ship,
    )


def build_node_states_from_save(
    parsed: ParsedSave,
    graph,
) -> tuple[dict[str, "NodeState"], dict[str, "NodeAllocation"], str | None, set[str]]:
    """Turns a `ParsedSave` into the engine's `NodeState`/`NodeAllocation`
    inputs, from the player's point of view. `graph` is the loaded
    `TradeGraph` (see `parsing/tradenodes.py`), used to place each node's
    aggregate steer power onto its specific outgoing links.

    See docs/implementation.md's "Trade simulation" section for the
    confirmed collect/steer/passive classification rules and the
    known_* replay fields this populates.
    """
    from app.engine.model import MerchantAction, NodeAllocation, NodeState

    node_states: dict[str, NodeState] = {}
    current_allocation: dict[str, NodeAllocation] = {}
    home_node: str | None = None
    real_presence: set[str] = set()

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
            if c.is_steering:
                other_steer_total += c.net_power
            elif c.has_capital or c.is_collecting:
                # Home always collects; an away merchant only counts as
                # collecting once it has actually realized a result (see
                # ParsedCountryInNode.is_collecting) -- has_trader alone
                # isn't enough, since a zero-tick save can have a merchant
                # placed but not yet reflected in any recorded value.
                other_collect += c.net_power
            else:
                # `val` is the authoritative value-weight even when
                # province_power/ship_power are 0 (e.g. colonial-range
                # presence with no owned provinces) -- same val-or-power
                # fallback as the branches above, or this country's share
                # of the node's value silently vanishes. `net_power` (val
                # adjusted for transfers in/out) rather than bare `val` --
                # see ParsedCountryInNode.net_power.
                other_passive += c.net_power

        outgoing = graph.outgoing(node_id) if node_id in graph else ()
        other_steer_power = _distribute_steer_weights(other_steer_total, node.steer_power_weights, outgoing)

        if player:
            if not player.has_trader:
                # No merchant stationed -- NONE even at home (simulate.py's
                # is_home compensation still counts the passive capital
                # collection; this keeps the +10% "merchant present" bonus,
                # which only applies with an actual merchant, from
                # firing here).
                action = MerchantAction.NONE
            elif player.is_steering:
                action = MerchantAction.STEER
            elif player.has_capital or player.is_collecting:
                action = MerchantAction.COLLECT
            else:
                # has_trader with no `type` (not steering) but no realized
                # result yet either (no `total` key) -- a merchant is
                # placed but nothing's been computed for it (zero-tick
                # save). Not COLLECT: there's nothing real to replay here.
                action = MerchantAction.NONE
            steer_target = None
            if action == MerchantAction.STEER and outgoing:
                idx = player.steer_link_index if player.steer_link_index < len(outgoing) else 0
                steer_target = outgoing[idx]
        else:
            action = MerchantAction.NONE
            steer_target = None

        # Authoritative save fields -- only trustworthy for REPLAYING this
        # exact recorded allocation (simulate() gates on
        # NodeState.matches_recorded()), see docs/implementation.md.
        has_known_data = node.retain_power > 0 or node.pull_power > 0

        player_base_power, player_power_per_ship, player_merchant_bonus = _player_base_power(player)
        # Only apply the save's own max_demand when we actually used `val` to derive
        # player_base_power above -- the raw-power fallback (no val at all) was never
        # demand-scaled to begin with, so treat it as already in finished units.
        player_max_demand = (player.max_demand or 1.0) if (player and player.val) else 1.0

        node_states[node_id] = NodeState(
            node_id=node_id,
            local_value=node.local_value,
            is_home=is_home,
            player_base_power=player_base_power,
            player_power_per_ship=player_power_per_ship,
            player_recorded_has_trader=(action != MerchantAction.NONE),
            player_merchant_bonus=player_merchant_bonus,
            player_max_demand=player_max_demand,
            player_t_in=player.t_in if player else 0.0,
            player_t_out=player.t_out if player else 0.0,
            other_collect_power=other_collect,
            other_steer_power=other_steer_power,
            other_passive_power=other_passive,
            known_gross_value=(node.local_value + node.incoming_sum) if has_known_data else None,
            known_retained_value=node.current_value if has_known_data else None,
            known_retain_power=node.retain_power if has_known_data else None,
            known_pull_power=node.pull_power if has_known_data else None,
            known_player_val=player.net_power if player else 0.0,
            known_player_action=action,
            known_player_light_ships=player.light_ships if player else 0,
            known_player_steer_target=steer_target,
        )

        if player:
            current_allocation[node_id] = NodeAllocation(
                merchant_action=action,
                steer_target=steer_target,
                light_ships=player.light_ships,
            )
            # Genuine presence -- owned provinces/ships, OR already doing
            # something real here, regardless of `val` (which, after the
            # fix above, can be a small nonzero "colonial range" figure at
            # nodes the player has nothing actually standing in -- not a
            # sane place to suggest a NEW merchant/ship). Raw power is the
            # right signal for "can this candidate be acted on at all",
            # val for "how much is acting on it worth".
            if player.power > 0 or is_home or action != MerchantAction.NONE:
                real_presence.add(node_id)

    return node_states, current_allocation, home_node, real_presence


def _player_base_power(player: "ParsedCountryInNode | None") -> tuple[float, float | None, float]:
    """The player's trade power components at a node, decomposed from the
    save's own recorded fields rather than guessed constants wherever
    possible, for simulate()'s `_player_power` to recombine with a
    hypothetical ship count / merchant action:

    - `base` (ship-count-INDEPENDENT max_pow, SAME action as recorded):
      `province_power + prev + modifier_power + bonus`, all read directly
      from the save -- CONFIRMED (S80, 889 entries): `max_pow =
      province_power + ship_power + prev + modifier_power + bonus` to
      <0.01 absolute, and neither `prev` nor province/modifier power
      depend on this country's own ships (`prev` is 0.2x downstream
      province power; see ParsedCountryInNode.prev).
    - `power_per_ship`: this country's OWN recorded `ship_power /
      light_ships` -- its actual real rate (CONFIRMED to vary: 3.05/ship
      for TUR at comorin_cape, 2.0/ship for KMC at girin -- fleet
      composition, not a universal constant) -- or None if it currently
      has no ships to derive a rate from (caller falls back to
      `Params.power_per_light_ship`, a guess, since there's nothing real
      to read).
    - `bonus`: whatever's left of `max_pow` once province power, ship
      power, `prev`, and modifiers are all subtracted -- CONFIRMED this is
      NOT a single constant/formula: it's nonzero even with no merchant at
      all whenever the country owns the node (has_capital) -- e.g. AAC at
      rheinland, has_trader=False, residual exactly 5.0 -- and the
      observed discrete values (0/2/5/7/12/17/22/27) don't decompose
      cleanly into "home" vs "away" vs "merchant present": the SAME tag
      can show a different value at its home node than away (e.g. KON:
      +2 extra at home, +0 extra away), which rules out a uniform
      per-nation idea bonus layered on a fixed home/away base. Most likely
      a mix of national ideas/government reforms this model doesn't
      attempt to decompose. Rather than enumerate every possible term,
      `base` is computed as `max_pow - ship_power` directly -- CONFIRMED
      this covers terms this model doesn't even have a name for: a purely
      passive, no-province/no-ship/no-merchant "presence" entry (e.g. SCA
      at carribean_trade, S80) can still have a nonzero `max_pow` that
      `province + prev + modifier_power + bonus` doesn't explain at all
      (there, all four are exactly 0) -- but it's still exactly `max_pow`
      once ship_power is the only thing subtracted out, so working from
      `max_pow` directly rather than re-summing named components is
      strictly more robust to whatever this model hasn't identified yet.
      `bonus` is still reported separately (NOT part of `base`'s return
      value's own subtraction) purely for the one case that needs an
      isolated number: the caller's "merchant toggled off" correction
      below, which has to subtract exactly the merchant's own share of
      `max_pow`, not all of it.
    """
    if not player or not player.val:
        # No `val` to work with (e.g. synthetic/manual data, or a
        # genuinely zero-power entry) -- fall back to raw power as-is,
        # with no ship/merchant decomposition to offer.
        return (player.power if player else 0.0), None, 0.0

    bonus = 0.0
    if player.has_trader or player.has_capital:
        bonus = player.max_pow - player.province_power - player.ship_power - player.prev - player.modifier_power

    base = player.max_pow - player.ship_power
    power_per_ship = (player.ship_power / player.light_ships) if player.light_ships > 0 else None
    return base, power_per_ship, bonus


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


def _extract_player_military(
    gamestate_text: str, player_tag: str
) -> tuple[int | None, int | None, float | None]:
    """Pulls the player's deployed-merchant count, total light-ship count,
    and the actual trade-power-per-light-ship implied by their real fleet
    composition, from the top-level `countries={ <TAG>={...} ... }` block,
    without tokenizing the other 1000+ countries in it, and without even
    scanning past our own tag's entry -- `countries` alone is tens of MB,
    so a naive "extract the whole block, then search within it" (like the
    `trade` block above) would burn several seconds walking all of it
    char-by-char just to find its end. `_extract_nested_block` stops the
    instant it finds `player_tag`."""
    country_block = _extract_nested_block(gamestate_text, "countries", player_tag)
    if country_block is None:
        return None, None, None
    country = parse(country_block[1:-1])
    merchants = country.get("merchants")
    max_merchants = len(as_list(merchants.get("envoy"))) if isinstance(merchants, dict) else 0
    subunits = country.get("num_subunits_type_and_cat")
    light_ship = subunits.get("light_ship") if isinstance(subunits, dict) else None
    max_light_ships = int(_as_float(light_ship.get("normal"))) if isinstance(light_ship, dict) else 0

    # Weighted-mean trade power per light ship, from the player's ACTUAL
    # fleet mix (e.g. 10 Early Frigate + 90 Frigate), not a flat guess --
    # see LIGHT_SHIP_TRADE_POWER's own docstring for where the per-type
    # numbers come from.
    type_counts: dict[str, int] = {}
    for navy in as_list(country.get("navy")):
        if not isinstance(navy, dict):
            continue
        for ship in as_list(navy.get("ship")):
            if not isinstance(ship, dict):
                continue
            t = ship.get("type")
            if t in LIGHT_SHIP_TRADE_POWER:
                type_counts[t] = type_counts.get(t, 0) + 1
    total_light_ships_seen = sum(type_counts.values())
    power_per_light_ship = (
        sum(LIGHT_SHIP_TRADE_POWER[t] * n for t, n in type_counts.items()) / total_light_ships_seen
        if total_light_ships_seen
        else None
    )

    return max_merchants, max_light_ships, power_per_light_ship


# Real `trade_power` stat per light_ship-category unit, read directly out
# of this game install's own `common/units/*.txt` (type=light_ship units
# only -- confirmed every one of them, there's no DLC/unique light_ship
# unit missing from this list). A public game-balance constant, not
# save-specific or proprietary data -- same category as the other named
# constants in engine/model.py's Params.
LIGHT_SHIP_TRADE_POWER: dict[str, float] = {
    "barque": 2.0,
    "caravel": 2.5,
    "early_frigate": 3.0,
    "frigate": 3.5,
    "heavy_frigate": 4.0,
    "great_frigate": 5.0,
}


def _extract_scalar(text: str, key: str) -> str | None:
    match = re.search(rf'(?m)^\s*{re.escape(key)}\s*=\s*"?([^"\n]+?)"?\s*$', text)
    return match.group(1) if match else None


def extract_top_level_block(text: str, key: str) -> str | None:
    """Finds `key={ ... }` at brace-depth 0 and returns the block including
    its braces, without tokenizing the rest of the (potentially huge)
    document. Returns None if the key isn't found at the top level."""
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
        if depth == 0:
            brace = _key_eq_brace_at(text, i, key)
            if brace is not None:
                end = _match_brace_block(text, brace)
                if end is not None:
                    return text[brace:end]
        i += 1
    return None


def _extract_nested_block(text: str, outer_key: str, inner_key: str) -> str | None:
    """Like `extract_top_level_block`, but for `outer_key={ inner_key={...}
    ... }` where `outer_key`'s block is too large to fully scan just to
    find its end (e.g. `countries`, tens of MB) -- stops the moment
    `inner_key` is found at depth 1, never walking the rest of
    `outer_key`'s block. Returns None if either key isn't found."""
    n = len(text)
    outer_start = None
    i = 0
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
        if depth == 0:
            brace = _key_eq_brace_at(text, i, outer_key)
            if brace is not None:
                outer_start = brace
                i = brace
                break
        i += 1
    if outer_start is None:
        return None

    # Now scan strictly inside the outer block, tracking depth relative to
    # it (starts at 1, right after its own opening brace), looking for
    # `inner_key={` at depth 1.
    depth = 0
    in_quotes = False
    i = outer_start
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
            if depth == 0:
                return None  # reached the end of outer_key's block
            i += 1
            continue
        if depth == 1:
            brace = _key_eq_brace_at(text, i, inner_key)
            if brace is not None:
                end = _match_brace_block(text, brace)
                return text[brace:end] if end is not None else None
        i += 1
    return None


def _key_eq_brace_at(text: str, i: int, key: str) -> int | None:
    """If `text[i:]` starts with the bareword `key` (not part of a longer
    identifier) followed by `=` and a `{`, returns the index of that `{`.
    Otherwise None."""
    n = len(text)
    if not (
        text.startswith(key, i)
        and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_"))
        and (i + len(key) >= n or not (text[i + len(key)].isalnum() or text[i + len(key)] == "_"))
    ):
        return None
    j = i + len(key)
    while j < n and text[j] in " \t":
        j += 1
    if j >= n or text[j] != "=":
        return None
    j += 1
    while j < n and text[j] in " \t":
        j += 1
    return j if j < n and text[j] == "{" else None


def _match_brace_block(text: str, start: int) -> int | None:
    """`start` is the index of a `{`. Returns the index just past its
    matching `}` (so `text[start:end]` is the whole `{...}` block),
    handling quoted strings/escapes. None if unterminated."""
    n = len(text)
    depth = 0
    in_quotes = False
    k = start
    while k < n:
        c = text[k]
        if in_quotes:
            if c == "\\":
                k += 2
                continue
            if c == '"':
                in_quotes = False
            k += 1
            continue
        if c == '"':
            in_quotes = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return k + 1
        k += 1
    return None
