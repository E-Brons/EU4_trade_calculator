# EU4 Trade Optimizer — Web App Description

## 1. User Story

1. User plays EU4, saves the game (`.eu4` file — plain or Ironman).
2. User uploads the save to the web app.
3. If Ironman: the app runs a **"melt"** step to convert it to plain-text
   format *(out of scope for this phase — assume a melt utility exists and
   is invoked as a black box producing a plain save)*.
4. Backend loads the (plain) snapshot and **parses** everything relevant to
   trade: node graph state, provinces, trade goods/prices, ships, merchants,
   modifiers, and rival powers per node.
5. Backend **computes the optimal** merchant/ship allocation (see
   `trade-income-calculation.md` §6).
6. Frontend shows the visualizations (see `trade-visualizations.md`), and
   lets the user **toggle between configurations**:
   - **Snapshot** — exactly what's in the save right now
   - **Optimal** — the computed best allocation
   - **Manual / named captures** — user-built configurations via sliders
     and pickers, savable under a custom name for later recall/comparison

---

## 2. High-Level Architecture

```
┌──────────────┐      upload       ┌───────────────────┐
│   Frontend   │ ───────────────▶  │   Backend API      │
│  (SPA)       │                   │                     │
│              │ ◀─────────────────│  1. Melt (if needed)│
│  Sankey /    │  parsed trade     │  2. Parse save      │
│  Waterfall / │  state + presets  │  3. Build trade DAG │
│  What-If UI  │                   │  4. Run optimizer   │
└──────────────┘                   │  5. Serve presets   │
                                    └───────────────────┘
                                              │
                                    ┌───────────────────┐
                                    │  Storage            │
                                    │  - parsed snapshot   │
                                    │  - named captures    │
                                    └───────────────────┘
```

---

## 3. Backend Responsibilities

### 3.1 Ingestion
- **Endpoint:** `POST /api/saves` — accepts a `.eu4` file upload.
- Detect Ironman vs. plain (by header/checksum block).
- If Ironman → invoke melt utility (external/out-of-scope) → plain save bytes.
- Store the raw parsed save keyed by a `snapshot_id`.

### 3.2 Parsing
Extract only what's needed for the trade model:
- Trade node graph topology (static game data, versioned separately from saves)
- Per-node: provinces owned by the player and their goods/production/price
- Per-node: all countries' trade power components (ships present, merchant
  presence, building/modifier bonuses)
- Player's available unassigned light ships and merchants (if any)
- Current merchant assignments and their actions (collect/steer + target)

Output: a normalized `TradeState` object — the single source of truth fed
into both the optimizer and the "Snapshot" preset.

### 3.3 Optimization
- **Endpoint:** `POST /api/saves/{snapshot_id}/optimize`
- Runs the DAG-DP + greedy-ship-allocation + tie-breaking algorithm.
- Returns a `TradeConfiguration` (see data model below) with `preset_type = optimal`.
- Designed to run in well under a second (per the algorithm doc); safe to
  call synchronously from the request handler.

### 3.4 Capture management
- **Endpoint:** `POST /api/saves/{snapshot_id}/configurations` — save a
  user-built manual configuration under a given name.
- **Endpoint:** `GET /api/saves/{snapshot_id}/configurations` — list all
  presets (snapshot, optimal, named manual captures) for this save.
- **Endpoint:** `POST /api/saves/{snapshot_id}/configurations/evaluate` —
  given an ad-hoc (unsaved) set of manual picks, return computed ducat
  results live, without persisting — powers the live-updating What-If panel.

---

## 4. Data Model (core shapes)

```
TradeState {
  snapshot_id: string
  nodes: Node[]
}

Node {
  id: string
  name: string
  local_value: number
  total_power: number
  your_power: number
  outgoing_edges: { target_node_id: string, base_fraction: number }[]
  incoming_node_ids: string[]
  rival_powers: { country_tag: string, power: number }[]
  merchant_available: boolean
  unassigned_ships_here: number   // ships currently stationed, reassignable
}

TradeConfiguration {
  id: string
  snapshot_id: string
  name: string                      // "Snapshot" | "Optimal" | user-given name
  preset_type: "snapshot" | "optimal" | "manual"
  assignments: NodeAssignment[]
  total_ducats: number              // computed result, cached
}

NodeAssignment {
  node_id: string
  merchant_assigned: boolean
  action: "collect" | "steer" | null
  steer_target_node_id: string | null
  ships_assigned: number
}
```

---

## 5. Frontend Responsibilities

- **Upload screen:** file picker, upload progress, Ironman-detected notice.
- **Main dashboard:** the three-view layout from `trade-visualizations.md`
  (Sankey + What-If panel + per-node waterfall), driven by whichever
  `TradeConfiguration` is currently selected.
- **Preset switcher:** dropdown/tabs for Snapshot / Optimal / named captures;
  switching re-renders all three views against the newly selected config.
- **Manual editing mode:** sliders/pickers become editable when the user is
  building a manual configuration; calls `.../evaluate` on each change
  (debounced) for live feedback.
- **Capture flow:** "Save this configuration" button → name prompt →
  `POST .../configurations` → appears in the preset switcher.

---

## 6. Explicit Out-of-Scope (this phase)

- Ironman **melt** implementation itself (assumed as an available utility/service)
- Multiplayer save support
- Historical/time-series tracking across multiple saves
- Any mechanic listed as excluded in `trade-income-calculation.md` §0
