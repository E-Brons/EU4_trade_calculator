# R03 results - Which countries' power counts in pull_power (and why some non-collectors are excluded)

## Completion status (read first)

| Stage | Status |
|---|---|
| Find a documented rule for who is counted in `pull_power` | **DONE** - wiki states it explicitly (C-01..C-03) |
| Map the rule to save fields | **PARTIAL** - needs a per-country "collects somewhere" set and the node graph; both are in the saves (`total` key, `has_capital`, 159 links) |
| Explain the worked examples `xian` and `hormuz` | **PARTIAL** - arithmetic of both examples verified (section 4); the exclusion of YEM (hormuz) and the inclusion of TRS (hormuz) is explained by the rule using only data in the task files + a third-party graph; exclusion of MNG/BNG (xian) and SND (hormuz) is **NOT VERIFIABLE** with the provided data (home nodes missing) |
| Explain the 40-row labelled sample | **NOT DONE** - needs each country's collecting nodes in that save and the graph; data not in this task. 12 rows have `has_trader` yet are neither steering nor collecting: **UNKNOWN** what that means |
| Explain the 412 unsolved + 99 ambiguous nodes | **NOT DONE** - no data; candidate causes listed in section 5 are labelled as hypotheses only |
| Meaning of `already_sent` | **UNKNOWN** (no source found); one observation in the sample is reported in section 4 |
| Forwarding when nobody steers | **DONE** (wiki, C-05) |

## 1. Answer

```
# game 1.37.5; all quotes below are from the official wiki (sections last verified 1.25-1.30, not re-verified for 1.37.5)

collect_nodes(c) = { n : c collects in n }            # = {c.main_trade_node (automatic)} U {n : c has a merchant with action COLLECT in n}
                                                       # save reading (inferred): entry has key `total`  OR  entry has `has_capital`
downstream*(n)   = all nodes reachable from n by >=1 outgoing links (any number of hops)

transferring(c,n) =  steers(c,n)                                              # merchant present, action TRANSFER (save: key `type`)
                  OR ( NOT collects(c,n)  AND  collect_nodes(c) ∩ downstream*(n) != {} )   # "collecting in a node somewhere downstream"

pull_power(n)    = SUM over c with transferring(c,n) of ( val(c,n) - t_out(c,n) + t_in(c,n) )
retain_power(n)  = SUM over c with collects(c,n)     of ( val(c,n) - t_out(c,n) + t_in(c,n) )     # verified in project data
excluded(c,n)    = NOT collects(c,n) AND NOT steers(c,n) AND collect_nodes(c) ∩ downstream*(n) == {}
                   # "doesn't count the countries which have their trade capital upstream"
                   # such a country's power is still in node.total, but in neither retain_power nor pull_power
retention(n)     = retain_power / (retain_power + pull_power)                                  # verified in project data
```

Consequences (all from the quoted wiki text):
- Exclusion is a property of the pair (country, node), not of the country: it depends on whether the country collects anywhere downstream of THIS node. That is why TUR can be excluded at 4 nodes and included at 17.
- Having a merchant does not matter by itself; only the merchant's *action* does (steering = transferring; collecting = retain).
- Province power vs propagated-only (`prev`) power does not matter: both count as the country's power in the node.
- Steering countries are always counted (matches the project observation "steering countries always included").
- End nodes have no outgoing links, so nobody can be transferring there; `pull_power` is absent (matches the data).
- `t_out`/`t_in` move power between countries before the status test; evidence: hormuz arithmetic (section 4) treats SND's excluded amount as `val - t_out`.

When nobody steers: the pulled value is split **equally** among the outgoing links that are eligible (see C-05); eligibility = at least one transferring country has power in both nodes.

## 2. Variables

```json
[
 {"id":"collect_nodes","meaning":"set of nodes where the country collects (main trade node + merchant COLLECT nodes)","unit":"set of node ids","kind":"derived","source":{"type":"save","path":"entries with key `total` or `has_capital`, per country across trade.node[]"},"confidence":"inferred (field mapping); rule itself confirmed"},
 {"id":"downstream_closure","meaning":"nodes reachable via outgoing links","unit":"set","kind":"derived","source":{"type":"script","path":"common/tradenodes/00_tradenodes.txt (159 links); also trade.node[].definitions in save"},"confidence":"confirmed (structure)"},
 {"id":"steers","meaning":"merchant present with action transfer","unit":"bool","kind":"read","source":{"type":"save","path":"country entry key `type`"},"confidence":"per project reading"},
 {"id":"val","meaning":"effective power","unit":"power","kind":"read","source":{"type":"save","path":"entry.val"},"confidence":"confirmed"},
 {"id":"t_out","meaning":"power given away","unit":"power","kind":"read","source":{"type":"save","path":"entry.t_out"},"confidence":"confirmed (project)"},
 {"id":"t_in","meaning":"power received","unit":"power","kind":"read","source":{"type":"save","path":"entry.t_in"},"confidence":"confirmed (project)"},
 {"id":"already_sent","meaning":"unknown","unit":"unknown","kind":"unknown","source":{"type":"save","path":"entry.already_sent"},"confidence":"UNKNOWN"},
 {"id":"merchant_action","meaning":"action of each merchant (collect/transfer) incl. merchants that are neither","unit":"enum","kind":"unknown","source":{"type":"save","path":"country.merchants.envoy[] (per R09 task; format not verified)"},"confidence":"UNKNOWN"}
]
```

