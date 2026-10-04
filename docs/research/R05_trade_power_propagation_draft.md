# R05 results - Trade power propagation between nodes (the prev field)

## 1. Answer

### Rule

For EU4 1.37.5, the best-supported exact rule for the save field `prev` is:

```text
for each country C
  for each outgoing link B -> D:
      p = province_power[D, C]

      if p >= 10:
          prev[B, C] += p / TRADE_PROPAGATE_DIVIDER
```

with:

```text
TRADE_PROPAGATE_DIVIDER = 5
effective propagation threshold = 10 provincial trade power
```

Equivalently, because the game defines `TRADE_PROPAGATE_THRESHOLD = 2` and `TRADE_PROPAGATE_DIVIDER = 5`, the documented effective threshold is 2 * 5 = 10:

```text
prev[B,C] =
    Σ over immediate downstream D of B:
        (province_power[D,C] / 5)   if province_power[D,C] >= 10
        0                           otherwise
```

The direction is therefore:

```text
trade-value direction:        B  ->  D  (downstream)
trade-power propagation:      D  ->  B  (upstream)
```

`D` is an immediate downstream node: it must be one of `B`'s outgoing links. Propagation is not recursive: `prev[D,C]` is not itself included in the amount propagated from `D` to `B`.

Each qualifying downstream link contributes independently. The 20% is **not divided among B's outgoing links**. A country with qualifying provincial power in several immediate downstream nodes receives 20% of its provincial power from **each** such node in B.

Only **provincial trade power** is propagated by the ordinary mechanism. Caravan power, merchant/presence power, capital flat power, and ordinary light-ship power do not enter this calculation. `ship_power_propagation` is the exception: when a positive ship-propagation modifier exists, ship trade power can also propagate, with the public documentation describing +20% ship propagation as 20% of the normal 20% rate, i.e. 4% of ship trade power.

Global trade-power modifiers do **not** modify the downstream amount before propagation; they apply in the receiving/upstream node instead.

### Implementation form

For the ordinary case used by the supplied 80-save dataset:

```pseudo
const DIVIDER = 5
const THRESHOLD_PROVINCE_POWER = 10

prev[B,C] = 0

for D in outgoing[B]:
    p = province_power[D,C]       # raw provincial TP at D

    if p >= THRESHOLD_PROVINCE_POWER:
        prev[B,C] += p / DIVIDER
```

Do **not** use `max_pow[D,C]`, `val[D,C]`, `province_power + ship_power`, or `province_power + prev` as the propagation source.

The exact internal ordering of the compiled threshold test — e.g. whether the executable tests `province_power >= 10`, `province_power / 5 >= 2`, or an equivalent expression — is **UNKNOWN**. The externally observable threshold is 10 provincial trade power.

### What remains unknown

The following cannot be established exactly from the available public sources and supplied save rows:

* whether the executable's boundary comparison is `>=` or `>`;
* the exact compiled rounding operation/order inside the trade calculation;
* whether `ship_power_propagation` is represented in the save in a way sufficient for a save-only calculator, or whether the calculator must reconstruct the country's modifier from ideas/age/other game state;
* whether there are any additional, undocumented exceptions to ordinary propagation in 1.37.5 beyond the documented ship-propagation modifier.

---

## 2. Variables

