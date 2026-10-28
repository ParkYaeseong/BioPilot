"""Exact registered WT lookup against the current Biohub Atlas, without compute.

No arbitrary search, variant upload, outcome text, or automatic folding. Raw upstream
prose is not forwarded to the prediction host. Numerical confidence is context only.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
import re

from app.core.targets import REFERENCE_SHA256, registered_profile, validate_target

BASE = 'https://biohub.ai/esm/protein/api/v1alpha1/proteins/'
MAX_BYTES = 6 * 1024 * 1024


def _unavailable(reason):
    return {'status': 'unavailable', 'reason': reason, 'scientific_evidence': False,
            'provider': 'biohub_esm_atlas', 'annotation_only': True,
            'baseline_rank_changed': False}


class AtlasContextClient:
    def __init__(self, *, read_approved=False, transport=None):
        self.read_approved = read_approved
        self.transport = transport

    def lookup_reference(self):
        if self.read_approved is not True:
            return _unavailable('external_read_not_approved')
        target = validate_target(registered_profile(), 'sequence_plausibility_review')
        protein_hash = hashlib.md5(target.reference_sequence.encode('ascii'), usedforsecurity=False).hexdigest()
        url = BASE + protein_hash
        params = {'fold_on_miss': 'false', 'topk_features': 10, 'normalize_features': 'true'}
        raw, http_status = None, None
        def unavailable(reason):
            return _unavailable(reason) | {'source_url': url, 'request_params': params,
                'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'http_status': http_status,
                'raw_response_sha256': hashlib.sha256(raw).hexdigest() if raw is not None else None,
                'reference_sha256': REFERENCE_SHA256, 'protein_hash_md5': protein_hash}
        try:
            if self.transport is None:
                import requests
                # Streaming caps the body before allocating an unbounded response.
                with requests.get(url, params=params, allow_redirects=False,
                                  timeout=(5, 20), stream=True) as response:
                    http_status = response.status_code
                    if response.status_code != 200:
                        return unavailable('not_found' if response.status_code == 404 else 'http_' + str(response.status_code))
                    chunks, size = [], 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > MAX_BYTES:
                            return unavailable('response_too_large')
                        chunks.append(chunk)
                    raw = b''.join(chunks)
            else:
                response = self.transport(url, params=params, allow_redirects=False, timeout=(5, 20))
                http_status = response.status_code
                if response.status_code != 200:
                    return unavailable('not_found' if response.status_code == 404 else 'http_' + str(response.status_code))
                raw = response.content
            if len(raw) > MAX_BYTES:
                return unavailable('response_too_large')
            data = json.loads(raw)
            if (data.get('protein_hash') != protein_hash
                    or data.get('sequence') != target.reference_sequence
                    or data.get('sequence_length') != 212
                    or data.get('folded_on_demand') is not False):
                return unavailable('response_identity_or_no_compute_mismatch')
            confidence = {}
            for key in ('ptm', 'mean_plddt'):
                value = data.get(key)
                if value is not None and (type(value) not in (int, float)
                        or not math.isfinite(value) or not 0 <= value <= 1):
                    return unavailable('invalid_confidence')
                confidence[key] = value
            # Do not project names/descriptions/header/function fields: they are
            # untrusted outcome-bearing text, even if the provider is public.
            identity = {}
            for key in ('accession', 'source'):
                value = data.get(key)
                if value is not None and (not isinstance(value, str)
                        or re.fullmatch('[A-Za-z0-9_.:|/-]{1,128}', value) is None):
                    return unavailable('invalid_source_identity')
                identity[key] = value
            features = data.get('sae_features')
            if not isinstance(features, list) or len(features) > 100:
                return unavailable('invalid_feature_envelope')
            return {'status': 'available', 'provider': 'biohub_esm_atlas',
                'source_url': url, 'request_params': params,
                'http_status': http_status,
                'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'raw_response_sha256': hashlib.sha256(raw).hexdigest(),
                'reference_sha256': REFERENCE_SHA256, 'protein_hash_md5': protein_hash,
                'sequence_context': 'full_212', 'identity': identity,
                'confidence': confidence, 'feature_count_recorded': len(features),
                'annotation_only': True, 'baseline_rank_changed': False,
                'scientific_evidence': True, 'experimental_validation': False,
                'folded_on_demand': False, 'raw_text_exposed': False}
        except (ValueError, TypeError, KeyError, OSError):
            return unavailable('provider_or_schema_error')
        except Exception as error:
            # Requests network errors are not exposed with URLs/tokens or raw body.
            if type(error).__module__.startswith('requests'):
                return unavailable('provider_unreachable')
            raise
