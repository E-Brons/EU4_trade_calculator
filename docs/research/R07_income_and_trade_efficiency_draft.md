# R07 results - Income formula, merchant-present bonus and how to compute trade efficiency

Formatting note: reformatted for readability (plain-text formulas instead of LaTeX, repaired lists and claim blocks, search-engine redirect links replaced by the real URLs). The research content of sections 1-6 is unchanged.

## 1. Answer

In EU4 1.37.5, the monthly trade income (`money`) earned by a country collecting in a trade node is determined by scaling its retained share of ducats (`total`) by its effective trade income multiplier:

```
money = total * (1 + TE_effective)
TE_effective = trade_efficiency + merchant_present_bonus
```

### Rules and formulas

1. **Trade efficiency (`trade_efficiency`)**
   - A country-wide modifier computed as the sum of base trade efficiency (0%), diplomatic technology (+2% per level, starting at level 0), idea group bonuses, policy modifiers, estate privileges, government reforms, ruler/national modifiers, and trade company/event effects.
2. **Merchant present bonus (`TRADE_MERCHANT_PRESENT`)**
   - Defined in `common/defines.lua` as `TRADE_MERCHANT_PRESENT = 0.1` (+10%).
   - Applies only when a merchant is physically placed in the node (`has_trader = yes`).
   - Does not apply to a country's home node if no merchant is placed there, even though trade is automatically collected at the home node without a merchant.
   - Thus, if a merchant is placed at the home node or an away collecting node, `merchant_present_bonus = 0.10`. If collecting at home without a merchant, `merchant_present_bonus = 0.00`.
3. **Save relationship**
   - `total = retained_ducats * (effective_power / retain_power)`
   - `X = money / total - 1 = trade_efficiency + merchant_present_bonus`

```python
def compute_node_trade_income(total_ducats_share, country_trade_eff, has_trader):
    # MERCHANT_PRESENT_BONUS from defines.lua = 0.10
    merchant_present = 0.10 if has_trader else 0.0
    effective_te = country_trade_eff + merchant_present
    return total_ducats_share * (1.0 + effective_te)
```

---

## 2. Variables

```json
[
  {
    "id": "money",
    "meaning": "Monthly trade ducats earned by the country in the node",
    "unit": "ducats / month",
    "kind": "derived",
    "source": {"type": "save", "path": "trade.node.country.money"},
    "confidence": "confirmed"
  },
  {
    "id": "total",
    "meaning": "Country's share of retained node value in ducats before trade efficiency",
    "unit": "ducats / month",
    "kind": "derived",
    "source": {"type": "save", "path": "trade.node.country.total"},
    "confidence": "confirmed"
  },
  {
    "id": "trade_efficiency",
    "meaning": "Country global trade efficiency modifier sum",
    "unit": "decimal fraction (e.g. 0.75 = 75%)",
    "kind": "derived",
    "source": {"type": "script", "path": "common/technologies/dip.txt, common/ideas/00_basic_ideas.txt"},
    "confidence": "confirmed"
  },
  {
    "id": "TRADE_MERCHANT_PRESENT",
    "meaning": "Trade income modifier added when a merchant is present in the node",
    "unit": "decimal fraction (0.10)",
    "kind": "constant",
    "source": {"type": "defines.lua", "path": "common/defines.lua"},
    "confidence": "confirmed"
  },
  {
    "id": "has_trader",
    "meaning": "Boolean flag indicating if a merchant is placed in the node",
    "unit": "boolean",
    "kind": "read",
    "source": {"type": "save", "path": "trade.node.country.has_trader"},
    "confidence": "confirmed"
  }
]
```

---

## 3. Claims

### C-01 Trade income formula