```json
[
  {
    "id": "prev",
    "meaning": "Trade power propagated into the current node from qualifying immediate downstream nodes",
    "unit": "trade power",
    "kind": "read",
    "source": {
      "type": "save",
      "path": "trade.node[].country[].prev"
    },
    "confidence": "confirmed"
  },
  {
    "id": "province_power_D",
    "meaning": "Country C's provincial trade power in downstream node D",
    "unit": "trade power",
    "kind": "read",
    "source": {
      "type": "save",
      "path": "trade.node[].country[].province_power"
    },
    "confidence": "confirmed"
  },
  {
    "id": "outgoing[B]",
    "meaning": "The immediate downstream trade-node links leaving node B",
    "unit": "node links",
    "kind": "read",
    "source": {
      "type": "save",
      "path": "trade.node[].outgoing / trade-node graph"
    },
    "confidence": "confirmed"
  },
  {
    "id": "TRADE_PROPAGATE_DIVIDER",
    "meaning": "Divisor applied to qualifying provincial trade power",
    "unit": "dimensionless",
    "kind": "constant",
    "source": {
      "type": "defines.lua",
      "path": "common/defines.lua: TRADE_PROPAGATE_DIVIDER"
    },
    "confidence": "confirmed"
  },
  {
    "id": "TRADE_PROPAGATE_THRESHOLD",
    "meaning": "Propagation threshold define; public documentation exposes its effective requirement as 10 provincial trade power",
    "unit": "trade-power threshold parameter",
    "kind": "constant",
    "source": {
      "type": "defines.lua",
      "path": "common/defines.lua: TRADE_PROPAGATE_THRESHOLD"
    },
    "confidence": "confirmed"
  },
  {
    "id": "ship_power",
    "meaning": "Light-ship trade power in node D",
    "unit": "trade power",
    "kind": "read",
    "source": {
      "type": "save",
      "path": "trade.node[].country[].ship_power"
    },
    "confidence": "confirmed"
  },
  {
    "id": "ship_power_propagation",
    "meaning": "Country modifier allowing ship trade power to propagate upstream",
    "unit": "fraction",
    "kind": "derived",
    "source": {
      "type": "other",
      "path": "country modifier / Age of Reformation ability"
    },
    "confidence": "reported"
  },
  {
    "id": "caravan_power",
    "meaning": "Trade-power contribution associated with inland-node caravan mechanics",
    "unit": "trade power",
    "kind": "read",
    "source": {
      "type": "other",
      "path": "country trade mechanics"
    },
    "confidence": "reported"
  }
]
```

---

## 3. Claims

### C-01 Direction: downstream to immediate upstream

- Claim: Ordinary trade-power propagation runs opposite to trade-value flow. A country's provincial trade power in a downstream node is added to the immediately upstream node.
- Formula:

  ```text
  D downstream of B
  propagated(D -> B) = qualifying_province_power[D] / 5
  ```
- Applies when: D is an immediate outgoing neighbour of B in the trade graph and the country has at least the propagation threshold of provincial trade power in D.
- Source: https://www.strategium.ru/forum/topic/5100-%D0%BF%D1%80%D0%B5%D1%84%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%B0-europa-universalis/page/44/
- Quote: "20% of their unmodified power transfers to the incoming node Beijing."
- Confidence: confirmed
- Caveats / contradicts: The quoted source is an old community copy of the wiki text, not a 1.37.5 developer source. The supplied 1.37.5 save data independently confirms the same direction.

---

### C-02 The propagated amount is 20% = one fifth

- Claim: The ordinary propagation divisor is 5.
- Formula:

  ```text
  propagation = province_power / 5
  ```
- Applies when: The downstream country satisfies the propagation threshold.
- Source: https://github.com/LysWalkorkill/eu4/blob/main/defines.lua
- Quote: "TRADE_PROPAGATE_DIVIDER = 5,"
- Confidence: confirmed
- Caveats / contradicts: The repository is a public copy of EU4 defines rather than a Paradox-published source pinned explicitly to 1.37.5. The same constant is independently present in the supplied task's assumed 1.37.5 environment.

---

### C-03 Effective threshold is 10 provincial trade power

- Claim: Propagation does not occur for a country with less than 10 provincial trade power in the downstream node.
- Formula:

  ```text
  if province_power[D,C] < 10:
      contribution = 0
  ```
- Applies when: Ordinary provincial trade-power propagation.
- Source: https://www.strategium.ru/forum/topic/5100-%D0%BF%D1%80%D0%B5%D1%84%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%B0-europa-universalis/page/44/
- Quote: "Any nation that has at least 10 provincial trade power in the node enjoys the propagation of that power upstream."
- Confidence: confirmed
- Caveats / contradicts: The exact compiled comparison at exactly 10.000 is UNKNOWN. Public descriptions say "at least 10"; no supplied row is a boundary test at exactly 10.000. The current public defines copy separately contains `TRADE_PROPAGATE_THRESHOLD = 2`, so the relationship between that internal parameter and the documented 10-point gameplay threshold is inferred from the constants 2 and 5.

---

### C-04 The threshold is on provincial power, not total power

- Claim: The threshold is applied to provincial trade power, not `max_pow`, `val`, ship power, or propagated `prev`.
- Formula:

  ```text
  qualifies = province_power[D,C] >= 10
  ```

not:

```text
max_pow[D,C] >= 10
val[D,C] >= 10
province_power[D,C] + ship_power[D,C] >= 10
province_power[D,C] + prev[D,C] >= 10
```

