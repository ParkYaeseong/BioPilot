"""Offline replay exports preserve scientific evidence and never look live."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXPORTER = ROOT / 'checks' / 'export_demo_replay.py'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def source_report():
    rows = [{'candidate_id': 'A32E', 'score': -1.25, 'full_position': 32,
             'wild_type': 'A', 'mutant': 'E', 'rank_policy': 'esm150_masked_v1',
             'score_kind': 'masked_marginal_log_likelihood_ratio', 'source_mode': 'live'}]
    artifact = {'source_mode': 'live', 'rows': rows, 'rank_policy': 'esm150_masked_v1',
                'provenance': {'checkpoint': 'esm2_t30_150M_UR50D',
                               'sequence_context': 'full_212', 'source_mode': 'live'},
                'score_units': 'dimensionless', 'phenotype_calibrated': False,
                'cached_positions_1based': [], 'limitations': ['Sequence preferences only.']}
    artifact['artifact_sha256'] = digest(artifact)
    return {'run_id': 'original-run', 'workflow': 'sequence_review',
            'status': 'sequence_review_complete', 'source_mode': 'live',
            'meta_source_mode': 'live', 'esm_source_mode': 'live',
            'provider': 'Meta Model API', 'requested_model': 'muse-spark-1.3',
            'actual_model': 'muse-spark-1.3', 'meta_request_attempts': 3,
            'ranking_scope': 'esm150_masked_v1',
            'scientific_scope': 'unvalidated_sequence_evidence_assistant',
            'biological_efficacy_established': False, 'actual_cost_micros': None,
            'cost_status': 'unknown', 'candidates': rows, 'score_artifacts': [artifact],
            'trace': [{'event': 'mcp_tool', 'tool': 'score_positions',
                       'arguments': {'positions_1based': [32]},
                       'result': {'status': 'completed',
                                  'artifact_sha256': artifact['artifact_sha256']}}]}


def run_export(source, destination):
    return subprocess.run([sys.executable, str(EXPORTER), '--source', str(source),
                           '--destination', str(destination)], cwd=ROOT,
                          capture_output=True, text=True, encoding='utf-8', timeout=30)


def write_source(tmp_path, report=None):
    path = tmp_path / 'original.json'
    path.write_text(json.dumps(report or source_report(), indent=2), encoding='utf-8')
    return path


def test_export_marks_playback_and_preserves_original_evidence(tmp_path):
    source = write_source(tmp_path)
    original = source.read_bytes()
    destination = tmp_path / 'replay.json'
    result = run_export(source, destination)
    assert result.returncode == 0, result.stderr
    replay = json.loads(destination.read_text(encoding='utf-8'))
    assert all(replay[field] == 'replay' for field in
               ('source_mode', 'meta_source_mode', 'esm_source_mode'))
    assert replay['scores_reused_from_saved_artifact'] is True
    assert replay['score_artifacts'] == source_report()['score_artifacts']
    assert replay['candidates'] == source_report()['candidates']
    lineage = replay['replay_export']
    assert lineage['source_file_sha256'] == hashlib.sha256(original).hexdigest()
    assert lineage['source_content_sha256'] == digest(json.loads(original))
    assert lineage['source_run_id'] == 'original-run'
    assert lineage['source_score_artifact_sha256'] == source_report()['score_artifacts'][0]['artifact_sha256']
    assert lineage['original_source_modes'] == {
        'source_mode': 'live', 'meta_source_mode': 'live', 'esm_source_mode': 'live'}
    assert lineage['export_date_kst'] == datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat()
    assert source.read_bytes() == original


def test_export_omits_unapproved_fields_and_nested_trace_secrets(tmp_path):
    report = source_report()
    report.update(artifact_path='C:\\private\\artifact.json', api_key='secret-marker',
                  evaluator_labels=[46.0], private_reasoning='secret-marker')
    report['trace'][0].update(authorization='secret-marker', reasoning_content='secret-marker')
    report['trace'][0]['arguments']['api_key'] = 'secret-marker'
    report['trace'][0]['result']['credentials'] = 'secret-marker'
    source = write_source(tmp_path, report)
    destination = tmp_path / 'replay.json'
    result = run_export(source, destination)
    assert result.returncode == 0, result.stderr
    encoded = destination.read_text(encoding='utf-8')
    assert 'secret-marker' not in encoded
    assert 'C:\\\\private' not in encoded
    assert 'evaluator_labels' not in encoded
    assert 'artifact_path' not in encoded


@pytest.mark.parametrize('damage', ['score_hash', 'candidate_rank', 'nested_secret', 'synthetic'])
def test_export_rejects_corrupt_or_nonreal_evidence_before_writing(tmp_path, damage):
    report = source_report()
    if damage == 'score_hash':
        report['score_artifacts'][0]['rows'][0]['score'] = 99
    elif damage == 'candidate_rank':
        report['candidates'] = []
    elif damage == 'nested_secret':
        artifact = report['score_artifacts'][0]
        artifact['provenance']['api_key'] = 'secret-marker'
        artifact['artifact_sha256'] = digest({k: v for k, v in artifact.items() if k != 'artifact_sha256'})
    else:
        report['source_mode'] = 'synthetic_fixture'
    destination = tmp_path / 'replay.json'
    result = run_export(write_source(tmp_path, report), destination)
    assert result.returncode != 0
    assert not destination.exists()


def test_export_refuses_overwrite_and_in_place_update(tmp_path):
    source = write_source(tmp_path)
    destination = tmp_path / 'existing.json'
    destination.write_text('do not replace', encoding='utf-8')
    original = source.read_bytes()
    assert run_export(source, destination).returncode != 0
    assert destination.read_text(encoding='utf-8') == 'do not replace'
    assert run_export(source, source).returncode != 0
    assert source.read_bytes() == original


@pytest.mark.parametrize('damage', [
    'provenance_fixture', 'row_fixture', 'provenance_unknown', 'row_unknown',
    'artifact_mode_conflict', 'meta_fixture', 'esm_fixture', 'meta_mode_conflict',
    'esm_mode_conflict', 'row_rank_policy', 'row_context', 'row_checkpoint',
    'report_rank_policy',
])
def test_export_rejects_conflicting_or_synthetic_provenance(tmp_path,damage):
    report=source_report()
    artifact=report['score_artifacts'][0]
    if damage.startswith('provenance_'):
        artifact['provenance']['source_mode']='synthetic_fixture' if damage.endswith('fixture') else 'unknown'
    elif damage.startswith('row_'):
        field,value={
            'row_fixture':('source_mode','synthetic_fixture'),
            'row_unknown':('source_mode','unknown'),
            'row_rank_policy':('rank_policy','esm650_masked_v1'),
            'row_context':('sequence_context','mature_181'),
            'row_checkpoint':('checkpoint','esm2_t33_650M_UR50D'),
        }[damage]
        artifact['rows'][0][field]=value
    elif damage=='artifact_mode_conflict':
        artifact['source_mode']='replay'
    elif damage=='meta_fixture':
        report['meta_source_mode']='synthetic_fixture'
    elif damage=='esm_fixture':
        report['esm_source_mode']='synthetic_fixture'
    elif damage=='meta_mode_conflict':
        report['meta_source_mode']='replay'
    elif damage=='esm_mode_conflict':
        report['esm_source_mode']='replay'
    else:
        report['ranking_scope']='esm650_masked_v1'
    artifact['artifact_sha256']=digest({k:v for k,v in artifact.items() if k!='artifact_sha256'})
    destination=tmp_path/'replay.json'
    result=run_export(write_source(tmp_path,report),destination)
    assert result.returncode!=0
    assert not destination.exists()


def test_export_accepts_real_cached_scores_without_relabeling_them_live(tmp_path):
    report=source_report()
    artifact=report['score_artifacts'][0]
    report['esm_source_mode']='replay'
    artifact['source_mode']='replay'
    artifact['cached_positions_1based']=[32]
    artifact['rows'][0]['source_mode']='replay'
    artifact['artifact_sha256']=digest({k:v for k,v in artifact.items() if k!='artifact_sha256'})
    destination=tmp_path/'replay.json'
    result=run_export(write_source(tmp_path,report),destination)
    assert result.returncode==0,result.stderr
    replay=json.loads(destination.read_text(encoding='utf-8'))
    assert replay['score_artifacts'][0]['provenance']['source_mode']=='live'
    assert replay['replay_export']['original_source_modes']['meta_source_mode']=='live'
    assert replay['replay_export']['original_source_modes']['esm_source_mode']=='replay'


def test_exported_report_envelope_keeps_raw_and_content_hashes_distinct(tmp_path):
    report = source_report()
    envelope = {'run_id': report['run_id'], 'artifact_id': digest(report), 'content': report}
    source = write_source(tmp_path, envelope)
    destination = tmp_path / 'replay.json'
    result = run_export(source, destination)
    assert result.returncode == 0, result.stderr
    replay = json.loads(destination.read_text(encoding='utf-8'))
    assert replay['replay_export']['source_content_sha256'] == envelope['artifact_id']
    assert replay['replay_export']['source_file_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert replay['score_artifacts'] == report['score_artifacts']
    corrupt = tmp_path / 'corrupt.json'
    envelope['content']['run_id'] = 'changed-after-save'
    corrupt.write_text(json.dumps(envelope), encoding='utf-8')
    rejected = tmp_path / 'rejected.json'
    assert run_export(corrupt, rejected).returncode != 0
    assert not rejected.exists()


def test_exported_real_sample_renders_nineteen_candidates_as_replay(monkeypatch):
    from app.viewer_data import load_run_view
    path = ROOT / 'examples' / 'artifacts' / 'sequence_review.replay.json'
    assert path.is_file(), 'A portable saved real replay must accompany the demo'
    view = load_run_view(path)
    assert view['esm_badge'] == 'REPLAY'
    assert view['scores_reused_from_saved_artifact'] is True
    assert view['candidate_count'] == 19
    assert view['cost_display'] == 'unknown (not verified)'
    assert view['actual_model'] == 'muse-spark-1.3'
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr('sys.argv', ['viewer.py', '--artifact', str(path)])
    app = AppTest.from_file(str(ROOT / 'app' / 'viewer.py'), default_timeout=60).run()
    assert not app.exception
    assert any('REPLAY' in str(item.value) and 'no new inference' in str(item.value)
               for item in app.caption)
    app.session_state['active_view'] = 'Candidates'
    app.run()
    assert not app.exception
    assert len(app.table[0].value) == 5
    app.toggle(key='show_all_candidates').set_value(True).run()
    assert not app.exception
    assert len(app.table[0].value) == 19
    assert any('unknown (not verified)' in str(item.value) for item in app.html)
