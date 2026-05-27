import requests
from django.conf import settings
from .cache import make_cache_key, get_cached, set_cached

BASE = 'https://comptox.epa.gov/dashboard-api'
SOURCE = 'comptox'


def _headers():
    return {'x-api-key': settings.EPA_COMPTOX_API_KEY} if settings.EPA_COMPTOX_API_KEY else {}


def _get(path: str, params: dict = None) -> dict:
    key = make_cache_key(path, params or {})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.get(f'{BASE}/{path}', params=params, headers=_headers(), timeout=15)
        r.raise_for_status()
        data = r.json()
        set_cached(SOURCE, key, data)
        return data
    except Exception:
        return {}


def get_chemical_details(name: str) -> dict:
    import urllib.parse
    encoded = urllib.parse.quote(name)
    return _get(f'ccdapp1/search/chemical/equal/{encoded}/', {'projection': 'chemicaldetailall'})


def get_hazard_data(dtxsid: str) -> dict:
    return _get(f'ccdapp1/hazard/search/by-dtxsid/{dtxsid}/', {'projection': 'hazardall'})


def get_bioassay_summary(dtxsid: str) -> dict:
    return _get(f'ccdapp1/bioactivity/search/by-dtxsid/{dtxsid}/')
