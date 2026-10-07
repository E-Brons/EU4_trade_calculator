#!/usr/bin/env python3
"""Round 2: writes jobs/*.json, effects/, patches/, ORDER.txt (run from anywhere). Plan and row mapping: PLAN.md.

Bases (paths relative to jobs/):
  E00   ../../out/E00/base_1444.12.01.eu4            VEN 1444.12.01, experiment mod; VEN has merchants at ragusa
                                                     (steer venice), wien (steer venice), venice (collects at home)
  U10   ../bases/U10_VEN.1444.12.01.eu4              Venice series, vanilla; VEN merchants at alexandria, ragusa, wien
                                                     (all steer), none at home  (prep_bases.py extracts it)
  NED18 ../../diversity/out/obs-1618-NED/NED_1618.06.01.eu4   (exists after the diversity batch)
Controls: jobs on E00 compare with round-1 E01c (patch path) / E01d (effects path), same base and runner;
jobs on U10 compare with R2-C-U10 (identity patch); NED18 jobs with R2-C-NED18; the diversity C save is the natural
continuation.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP_MOD = ["mod/eu4_experiments.mod"]
E00 = "../../out/E00/base_1444.12.01.eu4"
U10 = "../bases/U10_VEN.1444.12.01.eu4"
NED18 = "../../diversity/out/obs-1618-NED/NED_1618.06.01.eu4"

PATCH_HEAD = '''import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402,F401
'''

# --- save-text helpers used by several patches (embargo, transfer relation, trade port), kept in one module ---
HELPERS = '''"""Round-2 save edits not covered by savepatch.py. Formats are copied from saves:
- transfer relation (U25 diplomacy block): transfer_trade_power={ amount=1.000 is_enforced=yes first="LDU" second="MRA" start_date=... }
  (U04: 24 colony / trade protectorate relations, all amount=0.500)
- embargo (U25 country blocks): embargoer `trade_embargoes={ TAG }`, target `trade_embargoed_by={ TAG }`, both just
  before `score_rating=` in the country block
