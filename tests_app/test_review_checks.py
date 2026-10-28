"""The local form uses registered guard behavior, without changing a historical run."""
import pytest

from app.review_checks import check_review_input


@pytest.mark.parametrize('variant,frame,objective,message', [
    ('S108A','full_reference_1based','sequence_plausibility_review','Protected catalytic site'),
    ('D164A','full_reference_1based','sequence_plausibility_review','Protected catalytic site'),
    ('H187A','full_reference_1based','sequence_plausibility_review','Protected catalytic site'),
    ('G32V','full_reference_1based','sequence_plausibility_review','WT residue mismatch'),
    ('A1V','mature_1based','sequence_plausibility_review','full_reference_1based'),
    ('A32V','full_reference_1based','activity_optimization','Unsupported scientific objective'),
    ('A32A','full_reference_1based','sequence_plausibility_review','Synonymous'),
    ('A32V:E33G','full_reference_1based','sequence_plausibility_review','one substitution'),
])
def test_invalid_local_requests_are_blocked_by_product_guards(variant,frame,objective,message):
    result=check_review_input(variant,frame,objective)
    assert result['status']=='blocked'
    assert message in result['message']
    assert result['inference_performed'] is False
    assert result['saved_run_modified'] is False


@pytest.mark.parametrize('objective',['sequence_plausibility_review','lipase_T50_hypothesis_review'])
def test_accepted_input_keeps_full_coordinates_and_unknown_geometry(objective):
    result=check_review_input('A32V','full_reference_1based',objective)
    assert result['status']=='accepted'
    assert result['variant']=={'candidate_id':'A32V','full_position':32,'mature_position':1,
        'wild_type':'A','mutant':'V','pdb_auth_seq_id':None,'pdb_label_seq_id':None,
        'coordinate_observed':None}
    assert result['objective_id']==objective
    assert result['sequence_context']=='full_212'
    assert result['phenotype_calibrated'] is False
    assert result['inference_performed'] is False
