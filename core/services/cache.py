import hashlib
import json
from datetime import timedelta

from django.utils import timezone


TTL_MAP = {
    'pubchem': 7 * 24 * 3600,
    'chembl': 7 * 24 * 3600,
    'opentargets': 7 * 24 * 3600,
    'uniprot': 7 * 24 * 3600,
    'pkcsm': 7 * 24 * 3600,
    'comptox': 7 * 24 * 3600,
    'pubmed': 24 * 3600,
    'clinicaltrials': 24 * 3600,
    'openfda': 3 * 24 * 3600,
    'openfda_guidance': 3 * 24 * 3600,
    'dailymed': 3 * 24 * 3600,
    'askcos': 24 * 3600,
    'nist': 30 * 24 * 3600,
}


def make_cache_key(endpoint: str, params: dict) -> str:
    raw = json.dumps({'endpoint': endpoint, 'params': params}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def get_cached(source: str, key: str):
    from core.models import ExternalDataCache
    try:
        entry = ExternalDataCache.objects.get(source=source, query_key=key)
        if entry.expires_at > timezone.now():
            return entry.response_data
        entry.delete()
    except ExternalDataCache.DoesNotExist:
        pass
    return None


def set_cached(source: str, key: str, data: dict, ttl_seconds: int = None) -> None:
    from core.models import ExternalDataCache
    if ttl_seconds is None:
        ttl_seconds = TTL_MAP.get(source, 24 * 3600)
    expires_at = timezone.now() + timedelta(seconds=ttl_seconds)
    ExternalDataCache.objects.update_or_create(
        source=source,
        query_key=key,
        defaults={'response_data': data, 'expires_at': expires_at},
    )
