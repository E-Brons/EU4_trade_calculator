#!/usr/bin/env python3
"""Generate the experiment job specs, effect/console files and PLAN.md table from the EXPERIMENTS list below
(single source of truth). Re-run after editing:  python3 tools/EU4-game-automation/experiments/make_jobs.py

Design: one base game (E00, VEN, observe) saved on the first tick day 1444.12.01. Every other experiment loads that
base, applies ONE change right after loading (effects file, console line or save patch), then runs to the next two
1sts (1445.01.01 = first tick that applies the change, 1445.02.01 = second tick). Controls E01a/b (determinism),
E01c (patch path: save + reload, no change) and E01d (effects path: tag + empty run + observe) are the comparison
baseline for each treatment. Paths in the job files are relative to jobs/ (the runner resolves them against the
job file's directory)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODS = ["mod/eu4_experiments.mod"]
BASE = "../out/E00/base_1444.12.01.eu4"


def ticks(eid: str) -> list[dict]:
    return [{"date": "1445.01.01", "outfname": f"../out/{eid}/t1_1445.01.01.eu4"},
            {"date": "1445.02.01", "outfname": f"../out/{eid}/t2_1445.02.01.eu4"}]


def mod_effect(key: str) -> str:
    return f"add_country_modifier = {{\n\tname = exp_{key}\n\tduration = -1\n}}\n"


# id, priority, topic/question (request_2 row), nation/node, change, compare, dependency, kind, payload
EXPERIMENTS = [
    dict(id="E00", pri="P0", topic="all: base game", where="VEN, world", change="none: new game 1444.11.11, observe",
         compare="base for every other job; t1/t2 = natural continuation", dep="-", kind="base"),
    dict(id="E01a", pri="P0", topic="R14 row 1: do two runs from one A diverge?", where="world",
         change="none (load base, run)", compare="E01a vs E01b: whole trade block, multiplayer_random_count", dep="base_save route (Continue Game) not yet run by the runner", kind="none"),
    dict(id="E01b", pri="P0", topic="R14 row 1 (repeat)", where="world", change="none", compare="vs E01a", dep="as E01a", kind="none"),
    dict(id="E01c", pri="P1", topic="control for patch experiments", where="world", change="identity patch (save + reload)",
         compare="vs E01a: effect of the save/reload path itself", dep="patch path untested live", kind="patch", payload="identity.py"),
    dict(id="E01d", pri="P1", topic="control for effect experiments", where="world", change="empty effects file (tag, run, observe)",
         compare="vs E01a: effect of the tag/run/observe path", dep="as E01a", kind="effects", payload=("empty", "# no effect\n")),
    dict(id="E02", pri="P1", topic="R01 row 2: game effect of the ruler-DIP term (+0.005/point, V14)", where="VEN all nodes",
         change="ruler DIP +2 (change_dip = 2)", compare="VEN max_demand per node (domestic/foreign class) vs E01d", dep="as E01a", kind="effects", payload=("dip_plus2", "change_dip = 2\n")),
    dict(id="E03", pri="P1", topic="R01 row 1: per-country scalar = global_trade_power?", where="VEN",
         change="+10% global_trade_power (exp mod)", compare="VEN max_demand / max_pow vs E01d", dep="as E01a", kind="effects", payload=("mod_global_trade_power", mod_effect("global_trade_power"))),
    dict(id="E04", pri="P1", topic="R01 rows 1/10: domestic class = global_own_trade_power?", where="VEN home/domestic nodes",
         change="+10% global_own_trade_power (exp mod)", compare="domestic vs foreign class values vs E01d", dep="as E01a", kind="effects", payload=("mod_global_own_trade_power", mod_effect("global_own_trade_power"))),
    dict(id="E05", pri="P1", topic="R01 rows 1/10: foreign class = global_foreign_trade_power?", where="VEN foreign nodes",
         change="+10% global_foreign_trade_power (exp mod)", compare="as E04", dep="as E01a", kind="effects", payload=("mod_global_foreign_trade_power", mod_effect("global_foreign_trade_power"))),
    dict(id="E06", pri="P1", topic="R07 rows 4-6: decomposition of X (trade efficiency)", where="VEN venice (home collector)",
         change="+10% trade_efficiency (exp mod)", compare="money/total of VEN collector vs E01d", dep="as E01a", kind="effects", payload=("mod_trade_efficiency", mod_effect("trade_efficiency"))),
    dict(id="E07", pri="P1", topic="R11 row 1/4: ship factor f via global_ship_trade_power", where="VEN alexandria (3 light ships on mission)",
         change="+50% global_ship_trade_power (exp mod)", compare="VEN ship_power at alexandria vs E01d (f = 1 -> 1.5?)", dep="as E01a", kind="effects", payload=("mod_global_ship_trade_power", mod_effect("global_ship_trade_power"))),
    dict(id="E08", pri="P1", topic="R08 row 2: steering strength a_c", where="VEN rank-1 entries (ragusa, alexandria, wien)",
         change="+25% trade_steering (exp mod)", compare="VEN incoming.add on steered links vs E01d", dep="as E01a", kind="effects", payload=("mod_trade_steering", mod_effect("trade_steering"))),
    dict(id="E09", pri="P1", topic="R13 row 1: composition of M (province trade power)", where="VEN provinces",
         change="+25% global_prov_trade_power_modifier (exp mod)", compare="province trade_power of VEN provinces, VEN province_power per node vs E01d", dep="as E01a", kind="effects", payload=("mod_prov_trade_power", mod_effect("prov_trade_power"))),
    dict(id="P01", pri="P1", topic="R08 row 1: weight rule when one steerer changes its link", where="VEN ragusa (3 links: pest, venice, genua)",
         change="VEN ragusa merchant steers to genua (idx 2) instead of venice (idx 1); in the base the AI had moved the alexandria merchant home", compare="ragusa steer_power weights, incoming value/add on ragusa->venice and ragusa->genua vs E01c", dep="savepatch place/recall verified live (test_patch3)", kind="patch", payload="p01_ragusa_steer_genua.py"),
    dict(id="E10", pri="P2", topic="R07 row 6 / R01 row 10: technology (dip) effect on efficiency and power", where="VEN",
         change="dip tech +1 (add_dip_tech = 1)", compare="money/total, max_demand, merchants vs E01d", dep="as E01a", kind="effects", payload=("dip_tech_plus1", "add_dip_tech = 1\n")),
    dict(id="E11", pri="P2", topic="R07 row 6: technology (adm) effect on efficiency", where="VEN",
         change="adm tech +1 (add_adm_tech = 1)", compare="as E10", dep="as E01a", kind="effects", payload=("adm_tech_plus1", "add_adm_tech = 1\n")),
    dict(id="E12", pri="P2", topic="R13 row 4: mercantilism scale; R01 row 4 embargo-size input", where="VEN provinces",
         change="mercantilism +10 (add_mercantilism = 10)", compare="province trade_power, max_demand vs E01d", dep="as E01a", kind="effects", payload=("mercantilism_plus10", "add_mercantilism = 10\n")),
    dict(id="E13", pri="P2", topic="R07 row 7: merchant capacity; R09 merchants field", where="VEN",
         change="+1 merchant (exp mod)", compare="countries.VEN.merchants, envoys; AI may place it (observe)", dep="as E01a", kind="effects", payload=("mod_merchants", mod_effect("merchants"))),
    dict(id="E14", pri="P2", topic="R06 row 1: flat power term; R05: does flat power propagate?", where="VEN ragusa (Crete 163)",
         change="add_trade_modifier power 10 at Crete (ragusa node)", compare="VEN max_pow at ragusa (+10?), upstream prev, modifier list vs E01d", dep="as E01a", kind="effects",
         payload=("crete_flat_power", "163 = {\n\tadd_trade_modifier = {\n\t\twho = root\n\t\tduration = 3650\n\t\tpower = 10\n\t\tkey = exp_trade_power\n\t}\n}\n")),
    dict(id="E15", pri="P2", topic="R05 row 1: threshold 10 for prev (crossing from below)", where="SAV genua (province_power 9.714 on 1444.12.01)",
         change="Piedmont (103) +3 base production", compare="SAV province_power at genua (>10?), SAV prev at ragusa/alexandria/tunis/valencia/champagne vs E01d", dep="as E01a", kind="effects", payload=("sav_piedmont_dev", "103 = {\n\tadd_base_production = 3\n}\n")),
    dict(id="E16", pri="P2", topic="R13 row 1: center-of-trade flat term", where="VEN Venezia (112)",
         change="center of trade level +1", compare="province 112 trade_power, VEN province_power at venice vs E01d", dep="as E01a", kind="effects", payload=("venezia_cot", "112 = {\n\tadd_center_of_trade_level = 1\n}\n")),
    dict(id="E17", pri="P2", topic="R13 row 3: building effect on province trade power", where="VEN Venezia (112)",
         change="marketplace built", compare="province 112 trade_power vs E01d", dep="as E01a", kind="effects", payload=("venezia_marketplace", "112 = {\n\tadd_building = marketplace\n}\n")),
    dict(id="E18", pri="P2", topic="R13 row 1: autonomy factor (1 - 0.005 x autonomy) check", where="VEN Padova (4729)",
         change="local autonomy +25", compare="province 4729 trade_power vs E01d", dep="as E01a", kind="effects", payload=("padova_autonomy", "4729 = {\n\tadd_local_autonomy = 25\n}\n")),
    dict(id="E19", pri="P2", topic="R09 row 6 / R14 Q8(e): has_capital follows capital or trade port?", where="VEN venice node",
         change="capital moved to Padova (set_capital = 4729)", compare="has_capital entries, countries.VEN capital/trade_port vs E01d", dep="as E01a", kind="effects", payload=("capital_padova", "set_capital = 4729\n")),
    dict(id="E20a", pri="P2", topic="R04 row 4: transfer fraction by subject type (vassal)", where="VEN + MAN (Mantua 109)",
         change="MAN becomes VEN vassal", compare="MAN t_out / (val - 0.1) per node, transfer flags vs E01d", dep="as E01a", kind="effects", payload=("subject_vassal", "create_subject = {\n\tsubject = MAN\n\tsubject_type = vassal\n}\n")),
    dict(id="E20b", pri="P2", topic="R04 row 4 (march)", where="VEN + MAN", change="MAN becomes VEN march", compare="as E20a", dep="as E01a", kind="effects", payload=("subject_march", "create_subject = {\n\tsubject = MAN\n\tsubject_type = march\n}\n")),
    dict(id="E20c", pri="P2", topic="R04 row 4 (tributary)", where="VEN + MAN", change="MAN becomes VEN tributary", compare="as E20a", dep="as E01a", kind="effects", payload=("subject_tributary", "create_subject = {\n\tsubject = MAN\n\tsubject_type = tributary_state\n}\n")),
    dict(id="E20d", pri="P2", topic="R04 row 4 (personal union)", where="VEN + MAN", change="MAN in personal union under VEN", compare="as E20a", dep="as E01a", kind="effects", payload=("subject_personal_union", "create_subject = {\n\tsubject = MAN\n\tsubject_type = personal_union\n}\n")),
    dict(id="E21", pri="P2", topic="R08 row 7 / R09 row 2 / R10 row 7: aggregates when a country loses its last province", where="NAX (Naxos 164) -> VEN",
         change="Naxos ceded to VEN on 1444.12.01", compare="top_power, max, pull_power, retain_power, incoming.add at NAX's nodes on 12.03, 12.15 and 1445.01.01", dep="as E01a", kind="vanish", payload=("naxos_ceded", "164 = {\n\tcede_province = VEN\n}\n")),
    dict(id="E22", pri="P2", topic="R06 row 1 / R07 row 1 / R11 row 1: idea-group effects (console add_idea_group)", where="VEN",
         change="console: add_idea_group trade_ideas VEN", compare="active_idea_groups, max_pow merchant term, money/total vs E01a (semantics of the command to be read from the save)", dep="as E01a", kind="console", payload=("idea_trade", "add_idea_group trade_ideas VEN\n")),
    dict(id="P02", pri="P2", topic="R08 row 4 (Q5): weights of a node without steerers", where="hangzhou (3 links; MNG the only steerer)",
         change="recall every steering merchant at hangzhou", compare="hangzhou weights / link values vs E01c", dep="savepatch recall UNTESTED live; AI may re-send merchants before the 1st", kind="patch", payload="p02_recall_all_steerers_hangzhou.py"),
    dict(id="P03", pri="P2", topic="R06 row 2: merchant term for collecting-away merchants; R02 away penalty", where="VEN ragusa",
         change="ragusa merchant collects instead of steering", compare="VEN max_pow (term R), val, total/money at ragusa vs E01c", dep="savepatch UNTESTED live", kind="patch", payload="p03_ragusa_collect_away.py"),
    dict(id="P04", pri="P2", topic="R09 row 10 / R01 row 7: transfer_home_bonus with 4 steering merchants", where="VEN constantinople -> ragusa",
         change="+1 merchant (exp mod) then 4th steerer via patch", compare="transfer_home_bonus (0.4?), venice max_demand vs E13", dep="savepatch place UNTESTED live; needs a free envoy after the +1 merchant modifier (offline the patch refuses: no free merchant in the stored save)", kind="effects+patch", payload=(("mod_merchants", mod_effect("merchants")), "p04_fourth_steerer.py")),
    dict(id="P05", pri="P2", topic="R05 rows 4/5, R11 row 3: ships at a downstream node; income effect of one ship assignment", where="VEN light-ship fleet alexandria -> other node",
         change="fleet protect mission moved (first accepted of ragusa/constantinople/venice/genua/tunis)", compare="ship_power, light_ship, upstream prev, VEN total/money vs E01c", dep="set_light_ship_mission UNTESTED (copies another fleet's route; may refuse)", kind="patch", payload="p05_light_ships.py"),
    dict(id="E23", pri="P3", topic="R13 row 7: on which days province trade_power is recomputed; R09 row 10 daily transfer_home_bonus", where="world",
         change="none; one save every 2nd day 1444.12.03 .. 1445.01.02 (16 saves; `stop` cannot step 1 day)", compare="provinces block day by day", dep="as E01a", kind="daily"),
    dict(id="P06", pri="P3", topic="R05 row 2: link with bookmark weight 0 (california -> mexico) turning positive", where="XAL california",
         change="XAL steers california -> mexico", compare="XAL prev at upstream nodes of california vs E01c", dep="savepatch place UNTESTED; XAL may lack merchant capacity", kind="patch", payload="p06_xal_california_mexico.py"),
]

BLOCKED = [
    ("embargo on/off pair", "R01 row 4, R10 row 4, R14 row 3", "no console command or effect found; needs a save patch of the embargo fields or UI clicks"),
    ("privateer fleet pair", "R10 rows 1-2", "fleet mission privateer: savepatch has no function yet"),
    ("player recall leaving no merchant_recalled modifier", "R06 row 6", "needs a UI recall (a patch recall is not the game's recall action)"),
    ("merchant in transit, saved daily", "R09 row 10", "needs a UI send (a patch places the merchant instantly)"),
    ("trade-efficiency tooltip lines", "R07 row 2", "UI text, not in a save (screenshot of the tooltip could do it)"),
    ("other start dates", "R14", "runner supports new games only on 1444.11.11 (use a base save)"),
]


def write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path.name


AI_OFF_EXTRA = {"P02": ["MNG"], "P06": ["XAL"]}


def build() -> list[dict]:
    jobs = []
    for x in EXPERIMENTS:
        eid, kind, pl = x["id"], x["kind"], x.get("payload")
        # ai_off: the AI of these tags is disabled while observing, so merchants set by a patch (or the base state)
        # are not moved by the AI between load and the saves (verified live: test_patch3, 3 months).
        spec = {"nation": "VEN", "mods": MODS, "observe": True, "base_save": BASE, "script": [],
                "ai_off": ["VEN"] + AI_OFF_EXTRA.get(eid, [])}
        if kind == "base":
            spec.update(base_save=None, start_date="1444.11.11", ai_off=[])
            spec["script"] = [{"date": "1444.12.01", "outfname": "../out/E00/base_1444.12.01.eu4"},
                              {"date": "1445.01.01", "outfname": "../out/E00/t1_1445.01.01.eu4"},
                              {"date": "1445.02.01", "outfname": "../out/E00/t2_1445.02.01.eu4"}]
        elif kind == "none":
            spec["script"] = ticks(eid)
        elif kind == "effects":
            name = write(HERE / "effects" / f"{pl[0]}.txt", pl[1])
            spec["script"] = [{"effects": f"../effects/{name}"}] + ticks(eid)
        elif kind == "console":
            name = write(HERE / "console" / f"{pl[0]}.txt", pl[1])
            spec["script"] = [{"console_commands": f"../console/{name}"}] + ticks(eid)
        elif kind == "patch":
            spec["script"] = [{"patch": f"../patches/{pl}"}] + ticks(eid)
        elif kind == "effects+patch":
            (ename, etext), pname = pl
            name = write(HERE / "effects" / f"{ename}.txt", etext)
            spec["script"] = [{"effects": f"../effects/{name}"}, {"patch": f"../patches/{pname}"}] + ticks(eid)
        elif kind == "vanish":
            name = write(HERE / "effects" / f"{pl[0]}.txt", pl[1])
            spec["script"] = [{"effects": f"../effects/{name}"},
                              {"date": "1444.12.03", "outfname": f"../out/{eid}/d_1444.12.03.eu4"},  # stop cannot do 1 day
                              {"date": "1444.12.15", "outfname": f"../out/{eid}/d_1444.12.15.eu4"},
                              {"date": "1445.01.01", "outfname": f"../out/{eid}/t1_1445.01.01.eu4"}]
        elif kind == "daily":
            import datetime as dt
            d = dt.date(1444, 12, 3)  # every 2nd day: EU4 `stop` ignores the next day
            while d <= dt.date(1445, 1, 2):
                s = f"{d.year}.{d.month:02d}.{d.day:02d}"
                spec["script"].append({"date": s, "outfname": f"../out/{eid}/d_{s}.eu4"})
                d += dt.timedelta(days=2)
        else:
            raise ValueError(kind)
        write(HERE / "jobs" / f"{eid}.json", json.dumps(spec, indent=1) + "\n")
        x["saves"] = ", ".join(Path(s["outfname"]).name for s in spec["script"] if "outfname" in s) if kind != "daily" else "16 saves, every 2nd day"
        jobs.append(x)
    return jobs


def plan(jobs: list[dict]) -> None:
    rows = ["| id | pri | research topic / question (request_2 row) | nation / node | change | saves (out/<id>/) | compare | dependency |",
            "|---|---|---|---|---|---|---|---|"]
    for x in jobs:
        rows.append(f"| {x['id']} | {x['pri']} | {x['topic']} | {x['where']} | {x['change']} | {x['saves']} | {x['compare']} | {x['dep']} |")
    blocked = ["| experiment | request_2 rows | why blocked |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in BLOCKED]
    text = f"""# Experiments (runnable job specs)

