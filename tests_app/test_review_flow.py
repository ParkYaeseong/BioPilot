import pytest


def test_saved_review_navigation_is_not_a_numbered_workflow():
    from app.viewer import VIEWS, VIEW_LABELS
    assert VIEWS == ('Overview', 'Candidates', 'Agent Trace', 'Evidence')
    assert all(VIEW_LABELS[name] == name for name in VIEWS)


def test_confirmation_is_required_and_can_only_be_consumed_once():
    from app.review_flow import prepare_review, consume_review
    from app.session_exec import SessionBudget
    state = {'pending_review': prepare_review('Review A32V', 'esm150'), 'review_phase': 'validated'}
    budget = SessionBudget()
    with pytest.raises(ValueError):
        consume_review(state, armed=False, model_key='esm150', budget=budget)
    assert state['pending_review']
    consume_review(state, armed=True, model_key='esm150', budget=budget)
    assert state['pending_review'] is None and state['review_phase'] == 'running'
    with pytest.raises(ValueError):
        consume_review(state, armed=True, model_key='esm150', budget=budget)


def test_guards_and_result_states_are_preserved():
    from app.review_flow import prepare_review, result_phase
    for text in ('Review S108A', 'Review G32V', 'mature position 32'):
        with pytest.raises(ValueError):
            prepare_review(text, 'esm150')
    assert [result_phase(s) for s in ('sequence_review_complete', 'partial', 'failed')] == ['completed', 'partial', 'failed']