- Applies when: Ordinary propagation.
- Source: https://www.strategium.ru/forum/topic/5100-%D0%BF%D1%80%D0%B5%D1%84%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%B0-europa-universalis/page/44/
- Quote: "Any nation that has at least 10 provincial trade power in the node enjoys the propagation of that power upstream."
- Confidence: confirmed
- Caveats / contradicts: The exact compiled implementation is unavailable because the trade formulas are compiled. The 22 supplied rows provide strong empirical confirmation: rows with provincial power below 10 contribute zero even when they have ships or `prev`.

---

### C-05 Each immediate downstream link contributes independently

- Claim: If B has multiple outgoing links, a qualifying country's provincial power in each immediate downstream node contributes 20% to B. The amount is not split across B's outgoing links.
- Formula:

  ```text
  prev[B,C] = Σ_D (province_power[D,C] / 5)
  ```

for all qualifying D in `outgoing[B]`.

- Applies when: Each D is an immediate downstream node and independently meets the threshold.
- Source: https://www.strategium.ru/forum/topic/5100-%D0%BF%D1%80%D0%B5%D1%84%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%B0-europa-universalis/page/44/
- Quote: "20% of the nation's provincial trade power is added to the total trade power of that nation in every immediate upstream node"
- Confidence: confirmed
- Caveats / contradicts: This directly rules out dividing the propagated power by the number of outgoing links. Distance beyond one edge also does not enter this rule.

---

### C-06 Propagation is one edge only; `prev` does not chain

- Claim: Propagated `prev` at D is not used as a source for further propagation to B.
- Formula:

  ```text
  prev[B,C] += province_power[D,C] / 5
  ```

not:

```text
prev[B,C] += (province_power[D,C] + prev[D,C]) / 5
```

- Applies when: Ordinary downstream propagation.
- Source: https://www.reddit.com/r/eu4/comments/tqxqnw/so_sending_trade_power_upstream_ignores_prior_upstreamed_trade_power/
- Quote: "This is true. You can get upstream trade power ... but that 2 trade power will not add 0.4 trade power in Sevilla."
- Confidence: reported
- Caveats / contradicts: Community evidence rather than developer documentation. The supplied 1.37.5 data strongly supports it: adding the displayed downstream `prev` values produces the original false predictions, while excluding them produces the saved `prev` values.

---

### C-07 Global trade-power modifiers are not applied before propagation

- Claim: The amount propagated from D is based on unmodified provincial trade power; global trade-power modifiers are applied in the receiving node.
- Formula:

  ```text
  propagated_amount = raw/unmodified provincial_trade_power[D] / 5
  ```

then the receiving node's normal trade-power modifiers operate on the resulting trade power there.

- Applies when: Ordinary provincial propagation.
- Source: https://www.strategium.ru/forum/topic/5100-%D0%BF%D1%80%D0%B5%D1%84%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%B0-europa-universalis/page/44/
- Quote: "Global trade power modifiers do not apply to the amount considered for propagation, but are applied in the upstream node instead."
- Confidence: confirmed
- Caveats / contradicts: The source's surrounding wiki text was last verified for an older version. The supplied save field `province_power` is the relevant empirically fitted source for 1.37.5.

---

### C-08 Light ships normally do not propagate

- Claim: Ordinary light-ship trade power does not contribute to `prev`.
- Formula:

  ```text
  ordinary_ship_contribution = 0
  ```
- Applies when: No positive `ship_power_propagation` modifier is present.
- Source: https://steamcommunity.com/app/236850/discussions/0/2673382867118871689/
- Quote: "the trade power that gets transferred upstream is only from provinces unless you have the Age of Reformation ability 'Powerful Tradeships'."
- Confidence: reported
- Caveats / contradicts: This is a community explanation of the mechanic. The supplied 1.37.5 rows provide strong support: several downstream nodes contain substantial ship power, but the saved `prev` is exactly explained by qualifying provincial power alone.

---

### C-09 `ship_power_propagation` enables a separate ship contribution

- Claim: A positive ship-propagation modifier can make ship trade power propagate upstream.
- Formula supported by public documentation:

  ```text
  ship_propagated = ship_power * ship_power_propagation / 5
  ```

For the documented +20% modifier:

```text
ship_propagated = ship_power * 0.20 / 5
                = ship_power * 0.04
```

