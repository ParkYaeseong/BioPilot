"""Offline walkthrough of real controls over saved evidence.

The clock is injected by the UI. Advancing performs only the existing local input
guard and changes presentation state; it cannot create a run, arm a session, call
a provider, or recalculate a saved score. Playback cadence is presentation time,
never an inference-latency measurement.
"""
from copy import deepcopy
from dataclasses import dataclass

from app.review_checks import check_review_input


@dataclass(frozen=True)
class TourStep:
    id: str
    title: str
    view: str
    body: str
    focus: str
    seconds: float = 7.0


STEPS = (
    TourStep('overview', 'Understand the saved review', 'Overview',
             'Start with the research purpose, saved candidates and recorded Meta/ESM evidence. This is REPLAY, not a new run.',
             'overview'),
    TourStep('compare', 'Compare the saved shortlist', 'Candidates',
             'The first three saved candidates are selected below. Their recorded scores and ranks stay unchanged.',
             'comparison'),
    TourStep('validation_trace', 'Inspect Meta’s validation request', 'Agent Trace',
             'Open the first recorded MCP call. This is saved execution evidence, not a new Meta request.',
             'trace'),
    TourStep('scoring_trace', 'Inspect the recorded scoring call', 'Agent Trace',
             'Open the next recorded MCP call. ESM computes sequence preferences; code owns the common ranking policy.',
             'trace'),
    TourStep('provenance', 'Verify what supports the result', 'Evidence',
             'Inspect the saved provenance and local consistency checks. Unknown costs and unverified claims stay visible.',
             'evidence'),
    TourStep('unmodelled_position', 'Check the reference mapping', 'Evidence',
             'The selected candidate resolves through the registered join. Missing atoms are reported, never guessed.',
             'structure'),
    TourStep('protected_structure', 'Locate a protected residue', 'Evidence',
             'S108 uses its verified author-number join for a highlight in the experimental reference structure.',
             'structure'),
    TourStep('valid_input', 'Check a valid request', 'Input & Diagnostics',
             'A32V passes the real local numbering and residue guards. No model is called.',
             'input'),
    TourStep('protected_input', 'See the guard stop a request', 'Input & Diagnostics',
             'S108A is blocked locally because S108 is protected. This does not prove retained function.',
             'input'),
)

# Only presentation fields belong to this module. In particular armed, model_key,
# session_budget and live conversation/run records are never read or changed.
PRESENTATION_FIELDS = (
    'active_view', 'local_variant', 'local_frame', 'local_objective',
    'local_check_result', 'compare_candidates', 'show_all_candidates',
    'structure_focus', 'trace_step', 'evidence_section',
)


def _apply_step(state, candidates):
    index = state['tour_step']
    step = STEPS[index]
    state['active_view'] = step.view
    if step.id in ('valid_input', 'protected_input'):
        variant = 'A32V' if step.id == 'valid_input' else 'S108A'
        state['local_variant'] = variant
        state['local_frame'] = 'full_reference_1based'
        state['local_objective'] = 'sequence_plausibility_review'
        state['local_check_result'] = check_review_input(
            variant, 'full_reference_1based', 'sequence_plausibility_review')
    elif step.id == 'compare':
        state['compare_candidates'] = [row['candidate_id'] for row in candidates[:3]]
        state['show_all_candidates'] = False
    elif step.id == 'unmodelled_position':
        state['evidence_section'] = 'Reference mapping & saved structures'
        state['structure_focus'] = (
            f"{candidates[0]['candidate_id']} · full {candidates[0]['full_position']}"
            if candidates else 'S108 · protected')
    elif step.id == 'protected_structure':
        state['evidence_section'] = 'Reference mapping & saved structures'
        state['structure_focus'] = 'S108 · protected'
    elif step.id == 'validation_trace':
        state['trace_step'] = 0
    elif step.id == 'scoring_trace':
        state['trace_step'] = 1
    elif step.id == 'provenance':
        state['evidence_section'] = 'Run provenance'


def start_tour(state, candidates, *, now, autoplay=False):
    """Start or restart the tour, retaining the first pre-tour control snapshot."""
    if not state.get('tour_active'):
        state['tour_saved_fields'] = {
            key: deepcopy(state[key]) for key in PRESENTATION_FIELDS if key in state
        }
    state['tour_active'] = True
    state['tour_hidden'] = False
    state['tour_step'] = 0
    state['tour_complete'] = False
    state['tour_source_mode'] = 'REPLAY'
    state['tour_playing'] = bool(autoplay)
    state['tour_next_at'] = now + STEPS[0].seconds if autoplay else None
    _apply_step(state, candidates)


def advance_tour(state, candidates, *, now, delta=1):
    """Move the real presentation controls; never wrap at the last step."""
    if not state.get('tour_active'):
        return False
    state['tour_step'] = max(0, min(len(STEPS) - 1, state['tour_step'] + delta))
    state['tour_complete'] = False
    _apply_step(state, candidates)
    state['tour_next_at'] = (
        now + STEPS[state['tour_step']].seconds if state.get('tour_playing') else None)
    return True


def set_tour_playing(state, playing, *, now):
    """Pause or resume. Resume gives the reader a full interval at this step."""
    if not state.get('tour_active'):
        return
    state['tour_playing'] = bool(playing) and not state.get('tour_complete', False)
    state['tour_next_at'] = (
        now + STEPS[state['tour_step']].seconds if state['tour_playing'] else None)


def tick_tour(state, candidates, *, now):
    """Advance at most one step; a delayed browser must not skip visible actions."""
    if not state.get('tour_active') or not state.get('tour_playing'):
        return False
    deadline = state.get('tour_next_at')
    if deadline is None or now < deadline:
        return False
    if state['tour_step'] == len(STEPS) - 1:
        state['tour_complete'] = True
        state['tour_playing'] = False
        state['tour_next_at'] = None
        return True
    return advance_tour(state, candidates, now=now)


def stop_tour(state):
    """Exit and restore the pre-tour controls, including originally absent values."""
    if not state.get('tour_active'):
        return
    saved = state.get('tour_saved_fields', {})
    for key in PRESENTATION_FIELDS:
        if key in saved:
            state[key] = deepcopy(saved[key])
        elif key in state:
            del state[key]
    state['tour_active'] = False
    state['tour_playing'] = False
    state['tour_complete'] = False
    state['tour_next_at'] = None
    state['tour_hidden'] = True
    if 'tour_saved_fields' in state:
        del state['tour_saved_fields']
