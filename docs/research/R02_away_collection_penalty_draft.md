# R02 results - The penalty for collecting away from the capital node (TRADE_NON_CAPITAL_OFFICE = -0.5)

Status summary: the **rule** (x0.5 on the whole multiplier, applied to every power component) is well supported by the data (21 of 43 rows exactly 0.500, and every other row is explainable by factors already identified in R01). The **interaction with `reduced_trade_penalty_on_non_main_tradenode`** and the **capital/main-trade-city distinction** could not be settled; marked UNKNOWN.

## 1. Answer

```
# per country c, node n, game 1.37.5
collecting_away(c,n) = merchant of c at n has action COLLECT  AND  n != c.main_trade_node
                       # steering merchants, merchant-less power, and the home node are NOT penalized
away_factor(c,n) = 0.5 + reduced_trade_penalty_on_non_main_tradenode(c)   if collecting_away(c,n)   # wiki: penalty -50% base, bonuses add onto it
                 = 1                                                      otherwise
                 # no clamp at 1: wiki says >+50% from other sources INCREASES power in non-main nodes

max_demand(c,n)  = base(c,n) * embargo(c,n) * away_factor(c,n)             # base, embargo: see R01
val(c,n)         = max_pow(c,n) * max_demand(c,n)                          # so the penalty hits province, ship, merchant(+2..), prev and flat extras alike
power_used(c,n)  = val - t_out + t_in                                      # transferred-IN power is NOT halved (wiki), it is added after
```

Facts that follow from the data (inferred):
- The factor is multiplicative on the *whole* multiplier, not an additive -0.5 on `1 + modifiers` (an additive penalty would give 0.857/1.357 = 0.63 for AYU; observed 0.500).
- No component is exempt: ship power, prev power, merchant power and `extras` are all inside `max_pow`, and `val = max_pow * md`.
- It depends only on (collecting, node != main trade node); `has_trader` is True in all 43 rows, so no merchant-presence variation is observable.

Related rule the optimizer must model (wiki, mapping to the save is inferred): the home-node bonus `TRADE_POWER_HOME_BONUS` (+10% per steering merchant, max +100%) exists **only if no merchant of the country collects outside the home node**. Turning ONE steering merchant into an away collector therefore (a) halves that node's power, (b) removes this merchant from the steering count, and (c) deletes the home bonus of all remaining steering merchants.

## 2. Variables

```json
[
 {"id":"TRADE_NON_CAPITAL_OFFICE","meaning":"base away penalty, -0.5","unit":"fraction","kind":"constant","source":{"type":"defines.lua","path":"common/defines.lua NDefines.NEconomy.TRADE_NON_CAPITAL_OFFICE (listed on https://eu4.paradoxwikis.com/Defines; value -0.50 as given in the task)"},"confidence":"confirmed (name), value from task"},
 {"id":"reduced_trade_penalty_on_non_main_tradenode","meaning":"country modifier added to the -50%","unit":"fraction","kind":"unknown","source":{"type":"other","path":"computed from missions/decrees/great projects; NOT in save"},"confidence":"confirmed (existence, wiki list), value UNKNOWN"},
 {"id":"collecting_away","meaning":"merchant collects at a node that is not the main trade node","unit":"bool","kind":"read","source":{"type":"save","path":"country entry has `total` key and no `has_capital`"},"confidence":"inferred"},
 {"id":"main_trade_node","meaning":"node of main trade city (= capital node unless changed with Wealth of Nations)","unit":"node id","kind":"read","source":{"type":"save","path":"country.capital / main trade city (field name not verified); entry.has_capital"},"confidence":"UNKNOWN whether has_capital == main trade city"},
 {"id":"TRADE_POWER_HOME_BONUS","meaning":"+10% home-node power per steering merchant if none collects away","unit":"fraction","kind":"constant","source":{"type":"defines.lua","path":"common/defines.lua (named in R06 task: 0.1, MAX 1)"},"confidence":"reported"},
 {"id":"max_demand","meaning":"final multiplier containing the away factor","unit":"ratio","kind":"read","source":{"type":"save","path":"trade.node[].<TAG>.max_demand"},"confidence":"confirmed"}
]
```

## 3. Claims

### C-01 Collecting away halves trade power; multiplicative; after all other modifiers
- Claim: factor 0.5 when a merchant collects outside the main trade city.
- Formula: `away_factor = 0.5 (+ reduced_penalty)`
- Applies when: merchant action = collect, node != main trade city.
- Source: https://eu4.paradoxwikis.com/Trade (sections banner "last verified 1.25 / 1.30")
- Quote: "In this case, the country's trade power is reduced by −50%, unless the merchant is sent to the country's main trade city. This is a multiplicative modifier, applied after all other modifiers."
- Confidence: confirmed (wiki), consistent with 21 rows of data
- Caveats / contradicts: old Steam post https://steamcommunity.com/app/236850/discussions/0/541907867755424097/ says "So if you have a +40% bonus trade power then when you collect from non home nodes you have a -70% penalty." (additive, pre-1.2x). REFUTED by the data (section 4).

