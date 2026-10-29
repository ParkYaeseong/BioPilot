"""The walkthrough operates real local controls, preserves work, and never arms runs."""
from copy import deepcopy

import pytest

from app.guided_tour import (
    STEPS, advance_tour, set_tour_playing, start_tour, stop_tour, tick_tour,
)


CANDIDATES = [
    {'candidate_id': 'A32E', 'full_position': 32},
    {'candidate_id': 'A32S', 'full_position': 32},
    {'candidate_id': 'A32V', 'full_position': 32},
    {'candidate_id': 'A32D', 'full_position': 32},
]


def test_start_shows_the_saved_overview_without_touching_input_or_paid_controls():
    state = {'armed': True, 'session_budget': object(), 'model_key': 'esm650'}
    original_budget = state['session_budget']
    start_tour(state, CANDIDATES, now=10)
    assert 'local_variant' not in state
    assert 'local_check_result' not in state
    assert state['active_view'] == 'Overview'
    assert state['armed'] is True
    assert state['session_budget'] is original_budget
    assert state['model_key'] == 'esm650'
    assert state['tour_playing'] is False
    assert state['tour_source_mode'] == 'REPLAY'


def test_progression_changes_input_shortlist_structure_and_trace_controls():
    state = {}
    saved_candidates = deepcopy(CANDIDATES)
    start_tour(state, CANDIDATES, now=0, autoplay=False)
    advance_tour(state, CANDIDATES, now=1)
    assert state['active_view'] == 'Candidates'
    assert state['compare_candidates'] == ['A32E', 'A32S', 'A32V']
    advance_tour(state, CANDIDATES, now=2)
    assert state['active_view'] == 'Agent Trace'
    assert state['trace_step'] == 0
    advance_tour(state, CANDIDATES, now=3)
    assert state['trace_step'] == 1
    advance_tour(state, CANDIDATES, now=4)
    assert state['active_view'] == 'Evidence'
    assert state['evidence_section'] == 'Run provenance'
    advance_tour(state, CANDIDATES, now=5)
    assert state['active_view'] == 'Evidence'
    assert state['evidence_section'] == 'Reference mapping & saved structures'
    assert state['structure_focus'] == 'A32E · full 32'
    advance_tour(state, CANDIDATES, now=6)
    assert state['structure_focus'] == 'S108 · protected'
    advance_tour(state, CANDIDATES, now=7)
    assert state['active_view'] == 'Input & Diagnostics'
    assert state['local_variant'] == 'A32V'
    assert state['local_check_result']['status'] == 'accepted'
    assert state['local_check_result']['inference_performed'] is False
    assert state['local_check_result']['saved_run_modified'] is False
    advance_tour(state, CANDIDATES, now=8)
    assert state['local_variant'] == 'S108A'
    assert state['local_check_result']['status'] == 'blocked'
    assert 'Protected catalytic site' in state['local_check_result']['message']
    assert state['tour_step'] == len(STEPS) - 1
    assert CANDIDATES == saved_candidates


def test_tour_follows_the_submission_story_instead_of_beginning_with_diagnostics():
    assert [step.id for step in STEPS] == [
        'overview', 'compare', 'validation_trace', 'scoring_trace', 'provenance',
        'unmodelled_position', 'protected_structure', 'valid_input', 'protected_input',
    ]


def test_timer_has_no_effect_when_idle_and_advances_one_visible_step_per_tick():
    state = {}
    assert tick_tour(state, CANDIDATES, now=99) is False
    start_tour(state, CANDIDATES, now=10, autoplay=True)
    deadline = state['tour_next_at']
    assert tick_tour(state, CANDIDATES, now=deadline - 0.01) is False
    assert tick_tour(state, CANDIDATES, now=deadline + 100) is True
    assert state['tour_step'] == 1
    assert state['tour_next_at'] > deadline + 100


def test_pause_freezes_playback_and_resume_waits_a_full_step():
    state = {}
    start_tour(state, CANDIDATES, now=0, autoplay=True)
    set_tour_playing(state, False, now=1)
    assert tick_tour(state, CANDIDATES, now=100) is False
    assert state['tour_step'] == 0
    assert state['tour_next_at'] is None
    set_tour_playing(state, True, now=100)
    assert state['tour_next_at'] > 100
    assert tick_tour(state, CANDIDATES, now=100) is False


def test_back_and_forward_clamp_and_finish_does_not_loop():
    state = {}
    start_tour(state, CANDIDATES, now=0, autoplay=True)
    advance_tour(state, CANDIDATES, now=1, delta=-1)
    assert state['tour_step'] == 0
    for number in range(1, len(STEPS)):
        assert tick_tour(state, CANDIDATES, now=number * 100) is True
    assert state['tour_step'] == len(STEPS) - 1
    assert tick_tour(state, CANDIDATES, now=9999) is True
    assert state['tour_complete'] is True
    assert state['tour_playing'] is False
    assert tick_tour(state, CANDIDATES, now=10000) is False
    advance_tour(state, CANDIDATES, now=10001)
    assert state['tour_step'] == len(STEPS) - 1


def test_stop_restores_exact_prior_inputs_and_removes_originally_missing_keys():
    state = {'active_view': 'Check a file', 'local_variant': 'G32V',
             'compare_candidates': ['A32D'], 'local_check_result': {'nested': [1]},
             'evidence_section': 'Reference mapping & saved structures',
             'unrelated': 'preserved'}
    before = deepcopy(state)
    start_tour(state, CANDIDATES, now=0)
    advance_tour(state, CANDIDATES, now=1, delta=4)
    stop_tour(state)
    for key, value in before.items():
        assert state[key] == value
    for key in ('structure_focus', 'local_frame', 'local_objective', 'trace_step'):
        assert key not in state
    assert state['tour_active'] is False
    assert state['tour_playing'] is False


def test_restart_does_not_overwrite_the_original_snapshot():
    state = {'local_variant': 'G32V', 'compare_candidates': ['A32D']}
    start_tour(state, CANDIDATES, now=0)
    start_tour(state, CANDIDATES, now=2)
    stop_tour(state)
    assert state['local_variant'] == 'G32V'
    assert state['compare_candidates'] == ['A32D']


def test_stop_removes_the_evidence_section_if_it_was_previously_absent():
    state = {'active_view': 'Overview'}
    start_tour(state, CANDIDATES, now=0)
    advance_tour(state, CANDIDATES, now=1, delta=4)
    assert state['evidence_section'] == 'Run provenance'
    stop_tour(state)
    assert state['active_view'] == 'Overview'
    assert 'evidence_section' not in state


@pytest.mark.parametrize('candidates', [[], CANDIDATES[:1]])
def test_small_or_absent_cohort_is_handled_without_inventing_candidates(candidates):
    state = {}
    start_tour(state, candidates, now=0, autoplay=False)
    advance_tour(state, candidates, now=1)
    assert state['compare_candidates'] == [item['candidate_id'] for item in candidates]
    advance_tour(state, candidates, now=2, delta=4)
    assert state['structure_focus'] == (
        'A32E · full 32' if candidates else 'S108 · protected')
