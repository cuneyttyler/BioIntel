import requests
from .cache import make_cache_key, get_cached, set_cached

BASE = 'https://api.fda.gov'
SOURCE = 'openfda'
SOURCE_GUIDANCE = 'openfda_guidance'


def _get(path: str, params: dict, source: str = SOURCE) -> dict:
    key = make_cache_key(path, params)
    cached = get_cached(source, key)
    if cached is not None:
        return cached
    try:
        r = requests.get(f'{BASE}/{path}', params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        set_cached(source, key, data)
        return data
    except Exception:
        return {}


def search_labels(brand_name: str = None, generic_name: str = None, limit: int = 5) -> list:
    if brand_name:
        search = f'openfda.brand_name:"{brand_name}"'
    elif generic_name:
        search = f'openfda.generic_name:"{generic_name}"'
    else:
        return []
    data = _get('drug/label.json', {'search': search, 'limit': limit})
    return data.get('results', [])


def get_ndc(drug_name: str, limit: int = 10) -> list:
    data = _get('drug/ndc.json', {'search': f'generic_name:"{drug_name}"', 'limit': limit})
    return data.get('results', [])


def get_excipients(dosage_form: str, limit: int = 20) -> list:
    data = _get('drug/label.json', {'search': f'dosage_form:"{dosage_form}"', 'limit': limit})
    excipients = set()
    for result in data.get('results', []):
        for item in result.get('inactive_ingredient', []):
            for ingredient in item.split(','):
                stripped = ingredient.strip()
                if stripped:
                    excipients.add(stripped)
    return sorted(excipients)


def search_guidance(topic: str, limit: int = 10) -> list:
    data = _get('other/guidance.json', {'search': topic, 'limit': limit}, source=SOURCE_GUIDANCE)
    return data.get('results', [])
