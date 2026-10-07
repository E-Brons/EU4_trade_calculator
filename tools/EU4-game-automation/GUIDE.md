# EU4 game automation - usage guide

How to drive the real EU4 (1.37.5, macOS, non-Ironman) unattended and produce saves for analysis. Everything here was
verified live on 2026-10-06/07 (spike, runner tests, a 36-experiment overnight batch in `experiments/`).
The game's own console command list is `commands_1.37.5.md` (from `helplog`); `eu4_console_commands_spec.md` is the
older web-derived list (superseded, kept for reference).

## 1. Setup (once per session)

1. EU4 installed via Steam, Steam running, the game set to windowed mode (`settings.txt` `fullScreen=no`).
2. A display that fits the whole game window (2048x1330 points here): the laptop screen is too small, clicks reach only
   visible pixels. Keep the external display connected and the screen unlocked for the whole run (a locked screen or a
   sleeping display makes screenshots fail).
3. In an ordinary iTerm tab (not an agent shell - agent sandboxes block key injection), from the repo root:
   ```
   python3 tools/EU4-game-automation/worker.py
   ```
   iTerm2 needs Accessibility (keys/clicks) and Screen Recording (screenshots) in System Settings > Privacy & Security;
   restart iTerm after granting. Needs Pillow in that python. The worker compiles `eu4input.swift` on first use and
   restarts itself when `worker.py` changes.
4. Check from anywhere (also an agent sandbox): `python3 tools/EU4-game-automation/bridge.py ping` ->
   `accessibility_trusted: yes`.

## 2. Three ways to use it

| Layer | Use | Entry point |
|---|---|---|
| verbs | one action at a time (debugging, new UI flows) | `bridge.py <verb> ...` |
| job runner | a whole scenario: start, steps, dated saves | `runner.py job.json` / `run_job(spec)` |
| MCP server | the same for an AI client | `mcp_server.py` (registered in `/.mcp.json` as `eu4-automation`; approve it in Claude Code) |

### Verbs (`bridge.py`, executed by `worker.py`)
`ping`, `launch [args]` (default `-skiplauncher`: straight to the main menu), `fit_window` (move the window to a display
that fits), `quit`, `shot <name>` (PNG of the game window in `.bridge/shots/`), `click <x> <y>` (pixels of the last
screenshot at 2048 px width, resolved against the window position at click time), `hover x= y=`, `key <name>`,
`keys <text>`, `console <line> ...`, `save name=<n>`, `screen` (which known screen is shown, `refs/*.png`),
`wait_stopped max_s=<s>`, `cpu`, `wait <s>`, `screens`.

### Job spec (`runner.py`)
```json
{"nation": "VEN", "start_date": "1444.11.11", "base_save": null, "mods": [], "observe": true, "ai_off": ["VEN"],
 "script": [{"console_commands": "c.txt", "effects": "e.txt", "patch": "p.py", "date": "1445.01.01", "outfname": "out.eu4"}]}
```
Paths are relative to the job file. Per step, in this order: console lines -> effect file (`run`, while tagged as the
nation) -> save patch (save, `patch(text) -> text`, reload) -> run to `date` -> copy the save to `outfname`.
Every save is written while tagged as `nation` (player=<nation>), its `date=` is read back and must equal the step date.
`dlc_load.json` and `continue_game.json` are backed up and restored in all cases (also on failure).
Batch: `experiments/run_all.py` (status file, retry once, skip finished jobs, temp-save cleanup).

## 3. Mechanics that work (and the exact way)

| Need | How | Notes |
|---|---|---|
| new game | Single Player -> click the country on the map -> PLAY -> PLAY (Normal mode pre-selected) -> close intro | only VEN has a known map click; switch with `tag <TAG>`; only the 1444.11.11 bookmark |
| start from a save | copy it into `save games/` with a FRESH mtime, point `continue_game.json` at it BEFORE launch, click Continue Game, confirm the achievements notice | Continue Game opens the newest save file; verify the loaded date with a save |
| run to a date | console `stop YYYY.MM.DD` then `speed 5` | exact for >= 2 days ahead; a target exactly 1 day ahead is accepted but never fires |
| no pop-ups / involuntary pauses | console `observe` (spectator mode: the AI runs every country and answers events) | `tag <TAG>` returns to a country (pop-ups possible again) |
| keep a country's state fixed | `ai <TAG>` after every `observe` (toggle; leaving a tag re-enables its AI) | without it the AI moves even the observed nation's merchants within a month |
| any game effect | write an effect file into the EU4 user folder, `tag <TAG>`, `run <file>` | e.g. `add_treasury`, `add_trade_modifier`, `add_country_modifier`, `change_dip`, `add_dip_tech` |
| save | console `autosave`, copy `save games/autosave.eu4` | `savegame` writes nothing. The game rotates autosave -> old_autosave -> older_autosave: back up all three first (worker `save` does) |
| merchants | save patch (`savepatch.py`): `place_merchant`, `recall_merchant` | no console command or effect sends merchants. Verified live: a patched steering direction held 3 months with `ai_off` |
| light ships on protect trade | save patch `set_light_ship_mission` | copies the patrol route of a fleet already protecting that node; refuses nodes nobody protects (UI route untested) |
| tick-day values | save on the 1st | the 1st already contains the monthly trade computation |

Details of the merchant/ship save fields: `MERCHANTS_SHIPS.md`.

## 4. Console handling (why the worker is careful)

- The console is translucent; the worker detects "open" from the input-box border line in a screenshot.
- Never type into a closed console or while a pop-up/window holds the focus: letters become map hotkeys (opened the
  Ledger, ran wrong commands such as `frenzy` during the spike). The worker types only into a verified-open console,
  clears the input field, checks that the text arrived, then presses Enter.
- When the console stops reacting: press ` to close it and again to reopen.
- Windows opened by stray hotkeys cover the console: close them first (their X button).

## 5. Pitfalls met (and fixed)

| Symptom | Cause | Fix in code |
|---|---|---|
| clicks do nothing | window larger than the laptop screen | `fit_window` |
| `osascript` -10004 | agent sandbox | the user-started worker + file bridge |
| loaded the wrong game | Continue Game picks the newest save | fresh mtime + date check after load |
| game runs past the date | `stop` target in the past (wrong save) or 1 day ahead | date check, 1-day steps rejected |
| patched merchant gone next month | AI of the observed nation | `ai_off` |
| user's autosave lost | autosave rotation | backup of all three slots before every save |

## 6. Experiment practice

- One base save (on a 1st, after the first tick) shared by all treatments; one change per treatment; saves on the next
  two 1sts.
- Runs from one save diverge for other countries; the observed nation's power/demand/merchant fields stay identical
  (income about +-0.6 %): single runs are valid for those fields, income needs ratios or repeats.
- Check that the change happened (modifier present, relation created) before reading an effect: several commands did
  nothing in 1444 (centre of trade already at level 3, tributary relation not created).
- Results of the 2026-10-07 batch: `experiments/RESULTS.md`; plan: `experiments/PLAN.md`.
