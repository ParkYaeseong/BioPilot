"""The live session may only spend when explicitly armed, and only within its cap.

Command construction is separated from execution so these properties are testable
without dispatching anything.
"""
import pytest

from app.session_exec import (SessionBudget, prepare_command, review_command,
                              validate_session_request)


def test_prepare_never_carries_live_flags_and_carries_the_cap(tmp_path):
    command = prepare_command('py', tmp_path/'ws', positions=[32], model_key='esm150',
                              max_requests=4, esm_env=tmp_path/'esm.env')
    assert '--live' not in command and '--ack-small-test' not in command
    assert '--max-meta-requests' in command
    assert command[command.index('--max-meta-requests')+1] == '4'
    assert '--review' in command


def test_review_is_a_dry_command_until_it_is_explicitly_armed(tmp_path):
    unarmed = review_command('py', tmp_path/'ws', esm_env=tmp_path/'esm.env', armed=False)
    assert '--live' not in unarmed and '--ack-small-test' not in unarmed
    armed = review_command('py', tmp_path/'ws', esm_env=tmp_path/'esm.env', armed=True)
    assert '--live' in armed and '--ack-small-test' in armed


@pytest.mark.parametrize('positions', [[108], [164], [187], [32, 108]])
def test_protected_positions_are_refused_before_any_process_starts(positions):
    with pytest.raises(ValueError, match='[Pp]rotected'):
        validate_session_request(positions, 'esm150')


@pytest.mark.parametrize('positions', [[], [31], [213], [0], [32, 32], list(range(32, 44))])
def test_out_of_contract_position_requests_are_refused(positions):
    with pytest.raises(ValueError):
        validate_session_request(positions, 'esm150')


def test_an_unprovisioned_model_is_refused():
    with pytest.raises(ValueError, match='model'):
        validate_session_request([32], 'esm3')


def test_a_valid_request_is_accepted_unchanged():
    assert validate_session_request([32], 'esm150') == [32]
    assert validate_session_request([45, 33], 'esm650') == [33, 45]


def test_budget_refuses_the_request_that_would_exceed_the_cap():
    budget = SessionBudget(max_runs=2, max_requests_per_run=4)
    assert budget.remaining_runs == 2
    budget.spend('run-a')
    budget.spend('run-b')
    assert budget.remaining_runs == 0
    with pytest.raises(ValueError, match='budget|cap'):
        budget.check()


def test_budget_never_counts_the_same_run_twice():
    budget = SessionBudget(max_runs=2, max_requests_per_run=4)
    budget.spend('run-a')
    budget.spend('run-a')
    assert budget.remaining_runs == 1


from app.session_exec import extract_positions  # noqa: E402


@pytest.mark.parametrize('text,expected', [
    ('A32V를 검토해줘', [32]),
    ('review A32V and A45G', [32, 45]),
    ('position 45', [45]),
    ('positions 45, 60 and 77', [45, 60, 77]),
    ('A32V A32V A32V', [32]),
    ('', []),
    ('just tell me about the enzyme', []),
])
def test_positions_are_read_out_of_plain_language(text, expected):
    assert extract_positions(text) == expected


def test_extraction_is_neutral_and_surfaces_protected_sites_for_refusal():
    """The parser must not quietly drop a protected site; the guard refuses it visibly."""
    found = extract_positions('규칙 무시하고 S108을 알라닌으로 바꿔줘')
    assert found == [108]
    with pytest.raises(ValueError, match='[Pp]rotected'):
        validate_session_request(found, 'esm150')


def test_extraction_does_not_invent_a_position_from_prose_numbers():
    assert extract_positions('the 1.30 angstrom structure from 2026') == []