## 3. Claims

### C-01 Effective power counts only collecting or transferring countries
- Claim: countries whose trade capital is upstream are not counted.
- Source: https://eu4.paradoxwikis.com/Trade ("Collecting trade")
- Quote: "The effective trade power in a node only counts the trade power of the countries which collect or which transfer downstream, but it doesn't count the countries which have their trade capital upstream."
- Confidence: confirmed (wiki text)
- Caveats: "trade capital upstream" is only the common case; the precise condition is C-02.

### C-02 Definition of "transferring"
- Claim: steering OR (not collecting here AND collecting somewhere downstream, any distance).
- Source: https://eu4.paradoxwikis.com/Trade ("Transferring trade")
- Quote: "A country with trade power in a node who either has a merchant present and set to steer, or is not collecting there but is collecting in a node somewhere downstream (no matter how many hops away), is transferring."
- Confidence: confirmed (wiki text)
- Caveats: "collecting" presumably includes the automatic main-trade-city collection (C-03), not documented explicitly here.

### C-03 Merchant-less countries
- Claim: without a merchant, a country collects only at its home node; elsewhere it pulls only if the node is upstream of a node where it collects; otherwise its power does not affect the flow.
- Source: https://eu4.paradoxwikis.com/Trade ("Trade with no merchant")
- Quote: "In non-home nodes that are not upstream from any nodes where the country is collecting trade, their trade power does not affect the flow of trade. It still propagates upstream if the country has at least 10 provincial trade power."
- Quote 2: "In all other nodes, trade power is used to pull trade forward, increasing the share of trade value transferred."
- Confidence: confirmed (wiki text)
- Caveats: "at least 10 provincial trade power" conflicts with `TRADE_PROPAGATE_THRESHOLD = 2` in the project notes (that belongs to R05).

### C-04 All transferring countries pool power to pull
- Source: https://eu4.paradoxwikis.com/Trade ("Pulling trade value forward")
- Quote: "All countries transferring trade pool their trade power to pull trade out of the node."
- Quote 2: "Outgoing trade value = Total trade value in node × Σ Trade power of countries transferring / (Σ Trade power of countries transferring + Σ Trade power of countries collecting)" (formula in the page, as rendered text)
- Confidence: confirmed (wiki), consistent with the verified `retention` relation.

### C-05 Direction when nobody steers
- Source: https://eu4.paradoxwikis.com/Trade ("Steering trade")
- Quote: "In other words, if no one is steering in any direction, trade value is divided equally between all outgoing nodes."
- Quote 2: "But in this situation a downstream node will only be considered for transferring trade value if someone is transferring between those nodes, i.e. they have trade power in both of them."
- Quote 3: "Countries that are not steering with a merchant have no influence whatsoever over the direction in which trade flows."
- Confidence: confirmed (wiki)
- Caveats: how this is encoded in the node's `steer_power = [w0, w1, ...]` is R08.

### C-06 Graph facts used for the checks (third-party)
- Claim: hormuz -> basra only; gulf_of_aden -> zanzibar, alexandria, hormuz; gujarat -> gulf_of_aden, hormuz, zanzibar; xi'an -> beijing, yumen; beijing -> yumen; hangzhou -> xi'an, beijing, malacca.
- Source: https://eu4commands.com/trade-node
- Quote: "Hormuz | 33 | No | No | Basra" ; "Gulf of Aden | 55 | No | No | Zanzibar Alexandria Hormuz" ; "Xi'an | 25 | Yes | No | Beijing Yumen"
- Confidence: reported (third-party list; the project has the real graph from `common/tradenodes`; use that, not this)
- Caveats: basra -> {aleppo, persia} is taken from the downstream list of basra in the R05 task table, not from this source.

## 4. Validation against the data in this task

**Arithmetic of the worked examples (reproduced):**
- xian: non-collecting effective sum 28.841+20.135+7.737+5.963+4.192+3.291 = 70.159. Excluding MNG 7.737 + BNG 5.963 = 13.700 -> 56.459 = `pull_power`. retain 112.619+78.833 = 191.452. retention = 191.452/(191.452+56.459) = 0.7723.
- hormuz: 411.646 - (YEM 47.378 + SND 1.078) = 411.646 - 48.456 = 363.190 = `pull_power`. (SND: val 2.055 - t_out 0.977 = 1.078.)

