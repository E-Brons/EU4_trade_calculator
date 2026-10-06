# R04 response 1 - Transferred trade power (t_in / t_out / t_from / t_to / potential)

Scope: only the points the 82 fixture saves settle; all numbers come from script runs (`backend/scripts/research/r04_r05_r06_r04a.py` ... `r04f.py`; helper `r04_r05_r06_flat.py`; repo snapshot in /tmp/eu4research/repo). Counts are over all 82 saves (S01-S80 + U01/U02); U01/U02 repeat the dates of S80/S79, so the played-save counts are partly duplicated. "Giver" = entry with `t_out`; "receiver" = entry with `t_in`.

## Q1 - The 0.05 / 0.1 offset

### C-Q1.1 t_out = trunc3(0.5 x val - 0.05), exact for every giver
Claim: a giver sends half of its `val` minus a flat 0.050, truncated to 3 decimals; equivalently `val - 2 x t_out` is 0.100 or 0.101 (never anything else).
Formula: t_out = trunc3(0.5 x (val - 0.1)) = trunc3(0.5 x val) - 0.05.
Applies when: the entry has `t_out` (all `t_to` maps have exactly one key, the overlord).
Source: save corpus, `r04_r05_r06_r04a.py`.
Quote: 2,232 giver entries, 24 giver tags: `val - 2 x t_out` min 0.100, max 0.101 (0.100: 1,118; 0.101: 1,114); S79 mexico C03 `val=668.952 t_out=334.426 t_to={ SPA=334.426 }` (0.5 x 668.952 = 334.476; 334.476 - 0.05 = 334.426). The formula matches 2,232 of 2,232; `trunc3(0.5 x val)` alone matches 0; `round3(0.5 x (val - 0.1))` matches 1,263 (so it is truncation, not rounding).
Confidence: confirmed.
Characterisation of the offset: it is the same flat 0.050 for giver `val` from 1.443 (smallest giver in the corpus) to over 1,000 (log10 buckets 0, 1, 2, 3 all show only 0.100/0.101), it does not depend on the save/date, the tag (24 tags) or whether the giver has `prev` (1,444 givers with `prev > 0`, all fit); it is not a fraction of `val` (not 0.5 x 0.1 proportional). Nothing in the entry holds a 0.05/0.1 field. What happens for `val < 0.1` (no giver has such a value, minimum 1.443) is UNKNOWN. A source or mechanism for the 0.1 is UNKNOWN; what would settle it: a giver with a very small `val` (e.g. a colonial nation with one province) or an intervention pair changing `val` by a known amount.
Caveats: the draft's rows were not reproduced by `t_out = val x f`; the constant gap of 0.050 is systematic, not float truncation.

## Q3 - Which mechanisms create transfers (data part)

### C-Q3.1 The country-level list `transfer_trade_power_to` marks exactly the givers
Claim: a country gives trade power in all nodes where it has power if and only if its country block has `transfer_trade_power_to={ OVERLORD }`; the overlord's block lists the giver in `transfer_trade_power_from`.
Source: `countries` block vs trade entries, `r04_r05_r06_r04a.py` (all 82 saves).
Quote: country-saves with entries: flag and `t_out` in 490; neither in 42,647 (pseudo-tag `---` excluded; with it 42,729); flag without `t_out` in 2 (BEI in S80 and U01, overlord TUR, `transfer_trade_power_to={ TUR }`, 7 entries with `val` but no `t_out`); `t_out` without flag in 0. S80: `transfer_trade_power_from` of SPA = [C00, C02, C03, C06, C09, C12, C14, C16, C20, C21], TUR = [BEI, SND, C22], GBR = [C05, C10, C17], BRZ = [C04, C07, C11], BRI = [C08, C15, C19], SCA = [C18].
In every giver country-save the single receiver (`t_to`) is the country's `overlord` (490 of 490). Givers in the corpus are the colonial nations of SPA/POR/ENG/GBR/FRA/RUS/BRI/DAN/TUR/BRZ/SCA/CAS and SND (a vassal of TUR, S79/S80, `colonial_parent` absent); other vassals and march-like subjects do not give (e.g. S80: 12 non-colonial subjects have no `t_out`, 11 of them without the flag and BEI with it; S14: 107 subjects, 0 givers; S42: 53 non-colonial subjects, 0 givers). A country is never giver and receiver in the same node (0 entries have both `t_in` and `t_out`).
Confidence: confirmed as a description of the corpus (BEI is the only exception: flag present, `t_out` absent; played saves are saved mid-month, so a flag set after the last tick is a possible but untested reading).
Updated 2026-10-05: the BEI case was not re-examined in U03, U04, U05 (no check run there); the `transfers` stage is unchanged on them (section 'Update 2026-10-05').
Not answered from data: whether peace deals, trade companies or leagues create transfers (none visible), the fraction per subject type (every giver uses 0.5 with the Q1 offset; no other fraction occurs).

