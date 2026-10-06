# R02 final - The penalty for collecting away from the capital node (TRADE_NON_CAPITAL_OFFICE = -0.5)

Status: FINAL (2026-10-05). Merged from `R02_away_collection_penalty_draft.md` (rule and wiki statements), `R02_away_collection_penalty_response_1.md` (data findings, with its verification sections) and a fresh whole-corpus verification written for this document. Corpus: the 86 manifest entries of `backend/tests/fixtures/saves/saves.json` (S01-S80 and the stored user cases U01-U06); U01/U02 are byte-copies of S80/S79, so all counts are over the **84 distinct saves** unless marked otherwise. The core question (when, to what and by how much the away penalty applies) is settled by the data; the side questions that arose (the reducing modifier, which node is "home" when capital and main trade port differ) are moved to topic R15, the embargo size and the other `max_demand` mechanisms stay in R01/R10 (section 9).

Scripts (from `backend/`, `.venv/bin/python`): `scripts/research/final_r02_core.py` (classes, placebo, capital/port, colonial nations, switches, SUN), `final_r02_goalrows.py` (the 43 rows of the goal table), `final_r02_distinct.py` (distinct countries/pairs), `final_r02_colonial.py` (colonial tags). They were written for this document and do not reuse the logic of `r02_*.py`, `ver_*.py` or `ver2_*.py`.

## 1. Answer

```
# game 1.37.5; per country c, trade node n
home(c)        = the trade node that contains province country[c].trade_port          # = the node whose entry of c has key `has_capital` (C-03)
collects(c,n)  = entry(c,n) has key `total`  OR  entry(c,n) has key `has_capital`       # the collect action (one collector without `total`: C-02)
away(c,n)      = collects(c,n) AND n != home(c)

max_demand(c,n) = A(c,n) * ( 0.5  if away(c,n)  else  1.0 )                             # multiplicative, on the WHOLE max_demand
                  # A(c,n) = the value the country would have at n without the away penalty
                  # (country-wide scalar of its class, embargo etc.: topic R01, observed as an input)
val(c,n)        = fx( max_pow(c,n) * max_demand(c,n) )                                  # so every part of max_pow (province, ships, prev, merchant/capital extras) is halved in effect
not penalised   = steering merchants (key `type`), merchants without action (has_trader, neither `type` nor `total`),
                  countries without a merchant, and the collector at its own home node

changing a decision:  max_demand_new = max_demand_old * (0.5 if newly away else 1) / (0.5 if was away else 1)      # a factor of 0.5 or 2
```

Status in the code: `backend/app/trade/calc.py` `rule_away_adjustment` (lines 165-170, used at 268-269) implements exactly this ratio form, with `0.5 = 1 + TRADE_NON_CAPITAL_OFFICE`; its docstring still calls it a HYPOTHESIS, which this document replaces by the verified rule for decisions that switch a merchant between collecting away and steering/idle. `recorded_away = e.collecting and not e.has_capital` matches the definition above. The stage `multiplier` stays NOT IMPLEMENTED in `tests/trade/expected.py` because `A(c,n)` (R01) is still an observed input (`inputs.multipliers`), not derived.

## 2. Variables

