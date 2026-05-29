import requests
from .cache import make_cache_key, get_cached, set_cached

BASE = 'https://www.ebi.ac.uk/chembl/api/data'
SOURCE = 'chembl'


def _get(endpoint: str, params: dict = None) -> dict:
    key = make_cache_key(endpoint, params or {})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.get(f'{BASE}/{endpoint}', params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        set_cached(SOURCE, key, data)
        return data
    except Exception:
        return {}


def get_molecule(chembl_id: str) -> dict:
    return _get(f'molecule/{chembl_id}.json')


def search_molecule(name: str) -> list:
    data = _get('molecule/search.json', {'q': name, 'limit': 10})
    return data.get('molecules', [])


def get_mechanisms(chembl_id: str) -> list:
    data = _get('mechanism.json', {'molecule_chembl_id': chembl_id})
    return data.get('mechanisms', [])


def get_bioactivities(chembl_id: str, limit: int = 20) -> list:
    data = _get('activity.json', {'molecule_chembl_id': chembl_id, 'limit': limit})
    return data.get('activities', [])
