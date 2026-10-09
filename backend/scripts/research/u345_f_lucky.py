"""Does a save store a lucky-nations setting? Search gamestate text for luck/lucky and list top-level settings keys."""
import re, sys, zipfile
sys.path.insert(0, 'scripts/research')
from collections import Counter
targets = {'U03': 'tests/fixtures/saves/U03_TUR.1691.01.09.eu4', 'S79': 'tests/fixtures/saves_zip/S79_TUR_1665.4.22.eu4.zip'}
for sid, p in targets.items():
    t = zipfile.ZipFile(p).read('S79_TUR_1665.4.22.eu4') if p.endswith('.zip') else open(p, 'rb').read()
    print(sid, 'bytes', len(t), 'lucky:', len(re.findall(rb'(?i)lucky', t)), 'luck:', len(re.findall(rb'(?i)luck', t)))
    print('  luck contexts:', Counter(m.decode('utf8', 'replace') for m in re.findall(rb'(?i)[A-Za-z_ ="]{0,12}luck[A-Za-z_"]{0,10}', t)).most_common(8))
    head = t[:6000].decode('utf8', 'replace')
    print('  first top-level scalar keys:', re.findall(r'(?m)^([a-z_]+)=', head)[:60])
    for key in (b'lucky_nations', b'difficulty', b'ai_aggression', b'ai_difficulty', b'luck'):
        print('  ', key.decode(), len(re.findall(rb'(?m)^\s*' + key + rb'\s*=', t)))
