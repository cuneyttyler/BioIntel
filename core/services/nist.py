import requests
from .cache import make_cache_key, get_cached, set_cached

BASE = 'https://webbook.nist.gov/cgi-bin/cbook.cgi'
SOURCE = 'nist'

SPEC_TYPE_MAP = {
    'IR': {'cIR': 'on', 'Type': 'IR'},
    'MS': {'cMS': 'on', 'Type': 'MassSpec'},
}


def get_spectrum(cas: str, spec_type: str = 'IR') -> str:
    key = make_cache_key('spectrum', {'cas': cas, 'type': spec_type})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached.get('jcamp', '')
    try:
        type_params = SPEC_TYPE_MAP.get(spec_type.upper(), SPEC_TYPE_MAP['IR'])
        params = {'ID': cas, 'Units': 'SI', 'Index': 0, 'JCAMP': 'on', **type_params}
        r = requests.get(BASE, params=params, timeout=20)
        r.raise_for_status()
        data = {'jcamp': r.text}
        set_cached(SOURCE, key, data)
        return r.text
    except Exception:
        return ''


def get_compound_data(cas: str) -> dict:
    key = make_cache_key('compound', {'cas': cas})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.get(BASE, params={'ID': cas, 'Units': 'SI'}, timeout=15)
        r.raise_for_status()
        data = {'html': r.text[:5000]}
        set_cached(SOURCE, key, data)
        return data
    except Exception:
        return {}
