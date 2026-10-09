"""R09 Q4: country-level trade fields vs node entries, whole corpus."""
import sys,re,collections
sys.path.insert(0,'scripts/research')
import common
TAG=re.compile(r'^[A-Z0-9]{2,4}$')
def al(x): return x if isinstance(x,list) else [x]
st=collections.Counter(); ex=collections.defaultdict(list)
def chk(k,ok,c=None):
    st[k+' checks']+=1
    if not ok:
        st[k+' FAIL']+=1
        if len(ex[k])<4: ex[k].append(c)
envkeys=collections.Counter(); actions=collections.Counter()
for e in common.entries():
    C=common.block(e,'countries'); ns=common.nodes(e); prov=common.block(e,'provinces')
    ships=collections.Counter(); traders=collections.Counter(); tfrom=collections.defaultdict(set); tto=collections.defaultdict(set); capnode={}; steer=collections.Counter(); coll=collections.Counter(); money=collections.Counter()
    for n in ns:
        for t,v in n.items():
            if not(TAG.match(t) and isinstance(v,dict)): continue
            ships[t]+=v.get('light_ship',0); traders[t]+=bool(v.get('has_trader')); steer[t]+= 'type' in v; coll[t]+= ('total' in v and v.get('has_trader',False))
            money[t]+=v.get('money',0.0)
            if 't_from' in v: tfrom[t]|=set(v['t_from'])
            if 't_to' in v: tto[t]|=set(v['t_to'])
            if v.get('has_capital'): capnode[t]=n['definitions']
    for t,c in C.items():
        if not isinstance(c,dict): continue
        if 'num_ships_protecting_trade' in c or ships[t]:
            chk('num_ships_protecting_trade == sum(light_ship over nodes)', c.get('num_ships_protecting_trade',0)==ships[t], (e['id'],t,c.get('num_ships_protecting_trade'),ships[t]))
        env=c.get('merchants',{}).get('envoy') if isinstance(c.get('merchants'),dict) else None
        if env is not None or traders[t]:
            env=al(env) if env is not None else []
            for m in env:
                envkeys.update(m.keys()); actions[(m.get('type'),m.get('action'))]+=1
            chk('#merchants.envoy entries == #nodes with has_trader', len(env)==traders[t], (e['id'],t,len(env),traders[t]))
            n_trade=sum(1 for m in env if m.get('type')==1)
        if 'transfer_trade_power_from' in c or tfrom[t]:
            chk('transfer_trade_power_from == tags in t_from', set(al(c.get('transfer_trade_power_from',[])))==tfrom[t], (e['id'],t,c.get('transfer_trade_power_from'),sorted(tfrom[t])))
        if 'transfer_trade_power_to' in c or tto[t]:
            chk('transfer_trade_power_to == tags in t_to', set(al(c.get('transfer_trade_power_to',[])))==tto[t], (e['id'],t,c.get('transfer_trade_power_to'),sorted(tto[t])))
        if 'trade_embargoed_by' in c:
            for b in al(c['trade_embargoed_by']):
                chk('B in A.trade_embargoed_by => A in B.trade_embargoes', t in al(C.get(b,{}).get('trade_embargoes',[])), (e['id'],t,b))
        if 'trade_embargoes' in c:
            for b in al(c['trade_embargoes']):
                chk('B in A.trade_embargoes => A in B.trade_embargoed_by', t in al(C.get(b,{}).get('trade_embargoed_by',[])), (e['id'],t,b))
            if 'num_of_trade_embargos' in c: chk('num_of_trade_embargos == len(trade_embargoes)', c['num_of_trade_embargos']==len(al(c['trade_embargoes'])), (e['id'],t,c['num_of_trade_embargos'],c['trade_embargoes']))
        if 'trade_port' in c and t in capnode:
            p=prov.get(f"-{c['trade_port']}")
            if p and 'trade' in p: chk('node of province trade_port == node with has_capital', p['trade']==capnode[t], (e['id'],t,c['trade_port'],p['trade'],capnode[t]))
            if 'capital' in c: chk('trade_port == capital', c['trade_port']==c['capital'], (e['id'],t,c['trade_port'],c['capital']))
        if 'traded' in c and money[t]>0:
            chk('sum(traded) == sum(money)', abs(sum(al(c['traded']))-money[t])<0.01*max(1,len([1])), (e['id'],t,round(sum(al(c['traded'])),3),round(money[t],3)))
for k in sorted(st): print(k,st[k])
for k,v in ex.items(): print(k,v)
print('envoy keys',dict(envkeys)); print('(type,action) counts',dict(actions))
