# Research (to be run by an internet-enabled AI, e.g. GitLab Duo/Copilot)

Each topic `Rxx` is researched in rounds. A round never overwrites the previous one; the files pile up and the last one is `final`.

## File convention

| File | Role | Written by |
|---|---|---|
| `Rxx_<topic>_goal.md` | The question, the project context, the rules and the required answer format. Self-contained. Never edited after the first draft is received (fix typos only). | us |
| `Rxx_<topic>_draft.md` | The first answer to the goal, saved exactly as the AI produced it (formatting repairs only). A draft is **not trusted** until it is reviewed. | AI |
| `Rxx_<topic>_request_<i>.md` | Follow-up `i` (1, 2, ...): a list of specific gaps/errors found when reviewing the draft (or the previous response), each with the evidence (the data row, the contradiction, the missing field) and exactly what is asked. | us |
| `Rxx_<topic>_response_<i>.md` | The AI's answer to `request_<i>`, using the same required format as the goal (only the points asked). | AI |
| `Rxx_<topic>_final.md` | Consolidated answer once every open point is answered or explicitly `UNKNOWN`. Same format as the goal, plus section 7 (provenance). **This is the only file integrated into the spec and code.** | us (merged from draft + responses) |

Example for topic R10: `goal` -> `draft` -> `request_1` -> `response_1` -> `request_2` -> `response_2` -> `final`.

### Rules

1. **Review before asking.** Every draft/response is reviewed against its goal: required sections present, claims sourced with verbatim quotes, validation uses the real data tables (not invented rows), no contradiction with the verified facts in the goal or with other topics. The review findings become the next `request_<i>`.
2. **A request is self-contained enough to run alone.** It starts with the files to read (`goal`, `draft`, earlier `request`/`response` files, by path). If the AI cannot read the repository, paste those files in. It lists numbered points (`Q1`, `Q2`, ...), each with: what is wrong or missing, the evidence, and the expected form of the answer. It repeats the goal's rules (source + quote + confidence, `UNKNOWN` instead of a guess).
3. **A response answers only the numbered points** and keeps the numbering, so `final` can map each point to its answer.
4. **`final` is written when no point is open.** Every claim in it names where it came from (draft or `response_<i>` + point number). Anything still unanswered stays as `UNKNOWN` with what would settle it (often an intervention pair, see R14).
5. **Contradictions with data win.** If a source claim disagrees with the save corpus, the data is right and the claim is recorded as rejected in `final`, with the evidence.
6. **Status of a topic = its newest file** (see table below). Only `final` unblocks calculation work; code may use a `draft` only for exploration.
7. Files are append-only and numbered monotonically; never renumber or delete a request/response.

### Format of `final` (addition to the goal's template)

The goal's sections 1-6 (Answer, Variables JSON, Claims, Validation, Unknowns, Sources) plus:

```
## 7. Provenance
| Item | Source file | Point |
|---|---|---|
| C-01 | Rxx_..._response_1.md | Q2 |
| Variable X | Rxx_..._draft.md | - |
## 8. Rejected claims
(claim, where it came from, the data that contradicts it)
```

### Formatting of AI output

Save the AI's text unchanged except for repairs that do not alter wording or numbers: remove an outer ```` ```markdown ```` wrapper, balance code fences, fix broken tables and list nesting, remove citation artifacts such as `[cite: 1]`, render links.

## Automation (CI research agent)

`.github/workflows/research.yml` runs on a push to any branch (not tags) that changes something under `docs/research/**`, and only then. `.github/scripts/research_pending.py plan` decides what is waiting for the agent:

| Newest file of a topic | The agent writes |
|---|---|
| `goal` | `<topic>_draft.md` |
| `request_<i>` (i <= 4) | `<topic>_response_<i>.md` |
| `draft`, `response_<i>`, `final` | nothing (review or integration is the next step, done by a human/Claude) |

The agent gets the README plus the goal, draft, earlier requests/responses and the newest request as its prompt, its output is checked (non-empty markdown, outer code fence removed) and only new `*_draft.md` / `*_response_<i>.md` files are committed by the bot with `[skip ci]`. Goals, requests, finals and this README are never touched by CI. Needs the repository secret `COPILOT_TOKEN`. A target file that already exists is never regenerated, so re-pushing does not repeat work; to redo a response, write a new `request_<i+1>`.

## Topics

Tasks are independent and can run in parallel. Priority: R01-R04 and R06-R08 unblock the calculation (they are the stages that still fail against the saves); R05, R09-R12 refine and document; R13 is optional; R14 designs the counterfactual fixture saves the user will make in-game.

