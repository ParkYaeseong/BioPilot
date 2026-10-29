"""Local UI preparation; grants no provider or execution authority."""
import re
from app.review_checks import check_review_input
from app.session_exec import extract_positions, validate_session_request


def prepare_review(message, model_key):
    if re.search(r'\bmature\b|성숙체|성숙\s*(?:서열|번호)', message, re.I):
        raise ValueError('Declare full-reference 1-based numbering; mature numbering is refused.')
    for token in re.findall(r'(?<![A-Za-z0-9])[ACDEFGHIKLMNPQRSTVWY]\d{1,3}[ACDEFGHIKLMNPQRSTVWY](?![A-Za-z0-9])', message):
        result = check_review_input(token, 'full_reference_1based', 'sequence_plausibility_review')
        if result['status'] != 'accepted':
            raise ValueError(result['message'])
    found = extract_positions(message)
    if not found:
        raise ValueError('I could not read a full-reference position. Specify a variant or position.')
    positions = validate_session_request(found, model_key)
    return {'message': message, 'model_key': model_key, 'positions': positions}


def consume_review(state, *, armed, model_key, budget):
    request = state.get('pending_review')
    if state.get('review_phase') != 'validated' or not request:
        raise ValueError('Validate a new request before executing.')
    if not armed:
        raise ValueError('Explicit execution permission is required.')
    if request['model_key'] != model_key:
        raise ValueError('Checkpoint changed. Validate the request again.')
    budget.check()
    state['pending_review'] = None
    state['review_phase'] = 'running'
    return request


def result_phase(status):
    if status in {'sequence_review_complete', 'validation_complete', 'final_report_complete'}:
        return 'completed'
    if status == 'partial':
        return 'partial'
    return 'failed'
