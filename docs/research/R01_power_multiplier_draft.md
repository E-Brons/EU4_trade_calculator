# R01 results - What determines max_demand (the multiplier from raw power to effective power)

Status summary: the **structure** of `max_demand` is established (cap x embargo factor x away factor); the **cap's composition from country modifiers is UNKNOWN** (not documented anywhere I could find, and not derivable from the save). No source documents the save field name `max_demand`; the mapping below is `inferred` from the data.

## 1. Answer
   
```
# per country c, per node n, game 1.37.5
# 1) base multiplier ("cap") - depends only on country modifiers and on the node CLASS
domestic(c,n)  = (n == c.main_trade_node)  OR  (c has the highest *provincial* trade power in n)   # wiki, 'Trade modifiers'
cap_dom(c)     = 1 + global_trade_power(c) + global_own_trade_power(c)       # inferred, composition UNKNOWN
cap_for(c)     = 1 + global_trade_power(c) + global_foreign_trade_power(c)   # inferred, composition UNKNOWN
                 # (+ overextension penalty on the foreign part: -1% per % overextension, wiki)
base(c,n)      = cap_dom(c) if domestic(c,n) else cap_for(c)

# 2) embargo factor (only if c is embargoed by country e that ALSO has power in n)
Share_e(n)     = (PShip_e + PProv_e) / (SShip + SProv + 5*NHome) * EMBARGO_BASE_EFFICIENCY(0.5) * embargo_efficiency_e
                 # P* = e's ship+merchant / province power in n; S* = sums over ALL countries in n;
                 # propagated power ('prev') is excluded; NHome = #countries whose main port is in n
embargo(c,n)   = 1 - sum_e Share_e(n)              # additive across embargoers: NOT verified; clamp at >= 0: NOT verified

# 3) away factor (merchant COLLECTING outside main trade node)
away(c,n)      = 0.5 + reduced_trade_penalty_on_non_main_tradenode(c)   if collecting_away(c,n) else 1
                 # wiki: "multiplicative modifier, applied after all other modifiers"  (details: R02)

max_demand(c,n) = base(c,n) * embargo(c,n) * away(c,n)        # inferred
val(c,n)        = max_pow(c,n) * max_demand(c,n)              # verified in the project data
```

Not in `max_demand` (they act on provincial power, which is already inside `province_power`/`max_pow`): `global_prov_trade_power_modifier`, mercantilism, `province_trade_power_modifier`, buildings. Not in it either: `trade_steering` (steering weight only), `trade_efficiency` (income only).

**Predicting max_demand where the country has no entry** (merchant/ships into a new node n):
1. Class: `domestic(c,n)` is decided by *provincial* power, so adding ships or a merchant cannot make n domestic (inferred from the wiki wording; ships/merchant are not provincial power). Use the node's `top_provinces[0]` (save) to test whether c is top.
2. Cap: read it from the save as `cap_for(c) = max md over c's entries that are non-domestic, non-away`, `cap_dom(c) = max md over c's domestic entries`. Caveat: under-estimates if every observed entry is embargoed. If c has no entry of a class, the cap is UNKNOWN from the save.
3. Embargo: needs the list of embargoers (`trade_embargoed_by`) and their `province_power`/`ship_power` in n (save) plus their `embargo_efficiency` (NOT in the save; UNKNOWN, use 1.0 as baseline).
4. Away: multiply by `0.5 + reduced_trade_penalty_on_non_main_tradenode` if the new merchant will collect outside the main node.

## 2. Variables

