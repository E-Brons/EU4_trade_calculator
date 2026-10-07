# Experiment results (batch 2026-10-06/07)

Saves: `out/<id>/*.eu4`. Every treatment loads `out/E00/base_1444.12.01.eu4` (VEN, observe), applies ONE change on
1444.12.01, runs with `ai_off=[VEN]` and saves on 1445.01.01 (t1, first tick with the change) and 1445.02.01 (t2).
Scripts: `analysis/` (run from this folder with `../../../backend/.venv/bin/python analysis/<script>.py`):
`a1_verify` (dates/player/format), `a2_noise` (run-to-run diffs), `a3_ven_spread` (VEN fields across controls),
`a4_treatments`/`a5_summary` (VEN entry deltas vs control), `a6_checks`/`a7_checks2` (was the change applied;
province/country evidence), `a8_p01_e21`. Numbers below are stored values; deltas in thousandths where noted.

## 1. Output check
67 saves (all jobs except E23; E23 below): date = file-name date, player=VEN, EU4txt in 67/67 (`a1_verify`).

## 2. Noise verdict
- Two runs from the same save are NOT identical: E01a vs E01b differ in 4,859 of 73,073 trade-block fields at t1
  and 8,029 at t2 (68k / 96k raw lines); mostly other countries' `max_demand`, events, AI decisions (`a2_noise`).
- VEN's own trade entries are stable: across the four controls E01a-d (plain reload, patch path, effects path),
  101 of 103 VEN entry fields are identical at t1 and at t2; only `venice.money` / `venice.total` vary
  (7.005-7.092 / 5.307-5.373, about +-0.6 %), plus the derived VEN `power_fraction` at venice by +-0.002 (`a3_ven_spread`).
- **Verdict:** single-run A/B comparisons are valid for VEN power, demand, val, prev, province_power, ship_power,
  add and merchant fields (exact equality in the controls). Income-level fields (money, total, treasury) need
  ratios (money/total) or repeats. Other countries' fields are noisy unless a direct identity is used.
  The reload path (E01c) and the effects path (E01d) add no VEN-specific change.

## 3. Results