```json
[
 {"id":"TRADE_NON_CAPITAL_OFFICE","meaning":"base away penalty; factor = 1 + value = 0.5","unit":"fraction","kind":"constant","source":{"type":"defines.lua","path":"common/defines.lua NDefines.NEconomy.TRADE_NON_CAPITAL_OFFICE = -0.50 (value as stated in the R02 goal; not re-read from game files)"},"confidence":"reported (value); the factor 0.5 itself is confirmed by the data (C-01)"},
 {"id":"away_factor","meaning":"multiplier on max_demand for a collecting merchant away from home","unit":"ratio","kind":"derived","source":{"type":"other","path":"1 + TRADE_NON_CAPITAL_OFFICE"},"confidence":"confirmed (C-01)"},
 {"id":"collects","meaning":"country collects at the node","unit":"bool","kind":"read","source":{"type":"save","path":"trade.node[].<TAG> has key `total` or key `has_capital`"},"confidence":"confirmed (C-02; one exception entry)"},
 {"id":"steers","meaning":"merchant steers","unit":"bool","kind":"read","source":{"type":"save","path":"trade.node[].<TAG>.type"},"confidence":"confirmed (C-02)"},
 {"id":"has_trader","meaning":"merchant present","unit":"bool","kind":"read","source":{"type":"save","path":"trade.node[].<TAG>.has_trader"},"confidence":"confirmed"},
 {"id":"home_node","meaning":"node of the country's main trade port","unit":"node id","kind":"read","source":{"type":"save","path":"node containing province countries.<TAG>.trade_port; equivalently the node whose entry has `has_capital`"},"confidence":"confirmed in the corpus (C-03); differs from the capital node in no case, so the rule for the differing case is open (R15)"},
 {"id":"max_demand","meaning":"multiplier from max_pow to val, contains the away factor","unit":"ratio","kind":"read","source":{"type":"save","path":"trade.node[].<TAG>.max_demand"},"confidence":"confirmed"},
 {"id":"class_scalar_A","meaning":"max_demand a country has at a node without the away penalty (domestic / foreign class, embargo)","unit":"ratio","kind":"read","source":{"type":"save","path":"max_demand of the same country at non-away nodes of the same class"},"confidence":"composition UNKNOWN (R01)"},
 {"id":"trade_embargoed_by","meaning":"countries that embargo this country; an embargoer with own power at a node lowers max_demand there","unit":"list of tags","kind":"read","source":{"type":"save","path":"countries.<TAG>.trade_embargoed_by"},"confidence":"confirmed (filter used in C-01); size of the reduction: R01"}
]
```

## 3. Claims

