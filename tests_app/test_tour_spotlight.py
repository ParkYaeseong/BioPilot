"""The tutorial points at real widgets and never owns live authority."""
import re

from app.guided_tour import STEPS


def test_every_step_has_a_real_focus_target_and_english_instructions():
    from app.tour_spotlight import spotlight_document, TARGETS
    assert set(TARGETS) == {step.id for step in STEPS}
    html = spotlight_document(0, appearance='Light', playing=False)
    assert 'tour_overview' in html
    assert 'Understand the saved review' in html
    assert 'bio-tour-root' in html
    assert 'getBoundingClientRect' in html
    assert 'Escape' in html
    assert 'tour_next' in html and 'exit_demo' in html
    assert 'fetch(' not in html and 'XMLHttpRequest' not in html
    assert 'armed' not in html
    for appearance in ('Light', 'Dark'):
        for index in range(len(STEPS)):
            html = spotlight_document(index, appearance=appearance)
            assert 'data:image/png;base64,' in html
            assert not re.search(r'[\uac00-\ud7a3]', html)
            assert 'Guided tutorial' in html
            assert 'Close tutorial' in html
            assert 'Skip' in html and 'Back' in html
            assert 'Finish' in html and 'Next' in html


def test_inactive_render_removes_the_previous_overlay():
    from app.tour_spotlight import spotlight_document
    html = spotlight_document(None)
    assert 'bio-tour-root' in html
    assert '.remove()' in html
    assert 'createElement' not in html


def test_tutorial_uses_manual_steps_by_default_in_the_real_app(monkeypatch):
    from tests_app.test_workspace_flow import viewer
    app = viewer(monkeypatch)
    app.button(key='start_demo').click().run()
    assert not app.exception
    assert app.session_state['tour_active'] is True
    assert app.session_state['tour_playing'] is False
