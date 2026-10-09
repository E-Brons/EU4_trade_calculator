# R05 response 1 - Trade power propagation (prev)

Scope: only points the 82 fixture saves settle. Every number comes from a script run (`backend/scripts/research/r04_r05_r06_r05*.py`, helper `r04_r05_r06_flat.py`, snapshot of the repo in /tmp/eu4research/repo). "Snapshots" = S01-S78 (hands-off start saves); "played" = S79, S80, U01, U02 (not saved on the 1st of a month; U01/U02 are the same dates as S80/S79). Candidate = a (save, node B, tag) that has an entry at B, or whose tag has `province_power >= 10` at some downstream node D of B (113,559 candidates: 109,487 snapshot, 4,072 played).

## Q2 - Threshold semantics

### C-Q2.1 Threshold lies between 9.961 and 10.036 on downstream `province_power`
Claim: a downstream node D contributes to `prev` only if the country's `province_power` at D is >= ~10. In the snapshots the largest `province_power` that did not propagate is 9.961 and the smallest that did is 10.036.
Formula: contribution_D = trunc3(province_power_D / 5) if province_power_D >= 10 else 0.
Applies when: the link B->D is carrying flow (see Q3).
Source: save corpus, `r04_r05_r06_r05h.py`.
Quote (values just below / above 10, snapshots): below 9.88, 9.884, 9.9, 9.92, 9.955, 9.961; above 10.036, 10.038, 10.08, 10.092, 10.125, 10.14.
Confidence: confirmed for "threshold in (9.961, 10.036]"; `>` vs `>=` at exactly 10.000 is UNKNOWN (no save has an entry at exactly 10.000). `province_power/5 >= 2` is the same test as `province_power >= 10`; the data cannot tell them apart.
Caveats: `TRADE_PROPAGATE_THRESHOLD = 2 -> 10` is inferred, not documented.

## Q3 - Residual failures

With the rule "per-link truncation + threshold 10" and no other condition, 168 of 110,589 entries that carry data keys fail (tolerance 0.0005): 158 with recorded `prev` = 0 and 10 (MOR, S80/U01) with `prev` higher than predicted.

