# R03 final - Which countries' power counts in pull_power (and why some non-collectors are excluded)

Status: FINAL (2026-10-05). Merged from `R03_pull_power_composition_draft.md` (wiki rule and quotes), `R04_transferred_trade_power_response_1.md` (Q6, the POR case) and a fresh whole-corpus verification written for this document. Corpus: the 85 entries of `backend/tests/fixtures/saves/saves.json` (S01-S80 and the stored user cases U01-U05); U01/U02 are copies of S80/S79, so there are **83 distinct saves** (`U01`/`U02` counted separately only where a line says "85 saves"). Scripts: `backend/scripts/research/r03_final_verify.py`, `r03_final_detail.py`, `r03_final_endnodes.py`, `r03_final_ab.py`, `r03_final_alt.py`, `r03_final_sample.py` (independent code: raw save keys and the trade graph only, no `app.trade.calc`). "Match" = |computed - recorded| <= 0.0105 on the node sum; every match counted below is also within 0.0005 (float noise), so the rule is exact at the save's 3-decimal precision.

## 1. Answer

```
# game 1.37.5; effective power of a country at a node
eff(c,n)        = val(c,n) - t_out(c,n) + t_in(c,n)             # entries that carry only t_in/t_out count with val = 0

collects(c,n)   = entry(c,n) has key `total`  OR  entry(c,n) has key `has_capital`     # has_capital = the country's main trade port node
steers(c,n)     = entry(c,n) has key `type`                                               # merchant present and set to steer
collect_set(c)  = { n : collects(c,n) }
steer_set(c)    = { n : steers(c,n) }
downstream*(n)  = all nodes reachable from n over >= 1 outgoing links (any number of hops)

pulls(c,n)      = steers(c,n)
                  OR ( NOT collects(c,n)  AND  ( collect_set(c) U steer_set(c) ) ∩ downstream*(n) != {} )     # rule B (used)
                  # rule A (the wiki rule) is the same without  U steer_set(c)

retain_power(n) = SUM over c with collects(c,n) of eff(c,n)
pull_power(n)   = SUM over c with pulls(c,n)    of eff(c,n)            # absent at end nodes (no outgoing links)
retention(n)    = retain_power / (retain_power + pull_power)           # 1.0 when both are 0
not counted     = NOT collects AND NOT steers AND nothing downstream collected or steered by the country:
                  its power is in node.total but in neither retain_power nor pull_power
```

Rule B is the rule of this document because it has the fewest unexplained exceptions over the corpus: **5,895 of 5,896 nodes** with `pull_power` (one exception, `ethiopia` in U05, is a stale-aggregate case, C-09). Rule A (steering downstream not counted) is the literal wiki rule; it fits **5,893 of 5,896** and fails exactly at S79 `ohio` and `chesapeake_bay` (the overlord POR) and at U05 `ethiopia`. B and A differ at exactly those two S79 nodes and nowhere else in the corpus, and the record follows B there (C-02). So the core of the rule is confirmed by the whole corpus, and the extension "steering downstream also makes a non-collector pull" rests on one country in one save (inferred).

Properties that follow (each tested, see section 4):
- Membership is a property of the pair (country, node), not of the country: the goal's example TUR excluded at 4 nodes and included at 17 is the expected pattern.
- Merchant presence does not matter by itself; only the action does. Merchants with neither `type` nor `total` behave like countries without a merchant (C-03).
- Province power or propagated-only power (`prev`) does not matter; both are part of `val`.
- Steering countries are always counted (every steering entry in the corpus fits).
- Transferred power is handled through `eff`; receiving transferred power does not make a country pull (C-04).

## 2. Variables