## Q4 - What part is transferred; does it propagate?

### C-Q4.1 The transferred amount comes from `val` (which contains `prev`), and transfers do not propagate upstream
Claim: (a) `t_out` is a function of the giver's `val = trunc3(max_pow x max_demand)`, so it contains the giver's `prev` and ship/flat power; (b) neither `t_out` nor `t_in` changes anything upstream: the `prev` of a country in an upstream node depends only on its own `province_power` downstream; (c) `t_in` is not inside the receiver's `max_pow`.
Source: `r04_r05_r06_r04b.py`.
Quote: (a) 2,232 of 2,232 givers have `val == trunc3(max_pow x max_demand)` and t_out from that `val`; 1,444 of them have `prev > 0`. (b) Snapshot entries whose downstream node holds a receiver entry (`t_in > 0`, `province_power >= 10`, link carrying flow): 59, and `prev` equals the plain province-power rule (R05) in 59 of 59; entries whose downstream node holds a giver entry: 1,188, 1,188 of 1,188 match, using the giver's full `province_power` (not reduced by `t_out`). (c) Snapshot receivers with `max_pow` (457): `max_pow = province_power + ship_power + prev + 5 x has_capital + modifier powers` in 457 of 457 (e.g. S42 lima SPA `max_pow=0.93 t_in=96.988 val=1.575`).
Confidence: confirmed (snapshots; no exceptions).

## Q5 - `potential`

### C-Q5.1 potential = trunc3((t_out - t_in) / node total), truncation toward zero
Formula: potential = trunc_toward_zero_3((t_out - t_in) / total), where `total` is the node's `total`; positive for givers, negative for receivers.
Source: `r04_r05_r06_r04c.py`.
Quote: 3,584 entries with `potential` in nodes that have `total` (2,232 givers, 1,352 receivers, 0 others): truncation toward zero 3,584 of 3,584; floor 2,232; round-half-up 1,841; the 1,352 negative values are not floor-exact (floor fails on exactly these). Denominator `retain_power` or `collector_power`: 0 matches. `potential == 0` with a transfer: 0 entries; `potential != 0` without a transfer in a node with `total`: 0.
Confidence: confirmed. The draft's "exact" entries are truncations (the project's tables agree).
Separate observation: 23,660 further entries (`potential` only plus `max_demand`, no `t_in`/`t_out`) exist in the node `cape_of_good_hope` of the 1444-era saves, where the node has no `total`: `potential = -0.002` in 23,625 and -0.001 in 35. The formula does not apply there (no `total`); it looks like a placeholder of a node without data. What `potential` is used for in the game: not answered (needs an outside source).

## Q6 - Receiver income share and the POR case

