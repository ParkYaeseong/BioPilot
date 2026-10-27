"""Deterministic common-baseline ranking; annotations never silently rerank."""
from copy import deepcopy
import math

from app.science.esm_engine import SCORE_KIND, REFERENCE_SHA256
from app.science.models import MODEL_REGISTRY


def rank_candidates(records, rank_policy='esm150_masked_v1'):
    specs = [spec for spec in MODEL_REGISTRY.values() if spec.rank_policy == rank_policy]
    if len(specs) != 1:
        raise ValueError('Unsupported rank policy')
    spec = specs[0]
    rows = [deepcopy(dict(record)) for record in records]
    if not rows:
        return []
    common_keys = (
        'checkpoint', 'reference_sha256', 'sequence_context', 'score_kind',
        'weights_sha256', 'tokenizer_sha256', 'implementation', 'precision',
        'model_key', 'rank_policy',
    )
    expected = {key: rows[0].get(key) for key in common_keys}
    if (any(value is None for value in expected.values()) or expected['checkpoint'] != spec.checkpoint
            or expected['model_key'] != spec.key or expected['rank_policy'] != rank_policy
            or expected['reference_sha256'] != REFERENCE_SHA256
            or expected['sequence_context'] != 'full_212' or expected['score_kind'] != SCORE_KIND):
        raise ValueError('Ranking requires the registered common ESM baseline')
    seen = set()
    fixture = rows[0].get('source_mode') == 'synthetic_fixture'
    for row in rows:
        candidate_id = row.get('candidate_id')
        score = row.get('score')
        if (not isinstance(candidate_id, str) or not candidate_id or candidate_id in seen
                or isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score)):
            raise ValueError('Missing, duplicate or invalid candidate score')
        if any(row.get(key) != value for key, value in expected.items()):
            raise ValueError('Mixed checkpoint/context/provenance cannot be ranked')
        if row.get('source_mode') not in {'live', 'replay', 'synthetic_fixture'}:
            raise ValueError('Unknown score source mode')
        if (row.get('source_mode') == 'synthetic_fixture') != fixture:
            raise ValueError('Synthetic fixture and real results cannot share a rank')
        seen.add(candidate_id)
    return sorted(rows, key=lambda row: (-row['score'], row['candidate_id']))