```json
[
 {"id":"max_demand","meaning":"multiplier raw->effective trade power","unit":"ratio","kind":"read","source":{"type":"save","path":"trade.node[].<TAG>.max_demand"},"confidence":"confirmed (val=max_pow*max_demand in project data)"},
 {"id":"global_trade_power","meaning":"country modifier, applies to all trade power sources","unit":"fraction","kind":"unknown","source":{"type":"other","path":"computed by game from ideas/policies/prestige/power projection; not in save"},"confidence":"confirmed (existence), UNKNOWN (value)"},
 {"id":"global_own_trade_power","meaning":"'Domestic trade power' modifier","unit":"fraction","kind":"unknown","source":{"type":"other","path":"country modifier, not in save"},"confidence":"confirmed (existence), UNKNOWN (value)"},
 {"id":"global_foreign_trade_power","meaning":"'Trade power abroad' modifier","unit":"fraction","kind":"unknown","source":{"type":"other","path":"country modifier, not in save"},"confidence":"confirmed (existence), UNKNOWN (value)"},
 {"id":"overextension","meaning":"-1% trade power abroad per percentage point","unit":"percent","kind":"unknown","source":{"type":"other","path":"country state, not in trade block"},"confidence":"confirmed (wiki)"},
 {"id":"domestic_flag","meaning":"node is main trade node or country has highest provincial power","unit":"bool","kind":"derived","source":{"type":"save","path":"country.main_trade_node (capital node) ; trade.node[].top_provinces[0]"},"confidence":"reported (wiki 'Trade modifiers'; save mapping inferred)"},
 {"id":"cap_for","meaning":"max_demand of unembargoed, non-away, non-domestic entry","unit":"ratio","kind":"derived","source":{"type":"save","path":"max over non-domestic non-collecting entries of max_demand"},"confidence":"inferred"},
 {"id":"cap_dom","meaning":"same for domestic nodes","unit":"ratio","kind":"derived","source":{"type":"save","path":"max over domestic entries"},"confidence":"inferred"},
 {"id":"EMBARGO_BASE_EFFICIENCY","meaning":"base embargo strength","unit":"ratio","kind":"constant","source":{"type":"defines.lua","path":"common/defines.lua EMBARGO_BASE_EFFICIENCY = 0.5 (value as quoted in forum; not re-read from file)"},"confidence":"reported"},
 {"id":"EMBARGO_MERCANTILISM_EFFICIENCY","meaning":"stated: mercantilism->embargo efficiency","unit":"-","kind":"constant","source":{"type":"defines.lua","path":"common/defines.lua"},"confidence":"reported ('does not seem to have an effect' per forum; other sources say +0.5% per mercantilism point)"},
 {"id":"embargo_efficiency","meaning":"country modifier multiplying embargo share","unit":"fraction","kind":"unknown","source":{"type":"other","path":"not in save"},"confidence":"UNKNOWN value"},
 {"id":"PShip,PProv,SShip,SProv,NHome","meaning":"embargoer ship/province power, node sums, #home-node countries","unit":"power","kind":"read","source":{"type":"save","path":"ship_power, province_power per entry; has_capital count"},"confidence":"reported formula, save mapping inferred"},
 {"id":"trade_embargoed_by","meaning":"list of embargoers of c","unit":"tags","kind":"read","source":{"type":"save","path":"country.trade_embargoed_by"},"confidence":"confirmed (field named in task)"},
 {"id":"TRADE_NON_CAPITAL_OFFICE","meaning":"-0.5 away penalty (multiplicative)","unit":"fraction","kind":"constant","source":{"type":"defines.lua","path":"common/defines.lua"},"confidence":"confirmed (wiki: -50%)"},
 {"id":"reduced_trade_penalty_on_non_main_tradenode","meaning":"reduces away penalty","unit":"fraction","kind":"unknown","source":{"type":"other","path":"country modifier, not in save"},"confidence":"confirmed (existence)"}
]
```

## 3. Claims

### C-01 Global trade power applies to every trade-power source
- Claim: `global_trade_power` multiplies all of a country's trade power.
- Formula: part of `base = 1 + GTP + ...`
- Applies when: always.
- Source: https://eu4.paradoxwikis.com/Trade (sections last verified for 1.25-1.30 per page banners; page itself unversioned)
- Quote: "Each country's trade power is increased by their global trade power modifier for all uses."
- Confidence: confirmed
- Caveats: wiki does not state that the multiplier is `1 + sum` in one place; that is `inferred`.