- Applies when: A country has a positive ship-trade-power propagation modifier.
- Source: https://www.strategium.ru/forum/topic/5100-%D0%BF%D1%80%D0%B5%D1%84%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%B0-europa-universalis/page/44/
- Quote: "+20% Ship tradepower propagation: An amount of 20% × 20% of ship tradepower also added to upstream node."
- Confidence: reported
- Caveats / contradicts: The source establishes the +20% example and the 4% effective rate, but it does not establish from compiled code that the general formula is always exactly `ship_power * ship_power_propagation / 5` for arbitrary positive values. Treat the generalized formula as inferred. The ordinary 1.37.5 saves appear to have zero ship propagation, consistent with `ship_power` contributing 0.

---

### C-10 Caravan power does not participate in downstream-propagation

- Claim: Caravan power is not propagated by the ordinary "transfer from traders downstream" mechanism.
- Formula:

  ```text
  caravan_contribution_to_prev = 0
  ```
- Applies when: Ordinary propagation.
- Source: https://www.reddit.com/r/eu4/comments/1vd0lps/any-good-guides-on-trade/
- Quote: "This only applies to province trade power, caravan power is not propagated through this mechanism."
- Confidence: reported
- Caveats / contradicts: This is recent community evidence, not a developer source. It is consistent with the supplied rows and with the distinction in the older wiki text between provincial propagation and other trade-power sources.

---

### C-11 Trade steering does not change `prev`

- Claim: Trade steering affects the use of trade power for directing trade value, not the amount of provincial trade power propagated upstream.
- Formula:

  ```text
  prev = function(province_power, outgoing_links, propagation_constants)
  ```

and not a function of `trade_steering`, `steer_power`, or merchant direction.

- Applies when: Calculating ordinary propagated power.
- Source: https://www.strategium.ru/forum/topic/5100-%D0%BF%D1%80%D0%B5%D1%84%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%B0-europa-universalis/page/44/
- Quote: "Trade steering is applied as a multiplicative bonus to trade power used for steering when determining which outgoing node trade is steered to."
- Confidence: reported
- Caveats / contradicts: The source describes steering separately from provincial propagation. The supplied task data also shows no need for a steering term.

---

### C-12 Merchant presence and capital extras do not propagate

- Claim: Merchant flat power, capital flat power, and other non-provincial flat additions do not become the source of ordinary downstream propagation.
- Formula:

  ```text
  propagation_source = province_power
  ```

not:

```text
max_pow
```

- Applies when: Ordinary propagation.
- Source: https://steamcommunity.com/app/236850/discussions/0/3002172678263665211/
- Quote: "If a nation has some Provincial(!) Trade Power in a Node it automatically gets TP in all adjacent upstream Nodes."
- Confidence: reported
- Caveats / contradicts: This source does not enumerate every possible flat modifier. The supplied dataset empirically supports the narrower rule that the saved `prev` is explained by downstream `province_power` alone.

---

## 4. Validation against the data in this task

The task supplied 22 of the stated 26 originally failing entries. Applying:

```text
prediction =
    Σ(province_power_D / 5)
    for D in B.outgoing
    where province_power_D >= 10
```

reproduces all 22 supplied rows. The residual 0.001 differences are consistent with the displayed downstream `province_power` being rounded to two decimals while `prev` is stored/displayed to three decimals.

### Five detailed examples

#### 1. patagonia / C06

Downstream:

```text
laplata: prov = 4.94   -> below 10 -> 0
cuiaba:  prov = 99.50  -> qualifies -> 99.50 / 5 = 19.900
```

Therefore:

```text
predicted prev = 19.900
saved prev     = 19.900
```

The original naive formula was 20.889 because it incorrectly included `4.94 / 5 = 0.988`. It also did not need the downstream `prev` values.

**Result: reproduced exactly.**

Task source: `R05_trade_power_propagation_goal.md`, lines 55-57.

---

#### 2. california / POR

Downstream:

```text
mexico:             prov = 0.00   -> 0
mississippi_river:  prov = 0.62   -> 0
polynesia_node:     prov = 10.20  -> 10.20 / 5 = 2.040
```

Therefore:

```text
predicted prev = 2.040
saved prev     = 2.040
```

**Result: reproduced exactly.**

Task source: `R05_trade_power_propagation_goal.md`, lines 55-58.

---

#### 3. mississippi_river / C04

Downstream:

```text
carribean_trade: prov = 13.60 -> 13.60 / 5 = 2.720
ohio:            prov =  9.78 -> below 10 -> 0
```

