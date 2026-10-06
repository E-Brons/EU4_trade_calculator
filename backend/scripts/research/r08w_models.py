"""R08 Q1: which power sets the node `steer_power` weights? Tested only on tick-day saves (R12 final: the stored weights are
that day's computation; start snapshots and U07-U09 hold uniform pre-tick weights and cannot test any rule).

A model gives each outgoing link a pull; weight_i = pull_i / sum(pull). A node matches when every weight is within 0.0015.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402
from app.parsing.tradenodes import load_trade_graph  # noqa: E402

TICK_DAY = ["U04", "U10", "U14", "U20", "U25", "U27", "U28", "U29"]
G = load_trade_graph()


def downstream(node: str, memo: dict = {}) -> frozenset[str]:
    if node not in memo:
        out: set[str] = set()
        for t in G.outgoing(node):
            out |= {t} | downstream(t)
        memo[node] = frozenset(out)
    return memo[node]


def f(c, k):
    try:
        return float(c.get(k, 0.0))
    except (TypeError, ValueError):
        return 0.0


def load(sid: str):
    entry = next(e for e in common.entries() if e["id"] == sid)
    nodes = {n["definitions"]: n for n in common.nodes(entry)}
    ents = {nid: {t: c for t, c in n.items() if isinstance(c, dict) and len(t) == 3 and t.isupper() or (isinstance(c, dict) and t[:1] == "C" and t[1:].isdigit())}
            for nid, n in nodes.items()}
    active = defaultdict(set)   # collect or steer nodes per tag
    collect = defaultdict(set)
    for nid, es in ents.items():
        for t, c in es.items():
            if "total" in c or "has_capital" in c:
                active[t].add(nid); collect[t].add(nid)
            if "type" in c:
                active[t].add(nid)
    return nodes, ents, active, collect


def link_of(tag, node, targets, nodeset):
    """Links whose target or its downstream contains one of the tag's nodes."""
    return [i for i, t in enumerate(targets) if nodeset[tag] & ({t} | downstream(t))]


def run(models):
    score = Counter(); total = Counter()
    for sid in TICK_DAY:
        nodes, ents, active, collect = load(sid)
        for nid, n in nodes.items():
            targets = G.outgoing(nid)
            w = [float(x) for x in common.as_list(n.get("steer_power"))]
            if len(targets) < 2 or len(w) != len(targets) or float(n.get("outgoing", 0) or 0) <= 0:
                continue
            total[sid] += 1
            for name, fn in models.items():
                pull = fn(nid, targets, ents[nid], active, collect)
                s = sum(pull)
                if s > 0 and all(abs(p / s - x) <= 0.0015 for p, x in zip(pull, w)):
                    score[(name, sid)] += 1
    for name in models:
        print(f"{name:34s}", " ".join(f"{sid}:{score[(name, sid)]}/{total[sid]}" for sid in TICK_DAY),
              f"| all {sum(score[(name, s)] for s in TICK_DAY)}/{sum(total.values())}")


def eff(c):
    return f(c, "val") - f(c, "t_out") + f(c, "t_in")


def m_steer(power):
    def fn(nid, targets, es, active, collect):
        pull = [0.0] * len(targets)
        for t, c in es.items():
            if "type" in c:
                pull[int(f(c, "steer_power"))] += power(c)
        return pull
    return fn


def m_steer_plus_pullers(power, nodeset_name, ambiguous):
    def fn(nid, targets, es, active, collect):
        nodeset = active if nodeset_name == "active" else collect
        pull = [0.0] * len(targets)
        for t, c in es.items():
            if "type" in c:
                pull[int(f(c, "steer_power"))] += power(c)
            elif not ("total" in c or "has_capital" in c):
                links = link_of(t, nid, targets, nodeset)
                if not links:
                    continue
                if ambiguous == "first":
                    pull[links[0]] += power(c)
                elif ambiguous == "split":
                    for i in links:
                        pull[i] += power(c) / len(links)
                elif ambiguous == "only_unique" and len(links) == 1:
                    pull[links[0]] += power(c)
        return pull
    return fn


if __name__ == "__main__":
    val = lambda c: f(c, "val")  # noqa: E731
    run({
        "steerers val": m_steer(val),
        "steerers eff": m_steer(eff),
        "steer+pullers(active) val first": m_steer_plus_pullers(val, "active", "first"),
        "steer+pullers(active) val split": m_steer_plus_pullers(val, "active", "split"),
        "steer+pullers(active) val uniq": m_steer_plus_pullers(val, "active", "only_unique"),
        "steer+pullers(active) eff first": m_steer_plus_pullers(eff, "active", "first"),
        "steer+pullers(collect) val first": m_steer_plus_pullers(val, "collect", "first"),
        "steer+pullers(collect) eff split": m_steer_plus_pullers(eff, "collect", "split"),
    })


