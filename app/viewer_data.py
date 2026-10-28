"""Pure read model for the local viewer.

Reads a saved run artifact and nothing else: no provider call, no inference, no
subprocess, no credentials. Numbers come from the stored record, never from model
prose. Keep this module import-free of anything that can reach a network or a GPU.
"""
import csv
import hashlib
import io
import json
import math
from pathlib import Path

CLAIM_BANNER = (
    'ESM scores are sequence preferences. They are not T50, activity, solubility, Tm '
    'or experimental validation. No biological efficacy is established, and geometry, '
    'coordinate mapping and retained function remain unverified.')

_BADGES = {'live':'LIVE','replay':'REPLAY','synthetic_fixture':'SYNTHETIC_FIXTURE'}


def load_run_view(path):
    """Return a flat, display-ready view of one saved run artifact."""
    path = Path(path)
    if not path.is_file():
        raise ValueError('No saved run artifact at that path; nothing is rendered')
    raw = path.read_bytes()
    record = json.loads(raw.decode('utf-8'))
    # Accept both a bare report and an ArtifactStore envelope.
    if isinstance(record, dict) and 'content' in record and 'artifact_id' in record:
        if (_digest_or_none(record['artifact_id']) is None
                or _canonical_digest(record['content']) != record['artifact_id']):
            raise ValueError('Saved report envelope checksum mismatch')
        record = record['content']
    if not isinstance(record, dict) or 'status' not in record:
        raise ValueError('Saved artifact is not a run report')
    # source_mode may describe a live Meta validation with no ESM computation.
    # Only score-specific provenance can establish an ESM source mode.
    score_hash = _score_artifact_sha256(record)
    artifacts = record.get('score_artifacts') or []
    score = artifacts[0] if artifacts and isinstance(artifacts[0],dict) else {}
    esm_mode = (record.get('esm_source_mode') or score.get('source_mode')) if score_hash else None
    original_esm_mode = (record.get('source_score_mode_at_original_execution')
                         or _provenance(record).get('source_mode') or esm_mode) if score_hash else None
    cost = record.get('actual_cost_micros')
    file_digest = hashlib.sha256(raw).hexdigest()
    chain = provenance_chain(record, file_digest)
    integrity = ('mismatch' if any(link['mismatch'] for link in chain) else
                 'incomplete' if any(link['absent'] for link in chain[:3]) else
                 'locally_consistent')
    return {
        'run_id': record.get('run_id'),
        'workflow': record.get('workflow'),
        'status': record.get('status'),
        'stop_reason': record.get('stop_reason'),
        'is_complete': record.get('status') in {'sequence_review_complete','validation_complete',
                                                'final_report_complete'},
        'provider': record.get('provider'),
        'requested_model': record.get('requested_model'),
        'actual_model': record.get('actual_model'),
        'mcp_protocol_version': record.get('mcp_protocol_version'),
        'meta_request_attempts': record.get('meta_request_attempts'),
        'source_mode': record.get('source_mode'),
        'esm_source_mode': esm_mode,
        'esm_badge': _BADGES.get(esm_mode,'UNKNOWN') if score_hash else 'UNAVAILABLE',
        'original_esm_badge': _BADGES.get(original_esm_mode,'UNKNOWN') if score_hash else 'UNAVAILABLE',
        'is_scientific_evidence': esm_mode in {'live','replay'} and integrity == 'locally_consistent',
        'integrity_status': integrity,
        'external_authenticity_verified': False,
        'scores_reused_from_saved_artifact': bool(record.get('scores_reused_from_saved_artifact')),
        'ranking_scope': record.get('ranking_scope'),
        'scientific_scope': record.get('scientific_scope'),
        'biological_efficacy_established': bool(record.get('biological_efficacy_established')),
        'candidates': record.get('candidates') or [],
        'candidate_count': len(record.get('candidates') or []),
        'score_artifact_sha256': score_hash,
        'provenance': _provenance(record),
        'tool_calls': [event.get('tool') for event in record.get('trace') or []
                       if event.get('event')=='mcp_tool'],
        'model_narrative': record.get('model_narrative'),
        'actual_cost_micros': cost,
        'cost_status': record.get('cost_status'),
        'cost_display': _cost_display(cost, record.get('cost_status')),
        'task_context': task_context(record),
        'tool_events': public_tool_events(record.get('trace') or []),
        'decision_steps': public_decision_steps(record.get('trace') or []),
        'file_sha256': file_digest,
        'lineage': _pick(record.get('replay_export') or {}, _LINEAGE_FIELDS),
        'provenance_chain': chain,
    }