```json
[
 {"id":"eff","meaning":"effective power of a country at a node: val - t_out + t_in (entries with only t_in/t_out use val = 0)","unit":"power","kind":"derived","source":{"type":"save","path":"trade.node[].<TAG>.{val,t_out,t_in}"},"confidence":"confirmed (corpus)"},
 {"id":"collects","meaning":"country collects at the node: key `total` present or key `has_capital` present","unit":"bool","kind":"read","source":{"type":"save","path":"trade.node[].<TAG>.total | has_capital"},"confidence":"confirmed with one exception (C-06)"},
 {"id":"steers","meaning":"merchant steers at the node: key `type` present","unit":"bool","kind":"read","source":{"type":"save","path":"trade.node[].<TAG>.type"},"confidence":"confirmed (corpus)"},
 {"id":"collect_set","meaning":"nodes where the country collects (home node included)","unit":"set of node ids","kind":"derived","source":{"type":"save","path":"all entries of the country over trade.node[]"},"confidence":"confirmed (corpus)"},
 {"id":"steer_set","meaning":"nodes where the country steers","unit":"set of node ids","kind":"derived","source":{"type":"save","path":"all entries of the country over trade.node[]"},"confidence":"inferred (only POR S79 distinguishes it from collect_set, C-02)"},
 {"id":"downstream_closure","meaning":"nodes reachable over outgoing links, any number of hops","unit":"set of node ids","kind":"derived","source":{"type":"other","path":"backend/data/tradenodes.json (80 nodes, 159 links; from common/tradenodes)"},"confidence":"confirmed"},
 {"id":"val","meaning":"effective power incl. multiplier (R01); stored","unit":"power","kind":"read","source":{"type":"save","path":"entry.val"},"confidence":"confirmed"},
 {"id":"t_out","meaning":"power given to the overlord (R04); stored","unit":"power","kind":"read","source":{"type":"save","path":"entry.t_out"},"confidence":"confirmed"},
 {"id":"t_in","meaning":"power received from subjects (R04); stored","unit":"power","kind":"read","source":{"type":"save","path":"entry.t_in"},"confidence":"confirmed"},
 {"id":"retain_power","meaning":"sum of eff of collecting countries","unit":"power","kind":"derived","source":{"type":"save","path":"node.retain_power"},"confidence":"confirmed (5,966 of 5,968 nodes, C-06, C-09)"},
 {"id":"pull_power","meaning":"sum of eff of pulling countries; absent at end nodes","unit":"power","kind":"derived","source":{"type":"save","path":"node.pull_power"},"confidence":"confirmed (5,895 of 5,896 nodes, C-01, C-02)"},
 {"id":"retention","meaning":"retain_power / (retain_power + pull_power)","unit":"fraction","kind":"derived","source":{"type":"save","path":"node.retention"},"confidence":"confirmed"},
 {"id":"already_sent","meaning":"not part of membership; R09 response_1 C-13 relates it to province_power/5 x k","unit":"unknown","kind":"unknown","source":{"type":"save","path":"entry.already_sent"},"confidence":"UNKNOWN meaning; no effect on membership (C-07)"}
]
```

## 3. Claims

### C-01 Pull membership: steering, or not collecting here and collecting downstream
Claim: a country's effective power at a node is in `pull_power` iff it steers there, or it does not collect there and collects at some node downstream (any number of hops). All other non-collecting power is in neither `retain_power` nor `pull_power`.
Formula: `pulls(c,n) = steers(c,n) OR (NOT collects(c,n) AND collect_set(c) ∩ downstream*(n) != {})` (rule A).
Applies when: the node has outgoing links (end nodes have no `pull_power`).
Source: wiki `https://eu4.paradoxwikis.com/Trade` ("Transferring trade"), via `R03_pull_power_composition_draft.md` C-02; corpus verification `r03_final_verify.py`, `r03_final_ab.py`.
Quote: "A country with trade power in a node who either has a merchant present and set to steer, or is not collecting there but is collecting in a node somewhere downstream (no matter how many hops away), is transferring." (wiki text as quoted in the draft; not re-fetched for this document)
Confidence: confirmed for the data: rule A matches 5,893 of 5,896 nodes with `pull_power` in the 83 distinct saves (6,045 of 6,050 in the 85 entries). Exceptions: S79 `ohio` (recorded 440.306, A gives 402.981, difference -37.325 = POR's eff), S79 `chesapeake_bay` (646.532 vs 607.474, -39.058 = POR's eff), U05 `ethiopia` (247.475 vs 244.865, -2.610, C-09); in the 85-entry count the two S79 nodes appear twice (U02).
Caveats / contradicts: the wiki sections are banner-dated 1.25-1.30; the data shows the same rule in 1.37.5 saves, so the banner does not matter for the calculation.

