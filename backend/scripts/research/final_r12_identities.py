"""R12 final, script 1: identities between stored node values, exact in integer thousandths (m3), whole corpus.
  I1 retention            == ceil3( retain_power / (retain_power + pull_power) )      (1.000 when both are 0)
  I2 current              == ceil3( gross * retention ), gross = local_value + sum(incoming.value);
                              == gross when the node has outgoing links and sum(steer_power) == 0
  I3 outgoing             == gross - current          (absent key = 0)
  I4 value_added_outgoing == outgoing                 (same presence)
  I5 power_fraction       == trunc3( eff / retain_power ) for entries with `power_fraction`;  eff = val - t_out + t_in
  I6 entry `total`        == trunc3( current * power_fraction )   (collectors' share of the node's current)
  I7 val                  == trunc3( max_pow * max_demand )
Independent of app.trade.calc. Run from backend/:  .venv/bin/python scripts/research/final_r12_identities.py"""
import sys
sys.path.insert(0, "scripts/research")
from collections import Counter, defaultdict
from final_r12_common import *

def cdiv(a, b): return -((-a) // b)
def tdiv(a, b):                      # truncation toward zero of a/b (b > 0)
    return a // b if a >= 0 else -((-a) // b)

def group(sid, date, kind):
    if date == "1444.11.11": return "bookmark 1444.11.11 (35)"
    if kind == "start": return "start later dates (43)"
    if kind == "ticked": return "played S79,S80 (2)"
    return "user U03-U06 (4)"

N = defaultdict(Counter); OK = defaultdict(Counter); EX = defaultdict(list)
def chk(name, g, ok, info):
    N[name][g] += 1
    if ok: OK[name][g] += 1
    else: EX[name].append(info)

for sid, date, kind, nodes in saves(distinct=True):
    g = group(sid, date, kind)
    inc = incoming_links(nodes)
    insum = defaultdict(int)
    for (s, d), L in inc.items(): insum[d] += sum(v for v, a in L)
    for n in nodes:
        nid = n["definitions"]
        rp = m3(n.get("retain_power", 0)); pl = m3(n.get("pull_power", 0)); ret = m3(n["retention"])
        tot = rp + pl
        exp_ret = 1000 if tot == 0 else cdiv(rp * 1000, tot)
        chk("I1 retention = ceil3(retain/(retain+pull))", g, ret == exp_ret, (sid, nid, ret, exp_ret))
        gross = m3(n.get("local_value", 0)) + insum[nid]
        cur = m3(n.get("current", 0)); out = m3(n.get("outgoing", 0))
        sw = sum(m3(x) for x in lst(n.get("steer_power")))
        if OUT[nid] and sw == 0:
            chk("I2b current = gross when links exist and sum(steer_power) = 0", g, cur == gross, (sid, nid, cur, gross, ret))
            N["I2b-detail: of these, retention < 1"][g] += 1 if ret < 1000 else 0
        else:
            chk("I2a current = ceil3(gross*retention) (all other nodes)", g, cur == cdiv(gross * ret, 1000), (sid, nid, cur, cdiv(gross * ret, 1000)))
            # alternatives, counted on the same nodes
            N["I2a alt: trunc3"][g] += 1; OK["I2a alt: trunc3"][g] += cur == (gross * ret) // 1000
            N["I2a alt: round3"][g] += 1; OK["I2a alt: round3"][g] += cur == (gross * ret + 500) // 1000
        chk("I3 outgoing = gross - current (all nodes, absent = 0)", g, out == gross - cur, (sid, nid, out, gross - cur))
        chk("I4a value_added_outgoing present iff outgoing present", g, ("value_added_outgoing" in n) == ("outgoing" in n), (sid, nid))
        if "outgoing" in n:
            chk("I4b value_added_outgoing = outgoing (where present)", g, m3(n.get("value_added_outgoing")) == out, (sid, nid, n.get("value_added_outgoing"), n["outgoing"]))
        for tag, e in entries_of(n).items():
            if "max_pow" in e and "max_demand" in e and "val" in e:
                chk("I7 val = trunc3(max_pow*max_demand)", g, m3(e["val"]) == tdiv(m3(e["max_pow"]) * m3(e["max_demand"]), 1000), (sid, nid, tag, e["val"], e["max_pow"], e["max_demand"]))
            if "power_fraction" in e and "val" in e:
                eff = m3(e["val"]) - m3(e.get("t_out", 0)) + m3(e.get("t_in", 0))
                chk("I5 power_fraction = trunc3(eff/retain_power)", g, rp > 0 and m3(e["power_fraction"]) == tdiv(eff * 1000, rp), (sid, nid, tag, e["power_fraction"], eff, rp))
                if "total" in e and "current" in n:
                    chk("I6 entry total = trunc3(current*power_fraction)", g, m3(e["total"]) == tdiv(cur * m3(e["power_fraction"]), 1000), (sid, nid, tag, e["total"], cur, e["power_fraction"]))

groups = ["bookmark 1444.11.11 (35)", "start later dates (43)", "played S79,S80 (2)", "user U03-U06 (4)"]
for name in sorted(N):
    if name.startswith("I2b-detail"):
        print(f"{name}: {sum(N[name].values())}"); continue
    tn = sum(N[name].values()); to = sum(OK[name].values())
    print(f"{name}: {to} of {tn}")
    print("    " + " | ".join(f"{g.split(' (')[0]} {OK[name][g]}/{N[name][g]}" for g in groups))
for name, L in EX.items():
    print("EXCEPTIONS", name, len(L)); print("   ", L[:60])
