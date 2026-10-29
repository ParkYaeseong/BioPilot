"""Actual workbench interactions, without providers or new scientific computation."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / 'demo/artifacts/sequence_review.replay.json'


def app_view(monkeypatch):
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr('sys.argv', ['viewer.py', '--artifact', str(REPLAY)])
    return AppTest.from_file(str(ROOT / 'app/viewer.py'), default_timeout=60).run()


def at_view(app, name):
    """Open one view. The viewer renders only the active view, as the tour drives it."""
    if name in ('Input', 'Input & Diagnostics'):
        app.session_state['evidence_section'] = 'Advanced diagnostics'
        name = 'Evidence'
    app.session_state['active_view'] = name
    return app.run()


def test_example_buttons_execute_real_local_guards_and_preserve_saved_run(monkeypatch):
    before = REPLAY.read_bytes()
    app = app_view(monkeypatch)
    at_view(app, 'Input & Diagnostics')
    keys = {button.key for button in app.button}
    assert {'example_A32V', 'example_S108A', 'example_G32V'} <= keys
    app.button(key='example_S108A').click().run()
    assert not app.exception
    assert app.text_input(key='local_variant').value == 'S108A'
    assert any('Protected catalytic site' in str(e.value) for e in app.error)
    app.button(key='example_G32V').click().run()
    assert any('WT residue mismatch' in str(e.value) for e in app.error)
    app.button(key='example_A32V').click().run()
    assert any('satisfies the registered' in str(e.value) for e in app.success)
    assert REPLAY.read_bytes() == before


def test_compare_top_three_preserves_original_ranks_and_can_clear(monkeypatch):
    before = REPLAY.read_bytes()
    app = app_view(monkeypatch)
    at_view(app, 'Candidates')
    assert 'compare_top_three' in {button.key for button in app.button}
    app.button(key='compare_top_three').click().run()
    assert not app.exception
    assert app.multiselect(key='compare_candidates').value == ['A32E', 'A32S', 'A32D']
    assert app.table[1].value['Rank'].tolist() == [1, 2, 3]
    app.button(key='clear_comparison').click().run()
    assert app.multiselect(key='compare_candidates').value == []
    assert REPLAY.read_bytes() == before


def test_recorded_trace_navigation_moves_only_between_saved_events(monkeypatch):
    before = REPLAY.read_bytes()
    app = app_view(monkeypatch)
    at_view(app, 'Agent Trace')
    assert 'next_trace' in {button.key for button in app.button}
    assert app.selectbox(key='trace_step').value == 0
    assert app.button(key='previous_trace').disabled
    app.button(key='next_trace').click().run()
    assert not app.exception
    assert app.selectbox(key='trace_step').value == 1
    assert app.button(key='next_trace').disabled
    app.button(key='previous_trace').click().run()
    assert app.selectbox(key='trace_step').value == 0
    assert REPLAY.read_bytes() == before


def test_editing_input_does_not_relabel_the_last_checked_request(monkeypatch):
    app = app_view(monkeypatch)
    at_view(app, 'Input & Diagnostics')
    app.button(key='FormSubmitter:offline_check-Check input locally').click().run()
    assert any('Last checked: A32V' in str(e.value) for e in app.caption)
    app.text_input(key='local_variant').set_value('S108A').run()
    assert any('Last checked: A32V' in str(e.value) for e in app.caption)


def test_decision_trace_shows_model_turns_and_code_turns_in_saved_order(monkeypatch):
    """The division of labour is the product claim; both actors must be visible."""
    before = REPLAY.read_bytes()
    app = app_view(monkeypatch)
    assert not app.exception
    at_view(app, 'Agent Trace')
    assert any('Recorded handoffs' in str(block.value) for block in app.markdown)
    rendered = ' '.join(str(block.value) for block in app.html)
    assert 'muse-spark-1.3' in rendered
    assert 'validate_target_context' in rendered and 'score_positions' in rendered
    # The model asks before the registered code computes.
    assert rendered.index('muse-spark-1.3') < rendered.index('validate_target_context')
    # Public accounting only: the reply length is shown, never reply text.
    assert '84-char reply' in rendered
    assert REPLAY.read_bytes() == before


def test_structure_evidence_refuses_to_fake_an_unmodelled_position(monkeypatch):
    """Selecting a saved candidate must report absence, not approximate a neighbour."""
    before = REPLAY.read_bytes()
    app = app_view(monkeypatch)
    assert not app.exception
    at_view(app, 'Structure')
    focus = app.selectbox(key='structure_focus')
    # Every saved candidate is A32X, and full 32 carries no atoms in 1ISP.
    assert focus.options[0].startswith('A32')
    assert any('protected' in option for option in focus.options)
    assert any('not modelled' in str(block.value).lower() for block in app.warning)
    assert not any('author residue' in str(block.value) for block in app.success)
    # A protected residue resolves through the registered join to real author numbering.
    protected = [option for option in focus.options if option.startswith('S108')][0]
    focus.set_value(protected).run()
    assert not app.exception
    assert any('author residue 77' in str(block.value) for block in app.success)
    assert REPLAY.read_bytes() == before


def test_guided_tour_moves_the_screen_rather_than_only_numbering_steps(monkeypatch):
    """Next must open the view it names, not just advance a counter."""
    before = REPLAY.read_bytes()
    app = app_view(monkeypatch)
    assert not app.exception
    at_view(app, 'Candidates')
    app.multiselect(key='compare_candidates').set_value(['A32V']).run()
    at_view(app, 'Overview')
    assert app.session_state['active_view'] == 'Overview'
    app.button(key='start_demo').click().run()
    assert app.session_state['active_view'] == 'Overview'
    assert app.session_state['tour_step'] == 0
    assert app.table[0].value['Variant'].tolist() == ['A32E', 'A32S', 'A32D']
    assert REPLAY.read_bytes() == before

    app.button(key='tour_next').click().run()
    assert app.session_state['active_view'] == 'Agent Trace'
    assert app.selectbox(key='trace_step').value == 0
    app.button(key='tour_next').click().run()
    assert app.selectbox(key='trace_step').value == 1
    app.button(key='tour_next').click().run()
    assert app.session_state['active_view'] == 'Candidates'
    assert app.multiselect(key='compare_candidates').value == ['A32E', 'A32S', 'A32D']
    assert app.table[1].value['Rank'].tolist() == [1, 2, 3]

    app.button(key='tour_next').click().run()
    assert app.session_state['active_view'] == 'Evidence'
    assert app.session_state['evidence_section'] == 'Run provenance'
    app.button(key='tour_next').click().run()
    assert app.session_state['active_view'] == 'Structure'
    assert app.selectbox(key='structure_focus').value.startswith('A32')
    assert any('not modelled' in str(block.value).lower() for block in app.warning)
    app.button(key='tour_next').click().run()
    assert app.selectbox(key='structure_focus').value == 'S108 · protected'
    assert any('author residue 77' in str(block.value) for block in app.success)

    app.button(key='tour_next').click().run()
    assert app.session_state['active_view'] == 'Evidence'
    assert app.text_input(key='local_variant').value == 'A32V'
    assert app.session_state['local_check_result']['status'] == 'accepted'
    assert app.session_state['local_check_result']['inference_performed'] is False
    app.button(key='tour_next').click().run()
    assert app.session_state['active_view'] == 'Evidence'
    assert app.text_input(key='local_variant').value == 'S108A'
    assert app.session_state['local_check_result']['status'] == 'blocked'
    assert any('Protected catalytic site' in str(block.value) for block in app.error)
    assert app.button(key='tour_next').disabled

    # Back really revisits A32V; exiting restores the user's pre-tour selection.
    app.button(key='tour_back').click().run()
    assert app.text_input(key='local_variant').value == 'A32V'
    assert app.session_state['local_check_result']['status'] == 'accepted'
    app.button(key='exit_demo').click().run()
    assert not app.exception
    assert not app.session_state['tour_active']
    assert app.session_state['active_view'] == 'Overview'
    assert app.session_state['compare_candidates'] == ['A32V']
    at_view(app, 'Candidates')
    assert app.multiselect(key='compare_candidates').value == ['A32V']
    assert REPLAY.read_bytes() == before
