"""Replay engine for 'what if a country's power at one node changes' on a recorded save.

Everything not affected stays as recorded: other countries' effective power, retention of downstream nodes, local values,
link ratios (incoming.value / upstream outgoing), collectors' power_fraction and the money/share ratio of each collector.
Stage formulas are those of app/trade/calc.py (retention = retain/(retain+pull); current = gross*retention; outgoing = gross-current;
share = fx(current*power_fraction); money = share*(money/share recorded)). Steering weights are NOT recomputed (R08 rule still unknown).
"""
import sys
sys.path.insert(0, 'scripts/research')
import common
from app.trade import calc, game_data

A = common.as_list


def f(c, k, d=0.0):
    try:
        return float(c.get(k, d))
    except (TypeError, ValueError):
        return d


class Save:
    def __init__(self, e):
        self.e = e
        self.nodes = common.nodes(e)
        self.order = [n['definitions'] for n in self.nodes]
        self.N = {n['definitions']: n for n in self.nodes}
        self.links = {}          # (src, dst) -> (value, add)
        self.children = {n: [] for n in self.order}
        for n in self.nodes:
            for i in A(n.get('incoming')):
                if isinstance(i, dict) and 0 < int(i['from']) <= len(self.order):
                    s = self.order[int(i['from']) - 1]
                    self.links[(s, n['definitions'])] = (float(i['value']), float(i.get('add', 0.0)))
                    self.children[s].append(n['definitions'])

    def node_vals(self, nid):
        n = self.N[nid]
        inc = sum(v for (s, d), (v, a) in self.links.items() if d == nid)
        return dict(local=f(n, 'local_value'), inc=inc, gross=f(n, 'local_value') + inc, ret=f(n, 'retention'), cur=f(n, 'current'),
                    out=f(n, 'outgoing'), retain=f(n, 'retain_power'), pull=f(n, 'pull_power'))

    def entry(self, nid, tag):
        c = self.N[nid].get(tag)
        return c if isinstance(c, dict) else None

    def eff(self, c):
        return f(c, 'val') - f(c, 't_out') + f(c, 't_in')

    def collect_nodes(self, tag):
        return {nid for nid in self.order if (c := self.entry(nid, tag)) is not None and 'total' in c}

    def membership(self, nid, tag):
        """('collect'|'pull'|None) of tag at nid under the R03 rule, from the recorded entry."""
        c = self.entry(nid, tag)
        if c is None:
            return None
        if 'total' in c:
            return 'collect'
        steering = 'type' in c
        if calc.rule_is_pulling(nid, steering, False, self.collect_nodes(tag)):
            return 'pull'
        return None

    def replay(self, changes):
        """changes: {(node, tag): d_effective_power}. Returns per-node new values and per-(node,tag) new collector share/money."""
        new = {}
        # affected source nodes
        for (nid, tag), d in changes.items():
            v = new.setdefault(nid, dict(self.node_vals(nid)))
            m = self.membership(nid, tag)
            if m == 'collect':
                v['retain'] += d
            elif m == 'pull':
                v['pull'] += d
        for nid, v in list(new.items()):
            v['ret'] = calc.rule_retention(v['retain'], v['pull'])
        # topological propagation (order by depth from the sources)
        done = {}
        frontier = list(new)
        seen = set()
        order = []

        def visit(n):
            if n in seen:
                return
            seen.add(n)
            for c in self.children[n]:
                visit(c)
            order.append(n)
        for n in frontier:
            visit(n)
        order.reverse()
        vals = {}
        for nid in order:
            v = new.get(nid) or dict(self.node_vals(nid))
            # gross from (possibly updated) incoming
            inc = 0.0
            for (s, d), (val, add) in self.links.items():
                if d != nid:
                    continue
                if s in vals and self.node_vals(s)['out'] > 0:
                    rho = val / self.node_vals(s)['out']
                    inc += rho * vals[s]['out']
                else:
                    inc += val
            v['inc'] = inc
            v['gross'] = v['local'] + inc
            v['cur'], v['out'] = calc.rule_current_outgoing(v['gross'], v['ret'])
            vals[nid] = v
        return vals

    def collector_money(self, vals, tag, changes=None):
        """New share/money of `tag` at every collecting node present in `vals` (recorded ratios kept)."""
        out = {}
        for nid, v in vals.items():
            c = self.entry(nid, tag)
            if c is None or 'total' not in c:
                continue
            rec_share, rec_money = f(c, 'total'), f(c, 'money')
            pf = f(c, 'power_fraction')
            if changes and (nid, tag) in changes:
                eff_new = self.eff(c) + changes[(nid, tag)]
                pf = calc.rule_power_fraction(eff_new, v['retain'])
            else:
                # power fraction of an unchanged collector shrinks/grows with retain only at the changed node itself
                if abs(v['retain'] - f(self.N[nid], 'retain_power')) > 1e-9:
                    pf = calc.rule_power_fraction(self.eff(c), v['retain'])
            share = calc.rule_income_share(v['cur'], pf)
            ratio = rec_money / rec_share if rec_share > 0 else 0.0
            out[nid] = dict(share=share, money=share * ratio, rec_share=rec_share, rec_money=rec_money, pf=pf)
        return out


def cont_delta(S, vals, tag, changes=None):
    """Continuous (untruncated) change of `tag`'s money at every collecting node in `vals`: cur*pf*x after minus before."""
    out = {}
    for nid, v in vals.items():
        c = S.entry(nid, tag)
        if c is None or 'total' not in c:
            continue
        share_rec = f(c, 'total')
        x = f(c, 'money') / share_rec if share_rec > 0 else 0.0
        n = S.N[nid]
        cur0 = f(n, 'current')
        retain0 = f(n, 'retain_power')
        if changes and (nid, tag) in changes or abs(v['retain'] - retain0) > 1e-12:
            eff0 = S.eff(c)
            eff1 = eff0 + (changes or {}).get((nid, tag), 0.0)
            pf0 = eff0 / retain0 if retain0 > 0 else 0.0
            pf1 = eff1 / v['retain'] if v['retain'] > 0 else 0.0
        else:
            pf0 = pf1 = f(c, 'power_fraction')
        out[nid] = dict(d_money=(v['cur'] * pf1 - cur0 * pf0) * x, d_cur=v['cur'] - cur0, d_pf=pf1 - pf0, x=x)
    return out