def _score_artifact_sha256(record):
    artifacts = record.get('score_artifacts') or []
    if artifacts and isinstance(artifacts[0], dict):
        return artifacts[0].get('artifact_sha256')
    return record.get('source_score_artifact_sha256')


def _provenance(record):
    artifacts = record.get('score_artifacts') or []
    if artifacts and isinstance(artifacts[0], dict):
        return _pick(artifacts[0].get('provenance') or {}, _PROVENANCE_FIELDS)
    return {}


def _cost_display(micros, status):
    """A reservation is not a bill. Unverified cost stays visibly unverified."""
    if type(micros) is int and status == 'actual':
        return f'${micros/1_000_000:.6f}'
    return 'unknown (not verified)'


def format_candidate_rows(candidates):
    """Rank rows straight from the stored numbers, preserving the saved order."""
    return [{'rank': index,
             'candidate_id': row.get('candidate_id'),
             'wild_type': row.get('wild_type'),
             'full_position': row.get('full_position'),
             'mutant': row.get('mutant'),
             'score': f"{row['score']:.6f}" if type(row.get('score')) in (int,float) and math.isfinite(row['score']) else None,
             'score_kind': row.get('score_kind'),
             'rank_policy': row.get('rank_policy')}
            for index, row in enumerate(candidates, start=1)]


def claim_banner(view=None):
    """The scope statement shown on every screen, regardless of run outcome."""
    return CLAIM_BANNER


_PROVENANCE_FIELDS = frozenset({
    'checkpoint', 'checkpoint_revision', 'model_key', 'device', 'precision',
    'sequence_context', 'source_mode', 'reference_id', 'reference_sha256',
    'tokenizer_sha256', 'weights_sha256', 'config_sha256', 'implementation',
    'score_kind', 'upstream_authenticity', 'scoring_method', 'sequence_sha256'})
_LINEAGE_FIELDS = frozenset({
    'source_file_sha256', 'source_content_sha256', 'source_run_id',
    'source_score_artifact_sha256', 'export_date_kst'})
_ARGUMENT_FIELDS = frozenset({
    'reference_id', 'positions_1based', 'model_key', 'candidate_id', 'max_hits',
    'atlas_accession', 'accession'})
_RESULT_FIELDS = frozenset({
    'status', 'source_mode', 'artifact_sha256', 'model_key', 'task_id',
    'reference_id', 'error', 'message', 'available', 'reason', 'candidate_count',
    'coordinate_mapping_verified', 'phenotype_calibrated'})
# A model turn may only contribute public accounting. content_chars is a length,
# never the text, and no reasoning field is ever read.
_USAGE_FIELDS = frozenset({'prompt_tokens', 'completion_tokens', 'total_tokens'})


def _pick(value, fields):
    """Bound public scalar/array fields; never copy arbitrary nested source objects."""
    if not isinstance(value, dict):
        return {}
    public = {}
    for key in sorted(fields & value.keys()):
        item = value[key]
        if isinstance(item, str):
            public[key] = item[:2000]
        elif item is None or type(item) in (bool, int):
            public[key] = item
        elif type(item) is float and math.isfinite(item):
            public[key] = item
        elif isinstance(item, list):
            public[key] = [v[:200] if isinstance(v, str) else v for v in item[:200]
                           if v is None or type(v) in (bool, int, str)
                           or (type(v) is float and math.isfinite(v))]
    return public