### C-02 Domestic vs abroad trade power are separate modifiers
- Claim: domestic and abroad modifiers exist as separate country modifiers; abroad also suffers overextension.
- Source: https://eu4.paradoxwikis.com/Trade
- Quote: "Trade nodes that are not domestic are considered abroad and will suffer from over-extension penalties."
- Confidence: confirmed
- Caveats: wiki gives no formula for how they enter the multiplier.

### C-03 Definition of "domestic" node
- Claim: domestic = home node, or node where the country has the highest *provincial* trade power.
- Source: https://eu4.paradoxwikis.com/Trade (search excerpt of 'Trade modifiers'; I did not see the section in the fetched truncated page)
- Quote: "A country's home node and nodes where a nation has the highest provincial trade power are considered domestic."
- Confidence: reported (wiki text, version not stated)
- Caveats / contradicts: Steam thread https://steamcommunity.com/app/236850/discussions/0/361798516941772193 (2016) gives two other readings: "Domestic is a bonus to trade power in trade nodes where you control physical territory" and (bri, 2020) "a) have your capital/main trading port ... b) are the dominant trade power". Namu wiki: "Trade power applied to the base node and the node with the highest market share". "Highest provincial power" (wiki) vs "dominant" (total power) differ; test with `top_provinces[0]` in the save (see section 4).

### C-04 Embargo reduces the target's trade power in shared nodes, multiplicatively
- Claim: embargoed country's trade power in node n is multiplied by roughly (1 - Share).
- Source: https://forum.paradoxplaza.com/forum/threads/embargo-question.1237666/ (posts #6, #8; community reverse-engineering, patch ~1.28-1.29, Aug 2019)
- Quote: "This is done to let the embargo trade power reduction act as an multiplicative and not as an additive modifier on the trade power of the embargoed country."
- Confidence: reported
- Caveats: post author also says displayed reduction = "share of trade * global trade power modifier"; I read this as reduction_additive = Share*(1+mods), i.e. result = (1+mods)*(1-Share). That reading is `inferred`.

### C-05 Embargo share formula
- Claim: `Share = (PShip+PProvince)/(SShip+SProvince+5*NHome) * 0.5 * EmbargoEfficiency`.
- Source: same thread, post #8 (Tempscire)
- Quote: "Share = (PShip + PProvince) / (SShip + SProvince + 5 * NHome) * 0.5 * EmbargoEfficiency,"
- Confidence: reported
- Caveats: same author: "in particular transfer from traders downstream is irrelevant"; later post: "SShip should include caravan power, while PShip does not". "Also any bonuses to global trade power do not seem to play a role" and "EMBARGO_MERCANTILISM_EFFICIENCY = 50 does not seem have an effect" - contradicts Steam guide https://steamcommunity.com/sharedfiles/filedetails/?id=273734181 ("each 1% of mercantilism provides ... 0.5% embargo efficiency"). Combination of several embargoers (sum vs product) is not documented. Maximize-profit policy adds a trade power modifier inside embargo nodes (same post).

### C-06 Embargo only acts where both countries have power
- Source: https://steamcommunity.com/app/236850/discussions/0/558746089011243293/ (quotes the wiki, old)
- Quote: "The defending country suffers a penalty to Trade Power in all trade nodes that both countries have power in."
- Confidence: reported (old wiki text, ~2016 versions)

### C-07 Prestige and power projection feed global trade power
- Source: forum thread above, post #6
- Quote: "prestige and power projection both confer the global trade power modifier."
- Confidence: reported
- Caveats: this makes GTP time-varying and not in the save (the save stores prestige/power projection separately; mapping coefficients UNKNOWN).