- main trade port: country field `trade_port=<province id>` (E00: VEN capital=112, trade_port=112)
"""
import re


def country_span(t: str, tag: str) -> tuple[int, int]:
    c = t.index("\\ncountries={")
    i = t.index(f"\\n\\t{tag}={{", c)
    return i, t.index("\\n\\t}", i)


def add_transfer(t: str, giver: str, receiver: str, amount: float, date: str) -> str:
    d = t.index("\\ndiplomacy={")
    rel = (f"\\n\\ttransfer_trade_power={{\\n\\t\\tamount={amount:.3f}\\n\\t\\tis_enforced=yes\\n\\t\\tfirst=\\"{giver}\\""
           f"\\n\\t\\tsecond=\\"{receiver}\\"\\n\\t\\tstart_date={date}\\n\\t}}")
    k = d + len("\\ndiplomacy={")
    return t[:k] + rel + t[k:]


def _add_list(t: str, tag: str, key: str, item: str) -> str:
    i, e = country_span(t, tag)
    blk = t[i:e]
    m = re.search(rf"\\n\\t\\t{key}={{([^}}]*)}}", blk)
    if m:
        if item in m.group(1).split():
            return t
        new = blk[:m.start(1)] + m.group(1).rstrip() + f" {item} \\n\\t\\t" + blk[m.end(1):]
    else:
        j = blk.index("\\n\\t\\tscore_rating=")
        new = blk[:j] + f"\\n\\t\\t{key}={{\\n\\t\\t\\t{item} \\n\\t\\t}}" + blk[j:]
    return t[:i] + new + t[e:]


def add_embargo(t: str, embargoer: str, target: str) -> str:
    t = _add_list(t, embargoer, "trade_embargoes", target)
    return _add_list(t, target, "trade_embargoed_by", embargoer)


def set_trade_port(t: str, tag: str, province: int) -> str:
    i, e = country_span(t, tag)
    blk = t[i:e]
    new, n = re.subn(r"\\n\\t\\ttrade_port=\\d+", f"\\n\\t\\ttrade_port={province}", blk, count=1)
    assert n == 1, "trade_port field not found"
    return t[:i] + new + t[e:]


def privateer(t: str, tag: str, node: str) -> str:
    """Experimental: protect-trade mission in `node` (savepatch), then the mission key renamed to privateer_mission
    (key present in the game binary; field set of a real privateer mission not seen in any save)."""
    import savepatch as sp
    t2 = sp.set_light_ship_mission(t, tag, node)
    i, e = country_span(t2, tag)
    blk = t2[i:e]
    j = blk.rfind("protect_mission={")
    assert j >= 0
    return t2[:i] + blk[:j] + "privateer_mission={" + blk[j + len("protect_mission={"):] + t2[e:]
'''

EXPS: list[dict] = []


def exp(id_, rows, base, script, change, ai_off=("VEN",), mods=EXP_MOD, control="", start_date=None):
    EXPS.append(dict(id=id_, rows=rows, base=base, script=script, change=change, ai_off=list(ai_off), mods=mods,
                     control=control, start_date=start_date))


def ticks(id_, d1="1445.01.01", d2="1445.02.01"):
    return [{"date": d1, "outfname": f"../out/{id_}/t1_{d1}.eu4"}, {"date": d2, "outfname": f"../out/{id_}/t2_{d2}.eu4"}]


def write(p: Path, text: str) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p.name


def patch_file(name: str, doc: str, body: str, helpers: bool = False) -> str:
    imp = "import r2helpers as h  # noqa: E402\n" if helpers else ""
    src = f'"""{doc}"""\n' + PATCH_HEAD + ("sys.path.insert(0, str(Path(__file__).resolve().parent))\n" + imp if helpers else "") + \
        "\n\ndef patch(t: str) -> str:\n" + "".join(f"    {ln}\n" for ln in body.strip().splitlines())
    return write(HERE / "patches" / name, src)


def effects_file(name: str, text: str) -> str:
    return write(HERE / "effects" / name, text)


def build() -> None:
    write(HERE / "patches" / "r2helpers.py", HELPERS)
    write(HERE / "patches" / "identity.py", '"""Control: save + reload, no change."""\n\n\ndef patch(t: str) -> str:\n    return t\n')

    # R07 B5: merchant at the home node (behaviour +0.10 settled observationally; the size is not, E00 vs Venice 0.32 vs 0.12)
    p = patch_file("b5a_recall_home.py", "R07 B5a: recall VEN's merchant at its home node venice (collecting at home); nothing else.",
                   'return sp.recall_merchant(t, "VEN", "venice")')
    exp("R2-B5a", ["R07 row 1 (size of the merchant term at home)", "R07 row 2 (+0.05 steps)"], E00,
        [{"patch": f"../patches/{p}"}] + ticks("R2-B5a"), "VEN home merchant at venice recalled", control="E01c (round 1)")
    p = patch_file("b5b_place_home.py", "R07 B5b (base U10, no home merchant): VEN's alexandria merchant moved to venice (collect at home).",
                   'return sp.place_merchant(sp.recall_merchant(t, "VEN", "alexandria"), "VEN", "venice", "collect")')
    exp("R2-B5b", ["R07 row 1", "R01 row 7 (transfer_home_bonus: alexandria steerer leaves)"], U10,
        [{"patch": f"../patches/{p}"}] + ticks("R2-B5b"), "VEN alexandria steerer -> merchant at home venice", mods=[], control="R2-C-U10")
    p = patch_file("b5c_recall_alexandria.py", "R07/R01 (base U10): recall only the alexandria steerer (separates B5b's two parts).",
                   'return sp.recall_merchant(t, "VEN", "alexandria")')
    exp("R2-B5c", ["R01 row 7 (transfer_home_bonus counting)", "R07 row 1 (B5b minus this = home merchant)"], U10,
        [{"patch": f"../patches/{p}"}] + ticks("R2-B5c"), "VEN alexandria steerer recalled", mods=[], control="R2-C-U10")
    exp("R2-C-U10", ["control for U10 jobs"], U10, [{"patch": "../patches/identity.py"}] + ticks("R2-C-U10"),
        "identity patch (save + reload)", mods=[], control="-")

    # R01/R09 home bonus counting: wien steers venice (direct link); recall it (catalogue B4)
    p = patch_file("b4_recall_wien.py", "R01/R09: recall VEN's wien steerer (direct link into the home node).",
                   'return sp.recall_merchant(t, "VEN", "wien")')
    exp("R2-B4", ["R01 row 7", "R09 row 10", "R08 row 1 (weights without VEN at wien)"], E00,
        [{"patch": f"../patches/{p}"}] + ticks("R2-B4"), "VEN wien steerer recalled", control="E01c (round 1)")

    # R04: the transfer fraction = amount of the transfer_trade_power relation (U25 LDU 1.000, U04 all 0.500)
    for amt, tag in ((0.5, "05"), (1.0, "10")):
        p = patch_file(f"transfer_man_{tag}.py", f"R04: add transfer_trade_power MAN -> VEN amount={amt:.3f} (is_enforced) on 1444.12.1.",
                       f'return h.add_transfer(t, "MAN", "VEN", {amt}, "1444.12.1")', helpers=True)
        exp(f"R2-T{tag}", ["R04 row 4 (what sets the fraction)", "R04 row 2 (flag without t_out)", "R04 row 3 (transfers by diplomatic setting)"], E00,
            [{"patch": f"../patches/{p}"}] + ticks(f"R2-T{tag}"), f"transfer relation MAN -> VEN amount {amt}", ai_off=("VEN", "MAN"),
            control="E01c (round 1)")

    # R04/R14 void E20c: tributary needs the overlord flag (00_subject_types.txt: forced_tributary_state / can_create_tributaries_flag)
    e = effects_file("tributary_man.txt", "set_country_flag = forced_tributary_state\ncreate_subject = {\n\tsubject_type = tributary_state\n\tsubject = MAN\n}\nclr_country_flag = forced_tributary_state\n")
    exp("R2-TRIB", ["R04 row 4 (subject types)", "fix of void E20c"], E00, [{"effects": f"../effects/{e}"}] + ticks("R2-TRIB"),
        "MAN tributary of VEN (with forced_tributary_state flag)", control="E01d (round 1)")

    # R02/R09/R14: has_capital follows capital or main trade port (E19 moved both inside venice)
    p = patch_file("port_zara.py", "R02/R09: VEN main trade port -> Zara (4753, ragusa node); capital stays Venezia (112).",
                   'return h.set_trade_port(t, "VEN", 4753)', helpers=True)
    exp("R2-PORT", ["R02 row 1", "R09 row 6", "R14 open row (has_capital)"], E00, [{"patch": f"../patches/{p}"}] + ticks("R2-PORT"),
        "VEN trade_port 112 -> 4753 (ragusa node), capital unchanged", control="E01c (round 1)")
    e = effects_file("capital_zara.txt", "set_capital = 4753\n")
    exp("R2-CAP", ["R02 row 1", "R09 row 6"], E00, [{"effects": f"../effects/{e}"}] + ticks("R2-CAP"),
        "VEN capital 112 -> 4753 (ragusa node) via set_capital (does trade_port follow?)", control="E01d (round 1)")

    # R01/R10/R07 embargo (defines: EMBARGO_BASE_EFFICIENCY 0.5, EMBARGO_MERCANTILISM_EFFICIENCY 50)
    p = patch_file("embargo_rag.py", "R01/R10: VEN embargoes RAG (RAG has power at ragusa and venice, where VEN is strong).",
                   'return h.add_embargo(t, "VEN", "RAG")', helpers=True)
    exp("R2-EMB", ["R01 row 4 (embargo size)", "R10 row 4 (magnitude)", "R10 row 5 (money)", "R07 row 3"], E00,
        [{"patch": f"../patches/{p}"}] + ticks("R2-EMB"), "VEN embargo on RAG (save patch, U25 format)", ai_off=("VEN", "RAG"),
        control="E01c (round 1)")

    # R01/R06/R07/R08 one idea at a time (E22's console command gives all 7)
    e = effects_file("idea_trade_1.txt", "add_idea_group = trade_ideas\nadd_idea = shrewd_commerce_practise\n")
    exp("R2-IDEA1", ["R01 row 3 (cap, single idea)", "R06 row 1 (constants)", "R07 row 4", "R08 row 2"], E00,
        [{"effects": f"../effects/{e}"}] + ticks("R2-IDEA1"), "trade_ideas group + first idea (effects; add_idea untested)",
        control="E01d (round 1)")
    e = effects_file("idea_trade_2.txt", "add_idea_group = trade_ideas\nadd_idea = shrewd_commerce_practise\nadd_idea = merchant_adventures\n")
    exp("R2-IDEA2", ["as R2-IDEA1 (compare with it)"], E00, [{"effects": f"../effects/{e}"}] + ticks("R2-IDEA2"),
        "trade_ideas + first two ideas", control="R2-IDEA1")

    # R08 strength functional form: +25 % gave add 0.071 -> 0.083 (E08); two more levels
    for pct, key in ((50, "exp_trade_steering_50"), (100, "exp_trade_steering_100")):
        e = effects_file(f"steer_{pct}.txt", f"add_country_modifier = {{\n\tname = {key}\n\tduration = -1\n}}\n")
        exp(f"R2-STEER{pct}", ["R08 row 2 (strength a_c functional form)"], E00, [{"effects": f"../effects/{e}"}] + ticks(f"R2-STEER{pct}"),
            f"+{pct} % trade_steering", control="E01d / E08 (round 1)")

    # R11/R05 ships at a passive node (catalogue B8) and privateers (R10)
    p = patch_file("ships_constantinople.py", "R11/R05: VEN light-ship fleet -> protect trade at constantinople (VEN passive there).",
                   'return sp.set_light_ship_mission(t, "VEN", "constantinople")')
    exp("R2-SHIPCON", ["R11 row 4 (income effect)", "R05 row 4 (threshold with ships)"], E00, [{"patch": f"../patches/{p}"}] + ticks("R2-SHIPCON"),
        "VEN light ships protect constantinople", control="E01c (round 1)")
    p = patch_file("privateer_ragusa.py", "R10 (experimental): VEN light-ship fleet privateering at ragusa (mission key renamed).",
                   'return h.privateer(t, "VEN", "ragusa")', helpers=True)
    exp("R2-PRIV", ["R10 rows 1-2 (privateer power, residual nodes)", "R07 row 3"], E00, [{"patch": f"../patches/{p}"}] + ticks("R2-PRIV"),
        "VEN fleet privateer_mission at ragusa (experimental format)", control="E01c (round 1)")

    # R13 trade company (later era): NED 1618, its non-state overseas provinces into a trade company
    e = effects_file("ned_trade_company.txt", "every_owned_province = {\n\tlimit = { is_territory = yes }\n\tadd_to_trade_company = NED\n}\n")
    exp("R2-TC", ["R13 row 4 (trade company region effects)", "R14 open row (trade company)"], NED18,
        [{"effects": f"../effects/{e}"}] + ticks("R2-TC", "1618.07.01", "1618.08.01"), "NED territories added to a trade company (effect untested)",
        ai_off=("NED",), mods=[], control="R2-C-NED18")
    exp("R2-C-NED18", ["control for NED 1618 jobs"], NED18, [{"patch": "../patches/identity.py"}] + ticks("R2-C-NED18", "1618.07.01", "1618.08.01"),
        "identity patch", ai_off=("NED",), mods=[], control="-")

    # R13 void E16 (Venezia already CoT 3): Verona (108) is level 1; trade depot (province_trade_power_modifier = 1)
    e = effects_file("cot_verona.txt", "108 = {\n\tadd_center_of_trade_level = 1\n}\n")
    exp("R2-COT", ["R13 row 1 (centre-of-trade step)", "fix of void E16"], E00, [{"effects": f"../effects/{e}"}] + ticks("R2-COT"),
        "Verona (108) centre of trade level 1 -> 2", control="E01d (round 1)")
    e = effects_file("depot_venezia.txt", "112 = {\n\tadd_building = trade_depot\n}\n")
    exp("R2-DEPOT", ["R13 row 3 (buildings other than the marketplace)"], E00, [{"effects": f"../effects/{e}"}] + ticks("R2-DEPOT"),
        "trade depot built in Venezia (112)", control="E01d (round 1) / E17 marketplace")

    # R01 row 2: DIP change before the first tick in a fresh game (cross-game; compare GEN with the E00 base game)
    e = effects_file("gen_dip_plus2.txt", "GEN = { change_dip = 2 }\n")
    EXPS.append(dict(id="R2-DIPFRESH", rows=["R01 row 2 (cross-game DIP pattern)"], base=None, start_date="1444.11.11",
                     script=[{"effects": f"../effects/{e}"}, {"date": "1444.12.01", "outfname": "../out/R2-DIPFRESH/base_1444.12.01.eu4"}],
                     change="new game; GEN ruler DIP +2 on 1444.11.11 (before the first tick)", ai_off=[], mods=EXP_MOD,
                     control="E00 base (another fresh game) and the S01/U07 pattern"))

    order = []
    for x in EXPS:
        spec = {"nation": "NED" if x["base"] == NED18 else "VEN", "mods": x["mods"], "observe": True, "ai_off": x["ai_off"],
                "base_save": x["base"], "script": x["script"]}
        if x.get("start_date"):
            spec["start_date"] = x["start_date"]
        write(HERE / "jobs" / f"{x['id']}.json", json.dumps(spec, indent=1) + "\n")
        order.append(x["id"])
    # by value: controls first (each base), then the topic-closing jobs
    first = ["R2-C-U10", "R2-B5a", "R2-B5b", "R2-B5c", "R2-T05", "R2-T10", "R2-PORT", "R2-CAP", "R2-EMB", "R2-B4",
             "R2-STEER50", "R2-STEER100", "R2-IDEA1", "R2-IDEA2", "R2-COT", "R2-DEPOT", "R2-TRIB", "R2-SHIPCON", "R2-PRIV", "R2-DIPFRESH",
             "R2-C-NED18", "R2-TC"]
    assert sorted(first) == sorted(order), set(first) ^ set(order)
    write(HERE / "ORDER.txt", "\n".join(first) + "\n")
    write(HERE / "jobs_table.json", json.dumps(EXPS, indent=1) + "\n")
    print(len(order), "jobs written")


if __name__ == "__main__":
    build()
