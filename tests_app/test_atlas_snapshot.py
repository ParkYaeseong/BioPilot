"""MCP sees only a fixed sanitized WT snapshot, never the live Atlas API."""
import json
from pathlib import Path

import pytest

from app.core.atlas_snapshot import load_registered_atlas_snapshot
from app.core.runtime_bundle import build_runtime_bundle
from app.core.targets import REFERENCE_ID
from app.core.tool_executor import ToolExecutor
from tests_app.test_mcp_roundtrip import make_context

ROOT = Path(__file__).resolve().parents[1]


def test_enabled_pinned_atlas_is_offered_and_bound_to_one_reference(tmp_path):
    executor = ToolExecutor(make_context(tmp_path))
    assert 'retrieve_atlas_evidence' in {x['name'] for x in executor.list_tools()}
    result = executor.dispatch('retrieve_atlas_evidence', {
        'reference_id': REFERENCE_ID, 'max_hits': 1, 'reason_brief': 'Inspect independent WT context'})
    assert result['status'] == 'ok'
    assert result['source_mode'] == 'imported_snapshot'
    assert result['snapshot_integrity_verified'] is True
    assert result['upstream_authenticity_verified'] is False
    assert result['query_scope'] == 'exact_registered_wt_only'
    assert result['hits'][0]['accession'] == '2702335490'
    assert result['hits'][0]['structure_confidence'] == {'ptm': None, 'mean_plddt': None}
    assert result['baseline_rank_changed'] is False
    assert 'sequence' not in result['hits'][0]
    assert executor.dispatch('get_run_status', {})['capabilities']['atlas'] is True


@pytest.mark.parametrize('arguments', [
    {'reference_id': 'private', 'max_hits': 1, 'reason_brief': 'x'},
    {'reference_id': REFERENCE_ID, 'max_hits': 0, 'reason_brief': 'x'},
    {'reference_id': REFERENCE_ID, 'max_hits': 1, 'reason_brief': 'x', 'url': 'https://evil.test'},
    {'reference_id': REFERENCE_ID, 'max_hits': 1, 'reason_brief': 'x', 'path': '../evaluation_private'},
])
def test_atlas_arguments_cannot_change_reference_or_source(tmp_path, arguments):
    assert ToolExecutor(make_context(tmp_path)).dispatch('retrieve_atlas_evidence', arguments)['status'] == 'blocked'


def test_disabled_or_tampered_snapshot_is_not_a_capability(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    reference = source / 'reference'
    reference.mkdir(parents=True)
    for name in ('atlas_snapshot_policy.json', 'atlas_registered_reference_20261028.json'):
        (reference / name).write_bytes((ROOT / 'reference' / name).read_bytes())
    snapshot = reference / 'atlas_registered_reference_20261028.json'
    snapshot.write_text(snapshot.read_text() + ' ')
    with pytest.raises(ValueError, match='hash'):
        load_registered_atlas_snapshot(source)
    import app.core.tool_executor as module
    monkeypatch.setattr(module, 'load_registered_atlas_snapshot', lambda: load_registered_atlas_snapshot(source))
    executor = ToolExecutor(make_context(tmp_path))
    assert 'retrieve_atlas_evidence' not in {x['name'] for x in executor.list_tools()}
    assert executor.dispatch('get_run_status', {})['capabilities']['atlas'] is False
    assert executor.dispatch('retrieve_atlas_evidence', {
        'reference_id': REFERENCE_ID, 'max_hits': 1, 'reason_brief': 'x'})['status'] == 'blocked'


def test_runtime_bundle_has_sanitized_context_and_no_network_atlas_client(tmp_path):
    destination = tmp_path / 'runtime'
    build_runtime_bundle(ROOT, destination)
    assert load_registered_atlas_snapshot(destination)['status'] == 'available'
    assert not (destination / 'app/science/atlas_context.py').exists()
    assert not (destination / 'app/science/optional_worker.py').exists()
    raw = (destination / 'reference/atlas_registered_reference_20261028.json').read_text()
    assert 'raw_text_exposed' in raw
    assert 'sae_features' not in raw and 'header' not in raw and 'experimental T50' not in raw


def test_disabling_atlas_keeps_the_other_product_runtime_buildable(tmp_path):
    source = tmp_path / 'source'
    build_runtime_bundle(ROOT, source)
    policy = source / 'reference/atlas_snapshot_policy.json'
    data = json.loads(policy.read_text())
    data['enabled'] = False
    policy.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='disabled'):
        load_registered_atlas_snapshot(source)
    build_runtime_bundle(source, tmp_path / 'disabled_runtime')