Therefore:

```text
predicted prev = 2.720
saved prev     = 2.719
```

Difference:

```text
0.001 / 2.719 = 0.0368%
```

**Result: reproduced within 0.04%.**

The discrepancy is far smaller than the original failed prediction and is consistent with save/display precision.

Task source: `R05_trade_power_propagation_goal.md`, lines 55-59.

---

#### 4. chengdu / MNG

Downstream:

```text
canton: prov = 56.59 -> 56.59 / 5 = 11.318
xian:   prov =  5.83 -> below 10 -> 0
burma:  prov =  1.46 -> below 10 -> 0
```

Therefore:

```text
predicted prev = 11.318
saved prev     = 11.318
```

**Result: reproduced exactly.**

Task source: `R05_trade_power_propagation_goal.md`, lines 55-60.

---

#### 5. ivory_coast / SPA

Downstream:

```text
carribean_trade:  prov =   0.00 -> 0
bordeaux:         prov =   5.66 -> 0
english_channel:  prov =  53.95 -> 53.95 / 5 = 10.790
sevilla:          prov = 386.40 -> 386.40 / 5 = 77.280
```

Therefore:

```text
predicted prev = 10.790 + 77.280
               = 88.070
```

Saved:

```text
prev = 88.069
```

Difference:

```text
0.001 / 88.069 = 0.00114%
```

**Result: reproduced within 0.002%.**

Task source: `R05_trade_power_propagation_goal.md`, lines 55-76.

---

### All 22 supplied failure rows

| node B | country | saved prev | thresholded prediction | absolute error | result |
|---|---:|---:|---:|---:|---|
| patagonia | C06 | 19.900 | 19.900 | 0.000 | reproduced |
| california | POR | 2.040 | 2.040 | 0.000 | reproduced |
| mississippi_river | C04 | 2.719 | 2.720 | 0.001 | reproduced |
| chengdu | MNG | 11.318 | 11.318 | ~0 | reproduced |
| chengdu | BNG | 59.124 | 59.124 | 0.000 | reproduced |
| gulf_of_siam | KHM | 4.544 | 4.544 | 0.000 | reproduced |
| canton | TUR | 13.330 | 13.330 | ~0 | reproduced |
| canton | BEI | 14.429 | 14.430 | 0.001 | reproduced |
| philippines | TUR | 19.491 | 19.490 | 0.001 | reproduced |
| cuiaba | C06 | 29.330 | 29.330 | ~0 | reproduced |
| xian | CSH | 17.609 | 17.610 | 0.001 | reproduced |
| deccan | TUR | 3.968 | 3.968 | 0.000 | reproduced |
| gujarat | AJU | 14.849 | 14.850 | 0.001 | reproduced |
| katsina | SPA | 12.012 | 12.012 | 0.000 | reproduced |
| gulf_of_aden | SPA | 2.662 | 2.662 | 0.000 | reproduced |
| basra | IRQ | 9.175 | 9.176 | 0.001 | reproduced |
| alexandria | SPA | 20.755 | 20.756 | 0.001 | reproduced |
| alexandria | BLG | 7.285 | 7.286 | 0.001 | reproduced |
| novgorod | DAN | 15.125 | 15.126 | 0.001 | reproduced |
| ivory_coast | SPA | 88.069 | 88.070 | 0.001 | reproduced |
| ragusa | SPA | 20.755 | 20.756 | 0.001 | reproduced |
| ragusa | BLG | 7.285 | 7.286 | 0.001 | reproduced |

**Failures among the 22 supplied rows: none.**

The four additional failures mentioned by the task are not present in the uploaded data, so they cannot be independently validated here. They should not be silently assumed to pass.

---

## 5. Unknowns, contradictions between sources, and what would settle them

### U-01 Exact comparison at the threshold

The public description says:

> "Any nation that has at least 10 provincial trade power in the node enjoys the propagation of that power upstream."

The defines copy says:

> "TRADE_PROPAGATE_DIVIDER = 5,"

and:

> "TRADE_PROPAGATE_THRESHOLD = 2,"

The externally observable semantics are therefore a 10 provincial-trade-power threshold, but the exact compiled expression is UNKNOWN.

**Best intervention:** create a save with the same country at approximately 9.99, exactly 10.00, and 10.01 provincial trade power in a downstream node, with no other sources of power. Inspect `prev` upstream.