### C-02 Extension: steering downstream counts like collecting downstream (inferred, one country)
Claim: for the membership test "collects downstream" a node where the country steers counts like a node where it collects.
Formula: rule B of section 1 (`(collect_set U steer_set) ∩ downstream*(n)`).
Applies when: a country has positive effective power at a node, does not collect there, collects nowhere downstream, but steers at a node downstream.
Source: `R04_transferred_trade_power_response_1.md` C-Q6.2 (first found there), independently re-run in `r03_final_ab.py` over all 83 distinct saves.
Quote: S79 `ohio`: `pull_power=440.306`, rule A 402.981, difference 37.325 = POR `val 1.11, t_in 36.215, t_from={ C04=24.181 C07=12.034 }` (no `has_trader`, no `type`, no `total`); POR steers at `champagne` and `north_sea` (both downstream of `ohio` and of `chesapeake_bay`) and collects only at `sevilla`. S79 `chesapeake_bay`: `pull_power=646.532`, A 607.474, difference 39.058 = POR's eff.
Counts: of 5,896 nodes, rules A and B differ (by more than 0.0105) in exactly 2, S79 `ohio` and `chesapeake_bay`; the record follows B in both and A in neither. In no other node of 83 saves does a country with positive eff satisfy "steers downstream, collects nowhere downstream, does not collect here".
Confidence: inferred - the evidence is one country (POR) in one save (S79; U02 is its copy). An alternative explanation, C below, was tested and refuted (C-04).
Caveats / contradicts: the wiki text does not mention steering downstream; B is a data-driven extension. The S80 and U03-U05 overlord BRZ receives transferred power at the same nodes (`ohio`, `chesapeake_bay`, `mississippi_river`, `panama`, `carribean_trade`) and is NOT counted there, which fits B because BRZ steers nowhere downstream.

### C-03 Only the (country, node) status matters; a merchant without action is not special
Claim: a merchant that neither steers nor collects (key `has_trader` without `type`, `total` or `has_capital`) is treated exactly like a country without a merchant: counted iff rule A/B says so for its power.
Source: `r03_final_ab.py`.
Quote: 4,453 such entries at nodes with `pull_power` in the 83 distinct saves; rule A classifies 1,482 as pulling and 2,971 as not counted, and the node sums match in 5,893 of 5,896 nodes with that classification (so the classification cannot be far off in the aggregate).
Confidence: confirmed as consistency with the node sums (whole corpus); the per-entry membership of a single entry is not observable, only node sums are stored.
Caveats / contradicts: the one place where such a merchant IS counted is C-06 (end node `english_channel`, S79).

### C-04 Receiving transferred power does not make a country pull (alternative refuted)
Claim: a country that receives transferred power (`t_in > 0`) and does not collect at the node is not thereby pulling; its status follows C-01/C-02.
Formula: rejected alternative C: `pulls = A OR (NOT collects AND t_in > 0)`.
Source: `r03_final_alt.py`.
Quote: 1,434 non-collecting receivers in the 83 distinct saves, of which rule A already counts 1,386. Rule C differs from A in 48 nodes; the record follows A in 46 and C in 2 (the two S79 POR nodes). E.g. SPA at `chesapeake_bay` in S38-S78 (eff 0.76-16.9) is not counted; BRZ at `mississippi_river` in S80 and U03-U05 (eff 129-138) is not counted.
Confidence: confirmed (whole corpus; the alternative is refuted in 46 of 48 discriminating nodes).

### C-05 Effective power and the two sums
Claim: `eff = val - t_out + t_in` is the quantity summed in both `retain_power` and `pull_power`; entries that carry only `t_in`/`t_out` contribute with `val = 0`.
Formula: see section 1.
Source: `r03_final_verify.py`; consistent with the README integration log (R04 transfers).
Quote: with that definition `pull_power` matches as stated in C-01/C-02 and `retain_power` matches in 5,966 of 5,968 nodes with a `retain_power` (C-06, C-09 give the two exceptions). `retention = retain/(retain+pull)` computed from the rule's own sums deviates from the recorded `retention` by more than 0.0011 in 2 nodes under B (U05 `ethiopia`, U05 `gulf_of_aden`, both C-09) and in 4 distinct nodes under A (the same two plus S79 `ohio`, `chesapeake_bay`).
Confidence: confirmed (whole corpus, exceptions listed).