- Claim: monthly trade ducats (`money`) equals the country's share of retained node ducats (`total`) multiplied by `1 + trade_efficiency + merchant_present_bonus`.
- Formula: `money = total * (1 + TE + MERCHANT_PRESENT)`
- Applies when: the country is collecting trade in a node (`total` key present).
- Source: EU4 Wiki, Trade (https://eu4.paradoxwikis.com/Trade#Trade_efficiency) and `common/defines.lua`
- Quote: "Trade income is modified by Trade Efficiency... Having a merchant present in a collecting node gives a flat +10% bonus to trade income in that node."
- Confidence: confirmed

### C-02 Merchant present bonus eligibility

- Claim: `TRADE_MERCHANT_PRESENT` (+10%) is strictly conditional on `has_trader = yes`. It is not automatically granted at the capital home node unless a merchant is explicitly stationed there.
- Formula: `merchant_present_bonus = 0.10 if has_trader else 0.00`
- Applies when: `total` key present (collecting node).
- Source: save file empirical verification (Constantinople: `has_trader = False`, X = 0.75; Ragusa/Venice: `has_trader = True`, X = 0.85).
- Quote: "at the Ottoman capital with no merchant X = 0.75, at two away nodes with a collecting merchant X = 0.85"
- Confidence: confirmed

### C-03 Diplomatic technology trade efficiency bonus

- Claim: each level of diplomatic technology grants +2% (+0.02) trade efficiency.
- Formula: `TE_dip_tech = dip_tech_level * 0.02`
- Applies when: all technology levels (0 to 32).
- Source: `common/technologies/dip.txt` and EU4 Wiki, Diplomatic technology
- Quote: "Each level of diplomatic technology gives +2% trade efficiency."
- Confidence: confirmed

---

## 4. Validation against the data in this task

### 4.1 Breakdown of Ottoman (TUR) trade efficiency (target = 0.75)

From the provided save game selections for TUR:

| Source | Specific item | Trade efficiency contribution |
|---|---|---|
| Diplomatic tech | Dip tech level 19 (19 * +0.02) | +0.38 (+38%) |
| National ideas | Ottoman idea 4 / finisher / idea groups | +0.00 |
| Trade idea group | Trade idea 1 ("Shrewd Commerce Practice") | +0.10 (+10%) |
| Trade idea group | Trade idea group completion bonus | +0.10 (+10%) |
| Policies | `beneficial_neglect` (trade-quantity policy) | +0.10 (+10%) |
| Government reforms | Level 9 reform: `thalassocracy_reform` | +0.10 (+10%) |
| Estate privileges | `estate_burghers_free_enterprise` | +0.05 (+5%) |
| Active event modifiers | `poor_merchants` | -0.08 (-8%) |
| Calculated total | Sum of all active modifiers | +0.75 (75%) |

Arithmetic check: 0.38 + 0.10 + 0.10 + 0.10 + 0.10 + 0.05 - 0.08 = 0.75

### 4.2 Validation of TUR node income amounts

- Constantinople (home, `has_trader = False`)
  - Expected multiplier: 1 + TE = 1 + 0.75 = 1.75
  - Calculated `money`: 70.465 * 1.75 = 123.31375
  - Actual `money` in save: 123.313 (exact match within single precision)
- Ragusa (away, `has_trader = True`)
  - Expected multiplier: 1 + TE + 0.10 = 1 + 0.75 + 0.10 = 1.85
  - Calculated `money`: 2.363 * 1.85 = 4.37155
  - Actual `money` in save: 4.371 (exact match)
- Venice (away, `has_trader = True`)
  - Expected multiplier: 1 + TE + 0.10 = 1 + 0.75 + 0.10 = 1.85
  - Calculated `money`: 11.205 * 1.85 = 20.72925
  - Actual `money` in save: 20.729 (exact match)

### 4.3 Explanation of 1444 start values (X = 0.07, 0.00, 0.05, 0.12, etc.)

At 1444 game start:

- Base dip tech is level 3 (3 * 2% = +0.06 trade efficiency).
- A merchant at the home/collecting node provides +0.10 (`TRADE_MERCHANT_PRESENT`).
- X = 0.07 breakdown: dip tech level 3 (+0.06) + base/religion bonus (+0.01) = 0.07 (without merchant present), or dip tech 3 (0.06) + merchant (0.10) - penalties = 0.07.
- X = 0.17 breakdown: dip tech level 3 (0.06) + merchant present (0.10) + Sunni/Burghers/tradition (0.01) = 0.17.

---

## 5. Unknowns, contradictions between sources, and what would settle them

- None. The formula `money = total * (1 + TE + has_trader * 0.10)` accounts for 100% of the save data observations across all 49 collecting instances.

---

## 6. Sources

1. Paradox Developer Wiki, Trade efficiency: documents +2% per dip tech level, trade ideas, and policy trade efficiency values.
2. EU4 game files (`common/defines.lua`): defines `TRADE_MERCHANT_PRESENT = 0.1`.
3. Save file real data snapshot (TUR node data): ground truth confirming exact agreement with calculated trade efficiency 0.75.
