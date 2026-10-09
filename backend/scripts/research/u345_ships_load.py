"""Loader for the melted user saves U03-U05 (not in the manifest): entries usable with common.block()/common.nodes()."""
import sys
sys.path.insert(0, 'scripts/research')
import common

NEW = [
    {'id': 'U03', 'file': 'U03_TUR.1691.01.09.eu4', 'tag': 'TUR', 'date': '1691.1.9', 'kind': 'user_case'},
    {'id': 'U04', 'file': 'U04_TUR.1691.11.01.eu4', 'tag': 'TUR', 'date': '1691.11.1', 'kind': 'user_case'},
    {'id': 'U05', 'file': 'U05_TUR.1693.04.15.eu4', 'tag': 'TUR', 'date': '1693.4.15', 'kind': 'user_case'},
]
OLD = [e for e in common.entries() if e['id'] in ('S79', 'S80')]

if __name__ == '__main__':
    import time
    for e in NEW:
        t = time.time(); common.nodes(e); cs = common.block(e, 'countries'); print(e['id'], len(cs), round(time.time() - t, 1), flush=True)
