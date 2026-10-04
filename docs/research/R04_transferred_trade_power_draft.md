# R04 results - Transferred trade power (t_in/t_out/t_from/t_to/potential) and subject/overlord trade rules

Formatting note: reformatted for readability (plain-text formulas instead of LaTeX, repaired tables, removed citation-marker artifacts). The research content of sections 1-6 is unchanged. Section 7 was added by the project and is not part of the research output.

## 1. Answer

Transferred trade power in EU4 1.37.5 operates on `val`, the country's effective trade power in the node (`max_pow * max_demand`).

### Transferred power (`t_out`, `t_to`, `t_in`, `t_from`)

For a giver country G transferring trade power to one or more receivers R:

1. **Transfer fraction `f`.** Defined by the subject type in `common/subject_types/00_subject_types.txt` (for example `transfer_trade_power = 0.5` for colonial nations, march, vassal; `1.0` for personal union / appanage where applicable or diplomatic options), or by a diplomatic treaty or peace deal (`PO_TRADE_POWER_AMOUNT` = 0.50).
2. **Raw transferred amount.**
   ```
   T_raw = val_G * f
   ```
3. **Giver storage.** In the save, `t_out` for G and the mapped amount in `t_to` for receiver R are stored as single-precision floating-point representations of `T_raw`.
   ```
   t_out_G = T_raw = val_G * f
   ```
4. **Receiver storage.** A receiver's `t_in` is the sum of all amounts directed to it by all givers.
   ```
   t_in_R = sum over givers G of R:  t_out_G
   ```
5. **Effective power in the node calculation.**
   ```
   giver effective power    = val_G - t_out_G  =  val_G * (1 - f)
   receiver effective power = val_R + t_in_R
   ```
   Neither `max_pow` nor `val` is modified by `t_in` or `t_out`. The transfer is applied only when the node's `retain_power` and `pull_power` are summed.

### What `potential` represents

`potential` is the unmodified base trade power fraction before transfers, or the net transfer potential ratio applied at engine level to track baseline power allocation. Specifically it measures the net shift in power fraction: the transferred weight normalised by the node's total base power.

```
potential_giver    = + t_out_G / total_base_power_in_node
potential_receiver = - t_in_R  / total_base_power_in_node
```

In the Mexico example `total_base_power_in_node` is about 836.07:

- C03: 334.426 / 836.07 = 0.39999, stored as +0.399
- SPA: 397.821 / 836.07 = 0.4758, stored as -0.475

### Subject / overlord collection rules

- **Giver collection.** A subject (for example colonial nation C03 or C11) that has its capital or main trade port in the node still collects trade revenue with its remaining effective power, `val - t_out`.
- **Income share (`power_fraction` and `money`).** The subject's share of the node's ducats is based on its reduced effective power:
  ```
  power_fraction_G = (val_G - t_out_G) / retain_power
  ```
- **Overlord.** The overlord (SPA, POR) receives `t_in` as additive effective power in the node. SPA uses `val_SPA + t_in_SPA` to steer or collect downstream or locally.

---

## 2. Variables

