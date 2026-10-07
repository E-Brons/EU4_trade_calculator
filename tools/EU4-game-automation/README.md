# EU4-game-automation

How to use it (setup, verbs, job spec, mechanics, pitfalls): **`GUIDE.md`**.

Drives the real EU4 (1.37.5, non-Ironman) to produce saves for the research (`docs/research/*_request_2.md`) and any
other analysis. Goal: a job runner / MCP server taking
`{nation, start_date, mods, script: [{console_commands, date, outfname}, ...]}`.

## Why a worker
Agent shells (Apple Claude Code) run inside a sandbox that blocks key injection (`osascript` -> -10004). So exactly one
process drives the game: `worker.py`, started by hand in an ordinary iTerm tab. Agents talk to it only through files
(`bridge.py`), the same pattern as `backend/tools/melt_worker.py`. The worker runs a fixed verb list, never arbitrary
shell, and restarts itself when `worker.py` changes.

```
python3 tools/EU4-game-automation/worker.py          # own iTerm tab; iTerm2 needs Accessibility + Screen Recording; Pillow
python3 tools/EU4-game-automation/bridge.py ping     # from anywhere, incl. the agent sandbox
```

## Verbs (worker.py)
`ping`, `launch [args]` (default `-skiplauncher`), `fit_window`, `quit`, `shot <name>`, `click <x> <y>` (pixels of the
last window screenshot, resolved against the window position at click time), `hover x= y=`, `key <name>`, `keys <text>`,
`console <line>...`, `save name=<n>`, `screen` (which known screen shows: refs/*.png templates), `wait_stopped max_s=`
(date display unchanged for ~4.5 s), `cpu`, `wait <s>`, `screens`.

## Job runner (runner.py)
`python3 tools/EU4-game-automation/runner.py job.json` or `run_job(spec)`; spec format in the module docstring
(`nation`, `start_date` (only 1444.11.11 for new games), `base_save`, `mods`, `observe`, `script` of steps with
`console_commands` / `effects` / `patch` / `date` / `outfname`). New games start as VEN (known map click) and switch
with `tag <nation>`. Every `date` is checked by reading `date=` from a save (re-run up to 4 times if the game stopped
early); saves are written while tagged as the nation (player=<nation>), then back to `observe`. `patch` = module with
`patch(text) -> text`: save, patch, reload via Continue Game (not yet tested live). dlc_load.json / continue_game.json
are backed up to `.bridge/runner_backup/` and restored in all cases.

Test 2026-10-06 (`.bridge/jobs/test1.json`, VEN, observe, saves at 1444.12.01 and 1445.01.01): ok; both saves
plain text, exact dates, player VEN, 80 nodes via `backend/scripts/research/venice_load.py`; merchant term present
on 1444.12.01 (VEN ragusa/wien R=2, venice 7; R>0 in 993/996 has_trader rows), i.e. tick-day values.

## Spike results (2026-10-06, Venice 1444)
| Mechanic | Result |
|---|---|
| launch | `-skiplauncher` opens the main menu directly |
| clicks | work only on visible pixels: the 2048x1330 game window is larger than the laptop screen, `fit_window` moves it to a display that fits |
| new game | Single Player -> click the country on the map -> PLAY -> PLAY (Normal mode is pre-selected) |
| console | game's own list: `commands_1.37.5.md` (`helplog`, 326 commands). The console is translucent; open/closed is detected from the input-box border line in a screenshot. The worker never types unless the console is verifiably open (otherwise the letters are map hotkeys) and checks that the text arrived before pressing Enter; when the console stops reacting it is toggled closed/open |
| run to date | `stop YYYY.MM.DD` ("Pauses the game at a specified date") + `speed 5`: paused exactly on the date |
| pop-ups / involuntary pauses | `observe` (spectator mode: the AI runs every country and answers events) ran 1445.09.01 -> 10.01 with no pop-up. `tag VEN` returns to a country (events can pop up again) |
| effects | `run <file>` runs an effect file from the EU4 user folder (`add_treasury = 1234` applied) |
| save | `savegame` writes nothing; `autosave` writes `save games/autosave.eu4` (plain text, exact date). `save` copies it to `.bridge/saves/<name>.eu4` after backing up the three rotating autosave slots |
| load a (patched) save | point `continue_game.json` at the file, restart, click Continue Game, confirm the achievements notice: patched treasury 7777 loaded |
| scheduled event (mod) | `on_startup` + `days = 20` fired on 1444.12.01 and paused the game (after the monthly trade tick); not needed now that `stop` exists |

Still open: merchants and light ships (no console command; save patching or UI clicks), whether `stop` is exact for
every date in observer mode, end-to-end job runner, MCP wrapper.

## Files
- `worker.py`, `eu4input.swift` (CGEvent keys/text/clicks, window lookup and move; compiled by the worker), `bridge.py`
- `commands_1.37.5.md` - the game's own console command list; `eu4_console_commands_spec.md` - web-derived (superseded)
- `spike/` - pause-event test mod + `install.py` (enable only that mod, back up / restore `dlc_load.json`)
