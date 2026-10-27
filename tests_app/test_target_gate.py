from copy import deepcopy
from dataclasses import FrozenInstanceError
import hashlib
import pytest

from app.core.targets import (registered_profile, validate_target, validate_variant,
                              normalize_sequence, require_coordinates)

GOAL = 'sequence_plausibility_review'

def test_registered_target_has_immutable_full_context():
    target = validate_target(registered_profile(), GOAL)
    assert len(target.reference_sequence) == 212
    assert target.sequence_context == 'full_212'
    assert target.protected_positions == (108, 164, 187)
    assert target.coordinate_mapping_verified is False
    assert target.phenotype_calibrated is False
    with pytest.raises(FrozenInstanceError):
        target.protected_positions = ()

@pytest.mark.parametrize('frame', ['mature_1based', 'pdb_auth', None])
def test_mature_frame_is_not_silently_accepted(frame):
    with pytest.raises(ValueError, match='frame|numbering'):
        validate_target(registered_profile(), GOAL, reference_numbering=frame)

@pytest.mark.parametrize('field,value', [
    ('protected_sites', []), ('reference_id', 'arbitrary'),
    ('reference_indexing', 'mature_1based'),
    ('baseline', {'inference_context': 'mature_181'})])
def test_caller_cannot_change_registry_policy(field, value):
    profile = registered_profile()
    profile[field] = value
    with pytest.raises(ValueError):
        validate_target(profile, GOAL)

def test_self_consistent_alternate_sequence_is_not_registered():
    profile = registered_profile()
    profile['reference_sequence'] = 'A' + profile['reference_sequence'][1:]
    profile['reference_sha256'] = hashlib.sha256(profile['reference_sequence'].encode()).hexdigest()
    with pytest.raises(ValueError, match='registered'):
        validate_target(profile, GOAL)

@pytest.mark.parametrize('variant,full,mature', [('A32V',32,1), ('N212A',212,181)])
def test_allowed_variants_keep_exact_mapping(variant, full, mature):
    result = validate_variant(registered_profile(), variant)
    assert (result.full_position, result.mature_position) == (full, mature)
    assert result.candidate_id == variant
    assert result.coordinate_observed is None
    assert result.pdb_auth_seq_id is None

@pytest.mark.parametrize('variant', ['S108A', 'D164A', 'H187A', 'S77A', 'A32A',
                                      'G32A', 'M1A', 'A32V:N212A', 'A0V', 'A213V'])
def test_invalid_or_protected_variants_are_blocked(variant):
    with pytest.raises(ValueError):
        validate_variant(registered_profile(), variant)

def test_variant_frame_cannot_be_changed():
    with pytest.raises(ValueError, match='frame|numbering'):
        validate_variant(registered_profile(), 'A32V', reference_numbering='mature_1based')

def test_coordinate_claim_fails_closed():
    target = validate_target(registered_profile(), GOAL)
    with pytest.raises(ValueError, match='coordinates'):
        require_coordinates(target, [32, 108])

def test_unsupported_goal_is_blocked():
    with pytest.raises(ValueError, match='objective'):
        validate_target(registered_profile(), 'activity_optimization')

def test_t50_goal_stays_uncalibrated():
    target = validate_target(registered_profile(), 'lipase_T50_hypothesis_review')
    assert target.claim_level == 'hypothesis'
    assert target.phenotype_calibrated is False

def test_normalize_single_fasta_without_cropping():
    sequence = registered_profile()['reference_sequence']
    assert normalize_sequence('>public reference\n' + sequence.lower() + '\n') == sequence

@pytest.mark.parametrize('text', ['', '>empty\n', '>a\nACD\n>b\nEFG', 'ACX', 'A-C', 'A'*513])
def test_ambiguous_or_multi_record_sequence_rejected(text):
    with pytest.raises(ValueError):
        normalize_sequence(text)
