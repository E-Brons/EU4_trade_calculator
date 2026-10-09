"""Independent re-computation of the headline R04 claims (integer thousandths, own loop over common.nodes)."""
import sys, collections
from decimal import Decimal as D, ROUND_DOWN
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
from common import as_list

def q(x):            # value as integer thousandths (saves store at most 3 decimals)
    return int(round(float(x) * 1000))
def trunc3(d):       # Decimal -> Decimal truncated toward zero, 3 decimals
    return d.quantize(D('0.001'), rounding=ROUND_DOWN)
def thou(x):         # exact Decimal from the stored float
    return D(repr(float(x)))

ents = common.entries()
cnt = collections.Counter(); offs = collections.Counter(); valchk = collections.Counter()
pot = collections.Counter(); flag = collections.Counter(); recv_ok = collections.Counter()
minval = None; tags = set(); overl = collections.Counter()
powfrac = collections.Counter()
for e in ents:
    sid = e['id']
    ns = common.nodes(e)
    cb = common.block(e, 'countries')
    for n in ns:
        total = n.get('total')
        for tag, c in n.items():
            if not (isinstance(c, dict) and len(tag) <= 4 and tag.isupper() or (isinstance(c, dict) and tag[:1].isalnum() and tag.upper() == tag and len(tag) <= 4)):
                continue
            if 't_out' in c:
                cnt['givers'] += 1; tags.add(tag)
                v, t = q(c['val']), q(c['t_out'])
                offs[v - 2 * t] += 1
                # trunc3(0.5*(val-0.1)) in integer thousandths: floor((v-100)/2)
                cnt['t_out = (v-100)//2'] += (t == (v - 100) // 2)
                cnt['t_out = trunc3(0.5*val)-0.05'] += (t == v // 2 - 50)
                cnt['t_out = trunc3(0.5*val)'] += (t == v // 2)
                minval = v if minval is None else min(minval, v)
                # val = trunc3(max_pow * max_demand)
                pm = trunc3(thou(c['max_pow']) * thou(c['max_demand']))
                valchk['val==trunc3(max_pow*md)'] += (q(pm) == v)
                tt = c.get('t_to')
                keys = list(tt) if isinstance(tt, dict) else []
                cnt['t_to one key'] += (len(keys) == 1)
                cnt['t_to amount == t_out'] += (len(keys) == 1 and q(tt[keys[0]]) == t)
                ov = cb.get(tag, {}).get('overlord')
                overl['receiver == overlord'] += (len(keys) == 1 and keys[0] == ov)
                flag[('giver has transfer_trade_power_to', 'transfer_trade_power_to' in cb.get(tag, {}))] += 1
            if 't_in' in c:
                cnt['receivers'] += 1
                if 't_out' in c: cnt['both t_in & t_out'] += 1
            if 'potential' in c and total is not None and ('t_out' in c or 't_in' in c):
                num = thou(c.get('t_out', 0)) - thou(c.get('t_in', 0))
                p = trunc3(num / thou(total))
                pot['trunc toward 0 ok'] += (q(p) == q(c['potential']))
                pot['n'] += 1
            elif 'potential' in c and total is not None:
                pot['potential without transfer in node with total'] += 1
# flag vs t_out at the country-save level
for e in ents:
    cb = common.block(e, 'countries'); ns = common.nodes(e)
    giv = set(); 
    for n in ns:
        for tag, c in n.items():
            if isinstance(c, dict) and 't_out' in c: giv.add(tag)
    present = set(tag for n in ns for tag, c in n.items() if isinstance(c, dict) and set(c) - {'max_demand'})
    for tag in present:
        f = 'transfer_trade_power_to' in cb.get(tag, {})
        flag[('country-save flag,t_out', f, tag in giv)] += 1
print('givers', cnt['givers'], 'distinct tags', len(tags), 'receivers', cnt['receivers'], 'both', cnt['both t_in & t_out'])
print('val-2*t_out (thousandths):', dict(offs))
for k in ('t_out = (v-100)//2', 't_out = trunc3(0.5*val)-0.05', 't_out = trunc3(0.5*val)'): print(k, cnt[k])
print('min giver val', minval / 1000, valchk, 't_to one key', cnt['t_to one key'], 'amount==t_out', cnt['t_to amount == t_out'], overl)
print('potential', dict(pot))
print('flag vs t_out', {k: v for k, v in flag.items()})
