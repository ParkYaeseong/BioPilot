"""Fixed, reviewed Atlas WT context. No network client or caller-selected source.

The snapshot commits a sanitized projection of an actual HTTP response. Its local
hash is verified; it is not a cryptographic signature from the upstream provider.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re

from app.core.targets import REFERENCE_SHA256

SNAPSHOT_NAME = 'reference/atlas_registered_reference_20261028.json'
POLICY_NAME = 'reference/atlas_snapshot_policy.json'
SNAPSHOT_SHA256 = '6fe772ae6a5d1fe02824e67fc3481f5f5464c342d6a1c1090b4e37e69c50c7ce'
PROTEIN_MD5 = '5003d8cdae76deeb4cce054dfa7a3b04'
SOURCE_URL = 'https://biohub.ai/esm/protein/api/v1alpha1/proteins/' + PROTEIN_MD5


def load_registered_atlas_snapshot(root=None, *, require_enabled=True):
    """Only a provisioned root is injectable by trusted code/tests; MCP has no path."""
    root = Path(root) if root is not None else Path(__file__).resolve().parents[2]
    policy = json.loads((root / POLICY_NAME).read_text(encoding='utf-8'))
    if (not isinstance(policy, dict) or set(policy) != {'enabled', 'provider', 'snapshot_sha256'}
            or type(policy['enabled']) is not bool
            or (require_enabled and policy['enabled'] is not True)
            or policy['provider'] != 'biohub_esm_atlas'
            or policy['snapshot_sha256'] != SNAPSHOT_SHA256):
        raise ValueError('Atlas snapshot is disabled or differs from reviewed policy')
    raw = (root / SNAPSHOT_NAME).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SNAPSHOT_SHA256:
        raise ValueError('Atlas snapshot hash mismatch')
    data = json.loads(raw)
    fields = {'status', 'provider', 'source_url', 'request_params', 'http_status', 'retrieved_at',
              'raw_response_sha256', 'reference_sha256', 'protein_hash_md5', 'sequence_context',
              'identity', 'confidence', 'feature_count_recorded', 'annotation_only',
              'baseline_rank_changed', 'scientific_evidence', 'experimental_validation',
              'folded_on_demand', 'raw_text_exposed'}
    if (not isinstance(data, dict) or set(data) != fields or data['status'] != 'available'
            or data['provider'] != 'biohub_esm_atlas' or data['source_url'] != SOURCE_URL
            or data['http_status'] != 200 or data['reference_sha256'] != REFERENCE_SHA256
            or data['protein_hash_md5'] != PROTEIN_MD5 or data['sequence_context'] != 'full_212'
            or data['request_params'] != {'fold_on_miss': 'false', 'topk_features': 10,
                                          'normalize_features': 'true'}
            or data['annotation_only'] is not True or data['baseline_rank_changed'] is not False
            or data['scientific_evidence'] is not True or data['experimental_validation'] is not False
            or data['folded_on_demand'] is not False or data['raw_text_exposed'] is not False
            or not isinstance(data['identity'], dict) or set(data['identity']) != {'accession', 'source'}
            or not isinstance(data['confidence'], dict) or set(data['confidence']) != {'ptm', 'mean_plddt'}
            or type(data['feature_count_recorded']) is not int or not 0 <= data['feature_count_recorded'] <= 10
            or re.fullmatch('[0-9a-f]{64}', data['raw_response_sha256']) is None):
        raise ValueError('Atlas snapshot differs from reviewed safe context schema')
    for value in data['identity'].values():
        if value is not None and (not isinstance(value, str)
                or re.fullmatch('[A-Za-z0-9_.:|/-]{1,128}', value) is None):
            raise ValueError('Invalid Atlas identity')
    for value in data['confidence'].values():
        if value is not None and (type(value) not in (int, float)
                or not math.isfinite(value) or not 0 <= value <= 1):
            raise ValueError('Invalid Atlas structure confidence')
    return deepcopy(data)


def atlas_tool_result(snapshot, max_hits):
    """One exact WT record; requested hit count never causes a search or computation."""
    if type(max_hits) is not int or not 1 <= max_hits <= 100:
        raise ValueError('Invalid Atlas hit bound')
    return {'status': 'ok', 'source_mode': 'imported_snapshot',
        'original_acquisition_mode': 'actual_external_http_response',
        'provider': 'biohub_esm_atlas', 'query_scope': 'exact_registered_wt_only',
        'snapshot_sha256': SNAPSHOT_SHA256, 'snapshot_integrity_verified': True,
        'upstream_authenticity_verified': False,
        'raw_response_sha256': snapshot['raw_response_sha256'],
        'source_url': SOURCE_URL, 'retrieved_at': snapshot['retrieved_at'],
        'hits': [{'accession': snapshot['identity']['accession'],
                  'source': snapshot['identity']['source'], 'reference_sha256': REFERENCE_SHA256,
                  'sequence_length': 212, 'structure_confidence': snapshot['confidence'],
                  'sae_feature_count': snapshot['feature_count_recorded']}],
        'annotation_only': True, 'baseline_rank_changed': False,
        'experimental_validation': False, 'folded_on_demand': False,
        'limitations': 'Exact registered WT context only; no homolog search was performed. '
                      'Null structure confidence does not establish a stored structure. '
                      'Atlas context does not establish a variant effect, T50 or retained activity.'}
