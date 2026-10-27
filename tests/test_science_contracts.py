"""Offline guard tests. Synthetic scores are not biological predictions."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ScienceContractTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'checks/science_contracts.py'
        self.assertTrue(path.exists(), 'Scientific guard implementation is not present yet')
        spec = importlib.util.spec_from_file_location('science_contracts', path)
        self.s = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.s)
        self.p = json.loads((ROOT/'reference/target_profile.json').read_text())

    def test_exact_mapping_finds_start_32(self):
        m = self.s.exact_sequence_map(self.p['reference_sequence'], self.p['mature_sequence'])
        self.assertEqual((m[1],m[77],m[133],m[156],m[181]), (32,108,164,187,212))
    def test_mapping_is_not_assumed_offset(self):
        self.assertEqual(self.s.exact_sequence_map('MMADEF','ADEF'), {1:3,2:4,3:5,4:6})
    def test_ambiguous_mapping_rejected(self):
        with self.assertRaises(ValueError): self.s.exact_sequence_map('AAAA','AA')
    def test_nonmatching_mapping_rejected(self):
        with self.assertRaises(ValueError): self.s.exact_sequence_map('ACDEF','ACGEF')
    def test_noncanonical_sequence_rejected(self):
        with self.assertRaises(ValueError): self.s.exact_sequence_map('ACXEF','CEF')
    def test_registered_target_verifies(self):
        out=self.s.verify_target(self.p)
        self.assertEqual(out['protected_full_positions'],[108,164,187])
        self.assertFalse(out['coordinate_mapping_verified'])
    def test_wrong_reference_hash_rejected(self):
        self.p['reference_sha256']='0'*64
        with self.assertRaises(ValueError): self.s.verify_target(self.p)
    def test_wrong_protected_residue_rejected(self):
        self.p['protected_sites'][0]['full_position']=77
        with self.assertRaises(ValueError): self.s.verify_target(self.p)
    def test_wrong_protected_numbering_rejected(self):
        self.p['protected_sites'][2]['mature_position']=155
        with self.assertRaises(ValueError): self.s.verify_target(self.p)
    def test_allowed_variant_keeps_reference_mapping(self):
        out=self.s.validate_variant(self.p,'A32V')
        self.assertEqual((out['full_position'],out['mature_position'],out['wild_type']), (32,1,'A'))
    def test_catalytic_site_blocked(self):
        with self.assertRaises(ValueError): self.s.validate_variant(self.p,'S108A')
    def test_mature_number_not_silently_used_as_full(self):
        with self.assertRaises(ValueError): self.s.validate_variant(self.p,'S77A')
    def test_prefix_outside_mature_region_blocked(self):
        with self.assertRaises(ValueError): self.s.validate_variant(self.p,'M1A')
    def test_full_length_terminal_variant_valid(self):
        self.assertEqual(self.s.validate_variant(self.p,'N212A')['mature_position'],181)
    def test_multimutant_rejected(self):
        with self.assertRaises(ValueError): self.s.validate_variant(self.p,'A32V:H34A')
    def test_synonymous_rejected(self):
        with self.assertRaises(ValueError): self.s.validate_variant(self.p,'A32A')
    def test_zero_position_rejected(self):
        with self.assertRaises(ValueError): self.s.validate_variant(self.p,'A0V')
    def test_generic_objective_not_calibrated(self):
        self.assertFalse(self.s.objective_capability('sequence_plausibility_review')['phenotype_calibrated'])
    def test_t50_objective_remains_hypothesis(self):
        self.assertEqual(self.s.objective_capability('lipase_T50_hypothesis_review')['claim_level'],'hypothesis')
    def test_unsupported_activity_objective_blocked(self):
        with self.assertRaises(ValueError): self.s.objective_capability('activity_optimization')
    def test_median_bin_is_not_wt_improvement(self):
        self.assertEqual(self.s.binary_label_meaning(1,'median'),'upper_median_group_not_WT_improvement')
    def test_unknown_binary_rule_not_guessed(self):
        with self.assertRaises(ValueError): self.s.binary_label_meaning(1,'unknown')
    def test_missing_wt_is_unknown(self):
        self.assertEqual(self.s.classify_t50(48,None,0.5,True,True),'unknown')
    def test_unverified_error_rule_is_unknown(self):
        self.assertEqual(self.s.classify_t50(48,47,0.5,True,False),'unknown')
    def test_mismatched_assay_is_unknown(self):
        self.assertEqual(self.s.classify_t50(48,47,0.5,False,True),'unknown')
    def test_verified_change_is_not_experimental_proof(self):
        self.assertEqual(self.s.classify_t50(48,47,0.5,True,True),'above_WT_under_registered_rule')
    def test_equal_error_boundary_not_above(self):
        self.assertEqual(self.s.classify_t50(47.5,47,0.5,True,True),'not_above_WT_under_registered_rule')
    def test_nonfinite_phenotype_rejected(self):
        with self.assertRaises(ValueError): self.s.classify_t50(float('nan'),47,0.5,True,True)
    def test_negative_error_margin_rejected(self):
        with self.assertRaises(ValueError): self.s.classify_t50(48,47,-1,True,True)
    def records(self):
        common={'checkpoint':'fixture150','score_kind':'masked_marginal','reference_sha256':'a'*64,'sequence_context':'full_212'}
        return [dict(common,candidate_id='c2',score=1.0,annotation={'score650':90}),dict(common,candidate_id='c1',score=1.0,annotation={'score650':-90}),dict(common,candidate_id='c3',score=-1.0)]
    def rank(self, rows):
        return self.s.rank_baseline(rows,checkpoint='fixture150',score_kind='masked_marginal',reference_sha256='a'*64,sequence_context='full_212')
    def test_rank_ties_deterministic_annotations_ignored(self):
        self.assertEqual([r['candidate_id'] for r in self.rank(self.records())],['c1','c2','c3'])
    def test_mixed_model_rejected(self):
        r=self.records();r[0]['checkpoint']='fixture650'
        with self.assertRaises(ValueError):self.rank(r)
    def test_mixed_full_mature_context_rejected(self):
        r=self.records();r[0]['sequence_context']='mature_181'
        with self.assertRaises(ValueError):self.rank(r)
    def test_duplicate_candidates_rejected(self):
        r=self.records();r[1]['candidate_id']='c2'
        with self.assertRaises(ValueError):self.rank(r)
    def test_nan_score_rejected(self):
        r=self.records();r[0]['score']=float('nan')
        with self.assertRaises(ValueError):self.rank(r)
    def test_unknown_coordinate_not_zero(self):
        row={'coordinate_observed':None,'pdb_auth_seq_id':None,'pdb_label_seq_id':None}
        with self.assertRaises(ValueError):self.s.require_coordinate_row(row)
    def test_unobserved_coordinate_blocked(self):
        row={'coordinate_observed':False,'pdb_auth_seq_id':'77','pdb_label_seq_id':77}
        with self.assertRaises(ValueError):self.s.require_coordinate_row(row)
    def test_missing_prediction_is_not_dropped(self):
        with self.assertRaises(ValueError):self.s.validate_prediction_cohort(['c1'],['c1','c2'])
    def test_exact_cohort_passes(self):
        self.s.validate_prediction_cohort(['c2','c1'],['c1','c2'])
    def test_duplicate_prediction_rejected(self):
        with self.assertRaises(ValueError):self.s.validate_prediction_cohort(['c1','c1'],['c1'])

if __name__=='__main__': unittest.main()