# --- country steering strength a_c (R08 V-R08-1: add = a_c / rank among the add-carrying entries of the same link) ---
def strengths(ents, order="val"):
    """Per-country a_c = median of (add + 0.0005) * rank over its add-carrying steering entries in the save."""
    from statistics import median
    per = defaultdict(list)
    for nid, es in ents.items():
        groups = defaultdict(list)
        for t, c in es.items():
            if "add" in c and "type" in c:
                groups[int(f(c, "steer_power"))].append((t, c))
        for items in groups.values():
            items.sort(key=lambda tc: -f(tc[1], order))
            for rank, (t, c) in enumerate(items, 1):
                per[t].append((f(c, "add") + 0.0005) * rank)
    return {t: median(v) for t, v in per.items()}


def run_strength(order="val", default=0.05, power="val", passive=False):
    score = Counter(); total = Counter(); worst = []
    for sid in TICK_DAY:
        nodes, ents, active, collect = load(sid)
        a = strengths(ents, order)
        for nid, n in nodes.items():
            targets = G.outgoing(nid)
            w = [float(x) for x in common.as_list(n.get("steer_power"))]
            if len(targets) < 2 or len(w) != len(targets) or float(n.get("outgoing", 0) or 0) <= 0:
                continue
            has_passive = any(not ("type" in c or "total" in c or "has_capital" in c) and f(c, "val") > 0
                              and link_of(t, nid, targets, active) for t, c in ents[nid].items())
            key = (sid, "passive" if has_passive else "nopassive")
            total[key] += 1
            pull = [0.0] * len(targets)
            for t, c in ents[nid].items():
                if "type" in c:
                    pull[int(f(c, "steer_power"))] += f(c, power) * a.get(t, default)
            s = sum(pull)
            err = max(abs(p / s - x) for p, x in zip(pull, w)) if s else 9
            if err <= 0.0015:
                score[key] += 1
            elif not has_passive:
                worst.append((err, sid, nid))
    for kind in ("nopassive", "passive"):
        print(f"  {order}/{power}/default={default} {kind}: " + " ".join(f"{sid}:{score[(sid, kind)]}/{total[(sid, kind)]}" for sid in TICK_DAY),
              f"| all {sum(score[(s, kind)] for s in TICK_DAY)}/{sum(total[(s, kind)] for s in TICK_DAY)}")
    return sorted(worst, reverse=True)


def strength_intervals(ents, order="max_pow"):
    """add = trunc3(a / rank) => a in [add * rank, (add + 0.001) * rank). Intersect per country; count conflicts."""
    lo = defaultdict(float); hi = defaultdict(lambda: 9.0); n = Counter()
    for nid, es in ents.items():
        groups = defaultdict(list)
        for t, c in es.items():
            if "add" in c and "type" in c:
                groups[int(f(c, "steer_power"))].append((t, c))
        for items in groups.values():
            items.sort(key=lambda tc: -f(tc[1], order))
            for rank, (t, c) in enumerate(items, 1):
                lo[t] = max(lo[t], f(c, "add") * rank)
                hi[t] = min(hi[t], (f(c, "add") + 0.001) * rank)
                n[t] += 1
    return {t: (lo[t], hi[t]) for t in lo}


def strengths_by_pull(ents, power=eff, rounds=6, default=0.05):
    """Rank = order by steering pull (power * a) among the add-carrying entries of a link; a from interval intersection."""
    a: dict[str, float] = {}
    for es in ents.values():          # start: the largest add of the country = its value at rank 1
        for t, c in es.items():
            if "add" in c and "type" in c:
                a[t] = max(a.get(t, 0.0), f(c, "add") + 0.0005)
    for _ in range(rounds):
        iv = strength_intervals_keyed(ents, lambda t, c: power(c) * a.get(t, default))
        a = {t: (lo + hi) / 2 if lo <= hi else (lo + hi) / 2 for t, (lo, hi) in iv.items()}
    return a, iv


def strength_intervals_keyed(ents, key):
    lo = defaultdict(float); hi = defaultdict(lambda: 9.0)
    for nid, es in ents.items():
        groups = defaultdict(list)
        for t, c in es.items():
            if "add" in c and "type" in c:
                groups[int(f(c, "steer_power"))].append((t, c))
        for items in groups.values():
            items.sort(key=lambda tc: -key(*tc))
            for rank, (t, c) in enumerate(items, 1):
                lo[t] = max(lo[t], f(c, "add") * rank)
                hi[t] = min(hi[t], (f(c, "add") + 0.001) * rank)
    return {t: (lo[t], hi[t]) for t in lo}


