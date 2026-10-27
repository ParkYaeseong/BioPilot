"""Behavior tests for offline catalog, scoring and recording guards; no live API tests."""
from __future__ import annotations
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class HackathonContractsTests(unittest.TestCase):
    def setUp(self):
        path=ROOT/'checks'/'hackathon_contracts.py'
        self.assertTrue(path.exists(), 'Planned offline contract helper is not implemented')
        spec=importlib.util.spec_from_file_location('hackathon_contracts',path)
        self.h=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.h)
        self.catalog=[
          {'name':'score_positions','description':'Score registered positions.','inputSchema':{
            'type':'object','properties':{'model_key':{'type':'string','enum':['esm150','esm650']}},
            'required':['model_key'],'additionalProperties':False}},
          {'name':'get_run_status','description':'Read status.','inputSchema':{
            'type':'object','properties':{},'required':[],'additionalProperties':False}},
          {'name':'predict_structure','description':'Optional fold.','inputSchema':{
            'type':'object','properties':{},'required':[],'additionalProperties':False}},
        ]

    def test_default_catalog_omits_optional_fold(self):
        got=self.h.select_tools(self.catalog,{'score_positions','get_run_status','predict_structure'})
        self.assertEqual([x['name'] for x in got],['score_positions','get_run_status'])

    def test_default_catalog_disallows_verifier_checkpoint(self):
        got=self.h.select_tools(self.catalog,{'score_positions'})
        self.assertEqual(got[0]['inputSchema']['properties']['model_key']['enum'],['esm150'])

    def test_catalog_filter_does_not_mutate_shared_schema(self):
        original=copy.deepcopy(self.catalog)
        self.h.select_tools(self.catalog,{'score_positions'})
        self.assertEqual(self.catalog,original)

    def test_explicit_optional_capabilities_preserve_requested_tools(self):
        got=self.h.select_tools(self.catalog,{'score_positions','predict_structure'},fold_enabled=True,verifier_enabled=True)
        self.assertEqual([x['name'] for x in got],['score_positions','predict_structure'])
        self.assertEqual(got[0]['inputSchema']['properties']['model_key']['enum'],['esm150','esm650'])

    def test_unknown_tool_cannot_be_whitelisted(self):
        with self.assertRaises(ValueError):self.h.select_tools(self.catalog,{'read_labels'})

    def test_evaluator_tool_rejected_even_when_claimed_available(self):
        malicious={'name':'read_labels','description':'Read outcomes','inputSchema':{'type':'object','properties':{}}}
        with self.assertRaises(ValueError):self.h.select_tools(self.catalog+[malicious],{'read_labels'})

    def test_duplicate_catalog_tool_names_rejected(self):
        with self.assertRaises(ValueError):self.h.select_tools(self.catalog+[self.catalog[0]],{'score_positions'})

    def test_native_conversion_preserves_schema(self):
        got=self.h.to_chat_tools([self.catalog[1]])
        self.assertEqual(got,[{'type':'function','function':{'name':'get_run_status','description':'Read status.','strict':True,
          'parameters':{'type':'object','properties':{},'required':[],'additionalProperties':False}}}])

    def test_weighted_score_uses_latest_rubric(self):
        got=self.h.weighted_score({'impact':10,'meta_tooling':0,'technical_execution':0,'demo':0})
        self.assertEqual(got,3.0)

    def test_weighted_score_mixed_values(self):
        got=self.h.weighted_score({'impact':8,'meta_tooling':6,'technical_execution':10,'demo':4})
        self.assertAlmostEqual(got,6.9)

    def test_weighted_score_missing_category_is_not_zero(self):
        with self.assertRaises(ValueError):self.h.weighted_score({'impact':8})

    def test_weighted_score_rejects_out_of_range_and_nonfinite(self):
        for bad in [-1,11,float('nan'),float('inf'),True]:
            with self.subTest(bad=bad):
                scores=dict(impact=bad,meta_tooling=5,technical_execution=5,demo=5)
                with self.assertRaises(ValueError):self.h.weighted_score(scores)

    def test_180_second_timeline_accepted(self):
        self.assertEqual(self.h.validate_timeline([{'start_s':0,'end_s':25},{'start_s':25,'end_s':180}]),180)

    def test_timeline_overlap_rejected(self):
        with self.assertRaises(ValueError):self.h.validate_timeline([{'start_s':0,'end_s':90},{'start_s':80,'end_s':180}])

    def test_timeline_gap_rejected(self):
        with self.assertRaises(ValueError):self.h.validate_timeline([{'start_s':0,'end_s':90},{'start_s':100,'end_s':180}])

    def test_timeline_overlong_rejected(self):
        with self.assertRaises(ValueError):self.h.validate_timeline([{'start_s':0,'end_s':181}])

    def test_timeline_empty_rejected(self):
        with self.assertRaises(ValueError):self.h.validate_timeline([])

    def test_bundle_only_contains_explicit_runtime_files(self):
        allowed={'reference/target_profile.json','prompts/runtime/00_developer.txt'}
        self.assertEqual(self.h.validate_bundle_paths(['reference/target_profile.json'],allowed),['reference/target_profile.json'])

    def test_evaluator_paths_cannot_be_allowed_by_config(self):
        for path in ['evaluation_private/assay_protocol.json','tests/test_science_contracts.py','docs/04_science_and_evaluation.md']:
            with self.subTest(path=path):
                with self.assertRaises(ValueError):self.h.validate_bundle_paths([path],{path})

    def test_traversal_and_absolute_paths_rejected(self):
        for path in ['../labels.json','/tmp/labels.json','C:\\labels.json','reference/../labels.json']:
            with self.subTest(path=path):
                with self.assertRaises(ValueError):self.h.validate_bundle_paths([path],{path})

    def test_arbitrary_unlisted_runtime_file_rejected(self):
        with self.assertRaises(ValueError):self.h.validate_bundle_paths(['reference/extra.json'],{'reference/target_profile.json'})

    def test_duplicate_bundle_paths_rejected(self):
        path='reference/target_profile.json'
        with self.assertRaises(ValueError):self.h.validate_bundle_paths([path,path],{path})

    def test_replay_is_not_labeled_live(self):
        self.assertEqual(self.h.evidence_badge('replay'), 'REPLAY - previously recorded real execution')

    def test_synthetic_fixture_is_not_evidence(self):
        self.assertEqual(self.h.evidence_badge('synthetic_fixture'), 'SYNTHETIC FIXTURE - not scientific evidence')

    def test_unknown_source_mode_rejected(self):
        with self.assertRaises(ValueError):self.h.evidence_badge('almost_live')

if __name__=='__main__':unittest.main()