---

### U-02 Exact rounding/ordering

The thresholded formula predicts many rows 0.001 above/below the saved three-decimal value when using the two-decimal `province_power` values printed in the task.

This strongly suggests that the actual calculation uses more precision than the displayed input rows, but the exact internal rounding/order is UNKNOWN.

**Best intervention:** use a raw save with maximum available decimal precision for `province_power` and `prev`, or compare the game before/after a tiny controlled province-trade-power change.

---

### U-03 Ship propagation in 1.37.5

The public mechanic is clear that a positive ship propagation modifier exists, but the supplied saves do not demonstrate a positive `ship_power_propagation` case.

**Best intervention:** in EU4 1.37.5, obtain the Age of Reformation ability "Powerful Tradeships", put a known number of light ships in a downstream node, keep provincial power below the ordinary threshold, and inspect `prev` in the immediately upstream node. This isolates ship propagation.

---

### U-04 Generalized ship formula

For the documented +20% ship propagation, the public source explicitly describes:

```text
20% normal propagation × 20% ship propagation = 4% ship power
```

It is reasonable to infer:

```text
ship_power / 5 * ship_power_propagation
```

but the generalized arbitrary-modifier formula is not directly established by the available source.

---

### U-05 Four missing original failures

The task says there are 26 failing entries but supplies only the first 22. The remaining four are UNKNOWN and were not claimed as validated.

---

### U-06 Version continuity

The strongest textual description of "Transfers from traders downstream" available through search is from older wiki/community material, including material explicitly marked as last verified for approximately 1.25. The 1.30-era guide also describes the same 10/20% mechanism, and the current public defines copy still contains the same divider/threshold constants. The supplied 1.37.5 saves then provide direct empirical confirmation of the formula.

Therefore:

* **1.37.5 save behavior:** strongly confirmed by the supplied data.
* **1.37.5 official public prose:** not located.
* **No evidence found in this research that 1.37.5 changed this mechanism.**

---

## 6. Sources

1. **Paradox Wiki text reproduced by a community source — highest-quality available textual mechanic description, but version-old.**  
   https://www.strategium.ru/forum/topic/5100-%D0%BF%D1%80%D0%B5%D1%84%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%B0-europa-universalis/page/44/  
   Contains the key statements: 10 provincial-power threshold, 20% to every immediate upstream node, global modifiers excluded before propagation, and +20% ship propagation.

2. **Public EU4 defines.lua copy — direct numerical constants.**  
   https://github.com/LysWalkorkill/eu4/blob/main/defines.lua  
   Contains:
   `TRADE_PROPAGATE_DIVIDER = 5` and `TRADE_PROPAGATE_THRESHOLD = 2`.

3. **EU4 modding documentation — explicit interpretation of the constants.**  
   https://github.com/sandsevenone/eu4-modding-skill/blob/main/docs/Defines.md  
   Quote: "1/5 or 20% of your provincial trade power is added to your upstream node (if you have at least 10 provincial trade power in this downstream node)".

4. **Steam community discussion, 2020 — corroborates direction and ship exception.**  
   https://steamcommunity.com/app/236850/discussions/0/2673382867118871689/  
   Quote: "the trade power that gets transferred upstream is only from provinces unless you have the Age of Reformation ability 'Powerful Tradeships'."

5. **Reddit r/eu4, 2024 — corroborates one-hop, 20%, and threshold behavior.**  
   https://www.reddit.com/r/eu4/comments/1ay3azo/downstream_trade/  
   Quote: "20% of your provincial trade power (so long as you have 10 in the node already) goes upstream."

6. **Reddit r/eu4, 2026 — corroborates that caravan power is not part of this mechanism.**  
   https://www.reddit.com/r/eu4/comments/1vd0sru/any_good_guides_on_trade/  
   Quote: "This only applies to province trade power, caravan power is not propagated through this mechanism."

7. **rakaly/eu4save — relevant save-parser project, but not a source for the compiled trade formula.**  
   https://github.com/rakaly/eu4save  
   Reliability: useful evidence that EU4 save data can be parsed programmatically; it does not establish `prev` semantics.

8. **Supplied 1.37.5 task data — strongest direct validation for this particular implementation.**  
   `R05_trade_power_propagation_goal.md`, especially lines 45-49 and 55-78.  
   It supplies the 519-entry empirical fit and the 22 displayed failure rows used above.