### C-Q3.1 The `prev` = 0 entries (first group) are links whose node `steer_power` weight is 0 (start snapshots only)
Claim: in the 78 start snapshots, propagation along link B->D happens exactly when the recorded `steer_power` weight of that link at node B is > 0. The 158 failing entries (california/XAL 40, cape_of_good_hope/BEN, KON, JOL 35 each, patagonia/INC 5, cuiaba/C04 5, amazonas_node/C03 3) are all links with weight 0, and in total 3,181 snapshot (B, D, tag) links with downstream `province_power >= 10` have weight 0 (most of them with no entry at all at B).
Formula: prev_B(tag) = sum over the outgoing links i of B (graph edge order = order of the node's `steer_power` list) with `steer_power[i] > 0` of trunc3(province_power_D(tag)/5) over those D with province_power_D(tag) >= 10.
Applies when: snapshot saves.
Source: `r04_r05_r06_r05g.py`, `r04_r05_r06_r05h.py`, `r04_r05_r06_r05_summary.py`.
Quote: S14 `california` `steer_power={ 0.0 1.0 0.0 0.0 }` (links mexico, mississippi_river, girin, polynesia_node): XAL has `province_power=11.31` at mexico and at california only `province_power=0.87 max_pow=0.87` (no `prev`); S14 `cape_of_good_hope` `steer_power=0.0`: BEN/KON/JOL have `province_power` 28.46 / 18.599 / 20.593 at ivory_coast and `potential=-0.002`, no `prev`.
Result: snapshots 109,487 of 109,487 candidates reproduced exactly (0 failures) with the gate; 106,377 without it. Single-link cases: weight > 0 and propagated 33,808; weight 0 and not propagated 3,039; 0 exceptions.
Confidence: confirmed as a description of the 78 snapshots. NOT confirmed as a general game rule: see C-Q3.2.
Caveats: the weight depends on `val`, which contains `prev`; a what-if that changes steering changes which links propagate, so the two cannot be computed independently.

### C-Q3.2 In the played saves the weight gate does not hold
Claim: in S79, S80, U01, U02 the gate explains fewer entries than the plain threshold rule.
Quote: single-link cases in the played saves (1,836): weight > 0 and propagated 1,636; weight 0 and propagated 182; weight 0 and not propagated 18 (all `polynesia_node` -> australia/panama, S79 and S80 `steer_power` of polynesia_node differ); weight > 0 and not propagated 0. All candidates: gate 3,796 of 4,072; threshold rule without the gate 4,044 of 4,072. Example S80 `california` `steer_power={0.885 0.114 0.0 0.0}` yet entries propagate over the link to girin (weight 0).
Confidence: the contradiction is confirmed. The reason is UNKNOWN. Candidate explanation (inferred, untested): in a save not written on a tick day the stored link weights and the stored `prev` come from different ticks. What would settle it: two saves of the same game on consecutive days with unchanged steering, or an intervention pair (R14).
Updated 2026-10-05: the candidate explanation (a save not written on a tick day) is REJECTED by U04 (in-game date 1691.11.1, a tick day): the gate fails there like in U03, U05, S79 and S80, and the plain threshold rule is exact in every failure. The difference is start saves versus played saves (section 'Update 2026-10-05', U-R05-2).
Caveat: the simple threshold rule therefore fails for the 78 snapshots (3,110 of 109,487 candidates) and the gated rule fails for the played saves (276 of 4,072); neither alone fits all 82 saves.

### C-Q3.3 Second group (MOR, S80/U01): ships propagate for MOR with factor 0.25
Claim: the extra `prev` of MOR is 0.25 x downstream `ship_power` / 5.
Formula: prev_B(MOR) += sum over D (link allowed, province_power_D >= 10) of ship_power_D(MOR) x 0.25 / 5.
Source: `r04_r05_r06_r05d.py`, `r04_r05_r06_r05g.py`.
Quote (S80, same in U01): kongo prev 10.797 vs 10.272 (+0.525; ivory_coast `ship_power=10.5 light_ship=3`, province_power 51.36); katsina 12.305 vs 11.78 (+0.525; tunis ship_power 10.5); cape_of_good_hope and brazil 10.797 vs 10.272 (+0.525); timbuktu 14.216 vs 13.341 (+0.875 = (safi 7.0 + ivory_coast 10.5) x 0.05).
Result: MOR candidates (gated rule, all 82 saves: 426 snapshot + 34 played) 460: 460 match with the term, 450 without (the 10 others are the residuals above). Non-MOR entries with downstream `ship_power > 0` in played saves (S79 267, S80 232, U01 232, U02 267) are all explained without any ship term. The 78 snapshots contain 0 entries with downstream ship power, so "ships do not propagate" is tested only in the played saves.
Confidence: inferred (the term fits 10 of 10 residuals and 460 of 460 MOR candidates, but it is one country in one game: S80 and U01 are the same save). The factor 0.25 is fitted from three distinct ship-power sums (10.5, 10.5, 17.5), not from a source; the country modifier that produces it is UNKNOWN (the save has no string `propagat` and no `caravan`, checked on S80 gamestate).
Updated 2026-10-05: weakened, not refuted. In U03, U04, U05 MOR has no ship power and no downstream node with provincial power >= 10 and ship power, so the term is untestable there; for every other tag the plain rule needs no ship term in four played saves (section 'Update 2026-10-05', U-R05-3).

## Q4 - `ship_power_propagation` (data part only)
The save does not store it: the string `ship_power_propagation` does not occur in the S80 gamestate, and the MOR country block has only `active_idea_groups` (MOR_ideas 7, ...) and `modifier` entries from which it could come. See C-Q3.3 for the fitted effect. Which ideas/policies grant it: not answered (needs an outside source). Whether the threshold 10 applies to the province power when ships propagate: all MOR cases in the data have `province_power >= 10` at the downstream node with ships, so UNKNOWN.

## Q5 - Rounding and `caravan_power`

### C-Q5.1 Truncation per link, not rounding and not truncation of the sum
Claim: each downstream link contributes trunc3(province_power_D/5) and the contributions are added.
Formula: prev = sum_D trunc3(province_power_D / 5).
Source: `r04_r05_r06_r05h.py`; exact-match tolerance 1e-6, snapshot candidates with the weight gate (109,487).
Quote / result (exact matches of all / single-link (33,808) / multi-link (1,367)):
- sum_D trunc3(p/5): 109,487 / 33,808 / 1,367 (0 failures)
- trunc3(sum p / 5): 108,962 / 33,808 / 842
- round3(sum p / 5): 99,447 / 24,680 / 455
- sum_D round3(p/5): 99,566 / 24,680 / 574
- exact sum p / 5: 89,667 / 15,241 / 114
Confidence: confirmed (the only variant with no failure; the multi-link column separates per-link truncation from truncation of the sum).
Caveat: this uses the 3-decimal `province_power` as stored; the game's underlying value may have more decimals, but the match is exact anyway.

### `caravan_power`
No key or string `caravan` exists in the S80 gamestate, and the trade-block keys of all 82 saves contain no such field, so it is not a stored quantity. Whether the game has it as an internal term: not answered (needs an outside source). The fits above need no caravan term.

## Not answered (needs an outside source)
Q1 (URLs, quotes, strategium.ru/wiki provenance, Defines.md status); Q2 "documented" wording of the define; Q4 which ideas/abilities grant `ship_power_propagation` (file + line); Q5 `caravan_power` existence in the game files.

## Updated UNKNOWN list
- Why the link-weight gate holds in all 78 snapshots but not in the played saves (needs same-game consecutive-day saves or an intervention pair).
- `>` vs `>=` at exactly 10.000 (needs an entry with exactly 10.000).
- Source and country/modifier of MOR's 0.25 ship factor (needs the MOR modifier values; other countries with the same modifier would show the same term).

## Verification (date 2026-10-04)
Independent re-computation in `backend/scripts/research/ver_r05.py`, `ver_r05b.py`, `ver_r05c.py` (own candidate set from `common.nodes`, graph edge order from `data/tradenodes.json`, per-link truncation by exact `Decimal` division of the 3-decimal `province_power`; no author code reused). The author's `r04_r05_r06_r05*.py` were also re-run. Note for anyone re-implementing: `trunc3(p / 5)` must divide exactly (or add a small epsilon); float division gives 2.719 for 13.6 / 5 and loses about 1,750 matches.

Re-run and matching:
- Candidates 113,559 (109,487 snapshot, 4,072 played); `steer_power` length equals the number of outgoing links in 6,560 of 6,560 nodes (so the weight-to-link index mapping is well defined).
- Snapshots: gated rule 109,487 of 109,487, ungated 106,377; variants: sum of per-link trunc3 109,487 (multi-link 1,367 of 1,367), trunc3 of the sum 108,962 (842), round3 of the sum 99,447 (455), exact sum / 5 89,667 (114).
- Threshold: largest non-propagating value 9.961, smallest propagating 10.036 (snapshots).
- Played saves: gated 3,796 of 4,072, ungated 4,044; single-link cases: weight > 0 and propagated 1,636, weight 0 and propagated 182, weight 0 and not propagated 18, weight > 0 and not propagated 0.
- Ungated rule on existing entries: 168 of 110,589 fail (158 with recorded `prev` = 0: california/XAL 40, cape_of_good_hope BEN/KON/JOL 35 each, patagonia/INC 5, cuiaba/C04 5, amazonas_node/C03 3; 10 MOR in S80/U01 with recorded `prev` higher).
- MOR: in the played saves the ship term (0.25 x downstream `ship_power` / 5) matches 34 of 34 MOR candidates (24 without it); 886 non-MOR played-save entries with ship power on an allowed link: 878 match the ungated rule without a ship term, 0 match with it (the 8 others are the weight-0 non-propagating `polynesia_node` cases).
- `ship_power_propagation`, `propagat`, `caravan` do not occur in the S80 gamestate text (0 occurrences each).

Corrected:
- C-Q3.3 confidence `confirmed` -> `inferred` (one country, one game; the factor 0.25 is a fit from three ship-power sums) and the meaning of "MOR candidates 460" made explicit (82 saves, 426 snapshot + 34 played).
- The `request_2` fact on the MOR term was aligned with this.

Not verified: the author's count "non-MOR entries with downstream ship_power > 0: S79 267, S80 232" uses a wider definition (any downstream ship power, not only on an allowed link); the narrower independent count above (886 over the four files) supports the same conclusion. The reason for the gate failure in the played saves, the `>` vs `>=` question and the source of the 0.25 remain UNKNOWN, as the response states.

## Update 2026-10-05 - saves U03, U04, U05

Status: the results below are single runs of `backend/scripts/research/u345_pipe_*.py` (own code; `u345_pipe_stages.py` runs the project's `verify_world`); they have not been independently re-computed, unlike the Verification section above. New data: U03 (in-game date 1691.1.9), U04 (in-game date 1691.11.1, a tick day; its file name says 1691.11.17) and U05 (1693.4.15) are melted Ironman saves of the same Ottoman campaign (player TUR, game 1.37.5, 80 trade nodes) as S79 (1665.4.22) and S80 (1682.4.18); they are not independent samples. Counts refer to these saves unless stated otherwise.

### U-R05-1 Propagation stage on the new saves
Project stage `propagation` (threshold 10, per-link truncation, no gate), failures / checks: U03 115/959, U04 117/963, U05 108/951 (S79 148/1055, S80 123/972; 78 start saves 5209/106535). Largest-error failures: `prev` at cuiaba, amazonas_node, patagonia for C14 (U03 and U04: calc 3.197 / 3.128 / 2.550, recorded 0.0; U05 3.307 / 3.159 / 2.654).

### U-R05-2 The tick-day hypothesis is rejected (updates C-Q3.2)
Rule tested (`u345_pipe_prev.py`): `prev(B, tag) = sum over links B->D with province_power_D(tag) >= 10 of trunc3(province_power_D / 5)`, with or without the gate "`steer_power` weight of the link > 0".

| save | date | candidates | gated rule exact | ungated rule exact |
|---|---|---|---|---|
| 78 start saves | 1444-1744 | 109,487 | 109,487 | 106,377 |
| S79 | 1665.4.22 | 1,060 | 993 | 1,055 |
| S80 | 1682.4.18 | 976 | 905 | 967 |
| U03 | 1691.1.9 | 963 | 891 | 959 |
| **U04** | **1691.11.1 (tick day)** | 967 | 896 | 963 |
| U05 | 1693.4.15 | 955 | 886 | 951 |

Result: U04 is written on the 1st of a month and behaves exactly like U03, U05, S79 and S80: the gate fails in 71 of 967 candidates (U03 72, U05 69) and in every one of those failures the ungated rule is exact (U03 72/72, U04 71/71, U05 69/69). The candidate explanation of C-Q3.2 (stored weights and stored `prev` come from different ticks in a save not written on a tick day) is therefore rejected; the split is start snapshot versus played save. Confidence: confirmed for these three saves and S79/S80 (one campaign, counts not independent).
Remaining misses of the ungated rule in played saves: the same 4 entries in each new save, all at `polynesia_node` (tags C02, C03, C12, HOL; node weights `[1.0, 0.0, 0.0]`, downstream panama/australia; recorded `prev` 0, rule predicts 26.075 / 3.437 / 46.832 / 4.848 in U03); S79 has 5 (adds MCA), S80 the same 4 plus 5 MOR cases. In the gate-failure nodes the weights look like `california [0.823, 0.176, 0.0, 0.0]`: links with weight 0.0 still contribute to `prev`. Two other gates were tested ("the link counts iff the downstream node has an `incoming` entry from B", and the same with value > 0): neither explains both groups (S79: 519/524 and 448/524; U03: 497/501 and 429/501). No single gate for `prev` in played saves is established: UNKNOWN. In the start saves the gated rule is exact everywhere and the ungated one is not.

### U-R05-3 The MOR ship term (updates C-Q3.3)
In U03, U04, U05 MOR has no own `ship_power` at any node and no downstream node with provincial power >= 10 and ship power, so the term is untestable there (0 cases), not refuted. For every other tag the ungated rule without any ship term is exact for all entries with downstream `ship_power > 0` outside `polynesia_node`: S79 234/234, U03 207/207, U04 210/210, U05 213/213 (S80 200/205; the 5 misses are MOR). "Ships do not propagate" now holds in four played saves of the same campaign; the MOR case remains a single-country, single-save observation (inferred). UNKNOWN: what gives MOR the extra term.

### Updated UNKNOWN list (2026-10-05)
- What differs between start saves and played saves such that links with steer weight 0 propagate (the tick-day candidate is rejected).
- Which rule, if any, selects the links that feed `prev` in played saves (both tested gates fail on one group); why 4 entries at `polynesia_node` (C02, C03, C12, HOL) have `prev` 0.
- Source and country/modifier of MOR's 0.25 ship factor (untestable in U03-U05).
- `>` vs `>=` at exactly 10.000.

### Verification 2026-10-05 (second pass)

Method: new code `backend/scripts/research/ver2_c_stages.py` (project `verify_world` over all 85 manifest saves; U01/U02 are copies of S80/S79, so corpus-wide counts contain two duplicates), `ver2_c_identities.py` (own re-computation of the identities, prev rule, gate and ship-term counts from the parsed trade trees, exact decimal truncation), `ver2_c_gates.py`, `ver2_c_worst.py`.

Matched: propagation stage 115/959 (U03), 117/963 (U04), 108/951 (U05), S79 148/1055, S80 123/972, 78 start saves 5,209/106,535; worst failures `prev` of C14 at cuiaba / amazonas_node / patagonia (3.197 / 3.128 / 2.55 vs 0.0 in U03 and U04; 3.307 / 3.159 / 2.654 in U05). Candidates / gated exact / ungated exact: 78 start saves 109,487 / 109,487 / 106,377; S79 1,060 / 993 / 1,055; S80 976 / 905 / 967; U03 963 / 891 / 959; U04 967 / 896 / 963; U05 955 / 886 / 951. Gate failures 72 (U03), 71 (U04), 69 (U05), in every one the ungated rule is exact. Ship term: S79 234/234, U03 207/207, U04 210/210, U05 213/213 entries with downstream ship power outside `polynesia_node` exact without a ship term; S80 200/205 with the 5 misses all MOR (kongo, katsina, cape_of_good_hope, brazil, timbuktu); MOR has 3 entries with own `ship_power` in S80 and none in U03-U05. `polynesia_node`: weights `[1.0, 0.0, 0.0]` over nippon / australia / panama in S79, U03, U04, U05; the four tags (C02, C03, C12, HOL) have downstream provincial power >= 10 only at panama (C02, C03, HOL) or australia (C12), both weight-0 links; recorded `prev` 0; ungated prediction 26.075 / 3.437 / 46.832 / 4.848 in U03 (S79 adds MCA); `california` weights `[0.823, 0.176, 0.0, 0.0]` in U03. Alternative gates: "incoming entry from B" 519/524 (S79) and 497/501 (U03) over the candidates with a qualifying link, "incoming value > 0" 448/524 and 429/501; the ungated rule reaches the same 519/524 and 497/501 (the first alternative gate is equivalent to the ungated rule in these saves).
Sharpened: (1) the tick-day rejection rests on one tick-day played save (U04); it refutes the universal form of the theory, it does not identify a cause. Supporting fact: the 78 start saves are dated the 11th (59) or the 1st (19) and have 0 gate failures in both groups, so the day of the month does not matter there either. The U04 file name says 11.17 while the save says 1691.11.1; the counterexample needs the save date to be right. (2) At `polynesia_node` the gate is right (weight 0 and `prev` 0), so weight-0 links do not propagate everywhere in played saves. (3) Label of the tick-day result: `confirmed` as a counterexample in this campaign, not as a general statement about all played games.
Unverifiable: the cause of the start/played difference; what gives MOR the extra term.

## Update 2026-10-05 - Venice series U07-U30 (the start-versus-played split is history, not game mode)

Data: the Venice series U07-U30 (player VEN, game 1.37.5, non-Ironman plain-text saves, same mod list as S01, new campaign started 1444.11.11): U07 1444.11.11, U08 11.14, U09 11.30, U10 12.01, U11 12.02, U12 12.11, U13 12.31, U14 1445.01.01, U15 01.02, U16 01.15, U17 01.24, U18 01.30, U19 01.31, U20 02.01, U21 02.03, U22 02.10, U23 02.17, U24 02.28, U25 03.01 (U07-U25: no player action at all); then U26 03.31 (all three VEN merchants recalled during March), U27 04.01, U28 05.01 (ragusa merchant sent again), U29 06.01 (alexandria), U30 07.02 (wien). Scripts: `backend/scripts/research/venice_a_*.py` (loader `venice_load.py`), second pass `venice_a_ver.py` (raw text diff of the `trade` block, own Decimal loop for `prev`).

### V-R05-1 The weight gate holds before the first 1st and from then on with the bookmark weights, not with the current ones
Claim: `prev(B, tag) = sum over links B->D with province_power_D(tag) >= 10 of trunc3(province_power_D / 5)`, restricted to links whose node weight was > 0 in the bookmark state (U07). The gate on the CURRENT weights fails from the first 1st on (U10) exactly as in the played saves; the gate on the previous save's weights fails from the second 1st on; the gate on the bookmark weights is exact for every entry at every 1st.
Source: `venice_a_prev.py`, `venice_a_lag.py`, second implementation `venice_a_ver.py 2` (Decimal loop).
Quote (entries with `max_pow` / exact with: no gate / current-weight gate / bookmark-weight gate): U07-U09 1,187 / 1,186 / 1,187 / 1,187; U10 (12.1) 1,413 / 1,412 / 1,367 / 1,413; U14 (1.1) 1,500 / 1,499 / 1,457 / 1,500; U20 1,504 / 1,503 / 1,461 / 1,504; U25 1,501 / 1,500 / 1,458 / 1,501; U27 1,501 / 1,500 / 1,458 / 1,501; U28 1,501 / 1,500 / 1,458 / 1,501; U29 1,501 / 1,500 / 1,458 / 1,501; U30 1,502 / 1,501 / 1,459 / 1,502. Previous-save-weight gate (exact / entries): U10 1,413 / 1,413, U14 1,454 / 1,500, U20 1,461 / 1,504, U25 1,458 / 1,501. The single miss of the ungated rule in every save is XAL `california` (weights [0.0, 1.0, 0.0, 0.0], link to `mexico`, `province_power` 11.31, recorded `prev` absent): a link with weight 0 since the bookmark. The misses of the current-weight gate (46 entries at U10, 43 at U30, e.g. `girin` SHY/MNG -> beijing/siberia, `tunis` FRA/PRO/GEN/... -> valencia/genua, `comorin_cape` ADE/HDR/YEM/... -> gulf_of_aden, `basra` AKK/KAR/SYR/RAM -> aleppo) are links whose weight is 0 now but was positive at the bookmark (weights move after the first 1st, e.g. `tunis` [1.0, 0.0, 0.0]); they propagate.
Links with weight 0 in the bookmark state: 31; none of them is positive in any later save of the series, so the series cannot tell "zero at the start" from "never positive so far".
Confidence: confirmed for the series (one game); the general rule (link set fixed at game start, or links never positive) is inferred.
Consequence: the "start saves gated / played saves ungated" split (C-Q3.1/C-Q3.2, U-R05-2) is a history effect: in a played save the set of links that have always had weight 0 is unknown from the save alone; the 4 `polynesia_node` entries (weights [1.0, 0.0, 0.0], `prev` 0) are consistent with links that were always 0.

### V-R05-2 Threshold
Smallest `province_power` that propagates in the series: 10.038 (MAI `wien` -> `rheinland`, `prev` 2.007), 10.047 (U30); the largest `province_power` below 10 in the series is 9.86 (U07-U13) and adds to no `prev` (the ungated rule with threshold 10 matches). With the earlier bounds (9.961, 10.036) the threshold T stays in (9.961, 10.036]; no entry has exactly 10.000: `>` versus `>=` is still open.

### V-R05-3 Ships
VEN has 3 light ships at `alexandria` (`ship_power` 6.0) and no `province_power` there; no entry of the series tests ship propagation. The MOR 0.25 factor is not addressed.

### Verification 2026-10-05 (second pass)
V-R05-1 recomputed with `venice_a_ver.py 2` (own loop, Decimal, weights read from the first save): exact for every entry at the 8 later 1sts (1,413 / 1,500 / 1,504 / 1,501 / 1,501 / 1,501 / 1,501 / 1,502).

## Data basis (2026-10-06)

On 2026-10-06 the research data was rebuilt (`docs/research/data_audit.md`): only **clean** saves are kept (the 1st of a month after the game's first trade computation, none of the player's merchants or fleets on the way; R12 final). Kept: U04 (TUR 1691.11.01), U10, U14, U20, U25, U27, U28, U29 (VEN 1444-1445). Removed: the 78 start snapshots S01-S78 and U07-U09 (saved before the first computation: steering weights, `add` and other computed fields are placeholders there) and 21 mid-month saves (S79, S80, U01-U03, U05, U06, U11-U13, U15-U19, U21-U24, U26, U30: numbers from the last 1st, merchant/ship flags from the save day). Counts above that include removed saves are kept as recorded but are **unverified on clean data** unless listed as re-checked below. Clean-data stage results quoted here: `scripts/verify_all.sh` on the 8 kept saves (calc 0.2.0).

- The "weight gate" (holds in start saves, not in played saves; C-Q3.1/C-Q3.2, U-R05-2) compares pre-first-tick placeholder weights with computed ones: it is most likely a **pre-first-tick artifact**, not a game rule. Re-test on clean saves only.
- Plain rule (threshold 10, per-link truncation) on clean data: 28 failures of 16,140 checks (7 of 8 saves); those 28 are the open part.
- MOR ship term: S80 only (removed): unverified on clean data.


## Update 2026-10-07 - controlled experiments (E00-P06)

Source: single-change experiments run in the game (EU4 1.37.5) with the automation in `tools/EU4-game-automation/experiments/` (`PLAN.md`, `RESULTS.md`, scripts `analysis/a1`-`a8`). Every treatment loads the same base save `out/E00/base_1444.12.01.eu4` (new game VEN 1444.11.11, spectator mode, saved on the first tick day), applies one change on 1444.12.01, runs with the AI of VEN switched off and is saved on 1445.01.01 (t1, first tick with the change) and 1445.02.01 (t2); saves under `tools/EU4-game-automation/experiments/out/<id>/` (67 saves checked: date, player VEN, plain text). Noise (controls E01a-E01d): two runs from one save diverge in other countries' fields (E01a vs E01b: 4,859 of 73,073 trade-block fields at t1, 8,029 at t2), but 101 of 103 VEN entry fields are identical in all four controls; only venice `money`/`total` vary (about +-0.6 %). Single-run comparisons are therefore used only for VEN power, demand, `val`, `prev`, `province_power`, `ship_power`, `add` and merchant fields, and for income only as the ratio `money/total`.

### V2-R05-1 `prev` = home `province_power` / 5, same tick
Claim (E09): +25 % `global_prov_trade_power_modifier` raises VEN `province_power` at venice 99.655 -> 114.317 at t1, and VEN `prev` at alexandria, ragusa and wien (the upstream nodes) 19.931 -> 22.863 = 114.317 / 5 in the same save. Confidence: confirmed.

### V2-R05-2 The threshold lies between 9.716 and 10.196
Claim (E15): Piedmont (103) base production 7 -> 10 (province trade power 4.08 -> 4.80) raises SAV `province_power` at genua 9.716 -> 10.436 at t1, and SAV `prev` 2.087 (= 10.436 / 5) appears at alexandria, champagne, ragusa, tunis and valencia; in the control there is no SAV `prev` at 9.716, and `prev` 2.039 appears at t2 after natural growth to 10.196. Consistent with `>= 10`; exactly 10.000 not observed. Confidence: confirmed for the bracket.

### V2-R05-3 Flat node power and ship power stay local
Claim (E14): a node modifier with power 10 at VEN ragusa raises ragusa `max_pow` by 10.000 (`val` +10.360) and changes no `province_power` and no upstream `prev`. Claim (P05): moving VEN's light-ship fleet (2 light ships) from venice to ragusa moves `ship_power` 4.000 and `light_ship` 2 between the nodes (`max_pow` -4.000 / +4.000) and changes no upstream `prev`: ships at venice (where VEN's `province_power` is far above 10) add nothing to `prev`. Confidence: confirmed (VEN).

### V2-R05-4 A start-zero link (inconclusive)
Claim (P06): XAL made the only steerer at california (link index 0): the node's weights go from [0, 1, 0, 0] to [1, 0, 0, 0] at the next tick and XAL `max_pow` 0.87 -> 2.87 (merchant term 2). XAL's `province_power` is far below 10, so whether a start-zero link propagates once positive is not answered. Confidence: confirmed for the weights only.

## Update 2026-10-08 - experiment round 2

Source: 27 single-change jobs run in the game by the automation (`tools/EU4-game-automation/experiments/round2/`: `PLAN.md`, `RESULTS.md`, scripts `analysis/`); saves under `round2/out/<id>/` (t1 = 1445.1.1, t2 = 1445.2.1; all dated, player and plain text checked). Controls as in round 1 (E01c / E01d on the E00 base) plus R2-C-U10, R2-H-MAM-C, R2-H-TUR-C, R2-C-NED18. **Void:** every merchant recall by save patch (R2-B5a, R2-B4, R2-B5c, R2-H-MAM-B1, R2-H-TUR-B1 and the recall half of R2-B5b / R2-H-MAM-B2): the patched save has no merchant at the node, t1 has it again (cause unknown); the embargo (R2-EMB) and privateer (R2-PRIV) patches are dropped on load; R2-TC added nothing (no territory province). No claim below rests on a recall.

### V4-R05-1 Ships neither propagate nor count for the gate
Claim (R2-SHIPCON): VEN's 2 light ships moved to constantinople (VEN `province_power` 2.8 there): `ship_power` 4.000 and `max_pow` +4.000 at constantinople, no `prev` change in any node. The gate is `province_power / TRADE_PROPAGATE_DIVIDER (5) >= TRADE_PROPAGATE_THRESHOLD (2)` (defines.lua 1205-1206) on province power only. Confidence: confirmed.


## Update 2026-10-09 - project check on the 205 clean saves (calc 0.3.0)

- **Ships propagate through a country modifier.** `prev` = sum over directly downstream nodes of
  fx((province_power + ship_power x ship_power_propagation) / TRADE_PROPAGATE_DIVIDER), counted when that reaches
  TRADE_PROPAGATE_THRESHOLD (the threshold applies to the sum: KUT gulf_of_siam (8.99 + 10 x 0.25) / 5 = 2.298, while
  8.99 / 5 alone is below 2). In the 1618-1789 saves the residual of every failing entry was ship_power / 4 downstream;
  per country the factor is 0.25 or 0, and the 0.25 countries have Maritime ideas with `grand_navy` (4th idea, +0.25;
  colonial nations with all Maritime ideas included). Other sources in 1.37.5: age ability `ab_ship_power_propagation`
  +0.2, reform `power_to_the_smugglers_reform` +0.25, `private_enterprise_subject` +0.1, national ideas and mission
  modifiers. The previous MOR case (S80, +0.525) fits this rule.
- **Which links count.** In a node where some merchant steers, every outgoing link propagates; in a node nobody steers,
  only the links whose stored weight is above 0 (cape_of_good_hope -> ivory_coast with weight 0: no `prev`). Together
  with the ship term: 400,689 of 400,691 entries exact (failures before: 4,872).
