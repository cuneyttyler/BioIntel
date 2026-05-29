import requests
from .cache import make_cache_key, get_cached, set_cached

BASE = 'https://ops.epo.org/3.2/rest-services'
SOURCE = 'espacenet'


def _get(path: str, params: dict = None, headers: dict = None) -> dict:
    key = make_cache_key(path, params or {})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        h = {'Accept': 'application/json'}
        if headers:
            h.update(headers)
        r = requests.get(f'{BASE}/{path}', params=params, headers=h, timeout=15)
        r.raise_for_status()
        data = r.json()
        set_cached(SOURCE, key, data)
        return data
    except Exception:
        return {}


def get_patent(patent_number: str) -> dict:
    """Retrieve bibliographic data for a patent by publication number."""
    # EPO OPS biblio endpoint — works without OAuth for published data
    clean = patent_number.replace('/', '-')
    data = _get(f'published-data/publication/epodoc/{clean}/biblio')
    return data


def search_patents(query: str) -> list:
    """Keyword search across patent titles and abstracts."""
    data = _get('published-data/search', params={'q': query, 'Range': '1-10'})
    try:
        results = (
            data.get('ops:world-patent-data', {})
                .get('ops:biblio-search', {})
                .get('ops:search-result', {})
                .get('exchange-documents', [])
        )
        if isinstance(results, dict):
            results = [results]
        return results
    except Exception:
        return []