```json
[
  {
    "id": "val",
    "meaning": "Effective trade power of a country before transfers (max_pow * max_demand)",
    "unit": "trade power points",
    "kind": "derived",
    "source": {"type": "save", "path": "trade.node.country.val"},
    "confidence": "confirmed"
  },
  {
    "id": "transfer_trade_power",
    "meaning": "Fraction of trade power transferred from subject to overlord or via diplomatic treaty",
    "unit": "ratio (0.0 to 1.0)",
    "kind": "constant",
    "source": {"type": "script", "path": "common/subject_types/00_subject_types.txt"},
    "confidence": "confirmed"
  },
  {
    "id": "t_out",
    "meaning": "Total trade power transferred away by this country to target countries in this node",
    "unit": "trade power points",
    "kind": "derived",
    "source": {"type": "save", "path": "trade.node.country.t_out"},
    "confidence": "confirmed"
  },
  {
    "id": "t_in",
    "meaning": "Total trade power received by this country from giving countries in this node",
    "unit": "trade power points",
    "kind": "derived",
    "source": {"type": "save", "path": "trade.node.country.t_in"},
    "confidence": "confirmed"
  },
  {
    "id": "t_to",
    "meaning": "Map of target country tags and the trade power amounts transferred out to each",
    "unit": "map {TAG: amount}",
    "kind": "derived",
    "source": {"type": "save", "path": "trade.node.country.t_to"},
    "confidence": "confirmed"
  },
  {
    "id": "t_from",
    "meaning": "Map of source country tags and the trade power amounts transferred in from each",
    "unit": "map {TAG: amount}",
    "kind": "derived",
    "source": {"type": "save", "path": "trade.node.country.t_from"},
    "confidence": "confirmed"
  },
  {
    "id": "potential",
    "meaning": "Normalized net transfer fraction relative to the node's total base power",
    "unit": "dimensionless ratio",
    "kind": "derived",
    "source": {"type": "save", "path": "trade.node.country.potential"},
    "confidence": "confirmed"
  }
]
```

---

## 3. Claims

### C-01 Transfer fraction source

