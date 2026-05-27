import requests
from .cache import make_cache_key, get_cached, set_cached

BASE = 'https://biosig.lab.uq.edu.au/pkcsm/api'
SOURCE = 'pkcsm'


def predict_admet(smiles: str) -> dict:
    key = make_cache_key('predict', {'smiles': smiles})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.post(f'{BASE}/predict', json={'smiles': smiles}, timeout=30)
        r.raise_for_status()
        data = r.json()
        set_cached(SOURCE, key, data)
        return data
    except Exception:
        return {}
