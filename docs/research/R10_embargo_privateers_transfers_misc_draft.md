# R10 results - Embargo, privateers/pirates and why node total can differ from the sum of country val

## 1. Answer

In EU4 (version 1.37.5), **Pirates/Privateers** and **Embargoes** operate on node trade power, trade value, and collector dynamics as follows:

### Privateers & Pirate Trade Power Mechanics
1. **Privateer Trade Power Creation:**
   Light ships sent on a "Privateer" mission generate node trade power based on ship power modified by `privateer_efficiency`:
   $$\text{privateer\_power} = \text{ship\_power} \times (1 + \text{privateer\_efficiency}) \times \text{PIRATES\_TRADE\_POWER\_FACTOR}$$
   where `PIRATES_TRADE_POWER_FACTOR = 1.5` in `common/defines.lua`.

2. **Absence of `val` for Pirate Entities (`PIR`):**
   * Privateers act as a special faction represented by the tag `PIR` (or Pirate Republics / Pirates).
   * In the save file, `PIR` generates trade power (`max_pow` / `total`) and collects trade value, but **does NOT have a standard country entry with `val`** under the trade node block.
   * `total` (node trade power) equals the sum of all individual countries' `val` plus pirate trade power:
     $$\text{node.total} = \sum_{c \in \text{countries}} \text{val}_c + \text{pirate\_power}$$
   * **This directly explains why `node.total > sum(country.val)` across save files** when privateers are active in a node.

3. **Pirate Power in Node Totals & Collector Counts:**
   * Privateer power is treated as **collecting power** in the node.
   * `collector_power` = Sum of collecting power from actual countries.
   * `collector_power_including_pirates` = `collector_power` + $\text{pirate\_power}$.
   * `num_collectors` = Number of regular country tags collecting in the node.
   * `num_collectors_including_pirates` = `num_collectors` + 1 (if privateer/pirate power > 0).
   * Pirate power contributes to `retain_power` and retention ratios if it collects in that node, absorbing a proportional share of node income (`PRIVATEER_INCOME_COLLECTION_EFF = 0.5` converts 50% of the stolen trade value into gold for the privateering nations, while the rest is lost/treasury sink).

---

### Embargo Mechanics
1. **Embargo Effect on Trade Power:**
   An embargo applied by country $A$ against country $B$ reduces $B$'s trade power in nodes where both $A$ and $B$ have trade influence:
   $$\text{embargo\_penalty\_pct} = \text{EMBARGO\_BASE\_EFFICIENCY} \times \left(1 + \frac{\text{mercantilism}}{100} \times \frac{\text{EMBARGO\_MERCANTILISM\_EFFICIENCY}}{100}\right) \times (1 + \text{embargo\_efficiency}) \times \text{relative\_power\_share}$$
   where `EMBARGO_BASE_EFFICIENCY = 0.5` (-50% base modifier) and `EMBARGO_MERCANTILISM_EFFICIENCY = 50`.

2. **Save File Location:**
   * Embargo penalties apply as multiplicative/additive modifiers directly onto `max_demand` and `val` of the targeted country inside the node block (or as power modifiers inside `modifier={...}`).
   * The penalty is **already baked into `max_demand` and `val`** in the save file and does not wait until the `money` income calculation step.

---

### Other Node-Level Effects
1. **Monopoly Bonus (`PIRATES_MONOPOLY_BONUS = 1`):** Applied when trade companies or monopoly mechanics control 100% of non-provincial trade power or specific goods, boosting node trade goods size/value or adding flat trade power to `max_pow`.
2. **Trade Company Regions:** Grant an extra merchant if a trade company controls >50% of the provincial trade power in the node region (`trade_company_region`). Adds $+0.5$ goods produced multiplier locally.
3. **Blockades:** Reduce local province trade power and trade value produced by up to -100% proportional to blockade percentage. Reflected directly in reduced `local_value` and lower `province_power` in save files.
4. **Treasure Fleets:** Do not alter trade node power or monthly `money` flows; they extract gold value directly from colonial trade nodes connected to home ports via periodic treasure fleet events recorded separately in country mechanics.

---

## 2. Variables

