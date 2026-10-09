# Experiment saves: protocol and catalogue (research data redesign, 2026-10-06)

Goal: a small set (< 50) of saves that each answer specific open questions of `docs/research/Rxx`. Every save must be
**clean**: the game computes trade once a month, on the 1st (R12 final). Only a save from the 1st, after the game's
first computation, with none of your own merchants or fleets on the way, can be required to match exactly. The intake
tool checks this and rejects anything else (`backend/scripts/add_save.py`, see the end of this file).

## Protocol (every save)

1. Game 1.37.5, **no mods** (the dataset folder is per game version and mod list; a mod list opens a separate dataset), non-Ironman. The console is allowed for set-up changes (monarch points, money) because only the trade state matters.
2. Make the change on (or right after) a 1st, then play on until **all of your merchants and fleets have arrived** and save **on the next 1st** (pause on the 1st; the save of that day already contains that day's computation).
3. One change per B save. Write the change in one line when adding the save (`--change`).
4. Do not save on any other day for these series; mid-month saves are not used.

### Pair design (from R14, corrected)

- **A**: the baseline, a 1st.
- **C**: reload A, change nothing, play to the next 1st, save. Control for everything the world does in that month.
- **Bn**: reload A, make change n, play to the **same** 1st as C, save. Effect of change n = Bn - C.
- **C'**: once per series, a second C from the same A: tells whether two runs from one save diverge (determinism, R14 open item).

All Bs of a series share A and C, so a series of k changes costs k + 2 saves (+1 for C').

## Catalogue

Names: `<series>/<ID>_<TAG>_<yyyy.mm.dd>_<role>.eu4` (the intake tool renames). Facts about VEN in 1444 are from the
Venice series (U10-U29): home node `venice` (end node, no outgoing links); merchants at `alexandria`, `ragusa`, `wien`,
all steering to `venice` (link index 1, 1, 0); province power at `ragusa` (24.6) and `constantinople` (2.8), none at
`alexandria` (VEN has 3 light ships there) or `wien`. Node links: `alexandria` -> constantinople, venice, genua;
`ragusa` -> pest, venice, genua; `wien` -> venice, rheinland, saxony.

### Series `exp-core-1444` (VEN, new game, A = 1444.12.01, C/B = 1445.01.01)

Start a new game as VEN, play hands-off to 1444.12.01, save A. Then from A:

| Role | Change (one) | Answers | Edge cases |
|---|---|---|---|
| C, C' | nothing | drift; determinism | - |
| B1 | ragusa merchant: steer -> collect (away, with province power) | R02 away factor 0.5; R03 pull rule; R06 merchant term on an away collector; R07 merchant bonus | IV-02 |
| B2 | alexandria merchant: steer -> collect (away, no province power, ships present) | R02; R11 ships under the away factor | IV-02, IV-08 |
| B3 | wien merchant: steer venice -> steer saxony | R08 weights and `add` ranks of the other steerers; link flow | IV-04 |
| B4 | recall the wien merchant | R08 weights without VEN; R01 home bonus `transfer_home_bonus` 0.3 -> 0.2 | IV-11 |
| B5 | alexandria merchant -> `venice` (merchant at home) | R07 merchant bonus at home (rule M vs N); R01 home bonus | IV-01 |
| B6 | alexandria fleet (3 light ships) -> protect trade in `venice` (home) | R11 ship power at home; R05 ships do not propagate | IV-06 |
| B7 | alexandria fleet -> protect trade in `ragusa` (steering node) | R11 at a steering node | IV-07 |
| B8 | alexandria fleet -> protect trade in `constantinople` (VEN passive: province power, no merchant) | R11 at a passive node | IV-09 |
| B9 | B1's change **plus** the alexandria fleet -> `ragusa` (compare with B1, not C) | R11 ships at an away-collecting node | IV-08 |
| B10 | add galleys (or any non-light ship) to the fleet protecting alexandria | R11: only light ships count | IV-10 |
| B11 | +1 diplomatic technology (console: add diplomatic power, buy in the tech screen) | R07 trade efficiency per tech level; R01 scalar | - |
| B12 | +1 administrative technology | same | - |
| B13 | take the Trade idea group and its first idea | R07 efficiency; R08 steering strength; R06 merchant term (+15 at 5 ideas per R06) | IV-16 |
| B14 | Trade ideas, second idea (on top of B13; compare with B13) | same | IV-16 |
| B15 | a trade-related policy (needs two idea groups; else skip) | R07/R08 | - |

16 saves (A, C, C', B1-B13; B14/B15 optional).

### Series `exp-era-<year>` (3 later bookmarks)

Pick three bookmarks of the 1.37.5 bookmark list spread over roughly 1500, 1620 and 1700+. For each: start as a
country with a trade presence (e.g. POR or CAS around 1500, ENG/GBR or NED around 1620, GBR around 1700), play
hands-off to the first 1st, save A, play one more month, save C. 6 saves. Purpose: graph states, colonial nations and
their transfers, trade companies, later techs, embargo states, all on clean saves.

### Series `exp-edge` (on the latest era's A; C = that series' C)

| Role | Change (one) | Answers | Edge cases |
|---|---|---|---|
| B1 | declare an embargo on a rival that has power in one of your trade nodes | R10/R01 embargo size and placement | IV-12 |
| B2 | a subject's trade power transfer switched on (or off), via the subject interaction if available | R04 transfer fraction by subject type (AVR/LDU transfer their whole val) | IV-13 |
| B3 | add a province to a trade company | R13 trade company effects | IV-14 |
| B4 | change the main trade port (or move the capital to another trade node) | R02/R15 which node is home | IV-15 |
| B5 | send light ships privateering in a node of a rival | R10 privateer power | - |
| B6 | a vassal or tributary that gives 100% (if the era world has one) | R04 subject types | IV-13 |

6 saves.

### Kept baseline (already clean): U04 (TUR 1691.11.01), U10, U14, U20, U25, U27, U28, U29 (VEN 1444-1445)

## Count

16 (core) + 6 (eras) + 6 (edge) + 8 (kept) = **36**, with room for retakes under 50. Node-graph coverage (nodes with 1,
2, 3 and 4 links, end nodes, nodes nobody steers, inland nodes) comes from every save; no save is spent on it.

## Adding a save

```
cd backend
.venv/bin/python scripts/add_save.py ~/Documents/Paradox\ Interactive/Europa\ Universalis\ IV/save\ games/<file>.eu4 \
    --series exp-core-1444 --role B3 --change "wien merchant: steer venice -> saxony" --covers IV-04
```

The tool rejects the save if it is not from a 1st after the first computation, if any of your merchants or fleets is on
the way, if the game version or mod list does not match the dataset, or (for B/C) if it is not the same game as the
series' A. On success it zips the save into the series folder (git LFS) and records it in `series.json`.
