"""Leader records (country history) of the admirals that command protect-mission fleets, with the f of their entry."""
import re, sys, zipfile, tempfile
from pathlib import Path
sys.path.insert(0, 'scripts/research')
import common
def leader_record(text, lid):
    for m in re.finditer(r'id=\{\s*id=%d\s*type=49\s*\}' % lid, text):
        s = text.rfind('leader={', 0, m.start())
        if s < 0: continue
        blk = text[s:m.end() + 40]
        if blk.count('{') - blk.count('}') >= 1 and 'type=' in blk:
            fields = dict(re.findall(r'\n\s*(name|type|maneuver|fire|shock|siege|personality|country|activation|birth_date)=("?[^\n]*)', blk[:700]))
            return fields
    return None
def text_of(entry):
    with tempfile.TemporaryDirectory() as tmp:
        from app.trade import corpus, savefile
        return savefile.read_save_text(corpus.locate(entry, Path(tmp))).gamestate
if __name__ == '__main__':
    import u345_ships_load as L
    E = {e['id']: e for e in L.OLD + L.NEW}
    want = {'S79': [(31982, 'DAN lubeck f=1.1'), (29197, 'SPA ivory_coast f=1.05')], 'U03': [(32251, 'HOL english_channel f=1.1'), (32850, 'HOL 2nd leader-fleet'), (34276, 'HOL 3rd leader')]}
    for sid, items in want.items():
        t = text_of(E[sid])
        for lid, label in items: print(sid, lid, label, leader_record(t, lid))