def task_context(record):
    """Use recorded fields only. Registered policy is displayed separately by the UI."""
    candidates = record.get('candidates') or []
    provenance = _provenance(record)
    references = {row.get('reference_id') for row in candidates if row.get('reference_id')}
    positions = sorted({row['full_position'] for row in candidates
                        if type(row.get('full_position')) is int})
    return {
        'title': ('Saved sequence preference review' if record.get('workflow') == 'sequence_review'
                  else 'Saved run review'),
        'reference_id': (record.get('reference_id') or provenance.get('reference_id')
                         or (next(iter(references)) if len(references) == 1 else None)),
        'positions': positions,
        'objective_id': record.get('objective_profile_id'),
        'additional_constraints': record.get('additional_constraints'),
        'sequence_context': provenance.get('sequence_context'),
        'reference_numbering': record.get('reference_numbering'),
    }


def public_tool_events(trace):
    """Recorded MCP calls in exact order, with public short reasons, never reasoning."""
    events = []
    for event in trace:
        if not isinstance(event, dict) or event.get('event') != 'mcp_tool':
            continue
        arguments = event.get('arguments') or {}
        reason = arguments.get('reason_brief') if isinstance(arguments, dict) else None
        events.append({
            'step': len(events) + 1,
            'tool': str(event.get('tool') or 'unrecorded tool')[:120],
            'reason_brief': reason[:500] if isinstance(reason, str) else None,
            'arguments': _pick(arguments, _ARGUMENT_FIELDS),
            'result': _pick(event.get('result') or {}, _RESULT_FIELDS),
        })
    return events


def public_decision_steps(trace):
    """The full recorded alternation: the model asks, registered code computes.

    public_tool_events deliberately keeps its own tool-only numbering, so the two
    views can be read side by side without one renumbering the other. A model turn
    contributes public accounting only: finish reason, model, token usage, elapsed
    time and the *length* of its reply. Reply text and reasoning are never read.
    """
    steps = []
    for event in trace:
        if not isinstance(event, dict):
            continue
        kind = event.get('event')
        if kind == 'meta_response':
            elapsed = event.get('elapsed_seconds')
            chars = event.get('content_chars')
            steps.append({
                'step': len(steps) + 1,
                'kind': 'meta_response',
                'actor': 'Meta model',
                'label': str(event.get('actual_model') or 'unrecorded model')[:120],
                'finish_reason': str(event.get('finish_reason') or 'unrecorded')[:60],
                'usage': _pick(event.get('usage') or {}, _USAGE_FIELDS),
                'elapsed_seconds': (round(elapsed, 3)
                                    if type(elapsed) is float and math.isfinite(elapsed)
                                    else elapsed if type(elapsed) is int else None),
                'content_chars': chars if type(chars) is int else None,
            })
        elif kind == 'mcp_tool':
            arguments = event.get('arguments') or {}
            reason = arguments.get('reason_brief') if isinstance(arguments, dict) else None
            steps.append({
                'step': len(steps) + 1,
                'kind': 'mcp_tool',
                'actor': 'MCP server (registered code)',
                'label': str(event.get('tool') or 'unrecorded tool')[:120],
                'reason_brief': reason[:500] if isinstance(reason, str) else None,
                'arguments': _pick(arguments, _ARGUMENT_FIELDS),
                'result': _pick(event.get('result') or {}, _RESULT_FIELDS),
            })
    return steps


def select_candidate_rows(rows, candidate_ids=None, *, limit=None):
    """Filter already-ranked artifact rows. A selection never renumbers or reranks."""
    if candidate_ids is not None and len(set(candidate_ids)) > 3:
        raise ValueError('Compare at most three candidates')
    selected = [dict(row) for row in rows
                if candidate_ids is None or row['candidate_id'] in candidate_ids]
    return selected if limit is None else selected[:limit]


