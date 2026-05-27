import requests
from .cache import make_cache_key, get_cached, set_cached

BASE = 'https://rest.uniprot.org'
SOURCE = 'uniprot'
FIELDS = 'protein_name,gene_names,cc_function,cc_disease,cc_tissue_specificity,organism_name,xref_pdb,xref_chembl'


def get_protein(uniprot_id: str) -> dict:
    key = make_cache_key('protein', {'id': uniprot_id})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.get(
            f'{BASE}/uniprotkb/{uniprot_id}',
            params={'fields': FIELDS, 'format': 'json'},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        set_cached(SOURCE, key, data)
        return data
    except Exception:
        return {}


def search_protein(gene: str, organism_id: int = 9606) -> list:
    key = make_cache_key('search', {'gene': gene, 'organism_id': organism_id})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.get(
            f'{BASE}/uniprotkb/search',
            params={
                'query': f'gene:{gene} AND organism_id:{organism_id}',
                'fields': FIELDS,
                'format': 'json',
                'size': 5,
            },
            timeout=15,
        )
        r.raise_for_status()
        results = r.json().get('results', [])
        set_cached(SOURCE, key, results)
        return results
    except Exception:
        return []
