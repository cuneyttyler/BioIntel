import requests
from .cache import make_cache_key, get_cached, set_cached

BASE = 'https://askcos.mit.edu/api/v2'
SOURCE = 'askcos'


def _post(endpoint: str, payload: dict) -> dict:
    key = make_cache_key(endpoint, payload)
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.post(f'{BASE}/{endpoint}', json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        set_cached(SOURCE, key, data)
        return data
    except Exception as e:
        return {'error': str(e)}


def single_step_retro(smiles: str, num_templates: int = 10) -> dict:
    return _post('retro/', {'smiles': smiles, 'num_templates': num_templates, 'max_cum_prob': 0.999})


def multi_step_tree(smiles: str, max_depth: int = 5) -> dict:
    return _post('tree-builder/', {
        'smiles': smiles,
        'max_depth': max_depth,
        'max_branching': 5,
        'expansion_time': 60,
        'buyables_source': ['reaxys', 'sigma'],
    })


def forward_predict(reactants: str, reagents: str = '', solvent: str = '') -> dict:
    return _post('forward/', {'reactants': reactants, 'reagents': reagents, 'solvent': solvent})


def recommend_conditions(reactants: str, products: str, n: int = 5) -> dict:
    return _post('context/', {'reactants': reactants, 'products': products, 'n_conditions': n})


def check_buyable(smiles: str) -> dict:
    key = make_cache_key('buyables', {'smiles': smiles})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.get(f'{BASE}/buyables/', params={'q': smiles, 'limit': 5}, timeout=15)
        r.raise_for_status()
        data = r.json()
        set_cached(SOURCE, key, data)
        return data
    except Exception as e:
        return {'error': str(e)}