### C-08 Collecting away halves trade power, multiplicatively, after other modifiers
- Source: https://eu4.paradoxwikis.com/Trade
- Quote: "This is a multiplicative modifier, applied after all other modifiers."
- Confidence: confirmed (wiki; version-unverified)
- Caveats: details and exceptions belong to R02.

### C-09 Default trade policy adds +5%
- Source: https://eu4.paradoxwikis.com/Trade
- Quote: "+5% Trade power (Default policy)."
- Confidence: confirmed (wiki; the "maximize profit" policy)
- Caveats: part of `GTP`; whether the player's policy exists in a given save is UNKNOWN from the trade block.

### C-10 Provincial modifiers do not touch ships/merchants
- Source: https://steamcommunity.com/app/236850/discussions/0/361798516941772193 (bri)
- Quote: "Provincial trade power only applies to trade power generated by provinces, it does not apply to merchants or light ships."
- Confidence: reported
- Caveats: supports excluding `global_prov_trade_power_modifier` and mercantilism from `max_demand`.

### C-11 (data) Country caps are exact constants
- Claim: TUR foreign cap 2.110 (13 rows), TUR domestic cap 1.895 (constantinople, hormuz), GEN foreign cap 1.907 (6 rows). No row exceeds its cap.
- Source: tables in this task.
- Quote: n/a (derived)
- Confidence: inferred

## 4. Validation against the data in this task

**Cap constancy** (reproduced): TUR md = 2.110 exactly at philippines, polynesia_node, australia, hangzhou, the_moluccas, lahore, ethiopia, gulf_of_aden, zanzibar, tunis, champagne, valencia, genua. Example: philippines 26.001 x 2.11 = 54.862 (table 54.862); the_moluccas 110.785 x 2.11 = 233.756 (233.756); gulf_of_aden 110.631 x 2.11 = 233.431 (233.431). TUR domestic 1.895: constantinople 410.668 x 1.895 = 778.216 (778.215); hormuz 180.194 x 1.895 = 341.468 (341.467). GEN: 1.907 at ethiopia, gulf_of_aden, aleppo, crimea, tunis, ragusa (e.g. tunis 38.147 x 1.907 = 72.746).

**Lower-than-cap rows = embargo (structural test, passed):** reduction r = 1 - md/cap: TUR gulf_of_siam 13.3%, canton 18.6%, deccan 40.6%, astrakhan 48.0%, pest 31.2%, samarkand 21.8%, persia 25.0%, gujarat 28.8%, comorin_cape 27.5%, wien 14.7%, malacca 3.8%; domestic: aleppo 1.4%, alexandria 1.1%, basra 0.7%, crimea 13.0%. Necessary condition: embargoers (HUN, HAB, LUN, RUS, BNG, DEC) must have power in the node.
- gulf_of_aden (R08 table lists 17 countries, none of the six): TUR md = 2.11 = full cap. PASS.
- alexandria (R08 table lists HUN val 9.506 and HAB val 7.423): md 1.875 < 1.895. PASS (direction). Magnitude check: proxy shares by val/total: (9.506+7.423)/1054.341 = 1.61%, x 0.5 = 0.80% vs observed 1 - 1.875/1.895 = 1.06%. Ratio 1.3; plausible because the formula's denominator excludes `prev`, but NOT exactly validated (needs raw ship/province power and embargo_efficiency of HUN/HAB).
- Other rows: embargoer presence cannot be checked (their entries are not in the task data). I cannot confirm that DEC at gujarat/comorin_cape and BNG at canton/gulf_of_siam explain 28.8%/27.5%/18.6%/13.3%; R02's table does show DEC at gujarat (val 187) and comorin_cape (val 331), which is consistent.

