# Europa Universalis IV (EU4) — Complete Console Commands Specification

> **Scope:** PC single-player console commands for Europa Universalis IV.
>
> **Primary reference:** Paradox Wiki — Console commands.
>
> **Supplementary references:** EU4 Cheats, G2A's EU4 console-command guide, and the Steam community command guides supplied with this specification.
>
> **Important version note:** EU4 console commands are version-dependent. Some commands are internal/developer commands, some require DLC, and some historical community guides are obsolete. Where the supplied sources disagree or an exact current syntax cannot be established confidently, this specification marks the item rather than silently inventing syntax.

---

## 1. Console access

The console is available in a **non-Ironman single-player** game.

Common keys include:

- `~` / tilde
- `` ` `` / grave accent
- `Shift + 2`
- Depending on keyboard layout: `Alt + 2 1`, `Shift + 3`, `§`, `²`, `°`, `^`, or `AltGr + ^`

Type a command and press **Enter**.

Console use disables achievements for the affected non-Ironman game; commands are not intended for Ironman.

### Basic workflow

1. Enter `debug_mode`.
2. Hover over countries/provinces to obtain internal country tags and province IDs.
3. Enter the desired command.
4. Use `help [command]` or `findcommands [text]` when unsure about syntax.
5. Save before using commands that can permanently alter the game.

---

# 2. Syntax conventions

The notation used in this document is:

| Notation | Meaning |
|---|---|
| `[amount]` | Numeric value |
| `[tag]` | Three-letter country tag, e.g. `FRA` |
| `[province ID]` | Numeric province ID |
| `[event ID]` | Event identifier |
| `[religion]` | Internal religion identifier |
| `[idea group]` | Internal idea-group identifier |
| `[optional]` | Argument may be omitted |
| `<...>` | Placeholder; do not type the angle brackets |

Unless otherwise stated, commands apply to the player country when a country tag is omitted.

---

# 3. Discovery and help commands

| Command | Syntax | Description |
|---|---|---|
| `help` | `help` | Lists available console commands. |
| `help` | `help [command]` | Displays help for a command. |
| `helphelp` | `helphelp` | Developer/help Easter egg. |
| `helplog` | `helplog` | Writes the command list to `game.log`. |
| `findcommands` | `findcommands [text]` | Searches commands by name/description. |
| `debug_mode` | `debug_mode` | Displays useful debug information such as province IDs, country tags and distances. |
| `version` | `version` | Displays the game version. |
| `time` | `time` | Displays game/system timing information. |

**Recommended:** `debug_mode` is the most useful command when working with country or province IDs.

---

# 4. Money and monarch points

## 4.1 Ducats

| Command | Syntax | Description |
|---|---|---|
| `cash` | `cash [amount] [tag]` | Adds the specified number of ducats. Without an amount, commonly adds 5,000. Negative values remove ducats. |

Examples:

```text
cash 10000
cash -2000
cash 5000 FRA
```

---

## 4.2 Administrative, diplomatic and military power

| Command | Syntax | Description |
|---|---|---|
| `adm` | `adm [amount] [tag]` | Adds administrative power. Common default: 999. |
| `dip` | `dip [amount] [tag]` | Adds diplomatic power. Common default: 999. |
| `mil` | `mil [amount] [tag]` | Adds military power. Common default: 999. |
| `powerpoints` | `powerpoints [amount] [tag]` | Adds the same amount to administrative, diplomatic and military power. Common default: 999. |

Examples:

```text
adm 999
dip 999
mil 999
powerpoints 999
powerpoints -100
```

> **Do not confuse `powerpoints` with `power`.** `powerpoints` is the commonly documented command for adding ADM/DIP/MIL simultaneously. Older/partial command lists may describe `power` incorrectly.

---

# 5. Military resources

| Command | Syntax | Description |
|---|---|---|
| `manpower` | `manpower [amount] [tag]` | Adds manpower. The commonly documented unit is thousands: `manpower 100` gives 100,000. |
| `sailors` | `sailors [amount] [tag]` | Adds sailors. |
| `army_tradition` | `army_tradition [amount] [tag]` | Adds army tradition. |
| `navy_tradition` | `navy_tradition [amount] [tag]` | Adds naval tradition. |
| `army_professionalism` | `army_professionalism [amount] [tag]` | Changes army professionalism where supported by the game version. |
| `army_drill` | `army_drill [amount] [tag]` | Changes army drill where supported. |

Examples:

```text
manpower 100
sailors 10000
army_tradition 100
navy_tradition 100
```

---

# 6. Prestige, legitimacy and national modifiers

| Command | Syntax | Description |
|---|---|---|
| `prestige` | `prestige [amount] [tag]` | Adds/removes prestige. |
| `legitimacy` | `legitimacy [amount] [tag]` | Sets ruler legitimacy. |
| `stability` | `stability [amount] [tag]` | Changes stability. |
| `inflation` | `inflation [amount] [tag]` | Changes inflation. |
| `corrupt` | `corrupt [amount] [tag]` | Changes corruption. |
| `absolutism` | `absolutism [amount] [tag]` | Changes absolutism. |
| `innovativeness` | `innovativeness [amount] [tag]` | Changes innovativeness. |
| `reformprogress` | `reformprogress [amount] [tag]` | Adds government reform progress. |

Examples:

```text
prestige 100
legitimacy 100
stability 3
inflation -10
absolutism 100
reformprogress 100
```

---

# 7. Religion-specific resources

The following commands exist in various EU4 versions and/or DLC contexts:

| Command | Syntax | Description |
|---|---|---|
| `authority` | `authority [amount] [tag]` | Changes a religion/government authority resource where applicable. |
| `church_power` | `church_power [amount] [tag]` | Changes Protestant church power. |
| `devotion` | `devotion [amount] [tag]` | Changes devotion. |
| `fervor` | `fervor [amount] [tag]` | Adds fervor. |
| `harmony` | `harmony [amount] [tag]` | Changes harmony. |
| `harmonization` | `harmonization [amount] [tag]` | Changes harmonization progress where applicable. |
| `karma` | `karma [amount] [tag]` | Changes karma. |
| `mandate` | `mandate [amount] [tag]` | Changes mandate. |
| `meritocracy` | `meritocracy [amount] [tag]` | Changes meritocracy. |
| `piety` | `piety [amount] [tag]` | Changes piety. |
| `reform_desire` | `reform_desire [amount]` | Changes Catholic reform desire. |
| `doom` | `doom [amount] [tag]` | Changes Doom. |
| `horde_unity` | `horde_unity [amount] [tag]` | Changes horde unity. |
| `add_pa` | `add_pa [amount]` | Adds Patriarch Authority. |
| `add_pi` | `add_pi [amount]` | Adds Papal Influence. |

Examples:

```text
add_pa 100
add_pi 100
reform_desire 100
```

---

# 8. Technology and ideas

| Command | Syntax | Description |
|---|---|---|
| `tech` | `tech [amount]` | Adds the specified number of technology levels across ADM/DIP/MIL. |
| `ideas` | `ideas` | Completes/grants ideas according to the command's current implementation. |
| `add_idea_group` | `add_idea_group [idea group] [tag]` | Adds an idea group where supported. |

Example:

```text
tech 5
add_idea_group offensive_ideas
```

---

# 9. Map and visibility

| Command | Syntax | Description |
|---|---|---|
| `debug_mode` | `debug_mode` | Shows province IDs, country tags and debug information. |
| `fow` | `fow [province ID]` | Toggles Fog of War for a province; without an ID, toggles global Fog of War. |
| `ti` | `ti` | Toggles Terra Incognita. |
| `mapmode` | `mapmode [number]` | Changes the active map mode. |
| `observe` | `observe` | Enters observer/spectator mode. |
| `spectator` | `spectator` | Observer-mode command/alias where supported. |
| `clear` | `clear` | Clears console text. |

Example:

```text
debug_mode
fow
ti
observe
```

---

# 10. Country switching and AI

| Command | Syntax | Description |
|---|---|---|
| `tag` | `tag [country tag]` | Switches the player to another country. |
| `observe` | `observe` | Lets the AI run the entire game. |
| `ai` | `ai` | Toggles AI control/debug AI behavior depending on version. |
| `yesman` | `yesman` | Toggles AI acceptance of diplomatic proposals. |
| `lucky` | `lucky [tag]` | Toggles a country's Lucky Nation status where supported. |

Examples:

```text
tag FRA
tag ENG
yesman
```

`yesman` is a toggle: enter it again to turn it off.

---

# 11. Province ownership and control

| Command | Syntax | Description |
|---|---|---|
| `own` | `own [province ID] [tag]` | Transfers ownership of a province. |
| `own_core` | `own_core [province ID] [tag]` | Changes ownership and establishes the appropriate core relationship where supported. |
| `control` / `controll` | `control [province ID] [tag]` | Changes military control of a province. Older guides use `controll`. |
| `add_core` | `add_core [province ID] [tag]` | Adds a core. |
| `remove_core` | `remove_core [province ID] [tag]` | Removes a core. |
| `add_claim` | `add_claim [province ID] [tag]` | Adds a claim. |
| `add_permanent_claim` | `add_permanent_claim [province ID] [tag]` | Adds a permanent claim where supported. |
| `remove_claim` | `remove_claim [province ID] [tag]` | Removes a claim where supported. |
| `colonize` | `colonize [province ID] [tag]` | Colonizes a province. |

Example:

```text
debug_mode
own 242 BOH
add_core 222 FRA
add_claim 242
```

---

# 12. Province development and modifiers

| Command | Syntax | Description |
|---|---|---|
| `set_base_tax` | `set_base_tax [province ID] [amount]` | Sets base tax. |
| `set_base_production` | `set_base_production [province ID] [amount]` | Sets base production. |
| `set_base_manpower` | `set_base_manpower [province ID] [amount]` | Sets base manpower. |
| `add_baseunrest` | `add_baseunrest [province ID] [amount]` | Changes base unrest. |
| `add_devastation` | `add_devastation [province ID] [amount]` | Changes devastation. |
| `add_local_autonomy` | `add_local_autonomy [province ID] [amount]` | Changes local autonomy. |
| `add_prosperity` | `add_prosperity [province ID] [amount]` | Changes prosperity. |
| `province_modifier` | `province_modifier [province ID]` | Displays/works with province modifiers according to version. |
| `population` | `population [province ID] [amount]` | Changes population in mechanics/versions that support population. |
| `center_of_trade` | `center_of_trade [level] [province ID]` | Changes Center of Trade level. |

---

# 13. Culture

| Command | Syntax | Description |
|---|---|---|
| `culture` | `culture [province ID]` | Changes a province's culture to the player's primary culture. |
| `change_culture` | `change_culture [province ID] [culture]` | Changes province culture where supported. |
| `change_culture_court` | `change_culture_court [character] [culture]` | Changes a court character's culture where supported. |

Example:

```text
culture 183
```

---

# 14. Religion

| Command | Syntax | Description |
|---|---|---|
| `change_religion` | `change_religion [religion] [tag/province]` | Changes the religion of the specified target according to current command syntax. |
| `religion` | `religion [province ID] [religion]` | Changes a province's religion in versions supporting the command. |

Because syntax for `change_religion` has changed/been represented differently in community guides, use `help change_religion` in the actual game if the command is rejected.

Common internal religion identifiers include:

```text
catholic
protestant
reformed
orthodox
coptic
sunni
shiite
ibadi
buddhism
vajrayana
mahayana
confucianism
shinto
hinduism
sikhism
animism
shamanism
totemism
inti
nahuatl
tengri_pagan_reformed
norse_pagan_reformed
jewish
zoroastrian
jain
bon
```

The authoritative set of religion IDs is version-dependent.

---

# 15. War and military commands

| Command | Syntax | Description |
|---|---|---|
| `god` | `god` | Toggles god mode. |
| `winwars` | `winwars` | Attempts to give the player's current wars maximum warscore. |
| `siege` | `siege [province ID]` | Immediately completes a siege in the selected province. |
| `combat_dice` | `combat_dice [value]` | Forces combat dice to a specified value where supported. |
| `leader` | `leader [fire] [shock] [maneuver] [siege] [tag]` | Creates a general. |
| `admiral` | `admiral [fire] [shock] [maneuver] [siege] [tag]` | Creates an admiral. |
| `kill_leader` | `kill_leader [leader ID]` | Removes a leader where supported. |
| `army_drill` | `army_drill [amount] [tag]` | Changes army drill. |
| `repair` | `repair [tag]` | Repairs ships. |
| `spawn` | `spawn [province ID] [unit]` | Spawns a unit where supported. |
| `revolt` | `revolt [province ID]` | Starts a revolt. |
| `pirate` | `pirate [province ID]` | Creates pirates in a province where supported. |
| `native_uprising` | `native_uprising [province ID]` | Starts a native uprising. |

### `god`

```text
god
```

Toggle it once to enable and again to disable.

### `winwars`

```text
winwars
```

This command has been reported as unreliable/broken in some versions because of changes to warscore mechanics. Prefer normal war-ending commands or `yesman` when possible.

---

# 16. Diplomacy and subjects

| Command | Syntax | Description |
|---|---|---|
| `integrate` | `integrate [target tag] [actor tag]` | Integrates the target into the actor. |
| `vassalize` | `vassalize [target tag] [actor tag]` | Makes target a vassal of actor. |
| `annex` | `annex [target tag] [actor tag]` | Annexes a target according to the command's current implementation. |
| `form_union` | `form_union [target tag] [actor tag]` | Forms a personal union. |
| `make_subject` | `make_subject [target] [type] [actor]` | Creates a subject relationship where supported. |
| `create_march` | `create_march [target] [actor]` | Makes target a march. |
| `remove_march` | `remove_march [target] [actor]` | Removes march status. |
| `add_liberty_desire` | `add_liberty_desire [amount] [tag]` | Changes subject liberty desire. |
| `trust` | `trust [tag] [amount]` | Changes trust. |
| `favors` | `favors [tag] [amount]` | Changes favors. |
| `add_opinion` | `add_opinion [target] [amount]` | Changes opinion. |
| `insult` | `insult [tag]` | Sends an insult. |
| `rival` | `rival [tag]` | Adds a rival where supported. |
| `remove_rival` | `remove_rival [tag]` | Removes a rival. |
| `add_interest` | `add_interest [tag]` | Adds a country to interests. |
| `remove_interest` | `remove_interest [tag]` | Removes a country from interests. |
| `spynetwork` | `spynetwork [tag] [amount]` | Changes spy-network size. |
| `add_cb` | `add_cb [CB] [target tag] [actor tag]` | Adds a casus belli. |
| `remove_cb` | `remove_cb [CB] [target tag] [actor tag]` | Removes a casus belli. |
| `declare_war` | `declare_war [target] [actor]` | Declares war where supported. |
| `delete_wars` | `delete_wars [tag]` | Removes wars involving the target. |
| `clearae` | `clearae [tag]` | Clears aggressive expansion. |

---

# 17. Diplomats and colonists

| Command | Syntax | Description |
|---|---|---|
| `add_colonist` | `add_colonist [tag]` | Adds a colonist to the target country. |
| `add_diplo` | `add_diplo [tag]` | Adds a diplomat. |
| `fast_diplo` | `fast_diplo` | Makes diplomatic envoys return immediately/faster. |
| `fast_colonize` | `fast_colonize` | Toggles fast colonization. AI is affected too. |

**Warning:** `fast_colonize` affects AI countries as well as the player.

---

# 18. Rulers, heirs and consorts

| Command | Syntax | Description |
|---|---|---|
| `kill` | `kill [tag]` | Kills the current ruler. |
| `die` | `die [tag]` | Alternative ruler-death command where supported. |
| `kill_heir` | `kill_heir [tag]` | Kills the heir. |
| `add_heir` | `add_heir [tag]` | Adds an heir. |
| `add_age` | `add_age [tag]` | Adds age to the current heir in older/current implementations. |
| `age_heir` | `age_heir [age] [tag]` | Sets/changes heir age where supported. |
| `age_ruler` | `age_ruler [years] [tag]` | Changes ruler age where supported. |
| `age_consort` | `age_consort [years] [tag]` | Changes consort age where supported. |
| `add_consort` | `add_consort [tag]` | Adds a consort. |
| `kill_consort` | `kill_consort [tag]` | Kills the consort. |
| `kill_cardinal` | `kill_cardinal [tag]` | Kills a cardinal. |
| `add_cardinal` | `add_cardinal` | Adds a cardinal. |

Example:

```text
age_heir 15 FRA
kill_heir FRA
kill_consort FRA
```

> Older community guides sometimes mention a second numeric “country ID” alongside the three-letter tag. Later testing reported that the three-letter tag alone is generally sufficient. Use `debug_mode` and `help` for the current game version.

---

# 19. Events

| Command | Syntax | Description |
|---|---|---|
| `event` | `event [event ID] [country tag] [option ID]` | Fires an event. Country and option may be optional depending on event. |
| `testevent` | `testevent [event ID]` | Developer/testing event command. |
| `incident` | `incident [incident ID] [tag]` | Fires an incident where supported. |
| `imperial_incident` | `imperial_incident [incident ID]` | Fires an Imperial incident where supported. |
| `disaster` | `disaster [disaster ID]` | Starts a disaster where supported. |

Examples from community documentation:

```text
event 2011
event 2001
event dutch_republic.1
event anglican_events.14
```

Event IDs are **not console-command IDs**; they come from the game's event database.

---

# 20. Missions

| Command | Syntax | Description |
|---|---|---|
| `mission` | `mission [mission ID]` | Tests/activates a mission according to current implementation. |
| `testmission` | `testmission [mission ID]` | Tests a mission. |

Mission IDs are internal script identifiers and are version/mod dependent.

---

# 21. Estates and factions

| Command | Syntax | Description |
|---|---|---|
| `add_faction` | `add_faction [faction]` | Adds a faction where supported. |
| `add_loyalty` | `add_loyalty [estate] [amount]` | Changes estate loyalty. |
| `estate_agenda` | `estate_agenda [agenda]` | Manipulates an estate agenda where supported. |
| `add_backer` | `add_backer [province ID]` | Adds a backer where applicable. |

Examples from community testing:

```text
add_loyalty estate_church 100
add_loyalty estate_nobles 100
add_loyalty estate_burghers 100
add_loyalty estate_dhimmi 100
add_loyalty estate_cossacks 100
```

Estate identifiers vary by version/DLC.

---

# 22. Government reforms

| Command | Syntax | Description |
|---|---|---|
| `reformprogress` | `reformprogress [amount] [tag]` | Adds government reform progress. |
| `add_reformlevel` | `add_reformlevel [amount]` | Adds government reform levels where supported. |
| `clearreforms` | `clearreforms [tag]` | Clears government reforms where supported. |
| `pass_next_reform` | `pass_next_reform [reform ID]` | Advances a reform where supported. |

Example:

```text
reformprogress 100
```

---

# 23. Colonialism and natives

| Command | Syntax | Description |
|---|---|---|
| `fast_colonize` | `fast_colonize` | Toggles fast colonization. |
| `add_colonist` | `add_colonist [tag]` | Gives a colonist. |
| `add_natives` | `add_natives [province ID] [amount]` | Changes native population where supported. |
| `native_uprising` | `native_uprising [province ID]` | Creates a native uprising. |
| `population` | `population [province ID] [amount]` | Changes population in applicable mechanics/versions. |

---

# 24. Trade and Centers of Trade

| Command | Syntax | Description |
|---|---|---|
| `center_of_trade` | `center_of_trade [level] [province ID]` | Changes Center of Trade level. |
| `prices` | `prices` | Displays trade-good price information where supported. |
| `economy` | `economy` | Displays economy/debug information. |

---

# 25. Institutions

The `embrace` command can be used to force institution adoption where supported:

```text
embrace [province ID] [institution]
```

Common institution identifiers:

```text
feudalism
renaissance
new_world_i
printing_press
global_trade
manufactories
enlightenment
industrialization
```

The exact institution set is version-dependent.

---

# 26. Age of Discovery / Ages

| Command | Syntax | Description |
|---|---|---|
| `age` | `age [age number]` | Changes the active Age where supported. |
| `golden_age` | `golden_age [tag]` | Activates a Golden Age where supported. |

Typical age numbers:

```text
0 = Age of Discovery / Exploration
1 = Age of Reformation
2 = Age of Absolutism
3 = Age of Revolutions
```

Exact naming and support depend on version/DLC.

---

# 27. Revolution

| Command | Syntax | Description |
|---|---|---|
| `spread_revolution` | `spread_revolution [province ID]` | Spreads Revolution to a province where supported. |
| `revolution_target` | `revolution_target [tag]` | Changes Revolution-target status where supported. |

---

# 28. Save and game-state commands

| Command | Syntax | Description |
|---|---|---|
| `savegame` | `savegame` | Saves the current game. |
| `date` | `date [yyyy.mm.dd]` | Changes the game date. |
| `gamespeed` | `gamespeed [0–5]` | Changes game speed. |
| `stop` | `stop [date]` | Stops/pauses at a specified date where supported. |
| `clear` | `clear` | Clears the console. |
| `msg` | `msg` | Toggles message popups. |
| `fullscreen` | `fullscreen` | Toggles fullscreen. |
| `nextsong` | `nextsong` | Changes the current soundtrack. |
| `nopausetext` | `nopausetext` | Toggles pause-banner text. |

Example:

```text
date 1600.01.01
gamespeed 5
savegame
```

---

# 29. Debugging and developer commands

These commands are primarily for developers/modders.

```text
debug_info
debug_mode
debug_nogui
debug_reload_areas
debug_reload_regions

