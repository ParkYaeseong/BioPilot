"""Local policy intake only; uses product guards without providers or saved-run state."""
from dataclasses import asdict

from app.core.targets import registered_profile, validate_target, validate_variant


def check_review_input(variant, frame, objective):
    """Check one separately entered request; no inference or saved artifact mutation."""
    try:
        target = validate_target(registered_profile(), objective, reference_numbering=frame)
        checked = validate_variant(target, variant, reference_numbering=frame)
    except ValueError as error:
        return {'status': 'blocked', 'message': str(error), 'variant': variant,
                'reference_numbering': frame, 'objective_id': objective,
                'inference_performed': False, 'saved_run_modified': False}
    return {'status': 'accepted', 'message': 'Input satisfies the registered sequence review guards.',
            'variant': asdict(checked), 'reference_numbering': frame,
            'objective_id': objective, 'sequence_context': target.sequence_context,
            'phenotype_calibrated': False, 'inference_performed': False,
            'saved_run_modified': False}
