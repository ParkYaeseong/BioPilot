"""Export an explicit local report as portable playback; no runtime/provider imports."""
import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo


REPORT_FIELDS = frozenset({
    'run_id', 'workflow', 'status', 'stop_reason', 'provider', 'requested_model',
    'actual_model', 'meta_request_attempts', 'actual_cost_micros', 'cost_status',
    'scientific_scope', 'biological_efficacy_established', 'ranking_scope',
    'mcp_protocol_version', 'bundle_sha256', 'prompt_sha256', 'catalog_sha256',
    'final_instruction_sha256', 'final_report_max_tokens', 'summary', 'model_narrative'})
PROVENANCE_FIELDS = frozenset({
    'checkpoint', 'checkpoint_revision', 'config_sha256', 'device',
    'ignored_nonpersistent_buffers', 'implementation', 'model_key', 'precision',
    'rank_policy', 'reference_id', 'reference_sha256', 'score_kind',
    'sequence_context', 'source_mode', 'tokenizer_sha256', 'upstream_authenticity',
    'weight_file_hashes', 'weights_sha256'})
ROW_FIELDS = PROVENANCE_FIELDS | {'candidate_id', 'full_position', 'wild_type', 'mutant', 'score'}
ARTIFACT_FIELDS = frozenset({'artifact_sha256', 'cached_positions_1based', 'limitations',
    'phenotype_calibrated', 'provenance', 'rank_policy', 'rows', 'score_units', 'source_mode'})
TOKEN_FIELDS = frozenset({'prompt_tokens', 'completion_tokens', 'total_tokens'})
TRACE_FIELDS = frozenset({'event', 'actual_model', 'task_id', 'finish_reason',
    'content_chars', 'elapsed_seconds', 'tool', 'call_id'})
ARGUMENT_FIELDS = frozenset({'reference_id', 'reason_brief', 'model_key', 'positions_1based'})
RESULT_FIELDS = frozenset({'status', 'artifact_sha256', 'model_key', 'source_mode'})


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def selected(value, fields):
    if not isinstance(value, dict):
        raise ValueError('Expected a structured saved report')
    return {key: value[key] for key in fields if key in value}


def verify_artifact(artifact):
    if (not isinstance(artifact, dict) or set(artifact) - ARTIFACT_FIELDS
            or artifact.get('source_mode') not in {'live', 'replay'}
            or artifact.get('phenotype_calibrated') is not False):
        raise ValueError('Only a real, uncalibrated allowlisted score artifact may be exported')
    expected = canonical_hash({k: v for k, v in artifact.items() if k != 'artifact_sha256'})
    if artifact.get('artifact_sha256') != expected:
        raise ValueError('Score artifact checksum mismatch')
    provenance = artifact.get('provenance')
    if (not isinstance(provenance, dict) or set(provenance) - PROVENANCE_FIELDS
            or provenance.get('sequence_context') != 'full_212'
            or provenance.get('source_mode') not in {'live','replay'}
            or provenance.get('rank_policy',artifact.get('rank_policy'))!=artifact.get('rank_policy')):
        raise ValueError('Unapproved score provenance field or context')
    rows = artifact.get('rows')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 200:
        raise ValueError('Expected a bounded saved candidate cohort')
    for row in rows:
        if (not isinstance(row, dict) or set(row) - ROW_FIELDS
                or not isinstance(row.get('candidate_id'), str)
                or type(row.get('score')) not in {int, float}
                or not math.isfinite(row['score'])
                or row.get('source_mode') not in {'live','replay'}):
            raise ValueError('Unapproved candidate fields or score')
        common={**provenance,'rank_policy':artifact.get('rank_policy')}
        if any(row[key]!=common[key] for key in PROVENANCE_FIELDS-{'source_mode'}
               if key in row and key in common):
            raise ValueError('Candidate provenance differs from its common score artifact')
    # Original live provenance remains live when all cached rows are replayed.
    # Mixed fresh/cached rows require a live envelope; fixtures are never real.
    has_live_rows=any(row['source_mode']=='live' for row in rows)
    if (artifact['source_mode']!=('live' if has_live_rows else 'replay')
            or (has_live_rows and provenance['source_mode']!='live')):
        raise ValueError('Score artifact source modes conflict')
    return sorted(rows, key=lambda row: (-row['score'], row['candidate_id']))