ai_budget
ai_plan_regions [tag]
ai_army_tick [tag] [file]
aiinvalid
aiview

balance
diplocount
diplomacy_info
ideadump
powerspend
powerspend_count
score
stats
memory
low_memory

assert
check_save
ct
cv
echo
enable_all_commands
refresh_knowledge
refreshknowledgecount
test
test_neighbour
timer
timer_start
timer_stop
timer_reset
timer_restart
timer_dump
timer_show
validateevents
verify_loc
writetestentities
```

These should not be confused with ordinary gameplay cheats.

---

# 30. Reload commands

Developer/modding commands include:

```text
reload [file]
reload_canals
reload_heightmap
reload_lakes
reload_map
reload_provincemap
reload_straits
reload_treemap
reloadfx [file]
reloadinterface
reloadloc
reloadtexture [file]
reloadtradewinds
```

These are primarily useful while developing or debugging mods.

---

# 31. Map-generation and graphical developer commands

```text
map_random [seed] [restore] [nosmooth] [nosmoothcoasts] [topology] [terrain] [colormap] [minimap] [rivers] [trees]
map_vertextextures
highlight_islands [threshold]
canals
collision
rendertype
rgb [amount]
nudge
spritelevel [level]
texture_usage
touch_test
```

`map_random` is especially dangerous for an ordinary campaign because it changes/randomizes map-generation data.

---

# 32. Script execution

| Command | Syntax | Description |
|---|---|---|
| `run` | `run [file]` | Executes commands/script content from a file. |
| `run_commands` | `run_commands [file]` | Executes console commands from a file where supported. |
| `run_commands_from_file` | `run_commands_from_file [file]` | Alternate/internal file-execution command in some versions. |
| `runyear` | `runyear [year] [file]` | Runs a script in a specified year where supported. |

Exact file locations and command names vary between versions. Use:

```text
help run
help run_commands
```

in the actual game.

---

# 33. Flags

Internal flags are useful when debugging events and scripted mechanics:

```text
set_flag [flag]
clr_flag [flag]