### C-01 The away penalty is a factor 0.5 on the whole `max_demand`
Claim: a country collecting away from its home node has `max_demand` equal to exactly 0.5 times the value it has at its other, unpenalised nodes of the same class.
Formula: `max_demand(c,n) = 0.5 * A(c,n)` for `away(c,n)`.
Applies when: `away(c,n)` and no embargoer of c has own power at n.
Source: save corpus, `final_r02_core.py` (independent of response_1's class definition: here the baseline is every other non-away, embargo-clean entry of the same country in the same save).
Quote: 188 of 189 tested away-collecting entries (distinct saves; embargo-clean; a baseline exists) satisfy `|max_demand - 0.5 * b| <= 0.0015` for a value `b` of another node of the same country; none is at `b` itself. Examples (S79, md / baseline): `FRA genua 0.523 / 1.045`, `SPA genua 1.069 / 2.137`, `DEC comorin_cape 0.720 / 1.440`, `DLH lahore 0.821 / 1.642`, `GZI zanzibar 0.639 / 1.278`, `HAB english_channel 0.589 / 1.178`. The halving is multiplicative: with baselines from 1.045 to 2.137 the result is always half of the baseline, while an additive -0.5 would give 0.545 and 1.637 for the two extreme rows. Placebo (same test with other factors): 0.3: 0, 0.4: 0, 0.45: 1 (the exception row of C-07), 0.5: 188, 0.55: 0, 0.6: 0, 0.7: 0.
Confidence: confirmed (whole corpus, one exception listed in C-07). Coverage: the 188 entries are 47 distinct (country, node) pairs of 38 countries in 6 saves of **one** campaign (S79 34, S80 31, U03 31, U04 31, U05 30, U06 31); the 78 start snapshots contain no away collector at all (0 of their entries), so the evidence comes from a single simulated world.
Caveats: 105 further away collectors were excluded because an embargoer of theirs has own power at the node (not used for the factor; the 15 of them in the goal table are listed in C-05; the size of the embargo reduction is R01); `A(c,n)` is read from the save, its composition is R01.

### C-02 Only collecting is penalised
Claim: steering merchants, merchants without action and collectors at their home node keep the full value; the penalty follows the collect action.
Source: `final_r02_core.py`, same tolerance and baseline as C-01, embargo-clean entries.
Quote: steering entries: 0 of 21,969 at half of another node's value, 21,789 at the value of another node, 180 at neither (no other node with the same value, including the small reductions of C-07); merchants with `has_trader` but neither `type` nor `total`: 1 of 5,033 at half (S79 `POR english_channel`, md 0.897 against 1.794 / 1.719), 5,028 at the value of another node, 4 at neither; collectors at their home node (`total` and `has_capital`): 0 of 42,853 at half. The one idle-looking half entry is a collector: the node records `num_collectors 9` with 8 entries carrying `total`/`has_capital`, and its `retain_power` includes POR's `val 1.794` (R03 final, C-06) - a collecting merchant whose entry lacks the key `total`.
Confidence: confirmed (whole corpus; the single exception is the save marker, not the rule).
Caveats: "collects" is therefore the game's action, and the key `total` is a nearly complete marker of it (one entry in 84 saves lacks it).

### C-03 Home node = node of `trade_port` = node with `has_capital`
Claim: the node whose entry carries `has_capital` is always the node containing the country's `trade_port`; the capital province is always in the same node.
Source: `final_r02_core.py` (province to node from the static map `backend/data/tradenodes.json`, not from the save's province block).
Quote: 115,920 country-saves have a `trade_port`; 42,978 of them have a `has_capital` entry, all 42,978 at the node of `trade_port`, 0 elsewhere; the node of `capital` differs from the node of `trade_port` in 0 of 115,920. Colonial nations (tags C00-C17, 6,300 tag-saves with a `trade_port`): the 534 that have trade data all have a `has_capital` entry; the other 5,766 are inactive tags with only bare `max_demand` stubs (`final_r02_colonial.py`), which replaces the response_1 figure "87 without". Away collection by colonial nations: 53 entries, all at half (C-01).
Confidence: confirmed for the equality in the corpus. Which of capital and main trade port the game uses when they differ cannot be read from the corpus: side question, R15.

### C-04 Within-country switches show the factor directly
Claim: when a country starts collecting away at a node, its `max_demand` there halves relative to its unchanged nodes; when it stops, it doubles.
Source: `final_r02_core.py` section switches; consecutive saves of the campaign (S79, S80, U03, U04, U05, U06); ratio = `(md_B / md_A)` divided by the median change of the country's nodes that are passive and embargo-clean in both saves (at least 3 such nodes).
Quote: entering away: 8 pairs, 7 of them 0.5000-0.5003 (`S79>S80 YEM hormuz 0.5`, `YUE ganges_delta 0.5004`, `YAO ethiopia 0.5`, `S80>U03 C09 laplata 0.5`, `U04>U05 TUR gulf_of_aden 0.5002` (steering before), `U05>U06 ETH gulf_of_aden 0.5003`, `ZZZ ethiopia 0.5`); the eighth is `S79>S80 TUR the_moluccas 0.6391` (passive before; embargo and ship changes in that interval, cause not separated). Leaving away: 6 pairs, 6 of 6 at 1.9985-2.0000 (`AYU malacca 1.9985`, `AYU ganges_delta 1.9985`, `C11 mexico 2.0`, `FRA genua 2.0`, `ETH gulf_of_aden 2.0`, `YEM hormuz 1.9987`).
Confidence: inferred (one campaign, control not perfect); the rule itself is C-01.
Caveats: pairs are from saves 1-17 months apart; a looser selection of pairs in response_1 lists 12 entering and 12 leaving switches with 9 and 6 at the expected ratio.

### C-05 The goal's table (43 rows, all from S79) is fully explained
Claim: every row of the goal table is either exactly 0.5 x its class baseline or belongs to an embargoed country whose embargoer has own power at the node.
Source: `final_r02_goalrows.py`; every row was found in S79 and its `max_pow` and `max_demand` match the goal.
Quote: 28 rows at 0.5 x another node's value (AYU malacca 0.679/1.357, AYU ganges_delta, BLG genua 0.794/1.587, BRA lubeck 0.804/1.607, BRI champagne and english_channel 0.833/1.666, C02 carribean_trade, C03 panama, C04 chesapeake_bay, C06 brazil, C07 ohio, CSH yumen 0.653/1.306, DEC comorin_cape and gujarat 0.720/1.440, DLH lahore 0.821/1.642 and gujarat 0.688/1.376, FRA genua, GZI zanzibar 0.639/1.278, HAB english_channel, HAI english_channel, IRQ aleppo, KHM canton and malacca, LIT baltic_sea 0.525/1.049, MNG ganges_delta 0.785/1.570, SPA genua 1.069/2.137, TRI champagne, TRS persia); 15 rows with an embargoer that has own power (`province_power + ship_power > 0`) at the node: CSH beijing {MNG 2.3}, GEN champagne {SWI 34.2, PAP 4.2}, GEN venice {PAP 53.8, LAN 37.8}, KON ivory_coast {MOR 97.0}, LAN venice {GEN 47.1, PAP 53.8}, MAL ivory_coast {KON 52.2}, MOR ivory_coast {KON 52.2, SON 2.1}, PAP genua {GEN 238.2, LAN 131.1}, RUS baltic_sea {DAN 75.6}, SON ivory_coast {MOR 97.0}, SPA english_channel {GBR 453.7}, SUN malacca {BEI 96.1}, SWI genua {GEN 238.2}, TUR ragusa {HUN 6.8, HAB 89.8}, TUR venice {HAB 31.5}. 0 rows missing, 0 unexplained.
Confidence: confirmed for the partition. The ratios 0.597, 0.553, 0.551, 0.538, 0.505, 0.491, 0.384 of the goal's "ratio" column are a baseline artefact (median over nodes of different classes) and are listed in section 8.
Caveats: the size of the reduction at the 15 embargoed rows is not derived here (R01).

### C-06 Interaction with ships and other power
Claim: the penalty acts through `max_demand` only, so it halves the effective power of every component of `max_pow` at that node, including ships, propagated power and merchant extras.
Source: the verified identity `val = fx(max_pow * max_demand)` (stage `val` is green in `tests/trade/expected.py`; the README integration log records it exact in all 83,201 entries) combined with C-01.
Confidence: confirmed as a consequence; the composition of `max_pow` is R06/R11.

### C-07 One exception that is not the away penalty
Claim: S80 (and its copy U01) `SUN malacca`, an away collector, has `max_demand 0.648`, which is 0.434 x the class value 1.492 instead of 0.5 x.
Source: `final_r02_core.py` (SUN block).
Quote: SUN has no `trade_embargoed_by` in S80 and no country lists SUN in `trade_embargoes` (SUN itself embargoes BEI); SUN's steering entries in the same save are also below the class value (`burma 1.443`, `gulf_of_siam 1.455`, `canton 1.460`, `philippines 1.387` against 1.492, 2.9-7.0 % lower). So an additional reduction of about 13 % acts on SUN's nodes in S80; it is not part of the away factor.
Confidence: confirmed as an exception; cause UNKNOWN (other mechanisms that lower `max_demand`: R01).

### C-08 Source statements behind the rule
Claim: the wiki (Trade > Collect from Trade) describes a multiplicative -50% on trade power in nodes other than the country's home node.
Source: `R02_away_collection_penalty_draft.md` C-01 (not re-fetched here).
Quote: "In other nodes than the country's home node, this gives a multiplicative penalty of -50% trade power" (as quoted in the draft and in request_1).
Confidence: reported (quote not re-fetched; the rule is confirmed by the data, C-01).
Caveats: the wiki text does not say that steering is exempt; that exemption rests on the data (C-02), not on a source.

## 4. Validation against the data

| Check | Entries | Result |
|---|---|---|
| Away collectors, embargo-clean, with baseline | 189 | 188 at 0.5 x another node of the same country; 1 exception (C-07) |
| Same, other factors (placebo) | 189 | 0.3: 0, 0.4: 0, 0.45: 1, 0.55: 0, 0.6: 0, 0.7: 0 |
| Steering entries at half | 21,969 | 0 (21,789 at another node's value, 180 at neither) |
| Merchants without action at half | 5,033 | 1 (POR english_channel S79, a collector without `total`) |
| Home-node collectors at half | 42,853 | 0 |
| Away collectors excluded for embargo (embargoer with own power) | 105 | not used for the factor; their reductions are R01 |
| `has_capital` entry at the node of `trade_port` | 42,978 | 42,978 |
| node(`capital`) = node(`trade_port`) | 115,920 | 115,920 |
| Colonial nations with data that have a `has_capital` entry | 534 | 534 (5,766 inactive tags have stubs only) |
| Switches entering / leaving away | 8 / 6 | 7 of 8 at 0.5; 6 of 6 at 2.0 |
| Goal table rows | 43 | 28 at 0.5 x baseline, 15 embargoed with power, 0 unexplained |
| Away collectors in the 78 start snapshots | - | 0 |

Arithmetic for rows (S79, baseline = the country's value at other nodes of the same class): FRA genua 1.045 x 0.5 = 0.5225 (recorded 0.523); SPA genua 2.137 x 0.5 = 1.0685 (1.069); DEC comorin_cape 1.440 x 0.5 = 0.720; DLH lahore 1.642 x 0.5 = 0.821; GZI zanzibar 1.278 x 0.5 = 0.639; HAB english_channel 1.178 x 0.5 = 0.589.

Every failure: C-07 (SUN malacca S80) and the eighth entering switch (TUR the_moluccas S79>S80, 0.6391).

## 5. Unknowns, contradictions between sources, and what would settle them

All items below are outside the core question; none changes the rule in section 1.

1. Generality across campaigns: all 188 half-matches come from one campaign (6 saves, 38 countries). A save of a different game that contains away collectors would confirm the factor outside this world.
2. The exception C-07: an additional reduction of about 13 % at SUN's nodes in S80. Data requirement: the modifiers and relations of SUN in S80 that are absent from the trade block (countries.SUN modifiers, war and diplomacy state); the mechanism belongs to R01.
3. Interaction of the away factor with the embargo reduction (multiplicative or not) at the 105 excluded entries: a pair of saves, same country and node, with and without an embargoer that has own power (R14 embargo pair), or a save in which an embargoed country switches to collecting away.
4. The side questions moved to R15: the modifier `reduced_trade_penalty_on_non_main_tradenode` (value, sources, how it combines with 0.5) and the home node when capital and main trade port differ.

## 6. Sources (ranked)

1. The save corpus (84 distinct saves) and the scripts named above - primary; the factor is derived from it.
2. `R02_away_collection_penalty_draft.md` - wiki statements quoted by an AI assistant, not re-fetched: `reported`.
3. The R02 goal - the define value `TRADE_NON_CAPITAL_OFFICE = -0.50` and the verified facts of the project context: `reported`.

## 7. Provenance

| Item | Source file | Point |
|---|---|---|
| C-01 | this document (`final_r02_core.py`); prior evidence `R02_away_collection_penalty_response_1.md` | Q1 C-01 (108 of 108 under its own definition) |
| C-02 | this document (`final_r02_core.py`); response_1 | Q2 C-03 (20,573 of 20,591 and 4,433 of 4,433 under its definition) |
| C-03 | this document (`final_r02_core.py`, `final_r02_colonial.py`); response_1 | Q4 C-04, C-05 |
| C-04 | this document; response_1 Update U-1 and its second-pass verification | Update U-1 |
| C-05 | this document (`final_r02_goalrows.py`); response_1 | Q1 C-01, C-02 |
| C-06 | this document; `R02_away_collection_penalty_draft.md` | draft C-01 |
| C-07 | this document; response_1 | Q2 C-03 (exceptions) |
| C-08 | `R02_away_collection_penalty_draft.md` | draft C-01 |
| Variable TRADE_NON_CAPITAL_OFFICE | `R02_away_collection_penalty_goal.md`, draft | draft section 2 |
| Variables away_factor, collects, steers, has_trader, home_node, max_demand, class_scalar_A, trade_embargoed_by | this document; draft section 2 (names) | - |

## 8. Rejected claims

| Claim | Where it came from | The data that contradicts it |
|---|---|---|
| The ratios 0.597, 0.553, 0.551, 0.538, 0.505, 0.491, 0.384 (and 0.465, 0.45 ...) in the goal's "ratio" column show a different or variable penalty | R02 goal (median of the country's other nodes as baseline) | the median mixes domestic and foreign class values and embargo-reduced nodes; against the class baseline the rows are exactly 0.5 (C-05) |
| The penalty is additive, `1 + modifiers - 0.5` | considered in the goal's ratio discussion; the draft already rejects it | baselines from 1.045 to 2.137 all give exactly half (C-01) |
| Steering is exempt because the wiki sentence says so | draft C-02 (quote does not say it) | the quote does not say it; the exemption is supported by the data instead (C-02) |
| "`has_trader` is True in all 43 rows, so merchant presence cannot be tested" | draft section 1 | 5,033 merchants without action and 21,969 steering entries were tested (C-02) |
| Collecting is equivalent to "has key `total` and no `has_capital`" without exception | draft section 2 | one collector without `total` exists (POR english_channel S79, C-02) |
| 108 of 108 / 100 of 102 (two different totals) and "87 colonial country-saves without `has_capital`" | response_1 C-01, C-03, C-05 | replaced by the counts of C-01 and C-03 of this document (different baseline definition and scope); the 87 are inactive tags with stubs only |
| TUR `gulf_of_aden` was the first steering-to-away switch | response_1 U-1 | already corrected in its second pass: S79>S80 TUR comorin_cape; 14 switches in C-04 |

## 9. Disposition of request_2

| request_2 point | Where it is answered |
|---|---|
| Q1 other mechanisms that change `max_demand` at specific nodes | side question for R01 (and R10 for privateers/embargo); the data exception is C-07 |
| Q2 modifier `reduced_trade_penalty_on_non_main_tradenode`, combination with 0.5 | topic R15, question Q1 |
| Q3 main trade city / capital node, save field and rule, colonial nations | data part: C-03 (colonial nations closed); the sourced rule for the differing case: topic R15, Q2 |
| Q4 `TRADE_POWER_HOME_BONUS` define and interaction | topic R01 (same question as its request_2 Q3) |
| Q5(a) source of the away-penalty quote, (b) the define `TRADE_NON_CAPITAL_OFFICE` | recorded as `reported` in C-08 and section 6 (sourcing only; the data confirms the factor) |
| Q5(c) merchants with `has_trader` but neither `type` nor `total` | C-02 (not penalised: 5,028 of 5,033) |
| Data row: `has_capital` follows capital or main trade port | topic R15, Q2 |
| Data row: form of `r` | topic R15, Q1 |
| Data row: 87 colonial country-saves without `has_capital` | C-03 (inactive tags) |
| Data row: 2 collect-away and 18 steer-away exceptions (SUN, DLI, S80/U01) | C-07 for SUN malacca; the remaining steering/passive deviations belong to R01 |
| Data row: additive vs multiplicative on a 1444 start | closed by C-01 (multiplicative at all baselines 1.045-2.137); start snapshots have no away collector |
| Data row: the within-country switch is one country | C-04 (14 switches, 13 of 14 at the expected ratio) |

## 10. Note 2026-10-05 - Venice series U07-U30 (replication; no rule changes)

New data (saves U07-U30, a hands-off game of VEN from 1444.11.11 to 1445.7.2; details and scripts in `R02_away_collection_penalty_response_1.md`, section 'Update 2026-10-05 - Venice series', VA-1..VA-4, with second-pass verification):
- The rule of section 1 reproduces in a game outside the TUR campaign: 449 away-collecting entries of AI countries (23 countries, 25 country-node pairs) have `max_demand` = 0.5 x a class value of the country in 438 cases; steering away is not halved (12,320 of 12,388; the 68 others are embargo or top-node-class effects). The 11 exceptions are one pair (GEN crimea), moved to R01 request_2 as a side question (base at an embargoed top-province node).
- Replication of the closed row 'additive vs multiplicative on a 1444 start': the additive form `md - 0.5` is also excluded at md about 1.0 by 3-decimal data in a 1444 game (KTU ganges_delta 1.009 -> 0.505, additive would be 0.509; ARA genua 1.067 -> 0.534, additive 0.567).
- A start snapshot contains collecting-away merchants (5,028 entries in the 78 start snapshots) but with no `money` and no penalty: the penalty, the money and the +2 flat merchant power first appear at the first 1st of a game (38 away merchants in a fresh game, 23 remaining at 1444.12.1, all with money, 19 at exactly 0.5 x their previous `max_demand`). So the count 'away collectors in the 78 start snapshots: 0' of section 4 (collector = entry with `total`/`money`) is a statement about un-ticked snapshots, not about start-type games as such: a game advanced to its first 1st has them.
- `capital` differs from `trade_port` in 0 of 33,120 further country-saves; R15 Q2 is unchanged.
