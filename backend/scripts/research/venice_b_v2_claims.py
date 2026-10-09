"""SECOND PASS for the merchant claims, with raw-text extraction only."""
import re, sys
sys.path.insert(0, 'scripts/research')
import venice_b_v2_raw as R

print('C1/C2  transfer_home_bonus, steering envoys (action=2), max_demand at venice minus max_demand at alexandria:')
for p in R.files():
    cb = R.country_block(p, 'VEN')
    thb = re.search(r'transfer_home_bonus=([\d.]+)', cb)
    mer = re.search(r'merchants=\{(.*?)\n\t\t\}', cb, re.S)
    nact = len(re.findall(r'action=2', mer.group(1))) if mer else None
    nodes = R.nodes(p)
    md_v = float(nodes['venice'][0]['VEN']['max_demand']); md_a = float(nodes['alexandria'][0]['VEN']['max_demand'])
    print(f'  {p.stem[6:]}: thb={thb.group(1) if thb else None} envoys with action=2: {nact}  md(venice)={md_v} md(alexandria)={md_a} diff={md_v - md_a:.3f}')

print('C3  X = money/total of VEN at venice, 24 saves:')
print('  ', [round(float(R.nodes(p)['venice'][0]['VEN']['money']) / float(R.nodes(p)['venice'][0]['VEN']['total']), 3) for p in R.files()])