### C-Q6.1 Income share of givers and receivers that collect
Formula: `power_fraction = trunc3((val - t_out + t_in) / retain_power)`; `total` (the country's share) `= trunc3(current x power_fraction)`.
Source: `r04_r05_r06_r04f.py`.
Quote: 42,948 entries with `power_fraction`: givers 526 of 526, collecting receivers 6 of 6 (S80/U01 TUR at comorin_cape and gujarat, S80 BRZ at ivory_coast), other collectors 42,409 of 42,416 (7 pre-existing failures, listed by the project); `val / retain_power` alone fits 0 of 526 givers. Request example C03: S79 mexico C03 `val=668.952 t_out=334.426 power_fraction=0.995 retain_power=336.162`: (668.952 - 334.426) / 336.162 = 0.99513 -> 0.995. `total = trunc3(current x power_fraction)` holds for all 42,948 entries that have it. Receivers that do not collect (SPA/POR/GBR etc.) have no `power_fraction`, so the table cannot test them; the 6 collecting receivers fit the same formula.
Confidence: confirmed for all 526 givers and all 6 collecting receivers; for the other collectors the formula fails in 7 entries, all S64 `genua` (KNI, SPI, GEN, NAP, PAP, TUS, LUC).

### C-Q6.2 The POR / ohio / chesapeake_bay nodes: steering downstream also makes a non-collector "pull"
Claim: a country that neither collects nor steers in a node is counted in `pull_power` (with effective power `val - t_out + t_in`) when it collects or steers in some node downstream. The R03 rule (collect downstream only) fails in exactly two nodes of S79 (and their copies in U02); the extended rule fails in none.
Formula: pulls(node) = steers here, or (does not collect here and (collects or steers in some node downstream)).
Source: `r04_r05_r06_r04e.py` (5,819 nodes with `pull_power`; "collect" = `total` key present, "steer" = `type` key present; effective = `val - t_out + t_in`; tolerance 0.0105 on the node sum).
Quote: S79 `ohio`: `pull_power=440.306`; the R03 rule gives 402.981; the difference 37.325 equals POR's effective power (`val=1.11`, `t_in=36.215`, `t_from={ C04=24.181 C07=12.034 }`, no `has_trader`, no `type`, no `total`). S79 `chesapeake_bay`: `pull_power=646.532`, rule 607.474, difference 39.058 = POR's `t_in=39.058` (entry has no `val`). POR collects only at sevilla (not downstream of either node) but steers at malacca, ganges_delta, comorin_cape, ivory_coast, carribean_trade and north_sea, and north_sea is downstream of both nodes. Among the 1,176 non-collecting, non-steering receiver entries, 40 have no downstream collection: the 4 whose tag steers downstream (POR in S79/U02 at ohio and chesapeake_bay) are counted in `pull_power`, the 36 whose tag does not (S80/U01 BRZ 5+5, S38-S54 SPA, ...) are not counted. With the extended rule: 0 mismatching nodes of 5,819, and the prediction changes in exactly those 4 nodes.
Confidence: inferred (one tag, two nodes, four node copies; the alternative explanations "overlord of a collector" or "has `t_in`" are excluded by the 36 uncounted receivers). What would settle it: another save where a non-collecting country steers only downstream of a node where it holds a merchant-less entry.

## Not answered (needs an outside source)
Q1 mechanism/source for the 0.1; Q2 (file + line of `transfer_trade_power` per subject type; `1.0` for personal unions); Q3 peace-deal / trade-company / league mechanics (the data only show the diplomatic flag, and that subjects without the flag do not give); Q5 what `potential` is used for; Q7 quote replacement.

## Updated UNKNOWN list
- Origin of the flat 0.050 (behaviour for giver `val < 1.4`).
- Why BEI (S80/U01) has the flag but no `t_out`.
- Whether the "steers downstream" extension of the R03 pull rule holds beyond POR (no other case in the corpus).

## Verification (date 2026-10-04)
Independent re-computation in `backend/scripts/research/ver_r04.py`, `ver_r04b.py`, `ver_r04c.py`, `ver_r04d.py` (own loop over the parsed saves, integer thousandths / `Decimal`, no code reused from the author's scripts); the author's `r04_r05_r06_r04a.py` ... `r04f.py` were also re-run and print the numbers quoted above.

Re-run and matching (independent unless marked "author"):
- C-Q1.1: 2,232 givers, 24 tags; `val - 2 x t_out` = 0.100 (1,118) / 0.101 (1,114); `t_out = floor((val_thousandths - 100) / 2)` and `trunc3(0.5 x val) - 0.05` 2,232 of 2,232, `trunc3(0.5 x val)` 0; smallest giver `val` 1.443. `round3(0.5 x (val - 0.1))` 1,263 (author re-run only).
- C-Q3.1: flag and `t_out` in 490 country-saves, flag without `t_out` 2 (BEI, S80 and U01, 7 entries with `val` each), `t_out` without flag 0; `t_to` has one key in 2,232 of 2,232 giver entries, equals `t_out` in 2,232 and is the country's `overlord` in 2,232; 0 entries have both `t_in` and `t_out`. Subject counts S14 107/0, S42 53/0, S80 12 non-colonial without `t_out` (author re-run).
- C-Q4.1: snapshots: entries with a receiver downstream 59 of 59 and with a giver downstream 1,188 of 1,188 match the plain `province_power` rule (gated by the recorded `steer_power` weight); receivers' `max_pow` = `province_power + ship_power + prev + 5 x has_capital + modifier powers` in 457 of 457; `val = trunc3(max_pow x max_demand)` in 2,232 of 2,232 givers. In the played saves (not covered by the claim) the same check gives 68 of 68 with a receiver downstream and 256 of 268 with a giver downstream (the 12 others are not investigated here).
- C-Q5.1: `potential = trunc3-toward-zero((t_out - t_in) / total)` 3,584 of 3,584; the 23,660 stub entries are 35 saves x 676 (S01-S35), all in `cape_of_good_hope`.
- C-Q6.1: `power_fraction` givers 526 of 526, collecting receivers 6 of 6, other collectors 42,409 of 42,416.
- C-Q6.2: `pull_power` over 5,819 nodes: R03 rule mismatches exactly `ohio` and `chesapeake_bay` in S79 and U02 (4 node copies), the extended rule (steer here, or not collecting here and collects/steers downstream) 0 mismatches (tolerance 0.0105).

Corrected:
- Q3: "neither in 42,647" excluded the pseudo-tag `---`; the count including it is 42,729 (clarified in place).
- Q6.1: "Confidence: confirmed (counts above)" hid 7 failures of the formula among other collectors; now stated (all S64 `genua`).

Not verified / observations: the S80 colonial nation POR (overlord BRZ) has no flag and no `t_out` (author re-run); the statement "givers are the colonial nations of ..." is therefore a list of observed givers, not a rule "colonial nation => gives". The 12 unexplained played-save giver-downstream entries above are not analysed.

## Update 2026-10-05 - saves U03, U04, U05

Status: the results below are single runs of `backend/scripts/research/u345_pipe_*.py` (own code; `u345_pipe_stages.py` runs the project's `verify_world`); they have not been independently re-computed, unlike the Verification section above. New data: U03 (in-game date 1691.1.9), U04 (in-game date 1691.11.1, a tick day; its file name says 1691.11.17) and U05 (1693.4.15) are melted Ironman saves of the same Ottoman campaign (player TUR, game 1.37.5, 80 trade nodes) as S79 (1665.4.22) and S80 (1682.4.18); they are not independent samples. Counts refer to these saves unless stated otherwise.

### U-R04-1 The transfers stage on the new saves
Project stage `transfers` (`t_out = trunc3(0.5 x val - 0.05)`, `t_in`, `potential = trunc3-toward-zero((t_out - t_in) / total)`): 0 failures in 436 (U03), 436 (U04), 432 (U05) checks (S79 0/358, S80 0/414; 78 start saves 0/5,624). Confirmed for these saves (same campaign, not independent of S79/S80).

### U-R04-2 pull_power and retain_power near transfers
Project stages: `pull_power` 0/77 (U03), 0/77 (U04), 1/77 (U05); `retain_power` 0/80, 0/80, 1/80. The two U05 failures are not transfer effects: `pull_power` of `ethiopia` (recorded 247.475, calc 244.865) and `retain_power` of `gulf_of_aden` (recorded 795.345, calc 787.827) differ by exactly the `top_power` value of AFA (2.610 and 7.518), a country that lost its last province and has no entry there any more (see the R12 update, U-R12-2; inferred). The two S79 `pull_power` failures (the POR nodes `ohio`, `chesapeake_bay`) have no counterpart in U03 and U04 (0/77 failures); the "steers downstream" extension of the R03 rule was therefore not tested further (no new case).

### U-R04-3 Still open
The BEI exception (flag without `t_out`) was not examined in the new saves: UNKNOWN as before. Origin of the flat 0.05, subject types with a fraction other than 0.5, and the mechanisms other than the diplomatic flag: no new data.

### Verification 2026-10-05 (second pass)

Method: new code `backend/scripts/research/ver2_c_stages.py` (project `verify_world` over all 85 manifest saves; U01/U02 are copies of S80/S79, so corpus-wide counts contain two duplicates), `ver2_c_identities.py` (own re-computation of the identities, prev rule, gate and ship-term counts from the parsed trade trees, exact decimal truncation), `ver2_c_gates.py`, `ver2_c_worst.py`.

Matched: `transfers` 0 failures in 436 (U03), 436 (U04), 432 (U05), S79 0/358, S80 0/414, 78 start saves 0/5,624; over all 85 saves 0 failures in 8,472 checks. `pull_power` 0/77, 0/77, 1/77 (U05 `ethiopia`, calc 244.865, recorded 247.475) and `retain_power` 0/80, 0/80, 1/80 (U05 `gulf_of_aden`, calc 787.827, recorded 795.345); over all 85 saves `retain_power` 1 failure in 6,800 checks and `pull_power` 5 failures in 6,050 (S79 and its copy U02 at `chesapeake_bay` 607.474 vs 646.532 and `ohio` 402.981 vs 440.306, U05 1), i.e. 3 distinct nodes. The AFA difference equals AFA's `top_power` value (2.61 and 7.518 in the node lists).
Corrected: nothing in the numbers. Label: the transfers result is `confirmed` for the saves listed (85 saves, 2 duplicates, one campaign for the 7 played saves).
Unverifiable: BEI exception (not examined in U03-U05), origin of the flat 0.05, subject types with another fraction.

## Update 2026-10-05 - Venice series U07-U30 (first non-colonial transfers)

Data: Venice series U07-U30 (see the R12 Update of the same date for the series description); scripts `backend/scripts/research/venice_a_r04.py` and `venice_a_r04b.py` (whole corpus S01-S80, U01-U06 plus the series).

### V-R04-1 Plain vassals transfer their whole power: t_out = val - 0.1
Claim: two vassals give with a factor 1.0 instead of 0.5: `t_out = val - 0.100` exactly (the known rule `t_out = f x (val - 0.1)` with f = 0.5 for colonial nations and trade protectorates gives `0.5 x val - 0.05`).
Source: `venice_a_r04.py`, `venice_a_r04b.py` (ratio `t_out / (val - 0.1)` per giver-save; subject type from the `dependency={ first second subject_type }` block of the same save).
Quote: AVR (vassal of GAZ, `dependency` start 1435.1.1, `subject_type="vassal"`): `persia` val 1.986, `t_out` 1.886, `t_to` {GAZ: 1.886}; `astrakhan` val 9.487, `t_out` 9.387; the receiver GAZ has `t_in` 1.886 / 9.387 and `t_from` {AVR: ...} (U15-U24, i.e. 1445.1.1 to 2.28; country flag `transfer_trade_power_to=[GAZ]` until 2.17, then absent at 2.28 while the `t_out` entries are still there until the next 1st). LDU (vassal of MRA): `kongo` val 1.986, `t_out` 1.886; `zambezi` val 10.852, `t_out` 10.752 (U27, 1445.4.1). Over the whole corpus plus the series: colony givers ratio 0.5 in 534 giver-saves; trade_protectorate givers (SND, BEI) 0.5 in 10; vassal givers 1.0 in 12 (AVR 11, LDU 1); no other ratio occurs.
Confidence: confirmed as an association with the subject type (two givers, both plain vassals); the cause (subject type `vassal` versus a diplomatic setting such as a transfer action) is UNKNOWN.

### V-R04-2 The country flag moves at once, the entries follow the 1st
AVR: flag `transfer_trade_power_to=[GAZ]` first seen 1444.12.31 (U13), present through 1445.2.17 (U23), absent from 1445.2.28 (U24); the `t_out` / `t_in` entries first appear on 1445.1.1 (U14, the next 1st after the flag) and are still present on 1445.2.28 (U24, flag already gone), absent on 1445.3.1 (U25). LDU: flag seen 1445.3.31 (U26), `t_out` entries only on 1445.4.1 (U27); on 1445.5.1 (U28) the flag is still there but there are no `t_out` entries (unexplained; same type of case as BEI in S80), flag absent on 1445.6.1 (U29). Consistent with R12: entries change only on a 1st, country fields at once.

### Not addressed
Venice has no subject of its own; the rows of request_2 about BEI and small `val` are unchanged.

### Verification 2026-10-05 (second pass)
The vassal ratio was counted twice: by `venice_a_r04.py` (parsed entries, class `val-0.1`) and by `venice_a_r04b.py` (ratio and `dependency` block from the raw text); the corpus-only rerun lists the same 12 vassal giver-saves and 534 + 10 for the others.
