# R01 response 1 - What determines max_demand (data-based points only)

Scripts (`backend/scripts/research/`): `r01_classes2.py`, `r01_top_vs_home.py`, `r01_md_classes.py`, `r01_embargo.py`, `r01_embargo2.py`, `r01_embargo4.py`, `r01_tur_verdicts.py`, `r01_rowtable.py`, `r01_home_bonus.py`, `r01_home_bonus2.py`, `r01_cap_values.py`, `r01_cap_reg.py`. Corpus: 82 saves, 3,420,320 (country, node) `max_demand` values (every country has one at every node). Definitions: *home node* = node of `country.trade_port` (provinces block `trade=`); *top* = `node.top_provinces[0] == tag`; *own power* = `max_pow - prev`; *away* = entry with `total` and no `has_capital`.

## Q1 - The rows below the cap

### C-01 Non-embargoed countries have one country-wide multiplier
Claim: for a country without `trade_embargoed_by`, outside the home node, top-province nodes and away-collecting entries, `max_demand` is the same at every node.
Source: `r01_md_classes.py`.
Quote: 42,636 (save, country) groups; 42,632 (99.99%) have exactly one distinct value over all nodes that are not home, not top-province and not away-collecting; 4 have 6-7 values (SUN and DLI in S80/U01, values 1.387-1.492 and 1.817-1.955). (Corrected in verification: the author's script `r01_md_classes.py` did not exclude top-province nodes, which gave 41,774 single-valued / 858 with 2 values; the 858 are the countries whose top-province nodes carry the domestic value, see C-03. Independent recomputation: `ver_r01_const.py`.)
Confidence: confirmed. This excludes a node-dependent modifier (trade company region, goods, node size) as the cause of the lower rows for ordinary countries.

### C-02 The lower-than-cap rows are embargo (presence test)
Claim: an embargoed country's `max_demand` falls below its class cap only in nodes where an embargoer has own power.
Source: `r01_embargo4.py` (9,324 embargoed-country/node rows with a clean cap).
Quote: no embargoer with own power -> not reduced 7,968, reduced 2; some embargoer with own power -> reduced 1,206, not reduced 148 (120 of them embargoer share < 1%).
Confidence: confirmed for presence (independent recomputation `ver_r01_embargo.py`: 7,968 / 2 identical; the split of the rows with embargoer power depends on the threshold for "reduced": the author's is a reduction of more than 0.3% of the cap (1,206 reduced / 148 not); with an absolute 0.0015 threshold it is 1,284 / 70). Province+ship alone is the wrong embargoer measure: 320 reduced nodes had embargoers without province/ship power (merchant flat power counts, propagated `prev` does not).

### Per-row table, TUR S79 (class cap: domestic 1.895, foreign 2.110, from rows with no embargoer own power; pred = 0.5 * sum over embargoers of own_e / (sum of own over ALL entries of the node + 5*NH), where own = `max_pow - prev` taken raw (not clipped at 0) and NH = number of entries of the node with `has_capital`; observed reduction = 1 - md / class cap, away rows doubled first; "reproduced" = within 1 pp. The NH and sum definitions were missing in the first version; independent recomputation `ver_r01_tur.py` reproduces every row below)
| row | md | observed reduction % | pred % | verdict |
|---|---|---|---|---|
| gulf_of_siam | 1.830 | 13.27 | 10.59 | not reproduced (BNG 78.8) |
| canton | 1.718 | 18.58 | 14.70 | not reproduced (BNG 113.2) |
| malacca | 2.030 | 3.79 | 3.44 | reproduced (BNG 2.0, DEC 43.0) |
| deccan | 1.254 | 40.57 | 35.97 | not reproduced (DEC 218.0, share 0.72) |
| comorin_cape | 1.530 | 27.49 | 24.08 | not reproduced (DEC 302.2) |
| gujarat | 1.503 | 28.77 | 25.00 | not reproduced (DEC 187.0) |
| basra (dom) | 1.882 | 0.69 | 0.59 | reproduced (RUS 2.5) |
| samarkand | 1.651 | 21.75 | 18.17 | not reproduced (RUS 63.3) |
| persia | 1.583 | 24.98 | 20.85 | not reproduced (RUS 138.9) |
| aleppo (dom) | 1.869 | 1.37 | 1.35 | reproduced (HUN 7.0) |
| alexandria (dom) | 1.875 | 1.06 | 1.02 | reproduced (HUN 7.0) |
| astrakhan | 1.098 | 47.96 | 50.00 | not reproduced (RUS 140.9, share ~1.0) |
| crimea | 1.648 | 21.90 | 18.86 | not reproduced (RUS 98.8) |
| ragusa (dom/away, cap 0.9475) | 0.761 | 19.68 | 17.66 | not reproduced (HUN 13.8, HAB 89.8) |
| pest | 1.452 | 31.18 | 27.76 | not reproduced (HUN 44.6, HAB 96.6) |
| wien | 1.800 | 14.69 | 12.78 | not reproduced (HAB 128.5) |
| venice (dom/away) | 0.920 | 2.90 | 2.69 | reproduced (HAB 31.5) |
All other 15 TUR rows: md = class cap exactly and no embargoer has own power (philippines, polynesia_node, australia, hangzhou, the_moluccas, lahore, ethiopia, gulf_of_aden, hormuz, zanzibar, constantinople, tunis, champagne, valencia, genua). The draft's 40.6% (deccan) and 48.0% (astrakhan) are consistent with the embargo structure, because DEC holds 0.72 and RUS ~1.0 of the node's own power; the observed value is 1.13x the prediction for deccan (0.96x for astrakhan). Observed/predicted per embargoer: BNG 1.25-1.26, DEC 1.13-1.15, RUS 1.16-1.20 (astrakhan 0.96), suggesting a per-embargoer factor (`embargo_efficiency`, not in the save). Exact formula: UNKNOWN (see R10 C-06).
Non-embargo explanations excluded by data: a node-dependent modifier (C-01: constant in 42,632 of 42,636 groups), trade_company_region (yes at nearly all), the domestic class (classes are applied: see Q2), 5 rows with no embargoer power at all are exactly at cap.

## Q2 - Domestic vs foreign

### C-03 Domestic = home node OR top_provinces[0] == tag
Claim: a node where the country has the highest provincial power (`top_provinces[0]`) has the same multiplier as its home node; foreign nodes have another one.
Source: `r01_top_vs_home.py`, `r01_classes2.py` (non-embargoed countries with home entry, a top node and a foreign node).
Quote: top-node md == home-node md in 839 cases (96% of 871 in the author's run; independent run `ver_r01_top.py`: 839 of 873), == both (home = foreign) in 18, differs from both in 14 (independent run: 16 = C05, C08, C10 and BNG in each of S79, S80, U01, U02; these are exactly the home-bonus cases of C-06). Within each class the value is constant in all but 8 (save, country, class) groups.
Confidence: confirmed for the rule "home or top"; the alternative "dominant total power" was not tested. **Updated 2026-10-05:** the sign of domestic minus foreign also flips inside one campaign (TUR, see section Update, U-2).
TUR S79 rows classified by the rule (`top_provinces[0]`): dom = hormuz, constantinople, basra, aleppo, alexandria (and the away rows ragusa, venice); foreign = everything else including crimea (top RUS) and the_moluccas (top SUN, TUR 97.455 is not top) and gulf_of_aden (top YEM). With these classes every row is <= its class cap, and the draft's classification of crimea as domestic is contradicted (crimea 1.648 is a 21.9% embargo reduction of the foreign cap 2.110, RUS own power 98.8). the_moluccas: rule predicts foreign; md 2.110 = foreign cap: consistent.
GEN S79: classes from the same rule: genua dom (home), all others foreign; foreign cap 1.907 (ethiopia, gulf_of_aden, aleppo, crimea, tunis, ragusa); genua 1.241 (embargoers SWI 50.7, PAP 78.9, LAN 131.1 own power: embargoed, so 1.241 is not a clean domestic cap: GEN has no clean domestic row).
### C-04 Domestic cap below foreign cap is common, not a TUR/GEN oddity

Updated 2026-10-05: save U06 (1696.3.25) shows the two classes of one country moving in opposite directions between two saves (domestic -0.8%, foreign +2.7%); see 'Update 2026-10-05 - save U06' at the end.
Quote (non-embargoed countries, home vs foreign value): home lower 20,212, equal 20,586, higher 1,834 (ratio min 0.528, median 1.0, max 4.253). Independent run `ver_r01_homeforeign.py` (equal = within 0.0005): 20,233 / 20,569 / 1,834 over 42,636 groups; min/median/max identical. (The first version's three numbers sum to 42,632, the four multi-valued groups being excluded.) The explanation of why abroad can be larger is a modifier question (UNKNOWN from data). Constantinople and hormuz both 1.895 with no embargoer power there (consistent with no embargo at those two). **Updated 2026-10-05:** a direct within-country case now exists: TUR's domestic value is above its foreign value in U03 and U04 and below it in U05 (section Update, U-2).

## Q3 - GEN rows, baseline, home bonus

GEN S79 (cap foreign 1.907; `r01_tur_verdicts.py S79 GEN`): alexandria 1.835 (3.78% observed vs 3.21% pred, PAP 22.0) reproduced; wien 1.853 (2.83 vs 2.39, SWI 2.0 + PAP 22.0) reproduced; saxony 1.853 (2.83 vs 2.41) reproduced; rheinland 1.845 (3.25 vs 2.60, SWI 16.6 + PAP 22.0) reproduced; champagne (away) 0.887 (6.97 vs 6.28) reproduced; valencia 1.759 (7.76 vs 6.33, PAP 20.1) off by 1.4 pp; venice (away) 0.858 (10.02 observed; see R02 C-02) off by 1.6 pp. So saxony and rheinland (steering, not collecting) are near the cap only because of embargo, with no 0.5 factor (steering is not penalised: R02 C-03).

### C-05 Values below 1.0 and the baseline
Quote (foreign multiplier per country-save, 42,632 single-valued): most common 1.009 (13,786), 1.036, 0.993, 1.007, 1.031, 1.339, 1.026, 1.012 (the 8 most common = 59.7%); min 0.281 (ZUN S42), max 2.166; below 1.0: 3,815 country-saves (207 tags); exactly 1.000: one (S28 ETH; the pirate stub PIR, 82 saves, is 1.0 everywhere and is not a country). No single saved scalar explains it: correlation of the multiplier with prestige -0.09, power projection 0.17, mercantilism 0.09, government rank 0.08 (R2 <= 0.03; independent run `ver_r01_dist.py`; the first version gave -0.07 and 0.10 for prestige and rank). So the baseline for a country with no modifiers and the modifiers that make it negative: UNKNOWN from the data.
Confidence: confirmed (distribution), UNKNOWN (cause).

### C-06 Home-node bonus is visible inside `max_demand`: +0.1 per steering merchant, additive, in the played saves
Claim: at the home node, `max_demand` = domestic value + 0.1 * (number of steering merchants), when no merchant of the country collects away.
Source: `r01_home_bonus2.py`.
Quote: in S79, S80, U01, U02 every non-embargoed country that has a home entry and a top node, >=1 steering merchant (`type` + `has_trader`) and nobody collecting away shows home - top = exactly 0.1 x steering merchants: BNG 0.3/0.4 (3/4 merchants), C05 0.8 (8), C08 0.3 (3), C10 0.6 (6), 16 of 16; countries with a merchant collecting away: home == top in 12 of 12 (TUR 1.895 = hormuz 1.895). Additive (the difference does not scale with the base: C05 2.29 vs 1.49, BNG 1.514 vs 1.214).
Counter-evidence: in the 78 snapshot saves (`kind` start) 831 countries with >=1 steering merchant and nobody collecting away show home == top (no bonus), 14 with no steering merchant equal. So the bonus is present only in the ticked/played saves; a start snapshot stores the multiplier without it. Only 4 country tags in 2 saves (S79 = U02 and S80 = U01 are identical copies; whether S79 and S80 are independent games is not established by the data: the same tags BNG, C05, C08, C10 appear in both, so they are probably one campaign) carry the evidence. Independent run `ver_r01_homebonus.py` reproduces 16 of 16, 12 of 12 and 831 start snapshots without bonus. The "14 with no steering merchant equal" was not re-checked.
Confidence: inferred (perfect fit but narrow sample). The define value (0.1) and wording need an outside source. **Updated 2026-10-05:** BNG shows the same 0.400 (4 merchants) in U03, U04 (a tick-day played save) and U05, and 12 of 12 country-saves with a merchant collecting away show 0.000; still one country in one campaign (section Update, U-1).

## Q4 - Cap composition
Data-only partial answer: the foreign multiplier is a per-country scalar (C-01) with 749 distinct values and the clustering above; no saved scalar explains it (C-05). The modifier sums (idea, policy, government) need sourced values: not answered.

## Not answered (needs an outside source)
Q1 last bullet quotes; Q2 sourced explanation why abroad is larger; Q3 define `TRADE_POWER_HOME_BONUS`; Q4 (a)-(c) modifier names/values, "1 + sum vs product" quote; Q5 all source/quote repairs (C-03..C-11).

## Still UNKNOWN and what settles it
1. Exact embargo magnitude: per-embargoer `embargo_efficiency`, caravan power (not in save) or an embargo on/off pair.
2. Composition of the cap: pairs changing one idea/policy and reading the foreign multiplier at an unembargoed node.
3. Home bonus in start snapshots and beyond 4 tags: another played save with several steering merchants. (Updated 2026-10-05: U03-U05 add BNG only; see section Update.)

## Verification (date 2026-10-04)
Independent recomputations (new scripts `ver_r01_const.py`, `ver_r01_embargo.py`, `ver_r01_top.py`, `ver_r01_homeforeign.py`, `ver_r01_dist.py`, `ver_r01_homebonus.py`, `ver_r01_tur.py`, written without reusing the author's classification code) plus re-runs of `r01_md_classes.py`, `r01_top_vs_home.py`, `r01_embargo4.py`.
- Re-run and matching: corpus size 3,420,320 (C-01 header); embargo presence test 7,968 not reduced / 2 reduced without embargoer power (C-02); all TUR S79 observed reductions and predictions of the per-row table (after the NH / sum definitions were added) and the GEN S79 rows (alexandria 3.78/3.21, wien 2.83/2.39, saxony 2.83/2.41, rheinland 3.25/2.60, champagne 6.97/6.28, valencia 7.76/6.33, venice 10.02/8.41); observed/predicted ratios per embargoer (BNG 1.25-1.26, DEC 1.13-1.14, RUS 1.16-1.20, astrakhan 0.96); top == home 839 and top == both 18 (C-03); home higher 1,834 and ratio min/median/max (C-04); 749 distinct foreign values, top-8 share 59.7 %, min 0.281 ZUN S42, max 2.166, 3,815 country-saves below 1.0 in 207 tags (C-05); home bonus 16 of 16, 12 of 12, 831 start snapshots (C-06, sign: home is HIGHER than top by 0.1 x steering merchants).
- Corrected: C-01 single-valued groups 41,774 of 42,636 (98.0 %) -> 42,632 of 42,636 (99.99 %), the earlier script had not excluded top-province nodes; C-03 differs-from-both 14 of 871 -> 16 of 873 (the home-bonus cases); C-04 home lower / equal 20,212 / 20,586 -> 20,233 / 20,569 (tolerance); C-05 "exactly 1.000: none" -> one (S28 ETH), prestige correlation -0.07 -> -0.09 and rank 0.10 -> 0.08; C-06 "2 independent games" -> 2 saves (independence not established); per-row table: NH and sum-of-own definitions added; C-02: dependence of 1,206 / 148 on the "reduced" threshold stated.
- Not verified: "within each class the value is constant in all but 8 groups" (C-03); "14 with no steering merchant equal" (C-06); the correlation sample for power projection (n = 33,367 in the independent run); the regression `r01_cap_reg.py` / `r01_cap_values.py` numbers were not re-run; all Q4 / Q5 content is a source question.

## Update 2026-10-05 - saves U03, U04, U05

Status: the results below come from one run each of the scripts `backend/scripts/research/u345_home_*.py` (and `u345_ships_*.py` where stated). Unlike the Verification section above they have not been re-computed by an independent verifier. Labels: `confirmed` = whole set with exceptions listed, `inferred` = otherwise.

New data: U03 (1691.1.9), U04 (in-game date 1691.11.1, a tick day; its file name says 11.17) and U05 (1693.4.15) are melted Ironman saves of the same Ottoman campaign as S79 (1665.4.22) and S80 (1682.4.18). They are not independent of S79/S80 or of each other.

### U-1 Home-node bonus (updates C-06)
- BNG (4 steering merchants, nobody collecting away): home - top = 0.400 = 0.1 x 4 in U03, U04 (the tick-day save) and U05; earlier evidence S79/S80 (3 / 4 merchants). BNG has no embargoer in U03 but has some in U04 and U05, and the difference is still exact.
- Countries with a merchant collecting away: home - top = 0.000 in U03, U04 and U05 for BRZ (k 5 merchants), C02 (k 6), SPA (k 11) and TUR (k 4 / 4 / 3): 12 of 12 country-saves. TUR never has "steering merchants and nobody collecting away" in these saves, so TUR cannot test the bonus.
- Embargoed countries (GBR with k 9: 0.865-0.876 against 0.9; MNG, RUS, KON) differ because their comparison nodes are embargo-reduced: not usable.
- The bonus is present in a tick-day played save (U04), so it is not a mid-month artefact. It is still only one country (BNG) in one campaign [corrected in the second-pass verification below: four tags]; the 831 start-snapshot countries without it are unchanged. Confidence stays `inferred`.

### U-2 Domestic versus foreign inside one campaign (updates C-03, C-04)
- TUR domestic class (top-province nodes hormuz, basra, alexandria [alexandria corrected below: 2.190 / 2.190 / 2.188]): 2.216 (U03), 2.216 (U04), 2.214 (U05). Foreign class (crimea, gulf_of_aden; no embargoer of TUR has own power at either node in U03-U05): 1.932 (U03), 1.925 (U04); crimea 2.289 in U05 (gulf_of_aden is collecting away in U05, 1.145, half of its class value). In S79 the order was the reverse (domestic 1.895, foreign 2.110).
- So the sign of domestic minus foreign changes inside one campaign (S79 foreign higher; U03, U04 domestic higher; U05 foreign higher) without any embargo at those nodes. It is not a structural property of a country (confirms C-04 with a within-country case). Confidence: inferred (one country).
- The foreign scalar of TUR jumps by +19% between U04 and U05 (crimea 1.925 -> 2.289) while TUR's ideas, government reforms, technology levels, mercantilism (30) and estate loyalty tiers are unchanged; its modifier list changed in that interval (`trade_success` expired, `discontent_sowed` and `dip_boost` added). Whether these modifiers carry a trade-power effect is UNKNOWN (their definitions are not in the save). Cap composition (Q4) stays UNKNOWN.

### Verification 2026-10-05 (second pass)

Independent code (new, not reusing the author's logic): `backend/scripts/research/ver2_b_lib.py`, `ver2_b_tur.py`, `ver2_b_bonus.py`, `ver2_b_resid.py`, `ver2_b_x.py`, `ver2_b_switch.py`, `ver2_b_corpus.py`; corpus of 85 saves (S01-S80, U01-U05; U01/U02 copy S80/S79). Each Update claim was re-run and recomputed. Labels follow the rule confirmed = whole set with exceptions listed, else inferred.

Matched (re-run and independently recomputed):
- TUR's actions per node in S79, S80, U03, U04, U05 (home constantinople, trade_port 151, 8 merchants in every save; first merchant at home in U05; gulf_of_aden steering in U03/U04 and collecting away in U05).
- TUR `max_demand` at gulf_of_aden 1.932 / 1.925 / 1.145 and at crimea 1.932 / 1.925 / 2.289 (ratio 1.0000 / 1.0000 / 0.5002; crimea +18.9% U04 -> U05); no embargoer of TUR has own power (`max_pow - prev`) at either node in U03-U05.
- TUR ideas, government reforms, technology levels, mercantilism (30) and the number of estates with loyalty >= 60 (2) unchanged U04 -> U05; modifiers: `trade_success` removed, `discontent_sowed` and `dip_boost` added.
- BNG home - top = 0.400 in U03, U04 and U05 (k = 4); BRZ, C02, SPA, TUR 0.000 in U03-U05 (12 of 12); GBR difference at the top node bordeaux 0.865 / 0.874 / 0.876 (GBR's three top nodes north_sea, bordeaux, champagne give 0.842-1.238 in U03 because of embargo, so GBR is not usable).
- 831 of 831 start-snapshot country-saves with >= 1 steering merchant and nobody collecting away show home = top (no bonus); 14 of 14 without a steering merchant also equal (the second count was "not re-checked" in C-06 and is now checked).
- Earlier headline claims on all 85 saves: `max_demand` single-valued over the non-home, non-top, non-away nodes of non-embargoed country-saves: 42,632 of 42,636 for the 82 earlier saves (identical to C-01; the 4 multi-valued are SUN and DLI in S80/U01) and 323 of 323 in U03-U05; `has_capital` entry at the node of `trade_port` (static province-to-node map of `data/tradenodes.json`): 42,754 of 42,754 for the 82 earlier saves and 411 of 411 in U03-U05, no difference.

Corrected:
- U-1 "still only one country (BNG)" -> four tags fit, as in C-06: in U03-U05 BNG (k = 4, 0.400; U04/U05 embargo-touched but still 0.400), C05 (k = 8, 0.800), C08 (k = 3, 0.300), C10 (k = 7, 0.700; it had k = 6 and 0.600 in S79/S80, so the difference followed the merchant count) in all three saves: 26 of 26 played-save country-saves with >= 1 steering merchant, nobody collecting away and no embargoer power at the home or top nodes (S79, S80, U01-U05). Still one campaign, so `inferred` stays.
- U-1 "12 of 12" is a subset. With the own-power embargo filter and the away-collecting node excluded from the top nodes, the away collectors with home - top = 0.000 are BRZ, C02, C03, C06, SON in U03-U05 (15 of 15; 29 of 29 in all played saves); SPA, TUR and HAB (embargo-touched by that filter) are also 0.000 (9 of 9).
- U-2 "domestic class (hormuz, basra, alexandria) 2.216 / 2.216 / 2.214": alexandria is 2.190 / 2.190 / 2.188 (HUN has own power 7.0 there). The embargo-clean domestic nodes of TUR are hormuz, basra and philippines (3 nodes, 2.216 / 2.216 / 2.214) besides the collecting home node.
- U-2 order of the sign flip: S80 is domestic higher too (2.039 vs 1.596, both embargo-clean), so the sequence is S79 foreign higher, S80 domestic, U03 domestic, U04 domestic, U05 foreign higher.
- Addition: TUR's foreign value is one scalar shared by all embargo-clean foreign nodes of a save (42 nodes 2.110 in S79, 44 nodes 1.596 in S80, 37 nodes 1.932 in U03, 37 nodes 1.925 in U04, 36 nodes 2.289 in U05), so crimea is representative and the +19% is a jump of the whole foreign scalar, not a node effect.

Unverifiable here: the cause of the +19% jump (effects of `trade_success`, `discontent_sowed`, `dip_boost` are not in the save); the definition of the `trade_embargoed_by` lists of the embargoed country-saves is as in the save.

## Update 2026-10-05 - save U06

Status: single runs of `backend/scripts/research/u06_md.py`, `u06_embargo.py`, `u06_scalar.py`, `u06_tur_nodes.py` plus one independent recomputation of the TUR `max_demand` values through `app.trade.extract.extract_world` (`u06_indep.py`), which matched. Labels: `confirmed` = whole set with exceptions listed, `inferred` otherwise.

New data: U06 (TUR, in-game 1696.3.25; next save after U05 1693.4.15; same campaign, not independent). Its changes in country state: adm and dip technology 22 -> 23, parliament issue, 9th merchant, more ships (details in R07 response, 'Update 2026-10-05 - save U06', U-3).

### U-3 TUR `max_demand` U05 -> U06 (updates C-03, C-04; question: does the tech step raise the scalar?)
| Node | Class in U06 | U05 | U06 | Ratio |
|---|---|---|---|---|
| constantinople (home), hormuz, basra | domestic, no embargoer with own power | 2.214 | 2.196 | 0.9919 |
| aleppo, alexandria | embargoer HUN (own power 7.0) in both saves | 2.184 / 2.188 | 2.170 / 2.175 | 0.9936 / 0.9941 |
| malacca | embargoers SPA, DEC, C00, C02 in both saves | 2.139 | 2.119 | 0.9906 |
| crimea | foreign, no embargoer with own power | 2.289 | 2.351 | 1.0271 |
| genua | foreign, embargoer SPA (own power 104.9 -> 105.3) | 2.125 | 2.180 | 1.0259 |
| philippines | domestic in U05 (2.214); embargoer C12 has own power 17.0 in U06 and none in U05 | 2.214 | 2.078 | 0.9386 |
| ragusa | | 2.150 | 2.139 | 0.9949 |
- Finding 1 (confirmed for these nodes): the two embargo-free domestic nodes hormuz, basra and the home node moved together by -0.018 (0.9919); the embargo-free foreign node crimea moved by +0.062 (1.0271). So the technology step 22 -> 23 did not raise the per-country scalar: the domestic class fell and the foreign class rose. It is not one multiplier (inferred: six TUR saves; one campaign).
- Finding 2 (consistent with the embargo presence test of C-02 / V6): `philippines` dropped from the domestic value (2.214) to 2.078 in the same save in which embargoer C12 first has own power there (17.0; none in U05). The size of the drop (-6.1%) is not derived here (embargo magnitude stays UNKNOWN, Q4 of request_2).
- Finding 3: the 9th merchant collects away at `venice`: U05 (passive, no merchant action) 2.203, U06 (collecting away) 1.094, ratio 0.4966; another entering-away case for the 0.5 away factor (R02); TUR's `the_moluccas`, `comorin_cape`, `gujarat`, `gulf_of_aden` stay collecting away.
- Across all countries the U05 -> U06 ratio of `max_demand` per (country, node) has median 1.0000 but p10 0.9758 and p90 1.0553 (10,720 pairs; only 11% within 0.15% of 1), and per-country median ratios differ (TUR 1.0271 over all 80 nodes): the per-country scalar changes between any two saves for most countries; TUR's change is not special (the comparison mixes classes and embargo effects, so it is a description, not a test).
- Country scalars checked against the TUR domestic value over the six campaign saves (S79 1.895, S80 2.039, U03 2.216, U04 2.216, U05 2.214, U06 2.196; `u06_scalar.py`): prestige (83.1, 49.0, 65.9, 65.8, 68.7, 72.5), power projection (37, 43, 43, 43, 43, 43), mercantilism (28, 30, 30, 30, 30, 30), government rank 3, absolutism (12.9, 9.7, 7.6, 3.8, 3.0, absent), legitimacy, army and navy tradition, inflation (0.271, 0.786, 1.486, 1.486, 1.486, 0.001): none tracks the sequence (prestige rose +3.8 while the scalar fell 0.018). The composition of the scalar stays UNKNOWN.

### What settles it (U06 adds)
- Which modifiers lowered TUR's domestic-class scalar by 0.018 and raised its foreign-class scalar by 0.062 between U05 and U06 with no change of ideas, reforms, policies, modifier list and mercantilism: the game definition of `max_demand` (request_2 Q1) and the values of the tech level 23 and the parliament issue `charter_trade_companies`; or two saves of one country that differ only in one technology level.

## Update 2026-10-05 - Venice series U07-U30 (new game, VEN, 1444.11.11 to 1445.07.02)

Status: scripts `backend/scripts/research/venice_c_md_evolution.py`, `venice_c_ven_md.py`, `venice_c_natexp2.py`, `venice_c_foreign.py`, `venice_c_foreign2.py`, `venice_c_homebonus.py`, `venice_c_homebonus2.py`, `venice_c_embargo.py`, `venice_c_tick_scalar.py`, `venice_c_firsttick.py` (loader `venice_load.py`), every kept claim re-run with the independent regex readers `venice_c_raw.py` / `venice_c_ver1..5.py` (section 'Verification 2026-10-05 (second pass, Venice series)' at the end). Labels: `confirmed` = whole set, exceptions listed; `inferred` otherwise.

New data (stored as U07-U30): one fresh game as Venice (VEN), 24 saves. U07-U25 (1444.11.11, .11.14, .11.30, .12.01, .12.02, .12.11, .12.31, 1445.1.1, .1.2, .1.15, .1.24, .1.30, .1.31, .2.1, .2.3, .2.10, .2.17, .2.28, .3.1) are hands-off (no merchant action; VEN's three merchants steer; the fleet mission of VEN's 3-barque fleet was changed by the player twice, see R11). U26-U30 (1445.3.31, .4.1, .5.1, .6.1, .7.2): all three merchants recalled before 03.31 (no `has_trader` in the trade entries at 03.31), then one merchant re-sent per month (ragusa by 05.01, alexandria by 06.01, wien by 07.02). VEN never has an embargo, never collects away, has `trade_port = capital = 112` (node `venice`, an end node with no outgoing link). The same scenario as the older start snapshot S01 (VEN, 1444.11.11, same version and mods), but a different game (different `campaign_id`).

### VS-1 `max_demand` changes only when a 1st of the month is crossed
Claim: in the Venice series every `max_demand` value (53,290 country-node values per save) is identical between two saves unless a 1st of a month lies between them. 15 of 15 consecutive pairs without a 1st in between: 0 changed values; 8 of 8 pairs crossing a 1st: 19,074 (11.30 -> 12.01), 3,843 (12.31 -> 1.1), 14,704 (1.31 -> 2.1), 7,796 (2.28 -> 3.1), 21,020 (3.31 -> 4.1), 22,369 (4.1 -> 5.1), 9,339 (5.1 -> 6.1), 8,605 (6.1 -> 7.2) changed values.
Applies when: all countries and nodes of this game. Source: `venice_c_md_evolution.py` (per-pair table), independent `venice_c_ver1.py`.
Quote (VEN `venice`, `max_demand`): 1.323 on 1445.3.1 and on 1445.3.31 although the country field `transfer_home_bonus` is already 0.0 on 03.31 (0.3 on 03.1); 1.023 on 1445.4.1.
Confidence: confirmed. Consequence: within a month every stored `max_demand` is the value of the last 1st; a player action of the month (merchant recall, embargo, ...) shows in `max_demand` only at the next 1st (VS-2, VS-5).
Caveat: the embargo and recall events happen between the 1st's; a change made on the 1st itself after the tick could not be observed.

### VS-2 Home-node bonus: 0.1 per steering merchant, clean test outside the TUR/BNG campaign (updates C-06, V8, V10)
Claim: VEN's `max_demand` at its home node `venice` = base + `transfer_home_bonus`, where `transfer_home_bonus` (country field) = 0.1 x the number of VEN's steering merchants, and the bonus enters `max_demand` at the next 1st. The foreign class does not move with it.
Source: `venice_c_ven_md.py`, independent `venice_c_ver3.py`.
Rows (VEN, md at `venice` / md at every foreign node / field / steering merchants):
| save | md venice | md foreign | `transfer_home_bonus` | steering merchants |
|---|---|---|---|---|
| 1444.11.11 (U07, before any tick) | 1.013 | 0.937 | 0.0 | 3 |
| 1444.11.14 - 11.30 (U08, U09) | 1.013 | 0.937 | 0.3 | 3 |
| 1444.12.1 - 12.31 (U10-U13) | 1.313 | 0.937 | 0.3 | 3 |
| 1445.1.1 - 3.1 (U14-U25) | 1.323 | 0.946 | 0.3 | 3 |
| 1445.3.31 (U26) | 1.323 | 0.946 | 0.0 | 0 (recalled) |
| 1445.4.1 (U27) | 1.023 | 0.946 | 0.0 | 0 |
| 1445.5.1 (U28) | 1.122 | 0.945 | 0.1 | 1 (ragusa) |
| 1445.6.1 (U29) | 1.222 | 0.945 | 0.2 | 2 (+ alexandria) |
| 1445.7.2 (U30) | 1.322 | 0.945 | 0.3 | 3 (+ wien) |
So md(venice) - 0.937/0.946/0.945 = 0.076/0.077/0.077 (the base, without bonus; see the 1.013 and 1.023 rows) and +0.3 after the first 1st (1.313 - 1.013 = 0.300; 1.322 - 1.023 = 0.299 with the base 1.022 after 5.1), +0.1 per re-sent merchant. The field itself changes at once (0.0 -> 0.3 between 11.11 and 11.14; 0.3 -> 0.0 by 03.31 after the recall); `max_demand` follows at the next 1st (VS-1).
Answers: the home bonus exists for a country other than BNG/TUR/C05/C08/C10 (V8, V10 asked for this); nobody collects away, no embargo, top-province node = home node; the bonus is absent in a start snapshot (U07, S01) because the first 1st has not happened yet, not because start snapshots differ.
Population (all countries, U08-U30): 7,355 of 7,574 country-saves with >= 1 steering merchant have field = 0.1 x (steering merchant entries, i.e. entries with `has_trader` and `type`); restricting to merchants whose node has the home node downstream fits 7,422; 144 country-saves fit neither (e.g. BUR with one steerer at rheinland, home champagne, field 0.0; GEN, SAV, NOV, CHE, ORI, NAP, LIG, VER in 1444.11.14 with field 0.0 and one steerer). Steering direction does not matter in this case: VEN's steerers at alexandria and ragusa steer link 1 (genua) and the wien steerer link 0 (saxony), none towards `venice`; but each of the three nodes has `venice` as a direct link, so "merchant in a node adjacent to home" is not separated from "any steering merchant".
Confidence: confirmed for VEN (24 of 24 saves, 5 values of the count); inferred for the general rule (97.1% of country-saves).

### VS-3 The per-country scalar depends on the ruler's DIP skill: +0.005 per point in the foreign class (new; first identified cause of a scalar difference)
Claim: between two fresh games of the same scenario (S01 and U07, both VEN 1444.11.11) the foreign-class `max_demand` of a country changes by exactly 0.005 x (change of the current ruler's DIP skill) for the 34 countries whose scalar differs at all; in 535 countries with the same ruler DIP it is identical in both games.
Source: `venice_c_natexp2.py` (ruler = `history` monarch block whose id equals the country's current `monarch` id), independent `venice_c_ver2.py`.
Quote: of 666 countries present in both games, 2 have no ruler block; 535 have the same ruler DIP and the same `max_demand` at every node (S01 and U07); 129 have a different ruler DIP (random rulers of tribes and some small states): in 34 the foreign-class value changed, in all 34 by exactly 0.005 x delta-DIP (YOL +3 -> +0.015: 1.036 -> 1.051; AWN -4 -> -0.020: 1.049 -> 1.029; YAQ -6 -> -0.030: 1.049 -> 1.019; TUA +4 -> +0.020; RAG, BRE, SIE, FRI, HSA among them); 88 are one-class countries (the same value at all 80 nodes; no change although the DIP changed: AAC, FRN, ULM, ABE, APA ...); 7 are two-class countries with classes {1.009, 1.036} that did not respond (BLM, BNJ, MAA, TAN, TNK, TEA, TTT; delta-DIP -2, -5, +3, +3, +3, -4, +2). The domestic (home) class did not change in any of the 34.
Cross-section (U07): 238 of 281 two-class countries with a ruler satisfy foreign - domestic = 0.012 + 0.005 x DIP exactly (DIP 0..6; same 237-238 of 281 in S01, S10, S30); the other 43 have further terms (e.g. SWE +0.027, GOT +0.172, EFR +0.172, HDR +0.127, ORM +0.132, VEN 0.0 (domestic above foreign)). The formula fails in later-era saves (S50 111 of 254, S67 19 of 285, S78 39 of 311, S79 0 of 45, U06 1 of 30; `venice_c_dip_corpus.py`), so it is a description of the 1444 state, not a general formula.
Confidence: confirmed for the 34 responders (natural experiment: a single random difference); the mechanism and name of the game effect are UNKNOWN (request_2 Q7); why 95 countries do not respond is UNKNOWN (88 one-class ones have no foreign/domestic difference; the 7 non-responders have the same foreign value 1.036).
Relation to earlier open items: this is a term of the per-country scalar (V4, request_2 Q1); it is not the cause of the home `money/total` steps of 0.05 between identical peers at 1444 (SWE/DAN/BRA, R07): those steps are 10 times larger, and in the 25 countries with `feudalism_reform` the home X is 1.07 at ruler DIP 1, 3 and 5 in every country, but 1.07 or 1.12 at DIP 2 and 1.07 or 1.17 at DIP 4 (`venice_c_xdip.py`, U07), so X is not a function of the ruler's DIP.

### VS-4 How the scalar moves over time (new)
Claims:
- (confirmed) The foreign-class scalar of VEN did not react to the recall or re-adding of its merchants: 0.946 on 03.1, 03.31 and 04.1 (3 merchants, then 0), 0.945 from 05.1 (1, 2 and 3 merchants alike). Only the home class moved (VS-2).
- (confirmed) Number of countries whose most common `max_demand` changed at a 1st: 236 (1444.12.1), 47 (1445.1.1), 184 (2.1), 98 (3.1), 263 (4.1), 280 (5.1), 117 (6.1), 108 (7.2) of 666; typical size +0.002 (median), 224 of the 236 first-tick changes positive.
- (confirmed) First tick, large steps: GEN +0.202 (0.935 -> 1.137), NOV +0.202 (0.944 -> 1.146), HSA +0.102, RAG +0.100, PSK +0.100; all five are republics with reform `merchants_reform` (GEN, HSA, RAG) or `veche_republic` (NOV, PSK). Of the 32 republics the other 26 changed by at most 0.002 at that tick, and VEN (`venice_merchants_reform`) by 0.000. Their merchants at the first tick: GEN 2 collecting away + 1 steering; NOV 1 home + 1 away + 1 steering; HSA 3 steering; RAG 1 home + 2 steering; PSK 1 home + 1 steering. No pattern in merchant actions (HSA has no collecting merchant, VEN has three steering ones like HSA).
- (negative, inferred) No numeric country-block field tracks the tick changes: best correlations of the change with the change of a field over the 666 countries were `corruption` r = 0.83 at the first tick (n = 31 countries that carry the field; in 12 of the 30 countries where corruption changed the scalar did not) and <= 0.58 (`max_sailors`) at the other ticks; `venice_c_tick_scalar.py`, `venice_c_corruption.py`.
Confidence: confirmed for the counts; the cause of the drift and of the five republic steps is UNKNOWN.

### VS-5 Embargo: timing and the formula on nine new rows (updates C-05, C-06)
Claims:
- (confirmed) The embargo appears in the country block (`trade_embargoed_by`) first and lowers `max_demand` only at the next 1st: LAN embargoed by GEN from 1445.1.1 (not on 12.31), LAN at crimea 1.057 on 1.1 through 1.31 and 0.953 from 2.1; GEN embargoed by LAN from 1.15 (not on 1.2), GEN at alexandria 1.137 on 1.31, 1.136 from 2.1; ENG embargoed by FRA by 3.31 (not on 3.1), ENG at champagne 1.073 on 3.31, 0.899 from 4.1.
- (confirmed, inferred mechanism) Using the response_1 definition (`own = max_pow - prev`; predicted reduction = 0.5 x sum of embargoer own / (sum of all own + 5 x NH); observed reduction = 1 - md/cap with cap = the country's value at nodes with no embargoer own power), U30 rows outside the embargoed country's home node:
| embargoed, embargoer | node | md | cap | observed % | predicted % | ratio |
|---|---|---|---|---|---|---|
| ENG, FRA | rheinland | 1.044 | 1.047 | 0.29 | 0.23 | 1.3 |
| ENG, FRA | bordeaux | 0.946 | 1.047 | 9.65 | 7.62 | 1.27 |
| ENG, FRA | champagne | 0.896 | 1.047 | 14.42 | 12.11 | 1.19 |
| ENG, FRA | valencia | 0.955 | 1.047 | 8.79 | 7.68 | 1.14 |
| GEN, LAN | alexandria | 1.137 | 1.142 | 0.44 | 0.42 | 1.05 |
| GEN, LAN | champagne | 1.139 | 1.142 | 0.26 | 0.34 | 0.76 |
| LAN, GEN | crimea | 0.949 | 1.063 | 10.72 | 11.21 | 0.96 |
| LAN, GEN | constantinople | 1.050 | 1.063 | 1.22 | 5.03 | 0.24 |
| LAN, GEN | champagne | 1.060 | 1.063 | 0.28 | 0.34 | 0.82 |
7 of 9 rows are within 2.5 percentage points of the formula; the ENG rows are 14-27% larger than predicted (like the BNG/DEC/RUS factors of V6/Q4) and `constantinople` (LAN) is 4 times smaller. The exactness question stays open; the Venice rows are consistent with "approximately right, not exact".
Source: `venice_c_embargo.py` (`analyse`, `summary`), independent `venice_c_ver4.py` (D) and `venice_c_ver5.py` (3).
Confidence: confirmed for the timing (3 of 3 embargoes); inferred for the magnitude.

### What settles it (Venice series adds)
- The game effect behind +0.005 per ruler-DIP point (Q7), and what the 7 non-responders and the 88 one-class countries have in common.
- Why five republics rise by 0.1-0.2 at the first 1st and why VEN does not (country-block fields of GEN, NOV, HSA, RAG, PSK against VEN at 1444.11.30 and 1444.12.1).
- Whether a steering merchant must be in a node adjacent to / upstream of the home node to count for `transfer_home_bonus` (144 unexplained country-saves; a save with a steering merchant in a node with no link path to home).
- Embargo magnitude per embargoer (unchanged).

### Verification 2026-10-05 (second pass, Venice series)
Independent recomputation with regex readers over the raw files (`venice_c_raw.py`: no clausewitz parser, no cache) in `venice_c_ver1.py` (VS-1), `venice_c_ver2.py` (VS-3), `venice_c_ver3.py` (VS-2), `venice_c_ver4.py` (VS-5 timing), `venice_c_ver5.py` (VS-3 cross-section, VS-2 population, VS-5 rows):
- VS-1: identical counts for all 23 pairs (0 x 15; 19,074 / 3,843 / 14,704 / 7,796 / 21,020 / 22,369 / 9,339 / 8,605).
- VS-2: identical table for all 24 saves (md, field, steering entries); population 7,355 true / 219 false, identical.
- VS-3: 34 of 34 differing countries exact; 129 countries with a changed ruler, 34 changed / 95 unchanged (88 one-class + 7 non-responders); cross-section 238 of 281 (1 country without a ruler block). Error found and corrected by this pass: the first version of the ruler lookup took the first monarch block of the `1444.11.11` history entry, which for native tribes is the regency "Native Council" (DIP 3 in all of them) in some saves; the ruler must be the block whose id equals the country's current `monarch` id. With the wrong lookup the natural experiment looked like 24 of 112; with the right one it is 34 of 34, and the cross-section count changed from 215 to 238 of 281.
- VS-5: timing identical; the nine U30 rows identical.
- VS-4: the per-tick counts and the five republic steps were checked once more by `venice_c_firsttick.py` (merchant classes) only; the drift cause stays UNKNOWN, so nothing is claimed beyond the counts.
