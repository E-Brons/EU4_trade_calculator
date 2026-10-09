"""R11 Q2/Q4/Q7: types on protect missions, morale/strength vs counted, max ships per node, nps vs counted, inland/open sea."""
import sys,pickle,json; sys.path.insert(0,'scripts/research')
exec(open('scripts/research/r11_r14_fleetflags.py').read().split("unique=0")[0])
tn=json.load(open('data/tradenodes.json'))['nodes']
types=Counter(); nonlight_in_protect=Counter(); morale=[]; strength=Counter()
nps_rows=[]; maxship=[]
for e in common.entries():
    if e['id'] not in ('S79','S80'): continue
    nodes=common.nodes(e); order=[n['definitions'] for n in nodes]
    cs=common.block(e,'countries')
    cnt=defaultdict(lambda:[0,0,0])  # tag -> [counted-in-entries, protect light ships with on_my_way, all protect light ships]
    for n in nodes:
        for tag,c in n.items():
            if isinstance(c,dict) and c.get('light_ship'):
                cnt[tag][0]+=int(c['light_ship']); maxship.append((int(c['light_ship']),e['id'],n['definitions'],tag,tn[n['definitions']]['inland']))
    for tag in list(cnt):
        c=cs[tag]; nv=c.get('navy',[]); nv=nv if isinstance(nv,list) else [nv]
        for f in nv:
            m=f.get('mission')
            if not(isinstance(m,dict) and isinstance(m.get('protect_mission'),dict)): continue
            pm=m['protect_mission']
            for s in (f['ship'] if isinstance(f['ship'],list) else [f['ship']]):
                types[s['type']]+=1
                if s['type'] not in BASE: nonlight_in_protect[s['type']]+=1
                else:
                    cnt[tag][2]+=1
                    if 'on_my_way' in pm: cnt[tag][1]+=1
                    morale.append(s['morale']); strength[('strength' in s)]+=1
        nps_rows.append((e['id'],tag,c.get('num_ships_protecting_trade'),*cnt[tag]))
print('ship types in protect_mission fleets:',dict(types))
print('non-light types on protect missions:',dict(nonlight_in_protect))
print('light ships with a `strength` key:',dict(strength))
print('morale range of light ships on protect missions',min(morale),max(morale))
a=sum(1 for r in nps_rows if r[2]==r[4]); b=sum(1 for r in nps_rows if r[2]==r[3])
print('country-saves',len(nps_rows),'nps == all light ships on protect missions with on_my_way key:',a,' nps == sum of node light_ship:',b)
print('nps != node sum:',[r for r in nps_rows if r[2]!=r[3]])
print('nps != on_my_way-present sum:',[r for r in nps_rows if r[2]!=r[4]])
maxship.sort(reverse=True); print('largest light_ship per entry:',maxship[:6]); print('inland entries with ships:',[m for m in maxship if m[4]])
print('---')
print('nps == all light ships on protect missions:',sum(1 for r in nps_rows if r[2]==r[5]),'of',len(nps_rows),' mismatches',[r for r in nps_rows if r[2]!=r[5]])
print('nps counts non-light types too? mismatches when counting only light:', [r for r in nps_rows if r[2]!=r[5]])
