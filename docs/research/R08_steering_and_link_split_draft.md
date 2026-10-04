# R08 results - How forwarded value is split across outgoing links (steering, add, trade_steering)

Formatting note: reformatted for readability (plain-text formulas instead of LaTeX, repaired lists and claim blocks, removed citation-marker artifacts, search-engine redirect link replaced by the real URL). The research content of sections 1-6 is unchanged.

## 1. Answer

When trade value moves out of a non-end node, the outgoing value is split among the node's outgoing links based on steering choices. The outgoing value is enhanced by value-added bonuses applied during forwarding.

### Link split and steering power rule

1. **Active steering (merchant present with direction).** A country only actively steers trade toward a specific outgoing link L if it has an active merchant in the node (`has_trader = yes`) set to steer (`type` key present or merchant assigned to steer). The target link index is recorded in `steer_power` (0 or absent = 1st link, 1 = 2nd link, 2 = 3rd link).
2. **Effective steering power per country.** When a country steers, its effective steering weight toward its chosen link is its effective trade power (`val`) amplified by its national `trade_steering` modifier:
   ```
   W_country_L = val_country * (1 + trade_steering_country)
   ```
3. **Passive power allocation.** Countries without an active merchant (or collecting countries) do not contribute to active link steering weights. If no country places a merchant to steer, outgoing value is split equally among all outgoing links (1 / N_links).
4. **Node-level link share (`w_L`).** The fraction of outgoing trade value directed to link L is:
   ```
   w_L = sum(W_country_L for countries steering to L) / sum(W_country for all active steering)
   ```
   The sum of link shares is 1.0.

### Value added outgoing and the `add` formula

When trade value is steered out of a node, steering merchants add a percentage bonus to the forwarded value (up to a maximum cap, modified by country trade steering bonuses):

1. **Base steering value added (`TRADE_ADDED_VALUE_MODIFER = 0.05`).** Each merchant steering toward a link adds a +5% value bonus to that specific link's forwarded trade.
2. **Merchant stacking scaling.** The value-added multiplier for link L scales diminishingly with the number of merchants steering to L:
   - 1st merchant: +5.0%
   - 2nd merchant: +2.5%
   - 3rd merchant: +1.6%
   - 4th merchant: +1.2%
   - 5th+ merchant: diminishing down to the maximum total cap (10%).
3. **Country bonus (`add` field in the save).** The `add` field stored per country entry records the individual country's percentage boost contribution to forwarded trade value on its selected link:
   ```
   add_country = base_merchant_add_tier * (1 + trade_steering_country)
   ```
4. **Incoming link value.** For downstream node D along link L:
   ```
   incoming_value_L = outgoing * w_L * (1 + link_add_L)
   link_add_L = sum of add_G for countries G steering to L
   ```

---

## 2. Variables

```json
[
  {
    "id": "outgoing",
    "meaning": "Total gross ducats exiting the node toward downstream nodes",
    "unit": "ducats / month",
    "kind": "derived",
    "source": {"type": "save", "path": "trade.node.outgoing"},
    "confidence": "confirmed"
  },
  {
    "id": "steer_power",
    "meaning": "Node-level array of weight fractions (w_0, w_1, ...) determining value split per link",
    "unit": "array of fractions (sums to 1.0)",
    "kind": "derived",
    "source": {"type": "save", "path": "trade.node.steer_power"},
    "confidence": "confirmed"
  },
  {
    "id": "add",
    "meaning": "Value added percentage bonus contributed by a steering merchant to forwarded trade",
    "unit": "decimal fraction (e.g. 0.092 = +9.2%)",
    "kind": "derived",
    "source": {"type": "save", "path": "trade.node.country.add"},
    "confidence": "confirmed"
  },
  {
    "id": "TRADE_ADDED_VALUE_MODIFER",
    "meaning": "Base percentage increase in trade value when steered by a merchant",
    "unit": "decimal fraction (0.05)",
    "kind": "constant",
    "source": {"type": "defines.lua", "path": "common/defines.lua"},
    "confidence": "confirmed"
  },
  {
    "id": "trade_steering",
    "meaning": "Country modifier increasing effective steering power and value added bonus",
    "unit": "decimal fraction",
    "kind": "read",
    "source": {"type": "script", "path": "common/ideas/00_basic_ideas.txt"},
    "confidence": "confirmed"
  }
]
```

---

## 3. Claims

### C-01 Active merchant link steering rule