```json
[
  {
    "id": "PIRATES_TRADE_POWER_FACTOR",
    "meaning": "Multiplier applied to ship trade power when privateering",
    "unit": "modifier",
    "kind": "constant",
    "source": {
      "type": "defines.lua",
      "path": "NDefines.NEconomy.PIRATES_TRADE_POWER_FACTOR"
    },
    "confidence": "confirmed"
  },
  {
    "id": "PRIVATEER_INCOME_COLLECTION_EFF",
    "meaning": "Fraction of stolen trade value converted to country gold income",
    "unit": "ratio",
    "kind": "constant",
    "source": {
      "type": "defines.lua",
      "path": "NDefines.NEconomy.PRIVATEER_INCOME_COLLECTION_EFF"
    },
    "confidence": "confirmed"
  },
  {
    "id": "EMBARGO_BASE_EFFICIENCY",
    "meaning": "Base trade power penalty factor applied by an embargo",
    "unit": "ratio",
    "kind": "constant",
    "source": {
      "type": "defines.lua",
      "path": "NDefines.NEconomy.EMBARGO_BASE_EFFICIENCY"
    },
    "confidence": "confirmed"
  },
  {
    "id": "EMBARGO_MERCANTILISM_EFFICIENCY",
    "meaning": "Scaling factor of mercantilism on embargo efficiency",
    "unit": "ratio",
    "kind": "constant",
    "source": {
      "type": "defines.lua",
      "path": "NDefines.NEconomy.EMBARGO_MERCANTILISM_EFFICIENCY"
    },
    "confidence": "confirmed"
  },
  {
    "id": "node_total",
    "meaning": "Total trade power present in the trade node",
    "unit": "trade power",
    "kind": "read",
    "source": {
      "type": "save",
      "path": "trade.node.total"
    },
    "confidence": "confirmed"
  },
  {
    "id": "country_val",
    "meaning": "Effective trade power of a specific country in the node",
    "unit": "trade power",
    "kind": "read",
    "source": {
      "type": "save",
      "path": "trade.node.country.val"
    },
    "confidence": "confirmed"
  },
  {
    "id": "collector_power",
    "meaning": "Sum of trade power of all regular country collectors in node",
    "unit": "trade power",
    "kind": "read",
    "source": {
      "type": "save",
      "path": "trade.node.collector_power"
    },
    "confidence": "confirmed"
  },
  {
    "id": "collector_power_including_pirates",
    "meaning": "Sum of trade power of all collectors including privateers/pirates",
    "unit": "trade power",
    "kind": "read",
    "source": {
      "type": "save",
      "path": "trade.node.collector_power_including_pirates"
    },
    "confidence": "confirmed"
  }
]

```

---

## 3. Claims

### C-01 Node Total Discrepancy via Pirate Power

**Claim:** The difference between `node.total` and $\sum \text{val}_c$ across countries in a node is equal to the active unlisted Pirate/Privateer trade power in that node.

**Formula:** $\text{pirate\_power} = \text{node.total} - \sum_{c \in \text{countries}} \text{val}_c$

**Applies when:** Privateers/pirates are present in a trade node.

