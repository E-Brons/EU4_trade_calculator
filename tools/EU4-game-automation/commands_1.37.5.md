# EU4 1.37.5 console commands (from the game: `helplog` -> logs/game.log, 2026-10-06)

326 commands, in the order the game prints them. Details for one command: `help <name>` in the console.

| Command and arguments | Game description |
|---|---|
| `rendertype` | Reports what render backend is used |
| `CrashReporter.SimulateCrash` | Simulates a crash (resulting in the game exiting). |
| `CrashReporter.UploadCrash` | Upload the latest crash dump. |
| `CrashReporter.DeleteCrashData` | Delete local crash dumps older than X days. |
| `enable_all_commands []` |  |
| `center_of_trade(cot) [CoT Level] [Province ID]` | Create or upgrade/downgrade a center of trade |
| `run []` | Runs effects in specified file |
| `assert []` | Asserts trigger (otherwise causes test failure) |
| `country_modifier` | Show country modifier values. |
| `province_modifier` | Show province modifier values. |
| `nopausetext` | Toggles the pausebanner for nicer screenshots. |
| `nextsong` | Changes the currently playing soundtrack. |
| `date [date in format yyyy.mm.dd]` | Changes current date |
| `time` | What time is it? |
| `oos` | Make the client go oos |
| `print_modifiers(file)` | Print gamestate modifiers to a file |
| `combatsound` | How often does the combat view give a random sound? 0-50 |
| `morehumans(humans) [num]` | Adds more humans |
| `colonize [province]` |  |
| `fast_colonize` |  |
| `window(wnd) [Arguments: open/close] [window gui name]` | Opens or closes the specified window |
| `smoothframelog` | Toggles smooth frame logging |
| `reload [file name]` | Reloads the gui or lua file |
| `reloadtradewinds` | Reloads trade winds |
| `reloadinterface` | Reloads the entire interface |
| `reloadfx [Arguments: map/mapname/postfx or *.fx filename]` | Reloads the shader |
| `reloadtexture [texture file name]` | Reloads the specified texture |
| `reloadloc` | Reloads the localisation |
| `update_loc [localization tag]` | Updates the localization tag file |
| `verify_loc` | Verifies the localization keys |
| `poll` | Polls valid Events |
| `startup_screen` | Creates a new startup screen |
| `epicfail [<Target Country Tag> OPTIONAL]` | Makes all spies of target country fail |
| `event [event id] [<Target Country Tag> OPTIONAL] [<Option id> OPTIONAL]` | Executes an event |
| `disaster [distaste_key]` | Adds 100 progress to a disaster |
| `ai(ai) [<Target Country Tag>]` | Enables/Disables AI for all nations or a specific tag |
| `spectate(spectate,observe,spectator)` | Goes into Spectator mode |
| `rgb(rgb) [<Amount>]` | Prints desired amount of random color values to game.log |
| `reset_god` | Resets Personal Deity |
| `die(kill) [<Target Country Tag> OPTIONAL]` | Kills the monarch of a tag |
| `add_monarch [<Target Country Tag> OPTIONAL]` | Adds a monarch to a tag |
| `add_heir [<Target Country Tag> OPTIONAL]` | Adds a heir of a tag |
| `kill_heir [<Target Country Tag> OPTIONAL]` | Kills the heir of a tag |
| `add_consort [<Target Country Tag> OPTIONAL] [<Origin Country Tag> OPTIONAL]` | Adds a consort from a tag |
| `kill_consort [<Target Country Tag> OPTIONAL]` | Kills your consort |
| `siege [<Province ID>]` | Wins the siege in the specified province |
| `annex_all` | Annexes all other countries |
| `annex [<Target Country Tag>] [<Actor Country tag> OPTIONAL]` | Begin annex/annexes the specified tag |
| `reform [<Target Province ID>]` | Begin reformation in the specified province ID |
| `institution [<Province ID>] [<institution tag>] [<Amount> OPTIONAL]` | Add institution embracement to a province. |
| `remove_country [<Target Country Tag>]` | Obliterate a country from the map |
| `integrate [<Target Country Tag>] [<Actor Country tag> OPTIONAL]` | Begin integrate/integrates the specified tag |
| `vassalize [<Target Country Tag>] [<Actor Country tag> OPTIONAL]` | Vassalize the specified tag |
| `create_march [<Target Country Tag>] [<Actor Country tag> OPTIONAL]` | make a march the specified tag |
| `remove_march [<Target Country Tag>] [<Actor Country tag> OPTIONAL]` | make a march the specified tag |
| `discover [<Target Country Tag>] [<Actor Country tag> OPTIONAL]` | Discover capital of target tag |
| `modifiers_debug` | Show all modifiers and icons in country modifier view. |
| `golden_age [<Target Country Tag>]` | Give Golden Age to a tag. |
| `winwars` | Gives max war score in all wars for the country |
| `spritelevel [<Sprite level>]` | Sets a forced sprite level. Specify no argument to reset. |
| `sprite_pack_debug [<CountryTag> Optional]` | Prints debug data for sprite packs. |
| `add_cardinal` | Add a new Cardinal |
| `kill_cardinal [<Countrytag> OPTIONAL]` | Kill a Cardinal |
| `clear` | Clears the console |
| `clearae [<Against Country Tag>, <By Country Tag (empty for all)>]` | Clears Aggressive Expansion |
| `validateevents` | Validates all events without triggering it |
| `testevent [<Event ID>] [<Character ID>]` | Tests an event without triggering it |
| `cash [<Amount>] [<Target Country tag> OPTIONAL]` | Adds gold to the player |
| `trust [<Target Country tag>] [<Amount>]` | Adds trust with target country |
| `spynetwork [<Target Country tag>] [<Amount>]` | Adds spy network with target country |
| `favors [<Target Country tag>] [<Amount>]` | Adds favors with target country |
| `add_loyalty [<Target Estate>] [<Amount>]` | Adds loyalty to target estate |
| `church_power [<Amount>] [<Target Country tag> OPTIONAL]` | Adds church power to the player |
| `karma [<Amount>] [<Target Country tag> OPTIONAL]` | Adds karma to the player |
| `fervor [<Amount>] [<Target Country tag> OPTIONAL]` | Adds fervor to the player |
| `army_tradition [<Amount>] [<Target Country tag> OPTIONAL]` | Adds army tradition to the player |
| `navy_tradition [<Amount>] [<Target Country tag> OPTIONAL]` | Adds army tradition to the player |
| `splendor [<Amount>] [<Target Country tag> OPTIONAL]` | Adds splendor to the player |
| `absolutism [<Amount>] [<Target Country tag> OPTIONAL]` | Adds Absolutism to the player |
| `army_professionalism [<Amount>] [<Target Country tag> OPTIONAL]` | Sets army professionalism for target country |
| `religious_school [School] [<Target Country tag> OPTIONAL]` | Sets religious school for target country |
| `age [<which age>]` | age |
| `population [<ProvinceID>] [<Amount>]` | Adds population to a province. |
| `setmissionaryprogress [<ProvinceID>] [<Amount>]` | Sets the missionary progress for a province. |
| `manpower [<Amount>] [<Target Country tag> OPTIONAL]` | Adds manpower to player |
| `sailors [<Amount>] [<Target Country tag> OPTIONAL]` | Adds sailors to player |
| `add_natives [<ProvinceID>] [<Amount>]` | Add natives to given province |
| `native_uprising [<ProvinceID>]` | Create native uprising in given province |
| `pass_next_reform [<Amount>]` | Add reforms to empire |
| `add_liberty_desire [<Amount>] [<Target Country tag> OPTIONAL]` | Add liberty desire to the player |
| `add_opinion [<Actor Country tag>] [<Target Country tag> OPTIONAL]` | Add opinion to/from tag |
| `combat_dice [<Size>]` | Set Fixed Dice (-1 to disable) |
| `add_pa [<Country tag>]` | Add patriach authority to tag |
| `add_cb [<casus belli tag>] [<target country tag>] [<Actor Country tag> OPTIONAL]` | Add casus belli against target country |
| `remove_cb [<casus belli tag>] [<target country tag>] [<Actor Country tag> OPTIONAL]` | Remove casus belli from target country |
| `declare_war [<attacker tag>] [<defender tag>] [<call willing allies>]` | Declares war between two nations (no CB) |
| `tag [<Country tag>]` | Switch tag to another country |
| `remove_defender_faith` | Removes the defender of the Faith for the players religion |
| `form_union [<Country tag>] [<Country tag> OPTIONAL]` | Forms Union with target |
| `add_missionary [<Country tag>]` | Adds a missionary to a country |
| `add_pi [<Country tag>]` | Add papal influence to tag |
| `add_colonist [<Country tag>]` | Adds a colonist to a country |
| `add_interest [<Country tag>]` | Add specified country tag to your interest |
| `remove_interest [<Country tag>]` | Removes specified country tag from your interest |
| `add_diplo [<Country tag> OPTIONAL]` | Adds diplomatic entroute |
| `add_idea_group [<Idea group key>] [<Country tag> OPTIONAL]` | Adds the specified idea group |
| `tech [<AMOUNT>]` | Get levels in all techs |
| `power [<stability/tech_table_key/idea_key>] [<Country tag> OPTIONAL]` | Adds the specified idea group |
| `powerpoints [<AMOUNT> OPTIONAL] [<Country tag> OPTIONAL]` | Get power in all powers |
| `adm [<AMOUNT> OPTIONAL] [<Country tag> OPTIONAL]` | Get administrative power |
| `paper_mana [<AMOUNT> OPTIONAL] [<Country tag> OPTIONAL]` | Get administrative power |
| `dip [<AMOUNT> OPTIONAL] [<Country tag> OPTIONAL]` | Get diplomatic power |
| `bird_mana [<AMOUNT> OPTIONAL] [<Country tag> OPTIONAL]` | Get diplomatic power |
| `mil [<AMOUNT> OPTIONAL] [<Country tag> OPTIONAL]` | Get military power |
| `sword_mana [<AMOUNT> OPTIONAL] [<Country tag> OPTIONAL]` | Get military power |
| `add_republican_tradition [<AMOUNT> OPTIONAL] [<Country tag> OPTIONAL]` | Get republican tradition |
| `piety [<AMOUNT> OPTIONAL] [<Country tag> OPTIONAL]` | Get/Add piety |
| `stability [<AMOUNT> OPTIONAL] [<Country tag> OPTIONAL]` | Increase the stability of your country |
| `imperial_authority [<Amount>] [<Country tag> OPTIONAL]` | Increase your Imperial Authority |
| `lucky [<Country tag> OPTIONAL]` | Toggle lucky nation |
| `exhaust [<Amount>] [<Country tag> OPTIONAL]` | Alter your war exhaustion |
| `prestige [<Amount>] [<Country tag> OPTIONAL]` | Increase your prestige |
| `mandate [<Amount> OPTIONAL]` | Increase your mandate |
| `government_power(russian) [<Amount> OPTIONAL]` | Increase all your government powers |
| `incident [<IncidentTag>, <CountryTag> OPTIONAL]` | Trigger an incident for a country. |
| `isolationism []` | Set your isolation level |
| `inflation [<Amount>] [<Country tag> OPTIONAL]` | Increase your inflation |
| `PrintSynchStuff` | Prints random count and seed |
| `SetRandomCount` | Sets the randomcount to 0 or arg |
| `stop [<YYYY.MM.DD>]` | Pauses the game at a specified date |
| `fow(debug_fow) [<Province ID> OPTIONAL]` | Turns off fog of war in a province or in general |
| `collision(debug_collision)` | Toggles debug display of normals/bounding boxes/collision |
| `ti(debug_ti)` | Toggles Terra Incognita on/off |
| `savegame` | Creates an savefile. |
| `autosave` | Triggers an autosave. |
| `test [<test ID>]` | Runs a code test |
| `reinitchat []` | Posts a CChatSyncAllCommand |
| `nudge` | Go to the nudge tool |
| `embrace [<Province ID>] [<institution name> optional]` | Embraces all institutions in a province |
| `echo [Echo]` | Echoes the arguments in the console (also useful for commenting script files) |
| `invasion_target [<Province ID>]` | Force sets AI invasion target to province |
| `revolt [<Province ID>]` | Starts a Revolt in a province |
| `revolution_target [<CountryTag>]` | Sets the revolution target. |
| `add_local_autonomy [<Province ID>] [<Amount>]` | Adds local autonomy to a province. |
| `add_unrest [<CID Type>] [<CID Index>] [<Unrest>]` | Adds unrest to a faction |
| `add_baseunrest [<Province ID>] [<Base Unrest>]` | Adds base unrest to a province |
| `add_devastation [<Province ID>] [<Devastation>]` | Adds devastation to a province |
| `add_prosperity [<Province ID>] [<Prosperity>]` | Adds Prosperity to a state (provinceid is used) |
| `pirate [<Province ID>]` | Starts a Pirate in a province |
| `legitimacy [<AMOUNT>] [<Country tag> OPTIONAL]` | Set the legitimacy of the ruler |
| `corrupt [<AMOUNT>] [<Country tag> OPTIONAL]` | Set the corruption of the reich |
| `horde_unity [<AMOUNT>] [<Country tag> OPTIONAL]` | Set the unity of a horde |
| `meritocracy [<AMOUNT>] [<Country tag> OPTIONAL]` | Set the meritocracy of the Chinese Emperor |
| `devotion [<AMOUNT>] [<Country tag> OPTIONAL]` | Set the devotion of a theocracy |
| `doom [<AMOUNT>] [<Country tag> OPTIONAL]` | Add to a country's doom |
| `authority [<AMOUNT>] [<Country tag> OPTIONAL]` | Add to a country's authority |
| `mapmode [Mapmode type (int)]` | Change mapmode. |
| `fullscreen` | Toggles fullscreen |
| `score` | Score output. |
| `stats` | Stats to stats file. |
| `balance` | Region Balance output. |
| `prices` | Price Info |
| `add_core [<Province ID>] [<Country tag> OPTIONAL]` | Add core |
| `remove_core [<Province ID>] [<Country tag> OPTIONAL]` | Remove core |
| `add_faction [<factionname>]` | Adds a Faction to your country |
| `add_claim [<Province ID>] [<Country tag> OPTIONAL]` | Add claim |
| `add_permanent_claim [<Province ID>] [<Country tag> OPTIONAL]` | Add permanent claim |
| `remove_claim [<Province ID>] [<Country tag> OPTIONAL]` | Remove claim |
| `delete_wars [<Country tag> OPTIONAL]` | Delete wars without removing truces |
| `test_achievement [<achievement>]` | tests a specific achievement |
| `culture [<Province ID>]` | Changes culture on a province to your primary culture |
| `state [<Province ID>]` | Toggles State for owner of region of province. |
| `own [<Province ID>] [<Country tag> OPTIONAL]` | Change ownership |
| `own_core [<Province ID>] [<Country tag> OPTIONAL]` | Change ownership + add core |
| `controll [<Province ID>] [<Country tag> OPTIONAL]` | Change controller |
| `control [<Province ID>] [<Country tag> OPTIONAL]` | Change controller |
| `leader [<fire>] [<shock>] [<maneuver>] [<siege>] [<Country tag> OPTIONAL]` | Create a leader |
| `admiral [<fire>] [<shock>] [<maneuver>] [<siege>] [<Country tag> OPTIONAL]` | Create an admiral |
| `debug_reload_regions` | Reload map regions |
| `debug_reload_areas` | Reload map areas |
| `debug_nogui` | Toggles GUI on/off |
| `debug_info` | Toggles Debug info |
| `observe_mode []` | Changes the observe mode |
| `debug_achievements_clear` | Clear all achievements and user stats |
| `debug_achievements` | Enables popups for achievements to debug them |
| `spawnactor [<Actorname>] [<Province ID>] [<Animation> OPTIONAL]` | Spawns an actor with an optional animation |
| `spawn [<Province ID>] [<SubUnit Type>]` | Spawns a unit in a province |
| `spawn_all_units [<Animation state>]` | Spawns all units in capital for all existing countries. Requires unit_tester mod under Art/Test Resources enabled. |
| `change_religion [<province ID>] [<religion>]` | Change religion of a province or the state religion of the current country |
| `selflearningai` | Enables/Disables Self-Learning AI |
| `bearhaslanded` | An unwise command to use |
| `aiview` | Toggles additional AI info |
| `ai_minister [<0 = army, 1 = diplomacy, 2 = trade>]` | Enables/Disables specific AI ministers |
| `ai_recalc_strategy [<Country> OPTIONAL]` | Recalculates AI strategy immediately |
| `yesman` | Toggles AI positive responses |
| `memory` | Prints out the used memory |
| `leak` | Leaks memory |
| `leak_gpu [Chunk size (bytes)] [Number of Chunks]` | Leaks GPU memory |
| `refreshknowledgecount []` | Refresh knowledge perf couner |
| `economy []` | Prints out global economy statistics |
| `ai_budget [<tag> OPTIONAL]` |  |
| `powerspend_count []` | Prints out number of times powerspend was executed |
| `powerspend []` | Prints out global powerspend statistics |
| `heir_history []` | Prints out heir history |
| `reset_powerspend []` | Resets global powerspend statistics |
| `reset_economy []` | Resets global economy statistics |
| `diplocount` | Prints out global diploaction statistics |
| `timer` | Prints out debug timing info |
| `timer_start` | Starts debug timing |
| `timer_show` | Shows live timing data |
| `timer_restart` | Restarts (resets and starts) debug timing |
| `timer_reset` | Resets debug timing |
| `timer_stop` | Stops debug timing |
| `timer_dump` | Dumps debug timing info |
| `ct` | Puts timer info in clipboard |
| `popup_pause_all` | Sets all messages to popup and pause |
| `guibounds` | Toggles GUI bounds debug |
| `msg` | Toggles all messages popup |
| `great_project [<great project tag>]` | Create or destroy a great project |
| `canals` | Debug canals on map |
| `reload_canals` | Reload the canal bitmaps |
| `reload_straits` | Update strait vertex buffers |
| `map_vertextextures` | Toggle map rendering with vertex textures |
| `reload_map` | Reloads the map |
| `reload_heightmap` | Reloads the heightmap |
| `reload_provincemap` | Reloads the provincemap |
| `reload_treemap` | Reloads the treemap |
| `reload_lakes` | Reloads the lakes |
| `debug_mode` | Makes some debug features available |
| `texture_usage` | Prints texture usage |
| `low_memory` | Simulates a low memory alert and tries to reduce memory usage |
| `speed [<0-5>]` | Sets game speed |
| `runyear [<year>] [<command filename>]` | Runs command once we reach year |
| `nowar` | Toggles AI war declarations |
| `norevolts` | Toggles revolts |
| `aiinvalid` | Print invalid AI command counts |
| `zombie` | zombie army debug on/off |
| `god` | godmode on/off |
| `infinite_combat` | Infinite combat |
| `map_random [<seed=-1>] [<restore>] [<nosmooth>] [<nosmoothcoasts>] [<topology>] [<terrain>] [<colormap>] [<minimap>] [<rivers>] [<trees>]` | Randomize new world part of map (heightmap, terrain, ...) |
| `run_commands` | Runs the specified file with list of console commands |
| `helplog` | Print out all console commands to game.log file. |
| `help [command name]` | Print out all console commands or a specific command description. |
| `helphelp` | Double Rainbow help. |
| `findcommands [<Search string>]` | Finds console commands |
| `age_ruler [<age> <Country tag> OPTIONAL]` | Set rulers age |
| `age_heir [<age> <Country tag> OPTIONAL]` | Set heirs age |
| `age_consort [<age> <Country tag> OPTIONAL]` | Set consorts age |
| `remove_rival [<Country tag>]` | Remove rival |
| `show_ideas [<Country tag>]` | Show Ideas |
| `ideadump` | Dump all countries that have generic national ideas |
| `frenzy` | Force enable Great Power frenzy!!! |
| `frenzy_off` | Force disable Great Power frenzy!!! |
| `add_trait [<personality tag>, <heir> OPTIONAL, <consort> OPTIONAL]` | Add ruler personality |
| `remove_trait [<personality tag>]` | Remove ruler personality |
| `set_leader_trait [<personality>]` | Set selected leader's personality trait |
| `kill_advisors [<Country tag>]` | Kills all advisors in the court and from the pool |
| `repair [<Country tag>]` | Repairs all ships of country |
| `add_issue [<issue tag>]` | Add issue |
| `add_backer [<prov id>]` | Add backer |
| `version` | Prints the game version |
| `cv` | Prints the game version, and copies to clipboard. |
| `victorycard` | Force enables victory cards in singleplayer |
| `surrender` | Surrender |
| `touch_test` | Testing touch |
| `fast_diplo` | Ignore the date check for enroute diplomats |
| `diplomacy_info` | Print summary information about currently active diplomatic relations. |
| `kill_leader` | Kill a random leader with given death cause |
| `gamespeed [speed (0-5)]` | Set the current game speed, pausing the game at speed 0. |
| `set_prov_flag [<Flag>] [<Province>]` | Sets a flag for a province |
| `clr_prov_flag [<Flag>] [<Province>]` | Clears a flag from a province |
| `set_flag [<Flag>]` | Sets a global flag |
| `clr_flag [<Flag>]` | Clears a global flag |
| `set_country_flag [<Flag>]` | Sets a country flag |
| `clr_country_flag [<Flag>]` | Clears a country flag |
| `set_consort_flag [<Tag>] [<Flag>]` | Sets a global flag |
| `clr_consort_flag [<Tag>] [<Flag>]` | Clears a global flag |
| `print_flags` | Prints global flags |
| `print_prov_flags [<Prov ID>]` | Prints province flags |
| `make_subject [<Tag>]` | Make country a subject |
| `tributary [<Tag>]` | Make country a Tributary State |
| `harmony [<AMOUNT>] [<Country tag> OPTIONAL]` | Add to a country's Harmony |
| `harmonization [<AMOUNT [0, 100]>] [<Country tag> OPTIONAL]` | Set to a country's Harmonization progress |
| `army_drill [<AMOUNT [0.0, 100.0]>] [<Country tag> OPTIONAL]` | Sets drill for all your subunits |
| `test_neighbour [<Tag>]` | Will tell you if target Tag counts as neighbour to your country |
| `refresh_knowledge` | Will recalc bunch of stuff like neighbours, idea rules, etc. |
| `ai_plan_regions [<Country tag> OPTIONAL]` | Makes ai reevaluate all region assignments |
| `ai_army_tick [<Country tag> OPTIONAL] [<File name for logging> OPTIONAL]` | Makes ai reevaluate all army movements |
| `writetestentities []` |  |
| `check_save` | Check save and load persistence |
| `innovativeness` | Add Innovativeness |
| `reformprogress [Points to add] [Target tag <optional>]` | Add Government reform progress |
| `clearreforms [Target tag <optional>]` | Removes all government reforms |
| `change_religion_court [<ruler/heir/consort/admadv/dipadv/miladv>] [<Religion>]` | Changes the religion of a court member. |
| `change_culture_court [<ruler/heir/consort/admadv/dipadv/miladv>] [<Culture>]` | Changes the culture of a court member. |
| `insult [Sender] [Receiver] [Insult Index/Key]` | Sends a |
| `mission_tree [<true/false>] [<Tag>]` | Toggles mission tree completion |
| `mission [Mission identifier]` | Toggles mission completion |
| `invest [Investment Key] [Province ID]` | Toggles a Trade Company Investment defined by investment key in Trade Company defined by Province ID |
| `reshuffle_seat_bribes` | Will reshuffle all the seat bribes |
| `assimilate [<Province>] [<Tag> OPTIONAL]` | Change ownership, core, set culture and religion |
| `on_action [<Identifier>]` | Will run the giver on_action |
| `syntheticdawn [<Target Tag> OPTIONAL]` | The dawn of a scary new world |
| `tribal_development [<province id>, <value>]` | adds tribal development to the federation |
| `set_base_tax [<province id>, <value>]` | Sets base tax in province to provided value |
| `set_base_production [<province id>, <value>]` | Sets base production in province to provided value |
| `set_base_manpower [<province id>, <value>]` | Sets base manpower in province to provided value |
| `flagship_heavy` | Build a heavy flagship |
| `flagship_light` | Build a light flagship |
| `flagship_galley` | Build a galley flagship |
| `enable_game_controller` | Enables/disables support for game controller |
| `highlight_islands [<threshold>]` | Highlight islands on the map |
| `landing_page [<dlc_key>]` | Show Red Queen dlc landing page |
| `add_to_curia_treasury [<money>]` | Add money to the Curia Treasury |
| `pick_golden_bull [<name>]` | Pick a golden bull |
| `estate_agenda [<name>]` | Start a estate agenda |
| `imperial_incident [<name>]` | Start an imperial incident |
| `spread_revolution [<province ID or tag>]` | Spread the Revolution |
| `zeal [<Amount>] [[<Target Country tag>]]` | Adds Revolutionary Zeal to a country |
| `crownland [<Amount>] [[<Target Country tag>]]` | Adds Crownland to a country |
| `print_estate_land_share [<estate_type> [ <\|> percent]]` | Prints estates (or crown) land shares |
| `debug_crownland [<tag>]` | Will log the change in crownland for a tag |
| `debug_budgettag [<tag>]` | Will log income and expenditure for a tag |
| `debug_budgetall [<tag>]` | Will log income and expenditure for all countries. This will result in large files and a slower game! |
| `reform_desire [[<value>]]` | Will add reform desire (don't you dare) |
| `federation_cohesion [[<value>]]` | Will change federation cohesion by given value |