Generated by `make_jobs.py` (edit the list there, re-run). Jobs: `jobs/<id>.json`, run with
`python3 tools/EU4-game-automation/runner.py tools/EU4-game-automation/experiments/jobs/<id>.json`.

Before the first run: `python3 tools/EU4-game-automation/experiments/install_mod.py` (installs the single-modifier
test mod; every job enables it, including the base, so all saves share the same mod set).

Order: E00 first (it writes the base save every other job loads), then E01a/E01b (if they differ, every A/B below
needs repeat runs to separate noise from effect), then E01c/E01d, then by priority. Each treatment loads the base
(1444.12.01, a tick day), applies ONE change, and saves at 1445.01.01 (first tick that applies it) and 1445.02.01.
Compare a treatment with the control of the same path: effects -> E01d, patch -> E01c, console/none -> E01a.
Observe mode with `ai_off`: every job except E00 disables the AI of VEN (and of the patched tag in P02/P06) after each
switch to observe, so the AI cannot move merchants between load and the saves (verified live, test_patch3).

Dependencies: "base_save route" = Continue Game load by the runner (proven by hand in the spike, not yet run by the
runner); "savepatch UNTESTED" = the patch functions were derived from saves but never loaded into the game (the
live test `.bridge/jobs/test_patch.json` is pending).

{chr(10).join(rows)}

## Not runnable yet

{chr(10).join(blocked)}
"""
    (HERE / "PLAN.md").write_text(text)


if __name__ == "__main__":
    js = build()
    plan(js)
    print(len(js), "jobs written")