| Topic | What it answers | Status |
|---|---|---|
| R01 power_multiplier | What determines max_demand (the multiplier from raw power to effective power) | draft, integrated, `request_1` ready |
| R02 away_collection_penalty | The penalty for collecting away from the capital node (TRADE_NON_CAPITAL_OFFICE = -0.5) | draft, integrated, `request_1` ready |
| R03 pull_power_composition | Which countries' power counts in pull_power (and why some non-collectors are excluded) | draft, integrated, final-ready (no request needed) |
| R04 transferred_trade_power | Transferred trade power (t_in/t_out/t_from/t_to/potential) and subject/overlord trade rules | draft, integrated, `request_1` ready |
| R05 trade_power_propagation | Trade power propagation between nodes (the prev field) | draft, `request_1` ready |
| R06 flat_power_extras | Flat power additions: capital, merchants, placed_merchant_power, modifiers | draft, `request_1` ready |
| R07 income_and_trade_efficiency | Income formula, merchant-present bonus and how to compute trade efficiency | draft, `request_1` ready |
| R08 steering_and_link_split | How forwarded value is split across outgoing links (steering, add, trade_steering) | draft, `request_1` ready |
| R09 save_field_dictionary | Meaning of every trade-block field in an EU4 save | draft, `request_1` ready |
| R10 embargo_privateers_transfers_misc | Embargo, privateers/pirates and why node total can differ from the sum of country val | draft, `request_1` ready |
| R11 ships_and_trade_power | How assigned light ships become trade power in a node | draft, `request_1` ready |
| R12 monthly_tick_timing | Order and timing of the monthly trade tick versus the values stored in a save | draft, `request_1` ready |
| R13 province_trade_power | Per-province trade power and trade value (optional, lower priority) | draft, `request_1` ready |
| R14 intervention_saves | Design of intervention-pair saves (counterfactual validation) | draft, `request_1` ready |

All of R01-R14 have now been reviewed under rule 1. `request_1` files exist for every topic except R03, which is final-ready: its rule is already integrated and verified in code, so only its `final` document is still to be written. For R10-R14 the requests follow the review below; the next step is to give each one to the AI (with the files it names) and save the answer as `Rxx_<topic>_response_1.md`.

### Open points found in the review of R10-R14 (seed for each `request_1`)

- **R10**: validation is circular (gap computed as total - sum(val)); pirate power in `retain_power`/`pull_power` not answered; TUR embargo case not addressed; embargo formula has no source; the second data table contradicts C-02 (total = sum(val) there).
- **R11**: arithmetic needs 67 early frigates, TUR owns 66; max 3.675 power/ship unexplained; "modifiers included in `ship_power`" vs validation with bare base values; missing per-node cap, 98 vs 100 ships, port/org limits, flagship modifiers, how assignment is stored, rule for one more ship; C-02 quote is copied from our task.
- **R12**: explains the 4.5% link mismatch with `value_added_outgoing != outgoing` although the goal says they are equal there; validation uses invented nodes A-E; day of month for country modifiers not answered.
- **R13**: no validation on real data (invented cases); trade value with and without /12; caravan formula (dev x 3, cap 50) doubtful; `province_power` = sum of `trade_power` asserted, not tested; goods size, trade company region and merchant republic bonuses missing.
- **R14**: missing cases (inland ships, embargo off, transfer off), control design, "what to record", checklist, determinism answer; errors: FRA home node is champagne, PRU absent in 1444, away penalty additive vs the x0.5 used in R02, IV-12 claims ships change `prev`, date 1444.12.01 vs 1444.11.11.

## Integration log (what each `final` changed in `backend/app/trade/calc.py`)

Entries below predate the convention and refer to drafts; they are kept as written. New entries are added only when a `final` is integrated.

| Result | Integrated | Effect on the corpus (80 saves) | Still open |
|---|---|---|---|
| R03 pull_power | `rule_is_pulling`: a country pulls where it steers, or does not collect there but collects somewhere downstream; entries that carry only `t_in`/`t_out` count with val 0 | `pull_power` wrong in 57.8% of nodes -> 0.04% (2 of 5,588) | the two S79 nodes where the overlord POR receives transfers; merchants with `has_trader` but no recorded action |
| R02 away penalty | `rule_away_adjustment`: max_demand x 0.5 when the decision flips a country to/from collecting away (hypotheses for what-if only; snapshots cannot test it) | none on snapshots (unchanged decisions leave the recorded value) | needs IV-02/IV-08 intervention pairs; value of `reduced_trade_penalty_on_non_main_tradenode` |
| R01 multiplier | structure recorded in the R01 draft; `max_demand` stays an observed input (it exists for every country at every node in the save, so what-ifs can read it) | stage `multiplier` stays NOT IMPLEMENTED | cap composition (global_trade_power etc.), embargo factor (needs `trade_embargoed_by` + embargoer power), domestic test (needs `top_provinces`), home-bonus effect |
| R04 transfers | stage `transfers`: `t_out = fx(0.5*(val-0.1))` (the 0.1 offset was found by the project; the result's flat ~0.05 'unknown'), `t_in` = sum of givers' amounts, `potential = fx((t_out-t_in)/total)`; a giver's `t_out` now follows its `val` in the chain; constants in `data/game/empirical.json` | `transfers` GREEN: 6,396 checks, 0 failures | origin of the 0.1; subject types with a fraction other than 0.5 (none in the 80 saves); POR-as-receiver case in S79 |
| (found in the data, not in any result) | `rule_fx`: the game computes in 3-decimal fixed point with truncation: `val`, `power_fraction`, `share_total`, `money` | `income_share` wrong in 45.8% of entries -> 0.02% (14 of 85,056); `val` exact in all 83,201 entries | `retention` and `current` are not plain truncations of the exact quotient |
