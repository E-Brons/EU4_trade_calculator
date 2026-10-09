"""R02 final: independent whole-corpus check of the away-collection penalty (new code, does not reuse r02_*/ver_*/ver2_* logic).

Definitions (all from the saves plus the static map data/tradenodes.json):
  home(c)     = trade node containing province countries[c].trade_port
  action      = 'away_collect' entry has key `total`, node != home(c); 'home_collect' same at home;
                'steer' key `type`, no `total`; 'idle' has_trader but neither `type` nor `total`; 'passive' none of these
  baseline    = clusters (|diff| <= 0.0015, >= 2 members) of max_demand of the country's passive, embargo-clean, non-home entries
  embargo-clean (c, n) = no tag in countries[c].trade_embargoed_by has an entry at n with province_power + ship_power > 0
Run from backend/:  .venv/bin/python scripts/research/final_r02_core.py
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

TOL = 0.0015
NODEMAP = json.loads((Path(__file__).resolve().parents[2] / "data" / "tradenodes.json").read_text())["nodes"]
PROV2NODE = {p: nid for nid, n in NODEMAP.items() for p in n["member_provinces"]}
CAMPAIGN = ["S79", "S80", "U03", "U04", "U05", "U06"]
DUPLICATES = {"U01", "U02"}  # byte-copies of S80 / S79


def clusters(vals: list[float]) -> list[float]:
    vals = sorted(vals)
    out, cur = [], []
    for v in vals:
        if cur and v - cur[-1] > TOL:
            out.append(cur)
            cur = []
        cur.append(v)
    if cur:
        out.append(cur)
    multi = [statistics.median(c) for c in out if len(c) >= 2]
    return multi


def load(entry):
    nodes = common.nodes(entry)
    countries = common.block(entry, "countries")
    return nodes, countries


def classify(e: dict, n: str, home: str | None):
    if "total" in e:
        return "home_collect" if n == home else "away_collect"
    if "type" in e:
        return "steer"
    if e.get("has_trader"):
        return "idle"
    return "passive"


def per_save(entry):
    nodes, countries = load(entry)
    sid = entry["id"]
    homes = {}
    for tag, c in countries.items():
        if isinstance(c, dict) and "trade_port" in c:
            homes[tag] = PROV2NODE.get(int(c["trade_port"]))
    # entries by (tag, node)
    rows = defaultdict(dict)  # tag -> node -> entry
    for nd in nodes:
        nid = nd["definitions"]
        for tag, e in nd.items():
            if isinstance(e, dict) and "max_demand" in e and re.match(r"^[A-Z0-9]{2,4}$", tag):
                rows[tag][nid] = e
    # own power of embargoers
    def clean(tag, nid):
        emb = countries.get(tag, {}).get("trade_embargoed_by") if isinstance(countries.get(tag), dict) else None
        if not emb:
            return True
        if isinstance(emb, str):
            emb = [emb]
        for x in emb:
            ee = rows.get(x, {}).get(nid)
            if ee and (float(ee.get("province_power", 0) or 0) + float(ee.get("ship_power", 0) or 0)) > 0:
                return False
        return True

    res = Counter()
    exceptions = defaultdict(list)
    detail = {}
    FACTORS = [0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7]
    for tag, byn in rows.items():
        home = homes.get(tag)
        cls_of = {n: classify(e, n, home) for n, e in byn.items()}
        # all other non-away, embargo-clean entries of the same country in the same save
        pool = [(n, float(e["max_demand"])) for n, e in byn.items() if cls_of[n] != "away_collect" and clean(tag, n)]
        for n, e in byn.items():
            cls = cls_of[n]
            if cls == "passive":
                continue
            if not clean(tag, n):
                res[(cls, "embargoed_skip")] += 1
                continue
            md = float(e["max_demand"])
            others = [v for n2, v in pool if n2 != n]
            if not others:
                res[(cls, "no_baseline")] += 1
                continue
            full = any(abs(md - b) <= TOL for b in others)
            half = any(abs(md - 0.5 * b) <= TOL for b in others)
            k = "ambiguous" if (full and half) else "full" if full else "half" if half else "neither"
            res[(cls, k)] += 1
            if cls == "away_collect":
                res[("away_group", "campaign" if sid in CAMPAIGN else "start", k)] += 1
            if re.fullmatch(r"C\d\d", tag):
                res[("colonial", cls, k)] += 1
            if cls == "away_collect":
                for f in FACTORS:
                    if any(abs(md - f * b) <= TOL for b in others):
                        res[("placebo", f)] += 1
            if k == "neither" and cls == "away_collect" or (cls == "away_collect" and k != "half") or (cls in ("steer", "idle", "home_collect") and k in ("half", "ambiguous")):
                exceptions[(cls, k)].append((sid, tag, n, md, sorted({round(b, 3) for b in others})[:6]))
    detail["homes"] = homes
    detail["rows"] = rows
    detail["countries"] = countries
    detail["clean"] = clean
    return res, exceptions, detail


def capital_check(detail):
    homes, countries = detail["homes"], detail["countries"]
    rows = detail["rows"]
    n_hc = n_hc_ok = n_hc_bad = n_cap_ne_port = n_with_port = 0
    bad = []
    for tag, c in countries.items():
        if not isinstance(c, dict) or "trade_port" not in c:
            continue
        n_with_port += 1
        if "capital" in c and PROV2NODE.get(int(c["capital"])) != homes.get(tag):
            n_cap_ne_port += 1
        hc_nodes = [n for n, e in rows.get(tag, {}).items() if e.get("has_capital")]
        for n in hc_nodes:
            n_hc += 1
            if n == homes.get(tag):
                n_hc_ok += 1
            else:
                n_hc_bad += 1
                bad.append((tag, n, homes.get(tag)))
    return n_with_port, n_hc, n_hc_ok, n_hc_bad, n_cap_ne_port, bad


def main():
    entries = [e for e in common.entries()]
    tot = Counter()
    tot_all = Counter()
    exc_all = defaultdict(list)
    cap_tot = Counter()
    cap_bad = []
    colonial = Counter()
    saved = {}
    for e in entries:
        sid = e["id"]
        res, exc, detail = per_save(e)
        pw, hc, ok, bad, cne, badl = capital_check(detail)
        for k, v in res.items():
            tot_all[k] += v
            if sid not in DUPLICATES:
                tot[k] += v
        if sid not in DUPLICATES:
            for k, v in exc.items():
                exc_all[k].extend(v)
            cap_tot.update({"with_port": pw, "has_capital_entries": hc, "at_port_node": ok, "elsewhere": bad, "capital_node_ne_port_node": cne})
            cap_bad += badl
            # colonial nations (tags C00-C17) and colonial_parent holders
            for tag, byn in detail["rows"].items():
                c = detail["countries"].get(tag, {})
                is_col = bool(re.match(r"^C\d\d$", tag)) or (isinstance(c, dict) and "colonial_parent" in c)
                if not is_col:
                    continue
                has_hc = any(x.get("has_capital") for x in byn.values())
                colonial[("country_saves", has_hc)] += 1
        if sid in CAMPAIGN:
            saved[sid] = detail
        print(sid, "done", flush=True)

    print("\n== action classes, distinct saves (U01/U02 excluded), embargo-clean entries with a baseline ==")
    classes = ["away_collect", "home_collect", "steer", "idle"]
    for cls in classes:
        row = {k: tot[(cls, k)] for k in ("half", "full", "ambiguous", "neither", "no_baseline", "embargoed_skip")}
        n = sum(row[k] for k in ("half", "full", "ambiguous", "neither"))
        print(cls, "tested", n, row)
    print("away_collect by group:", {k[1:]: v for k, v in tot.items() if k[0] == "away_group"})
    print("colonial-nation tags C00-C17:", {k[1:]: v for k, v in tot.items() if k[0] == "colonial"})
    print("placebo (away_collect entries matching factor x another entry's value, distinct saves):", {f: tot[("placebo", f)] for f in (0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7)})
    print("\nall 86 manifest entries incl. U01/U02 copies:")
    for cls in classes:
        row = {k: tot_all[(cls, k)] for k in ("half", "full", "ambiguous", "neither")}
        print(cls, row)
    print("\n== exceptions (distinct saves) ==")
    for key, lst in sorted(exc_all.items()):
        print(key, len(lst))
        for x in lst[:25]:
            print("   ", x)

    print("\n== has_capital / trade_port / capital (distinct saves) ==", dict(cap_tot), "mismatches:", cap_bad[:5])
    print("colonial-nation country-saves (C00-C17 or colonial_parent) with / without a has_capital entry:",
          colonial[("country_saves", True)], colonial[("country_saves", False)])

    # within-country switches across consecutive campaign saves
    print("\n== switches between consecutive campaign saves ==")
    enter, leave = [], []
    for a, b in zip(CAMPAIGN, CAMPAIGN[1:]):
        da, db = saved[a], saved[b]
        for tag, rb in db["rows"].items():
            ra = da["rows"].get(tag)
            if not ra:
                continue
            ha, hb = da["homes"].get(tag), db["homes"].get(tag)
            ctl = []
            for n, eb in rb.items():
                ea = ra.get(n)
                if ea and classify(ea, n, ha) == "passive" and classify(eb, n, hb) == "passive" and da["clean"](tag, n) and db["clean"](tag, n) and float(ea["max_demand"]) > 0:
                    ctl.append(float(eb["max_demand"]) / float(ea["max_demand"]))
            if len(ctl) < 3:
                continue
            m = statistics.median(ctl)
            for n, eb in rb.items():
                ea = ra.get(n)
                if not ea or not (da["clean"](tag, n) and db["clean"](tag, n)) or float(ea["max_demand"]) <= 0:
                    continue
                ca, cb = classify(ea, n, ha), classify(eb, n, hb)
                r = (float(eb["max_demand"]) / float(ea["max_demand"])) / m
                if cb == "away_collect" and ca in ("steer", "idle", "passive"):
                    enter.append((a + ">" + b, tag, n, ca, round(r, 4)))
                elif ca == "away_collect" and cb in ("steer", "idle", "passive"):
                    leave.append((a + ">" + b, tag, n, cb, round(r, 4)))
    print("entering away:", len(enter), "within [0.47,0.53]:", sum(1 for x in enter if 0.47 <= x[4] <= 0.53))
    for x in enter:
        print("   ", x)
    print("leaving away:", len(leave), "within [1.97,2.03]:", sum(1 for x in leave if 1.97 <= x[4] <= 2.03))
    for x in leave:
        print("   ", x)

    # SUN in S80: who embargoes it
    d = saved["S80"]
    c = d["countries"]
    sun = c.get("SUN", {})
    print("\n== SUN in S80 ==", "trade_embargoed_by", sun.get("trade_embargoed_by"), "trade_embargoes", sun.get("trade_embargoes"))
    lst = [t for t, v in c.items() if isinstance(v, dict) and v.get("trade_embargoes") and "SUN" in (v["trade_embargoes"] if isinstance(v["trade_embargoes"], list) else [v["trade_embargoes"]])]
    print("countries whose trade_embargoes lists SUN:", lst)
    for t in lst:
        for n in ("malacca", "burma", "gulf_of_siam", "canton", "philippines"):
            ee = d["rows"].get(t, {}).get(n)
            print("   ", t, n, ee and {k: ee.get(k) for k in ("province_power", "ship_power", "max_pow", "prev")})
    for n in ("malacca", "burma", "gulf_of_siam", "canton", "philippines"):
        ee = d["rows"].get("SUN", {}).get(n)
        print("   SUN", n, ee and {k: ee.get(k) for k in ("max_demand", "has_trader", "type", "total")})


if __name__ == "__main__":
    main()