set_prov_flag [flag] [province ID]
clr_prov_flag [flag] [province ID]

print_flags
print_prov_flags [province ID]
```

Do not invent flag names. They must correspond to flags defined by the game's script or a loaded mod.

---

# 34. Special / Easter-egg commands

Some commands exist mainly for testing or Easter eggs:

```text
bearhaslanded [province ID]
epicfail [tag]
zombie
frenzy
frenzy_off
syntheticdawn [tag]
victorycard
morehumans [number]
humans [number]
```

### `bearhaslanded`

Historically used to create/spawn Jan Mayen-related content.

### `epicfail`

Causes the targeted country's spy actions to fail according to the documented implementation.

### `morehumans`

Adds human-controlled countries/players in supported contexts.

---

# 35. Commonly used command recipes

## Give yourself money and monarch points

```text
cash 100000
adm 999
dip 999
mil 999
```

## Give yourself all three monarch points simultaneously

```text
powerpoints 9999
```

## Give yourself manpower

```text
manpower 1000
```

This represents a very large manpower addition because the command is expressed in thousands.

## Remove aggressive expansion

```text
clearae
```

or, where a target tag is supported:

```text
clearae FRA
```

## Force diplomacy

```text
yesman
```

Turn it off by entering:

```text
yesman
```

again.

## Take a province

```text
debug_mode
own 242 BOH
```

## Add a core

```text
add_core 222 FRA
```

## Change province culture to your primary culture

```text
culture 183
```

## Kill a ruler

```text
kill FRA
```

## Kill an heir

```text
kill_heir FRA
```

## Give a country a new heir

```text
add_heir FRA
```

## Create a leader

```text
leader 6 6 6 3 FRA
```

The exact accepted range depends on the game version.

## Complete a siege

```text
siege 183
```

## Enable god mode

```text
god
```

Repeat to disable.

## Watch the AI

```text
observe
```

Return to a country:

```text
tag FRA
```

---

# 36. Country tags and province IDs

Before using a command requiring a country or province identifier:

```text
debug_mode
```

Hover over the relevant object.

Typical country tags:

```text
FRA = France
ENG = England
CAS = Castile
SPA = Spain
POR = Portugal
HAB = Austria
TUR = Ottomans
RUS = Russia
POL = Poland
LIT = Lithuania
SWE = Sweden
DAN = Denmark
MUS = Muscovy
```

These are examples only. Tags can differ for historical/formable countries and mods.

Province IDs are numeric and must be obtained from the game/debug information or a reliable province database.

---

# 37. Important warnings

## 37.1 Console commands are version-sensitive

EU4 has undergone many updates and DLC changes. A command documented for 1.12, 1.29, or an older DLC may not work identically in a current build.

The Steam guide supplied as a source explicitly identifies itself as an old list: its command list was updated for 1.12, while the later Steam guide supplied here was tested around the Manchu/1.29 era. Those sources are therefore useful historical references, not authoritative current syntax.

## 37.2 `debug_mode` is your friend

If a command requires an ID:

```text
debug_mode
```

first.

## 37.3 Test dangerous commands on a separate save

Especially:

```text
map_random
date
own
add_core
change_religion
event
disaster
observe
annex
integrate
vassalize
```

Some changes trigger scripts, modifiers, diplomatic recalculations or events that are not trivially reversible.

## 37.4 AI-affecting toggles

Some toggles affect the AI as well as the player.

In particular:

```text
fast_colonize
yesman
```

should be treated as global gameplay modifications.

## 37.5 Event commands can have side effects

An event can:

- change government;
- change religion;
- kill characters;
- add/remove modifiers;
- create wars;
- alter diplomatic relations;
- change country flags;
- trigger additional events.

Never assume `event` is equivalent to a simple one-line modifier.

---

# 38. Source reliability

The supplied sources have different roles.

### Paradox Wiki

The Paradox Wiki should be treated as the **primary reference** for current command behavior and syntax.

### EU4 Cheats

Useful as a broad command index and for examples. It is particularly useful for finding commands that are difficult to discover from the shorter community guides.

### G2A

Useful as a secondary practical guide. It documents console access, `debug_mode`, `cash`, `manpower`, `sailors`, `adm`, `dip`, `mil`, `powerpoints`, `siege`, `yesman`, `date`, `event`, `kill_heir`, `kill_cardinal`, `epicfail`, `add_colonist`, `add_diplo`, `savegame`, `clear`, `run`, and `observe`.

### Steam community guides

Useful for practical examples and historical commands, but the supplied Steam guides are old. One explicitly states that its command list was updated for EU4 1.12; another was tested around 1.29/Manchu. They should not override current-game behavior.

---

# 39. Quick-reference table

| Goal | Command |
|---|---|
| Find IDs | `debug_mode` |
| Search commands | `findcommands [text]` |
| Get command help | `help [command]` |
| Money | `cash [amount]` |
| ADM | `adm [amount]` |
| DIP | `dip [amount]` |
| MIL | `mil [amount]` |
| All monarch points | `powerpoints [amount]` |
| Manpower | `manpower [amount]` |
| Sailors | `sailors [amount]` |
| Prestige | `prestige [amount]` |
| Stability | `stability [amount]` |
| Legitimacy | `legitimacy [amount]` |
| Army tradition | `army_tradition [amount]` |
| Naval tradition | `navy_tradition [amount]` |
| Reform progress | `reformprogress [amount]` |
| Technology | `tech [amount]` |
| Add idea group | `add_idea_group [group]` |
| Fog of war | `fow` |
| Terra incognita | `ti` |
| Switch country | `tag [TAG]` |
| AI agrees | `yesman` |
| God mode | `god` |
| Win wars | `winwars` |
| Finish siege | `siege [province]` |
| Own province | `own [province] [TAG]` |
| Add core | `add_core [province] [TAG]` |
| Add claim | `add_claim [province] [TAG]` |
| Culture | `culture [province]` |
| Religion | `change_religion ...` |
| Integrate | `integrate [TAG] [actor]` |
| Vassalize | `vassalize [TAG] [actor]` |
| Form PU | `form_union [TAG] [actor]` |
| Clear AE | `clearae` |
| Add colonist | `add_colonist [TAG]` |
| Fast colonization | `fast_colonize` |
| Kill ruler | `kill [TAG]` |
| Kill heir | `kill_heir [TAG]` |
| Add heir | `add_heir [TAG]` |
| Add consort | `add_consort [TAG]` |
| Kill consort | `kill_consort [TAG]` |
| Kill cardinal | `kill_cardinal [TAG]` |
| Event | `event [ID] [TAG] [option]` |
| Save | `savegame` |
| Change date | `date [yyyy.mm.dd]` |
| Observe | `observe` |
| Clear console | `clear` |

---

# 40. Minimal cheat sheet

For a normal campaign, these are the commands most players actually need:

```text
debug_mode