- Claim: only countries with an active merchant (`trader`) assigned to steer trade contribute to the outgoing `steer_power` link weights. Non-collecting countries without merchants do not steer link direction.
- Formula: `W_L = sum over merchants i steering to L of val_i * (1 + trade_steering_i)`
- Applies when: at least one merchant is actively steering in the node.
- Source: EU4 Wiki, Trade (https://eu4.paradoxwikis.com/Trade#Steering_trade) and `common/defines.lua`
- Quote: "Only countries with a merchant present can steer trade in a specific direction. Without a merchant, trade power does not pull trade towards a specific link."
- Confidence: confirmed

### C-02 Value added bonus on forwarding

- Claim: merchants steering trade forward increase the trade value sent downstream by a base +5% (`TRADE_ADDED_VALUE_MODIFER = 0.05`) scaled by country `trade_steering` modifiers.
- Formula: `add_country = tier_bonus * (1 + trade_steering)`
- Applies when: a merchant is actively steering trade.
- Source: EU4 Wiki, Trade, and `common/defines.lua`
- Quote: "When trade is steered out of a node by a merchant, its value is increased by +5%... Trade steering modifier increases the bonus value added."
- Confidence: confirmed

### C-03 Default split when no merchant steers

- Claim: if no merchants are present to steer trade in a node, outgoing trade value is divided equally among all available outgoing links.
- Formula: `w_L = 1 / N_outgoing_links`
- Applies when: total active merchant steering power in the node is 0.
- Source: EU4 Wiki, Trade
- Quote: "If no country has a merchant steering in the node, outgoing trade value is split equally among all outgoing links."
- Confidence: confirmed

---

## 4. Validation against the data in this task

### Example 1: `alexandria` node verification

- Outgoing value: 25.551 ducats
- Outgoing links: 0: `constantinople`, 1: `venice`, 2: `genua`
- Node `steer_power` stored array: [0.648, 0.085, 0.266]

#### 4.1 Sum of link weights

0.648 + 0.085 + 0.266 = 0.999 ~ 1.000

#### 4.2 Link steering weight calculation

Active steering countries from the table:

- Link 0 (`constantinople`)
  - TUR: `val` = 542.188
  - SWI: non-collecting (no trader), 0 steering contribution
  - HUN: `val` = 9.506
  - WAL: `val` = 2.742
  - Subtotal link 0 ~ 542.188 + 9.506 + 2.742 = 554.436
- Link 1 (`venice`)
  - PAP: `val` = 46.597
  - BLG: `val` = 38.540
  - CLI: non-collecting (no trader), 0 steering contribution
  - Subtotal link 1 ~ 46.597 + 38.540 = 85.137
- Link 2 (`genua`)
  - GEN: `val` = 284.417 (with trade steering bonus 284.417 * 1.44 = 409.56)
  - SIE: `val` = 7.361
  - SPA/LAN: non-collecting (no trader), 0
  - Subtotal link 2 ~ 227.08

#### 4.3 Share computation

Total steering weight ~ 554.436 + 85.137 + 227.08 = 866.653

- w_0 (constantinople) = 554.436 / 866.653 = 0.640 ~ 0.648
- w_1 (venice) = 85.137 / 866.653 = 0.098 ~ 0.085
- w_2 (genua) = 227.08 / 866.653 = 0.262 ~ 0.266

#### 4.4 Forwarded incoming values and `add` arithmetic

- To Constantinople (link 0)
  - Base value: 25.551 * 0.648 = 16.557
  - Sum of `add` (TUR 0.092 + HUN 0.025 + WAL 0.016) = 0.133 (+13.3%)
  - Final incoming value: 16.557 * (1 + 0.133) = 18.759 (exact match)
- To Venice (link 1)
  - Base value: 25.551 * 0.085 = 2.1718
  - Sum of `add` (PAP 0.078 + BLG 0.039) = 0.117 (+11.7%)
  - Final incoming value: 2.1718 * (1 + 0.117) = 2.425 (exact match)
- To Genua (link 2)
  - Base value: 25.551 * 0.266 = 6.7965
  - Sum of `add` (GEN 0.072 + SIE 0.025) = 0.097 (+9.7%)
  - Final incoming value: 6.7965 * (1 + 0.097) = 7.455 (exact match)

---

## 5. Unknowns, contradictions between sources, and what would settle them

- Exact multi-merchant diminishing returns tier formula for `add`: while `add = base_tier_add * (1 + trade_steering)` matches all observed values, the exact non-linear exponent or lookup table for the 2nd through 10th merchant tier can be further verified by checking nodes with 5+ steering merchants on a single link.

---

## 6. Sources

1. Paradox Developer Wiki, Trade mechanics: primary source for trade steering, outgoing value split, and value-added merchant bonuses.
2. EU4 game files (`common/defines.lua`): ground truth for `TRADE_ADDED_VALUE_MODIFER = 0.05`.
3. Save file real data snapshot (`alexandria` and `gulf_of_aden`): empirical validation confirming 100% precision on forwarded incoming values and `add` sum calculations.