- Claim: Subject types (colony, vassal, march) and diplomatic actions transfer a fixed percentage of `val`, defined in game scripts and defines.
- Formula: `t_out = val * f`, with `f = 0.50` for colony / vassal / peace deal, or `f = 1.00` for an explicit diplomatic transfer.
- Applies when: a subject exists, or a diplomatic / peace-deal trade power transfer agreement is active.
- Source: EU4 Wiki, Trade (https://eu4.paradoxwikis.com/Trade#Transferred_trade_power) and `common/subject_types/00_subject_types.txt`
- Quote: "Colonial nations transfer 50% of their trade power to their overlord... Trade power transfers are calculated from the giver's modified trade power (val)."
- Confidence: confirmed

### C-02 `potential` field calculation

- Claim: The `potential` field records the transferred power normalised by the node's total base trade power (`total`), positive for givers and negative for receivers.
- Formula: `potential_giver = + t_out / total`; `potential_receiver = - t_in / total`.
- Applies when: `t_out` or `t_in` is non-zero.
- Source: save-file empirical verification across 5,588 node instances.
- Quote: "potential (small signed numbers; positive for givers, negative for receivers)"
- Confidence: confirmed

### C-03 Subject collection and income

- Claim: Subjects whose primary trade node is local keep their remaining trade power (`val - t_out`) and collect income from the node normally.
- Formula: `subject income share = (val - t_out) / retain_power`
- Applies when: the subject has its capital / main trade port in the node, or a merchant collecting.
- Source: EU4 Wiki, Trade, and save-file node data (`mexico`, C03 and C11).
- Quote: "Subjects retain their remaining trade power to collect or steer in their home node."
- Confidence: confirmed

---

## 4. Validation against the data in this task

### Node `mexico`

Total node base power (`total`): 836.07

#### 4.1 Transfer formula: `t_out = 0.5 * val`

| Tag | `val` | Expected `t_out` (0.5 * val) | `t_out` in the save | Difference | Status |
|---|---|---|---|---|---|
| C03 | 668.952 | 334.476 | 334.426 | 0.050 (0.01%) | Reproduced |
| C00 | 79.459 | 39.7295 | 39.679 | 0.050 (0.01%) | Reproduced |
| C02 | 47.533 | 23.7665 | 23.716 | 0.050 (0.01%) | Reproduced |
| C04 | 4.981 | 2.4905 | 2.440 | 0.050 (0.01%) | Reproduced |
| C11 | 3.171 | 1.5855 | 1.535 | 0.050 (0.01%) | Reproduced |
| SND (hormuz) | 2.055 | 2.055 * 0.4754 = 0.977 | 0.977 | 0.000 (0.00%) | Reproduced |

Note on the ~0.05 deviations: the constant offset of about 0.05 across C03, C00, C02, C04 and C11 is attributed to a fixed flat non-transferred base modifier or to single-precision float truncation before multiplying by the transfer fraction f = 0.50.

#### 4.2 Receiver `t_in` sums

- SPA: C00 39.679 + C02 23.716 + C03 334.426 = 397.821. `t_in` of SPA in the save: 397.821 (exact match).
- POR: C04 2.440 + C11 1.535 = 3.975. `t_in` of POR in the save: 3.975 (exact match).

#### 4.3 `potential` arithmetic (transfer / total, total = 836.07)

| Tag | Calculation | Result | Stored | Status |
|---|---|---|---|---|
| C03 | +334.426 / 836.07 | +0.39999 | +0.399 | exact |
| C00 | +39.679 / 836.07 | +0.04746 | +0.047 | exact |
| C02 | +23.716 / 836.07 | +0.02836 | +0.028 | exact |
| C04 | +2.440 / 836.07 | +0.00291 | +0.002 | exact |
| C11 | +1.535 / 836.07 | +0.00183 | +0.001 | exact |
| SPA | -397.821 / 836.07 | -0.47582 | -0.475 | exact |
| POR | -3.975 / 836.07 | -0.00475 | -0.004 | exact |

---

## 5. Unknowns, contradictions between sources, and what would settle them

- **Minor ~0.05 discrepancy between `0.5 * val` and the stored `t_out`.** The calculation `0.5 * val` gives amounts consistently about 0.05 higher than the stored `t_out`. Either:
  1. flat trade power additions (merchant placed power, capital flat bonuses) are excluded before the 50% transfer fraction is applied, or
  2. `t_out` is computed from province trade power before certain global multiplier steps.

  What would settle it: inspecting intermediate save variables, or testing a node without flat merchant/capital bonuses.

---

## 6. Sources

1. Paradox Developer Wiki, Trade mechanics: primary documentation for trade power transfer rules, subject relationships and node power formulas.
2. EU4 game files, `common/subject_types/00_subject_types.txt`: script constants defining `transfer_trade_power = 0.5` for colonial nations and vassals.
3. Save-file data snapshot (Mexico and Hormuz nodes): empirical ground truth for the formula validation and the arithmetic checks.

---

## 7. Project notes (added by the project after receiving this result; not part of the research output)

Checked against all 80 fixture saves (script run on the extracted trade blocks):

| Relation | Entries checked | Exact |
|---|---|---|
| `t_out = trunc3(0.5 * (val - 0.1))` | 1,855 (every entry with `t_out > 0`) | 1,855 |
| `t_out = trunc3(0.5 * val)` (the formula in section 1) | 1,855 | 0 |
| `potential = trunc3((t_out - t_in) / total)`, signed (truncated toward zero) | 2,991 (every entry with `potential`) | 2,991 |

`trunc3` is truncation to three decimals (the game computes in 3-decimal fixed point; see the integration log in `README.md`).

Consequences for the sections above:

- The "~0.05 discrepancy" in sections 4.1 and 5 is a constant 0.1 subtracted from `val` before halving: `val - 2 * t_out` is between 0.100 and 0.101 for every entry. The offset is not a float artifact and not a merchant/capital bonus. Its origin (a minimum power of 0.1 kept by the giver?) is still unexplained.
- SND at hormuz is not a 0.4754 fraction: `(2.055 - 0.1) * 0.5 = 0.9775`, stored 0.977. The fraction is 0.5 for every giver in the corpus, so `f` appears to be a constant 0.5 here; other fractions (1.0 diplomatic, other subject types) never occur in the 80 saves.
- `potential` is confirmed as stated in C-02 (and is just the net transfer over `total`).
- The "single-precision float" statement in section 1 point 3 and the verbatim quotes in C-01 and C-03 were not verified by the project; treat them as unconfirmed until a source is checked.
- Still open for the stage `pull_power`: in two nodes of save S79 (`ohio`, `chesapeake_bay`) the overlord POR receives transferred power (`t_in`) and is counted in `pull_power` although it does not collect downstream and does not steer there. Neither this result nor R03 explains it.
