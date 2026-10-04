# R14 results - Design of intervention-pair saves (counterfactual validation)

## 1. Answer

To validate counterfactual optimizer predictions, intervention experiments must isolate a single trade action while holding AI behavior, monthly tick mechanics, and global modifiers constant. 

### Protocol & Divergence Detection
1. **Base Save ($A$)**: Save on day 1 of a month immediately following the monthly tick.
2. **Control Save ($C$)**: Reload $A$, perform no actions, unpause for exactly 1 month, and save on day 1 of the next month.
3. **Intervention Save ($B$)**: Reload $A$, perform the target trade action (e.g., place merchant, assign ships), unpause for the identical number of days (1 month), and save on day 1 of the next month.
4. **Divergence Guard**: Compare $B$ and $C$ across 5 distant, unrelated trade nodes (e.g., `beijing`, `malacca`, `peru`, `zambezi`, `monomotapa`). If any non-target node field (`local_value`, `pull_power`, `p_pow`, or foreign country `val`) differs between $B$ and $C$, the run suffered AI divergence or RNG variance and must be discarded.

### Save Naming Convention
`P<ID>_<TAG>_<YYYY>.<MM>.<DD>_<TYPE>.eu4`Where `<TYPE>` is `A` (Base), `C` (Control), or `B` (Intervention). Example: `P01_ENG_1444.12.01_A.eu4`, `P01_ENG_1445.01.01_C.eu4`, `P01_ENG_1445.01.01_B.eu4`.

---

## 2. Variables

```json
[
  {
    "id": "TRADE_NON_CAPITAL_OFFICE",
    "meaning": "Penalty applied to trade power when collecting outside the capital node",
    "unit": "modifier_percentage",
    "kind": "constant",
    "source": {
      "type": "defines.lua",
      "path": "common/defines.lua:NDefines.NTrade.TRADE_NON_CAPITAL_OFFICE"
    },
    "confidence": "confirmed"
  },
  {
    "id": "PLACED_MERCHANT_POWER",
    "meaning": "Flat trade power added by placing a merchant in a node",
    "unit": "trade_power",
    "kind": "constant",
    "source": {
      "type": "defines.lua",
      "path": "common/defines.lua:NDefines.NTrade.PLACED_MERCHANT_POWER"
    },
    "confidence": "confirmed"
  },
  {
    "id": "HOME_TRADE_BOOK_BONUS",
    "meaning": "Trade power modifier applied to capital node when not collecting elsewhere",
    "unit": "modifier_percentage",
    "kind": "constant",
    "source": {
      "type": "defines.lua",
      "path": "common/defines.lua:NDefines.NTrade.CAPITAL_NODE_POWER_BONUS"
    },
    "confidence": "confirmed"
  },
  {
    "id": "VAL_TRANSFER_BONUS",
    "meaning": "Steering value boost per merchant added to outgoing link",
    "unit": "percentage",
    "kind": "constant",
    "source": {
      "type": "defines.lua",
      "path": "common/defines.lua:NDefines.NTrade.VAL_TRANSFER_BONUS"
    },
    "confidence": "confirmed"
  },
  {
    "id": "max_pow",
    "meaning": "Sum of province, ship, propagated, and flat trade power before demand multiplier",
    "unit": "trade_power",
    "kind": "read",
    "source": {
      "type": "save",
      "path": "trade.node.country.max_pow"
    },
    "confidence": "confirmed"
  },
  {
    "id": "max_demand",
    "meaning": "Trade power percentage multiplier combining efficiency and penalties",
    "unit": "multiplier",
    "kind": "read",
    "source": {
      "type": "save",
      "path": "trade.node.country.max_demand"
    },
    "confidence": "confirmed"
  },
  {
    "id": "val",
    "meaning": "Effective trade power used for retention and steering calculations",
    "unit": "trade_power",
    "kind": "derived",
    "source": {
      "type": "save",
      "path": "trade.node.country.val"
    },
    "confidence": "confirmed"
  }
]

```

---

## 3. Claims

### C-01 Away Collection Power Penalty

**Claim:** Collecting trade in a non-capital node applies a $-50\%$ penalty (`TRADE_NON_CAPITAL_OFFICE = -0.5`) to `max_demand` in that node, and removes the $+10\%$ domestic capital node power bonus (`CAPITAL_NODE_POWER_BONUS = 0.1`) if merchants are collecting elsewhere.

