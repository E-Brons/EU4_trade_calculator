"""Venice series: country-level VEN fields that move with the merchant recall / re-send (transfer_home_bonus, merchants envoy actions)."""
import sys
sys.path.insert(0, "scripts/research")
import venice_load as V
from final_r12_common import lst
for p in V.files():
    c = V.load(p, 'countries')['VEN']
    acts = [e.get('action') for e in lst((c.get('merchants') or {}).get('envoy'))]
    print(p.stem[6:], 'transfer_home_bonus', c.get('transfer_home_bonus'), 'envoy actions', acts)
