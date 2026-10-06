"""Data types of the trade calculation. No arithmetic lives here.

Three kinds of data, never mixed:
  * inputs     - raw variables read from the save (WorldInputs, EntryInput, NodeInput). calc.py may use only these.
  * decisions  - what each country does at each node (Decisions). The app varies the player's; tests use recorded ones.
  * recorded   - results the game itself stored in the save (Recorded*). Used only by verify.py and the isolated stage predictors.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Action(str, Enum):
    NONE = "none"
    COLLECT = "collect"
    STEER = "steer"


class UnknownVariable(Exception):
    """A variable the calculation needs is not known (not in the save, rule still under research). Never papered over."""

    def __init__(self, variable: str, where: str, research: str = ""):
        super().__init__(f"unknown variable '{variable}' at {where}" + (f" (see research task {research})" if research else ""))
        self.variable, self.where, self.research = variable, where, research


@dataclass(frozen=True)
class Modifier:
    key: str
    duration: float
    power: float
    power_modifier: float


@dataclass(frozen=True)
class EntryInput:
    """Raw variables of one country at one trade node, as the save stores them."""

    tag: str
    node: str
    province_power: float = 0.0
    ship_power: float = 0.0
    light_ships: int = 0
    has_capital: bool = False
    has_trader: bool = False
    steering: bool = False          # key `type` present: the merchant steers
    steer_link: int = 0             # key `steer_power`: index of the outgoing link (absent = first)
    collecting: bool = False        # key `total` present: the game marks this country as collecting here
    add: float | None = None        # key `add`: steering value bonus on steer_link (observed: size not derived, R08)
    t_in: float = 0.0
    t_out: float = 0.0
    modifiers: tuple[Modifier, ...] = ()
    transfers_to: tuple[tuple[str, float], ...] = ()
    transfers_from: tuple[tuple[str, float], ...] = ()


@dataclass(frozen=True)
class NodeInput:
    node_id: str
    local_value: float = 0.0
    trade_company_region: bool = False


@dataclass(frozen=True)
class NodeDecision:
    action: Action = Action.NONE
    steer_target: str | None = None
    light_ships: int = 0


@dataclass
class Decisions:
    """(tag, node) -> decision. Missing = no merchant, no ships."""

    by_entry: dict[tuple[str, str], NodeDecision] = field(default_factory=dict)

    def get(self, tag: str, node: str) -> NodeDecision:
        return self.by_entry.get((tag, node), NodeDecision())


@dataclass
class WorldInputs:
    game_version: str
    date: str
    player: str
    nodes: dict[str, NodeInput]
    entries: dict[tuple[str, str], EntryInput]  # only countries with data in the node (not bare max_demand stubs)
    node_order: tuple[str, ...]                 # the save's node list order (incoming.from is 1-based into it)
    multipliers: dict[tuple[str, str], float]   # `max_demand` of every country at every node: observed, docs/research/R01
    decisions: Decisions = field(default_factory=Decisions)  # decisions the save records
    ironman: bool = False
    mods: tuple[str, ...] = ()
    dlcs: tuple[str, ...] = ()


@dataclass(frozen=True)
class EntryRecorded:
    prev: float | None = None
    max_pow: float | None = None
    max_demand: float | None = None
    val: float | None = None
    potential: float | None = None
    already_sent: float | None = None
    money: float | None = None
    share_total: float | None = None   # the `total` key of a collecting country: its share of the retained ducats
    power_fraction: float | None = None


@dataclass(frozen=True)
class NodeRecorded:
    current: float | None = None
    outgoing: float | None = None
    value_added_outgoing: float | None = None
    retention: float | None = None
    retain_power: float | None = None
    pull_power: float | None = None
    total: float | None = None
    steer_weights: tuple[float, ...] = ()
    incoming: tuple[tuple[str, float, float], ...] = ()   # (source node id, value, add)
    num_collectors: int | None = None
    num_collectors_including_pirates: int | None = None
    collector_power: float | None = None
    collector_power_including_pirates: float | None = None


@dataclass
class Recorded:
    entries: dict[tuple[str, str], EntryRecorded]
    nodes: dict[str, NodeRecorded]


@dataclass
class World:
    inputs: WorldInputs
    recorded: Recorded
    save_id: str = ""
    unmapped_keys: dict[str, int] = field(default_factory=dict)  # trade-block keys the variable registry does not know


@dataclass
class EntryResult:
    prev: float = 0.0
    max_pow: float = 0.0
    val: float = 0.0
    effective: float = 0.0
    collecting: bool = False
    share_total: float = 0.0
    money: float = 0.0


@dataclass
class NodeResult:
    gross: float = 0.0
    retain_power: float = 0.0
    pull_power: float = 0.0
    retention: float = 0.0
    current: float = 0.0
    outgoing: float = 0.0
    steer_weights: tuple[float, ...] = ()
    link_values: dict[str, float] = field(default_factory=dict)


@dataclass
class TradeResult:
    entries: dict[tuple[str, str], EntryResult]
    nodes: dict[str, NodeResult]

    def income(self, tag: str) -> float:
        return sum(r.money for (_n, t), r in self.entries.items() if t == tag)
