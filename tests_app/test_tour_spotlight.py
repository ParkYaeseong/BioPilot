"""The tutorial points at real widgets and never owns live authority."""
from app.guided_tour import STEPS


def test_every_step_has_a_real_focus_target_and_korean_instructions():
    from app.tour_spotlight import spotlight_document, TARGETS
    assert set(TARGETS) == {step.id for step in STEPS}
    html = spotlight_document(0, appearance='Light', playing=False)
    assert 'tour_input' in html
    assert '배경' in html or '입력' in html
    assert 'bio-tour-root' in html
    assert 'getBoundingClientRect' in html
    assert 'Escape' in html
    assert 'tour_next' in html and 'exit_demo' in html
    assert 'fetch(' not in html and 'XMLHttpRequest' not in html
    assert 'armed' not in html
    for index in range(len(STEPS)):
        assert 'data:image/png;base64,' in spotlight_document(index)


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
