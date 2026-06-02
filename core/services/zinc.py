import requests
from .cache import get_cached, set_cached

ZINC_BASE = "https://zinc20.docking.org"


def _fetch_zinc_subset(subset: str, limit: int) -> list[dict]:
    cache_key = f"{subset}:{limit}"
    cached = get_cached("zinc", cache_key)
    if cached:
        return cached

    url = f"{ZINC_BASE}/substances/subsets/{subset}.json"
    params = {"count": min(limit, 10000)}
    results = []

    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.ok:
            data = resp.json()
            items = data if isinstance(data, list) else data.get("results", [])
            results = [
                {"smiles": item.get("smiles", ""), "zinc_id": item.get("zinc_id", "")}
                for item in items
                if item.get("smiles")
            ][:limit]
    except Exception:
        pass

    if results:
        set_cached("zinc", cache_key, results)
    return results


def get_fda_approved(limit: int = 5000) -> list[dict]:
    return _fetch_zinc_subset("fda", limit)


def get_clinical_candidates(limit: int = 5000) -> list[dict]:
    return _fetch_zinc_subset("clinical-candidates", limit)


def get_fragment_library(limit: int = 5000) -> list[dict]:
    return _fetch_zinc_subset("fragment-like", limit)