### C-06 What "collecting" is in the save, and its one exception
Claim: a country collects at a node iff its entry has `total` or `has_capital`.
Source: `r03_final_verify.py`, `r03_final_endnodes.py`, `r03_final_detail.py`.
Quote: `retain_power` equals the sum of eff over such entries in 5,966 of 5,968 nodes. The exception besides C-09: S79 (and U02) `english_channel`, an end node: computed 1,858.846, recorded `retain_power` 1,860.64; difference 1.794 = POR `{ val 1.794, max_pow 2.0, max_demand 0.897, has_trader }` (no `total`, no `has_capital`, no `type`); the node records `num_collectors 9` while 8 entries carry `total`/`has_capital`. So one merchant-only entry (max_pow 2.0 = the merchant constant, no provinces) is counted as a collector at an end node without a `total` key. At the three end nodes over the 83 distinct saves (249 instances), `retain_power` equals the sum over `total`/`has_capital` entries in 248 and also equals the sum over all entries in 5; 245 of 249 end nodes contain non-collecting entries, and leaving them out is correct in 244 of those 245 (the exception is the POR entry above).
Confidence: confirmed with one exception (S79 `english_channel`, cause UNKNOWN).

### C-07 `already_sent` is not a membership marker
Claim: the presence of `already_sent` does not indicate exclusion from `pull_power`.
Source: `r03_final_sample.py` (last block), 83 distinct saves, entries at nodes with `pull_power`.
Quote: entries with `already_sent`: 11,556 collecting, 1,399 steering, 1,154 pulling (by rule A), 1,200 not counted (7.8 %); without `already_sent`: 27,059 collecting, 20,433 steering, 15,004 pulling, 4,581 not counted (9.7 %).
Confidence: confirmed (whole corpus). The draft's observation that all 5 sample rows with `already_sent` are excluded does not generalise (section 8). Its meaning stays UNKNOWN here (R09 response_1 C-13: `already_sent = province_power/5 x k`, whole-number k).

### C-08 End nodes have no `pull_power`
Claim: end nodes (`english_channel`, `genua`, `venice`) have no `pull_power`; all collecting power is retained.
Source: `r03_final_endnodes.py`.
Quote: 249 end-node instances in the 83 distinct saves, 0 with a `pull_power`; `retention` is 1.0 there (see C-06 for the retain sum).
Confidence: confirmed.