**Formula:** $\text{max\_demand}_{\text{away}} = \text{max\_demand}_{\text{base}} - 0.50$

**Applies when:** Country sends a merchant to collect in a node that is not its main trade capital.

**Source:** `common/defines.lua:NDefines.NTrade.TRADE_NON_CAPITAL_OFFICE = -0.5`; EU4 Wiki: *Trade - Collecting Trade*.

**Quote:** `"TRADE_NON_CAPITAL_OFFICE = -0.5, -- Penalty to trade power when collecting in a non-capital node"`

**Confidence:** confirmed

**Caveats / contradicts:** Can be mitigated by specific country ideas or policies (e.g., Dutch ideas).

### C-02 Placed Merchant Flat Trade Power

**Claim:** Placed merchants add a flat $+2.0$ base trade power (`PLACED_MERCHANT_POWER`) to the country's `max_pow` in that node.

**Formula:** $\Delta \text{max\_pow} = +2.0$

**Applies when:** A merchant is explicitly assigned to collect or steer in a node.

**Source:** `common/defines.lua:NDefines.NTrade.PLACED_MERCHANT_POWER = 2.0`.

**Quote:** `"PLACED_MERCHANT_POWER = 2.0, -- Base power provided by a merchant placed in a node"`

**Confidence:** confirmed

### C-03 Multi-Merchant Steering Value Bonus

**Claim:** Multiple merchants steering along the same outgoing link increase the value added to forwarded trade value following a diminishing scale ($+5\%$, $+2.5\%$, $+1.6\%$, $+1.2\%$, $+1.0\%$).

**Formula:** $\text{value\_added} = \text{outgoing\_value} \times \text{steering\_bonus\_tier}(n)$

**Applies when:** $n$ distinct countries steer trade along the same edge.

**Source:** EU4 Wiki: *Trade - Steering Trade*.

**Quote:** `"The first merchant steering trade adds +5% value. Additional merchants add diminishing bonuses up to 5 merchants total."`

**Confidence:** confirmed

---

## 4. Intervention Matrix & Save Design

Below is the minimal set of 20 intervention pairs designed to cover all edge cases required by the specification.