### C-02 Steering / non-collecting power is not penalized
- Source: https://eu4.paradoxwikis.com/Trade
- Quote: "In other nodes than the country's home node, this gives a multiplicative penalty of −50% trade power." (under the "Collect from Trade" action; the "Transfer Trade Power" action has no such line)
- Confidence: confirmed (wiki), consistent with data (all penalized rows are collecting rows, `total` key present)

### C-03 Reduction of the penalty
- Claim: listed sources add onto the -50%; above +50% power is increased.
- Source: https://eu4.paradoxwikis.com/Trade
- Quote: "These bonuses add onto the −50% base penalty, having more than +50% from other sources means that the Trade Power is increased in non main trade nodes when collecting instead."
- Confidence: confirmed (wiki)
- Caveats: the wiki list (Nizwa Fort, Itchan Kala, Timurid mission, Panama/Sunset Invasion, Russian "The Asian Trade", Spanish Netherlands, Hungary mission, Emperor of China decree, ...) is the only enumeration I found; completeness for 1.37.5 is UNKNOWN. Whether the base is `0.5 + r` or `0.5 * (1 + r)` is not stated; "add onto" supports `0.5 + r` (inferred).

### C-04 Transferred power is not halved
- Source: https://eu4.paradoxwikis.com/Trade ("Other sources of trade power")
- Quote: "The trade power gained this way is not halved due to collecting outside the country's main trade node."
- Confidence: confirmed (wiki)
- Caveats: matches the save convention `val - t_out + t_in` (t_in added after `val`). Whether t_out is taken from the halved or unhalved power is R04.

### C-05 Home-node bonus is lost when collecting away
- Source: https://eu4.paradoxwikis.com/Trade
- Quote: "If no merchant is currently collecting outside the home node, then the home node receives a +10% bonus to trade power for each merchant who is steering trade."
- Confidence: confirmed (wiki text); that the bonus is inside `max_demand` (not `max_pow`) is `inferred`
- Caveats: also the wiki: "Other maluses, like the removal of transfer bonus in the main trade node, still apply." TUR in the data collects away (ragusa, venice), so its home md 1.895 is already without this bonus (consistent, not testable here).

### C-06 Main trade city vs capital
- Source: https://eu4.paradoxwikis.com/Trade
- Quote: "With the Wealth of Nations expansion, the main trade city can be changed at the cost of 200 diplomatic power. If the capital and main trade city are the same, moving the capital also moves the main trade city for free."
- Confidence: confirmed (wiki)
- Caveats: with Wealth of Nations the penalty is keyed to the main trade city, not the capital; the save field for the main trade city was not found in any source (UNKNOWN).

## 4. Validation against the data in this task

43 rows. Let ratio = md / median_md_elsewhere.

**Group A - ratio = 0.500 (21 rows): reproduced exactly by `away_factor = 0.5`, r = 0.**
AYU malacca 0.679/1.357 = 0.5004; AYU ganges_delta (max_pow = 2.0, merchant only) 0.679/1.357 = 0.5004; BLG genua 0.794/1.587 = 0.5003; BRA lubeck (province 50.669 + ship 3.5) 0.804/1.607 = 0.5003; BRI champagne (prev 2.882 included) 0.833/1.666 = 0.5000; C03 panama (ship 10.5) 0.772/1.543 = 0.5003; KHM canton (prev 4.544, extras 22) 0.724/1.447 = 0.5003; FRA genua (max_pow 2.0) 0.523/1.045 = 0.5005. Remaining exact rows: BRI english_channel, C02, C04, C06, C07, DLH gujarat, HAB, HAI, IRQ, KHM malacca, LIT, TRI, TRS. These rows contain province-only, ship, merchant-only and prev-bearing entries, so **no component is exempt**.
Refutation of the additive reading: AYU would be (1.357 - 0.5)/1.357 = 0.632, observed 0.500.