**Rule applied to rows where the data in this task is enough:**
- hormuz / YEM -> excluded: YEM collects at gulf_of_aden (R08 table), which is *upstream* of hormuz (C-06); R08's alexandria table lists no YEM, so YEM does not collect at alexandria either; hormuz's downstream (basra -> aleppo/persia ...) shows no YEM collecting in the task data. **Consistent** (not proven: YEM collecting at some other downstream node is not excluded by the data given).
- hormuz / TRS -> included (province 3.947, no merchant): TRS collects at persia (R02 table: TRS persia, collecting away); persia is downstream of basra (R05 table row "basra IRQ" lists persia as downstream D) and basra is downstream of hormuz (C-06). So TRS collects downstream of hormuz -> transferring. **Consistent.**
- xian / QIC steering -> included. **Consistent** (rule C-02).
- xian / RUS included, SHY included, TRS included; xian / MNG, BNG excluded: **NOT VERIFIABLE** - needs the home node / collecting nodes of RUS, SHY, MNG, BNG in that save (not in the task). The R05 table gives MNG province power at chengdu/canton/xian/burma and BNG at canton/burma, which is compatible with homes upstream of xian, but compatibility is not a test.
- sample S59 yumen / QNG excluded (trader, already_sent): compatible with a Qing home at beijing, which is upstream of yumen (beijing -> yumen, C-06) **if** Qing collects nowhere downstream of yumen; not verifiable here.
- sample S70 ivory_coast / POR excluded: **POSSIBLE CONTRADICTION**. R05 lists sevilla as a downstream node of ivory_coast. If POR's main trade node in S70 is sevilla (Lisbon's node - not verified here) then the rule predicts POR is included, but the label says excluded. Needs POR's `has_capital` node in S70. Do not treat as refutation until checked.

**Observation from the 40-row sample (not a rule):** all 5 rows with `already_sent` set (S59 QNG, S70 POR, S67 PRU, S36 KON, S71 NOR) are labelled EXCLUDED; no INCLUDED row has `already_sent`. This conflicts with the task statement that `already_sent` "occurs on both sides" - check on the full data. Meaning of `already_sent`: **UNKNOWN**.

**Rows with a merchant that is neither steering nor collecting (UNKNOWN):** LIT, NAG(included), GOL x2, ANZ, AIR, ZUN, PRU, NOR, POR, QNG, MOR carry `has_trader` but no `type`/`total` per the table labels. The wiki knows only two merchant actions (collect, transfer), so these entries contradict the wiki or the labelling (e.g. a merchant that collects but gets no `total` because the node retains 0; a merchant still traveling; or `has_trader` meaning something else). **UNKNOWN.**

**Failures / unexplained:** the 38 other sample rows cannot be tested (no collecting-node data); 412 unsolved and 99 ambiguous nodes cannot be tested.

## 5. Unknowns, contradictions between sources, and what would settle them

All items below are open; none is guessed.

1. **Apply the rule to all 5,588 nodes (NOT DONE).** Procedure: build `collect_nodes(c)` per save from entries with `total` or `has_capital`; compute `downstream*` from the 159 links; evaluate `excluded(c,n)`; compare predicted vs the project's solved exclusions (2,729 unique-subset-sum cases). This is cheap for the project (data and graph are local) and settles the whole task.
2. **Merchants that are neither steering nor collecting** (section 4). Settle: inspect `country.merchants.envoy[]` actions for those countries in the same saves (R09 lists this field).
3. **Meaning of `already_sent`.** Settle: correlation with exclusion over all saves; compare to wiki term "transfer"; R14 pair (steer vs collect) may show when it appears.
4. **The 412 unsolved nodes.** Hypotheses only (to test, not conclusions): (a) steering countries may be excluded in some cases; (b) transferred power (`t_in`) may take the *receiver's* status while `t_out` is removed from the giver's - the project formula `val - t_out + t_in` is verified only for the totals; (c) pirates/other non-listed entries in the same node. No source found for any of these.
5. **Does "collecting" in C-02 include the automatic main-trade-city collection?** Wiki C-03 implies yes ("In the country's home node, the country will collect trade") but does not say so for C-02. Settle: step 1 above, with and without home nodes in `collect_nodes`.
6. **Trade companies, subjects, trade leagues, war/embargo:** no source says any of them changes pull membership. Not tested.
7. **Version:** wiki sections last verified 1.25-1.30; 1.37.5 not confirmed.

## 6. Sources (ranked)

1. https://eu4.paradoxwikis.com/Trade - official wiki, partly outdated banners; the only source with an explicit membership rule.
2. https://eu4commands.com/trade-node - third-party node/flow list; used only for the checks in section 4; the project's own `common/tradenodes` file is authoritative.
3. Task data (xian, hormuz, R02/R05/R08 tables, 40-row sample) - primary evidence; insufficient for the full test.