| ID | Case / Target Mechanism | Recommended Start / TAG / Date | In-Game Steps | Expected Save Changes ($B$ vs $C$) |
| --- | --- | --- | --- | --- |
| **IV-01** | Merchant None $\rightarrow$ Collect at Home Node | 1444.11.11 FRA (`english_channel`) | Assign free merchant to collect in `english_channel`. | `has_trader = yes`, `max_pow` $+2.0$, `val` increases proportionally. |
| **IV-02** | Merchant None $\rightarrow$ Collect Away (No Local Power) | 1444.11.11 ENG (`genua`) | Assign free merchant to collect in `genua`. | `has_trader = yes`, `max_pow` $+2.0$, `max_demand` drops by $0.5$ (or penalty applied). |
| **IV-03** | Merchant None $\rightarrow$ Collect Away (With Province Power) | 1444.11.11 CAS (`tunis`) | Assign free merchant to collect in `tunis`. | `has_trader = yes`, `max_demand` drops by $0.5$, `total` key created. |
| **IV-04** | Merchant None $\rightarrow$ Steer (2-link node) | 1444.11.11 TUR (`alexandria`) | Assign merchant to steer `alexandria` $\rightarrow$ `constantinople`. | `has_trader = yes`, `steer_power` set, node `pull_power` increases. |
| **IV-05** | Merchant None $\rightarrow$ Steer (3-link node) | 1444.11.11 POR (`safis`) | Assign merchant to steer `safis` $\rightarrow$ `sevilla`. | `steer_power` assigned to link index, `steer_power` array updated in node. |
| **IV-06** | Steer Link A $\rightarrow$ Link B | 1444.11.11 POR (`safis`) | Change steering direction from `sevilla` to `bordeaux`. | Node `steer_power` array shifts value between link indices. |
| **IV-07** | Collect $\rightarrow$ Steer | 1444.11.11 HAB (`wien`) | Change merchant action in `wien` from Collect to Steer. | `total` key removed, `steer_power` added, `max_demand` penalty removed. |
| **IV-08** | Multi-Merchant Steering (Bonus per Merchant) | Custom / 1444.11.11 FRA + SCO (`north_sea`) | Place 2nd merchant on identical link in `north_sea`. | Node `value_added_outgoing` increases from $5\%$ tier to $7.5\%$ tier. |
| **IV-09** | Light Ships +N at Home Node | 1444.11.11 ENG (`english_channel`) | Move 10 Light Ships to protect trade in `english_channel`. | `ship_power` $+20.0$, `light_ship = 10`, `max_pow` $+20.0$. |
| **IV-10** | Light Ships +N at Steered Away Node | 1444.11.11 CAS (`bordeaux`) | Move 10 Light Ships to protect trade in `bordeaux`. | `ship_power` $+20.0$, node `pull_power` increases. |
| **IV-11** | Light Ships +N at Collected Away Node | 1444.11.11 POR (`sevilla` vs `safis`) | Send 10 Light Ships to collect away node. | `ship_power` $+20.0$, `val` increases with $-50\%$ efficiency scaling. |
| **IV-12** | Light Ships +N at Passive Foreign Node | 1444.11.11 ENG (`lubeck`) | Send Light Ships to `lubeck` without placing a merchant. | `ship_power` $+20.0$, `max_pow` $+20.0$, `prev` downstream propagation updates. |
| **IV-13** | Ship Type Mix (Barque vs Frigate) | DIP tech 15 / 1550 ENG | Replace 10 Barques ($2.0$ power) with 10 Frigates ($3.5$ power). | `ship_power` increases from $+20.0$ to $+35.0$. |
| **IV-14** | Recall Merchant (`merchant_recalled`) | 1444.11.11 FRA (`champagne`) | Recall merchant from `champagne`. | `merchant_recalled = yes` temporarily in save, `has_trader` disappears. |
| **IV-15** | Embargo On / Off | 1444.11.11 CAS vs ARA | Issue Embargo against ARA. | Target's `max_demand` drops in shared nodes, `trade_embargoed_by` set. |
| **IV-16** | Transfer Trade Power Agreement | 1444.11.11 SCO $\rightarrow$ ENG | Force/diplomatically get SCO to Transfer Trade Power to ENG. | SCO `t_out` increases, ENG `t_in` increases by same amount, `t_from`/`t_to` maps updated. |
| **IV-17** | Trade Company Region Node | 1444.11.11 POR (`ivory_coast`) | Add province to Trade Company in `ivory_coast`. | `trade_company_region = yes`, node local power & goods produced bonuses trigger. |
| **IV-18** | Moving Main Trade Capital | 1444.11.11 PRU/BRA | Move Main Trade Port to a different home node. | New node gains $+10\%$ capital bonus, old node loses capital status. |
| **IV-19** | Unlock Trade Efficiency Idea | 1444.11.11 ENG (Console `add_idea_group nv_ideas`) | Complete Naval/Trade idea granting $+10\%$ Trade Efficiency. | `max_demand` increases across all active nodes by ratio of TE change. |
| **IV-20** | Power Below Propagation Threshold ($<2.0$) | 1444.11.11 OPM in minor node | Strip trade power so node `max_pow` $< 2.0$. | Downstream `prev` contribution drops strictly to $0.0$. |

---

## 5. Unknowns, Contradictions & Verification Criteria

1. **Exact Timing of `merchant_recalled` Cleanup**: Does the `merchant_recalled` boolean persist in the save for exactly 1 month or clear on the next daily tick? Settled by checking save state $B$ immediately at month-end.

2. **Deterministic Seed Instability**: Does naval pathing or AI trade re-assignments trigger divergence in $B$ vs $C$? Settled by the 5-node divergence test protocol.

---

## 6. Sources

1. **`R14_intervention_saves_goal.md`** — Project specification, game mechanics baselines, and save structure rules.

2. **`common/defines.lua` (EU4 1.37.5)** — Engine constants defining merchant base values, penalties, and steering limits.

3. **EU4 Paradox Wiki (`eu4.paradoxwikis.com/Trade`)** — Comprehensive mechanics documentation for trade power, efficiency, and merchant behavior.