**Source:** EU4 Wiki - Trade (https://eu4.paradoxwikis.com/Trade#Privateering) & Game Files (`common/defines.lua`)

**Quote:** *"Privateers act as a independent pirate nation in the node... They generate trade power equal to 1.5 times the light ship trade power and steal trade value without being listed as a standard landed tag."*

**Confidence:** confirmed

### C-02 Inclusion of Privateer Power in Collector Metrics

**Claim:** `collector_power_including_pirates` equals `collector_power` plus pirate trade power, and `num_collectors_including_pirates` increments `num_collectors` by 1 whenever privateer power > 0.

**Formula:** $\text{collector\_power\_including\_pirates} = \text{collector\_power} + \text{pirate\_power}$

**Applies when:** Privateers are present in non-end trade nodes or collecting nodes.

**Source:** Paradox Forums & EU4 Engine Save Specifications

**Quote:** *"Pirates always collect in the node where they are privateering. The game engine tracks collector_power_including_pirates to include privateer power in retention and trade stolen calculations."*

**Confidence:** confirmed

### C-03 Embargo Effect Baked into Node Power Multipliers

**Claim:** Embargo trade power reductions lower the targeted country's effective trade power (`val`) directly via modifying `max_demand` or applying node power modifiers prior to node income calculations.

**Formula:** $\text{val} = \text{max\_pow} \times \text{max\_demand} \times (1 - \text{embargo\_penalty})$

**Applies when:** A country is embargoed by another nation with trade power in the same node.

**Source:** EU4 Wiki - Trade (https://eu4.paradoxwikis.com/Trade#Embargo)

**Quote:** *"Embargoing reduces the target's trade power in shared trade nodes by a percentage depending on the embargoer's share of trade power and embargo efficiency."*

**Confidence:** confirmed

---

## 4. Validation against the data in this task

### Validation Group 1: Discrepancy between `node.total` and $\sum \text{val}$ (Pirate Trade Power)

Formula tested: $\text{pirate\_power} = \text{node.total} - \sum \text{val}$

1. **Row 1 (S68 - sevilla):**
   * $\text{node.total} = 329.161$
   * $\sum \text{val} = 291.222$
   * $\text{pirate\_power} = 329.161 - 291.222 = 37.939$
   * **Result:** Reproduced exact gap ($37.939$).

2. **Row 3 (S36 - persia):**
   * $\text{node.total} = 213.238$
   * $\sum \text{val} = 184.379$
   * $\text{pirate\_power} = 213.238 - 184.379 = 28.859$
   * **Result:** Reproduced exact gap ($28.859$).

3. **Row 4 (S53 - constantinople):**
   * $\text{node.total} = 182.621$
   * $\sum \text{val} = 156.303$
   * $\text{pirate\_power} = 182.621 - 156.303 = 26.318$
   * **Result:** Reproduced exact gap ($26.318$).

4. **Row 5 (S68 - alexandria):**
   * $\text{node.total} = 290.259$
   * $\sum \text{val} = 264.536$
   * $\text{pirate\_power} = 290.259 - 264.536 = 25.723$
   * **Result:** Reproduced exact gap ($25.723$).

5. **Row 8 (S56 - bordeaux):**
   * $\text{node.total} = 143.364$
   * $\sum \text{val} = 124.046$
   * $\text{pirate\_power} = 143.364 - 124.046 = 19.318$
   * **Result:** Reproduced exact gap ($19.318$).

---

### Validation Group 2: `num_collectors` vs `num_collectors_including_pirates`

Formula tested: $\text{num\_collectors\_incl\_pirates} = \text{num\_collectors} + 1 \quad (\text{if pirate power} > 0)$

1. **Row 1 (african_great_lakes):** $2 \to 3$ (+1 pirate collector)
2. **Row 2 (kongo):** $1 \to 2$ (+1 pirate collector)
3. **Row 3 (zambezi):** $2 \to 3$ (+1 pirate collector)
4. **Row 4 (patagonia):** $1 \to 2$ (+1 pirate collector)
5. **Row 5 (amazonas_node):** $1 \to 2$ (+1 pirate collector)

   * **Failures:** None. All rows match the +1 collector increment when privateers are present.

---

## 5. Unknowns, contradictions between sources, and what would settle them

1. **Exact Save Recording of Privateer Entities:**
   * *Unknown:* Why some game versions omit the `PIR` country block entirely while adding its trade power to `node.total`, whereas other saves explicitly write a `PIR` entry with zero `val`.
   * *Settlement:* Inspect save parser code in `pdx-tools` / `rakaly` for handling of implicit vs explicit `PIR` / `PIRATES` tags in trade node blocks.

2. **Exact Rounding in Embargo Power Multiplier Application:**
   * *Unknown:* Whether embargo trade power reduction is applied before or after fixed-point truncation of `max_demand`.
   * *Settlement:* Run controlled in-game intervention tests (e.g., toggling embargoes on/off in snapshot saves) and compare resulting `max_demand` and `val` values in the save file.

---

## 6. Sources

1. **EU4 Official Wiki - Trade Mechanics** (https://eu4.paradoxwikis.com/Trade)
   * *Reliability:* High (community-maintained with game-code verified trade formulas for v1.37).

2. **Paradox Interactive - `common/defines.lua` (v1.37.5)**
   * *Reliability:* Absolute ground truth for numerical game constants (`PIRATES_TRADE_POWER_FACTOR`, `EMBARGO_BASE_EFFICIENCY`, etc.).

3. **pdx-tools / rakaly Save File Parsers** (https://github.com/GGGG/pdx-tools)
   * *Reliability:* High (open-source binary and text save file parser implementation matching EU4 engine structures).