| id | change applied? | result (VEN unless stated) | answers |
|---|---|---|---|
| E02 | yes: ruler DIP 4 -> 6 (also +2 DIP points) | no change in any `max_demand` (80 nodes) or other VEN field | R01 row 2: the "+0.005 per ruler DIP point" term is refuted |
| E03 | yes (modifier) | `max_demand` +0.100 in all 80 nodes; `max_pow` unchanged; `val` recomputed | R01 row 1: global_trade_power adds 1:1 to max_demand everywhere |
| E04 | yes | `max_demand` +0.100 only at venice (home node) | R01 rows 1/10: domestic class = home node only (not ragusa/constantinople where VEN owns provinces) |
| E05 | yes | `max_demand` +0.100 in the other 79 nodes, venice unchanged | R01 rows 1/10: foreign class = every node except the home node |
| E06 | yes | venice money/total 1.320 -> 1.420 (t1), 1.270 -> 1.370 (t2); controls 1.3198-1.3200 / 1.2698-1.2700 | R07 rows 4-6: money = total x (1 + trade_efficiency), efficiency additive |
| E07 | yes | venice `ship_power` 4.000 -> 6.000, `max_pow` +2.000 (2 light ships on mission at venice, not alexandria) | R11 rows 1/4: ship power x (1 + global_ship_trade_power), enters max_pow 1:1 |
| E08 | yes | `add` on VEN's steering entries ragusa and wien 0.071 -> 0.083 | R08 row 2: trade_steering scales the link bonus (+0.012 for +25 %; not a plain x1.25 of 0.071) |
| E09 | yes | province 112 trade_power 53.2 -> 60.8 at t1; VEN province_power venice 99.655 -> 114.317, ragusa 24.584 -> 28.098, constantinople 2.768 -> 3.164; `prev` at alexandria/ragusa/wien 19.931 -> 22.863 = 114.317/5 | R13 row 1: province trade power = base x (1 + S + mods), S = 0.75 at Venezia (53.2 = 30.4 x 1.75); R05: prev = home province_power / 5 confirmed |
| E10 | yes: dip_tech 3 -> 4 | no VEN trade field changes | R07 row 6 / R01 row 10: dip tech 4 has no trade effect |
| E11 | yes: adm_tech 3 -> 4 | no changes | R07 row 6: adm tech 4 none |
| E12 | yes: mercantilism 25 -> 35 | no change at t1; at t2 province 112 trade_power 53.2 -> 59.28, VEN province_power x1.1176 (venice), x1.1141 (ragusa), x1.1142 (constantinople) | R13 rows 1/4: mercantilism +10 adds +0.20 to the province multiplier (0.1176 x 1.699 = 0.1998); applied only at the province's next update (not on 1445.01.01) |
| E13 | yes: 3 -> 4 envoys | no trade changes (AI off: the merchant is not placed) | R07 row 7 / R09: merchant capacity is an envoy count only |
| E14 | yes: `modifier={key=exp_trade_power power=10}` at VEN ragusa | ragusa `max_pow` +10.000, `val` +10.360; no `province_power`, no `prev` change upstream | R06 row 1: flat node power enters max_pow 1:1; R05: flat power does not propagate |
| E15 | yes: Piedmont base production 7 -> 10, trade_power 4.08 -> 4.80 | SAV genua province_power 9.716 -> 10.436 (t1) and SAV `prev` 2.087 (= 10.436/5) appears at alexandria, champagne, ragusa, tunis, valencia; control: no prev at 9.716, prev 2.039 at t2 after natural growth to 10.196 | R05 row 1: gate between 9.716 and 10.196 (consistent with >= 10), prev = province_power / 5 |
| E16 | no-op: Venezia already centre of trade level 3 | nothing | void (needs a province below level 3) |
| E17 | yes: marketplace | province 112 trade_power 53.2 -> 68.4 at t1 (+0.50 on base 30.4); VEN province_power venice +15.200, prev upstream +3.040 | R13 row 3: marketplace +50 % local trade power, immediate |
| E18 | yes: Padova autonomy 0.75 -> 25.8 | trade_power 3.137 unchanged at t1, 2.743 at t2 (autonomy 25.7); ratio 0.8744 vs (1 - 0.005 x 25.7)/(1 - 0.005 x 0.625) = 0.8742 | R13 row 1: autonomy factor (1 - 0.005 x autonomy) confirmed; applied at the province's next update |
| E19 | yes: capital and trade_port 112 -> 4729 | has_capital stays at venice (same node); VEN province_power venice -0.200 at t2 | R09 row 6: not decided (capital and trade port both moved, both in the venice node); capital move costs 0.2 province power at venice |
| E20a/b/d | yes: MAN vassal / march / personal union (overlord VEN) | MAN `max_demand` -0.004 in all nodes (PU: +0.001 at t2); no `t_out` / transfer at MAN's home node venice in 2 months | R04 row 4: a subject collecting in its home node shows no transfer there |
| E20c | NO: tributary relation not created (MAN has no overlord) | small MAN max_demand changes only at t2 | void (create_subject tributary_state did not take) |
| E21 | yes: Naxos ceded on 12.01 | 12.03 and 12.15: NAX has no node entries but stays in `top_power` at alexandria (2.046) and constantinople (9.579); gone on 1445.01.01 | R08 row 7 / R09 row 2 / R10 row 7 / R12 C-06: aggregates of a vanished country stay until the next 1st |
| E22 | yes: `add_idea_group trade_ideas VEN` gives trade_ideas = 7 (all ideas) | `max_demand` +0.200 in all nodes; `max_pow` +15.000 at ragusa, venice, wien (VEN's merchant nodes); `add` 0.071 -> 0.083 | console command completes the whole group; R06 row 1: +15 per merchant node; R11: compare with E08 (same add) |
| P01 | yes: VEN ragusa steer idx 1 (venice) -> idx 2 (genua) | ragusa weights [0.254, 0.631, 0.114] -> [0.254, 0.067, 0.678]: exactly 0.564 moved from venice to genua, pest unchanged; link add venice 0.219 -> 0.017, genua 0.032 -> 0.266 | R08 row 1: one steerer's weight share is additive per link and moves with it (0.564 for VEN's val 48.189 of 101.264 summed steerer val) |
| P02 | NO: MNG still steers at hangzhou in t1/t2 (recall did not hold despite ai_off MNG) | weights unchanged [0, 1, 0] | void |
| P03 | yes: VEN ragusa merchant collects instead of steering | ragusa `max_demand` 1.036 -> 0.518 (x0.5), `max_pow` unchanged (merchant term stays), new `total` 0.481 / `money` 0.634; `transfer_home_bonus` 0.2 -> 0.0 and venice `max_demand` 1.213 -> 1.013 | R06 row 2 / R02: away collection halves max_demand, merchant term unchanged; R09: venice max_demand includes transfer_home_bonus, which drops to 0 although wien still steers home |
| P04 | yes: 4th envoy (exp_merchants) steers at constantinople -> ragusa | constantinople `max_pow` +2.000 (merchant term R = 2), `add` 0.071; `transfer_home_bonus` stays 0.2, venice max_demand unchanged | R09 row 10 / R01 row 7: a steerer not steering into the home node adds no home bonus |
| P05 | yes: light-ship fleet venice -> ragusa | ship_power 4.000 moves from venice to ragusa, `max_pow` +-4.000, `light_ship` 2 moves; no `prev` change upstream | R05 rows 4/5, R11 row 3: ship power is local, does not propagate |
| P06 | yes: XAL steers at california (idx 0) | node weights [0, 1, 0, 0] -> [1, 0, 0, 0]; XAL `max_pow` 0.87 -> 2.87 (merchant term 2) | R08 row 4: a sole steerer gets weight 1 on its link next tick; R05 row 2 not answerable (XAL province_power far below 10) |
| E23 | 15 of 16 saves (1444.12.03-12.31; the 1445.01.02 step stopped at 1.1 and could not do the remaining 1 day) | bulk province `trade_power` update on 12.2/12.3, then 0-3 provinces per 2 days | R13 row 7 |

