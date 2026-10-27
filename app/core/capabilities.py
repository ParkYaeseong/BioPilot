"""Supported scientific claims. No endpoint predictor is implied by a goal."""

def objective_capability(profile_id: str) -> dict:
    profiles = {
        'sequence_plausibility_review': 'sequence_model_preference',
        'lipase_T50_hypothesis_review': 'hypothesis',
    }
    if profile_id not in profiles:
        raise ValueError('Unsupported scientific objective: no registered predictor')
    return {'claim_level': profiles[profile_id], 'phenotype_calibrated': False}