cash 100000
powerpoints 9999
manpower 1000
sailors 10000
prestige 100
stability 3
legitimacy 100
army_tradition 100
navy_tradition 100
reformprogress 100

tech 5

yesman
clearae

own [province ID] [TAG]
add_core [province ID] [TAG]
add_claim [province ID] [TAG]
culture [province ID]

god
siege [province ID]
winwars

kill [TAG]
kill_heir [TAG]
add_heir [TAG]
kill_consort [TAG]
add_consort [TAG]

integrate [TAG]
vassalize [TAG]
form_union [TAG]

event [event ID]
date [yyyy.mm.dd]

fow
ti
tag [TAG]
observe
savegame
```

---

# 41. Verification principle

When a command in this document conflicts with the command parser in the installed game, **the installed game's parser wins**.

Use:

```text
help [command]
findcommands [keyword]
```

rather than assuming that a command from an old Steam guide or third-party cheatsheet still has identical syntax.

This is particularly important for:

- `change_religion`
- `integrate`
- `annex`
- `vassalize`
- `own`
- `control` / `controll`
- `event`
- `run`
- developer/debug commands
- DLC-specific mechanics

---

## Sources

1. Paradox Wiki — **Console commands**
2. EU4 Cheats — **EU4 Console Commands**
3. G2A — **Mastering EU4: Cheats, Console Commands, and Game Enhancements**, 11 December 2023.
4. Steam Community Guide — **Console Commands that work for Eu4!**, updated 25 January 2022.
5. Steam Community Guide — **Console Commands for EU4**, historical list updated through EU4 1.12.

