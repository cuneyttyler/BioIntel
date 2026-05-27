import requests
from .cache import make_cache_key, get_cached, set_cached

BASE = 'https://clinicaltrials.gov/api/v2'
SOURCE = 'clinicaltrials'


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


def search_trials(condition: str = None, intervention: str = None,
                  phase: str = None, page_size: int = 20) -> dict:
    params = {'pageSize': page_size}
    if condition:
        params['query.cond'] = condition
    if intervention:
        params['query.intr'] = intervention
    if phase:
        params['filter.advanced'] = f'AREA[Phase]{phase.upper()}'
    return _get('studies', params)


def get_trial(nct_id: str) -> dict:
    return _get(f'studies/{nct_id}')
