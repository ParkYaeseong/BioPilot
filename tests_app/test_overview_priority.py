"""The saved result explains its purpose before offering local diagnostics."""
from app.viewer_data import format_candidate_rows, load_run_view
from tests_app.test_workspace_flow import REPLAY, viewer


def test_landing_view_explains_the_saved_evidence_without_input_controls(monkeypatch):
    app = viewer(monkeypatch)
    assert not app.exception
    assert app.session_state['active_view'] == 'Overview'
    assert 'Review the saved evidence' in [item.value for item in app.subheader]
    text = ' '.join(str(item.value) for item in app.html)
    assert 'Research purpose' in text
    assert 'sequence plausibility' in text
    assert '19' in text and 'full_212' in text and 'muse-spark-1.3' in text
    assert 'Not established' in text and 'T50' in text
    assert not app.text_input
    assert not app.get('file_uploader')


def test_overview_numbers_come_from_the_unchanged_saved_rows(monkeypatch):
    before = REPLAY.read_bytes()
    app = viewer(monkeypatch)
    expected = format_candidate_rows(load_run_view(REPLAY)['candidates'])[:3]
    assert app.table[0].value['Variant'].tolist() == [r['candidate_id'] for r in expected]
    assert app.table[0].value['ESM preference'].tolist() == [r['score'] for r in expected]
    assert REPLAY.read_bytes() == before


def test_navigation_keeps_diagnostics_outside_the_four_result_views(monkeypatch):
    app = viewer(monkeypatch)
    assert 'workflow_next' not in {b.key for b in app.button}
    for name in ('Overview', 'Candidates', 'Agent Trace', 'Evidence'):
        app.session_state['active_view'] = name
        app.run()
        assert not app.exception
        assert not app.get('file_uploader')
    app.session_state['evidence_section'] = 'Advanced diagnostics'
    app.run()
    assert {'upload_fasta', 'upload_cif', 'upload_cif_fasta'} == {i.key for i in app.get('file_uploader')}


def test_structure_evidence_is_scoped_and_remains_separate_from_diagnostics(monkeypatch):
    app = viewer(monkeypatch)
    app.session_state['active_view'] = 'Structure'
    app.run()
    assert not app.exception
    assert 'Reference structure' in [item.value for item in app.subheader]
    assert app.selectbox(key='structure_focus')
    assert not app.get('file_uploader')
    assert any('atom geometry unvalidated' in str(item.value) for item in app.caption)


def test_overview_does_not_invent_the_unrecorded_original_objective(monkeypatch):
    app = viewer(monkeypatch)
    assert not app.exception
    assert any('Unavailable in this saved report' in str(item.value) for item in app.text)
    text = ' '.join(str(item.value) for item in app.html)
    assert 'current review scope' in text
