import requests
from .cache import make_cache_key, get_cached, set_cached

BASE = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug'
SOURCE = 'pubchem'
PROPS = 'MolecularFormula,MolecularWeight,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,IsomericSMILES,InChIKey'


def search_compound(name: str) -> list:
    key = make_cache_key('search', {'name': name})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached

    try:
        r = requests.get(f'{BASE}/compound/name/{requests.utils.quote(name)}/cids/JSON', timeout=10)
        r.raise_for_status()
        cids = r.json().get('IdentifierList', {}).get('CID', [])[:5]
        if not cids:
            set_cached(SOURCE, key, [])
            return []
        props = get_properties_batch(cids)
        set_cached(SOURCE, key, props)
        return props
    except Exception:
        return []


def get_properties_batch(cids: list) -> list:
    cid_str = ','.join(str(c) for c in cids)
    try:
        r = requests.get(f'{BASE}/compound/cid/{cid_str}/property/{PROPS}/JSON', timeout=10)
        r.raise_for_status()
        return r.json().get('PropertyTable', {}).get('Properties', [])
    except Exception:
        return []


def get_compound_properties(cid: int) -> dict:
    key = make_cache_key('properties', {'cid': cid})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached

    try:
        r = requests.get(f'{BASE}/compound/cid/{cid}/property/{PROPS}/JSON', timeout=10)
        r.raise_for_status()
        props_list = r.json().get('PropertyTable', {}).get('Properties', [])
        data = props_list[0] if props_list else {}
        set_cached(SOURCE, key, data)
        return data
    except Exception:
        return {}


def structure_png_url(cid: int) -> str:
    return f'{BASE}/compound/cid/{cid}/PNG'


def get_similar_compounds(smiles: str, threshold: int = 90) -> list:
    key = make_cache_key('similar', {'smiles': smiles, 'threshold': threshold})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached

    try:
        encoded = requests.utils.quote(smiles)
        r = requests.get(
            f'{BASE}/compound/fastsimilarity_2d/smiles/{encoded}/cids/JSON',
            params={'Threshold': threshold},
            timeout=15,
        )
        r.raise_for_status()
        cids = r.json().get('IdentifierList', {}).get('CID', [])[:20]
        set_cached(SOURCE, key, cids)
        return cids
    except Exception:
        return []