**Group B - ratio < 0.5 (17 rows).** Not explained by the away rule; consistent with the embargo factor from R01 (and a median that is itself biased). Conversion: `2*ratio` = implied remaining fraction relative to the median:
DEC comorin_cape/gujarat 0.768; GEN champagne 0.930; GEN venice 0.900; GZI zanzibar 0.982; KON ivory_coast 0.732; LAN venice 0.904; MAL ivory_coast 0.916; MOR ivory_coast 0.588; PAP genua 0.686; RUS baltic_sea 0.890; SON ivory_coast 0.734; SPA english_channel 0.662; SUN malacca 0.924; SWI genua 0.792; TUR ragusa 0.808; TUR venice 0.978.
Better measure against the R01 caps (not the median): TUR cap_for 2.110 -> 0.5*cap = 1.055; venice 0.92/1.055 = 0.872, ragusa 0.761/1.055 = 0.721. GEN cap 1.907 -> 0.9535; champagne 0.887/0.9535 = 0.930, venice 0.858/0.9535 = 0.900.
Same-node evidence that this is per-target and not per-node: genua has BLG and FRA at exactly 0.500 but PAP at 0.686 and SWI at 0.792 of it. A node-wide effect could not produce that; an embargo on specific targets can. **Reproduced only qualitatively** (no embargoer data in the task).

**Group C - ratio > 0.5 (5 rows): not settled.**
- DLH lahore 0.597 while DLH gujarat is exactly 0.500 (md 0.688, so cap_for = 1.376). If lahore is a domestic node for DLH (province 107.73, likely highest provincial power) and the away factor is still 0.5, then cap_dom(DLH) = 0.821/0.5 = 1.642 > cap_for (opposite order to TUR/GEN in R01). Plausible, untested.
- CSH beijing 0.656 and yumen 0.653 (ratios 0.553/0.551): two nodes with almost identical md although province power differs 88 vs 9 -> likely same class; 0.656/0.5 = 1.312 vs median 1.186, i.e. median 9.6% below. Either the median is depressed (as for TUR: median 1.882 vs cap 2.110, -10.8%) or r ~ 0.05. **Cannot distinguish.**
- MNG ganges_delta 0.538, SPA genua 0.505: same ambiguity (median bias vs small r vs domestic cap).

**Failures:** none of the 43 rows contradicts `md <= cap * 0.5 * (1 + r)` *if* r is allowed to be unknown; but the test is weak for groups B and C because the "median elsewhere" baseline mixes domestic/foreign/embargoed nodes (R01). The data in this task cannot separate r from cap-class effects.

## 5. Unknowns, contradictions between sources, and what would settle them

- **UNKNOWN: r for each country** (`reduced_trade_penalty_on_non_main_tradenode`). Not in the save. Settle: for each country compute `cap_for` from unembargoed non-away entries (R01) and then `r = md_away/(cap*embargo) - 0.5`; countries with exact ratio 0.500 prove r = 0. R14 pair "move the capital / merchant none -> collect away" measures it directly for one country.
- **UNKNOWN: does a country collecting at its capital node ever get the penalty?** Wiki: no, unless the main trade city differs from the capital (Wealth of Nations). The data show none, consistent with has_capital == main trade city, but the save field for the main trade city is not documented anywhere I found. Settle: R14 case "moving the capital" (and, with WoN, changing the main trade city).
- **UNKNOWN: country whose capital is in no trade node (colonial nation etc.).** No source. Inferred only: if no main node exists, every collecting node is "away". Settle: look for a colonial nation with a collecting entry and no `has_capital` anywhere; R02 rows C02..C07 are colonial nations that DO show exactly 0.500 at their collecting nodes (e.g. C03 panama, C04 chesapeake_bay), which supports "penalty applies where no home node is hit", but whether these nations have a main node at all is not known.
- **Contradiction:** additive (-70% with +40% bonus) vs multiplicative. Resolved for 1.37.5 by the data (Group A).
- **Contradiction/gap:** whether the home bonus (C-05) is in `max_demand`. Settle: pair "collect away -> steer" at a country with k>=1 other steering merchants; home md must change by exactly +0.1*k relative.
- **Version:** all wiki quotes come from sections last verified for 1.25-1.30; 1.37.5 not confirmed, but the data agree.

## 6. Sources (ranked)

1. https://eu4.paradoxwikis.com/Trade - official wiki; partly outdated banners (1.25/1.30) but the away-penalty text matches the data.
2. https://eu4.paradoxwikis.com/Defines - lists `TRADE_NON_CAPITAL_OFFICE` under NEconomy (name only; I did not obtain the value line from the game file).
3. https://steamcommunity.com/app/236850/discussions/0/2727382174628442937 - community summary of "halved" and the +10% home bonus; consistent with the wiki.
4. https://steamcommunity.com/app/236850/discussions/0/541907867755424097/ - community; additive claim, refuted by data.
5. Task data tables (43 rows) - primary evidence for the factor structure.
