# Round 2 - results (analysed offline 2026-10-08)

Scripts: `analysis/r2common.py` (loader), `analysis/r0_placements.py` (merchant placements + `transfer_home_bonus`),
`analysis/r1_compare.py` (job vs control: every field of the tag's node entries that differs, plus country fields).
Run from `round2/analysis/`, e.g. `python3 r1_compare.py t1 R2-PORT`; `python3 r0_placements.py VEN 1:E00:base 2:R2-B5a:t1`.
Controls: round-1 `E01c` (patch path, E00 base), `E01d` (effects path), `R2-C-U10` (U10 base), `R2-C-NED18`,
`R2-H-MAM-C`, `R2-H-TUR-C`. Noise rule of round 1: the nation's own power, demand, `val`, merchant fields are identical
across controls (single run is enough); income only as `money/total`.

## 1. Every output

27 jobs, all `ok`; every t1 / t2 save is dated 1445.1.1 / 1445.2.1 (1618.7.1 / 1618.8.1 for NED), plain text, player =
the job's nation (VEN, MAM, TUR, NED; R2-DIPFRESH writes only a 1444.12.1 base, player VEN).

| job | change happened? | note |
|---|---|---|
| R2-B5a, R2-B4, R2-B5c, R2-H-MAM-B1, R2-H-TUR-B1 (pure recalls) | **VOID as recalls**: `analysis/r3_recall_check.py` recomputes each patch on its base: the patched save has no `has_trader`/`type` at the recalled node, t1 has them again (the merchant is back at the same node, same direction). The game restores the merchant from something `savepatch.recall_merchant` does not change (envoys carry no node; no other reference found); cause unknown. No claim about a recall rests on these jobs | side observation only (patch artefact): the `transfer_home_bonus` value the patch writes stays for two months -> section 2 |
| R2-B5b, R2-H-MAM-B2 (recall + place at home) | recall part **VOID** (steerer back, one merchant entry more than envoys); the **placement holds** (collect at home on t1 and t2), as in round-1 P01/P03 | = "home merchant added, steerers unchanged"; section 3 |
| R2-T05, R2-T10 | yes (MAN -> VEN relation `amount` 0.5 / 1.0) | section 4 |
| R2-TRIB | yes (`dependency` VEN -> MAN `subject_type="tributary_state"`, 1444.12.1) | no transfer (section 4) |
| R2-PORT, R2-CAP | yes (`trade_port` 112 -> 4753; R2-CAP: `capital` and `trade_port` both 4753) | section 5 |
| R2-STEER50/100, R2-IDEA1/2, R2-COT, R2-DEPOT | yes | sections 6-8 |
| R2-SHIPCON | yes (VEN's 2 light ships protect `constantinople`) | section 9 |
| R2-DIPFRESH | yes (GEN ruler DIP 3 -> 5 before the first tick) | section 10 |
| R2-EMB | **void**: no `trade_embargoes` / `trade_embargoed_by` key in any country on t1 (the game drops the patched embargo on load) | VEN, RAG entries unchanged (+-0.002) |
| R2-PRIV | **void**: the renamed `privateer_mission` is gone on t1; VEN's 2 light ships have no mission (ship_power 4 -> none at venice, nowhere else) | real privateer save format still unknown |
| R2-TC | **void**: NED has 22 provinces in 1618, none a territory (`is_territory`), so `add_to_trade_company` added nothing (no `trade_company` block in either save) | |

## 2. `transfer_home_bonus` is a stored country field, added 1:1 to the home node's `max_demand` (patch artefact)

Not a recall result (section 1: the recalls are void). The recall patches also write `transfer_home_bonus` - 0.1 into
the country block, and the merchant came back; this section reads only what the game did with that written value. On t1 and t2 (two monthly
computations) the field is still the patched value and the home entry's `max_demand` is lower by exactly 0.100; nothing
else in the nation's entries changes (`val = fx(max_pow x max_demand)` follows).

| job (home node) | home kind | thb control -> job | home `max_demand` control -> job (t1 = t2) |
|---|---|---|---|
| R2-B5a (venice, VEN, E00 base) | end node | 0.2 -> 0.1 | 1.213 -> 1.113 |
| R2-B4 (venice) | end node | 0.2 -> 0.1 | 1.213 -> 1.113 |
| R2-B5c (venice, U10 base) | end node | 0.3 -> 0.2 | 1.313 -> 1.213 |
| R2-H-MAM-B1 (alexandria, MAM) | 3 outgoing links | 0.2 -> 0.1 | 1.232 -> 1.132 |
| R2-H-TUR-B1 (constantinople, TUR) | 1 outgoing link | 0.1 -> 0.0 | 1.207 -> 1.107 |

So: home `max_demand` = (home value without the bonus) + `transfer_home_bonus`, at end and non-end home nodes alike,
and the game does not recompute the field at a monthly tick when the merchant placements are unchanged (it is set by
merchant actions; inferred from R12 C-05 + these 5 x 2 saves). Income at home falls with it (VEN `total` 5.307 -> 5.173,
MAM 3.230 -> 3.052, TUR 4.306 -> 4.111).

## 3. Merchant at the home node: +0.10 trade efficiency and +2 power, end node and non-end node

| job | home | `max_pow` control -> job | X = money/total - 1 control -> job | `total` | thb |
|---|---|---|---|---|---|
| R2-B5b vs R2-C-U10 (t1 / t2) | venice (end) | 110.681 -> 112.681 | 0.12 -> 0.22 / 0.17 -> 0.27 | 5.655 -> 5.687 | 0.3 = 0.3 |
| R2-H-MAM-B2 vs MAM-C (t1 / t2) | alexandria (non-end) | 110.564 -> 112.564 | 0.07 -> 0.17 / 0.07 -> 0.17 | 3.230 -> 3.241 | 0.2 = 0.2 |

A collecting merchant at home adds `TRADE_MERCHANT_PRESENT = 0.1` (defines.lua line 1201, "bonus on income if trade
present") to X and +2.000 to `max_pow` (the flat merchant power, R06); `transfer_home_bonus` does not change (only
steerers count). The power gain raises the share only where the nation does not already hold the whole retained power
(`total` +0.6 % at venice, +0.3 % at alexandria). The 0.32 vs 0.12 home X of round 1 (E00 vs Venice series) is 0.10 of
this term plus a further 0.10 of unknown cause.

## 4. Transfer fraction = the relation's `amount` (causal); a tributary gives nothing

MAN (`val` 18.843 at venice on t1): with `transfer_trade_power={ amount=0.500 }` MAN's `t_out` is 9.371 at venice,
2.028 at ragusa and wien, 1.017 at alexandria; with `amount=1.000` 18.743 / 4.057 / 4.057 / 2.035 =
`fx(amount x (val - 0.1))` in all 8 entries; the first `t_out` appears on the first 1st after the relation date
(relation 1444.12.1, entries on 1445.1.1). MAN's own `total` at venice 0.738 -> 0.374 (0.5) / none (1.0).
R2-TRIB: the tributary relation exists but MAN has no `t_out` anywhere (t1, t2) - consistent with
`common/subject_types/00_subject_types.txt` (`transfer_trade_power = yes` only for colony, eyalet,
commercial_enterprise, trade_protectorate) and round-1 E20a/b/d (vassal, march, personal union: no transfer).

## 5. Home node = node of the main trade port

R2-PORT (only `trade_port` 112 Venezia -> 4753 Zara; capital stays 112): `has_capital` moves from venice to ragusa;
ragusa `max_demand` 1.036 -> 1.213 (the home value incl. thb 0.2), `max_pow` +5.000 (`TRADE_CAPITAL_POWER = 5.0`,
defines line 1195); venice (VEN's merchant still collects there, now away): `max_demand` 1.213 -> 0.507 (about 0.5 x the
home value without thb, 1.013: the away factor; not exact to the last digit, 0.5 x 1.013 = 0.5065), `max_pow` -10.000 (-5 capital power, -5 unexplained). R2-CAP (`set_capital = 4753`):
`trade_port` follows the capital (both 4753), the same move plus: the ragusa merchant stops steering (home node:
collects; `total` 0.948), `transfer_home_bonus` 0.2 -> 0.0 (an away collector exists, V19).

## 6. Steering strength: 0.05 x (1 + trade_steering)

VEN's `add` on its rank-1 steering entries (ragusa, wien): 0.071 (control) -> 0.083 (+25 %, E08) -> 0.096 (+50 %) ->
0.121 (+100 %): +0.05 per +100 % trade steering = `TRADE_ADDED_VALUE_MODIFER = 0.05` (defines line 1204) x the
modifier; the base 0.071 = 0.05 x 1.42-1.44 (VEN_ideas start `trade_steering = 0.33` plus about 0.1 of another
source). The most common identified strength in the corpus, 0.05, is a country without steering modifiers. Home income
rises with the steered value (VEN `total` 5.353 -> 5.616 -> 5.834).

## 7. Trade ideas

R2-IDEA1 (`trade_ideas` group, 1 idea): `max_demand` +0.200 in every node (`shrewd_commerce_practise`,
`global_trade_power = 0.2`). R2-IDEA2 (the command gave `trade_ideas` 3 and `VEN_ideas` 1): no further change in VEN's
entries (ideas 2-3: `merchants = 1`, `trade_range_modifier`; no trade-block field changes; the +1 merchant is not used
with the AI off).

## 8. Province trade power: centre of trade and trade depot

R2-COT: Verona (108) centre of trade 1 -> 2 (`province_trade_power_value` 5 -> 10, `common/centers_of_trade`): province
`trade_power` 11.354 -> 18.824 (+7.470 = 5 x 1.494: the flat value is multiplied by the province multiplier and the
autonomy factor, R13 V2-R13-1/2); VEN `province_power` at venice +7.470, `prev` +1.494 (= /5) at alexandria, ragusa,
wien. R2-DEPOT: trade depot in Venezia (`province_trade_power_modifier = 1`): 53.200 -> 83.600 (+30.4 = the province's
base 30.4 x 1.0); `province_power` +30.4, upstream `prev` +6.08.

## 9. Ships at a node where the nation has power below the gate

R2-SHIPCON: VEN's 2 light ships (barques, 2.0 each) from venice to constantinople (VEN `province_power` 2.8 there):
`ship_power` 4.000 and `max_pow` +4.000 move with the fleet; no `prev` changes anywhere (ship power does not propagate
and does not count for the gate); VEN home `total` 5.307 -> 5.264 (-0.8 %).

## 10. Ruler DIP at the first tick (cross-game)

R2-DIPFRESH: GEN's ruler DIP 3 -> 5 in a new game before the first tick; on 1444.12.1 GEN's `max_demand` equals E00's
(another new game, DIP 3) in 80 of 80 nodes. The U10 game (Venice series) differs from E00 by +0.1 at 78 GEN nodes
with the same DIP: the cross-game pattern of R01 VS-3 is not caused by the ruler's DIP.

## Still open after round 2 (data)

Pure merchant recalls need a way to stop the game re-sending an idle merchant (or a recall through the interface);
embargo and privateer missions need the game's own save format (a real embargo / privateer save); the trade-company
test needs a nation with territories (a later bookmark, e.g. POR/NED in 1700+ Asia); the unexplained -5 power at the
old home node (R2-PORT) and the second 0.10 of the E00 home X.
