"""R09 Q2: top_power_values = effective power (val - t_out + t_in); membership of top_power / top_provinces."""
import sys,re,collections
sys.path.insert(0,'scripts/research')
import common
TAG=re.compile(r'^[A-Z0-9]{2,4}$')
st=collections.Counter(); ex=collections.defaultdict(list)
def al(x): return x if isinstance(x,list) else [x]
for e in common.entries():
    for n in common.nodes(e):
        if 'top_power' not in n: continue
        es={t:v for t,v in n.items() if TAG.match(t) and isinstance(v,dict)}
        tp,tv=al(n['top_power']),al(n['top_power_values'])
        eff={t:v.get('val',0)-v.get('t_out',0)+v.get('t_in',0) for t,v in es.items() if ('val' in v or 't_in' in v)}
        st['nodes']+=1
        if all(abs(tv[i]-eff.get(t,-9))<0.0015 for i,t in enumerate(tp)): st['top_power_values==val-t_out+t_in']+=1
        elif len(ex['v'])<4: ex['v'].append((e['id'],n['definitions'],[(t,tv[i],eff.get(t)) for i,t in enumerate(tp) if abs(tv[i]-eff.get(t,-9))>=0.0015][:2]))
        # membership: all tags with eff>0 listed?
        pos={t for t,x in eff.items() if x>0.0005}
        if set(tp)==pos: st['top_power set == {eff>0}']+=1
        elif len(ex['m'])<4: ex['m'].append((e['id'],n['definitions'],sorted(pos-set(tp))[:3],sorted(set(tp)-pos)[:3],len(tp)))
        # sorted desc
        st['nodes without top_provinces'] += 'top_provinces' not in n
        tpr,tpv=al(n.get('top_provinces',[])),al(n.get('top_provinces_values',[0]))
        pp={t for t,v in es.items() if v.get('province_power',0)>0.0005}
        if set(tpr)==pp: st['top_provinces set == {province_power>0}']+=1
        elif len(ex['p'])<4: ex['p'].append((e['id'],n['definitions'],sorted(pp-set(tpr))[:3],sorted(set(tpr)-pp)[:3],len(tpr)))
        st['top_power len max']=max(st['top_power len max'],len(tp)); st['top_prov len max']=max(st['top_prov len max'],len(tpr))
        # highest_power relation
        st['highest_power<=top_provinces_values[0]']+= n.get('highest_power',0)<=tpv[0]+0.0015
        st['highest_power<=top_provinces_values[0] total']+=1
print(dict(st)); print(dict(ex))