REGION: dict = {}


def _vote(intervals, key=None):
    """Midpoint of the region covered by the most intervals, and that count (region kept in REGION[key])."""
    ev = sorted([(lo, 1) for lo, hi in intervals] + [(hi, -1) for lo, hi in intervals])
    best = (0, None, None); cur = 0
    for i, (x, d) in enumerate(ev):
        cur += d
        if d == 1 and cur > best[0]:
            nxt = ev[i + 1][0] if i + 1 < len(ev) else x
            best = (cur, x, nxt)
    if key is not None:
        REGION[key] = (best[1], best[2])
    return (best[1] + best[2]) / 2, best[0]


def strengths_vote(ents, power=eff, rounds=10, need_type=True):
    a: dict[str, float] = defaultdict(lambda: 0.05)   # first pass: equal strengths = rank by power alone
    support = {}
    for _ in range(rounds):
        ivs = defaultdict(list)
        for es in ents.values():
            groups = defaultdict(list)
            for t, c in es.items():
                if "add" in c and ("type" in c or not need_type):
                    groups[int(f(c, "steer_power"))].append((t, c))
            for items in groups.values():
                items.sort(key=lambda tc: -power(tc[1]) * a[tc[0]])
                for rank, (t, c) in enumerate(items, 1):
                    ivs[t].append((f(c, "add") * rank, (f(c, "add") + 0.001) * rank))
        new = {}
        for t, iv in ivs.items():
            v, n = _vote(iv, t)
            new[t] = v; support[t] = (n, len(iv))
        if new == a:
            break
        a = new
    return a, support


def test_weights(rounds=2, power=eff, strict=True, tol=0.0015):
    """Weights = share of sum over steerers (key `type`) of power * a_c, on nodes whose steering countries all have a
    consistent a_c (strict) or at least one estimate."""
    res = Counter(); bad = []
    for sid in TICK_DAY:
        nodes, ents, active, collect = load(sid)
        a, sup = strengths_vote(ents, rounds=rounds)
        for nid, n in nodes.items():
            targets = G.outgoing(nid)
            w = [float(x) for x in common.as_list(n.get("steer_power"))]
            if len(targets) < 2 or len(w) != len(targets) or float(n.get("outgoing", 0) or 0) <= 0:
                continue
            st = [(t, c) for t, c in ents[nid].items() if "type" in c]
            known = all(t in sup and (sup[t][0] == sup[t][1] or not strict) for t, _ in st)
            if not st or not known:
                res["unknown a"] += 1
                continue
            pull = [0.0] * len(targets)
            for t, c in st:
                pull[int(f(c, "steer_power"))] += power(c) * a[t]
            s = sum(pull)
            err = max(abs(p / s - x) for p, x in zip(pull, w))
            res["fit" if err <= tol else "miss"] += 1
            if err > tol:
                bad.append((round(err, 4), sid, nid))
    return res, sorted(bad, reverse=True)


def test_weights_interval(rounds=2, power=eff, slack=0.001):
    """Stored weight must lie in the range the a_c intervals allow (link pulls at their extremes), +- slack for the
    3-decimal truncation of the stored weight."""
    res = Counter(); bad = []
    for sid in TICK_DAY:
        nodes, ents, active, collect = load(sid)
        REGION.clear()
        a, sup = strengths_vote(ents, rounds=rounds)
        for nid, n in nodes.items():
            targets = G.outgoing(nid)
            w = [float(x) for x in common.as_list(n.get("steer_power"))]
            if len(targets) < 2 or len(w) != len(targets) or float(n.get("outgoing", 0) or 0) <= 0:
                continue
            st = [(t, c) for t, c in ents[nid].items() if "type" in c]
            if not st or not all(t in sup and sup[t][0] == sup[t][1] for t, _ in st):
                res["unknown a"] += 1
                continue
            lo = [0.0] * len(targets); hi = [0.0] * len(targets)
            for t, c in st:
                L = int(f(c, "steer_power")); r0, r1 = REGION[t]
                lo[L] += power(c) * r0; hi[L] += power(c) * r1
            ok = True
            for i, x in enumerate(w):
                wmin = lo[i] / (lo[i] + sum(hi[j] for j in range(len(w)) if j != i)) if lo[i] + sum(hi) > 0 else 0
                wmax = hi[i] / (hi[i] + sum(lo[j] for j in range(len(w)) if j != i)) if hi[i] > 0 else 0
                if not (wmin - slack <= x <= wmax + slack):
                    ok = False
            res["fit" if ok else "miss"] += 1
            if not ok:
                bad.append((sid, nid))
    return res, bad
