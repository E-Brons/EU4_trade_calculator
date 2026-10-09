"""R01 final, part 2: domestic vs foreign classes, alternative classification, home bonus (+0.1 per steering merchant).
Independent code. Run from backend/: .venv/bin/python scripts/research/final_r01_classes.py"""
import collections
import final_r01_lib as L

TOL = L.TOL
ALL = L.all_saves()
DIS = L.distinct(ALL)
PLAYED = {"S79", "S80", "U01", "U02", "U03", "U04", "U05", "U06"}


def analyse(sid, s):
    """yield per non-embargoed country with a single-valued foreign scalar F: dict(info)."""
    tags = sorted({t for n in s["nodes"].values() for t, e in n["e"].items() if e["md"] is not None})
    for t in tags:
        if s["c"].get(t, {}).get("emb_by"):
            continue
        rows = []
        for nid, n in s["nodes"].items():
            e = n["e"].get(t)
            rows.append((nid, e, n["top"] == t, n))
        ordin = [r for r in rows if not (r[1]["cap"] or r[2] or L.is_away(r[1]))]
        vals = sorted({r[1]["md"] for r in ordin})
        if len(vals) != 1:
            yield {"tag": t, "F": None, "ordin_vals": vals, "rows": rows}
            continue
        yield {"tag": t, "F": vals[0], "rows": rows}


# ---------- A. classes
cnt = collections.Counter()
top_eq = []          # (sid, tag, H, F, T values)
exc = []
hf = collections.Counter()      # home vs foreign
top_groups_multi = 0
top_groups = 0
alt = collections.Counter()
nodes_home_count = 0
for sid, s in DIS:
    for g in analyse(sid, s):
        if g["F"] is None:
            continue
        F = g["F"]; rows = g["rows"]
        home = [r for r in rows if r[1]["cap"]]
        H = home[0][1]["md"] if home else None
        if H is not None:
            hf["home<foreign" if H < F - TOL else "home>foreign" if H > F + TOL else "home=foreign"] += 1
        tops = [r for r in rows if r[2] and not r[1]["cap"] and not L.is_away(r[1])]
        if tops:
            tv = sorted({r[1]["md"] for r in tops})
            top_groups += 1
            top_groups_multi += len(tv) > 1
        if H is None or not tops:
            continue
        for r in tops:
            m = r[1]["md"]
            eqH = abs(m - H) <= TOL; eqF = abs(m - F) <= TOL
            disc = abs(H - F) > TOL
            if eqH and eqF:
                k = "top==home==foreign"
            elif eqH:
                k = "top==home"
            elif eqF:
                k = "top==foreign"
            else:
                k = "top differs from both"
                exc.append((sid, g["tag"], r[0], m, H, F))
            cnt[(k, "H!=F" if disc else "H=F")] += 1
        # alternative class "largest effective val at node" among non-home non-away non-top nodes
        if abs(H - F) > TOL:
            for nid, e, is_top, n in rows:
                if e["cap"] or L.is_away(e) or is_top or not e["val"]:
                    continue
                mx = max((x["val"] or 0) for x in n["e"].values())
                if (e["val"] or 0) >= mx:
                    alt["largest val, not top_provinces: md==F" if abs(e["md"] - F) <= TOL else "largest val, not top_provinces: md==H" if abs(e["md"] - H) <= TOL else "largest val, not top_provinces: other"] += 1
print("[A] top-province node md vs home md vs foreign scalar (one row per top node; non-embargoed, single-valued F):")
for k, v in sorted(cnt.items()):
    print("    ", k, v)
print("    top-node groups:", top_groups, " with several distinct top-node values:", top_groups_multi)
print("    home vs foreign (groups with a home entry):", dict(hf))
print("    exceptions top differs from both (grouped):", collections.Counter((e[0], e[1]) for e in exc))
for e in exc[:40]:
    print("       ", e)
print("[A2] alternative class 'largest val at node' (where not top_provinces, groups with home!=foreign):", dict(alt))

# ---------- B. home bonus
res = collections.defaultdict(list)
for sid, s in ALL:
    for g in analyse(sid, s):
        if g["F"] is None:
            continue
        rows = g["rows"]
        home = [r for r in rows if r[1]["cap"]]
        tops = [r for r in rows if r[2] and not r[1]["cap"] and not L.is_away(r[1])]
        if not home or not tops:
            continue
        tv = {r[1]["md"] for r in tops}
        if len(tv) != 1:
            continue
        T = tv.pop(); H = home[0][1]["md"]
        ks = sum(1 for r in rows if r[1]["steer"] and r[1]["trader"])
        away = sum(1 for r in rows if L.is_away(r[1]) and r[1]["trader"])
        homecoll = home[0][1]["trader"]
        res[sid].append((g["tag"], round(H - T, 4), ks, away, homecoll, home[0][1]["steer"]))
print("[B] home - top by save kind (non-embargoed, single top value):")
summ = collections.Counter()
for sid, lst in res.items():
    grp = "played(S79,S80,U01-U06)" if sid in PLAYED else "start/other"
    for tag, d, ks, away, hc, hs in lst:
        hasd = abs(d) > TOL
        if away:
            cat = "a merchant collects away"
        elif ks >= 1:
            cat = "steering>=1, nobody away"
        else:
            cat = "no steering merchant, nobody away"
        fit = abs(d - 0.1 * ks) <= 0.0025
        summ[(grp, cat, "diff" if hasd else "equal", "fits 0.1*k" if fit else "no fit")] += 1
for k, v in sorted(summ.items()):
    print("    ", k, v)
print("[B2] every played-save country-save where home-top != 0 (or steering>=1, nobody away):")
for sid in sorted(PLAYED):
    for tag, d, ks, away, hc, hs in sorted(res.get(sid, [])):
        if abs(d) > TOL or (ks >= 1 and not away):
            print("     ", sid, tag, "home-top", d, "steering merchants", ks, "away merchants", away, "home merchant", hc, "0.1*k", round(0.1 * ks, 3))
