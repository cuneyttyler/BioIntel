import requests
from .cache import make_cache_key, get_cached, set_cached

GRAPHQL_URL = 'https://api.platform.opentargets.org/api/v4/graphql'
SOURCE = 'opentargets'


def _query(query: str, variables: dict) -> dict:
    key = make_cache_key(query[:80], variables)
    cached = get_cached(SOURCE, key)
    if cached is not None:
        return cached
    try:
        r = requests.post(GRAPHQL_URL, json={'query': query, 'variables': variables}, timeout=20)
        r.raise_for_status()
        data = r.json().get('data', {})
        set_cached(SOURCE, key, data)
        return data
    except Exception:
        return {}


def search_disease(term: str) -> list:
    query = '''
    query SearchDisease($q: String!) {
      search(queryString: $q, entityNames: ["disease"], page: {index: 0, size: 10}) {
        hits {
          id
          name
          entity
          description
        }
      }
    }
    '''
    data = _query(query, {'q': term})
    return data.get('search', {}).get('hits', [])


def get_disease_targets(efo_id: str, page: int = 0, size: int = 20) -> dict:
    query = '''
    query DiseaseTargets($efoId: String!, $page: Int!, $size: Int!) {
      disease(efoId: $efoId) {
        id
        name
        description
        associatedTargets(page: {index: $page, size: $size}) {
          count
          rows {
            target {
              id
              approvedSymbol
              approvedName
            }
            score
          }
        }
      }
    }
    '''
    data = _query(query, {'efoId': efo_id, 'page': page, 'size': size})
    return data.get('disease', {})


def get_disease_drugs(efo_id: str, size: int = 20) -> dict:
    query = '''
    query DiseaseDrugs($efoId: String!, $size: Int!) {
      disease(efoId: $efoId) {
        id
        name
        knownDrugs(size: $size) {
          count
          rows {
            drug {
              id
              name
              maximumClinicalTrialPhase
            }
            phase
            status
            disease {
              id
              name
            }
          }
        }
      }
    }
    '''
    data = _query(query, {'efoId': efo_id, 'size': size})
    return data.get('disease', {})
