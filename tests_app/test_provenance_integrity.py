"""Saved bytes are locally checkable; recorded input hashes are not source authentication."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from app.viewer_data import load_run_view, provenance_chain


REPLAY = Path(__file__).resolve().parents[1] / 'demo/artifacts/sequence_review.replay.json'


@pytest.fixture
def replay():
    return json.loads(REPLAY.read_text(encoding='utf-8'))


def stage(record, name):
    return next(link for link in provenance_chain(record, 'f' * 64) if link['stage'] == name)


def reseal_score(record):
    """Model an internally rewritten file; it still has no external authenticity."""
    score = record['score_artifacts'][0]
    payload = {key: value for key, value in score.items() if key != 'artifact_sha256'}
    score['artifact_sha256'] = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def test_modified_score_payload_is_detected_without_rewriting_its_digest(replay):
    replay['score_artifacts'][0]['rows'][0]['score'] = 999.0
    score = stage(replay, 'score_artifact')
    assert score['link_verified'] is False
    assert score['mismatch'] is True
    assert score['detail']['computed_sha256'] != score['digest']


def test_modified_input_commitment_breaks_the_score_payload_checksum(replay):
    replay['score_artifacts'][0]['provenance']['reference_sha256'] = 'a' * 64
    assert stage(replay, 'score_artifact')['mismatch'] is True


def test_displayed_candidate_numbers_are_checked_against_committed_score_rows(replay):
    replay['candidates'][0]['score'] = 999.0
    score = stage(replay, 'score_artifact')
    assert score['link_verified'] is False
    assert score['mismatch'] is True
    assert score['detail']['candidate_rows_match'] is False


def test_displayed_rank_changes_are_detected_against_common_saved_ranking(replay):
    replay['candidates'][0], replay['candidates'][1] = replay['candidates'][1], replay['candidates'][0]
    assert stage(replay, 'score_artifact')['mismatch'] is True


@pytest.mark.parametrize('damage', ['missing', 'non_hex'])
def test_incomplete_input_hashes_stay_unverified_even_if_score_is_resealed(replay, damage):
    provenance = replay['score_artifacts'][0]['provenance']
    if damage == 'missing':
        del provenance['weights_sha256']
    else:
        provenance['weights_sha256'] = 'z' * 64
    reseal_score(replay)
    inputs = stage(replay, 'model_inputs')
    assert inputs['link_verified'] is False
    assert inputs['absent'] is True
    assert inputs['status'] == 'missing'


def test_input_files_are_not_declared_verified_from_their_recorded_hash_strings(replay):
    inputs = stage(replay, 'model_inputs')
    assert inputs['link_verified'] is False
    assert inputs['status'] == 'recorded only'
    assert inputs['check_scope'] == 'input_files_not_opened'


def test_checksum_and_candidate_rows_are_verified_for_the_unchanged_saved_score(replay):
    score = stage(replay, 'score_artifact')
    assert score['link_verified'] is True
    assert score['status'] == 'local checksum match'
    assert score['detail']['computed_sha256'] == '63a1c3752407d96a54f33b735d72e700839e4b0e9363894597738f6e8531157f'
    assert score['detail']['candidate_rows_match'] is True


def test_unrelated_trace_artifact_is_not_mistaken_for_the_scoring_tool_result(replay):
    replay['trace'].insert(0, {'event': 'mcp_tool', 'tool': 'retrieve_atlas_evidence',
                             'result': {'artifact_sha256': 'a' * 64}})
    trace = stage(replay, 'recorded_tool_result')
    assert trace['mismatch'] is False
    assert trace['link_verified'] is True


def test_missing_score_tool_digest_is_not_verified(replay):
    for event in replay['trace']:
        if event.get('tool') == 'score_positions':
            event['result'].pop('artifact_sha256', None)
    trace = stage(replay, 'recorded_tool_result')
    assert trace['absent'] is True
    assert trace['link_verified'] is False


def test_original_export_source_bytes_are_recorded_only_not_verified(replay):
    export = stage(replay, 'replay_export')
    assert export['link_verified'] is False
    assert export['status'] == 'recorded only'
    assert export['detail']['score_digest_matches'] is True
    assert export['check_scope'] == 'source_bytes_not_opened'


def test_missing_export_source_digest_is_not_treated_as_a_complete_stage(replay):
    del replay['replay_export']['source_content_sha256']
    export = stage(replay, 'replay_export')
    assert export['absent'] is True
    assert export['link_verified'] is False


def test_export_score_digest_disagreement_remains_an_explicit_mismatch(replay):
    replay['replay_export']['source_score_artifact_sha256'] = 'a' * 64
    export = stage(replay, 'replay_export')
    assert export['mismatch'] is True
    assert export['link_verified'] is False


def test_opened_file_hash_does_not_invent_an_upstream_link(replay):
    opened = stage(replay, 'opened_file')
    assert opened['digest'] == 'f' * 64
    assert opened['carries_upstream_digest'] is None
    assert opened['link_verified'] is False
    assert opened['status'] == 'computed locally'


def test_nonfinite_corruption_is_reported_without_a_hashing_crash(replay):
    replay['score_artifacts'][0]['rows'][0]['score'] = float('nan')
    score = stage(replay, 'score_artifact')
    assert score['mismatch'] is True
    assert score['link_verified'] is False


def test_corrupt_artifact_store_envelope_is_rejected_before_display(tmp_path, replay):
    content_hash = hashlib.sha256(json.dumps(
        replay, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    envelope = {'artifact_id': content_hash, 'content': copy.deepcopy(replay)}
    envelope['content']['candidates'][0]['score'] = 999.0
    path = tmp_path / 'corrupt-envelope.json'
    path.write_text(json.dumps(envelope), encoding='utf-8')
    with pytest.raises(ValueError, match='envelope|checksum'):
        load_run_view(path)


def test_corrupt_display_numbers_are_not_classified_as_scientific_evidence(tmp_path, replay):
    replay['candidates'][0]['score'] = 999.0
    path = tmp_path / 'corrupt-report.json'
    path.write_text(json.dumps(replay), encoding='utf-8')
    view = load_run_view(path)
    assert view['is_scientific_evidence'] is False
    assert view['integrity_status'] == 'mismatch'


def test_unchanged_record_reports_local_consistency_without_external_authenticity():
    view = load_run_view(REPLAY)
    assert view['integrity_status'] == 'locally_consistent'
    assert view['external_authenticity_verified'] is False
