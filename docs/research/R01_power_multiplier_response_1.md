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
Confidence: confirmed for the rule "home or top"; the alternative "dominant total power" was not tested.
TUR S79 rows classified by the rule (`top_provinces[0]`): dom = hormuz, constantinople, basra, aleppo, alexandria (and the away rows ragusa, venice); foreign = everything else including crimea (top RUS) and the_moluccas (top SUN, TUR 97.455 is not top) and gulf_of_aden (top YEM). With these classes every row is <= its class cap, and the draft's classification of crimea as domestic is contradicted (crimea 1.648 is a 21.9% embargo reduction of the foreign cap 2.110, RUS own power 98.8). the_moluccas: rule predicts foreign; md 2.110 = foreign cap: consistent.
GEN S79: classes from the same rule: genua dom (home), all others foreign; foreign cap 1.907 (ethiopia, gulf_of_aden, aleppo, crimea, tunis, ragusa); genua 1.241 (embargoers SWI 50.7, PAP 78.9, LAN 131.1 own power: embargoed, so 1.241 is not a clean domestic cap: GEN has no clean domestic row).
### C-04 Domestic cap below foreign cap is common, not a TUR/GEN oddity
Quote (non-embargoed countries, home vs foreign value): home lower 20,212, equal 20,586, higher 1,834 (ratio min 0.528, median 1.0, max 4.253). Independent run `ver_r01_homeforeign.py` (equal = within 0.0005): 20,233 / 20,569 / 1,834 over 42,636 groups; min/median/max identical. (The first version's three numbers sum to 42,632, the four multi-valued groups being excluded.) The explanation of why abroad can be larger is a modifier question (UNKNOWN from data). Constantinople and hormuz both 1.895 with no embargoer power there (consistent with no embargo at those two).

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
Confidence: inferred (perfect fit but narrow sample). The define value (0.1) and wording need an outside source.

## Q4 - Cap composition
Data-only partial answer: the foreign multiplier is a per-country scalar (C-01) with 749 distinct values and the clustering above; no saved scalar explains it (C-05). The modifier sums (idea, policy, government) need sourced values: not answered.

## Not answered (needs an outside source)
Q1 last bullet quotes; Q2 sourced explanation why abroad is larger; Q3 define `TRADE_POWER_HOME_BONUS`; Q4 (a)-(c) modifier names/values, "1 + sum vs product" quote; Q5 all source/quote repairs (C-03..C-11).

## Still UNKNOWN and what settles it
1. Exact embargo magnitude: per-embargoer `embargo_efficiency`, caravan power (not in save) or an embargo on/off pair.
2. Composition of the cap: pairs changing one idea/policy and reading the foreign multiplier at an unembargoed node.
3. Home bonus in start snapshots and beyond 4 tags: another played save with several steering merchants.

## Verification (date 2026-10-04)
Independent recomputations (new scripts `ver_r01_const.py`, `ver_r01_embargo.py`, `ver_r01_top.py`, `ver_r01_homeforeign.py`, `ver_r01_dist.py`, `ver_r01_homebonus.py`, `ver_r01_tur.py`, written without reusing the author's classification code) plus re-runs of `r01_md_classes.py`, `r01_top_vs_home.py`, `r01_embargo4.py`.
- Re-run and matching: corpus size 3,420,320 (C-01 header); embargo presence test 7,968 not reduced / 2 reduced without embargoer power (C-02); all TUR S79 observed reductions and predictions of the per-row table (after the NH / sum definitions were added) and the GEN S79 rows (alexandria 3.78/3.21, wien 2.83/2.39, saxony 2.83/2.41, rheinland 3.25/2.60, champagne 6.97/6.28, valencia 7.76/6.33, venice 10.02/8.41); observed/predicted ratios per embargoer (BNG 1.25-1.26, DEC 1.13-1.14, RUS 1.16-1.20, astrakhan 0.96); top == home 839 and top == both 18 (C-03); home higher 1,834 and ratio min/median/max (C-04); 749 distinct foreign values, top-8 share 59.7 %, min 0.281 ZUN S42, max 2.166, 3,815 country-saves below 1.0 in 207 tags (C-05); home bonus 16 of 16, 12 of 12, 831 start snapshots (C-06, sign: home is HIGHER than top by 0.1 x steering merchants).
- Corrected: C-01 single-valued groups 41,774 of 42,636 (98.0 %) -> 42,632 of 42,636 (99.99 %), the earlier script had not excluded top-province nodes; C-03 differs-from-both 14 of 871 -> 16 of 873 (the home-bonus cases); C-04 home lower / equal 20,212 / 20,586 -> 20,233 / 20,569 (tolerance); C-05 "exactly 1.000: none" -> one (S28 ETH), prestige correlation -0.07 -> -0.09 and rank 0.10 -> 0.08; C-06 "2 independent games" -> 2 saves (independence not established); per-row table: NH and sum-of-own definitions added; C-02: dependence of 1,206 / 148 on the "reduced" threshold stated.
- Not verified: "within each class the value is constant in all but 8 groups" (C-03); "14 with no steering merchant equal" (C-06); the correlation sample for power projection (n = 33,367 in the independent run); the regression `r01_cap_reg.py` / `r01_cap_values.py` numbers were not re-run; all Q4 / Q5 content is a source question.
