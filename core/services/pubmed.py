import requests
import xml.etree.ElementTree as ET
from .cache import make_cache_key, get_cached, set_cached

BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'
SOURCE = 'pubmed'


def search_articles(query: str, max_results: int = 20) -> list:
    key = make_cache_key('search', {'query': query, 'max': max_results})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.get(
            f'{BASE}/esearch.fcgi',
            params={'db': 'pubmed', 'term': query, 'retmax': max_results, 'retmode': 'json'},
            timeout=15,
        )
        r.raise_for_status()
        pmids = r.json().get('esearchresult', {}).get('idlist', [])
        set_cached(SOURCE, key, pmids)
        return pmids
    except Exception:
        return []


def get_summaries(pmids: list) -> list:
    if not pmids:
        return []
    key = make_cache_key('summaries', {'pmids': sorted(pmids)})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.get(
            f'{BASE}/esummary.fcgi',
            params={'db': 'pubmed', 'id': ','.join(pmids), 'retmode': 'json'},
            timeout=15,
        )
        r.raise_for_status()
        result = r.json().get('result', {})
        summaries = [result[pmid] for pmid in pmids if pmid in result]
        set_cached(SOURCE, key, summaries)
        return summaries
    except Exception:
        return []


def fetch_abstract(pmid: str) -> dict:
    key = make_cache_key('abstract', {'pmid': pmid})
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.get(
            f'{BASE}/efetch.fcgi',
            params={'db': 'pubmed', 'id': pmid, 'rettype': 'abstract', 'retmode': 'xml'},
            timeout=15,
        )
        r.raise_for_status()
        root = ET.fromstring(r.text)
        abstract_nodes = root.findall('.//AbstractText')
        abstract = ' '.join(n.text or '' for n in abstract_nodes if n.text)
        data = {'pmid': pmid, 'abstract': abstract}
        set_cached(SOURCE, key, data)
        return data
    except Exception:
        return {'pmid': pmid, 'abstract': ''}
