"""Ordered input and acting demo without dispatching scientific work."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / 'examples/artifacts/sequence_review.replay.json'


def viewer(monkeypatch):
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr('sys.argv', ['viewer.py', '--artifact', str(REPLAY)])
    return AppTest.from_file(str(ROOT / 'app/viewer.py'), default_timeout=60).run()


def test_tour_reviews_results_before_local_checks_then_restores_user_selection(monkeypatch):
    app = viewer(monkeypatch)
    app.session_state['active_view'] = 'Candidates'
    app.run()
    app.multiselect(key='compare_candidates').set_value(['A32V']).run()
    app.button(key='start_demo').click().run()
    assert not app.exception
    assert app.session_state['active_view'] == 'Overview'
    assert not app.text_input
    for _ in range(7):
        app.button(key='tour_next').click().run()
        assert not app.exception
    assert app.session_state['active_view'] == 'Evidence'
    assert app.text_input(key='local_variant').value == 'A32V'
    assert app.session_state['local_check_result']['status'] == 'accepted'
    app.button(key='tour_next').click().run()
    assert app.text_input(key='local_variant').value == 'S108A'
    assert app.error
    app.button(key='exit_demo').click().run()
    assert not app.exception
    assert app.session_state['active_view'] == 'Candidates'
    assert app.multiselect(key='compare_candidates').value == ['A32V']


def test_diagnostics_are_local_and_live_navigation_is_only_a_link(monkeypatch):
    app = viewer(monkeypatch)
    app.session_state['active_view'] = 'Evidence'
    app.session_state['evidence_section'] = 'Advanced diagnostics'
    app.run()
    assert not app.exception
    assert app.text_input(key='local_variant')
    assert not any(b.key == 'local_variant' for b in app.sidebar.text_input)
    rendered = ' '.join(str(e.value) for e in app.html)
    assert 'http://127.0.0.1:8521' in rendered
    assert 'New Review' in rendered
    assert 'Structure' not in [x.label for x in app.get('file_uploader')]


def test_live_session_has_light_appearance_and_examples_only_fill_a_draft(monkeypatch):
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr('sys.argv', ['session.py'])
    app = AppTest.from_file(str(ROOT / 'app/session.py'), default_timeout=60).run()
    app.selectbox(key='appearance').set_value('Light').run()
    assert not app.exception
    assert app.checkbox(key='armed').value is False
    app.button(key='draft_valid').click().run()
    assert not app.exception
    assert not app.session_state.get('turns')
    assert app.chat_input[0].value == 'Review A32V for sequence plausibility.'
