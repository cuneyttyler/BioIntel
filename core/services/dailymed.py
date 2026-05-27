import requests
from .cache import make_cache_key, get_cached, set_cached

BASE = 'https://dailymed.nlm.nih.gov/dailymed/services'
SOURCE = 'dailymed'


def _get(path: str, params: dict = None) -> dict:
    key = make_cache_key(path, params or {})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.get(f'{BASE}/{path}', params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        set_cached(SOURCE, key, data)
        return data
    except Exception:
        return {}


def search_spls(drug_name: str) -> list:
    data = _get('spls.json', {'drug_name': drug_name})
    return data.get('data', [])


def get_spl(set_id: str) -> dict:
    return _get(f'spls/{set_id}.json')
