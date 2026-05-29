import re
import requests
from .cache import make_cache_key, get_cached, set_cached

BASE = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug'
SOURCE = 'surechembl'


def _get_patent_ids_by_name(name: str) -> list:
    key = make_cache_key('patents_name', {'name': name})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        encoded = requests.utils.quote(name, safe='')
        r = requests.get(f'{BASE}/compound/name/{encoded}/xrefs/PatentID/JSON', timeout=15)
        if r.status_code == 404:
            set_cached(SOURCE, key, [])
            return []
        r.raise_for_status()
        info = r.json().get('InformationList', {}).get('Information', [])
        ids = info[0].get('PatentID', []) if info else []
        set_cached(SOURCE, key, ids)
        return ids
    except Exception:
        return []


def _get_patent_ids_by_cid(cid: int) -> list:
    key = make_cache_key('patents_cid', {'cid': cid})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.get(f'{BASE}/compound/cid/{cid}/xrefs/PatentID/JSON', timeout=15)
        if r.status_code == 404:
            set_cached(SOURCE, key, [])
            return []
        r.raise_for_status()
        info = r.json().get('InformationList', {}).get('Information', [])
        ids = info[0].get('PatentID', []) if info else []
        set_cached(SOURCE, key, ids)
        return ids
    except Exception:
        return []


def _get_cid_from_smiles(smiles: str) -> int | None:
    key = make_cache_key('cid_smiles', {'smiles': smiles})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        encoded = requests.utils.quote(smiles, safe='')
        r = requests.get(f'{BASE}/compound/smiles/{encoded}/cids/JSON', timeout=15)
        if r.status_code == 404:
            set_cached(SOURCE, key, None)
            return None
        r.raise_for_status()
        cids = r.json().get('IdentifierList', {}).get('CID', [])
        result = cids[0] if cids else None
        set_cached(SOURCE, key, result)
        return result
    except Exception:
        return None


_OFFICE_LABELS = {
    'US': 'USPTO',
    'EP': 'EPO',
    'WO': 'WIPO',
    'JP': 'JPO',
    'CN': 'CNIPA',
    'CA': 'CIPO',
    'AU': 'IP Australia',
    'GB': 'UKIPO',
    'DE': 'DPMA',
    'FR': 'INPI',
}

_TYPE_LABELS = {
    'US': 'US Patent',
    'EP': 'European Patent',
    'WO': 'PCT Application',
    'JP': 'Japanese Patent',
    'CN': 'Chinese Patent',
    'CA': 'Canadian Patent',
    'AU': 'Australian Patent',
    'GB': 'UK Patent',
    'DE': 'German Patent',
    'FR': 'French Patent',
}


def _parse_patent_meta(patent_id: str) -> dict:
    """Extract title, assignee, and filing year from a patent ID string."""
    meta = {
        'patent_number': patent_id,
        'document_id': patent_id,
        'title': None,
        'assignee': None,
        'filing_date': None,
        'date': None,
    }
    prefix = re.match(r'^([A-Z]{2})', patent_id)
    office = prefix.group(1) if prefix else ''
    meta['assignee'] = _OFFICE_LABELS.get(office, office or 'Unknown')
    meta['title'] = _TYPE_LABELS.get(office, 'Patent')

    # US patent applications encode filing year: US20030013699 → 2003
    m = re.match(r'^US(\d{4})\d{7}', patent_id)
    if m:
        meta['date'] = m.group(1)
        meta['title'] = f"US Patent Application ({m.group(1)})"
        return meta

    # WO/PCT applications encode year: WO2002064550 → 2002
    m = re.match(r'^WO(\d{4})', patent_id)
    if m:
        meta['date'] = m.group(1)
        meta['title'] = f"PCT Application ({m.group(1)})"
        return meta

    return meta


def search_compound(name: str) -> list:
    """Return patent records for a drug name (used by DrugPatentsView)."""
    ids = _get_patent_ids_by_name(name)
    return [_parse_patent_meta(pid) for pid in ids[:50]]


def get_compound_patents(schembl_id: str) -> list:
    """Kept for compatibility — schembl_id treated as PubChem CID."""
    try:
        cid = int(schembl_id)
        ids = _get_patent_ids_by_cid(cid)
        return [_parse_patent_meta(pid) for pid in ids[:20]]
    except (ValueError, TypeError):
        return []


def search_by_smiles(smiles: str) -> list:
    """Return patent records for a SMILES string."""
    cid = _get_cid_from_smiles(smiles)
    if not cid:
        return []
    ids = _get_patent_ids_by_cid(cid)
    return [_parse_patent_meta(pid) for pid in ids[:20]]


def get_patent_status(smiles: str) -> str:
    """Returns 'covered', 'free', or 'unknown' for a given SMILES."""
    try:
        cid = _get_cid_from_smiles(smiles)
        if cid is None:
            return 'unknown'
        ids = _get_patent_ids_by_cid(cid)
        return 'covered' if ids else 'free'
    except Exception:
        return 'unknown'
