"""Income: derive each country's trade efficiency X from the save + game files instead of observing it.

X_obs = identified at the capital node (money / share_total - 1 - merchant term), snapped to 0.01 inside the interval
allowed by the 3-decimal truncation of the capital `money` (income_x_snap.py: 5,368 of 5,392 away entries exact).
X_derived = sum of `trade_efficiency` over the country's active sources:
  diplomatic technology (cumulative over common/technologies/dip.txt levels), ideas (national: traditions + first n
  ideas (+ ambition at 7); generic group: first n ideas (+ bonus at 7)), government reforms, country modifiers,
  active policies, estate privileges, advisors (via active_advisors ids -> advisor type), ruler personalities;
  each source's value = every `trade_efficiency = v` inside its block in the game files (conditions ignored).
Prints the residual X_obs - X_derived per era and its most common values, and the share reproduced exactly.
Run from backend/: PYTHONPATH=. .venv/bin/python scripts/research/income_derive_x.py
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from app.trade import calc, corpus, savefile

GAME = Path.home() / "Library/Application Support/Steam/steamapps/common/Europa Universalis IV/common"
TE = re.compile(r"\btrade_efficiency\s*=\s*(-?[\d.]+)")


def blocks(text: str):
    """top-level `name = { ... }` blocks (name, body)."""
    i, n = 0, len(text)
    while i < n:
        m = re.compile(r"(?m)^\s*([A-Za-z0-9_\-\.']+)\s*=\s*\{").search(text, i)
        if not m:
            return
        depth, j = 0, m.end() - 1
        while j < n:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        yield m.group(1), text[m.end():j]
        i = j + 1


def strip_comments(t: str) -> str:
    return re.sub(r"#[^\n]*", "", t)


SKIP = ("conditional_modifier", "trigger", "potential", "allow", "ai_will_do", "effect", "on_granted", "on_revoked",
        "on_invalid", "can_select", "can_revoke", "is_valid", "on_activate", "on_deactivate", "modifier_by_land_ownership",
        "influence_scaled_modifier", "loyalty_scaled_modifier", "mechanics", "custom_trigger_tooltip")


def unconditional(body: str) -> str:
    """drop nested blocks whose effect depends on a condition (conditional_modifier, trigger, effects, ...)."""
    out, i = [], 0
    pat = re.compile(r"\b(" + "|".join(SKIP) + r")\s*=\s*\{")
    while True:
        m = pat.search(body, i)
        if not m:
            out.append(body[i:]); break
        out.append(body[i:m.start()])
        depth, j = 0, m.end() - 1
        while j < len(body):
            if body[j] == "{": depth += 1
            elif body[j] == "}":
                depth -= 1
                if depth == 0: break
            j += 1
        i = j + 1
    return "".join(out)


def te_sum(body: str) -> float:
    return sum(float(v) for v in TE.findall(unconditional(body)))


def source_map(folder: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for f in sorted((GAME / folder).glob("*.txt")):
        for name, body in blocks(strip_comments(f.read_text(encoding="latin-1"))):
            v = te_sum(body)
            if v:
                out[name] = out.get(name, 0.0) + v
    return out


def idea_groups() -> dict[str, dict]:
    out = {}
    for f in sorted((GAME / "ideas").glob("*.txt")):
        for name, body in blocks(strip_comments(f.read_text(encoding="latin-1"))):
            sub = list(blocks(body))
            ideas = [(n, te_sum(b)) for n, b in sub if n not in ("start", "bonus", "trigger", "ai_will_do", "category", "free", "important")]
            out[name] = {"start": sum(te_sum(b) for n, b in sub if n == "start"),
                         "bonus": sum(te_sum(b) for n, b in sub if n == "bonus"),
                         "ideas": [v for _n, v in ideas], "national": bool(re.search(r"(?m)^\s*free\s*=\s*yes", body))}
    return out


def dip_table() -> list[float]:
    t = strip_comments((GAME / "technologies" / "dip.txt").read_text(encoding="latin-1"))
    techs = re.split(r"(?m)^technology\s*=\s*\{", t)[1:]
    cum, out = 0.0, []
    for b in techs:
        cum += te_sum(b)
        out.append(round(cum, 4))
    return out


def advisor_types() -> dict[str, float]:
    return source_map("advisortypes")


IDEAS, DIP = idea_groups(), dip_table()
MAPS = {k: source_map(k) for k in ("government_reforms", "event_modifiers", "static_modifiers", "policies",
                                   "estate_privileges", "ruler_personalities", "parliament_issues", "factions")}
ADV = advisor_types()


def country_block(gs: str, tag: str) -> str | None:
    c0 = gs.find("\ncountries={")
    i = gs.find(f"\n\t{tag}={{", c0)
    if i < 0:
        return None
    return gs[i:gs.find("\n\t}", i)]


def advisors_by_id(gs: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(r"\n\t\t\tadvisor=\{\n(.*?)\n\t\t\t\}", gs, re.S):
        b = m.group(1)
        ty = re.search(r"\n?\t*type=(\w+)", b)
        i = re.search(r"id=\{\s*id=(\d+)", b)
        if ty and i:
            out[i.group(1)] = ty.group(1)
    return out


def active_advisors(gs: str) -> dict[str, list[str]]:
    out = defaultdict(list)
    i = gs.find("\nactive_advisors={")
    if i < 0:
        return out
    end = gs.find("\n}", i)
    for m in re.finditer(r"\n\t([A-Z0-9]{3})=\{(.*?)\n\t\}", gs[i:end], re.S):
        out[m.group(1)] = re.findall(r"id=(\d+)", m.group(2))
    return out


def derive(gs: str, tag: str, adv_types: dict[str, str], adv_ids: list[str]) -> tuple[float, dict]:
    b = country_block(gs, tag)
    parts = defaultdict(float)
    if b is None:
        return 0.0, parts
    m = re.search(r"\n\t\t\tdip_tech=(\d+)", b)
    if m and int(m.group(1)) < len(DIP):
        parts["dip_tech"] = DIP[int(m.group(1))]
    ig = re.search(r"\n\t\tactive_idea_groups=\{(.*?)\n\t\t\}", b, re.S)
    if ig:
        for g, n in re.findall(r"(\w+)=(\d+)", ig.group(1)):
            d = IDEAS.get(g)
            if not d:
                continue
            n = int(n)
            v = sum(d["ideas"][:n]) + (d["start"] if d["national"] or "_ideas" in g and g[:3].isupper() else 0)
            if n >= 7:
                v += d["bonus"]
            if v:
                parts["ideas:" + g] += v
    rs = re.search(r"\n\t\t\treform_stack=\{(.*?)\n\t\t\t\}", b, re.S)
    if rs:
        rf = re.search(r"reforms=\{(.*?)\}", rs.group(1), re.S)
        for r in re.findall(r'"(\w+)"', rf.group(1) if rf else ""):
            if r in MAPS["government_reforms"]:
                parts["reform:" + r] += MAPS["government_reforms"][r]
    for mod in re.findall(r'\n\t\tmodifier=\{\n\t\t\tmodifier="(\w+)"', b):
        for k in ("event_modifiers", "static_modifiers"):
            if mod in MAPS[k]:
                parts["modifier:" + mod] += MAPS[k][mod]
                break
    for pol in re.findall(r'\n\t\tactive_policy=\{\n\t\t\tpolicy="(\w+)"', b):
        if pol in MAPS["policies"]:
            parts["policy:" + pol] += MAPS["policies"][pol]
    for gp in re.findall(r"granted_privileges=\{(.*?)\n\t\t\t\}", b, re.S):
        for priv in re.findall(r"\b(estate_\w+)", gp):
            if priv in MAPS["estate_privileges"]:
                parts["privilege:" + priv] += MAPS["estate_privileges"][priv]
    for i in adv_ids:
        ty = adv_types.get(i)
        if ty and ty in ADV:
            parts["advisor:" + ty] += ADV[ty]
    mon = re.search(r"\n\t\tmonarch=\{\s*id=(\d+)", b)
    for p in re.findall(r"\n\t\t\t\t(\w+_personality)=yes", b):
        if p in MAPS["ruler_personalities"]:
            parts["personality:" + p] += MAPS["ruler_personalities"][p]
    return round(sum(parts.values()), 4), parts


def x_observed(world) -> dict[str, float]:
    out = {}
    for (node, tag), r in world.recorded.entries.items():
        e = world.inputs.entries[(node, tag)]
        if e.has_capital and r.money and r.share_total and r.share_total > 0.05:
            mb = calc.rule_merchant_bonus(e.has_trader)
            lo = r.money / r.share_total - 1 - mb
            hi = (r.money + 0.001) / r.share_total - 1 - mb
            cand = [v / 100 for v in range(int(lo * 100) - 1, int(hi * 100) + 2) if lo - 1e-9 <= v / 100 < hi + 1e-9]
            if len(cand) == 1:
                out[tag] = cand[0]
    return out


def main() -> None:
    by_era = defaultdict(Counter)
    resid_by_era = defaultdict(Counter)
    examples = defaultdict(list)
    ents = [e for e in corpus.selected() if "/vanilla/" in e.get("zip", "")]  # natural games only (no experiment mod)
    for entry, world in corpus.iter_worlds(ents):
        path = corpus.locate(entry, Path("/tmp/eu4_income_tmp"))
        text = savefile.read_save_text(path)
        gs = text.gamestate
        era = world.inputs.date.split(".")[0][:3] + "x"
        xo = x_observed(world)
        adv_types, act = advisors_by_id(gs), active_advisors(gs)
        for tag, x in xo.items():
            xd, parts = derive(gs, tag, adv_types, act.get(tag, []))
            res = round(x - xd, 2)
            by_era[era]["countries"] += 1
            resid_by_era[era][res] += 1
            if len(examples[era]) < 4 and res not in (0.05,):
                examples[era].append((entry["id"], tag, x, xd, dict(parts)))
    for era in sorted(by_era):
        n = by_era[era]["countries"]
        print(f"{era}: {n} countries; residual X_obs - X_derived most common: {resid_by_era[era].most_common(8)}")
        for ex in examples[era][:3]:
            print("   ", ex)


if __name__ == "__main__":
    main()