### C-09 Recorded aggregates can contain a country that no longer has an entry (stale node sums)
Claim: when a country ceases to exist between the last monthly computation and the save, its entry disappears at once but `pull_power` / `retain_power` keep its power.
Source: `R12_monthly_tick_timing_response_1.md` Update 2026-10-05 and its second-pass Verification; re-found here as the only two U05 failures.
Quote: U05 (1693.4.15) `ethiopia`: `pull_power` recorded 247.475, computed 244.865, difference 2.610 = AFA's `top_power` value there; U05 `gulf_of_aden`: `retain_power` recorded 795.345, computed 787.827, difference 7.518 = AFA's `top_power` value there. AFA has an entry in U04 at both nodes (`ethiopia`: `type 1`, steering, `val 2.586`; `gulf_of_aden`: capital node, `val 14.082`) and none in U05.
Confidence: inferred (one event in one save; exact equalities with AFA's `top_power` values, 2.610 and 7.518). These two nodes are not rule failures.

### C-10 Wiki statements behind the rule (source text, not re-fetched)
Claim: the wiki describes the same structure: only countries that collect or transfer count; a country without a merchant collects at its home node and otherwise pulls only where the node is upstream of a node where it collects; all transferring countries pool their power.
Source: `https://eu4.paradoxwikis.com/Trade` (sections "Collecting trade", "Trade with no merchant", "Pulling trade value forward"), quoted in the draft C-01, C-03, C-04.
Quote: "The effective trade power in a node only counts the trade power of the countries which collect or which transfer downstream, but it doesn't count the countries which have their trade capital upstream." / "All countries transferring trade pool their trade power to pull trade out of the node."
Confidence: reported (quotes taken from the draft, not re-fetched; the data reproduces their content).
Caveats / contradicts: the draft's caveat that the "at least 10 provincial trade power" propagation threshold conflicts with `TRADE_PROPAGATE_THRESHOLD = 2` is closed by R05: the recorded `prev` fits `province_power >= ~10` (between 9.961 and 10.036), i.e. 2 x divider 5; it does not affect pull membership.

## 4. Validation against the data

**Whole corpus, 83 distinct saves (85 entries), nodes with `pull_power`:**

| Rule | Nodes | Match | Exceptions |
|---|---|---|---|
| A (wiki) | 5,896 (6,050 incl. copies) | 5,893 (6,045) | S79 `ohio`, S79 `chesapeake_bay`, U05 `ethiopia` (+ U02 copies of the two S79 nodes) |
| B (used) | 5,896 (6,050) | 5,895 (6,049) | U05 `ethiopia` (C-09) |
| `retain_power` (collects = `total` or `has_capital`) | 5,968 (6,103) | 5,966 (6,100) | S79 `english_channel` (C-06, +U02 copy), U05 `gulf_of_aden` (C-09) |

**Worked examples of the goal (both found in S79 and in its copy U02; reproduced from the save rows):**
- `xian` (recorded retain 191.452, pull 56.459, total 261.611). Pulling: QIC steering 28.841 + RUS 20.135 + SHY 4.192 + TRS 3.291 = 56.459 = `pull_power`. Not counted: MNG 7.737 and BNG 5.963 (neither collects nor steers nor collects downstream of `xian`; their sum 13.700 is the goal's difference 70.159 - 56.459). Collecting: CHC 112.619 + CSH 78.833 = 191.452 = `retain_power`. `retention` = 191.452 / (191.452 + 56.459) = 0.7723. Total check: 191.452 + 56.459 + 13.700 = 261.611.
- `hormuz` (recorded pull 363.19, total 411.646). Pulling: TUR 342.444 + IRQ 12.796 + TRS 5.596 + DAW (steering) 2.354 = 363.190. Not counted: YEM 47.378 and SND 1.078 (SND: `val 2.055 - t_out 0.977`). 363.190 + 47.378 + 1.078 = 411.646 = `total`. Both exclusions are what rule A/B gives (per the rule, YEM and SND neither collect nor steer downstream of `hormuz`; TRS and IRQ do).

**The labelled sample of the goal:** the table has 43 rows (the goal says 40); all 43 (save, node, tag) rows exist in the fixture saves, and the label (included / EXCLUDED) agrees with rule A and with rule B in 43 of 43. Two rows the draft could not decide: S70 `ivory_coast` POR "EXCLUDED" (draft: possible contradiction) - in S70 POR collects only at `brazil` and steers only at `amazonas_node`, neither downstream of `ivory_coast`, so it is correctly excluded; S59 `yumen` QNG "EXCLUDED" - QNG collects only at `beijing`, which is not downstream of `yumen`, so it is excluded.

**Merchants without action:** C-03. **Receivers of transferred power:** C-04. **`already_sent`:** C-07.

**Failures / unexplained (complete list):** S79 `english_channel` retain (C-06, one merchant-only entry counted without `total`); U05 `ethiopia` pull and U05 `gulf_of_aden` retain (C-09, stale aggregates); the extension C-02 rests on two nodes of one save. Every other node of 83 saves matches.

## 5. Unknowns, contradictions between sources, and what would settle them

1. **Is "steering downstream counts" (C-02) general?** Evidence is POR in S79 (nodes `ohio`, `chesapeake_bay`). Data that settles it: another save in which a country with positive effective power at a node neither collects there nor downstream but steers downstream (rules A and B then differ in that node); or two saves identical except for that country's steering target. Update 2026-10-05 (Venice series U07-U30, `venice_b_35_r03_ab.py`): rules A and B give the same `pull_power` in all 1,584 node instances (24 saves x 66 nodes), i.e. no save of the series contains a case that separates them; both match 1,581 of 1,584 at tolerance 0.0105 (the project stage counts 4 at its own tolerance); all misses are in the mid-month saves U12 and U13, at nodes (astrakhan, champagne) where a merchant was recalled or placed after the last tick (`venice_b_15_stages.py`).
2. **Why is the merchant-only POR entry at S79 `english_channel` counted as a collector without `total` (C-06)?** Data that settles it: the action and location of POR's merchants in S79 (`countries.POR.merchants`), and other end-node entries with `max_pow` equal to the merchant constant only (none seen besides this one in 83 saves).
3. **Timing of stale aggregates (C-09).** Data that settles it: further saves in which a country lost its last province (or a merchant was recalled) between the last 1st-of-month and the save date, with the country block and the node sums both present. Update 2026-10-05: a merchant recall (VEN, U25 -> U26, three merchants) changes only the entry flags and leaves every node sum and link value of the last tick unchanged until the next tick (R08 response_1, V-R08-4), and the project's `pull_power` stage passes on all 8 tick-day Venice saves after the first tick, on U26 (recalled, stale) and on U27-U30 (VEN idle, then steering again: a recalled VEN still counts as pulling because it collects downstream at `venice`); a country losing its last province (the U05 case) is still a single event.
4. **Meaning of `already_sent`.** No effect on membership (C-07). Data that settles it: a pair of saves differing in one steering merchant placement, read for `already_sent` (R09 response_1 C-13 relates it to `province_power / 5 x k`, k in 1..5).
5. **Forwarding weights when nobody steers** (draft C-05, equal split) belong to R08; the stored weights are not equal in 303 of 602 start-save nodes with >= 2 links and no steerer (section 8). Not settled by this topic.
6. **Trade companies, subjects, trade leagues, war, embargo:** no deviation from the rule was found in any of the 5,896 nodes, so none of them changes pull membership in the corpus; no case isolates one of them as a variable, so they are not individually tested.

## 6. Sources (ranked)

1. Corpus verification of this document (85 fixture entries, 83 distinct saves; scripts `r03_final_*.py`): primary evidence for every count above.
2. `R04_transferred_trade_power_response_1.md` C-Q6.2 (POR case) and `R12_monthly_tick_timing_response_1.md` / `R10_embargo_privateers_transfers_misc_response_1.md` Update sections (stale aggregates, AFA): data-derived, each with its own second-pass verification.
3. https://eu4.paradoxwikis.com/Trade - official wiki; the only outside source with an explicit membership rule; reliable for the structure, banners dated 1.25-1.30, quotes carried over from the draft (reported).
4. https://eu4commands.com/trade-node - third-party node list, used only by the draft; superseded by the project's `common/tradenodes` graph (`backend/data/tradenodes.json`).

## 7. Provenance

| Item | Source file | Point |
|---|---|---|
| Rule A (C-01) | `R03_pull_power_composition_draft.md` C-02; corpus verification (this document, `r03_final_verify.py`) | - |
| Rule B / extension (C-02) | `R04_transferred_trade_power_response_1.md` C-Q6.2; corpus verification (`r03_final_ab.py`) | Q6 |
| Merchant without action (C-03) | corpus verification (`r03_final_ab.py`); draft section 4 raised the question | - |
| Receiver alternative refuted (C-04) | corpus verification (`r03_final_alt.py`) | - |
| `eff` and the sums (C-05) | project ledger (README integration log, R04); corpus verification | - |
| Collecting definition and exception (C-06) | corpus verification (`r03_final_endnodes.py`, `r03_final_detail.py`) | - |
| `already_sent` (C-07) | corpus verification (`r03_final_sample.py`); draft section 4 (observation); `R09_save_field_dictionary_response_1.md` C-13 | - |
| End nodes (C-08) | draft section 1 (consequence); corpus verification | - |
| Stale aggregates (C-09) | `R12_monthly_tick_timing_response_1.md` Update 2026-10-05; `R10_embargo_privateers_transfers_misc_response_1.md` Update 2026-10-05 | - |
| Wiki statements (C-10) | `R03_pull_power_composition_draft.md` C-01, C-03, C-04 | - |
| Threshold caveat closed (C-10) | `R05_trade_power_propagation_response_1.md` | Q2 |
| Variables `eff`, `collects`, `steers`, `collect_set`, `downstream_closure`, `pull_power`, `retain_power`, `retention` | `R03_pull_power_composition_draft.md` section 2 (names), corpus verification (confidence) | - |
| Variable `steer_set` | `R04_transferred_trade_power_response_1.md` C-Q6.2 | Q6 |
| Variable `already_sent` | `R09_save_field_dictionary_response_1.md` | C-13 |
| Worked examples and labelled sample | `R03_pull_power_composition_goal.md` (rows), corpus verification (`r03_final_sample.py`) | - |

## 8. Rejected claims

| Claim | Where it came from | The data that contradicts it |
|---|---|---|
| "Possible contradiction": S70 `ivory_coast` POR should be included if its home is `sevilla` | draft section 4 | In S70 POR collects only at `brazil` and steers at `amazonas_node`; neither is downstream of `ivory_coast` (downstream list: bordeaux, carribean_trade, champagne, chesapeake_bay, english_channel, genua, lubeck, north_sea, sevilla, st_lawrence, valencia). The row is excluded, as labelled. |
| All 5 sample rows with `already_sent` are EXCLUDED (suggesting `already_sent` marks exclusion) | draft section 4 | 15,309 entries carry `already_sent` in 83 saves: 11,556 collect, 1,399 steer, 1,154 pull, 1,200 are not counted (C-07). |
| Equal split of the pulled value among all outgoing nodes when nobody steers | draft C-05 (wiki quote) | R08 response_1 Q5: in the start snapshots 299 of 602 nodes with >= 2 links and no steerer have equal weights, 127 put everything on the first link, 176 are other (forwarding is R08's topic; not a membership statement). |
| Hypothesis (a): steering countries may be excluded in some cases | draft section 5, item 4 | Every steering entry is counted; rule A/B fit 5,893/5,895 of 5,896 nodes with steering as unconditional membership. |
| Hypothesis (b): transferred power takes the receiver's status | draft section 5, item 4 | C-04: making receivers pull fits 2 of the 48 nodes where it differs from A, the record follows A in 46. `val - t_out + t_in` with the country's own status fits all other nodes. |
| Hypothesis (c): pirates / unlisted entries change the sums | draft section 5, item 4 | The sums match without any `PIR` term in 5,893-5,895 of 5,896 nodes (PIR entries carry no `val`); at end nodes `retain_power` equals the collectors' sum in 248 of 249 (C-06, C-08). |
| "Merchants that are neither steering nor collecting contradict the wiki (UNKNOWN)" | draft section 4 | They behave like merchant-less countries (C-03): 4,453 entries, no node-sum misfit attributable to them. The single counted case is C-06. |
| Draft's "at least 10 provincial trade power" conflicts with `TRADE_PROPAGATE_THRESHOLD = 2` | draft C-03 caveat | No conflict: 2 x divider 5 = 10 (R05: the threshold lies between 9.961 and 10.036). |
| The goal's "40-row" sample | goal | The table has 43 rows; all 43 are reproduced by rules A and B. |
| Wiki quotes "last verified 1.25-1.30" for 1.37.5 | draft section 1 | Not contradicted; the rule is reproduced on 1.37.5 saves (C-01). The quotes stay `reported` because they were not re-fetched. |

## Data basis (2026-10-06)

On 2026-10-06 the research data was rebuilt (`docs/research/data_audit.md`): only **clean** saves are kept (the 1st of a month after the game's first trade computation, none of the player's merchants or fleets on the way; R12 final). Kept: U04 (TUR 1691.11.01), U10, U14, U20, U25, U27, U28, U29 (VEN 1444-1445). Removed: the 78 start snapshots S01-S78 and U07-U09 (saved before the first computation: steering weights, `add` and other computed fields are placeholders there) and 21 mid-month saves (S79, S80, U01-U03, U05, U06, U11-U13, U15-U19, U21-U24, U26, U30: numbers from the last 1st, merchant/ship flags from the save day). Counts above that include removed saves are kept as recorded but are **unverified on clean data** unless listed as re-checked below. Clean-data stage results quoted here: `scripts/verify_all.sh` on the 8 kept saves (calc 0.2.0).

- Rule B on clean data: `pull_power` exact in 539 of 539 checks and `retain_power` in 640 of 640 on the 8 kept saves: **confirmed on clean data**. The exceptions of this file (S79 `english_channel`, U05 `ethiopia` / `gulf_of_aden` stale AFA aggregates) were in removed mid-month saves; the steering-downstream extension (C-02) rested on S79 only and is **unverified on clean data**.
