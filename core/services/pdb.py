import requests
from .cache import get_cached, set_cached

RCSB_SEARCH = "https://search.rcsb.org/rcsbsearch/v1/query"
RCSB_DATA = "https://data.rcsb.org/rest/v1/core"


def search_structures(uniprot_id: str) -> list[dict]:
    cache_key = f"structures:{uniprot_id}"
    cached = get_cached("pdb", cache_key)
    if cached:
        return cached

    query = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                "operator": "exact_match",
                "value": uniprot_id,
            },
        },
        "return_type": "entry",
        "request_options": {"results_verbosity": "compact", "results_content_type": ["experimental"]},
    }

    try:
        resp = requests.post(RCSB_SEARCH, json=query, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = [
            {"pdb_id": entry["identifier"], "score": entry.get("score", 0)}
            for entry in data.get("result_set", [])
        ]
        set_cached("pdb", cache_key, results)
        return results
    except Exception:
        return []


def get_structure(pdb_id: str) -> dict:
    pdb_id = pdb_id.upper()
    cache_key = f"entry:{pdb_id}"
    cached = get_cached("pdb", cache_key)
    if cached:
        return cached

    try:
        resp = requests.get(f"{RCSB_DATA}/entry/{pdb_id}", timeout=15)
        resp.raise_for_status()
        data = resp.json()
        set_cached("pdb", cache_key, data)
        return data
    except Exception:
        return {}


def get_binding_sites(pdb_id: str) -> list[dict]:
    pdb_id = pdb_id.upper()
    cache_key = f"sites:{pdb_id}"
    cached = get_cached("pdb", cache_key)
    if cached:
        return cached

    sites = []
    try:
        resp = requests.get(f"{RCSB_DATA}/entry/{pdb_id}", timeout=15)
        if resp.ok:
            entry = resp.json()
            struct_sites = entry.get("struct_site", [])
            for site in struct_sites:
                sites.append({
                    "site_id": site.get("id", ""),
                    "details": site.get("details", ""),
                    "pdbx_evidence_code": site.get("pdbx_evidence_code", ""),
                })
    except Exception:
        pass

    # Fallback: ligand-based site inference from polymer instances
    if not sites:
        try:
            resp = requests.get(f"{RCSB_DATA}/entry/{pdb_id}/nonpolymer_entity_instances", timeout=15)
            if resp.ok:
                ligands = resp.json()
                for lig in (ligands if isinstance(ligands, list) else [])[:5]:
                    sites.append({
                        "site_id": lig.get("rcsb_nonpolymer_instance_feature_summary", [{}])[0].get("type", "ligand"),
                        "details": f"Ligand binding site inferred from {lig.get('comp_id', 'unknown')}",
                        "pdbx_evidence_code": "inferred",
                    })
        except Exception:
            pass

    set_cached("pdb", cache_key, sites)
    return sites