def candidate_csv(rows):
    """Export the displayed rows; neutralize spreadsheet formulas only in text cells."""
    output = io.StringIO(newline='')
    fields = ['rank', 'candidate_id', 'full_position', 'wild_type', 'mutant',
              'score', 'score_kind', 'rank_policy']
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for row in rows:
        safe = {}
        for field in fields:
            value = row.get(field)
            if field == 'score' and value is not None:
                # Only a finite decimal from our artifact formatter is numeric.
                try:
                    number = float(value)
                    value = value if math.isfinite(number) else None
                except (TypeError, ValueError):
                    value = None
            elif isinstance(value, str) and (value.startswith(('\t', '\r', '\n'))
                    or value.lstrip().startswith(('=', '+', '-', '@'))):
                value = "'" + value
            safe[field] = value
        writer.writerow(safe)
    return output.getvalue()


PROVENANCE_CHAIN_SCOPE = (
    'Local checks recompute the saved score payload checksum, compare the displayed rows '
    'with that payload, and compare the recorded scoring-tool digest. Input-file and '
    'original-export hashes are recorded only: those source bytes are not opened or '
    'authenticated here. The opened-file hash identifies the bytes being viewed; it '
    'does not link them to an external source. This record is not signed, not externally '
    'anchored and not a tamper-proof ledger. A holder could rewrite it consistently.'
)
_CHAIN_INPUT_FIELDS = ('reference_sha256', 'weights_sha256', 'tokenizer_sha256', 'config_sha256')


def _first_score_artifact(artifact):
    artifacts = artifact.get('score_artifacts')
    return artifacts[0] if isinstance(artifacts, list) and artifacts \
        and isinstance(artifacts[0], dict) else {}


def _digest_or_none(value):
    return value if (isinstance(value, str) and len(value) == 64
                     and set(value) <= set('0123456789abcdef')) else None


def _canonical_digest(value):
    """The saved artifact writer's JSON digest; malformed/nonfinite data stays invalid."""
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(encoded.encode()).hexdigest()


def _candidate_rows_match(artifact, score):
    """Verify the displayed order against the saved common ranking without changing it."""
    rows, candidates = score.get('rows'), artifact.get('candidates')
    if not isinstance(rows, list) or not rows or not isinstance(candidates, list):
        return False
    identities = set()
    for row in rows:
        if not isinstance(row, dict):
            return False
        identity, value = row.get('candidate_id'), row.get('score')
        if (not isinstance(identity, str) or not identity or identity in identities
                or type(value) not in (int, float) or not math.isfinite(value)):
            return False
        identities.add(identity)
    return candidates == sorted(rows, key=lambda row: (-row['score'], row['candidate_id']))


