# Requirements

## Goal

Guide an EU4 player on how to allocate merchants and light ships across
trade nodes to maximize their monthly trade income, using their actual
game state rather than generic advice.

## Functional requirements

1. **Input**
   - Upload an actual `.eu4` save file (plain text, manually pre-melted, or
     binary Ironman) and have the app extract the player's trade situation
     automatically.
   - Ironman saves must melt with **zero manual steps** for the player
     beyond having a small background helper process running once -- not
     "open a website yourself and re-upload."
   - A manual-entry form must always work as a fallback, independent of
     save parsing succeeding, since save-format parsing is inherently
     best-effort against an undocumented, patch-dependent format.

2. **Trade model**
   - Model the real EU4 trade node graph (~80 nodes, the actual topology
     from the game files, not a simplification).
   - Compute a player's trade income from a given merchant/ship allocation
     using the *real* EU4 trade formula (verified against the actual game
     constants and real save data), not tunable-by-guesswork
     approximations. Where a value genuinely cannot be derived (e.g. trade
     efficiency, which depends on techs/ideas/policies not present in the
     trade data), it must be clearly identified as such and left as an
     explicit, editable input -- not silently guessed.
   - "Current income" shown to the player must be the save's own exact
     figure wherever the save provides one, not a re-derived estimate --
     estimates are reserved for genuinely hypothetical allocations the
     player hasn't tried, where no ground truth can exist.

3. **Optimization**
   - Find the merchant (none / collect / steer-to-X) and light-ship
     allocation that maximizes income, given a merchant count and ship
     count budget and a candidate set of nodes.
   - The search space is large (per-node discrete choices, not a simple
     product), so use a heuristic (seed with the obvious choices, fill
     remaining merchants by marginal value, local search / restarts) with
     exhaustive search as a fallback for small enough instances, rather
     than brute force by default.
   - Report the marginal value of one more/fewer merchant and one
     chunk more/fewer light ships, so the player can judge whether it's
     worth building more of either -- not just the single best allocation.

4. **Output**
   - Recommended actions per node (collect / steer-to-X / ship count).
   - Income comparison: current (exact, from the save) vs. optimal
     (estimated, calibrated against the exact current figure so the two
     numbers are comparable) vs. baseline (no merchants/ships at all).
   - A per-node breakdown of value, power shares, and where forwarded
     value goes.

## Non-functional / process requirements established during the build

- **No hand-waved approximation.** When a calculation came out wrong, the
  requirement was to find and fix the actual missing or incorrect
  mechanic, not to describe the gap as inherent model imprecision. Every
  constant in `Params` must be either a real, named game constant or an
  explicitly-justified exception with a stated reason it can't be derived.
- **Ironman melting must not depend on the sandboxed dev/agent environment
  having open network/browser access.** The chosen design (a file-based
  job bridge to a separate, user-run, unsandboxed helper process) must
  work even when the primary development/service environment is
  network- and process-sandboxed.
- **Don't commit unused exploratory dependencies.** Vendored reference
  source (e.g. the `rakaly`/`jomini` and `pdx-tools` repos, read during
  development to find real selectors/mechanics) is not a runtime
  dependency of the shipped app and must not be committed to this
  repository.

## Explicit decisions (with the user)

- **Stack:** Python/FastAPI backend, Flutter web frontend.
- **Input priority:** manual form is the reliable baseline; save upload
  (including Ironman via automated background melting) is the fast path
  when available.
- **Optimizer:** discrete heuristic search (seed + marginal fill + local
  search/restarts), with exhaustive search for small candidate sets;
  candidates are nodes the player restricts to (trade range), not the
  whole 80-node graph by default.
- **Ironman melting approach:** reuse pdx.tools' existing, already-correct
  client-side melting (it's licensed to embed Paradox's private token
  dictionary; nothing in this project needs to reimplement or obtain that
  dictionary) by driving a real browser against it, rather than building
  or licensing a token-aware melter of our own.