def export_replay(source, destination):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError('Replay export cannot replace its source')
    if destination.exists():
        raise ValueError('Replay destination already exists; refusing overwrite')
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 2_000_000:
        raise ValueError('Expected an explicit local report file no larger than 2 MB')
    raw = source.read_bytes()
    document = json.loads(raw.decode('utf-8'))
    report = document
    if isinstance(document, dict) and 'content' in document and 'artifact_id' in document:
        report = document['content']
        if canonical_hash(report) != document['artifact_id']:
            raise ValueError('Source report envelope checksum mismatch')
    if (not isinstance(report, dict) or report.get('workflow') != 'sequence_review'
            or report.get('status') != 'sequence_review_complete'
            or report.get('source_mode') not in {'live', 'replay'}
            or report.get('scientific_scope') != 'unvalidated_sequence_evidence_assistant'
            or report.get('biological_efficacy_established') is not False):
        raise ValueError('Expected a completed real sequence-only review')
    artifacts = report.get('score_artifacts')
    if not isinstance(artifacts, list) or len(artifacts) != 1:
        raise ValueError('Exactly one original score artifact is required')
    ranked = verify_artifact(artifacts[0])
    meta_mode=report.get('meta_source_mode',report['source_mode'])
    esm_mode=report.get('esm_source_mode',artifacts[0]['source_mode'])
    if (meta_mode!=report['source_mode'] or esm_mode not in {'live','replay'}
            or (esm_mode!=artifacts[0]['source_mode']
                and not (esm_mode=='replay' and report.get('scores_reused_from_saved_artifact') is True))
            or report.get('ranking_scope')!=artifacts[0].get('rank_policy')):
        raise ValueError('Report source modes or ranking conflict with the saved evidence')
    if report.get('candidates') != ranked:
        raise ValueError('Candidate ranks differ from the original score artifact')
    exported = selected(report, REPORT_FIELDS)
    exported.update(source_mode='replay', meta_source_mode='replay', esm_source_mode='replay',
        scores_reused_from_saved_artifact=True, candidates=ranked, score_artifacts=artifacts)
    exported['usage'] = [selected(item, TOKEN_FIELDS) for item in report.get('usage', [])]
    exported['reasoning_effort'] = selected(report.get('reasoning_effort', {}),
                                           {'tool_stage', 'final_report'})
    exported['trace'] = []
    for event in report.get('trace', []):
        clean = selected(event, TRACE_FIELDS)
        for name, fields in [('usage', TOKEN_FIELDS), ('arguments', ARGUMENT_FIELDS),
                             ('result', RESULT_FIELDS)]:
            if name in event:
                clean[name] = selected(event[name], fields)
        exported['trace'].append(clean)
    exported['replay_export'] = {
        'export_date_kst': datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat(),
        'source_file_sha256': hashlib.sha256(raw).hexdigest(),
        'source_content_sha256': canonical_hash(report),
        'source_run_id': report.get('run_id'),
        'source_score_artifact_sha256': artifacts[0]['artifact_sha256'],
        'original_source_modes': {key: report.get(key) for key in
                                 ('source_mode', 'meta_source_mode', 'esm_source_mode')},
        'score_artifact_preserved_unchanged': True,
        'note': 'Playback of a saved real run. Inner source modes describe the original '
                'computation. This export performs no Meta calls or ESM inference.'}
    encoded = json.dumps(exported, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='utf-8') as handle:
        handle.write(encoded)
    return exported['replay_export']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    args = parser.parse_args()
    try:
        receipt = export_replay(args.source, args.destination)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f'Replay export blocked: {error}\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
