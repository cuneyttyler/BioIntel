import requests
from .cache import get_cached, set_cached

CCDC_BASE = "https://www.ccdc.cam.ac.uk/api/structures"


def search_structures(smiles: str) -> list[dict]:
    cache_key = f"search:{smiles}"
    cached = get_cached("ccdc", cache_key)
    if cached:
        return cached

    try:
        resp = requests.get(
            f"{CCDC_BASE}/search",
            params={"smiles": smiles, "max_hits": 20},
            timeout=15,
        )
        if resp.ok:
            data = resp.json()
            results = data.get("hits", data if isinstance(data, list) else [])
            set_cached("ccdc", cache_key, results)
            return results
    except Exception:
        pass
    return []


def get_crystal_data(identifier: str) -> dict:
    cache_key = f"entry:{identifier}"
    cached = get_cached("ccdc", cache_key)
    if cached:
        return cached

    try:
        resp = requests.get(f"{CCDC_BASE}/{identifier}", timeout=15)
        if resp.ok:
            data = resp.json()
            set_cached("ccdc", cache_key, data)
            return data
    except Exception:
        pass
    return {}