## 4. Follow-ups
- E16 again on a province below centre-of-trade level 3; E20c with a different tributary command (diplomatic action or `create_subject` with the right subject type key).
- P02: find why the recall did not hold (check the patched save before reload; MNG `ai` toggle state).
- R05 row 2: a steerer with province_power >= 10 at california (or another start-zero link).
- E02 repeated with a larger DIP change and a month-long run, to rule out a delayed update of the ruler term.
- Province update timing (E12, E18 at t2 only): E23 every 2nd day will show the update days.
- Repeat runs for income-level questions (money/total noise +-0.6 %).
- R04 transfer fraction by subject type needs a subject with power in a node where it does not collect.
- The home-bonus anomaly in P03 (bonus 0 with one steerer still home): one more case (recall instead of collect).

## E23 - days on which province `trade_power` changes (every 2nd day, one run from the base)

Script: `analysis/a9_e23_recompute_days.py`. 3,925 provinces with `trade_power`.

| pair | provinces whose `trade_power` changed |
|---|---|
| 1444.12.01 -> 12.03 | 1,006 (MNG 103, LIT 37, TUR 34, SHY 33, ...) |
| each 2-day step 12.03 -> 12.31 | 0-3 (single provinces of different owners: 2, 1, 1, 0, 2, 1, 3, 1, 1, 2, 0, 2, 0, 0) |

VEN `transfer_home_bonus` 0.200 on every save (no merchant change; AI off).
Claim: province `trade_power` is updated in bulk once a month shortly after the monthly trade computation; within December
of this game the bulk update lies on 12.02 or 12.03 (a 2-day step cannot separate them); the remaining changes are
isolated (single provinces, event-driven). Together with the Venice series (53 changes 1444.12.1 -> 12.2, 962 changes
1445.1.1 -> 1.2) the bulk day is 12.03 in December and 1.02 in January there: not a fixed day of the month. Open: the
rule for the day (needs saves on the 2nd and the 3rd of several months in one game, e.g. a run from a base on the
30th/31st with 2-day steps).

## Note on E07 (2026-10-07)

E07 measured the +50 % `global_ship_trade_power` on 1444 barques only (barque trade_power 2.0 in `common/units`). Ship power depends on the ship type (unit files: barque 2.0 ... great_frigate 5.0; the player reports higher in-game values for frigates, 4.5, and heavy frigates, 5): per-type values need later-tech saves (R11 request_2).