**Collect-away rows** (md = cap x 0.5 x embargo): TUR venice 0.92: cap_for x 0.5 = 1.055; 0.92/1.055 = 0.872 (embargo 12.8%). TUR ragusa 0.761/1.055 = 0.721 (27.9%). GEN champagne 0.887/(1.907 x 0.5) = 0.930; GEN venice 0.858/0.9535 = 0.900. All four are <= cap x 0.5 as required. Several R02 rows with ratio exactly 0.500 (AYU, BLG, BRA, BRI ...) fit `cap x 0.5` with no embargo and no penalty reduction.

**Not reproduced / open:**
1. Composition of caps. TUR cap_for - cap_dom = 2.110 - 1.895 = 0.215; GEN home genua md = 1.241 vs GEN cap_for 1.907 (difference 0.666). In both cases the domestic value is LOWER than the foreign one, which is not what "domestic bonus" suggests; either foreign modifiers are larger for these countries, or GEN's 1.241 is itself embargoed. Not decidable from this data (TUR's two domestic rows are identical, suggesting no embargo there).
2. the_moluccas: TUR province 97.455, md 2.11 (foreign cap). If TUR had the highest provincial power there, C-03 predicts domestic (1.895). Check in the save: `trade.node[the_moluccas].top_provinces[0]` must not be TUR. If it is TUR, C-03 (wiki wording) is wrong for 1.37.5.
3. gulf_of_aden: TUR is `node.highest_power` 30.66 = 28.66 + 2 (my reading), but md = 2.11 (foreign). Consistent with C-03 only if another country has more *provincial* power (AJU val 267.7 suggests yes). Verify with `top_provinces`.
4. Everything about `embargo_efficiency` values and additive vs multiplicative combination of several embargoers.

## 5. Unknowns, contradictions between sources, and what would settle them

- **UNKNOWN: the numeric composition of cap_dom / cap_for from ideas/policies/tech/government.** No source lists it as a closed formula; the save does not store the totals. Settle: (a) R14 pair "unlock an idea/policy with `global_trade_power` / `global_foreign_trade_power`" and read the change of md at an unembargoed foreign node; (b) in game, open the country's modifier tooltip (Trade power / Domestic / Abroad) once and record the numbers per country as fixtures.
- **UNKNOWN: whether md equals exactly `(1+GTP+x)*(1-Share)`**. Settle: R14 embargo on/off pair; compare md before/after at a node where both have power; check vs formula in C-05 with save-read `ship_power`, `province_power` of the embargoer.
- **Contradiction:** domestic definition (C-03: three readings). Settle: for every country entry in the 80 saves, correlate `top_provinces[0]==tag` with md class (cap_dom vs cap_for).
- **Contradiction:** embargo efficiency from mercantilism (forum: no effect; Steam guide: +0.5% per point). Settle: R14 pair changing mercantilism by promoting it with an embargo active.
- **Version gap:** embargo formula posts are from 2019 (about patch 1.28-1.29); not confirmed for 1.37.5.
- The name `max_demand` is not documented in any public source I found (search for the field name returned nothing relevant). Its meaning is inferred only from `val = max_pow * max_demand`.

## 6. Sources (ranked)

1. https://eu4.paradoxwikis.com/Trade - official wiki; partly outdated (banners say verified for 1.25-1.30); good for structure, no numbers for md.
2. https://forum.paradoxplaza.com/forum/threads/embargo-question.1237666/ - community reverse-engineering with explicit formulas (2019); not developer-confirmed.
3. https://steamcommunity.com/app/236850/discussions/0/361798516941772193 - community, conflicting definitions of domestic (2016/2020).
4. https://steamcommunity.com/app/236850/discussions/0/558746089011243293/ - community quoting old wiki on embargo scope.
5. https://steamcommunity.com/sharedfiles/filedetails/?id=273734181 - old (2014-era) guide; mercantilism->embargo claim contradicts #2.
6. https://en.namu.wiki/w/Europa%20Universalis%20IV/%EB%AC%B4%EC%97%AD - Korean wiki; summary only.