def provenance_chain(artifact, opened_file_sha256):
    """Local consistency checks and explicitly unverified source commitments.

    A recorded hash string alone does not verify a source file. Only checks supported
    by bytes available in this saved record can set link_verified. No source file is
    opened, and no provider, model or scientific runtime is imported.
    """
    if not isinstance(artifact, dict):
        raise ValueError('Expected a saved run artifact object')
    score = _first_score_artifact(artifact)
    provenance = score.get('provenance') if isinstance(score.get('provenance'), dict) else {}
    inputs = {field: _digest_or_none(provenance.get(field)) for field in _CHAIN_INPUT_FIELDS}
    artifact_digest = _digest_or_none(score.get('artifact_sha256'))
    computed_digest = _canonical_digest({key: value for key, value in score.items()
                                         if key != 'artifact_sha256'}) if score else None
    score_checksum_matches = artifact_digest is not None and computed_digest == artifact_digest
    candidate_rows_match = _candidate_rows_match(artifact, score)
    score_missing = (not score or artifact_digest is None or not score.get('rows')
                     or not isinstance(artifact.get('candidates'), list))
    score_verified = score_checksum_matches and candidate_rows_match and not score_missing
    score_mismatch = not score_missing and not score_verified

    recorded = None
    for event in artifact.get('trace') or []:
        if (not isinstance(event, dict) or event.get('event') != 'mcp_tool'
                or event.get('tool') != 'score_positions'):
            continue
        result = event.get('result')
        candidate = _digest_or_none(result.get('artifact_sha256')) if isinstance(result, dict) else None
        if candidate is not None:
            recorded = candidate
            break
    trace_matches = recorded is not None and artifact_digest is not None and recorded == artifact_digest
    trace_mismatch = recorded is not None and artifact_digest is not None and recorded != artifact_digest

    export = artifact.get('replay_export')
    export = export if isinstance(export, dict) else None
    export_carried = _digest_or_none((export or {}).get('source_score_artifact_sha256'))
    export_digest = _digest_or_none((export or {}).get('source_content_sha256'))
    export_file_digest = _digest_or_none((export or {}).get('source_file_sha256'))
    export_missing = export is None or any(value is None for value in
                                           (export_carried, export_digest, export_file_digest))
    export_mismatch = (export_carried is not None and artifact_digest is not None
                       and export_carried != artifact_digest)
    opened_digest = _digest_or_none(opened_file_sha256)

    chain = [
        {'stage': 'model_inputs', 'label': 'Recorded reference and model-file digests',
         'digest': inputs['reference_sha256'], 'detail': inputs,
         'carries_upstream_digest': None,
         'link_verified': False, 'check_scope': 'input_files_not_opened',
         'status': 'missing' if any(value is None for value in inputs.values()) else 'recorded only',
         'mismatch': False, 'absent': any(value is None for value in inputs.values())},
        {'stage': 'score_artifact', 'label': 'Saved score payload and displayed candidate rows',
         'digest': artifact_digest, 'detail': {
             'rows': len(score.get('rows') or []), 'computed_sha256': computed_digest,
             'candidate_rows_match': candidate_rows_match},
         'carries_upstream_digest': inputs['reference_sha256'],
         'link_verified': score_verified, 'check_scope': 'saved_score_payload_and_candidate_rows',
         'status': 'missing' if score_missing else ('local checksum match' if score_verified else 'mismatch'),
         'mismatch': score_mismatch, 'absent': score_missing},
        {'stage': 'recorded_tool_result', 'label': 'MCP tool result that returned that artifact',
         'digest': recorded, 'detail': {'source': 'score_positions result.artifact_sha256'},
         'carries_upstream_digest': artifact_digest,
         'link_verified': trace_matches, 'check_scope': 'recorded_score_digest_equality',
         'status': 'recorded digest match' if trace_matches else ('mismatch' if trace_mismatch else 'missing'),
         'mismatch': trace_mismatch, 'absent': recorded is None or artifact_digest is None},
        {'stage': 'replay_export', 'label': 'Recorded original export-source digests',
         'digest': export_digest, 'detail': {
             'source_score_artifact_sha256': export_carried,
             'source_file_sha256': export_file_digest,
             'score_digest_matches': (export_carried is not None and artifact_digest is not None
                                       and export_carried == artifact_digest)},
         'carries_upstream_digest': export_carried,
         'link_verified': False, 'check_scope': 'source_bytes_not_opened',
         'status': 'mismatch' if export_mismatch else ('missing' if export_missing else 'recorded only'),
         'mismatch': export_mismatch, 'absent': export_missing},
        {'stage': 'opened_file', 'label': 'Bytes of the file this screen is rendering',
         'digest': opened_digest, 'detail': {},
         'carries_upstream_digest': None,
         'link_verified': False, 'check_scope': 'opened_bytes_identity_only',
         'status': 'computed locally' if opened_digest else 'missing',
         'mismatch': False, 'absent': opened_digest is None},
    ]
    return chain
