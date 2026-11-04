"""The viewer renders saved artifacts only. It computes no science and calls nothing."""
import json

import pytest

from pathlib import Path as _Path

from app.viewer_data import (load_run_view, format_candidate_rows, claim_banner,
                            provenance_chain, PROVENANCE_CHAIN_SCOPE)

VIEWER_APP=_Path(__file__).resolve().parents[1]/'app'/'viewer.py'

def at_view(app, name):
    """Open one view. The viewer renders only the active view, as the tour drives it."""
    if name in ('Input', 'Input & Diagnostics'):
        app.session_state['evidence_section'] = 'Advanced diagnostics'
        name = 'Evidence'
    app.session_state['active_view'] = name
    return app.run()



def saved_report(**overrides):
    report={'run_id':'r1','workflow':'sequence_review','status':'sequence_review_complete',
        'provider':'Meta Model API','requested_model':'muse-spark-1.3','actual_model':'muse-spark-1.3',
        'source_mode':'live','meta_source_mode':'live','esm_source_mode':'live',
        'ranking_scope':'esm150_masked_v1','scientific_scope':'unvalidated_sequence_evidence_assistant',
        'biological_efficacy_established':False,'actual_cost_micros':None,'cost_status':'unknown',
        'mcp_protocol_version':'2025-11-25','meta_request_attempts':3,
        'model_narrative':'Sequence preferences only.',
        'candidates':[{'candidate_id':'A32E','score':-1.25,'full_position':32,'wild_type':'A','mutant':'E',
                       'score_kind':'masked_marginal_log_likelihood_ratio','rank_policy':'esm150_masked_v1'},
                      {'candidate_id':'A32S','score':-1.61,'full_position':32,'wild_type':'A','mutant':'S',
                       'score_kind':'masked_marginal_log_likelihood_ratio','rank_policy':'esm150_masked_v1'}],
        'score_artifacts':[{'artifact_sha256':'a'*64,'provenance':{'checkpoint':'esm2_t30_150M_UR50D',
            'device':'cpu','precision':'float32','sequence_context':'full_212'}}],
        'trace':[{'event':'meta_response','finish_reason':'tool_calls','content_chars':84},
                 {'event':'mcp_tool','tool':'validate_target_context','result':{'status':'ok'}},
                 {'event':'mcp_tool','tool':'score_positions','result':{'status':'completed',
                                                                        'artifact_sha256':'a'*64}}]}
    report.update(overrides)
    return report


def write(tmp_path,report):
    path=tmp_path/'report.json'
    path.write_text(json.dumps(report),encoding='utf-8')
    return path


def test_view_reads_only_the_saved_record(tmp_path):
    view=load_run_view(write(tmp_path,saved_report()))
    assert view['status']=='sequence_review_complete'
    assert view['actual_model']=='muse-spark-1.3'
    assert view['mcp_protocol_version']=='2025-11-25'
    assert view['candidate_count']==2
    assert view['tool_calls']==['validate_target_context','score_positions']
    assert view['score_artifact_sha256']=='a'*64


def test_unknown_cost_is_shown_as_unknown_never_zero(tmp_path):
    view=load_run_view(write(tmp_path,saved_report()))
    assert view['actual_cost_micros'] is None
    assert view['cost_display']=='unknown (not verified)'


def test_a_settled_cost_is_rendered_from_the_record(tmp_path):
    view=load_run_view(write(tmp_path,saved_report(actual_cost_micros=12345,cost_status='actual')))
    assert view['cost_display']=='$0.012345'


def test_rows_are_rendered_from_artifact_numbers_in_rank_order(tmp_path):
    rows=format_candidate_rows(saved_report()['candidates'])
    assert [row['rank'] for row in rows]==[1,2]
    assert [row['candidate_id'] for row in rows]==['A32E','A32S']
    assert rows[0]['score']=='-1.250000'
    assert rows[0]['score_kind']=='masked_marginal_log_likelihood_ratio'


def test_banner_always_states_the_unvalidated_scope(tmp_path):
    banner=claim_banner(load_run_view(write(tmp_path,saved_report())))
    assert 'not' in banner.lower()
    for forbidden in ('T50','activity','solubility','Tm'):
        assert forbidden in banner
    assert 'biological efficacy' in banner.lower()


def test_replayed_scores_are_labelled_differently_from_live(tmp_path):
    live=load_run_view(write(tmp_path,saved_report()))
    other=tmp_path/'b';other.mkdir()
    replay=load_run_view(write(other,saved_report(esm_source_mode='replay',
                                                  scores_reused_from_saved_artifact=True)))
    assert live['esm_badge']=='LIVE'
    assert replay['esm_badge']=='REPLAY'
    assert replay['scores_reused_from_saved_artifact'] is True
    assert live['scores_reused_from_saved_artifact'] is False


def test_synthetic_fixture_is_never_shown_as_real_evidence(tmp_path):
    view=load_run_view(write(tmp_path,saved_report(source_mode='synthetic_fixture',
                                                    esm_source_mode='synthetic_fixture')))
    assert view['esm_badge']=='SYNTHETIC_FIXTURE'
    assert view['is_scientific_evidence'] is False


def test_live_meta_validation_without_scores_has_no_esm_evidence(tmp_path):
    report=saved_report(status='validation_complete',source_mode='live',
                        candidates=[],score_artifacts=[])
    report.pop('esm_source_mode')
    view=load_run_view(write(tmp_path,report))
    assert view['esm_source_mode'] is None
    assert view['esm_badge']=='UNAVAILABLE'
    assert view['is_scientific_evidence'] is False


def test_esm_badge_requires_a_recorded_score_artifact(tmp_path):
    view=load_run_view(write(tmp_path,saved_report(score_artifacts=[])))
    assert view['esm_badge']=='UNAVAILABLE'
    assert view['is_scientific_evidence'] is False


def test_legacy_score_mode_comes_from_score_artifact_not_meta(tmp_path):
    report=saved_report(source_mode='live')
    report.pop('esm_source_mode')
    report['score_artifacts'][0]['source_mode']='replay'
    view=load_run_view(write(tmp_path,report))
    assert view['esm_badge']=='REPLAY'


def test_saved_live_record_is_always_presented_as_playback(tmp_path,monkeypatch):
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    path=write(tmp_path,saved_report())
    monkeypatch.setattr('sys.argv',['viewer.py','--artifact',str(path)])
    app=AppTest.from_file(str(VIEWER_APP),default_timeout=60).run()
    assert not app.exception
    assert any('REPLAY' in str(e.value) and 'no new inference' in str(e.value)
               for e in app.caption)
    at_view(app, 'Evidence')
    assert any('Recorded ESM source mode: LIVE' in str(e.value) for e in app.text)


def test_partial_run_is_not_displayed_as_complete(tmp_path):
    view=load_run_view(write(tmp_path,saved_report(status='partial',
                                                    stop_reason='invalid_or_forbidden_model_output')))
    assert view['status']=='partial'
    assert view['is_complete'] is False
    assert view['stop_reason']=='invalid_or_forbidden_model_output'


def test_missing_file_fails_loudly_rather_than_rendering_blanks(tmp_path):
    with pytest.raises((ValueError,OSError)):
        load_run_view(tmp_path/'absent.json')


def test_viewer_module_imports_nothing_that_can_call_a_provider():
    """Assert the real import graph, not words that may appear in a docstring."""
    import ast
    import app.viewer_data as module
    tree=ast.parse(open(module.__file__,encoding='utf-8').read())
    imported=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            imported.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node,ast.ImportFrom) and node.module:
            imported.add(node.module.split('.')[0])
    assert imported<={'json','pathlib','csv','io','hashlib','math'}
    for forbidden in ('urllib','requests','http','socket','subprocess','os','app','evaluation'):
        assert forbidden not in imported


def test_streamlit_config_pins_the_viewer_to_loopback():
    """A viewer that shows provenance must not be served on every interface."""
    import tomllib
    from pathlib import Path
    config=tomllib.loads(Path('.streamlit/config.toml').read_text(encoding='utf-8'))
    assert config['server']['address']=='localhost'
    assert config['server']['headless'] is True
    assert config['browser']['gatherUsageStats'] is False


def test_app_actually_renders_the_saved_run_without_exception(tmp_path,monkeypatch):
    """AppTest runs the script for real; an HTTP 200 on the shell page does not."""
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    path=write(tmp_path,saved_report())
    monkeypatch.setattr('sys.argv',['viewer.py','--artifact',str(path)])
    app=AppTest.from_file(str(VIEWER_APP),default_timeout=60).run()
    assert not app.exception
    text=' '.join(str(element.value) for element in app.caption)+' '.join(
        str(element.value) for element in app.warning)
    assert 'T50' in text or any('T50' in str(w.value) for w in app.warning)
    assert any('sequence_review_complete' in str(m.value) for m in app.caption)
    rendered = ' '.join(str(m.value) for m in app.html)
    assert 'muse-spark-1.3' in rendered
    assert 'unknown (not verified)' in rendered


def test_app_shows_an_error_instead_of_blanks_when_the_artifact_is_missing(tmp_path,monkeypatch):
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr('sys.argv',['viewer.py','--artifact',str(tmp_path/'absent.json')])
    app=AppTest.from_file(str(VIEWER_APP),default_timeout=60).run()
    assert not app.exception
    assert any('Nothing rendered' in str(e.value) for e in app.error)


def test_app_marks_an_incomplete_run_as_not_complete(tmp_path,monkeypatch):
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    path=write(tmp_path,saved_report(status='partial',stop_reason='invalid_or_forbidden_model_output'))
    monkeypatch.setattr('sys.argv',['viewer.py','--artifact',str(path)])
    app=AppTest.from_file(str(VIEWER_APP),default_timeout=60).run()
    assert not app.exception
    assert any('not a completed review' in str(e.value) for e in app.error)


def test_task_context_does_not_invent_an_unsaved_goal_or_constraints(tmp_path):
    report=saved_report()
    report['candidates'][0]['reference_id']='ESTA_BACSU_Nutschel_2020'
    view=load_run_view(write(tmp_path,report))
    assert view.get('task_context') == {
        'title':'Saved sequence preference review',
        'reference_id':'ESTA_BACSU_Nutschel_2020',
        'positions':[32], 'objective_id':None, 'additional_constraints':None,
        'sequence_context':'full_212', 'reference_numbering':None,
    }


def test_public_tool_timeline_preserves_order_and_omits_private_fields(tmp_path):
    report=saved_report()
    report['trace'][1]['arguments']={'reason_brief':'Validate the registered target',
        'reference_id':'ESTA_BACSU_Nutschel_2020','api_key':'secret-marker'}
    report['trace'][1]['result']['private_reasoning']='secret-marker'
    report['trace'][2]['arguments']={'reason_brief':'Score the approved cohort','positions_1based':[32]}
    view=load_run_view(write(tmp_path,report))
    events=view.get('tool_events',[])
    assert [event['tool'] for event in events]==['validate_target_context','score_positions']
    assert [event['step'] for event in events]==[1,2]
    assert events[0]['reason_brief']=='Validate the registered target'
    assert events[1]['arguments']=={'positions_1based':[32]}
    assert 'secret-marker' not in json.dumps(events)


def test_subset_and_csv_keep_original_ranks_and_formula_safe_text():
    from app import viewer_data
    rows=format_candidate_rows(saved_report()['candidates'])
    selected=viewer_data.select_candidate_rows(rows,['A32S'])
    assert [row['rank'] for row in selected]==[2]
    assert selected[0]['score']=='-1.610000'
    csv_text=viewer_data.candidate_csv([dict(selected[0],candidate_id='=HYPERLINK("bad")')])
    import csv,io
    exported=list(csv.DictReader(io.StringIO(csv_text)))
    assert exported[0]['rank']=='2'
    assert exported[0]['candidate_id'].startswith("'=")
    assert exported[0]['score']=='-1.610000'


def test_workbench_top_five_selection_and_trace_are_real_interactions(monkeypatch):
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    path=VIEWER_APP.parents[1]/'examples'/'artifacts'/'sequence_review.replay.json'
    monkeypatch.setattr('sys.argv',['viewer.py','--artifact',str(path)])
    app=AppTest.from_file(str(VIEWER_APP),default_timeout=60).run()
    assert not app.exception
    at_view(app, 'Candidates')
    assert len(app.table[0].value)==5
    assert app.multiselect(key='compare_candidates').value==[]
    app.multiselect(key='compare_candidates').set_value(['A32S','A32E']).run()
    assert not app.exception
    compared=app.table[1].value
    assert list(compared['Rank'])==[1,2]
    assert list(compared['Variant'])==['A32E','A32S']
    app.toggle(key='show_all_candidates').set_value(True).run()
    assert len(app.table[0].value)==19
    at_view(app, 'Agent Trace')
    assert app.selectbox(key='trace_step').options[0].startswith('01')


def test_local_input_check_refuses_protection_without_touching_artifact(tmp_path,monkeypatch):
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    path=write(tmp_path,saved_report())
    before=path.read_bytes()
    monkeypatch.setattr('sys.argv',['viewer.py','--artifact',str(path)])
    app=AppTest.from_file(str(VIEWER_APP),default_timeout=60).run()
    at_view(app, 'Input & Diagnostics')
    app.text_input(key='local_variant').set_value('S108A')
    app.button(key='FormSubmitter:offline_check-Check input locally').click().run()
    assert not app.exception
    assert any('Protected catalytic site' in str(item.value) for item in app.error)
    assert path.read_bytes()==before


@pytest.mark.parametrize('payload',['=1+1',' +SUM(A1)','-cmd','@formula','\tplain','\rplain','\nplain'])
def test_csv_neutralizes_text_formulas_and_control_prefixes(payload):
    from app.viewer_data import candidate_csv
    import csv,io
    row=format_candidate_rows(saved_report()['candidates'])[0]
    row['candidate_id']=payload
    exported=list(csv.DictReader(io.StringIO(candidate_csv([row]))))
    assert exported[0]['candidate_id']=="'"+payload
    assert exported[0]['score']=='-1.250000'


def test_comparison_limit_is_enforced_even_without_a_widget():
    from app.viewer_data import select_candidate_rows
    with pytest.raises(ValueError,match='three'):
        select_candidate_rows([],['A32E','A32S','A32D','A32Q'])


def test_raw_artifact_markup_stays_plain_text_and_private_provenance_is_absent(tmp_path,monkeypatch):
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    report=saved_report(model_narrative='<script>alert(1)</script> ![remote](https://example.com/pixel)')
    report['trace'][1]['arguments']={'reason_brief':'<img src=x onerror=alert(1)>'}
    report['score_artifacts'][0]['provenance']['api_key']='private-marker'
    path=write(tmp_path,report)
    monkeypatch.setattr('sys.argv',['viewer.py','--artifact',str(path)])
    app=AppTest.from_file(str(VIEWER_APP),default_timeout=60).run()
    assert not app.exception
    at_view(app, 'Candidates')
    assert report['model_narrative'] in [item.value for item in app.text]
    at_view(app, 'Agent Trace')
    assert '<img src=x onerror=alert(1)>' in [item.value for item in app.text]
    at_view(app, 'Evidence')
    assert not any('private-marker' in str(item.value) for item in app.json)


# --- Provenance chain -----------------------------------------------------------

REPLAY = _Path(__file__).resolve().parents[1] / 'examples' / 'artifacts' / 'sequence_review.replay.json'


def _replay_artifact():
    return json.loads(REPLAY.read_text(encoding='utf-8'))


def test_provenance_chain_reports_ordered_committed_stages():
    chain = provenance_chain(_replay_artifact(), 'f' * 64)
    stages = [link['stage'] for link in chain]
    assert stages == ['model_inputs', 'score_artifact', 'recorded_tool_result',
                      'replay_export', 'opened_file']
    assert [link['stage'] for link in chain if link['link_verified']] == [
        'score_artifact', 'recorded_tool_result']
    assert chain[1]['digest'] == '63a1c3752407d96a' + chain[1]['digest'][16:]
    # Recorded links retain the source score digest; absent original source bytes
    # and input files do not become authenticated merely by carrying hash strings.
    assert chain[2]['carries_upstream_digest'] == chain[1]['digest']
    assert chain[3]['carries_upstream_digest'] == chain[1]['digest']


def test_provenance_chain_detects_a_broken_commitment():
    artifact = _replay_artifact()
    artifact['trace'][3]['result']['artifact_sha256'] = 'a' * 64
    chain = provenance_chain(artifact, 'f' * 64)
    broken = [link for link in chain if link['mismatch']]
    assert [link['stage'] for link in broken] == ['recorded_tool_result']
    assert broken[0]['mismatch'] is True


def test_provenance_chain_states_it_is_not_a_signed_ledger():
    assert 'not' in PROVENANCE_CHAIN_SCOPE.lower()
    scope = PROVENANCE_CHAIN_SCOPE.lower()
    assert 'signed' in scope or 'anchor' in scope
    chain = provenance_chain(_replay_artifact(), 'f' * 64)
    assert chain[-1]['digest'] == 'f' * 64


def test_provenance_chain_marks_a_missing_stage_rather_than_inventing_one():
    artifact = _replay_artifact()
    del artifact['replay_export']
    chain = provenance_chain(artifact, 'f' * 64)
    export = [link for link in chain if link['stage'] == 'replay_export'][0]
    assert export['digest'] is None and export['link_verified'] is False
    assert export['absent'] is True


def test_whole_viewer_render_path_cannot_reach_a_provider():
    """A refresh, filter change or selection must not be able to spend money.

    Asserts the real import graph of every module on the render path, so the guarantee
    survives future edits instead of resting on convention.
    """
    import ast
    forbidden = {'urllib', 'http', 'requests', 'httpx', 'socket', 'subprocess',
                 'os', 'dotenv', 'modal', 'torch', 'transformers'}
    root = _Path(__file__).resolve().parents[1]
    for relative in ('app/viewer.py', 'app/review_checks.py', 'app/viewer_data.py',
                     'app/viewer_structure.py', 'app/viewer_render.py', 'app/brand.py',
                     'app/upload_checks.py', 'app/core/coordinate_join.py',
                     'app/guided_tour.py', 'app/tour_spotlight.py', 'app/prediction_view.py', 'app/core/atlas_snapshot.py'):
        tree = ast.parse((root / relative).read_text(encoding='utf-8'))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {alias.name.split('.')[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split('.')[0])
        assert not (imported & forbidden), (relative, sorted(imported & forbidden))


def saved_report_with_full_trace():
    """The real recorded shape: three Meta turns alternating with two MCP calls."""
    report=saved_report()
    report['trace']=[
        {'event':'meta_response','finish_reason':'tool_calls','actual_model':'muse-spark-1.3',
         'content_chars':84,'elapsed_seconds':2.124,'task_id':'t1',
         'usage':{'prompt_tokens':1136,'completion_tokens':313,'total_tokens':1449},
         'content':'secret-marker','private_reasoning':'secret-marker'},
        {'event':'mcp_tool','tool':'validate_target_context',
         'arguments':{'reason_brief':'Validate the registered target',
                      'reference_id':'ESTA_BACSU_Nutschel_2020'},
         'result':{'status':'ok'}},
        {'event':'meta_response','finish_reason':'tool_calls','actual_model':'muse-spark-1.3',
         'content_chars':79,'elapsed_seconds':1.493,'task_id':'t2',
         'usage':{'prompt_tokens':1431,'completion_tokens':214,'total_tokens':1645}},
        {'event':'mcp_tool','tool':'score_positions',
         'arguments':{'reason_brief':'Score the approved cohort','positions_1based':[32]},
         'result':{'status':'completed','artifact_sha256':'a'*64}},
        {'event':'meta_response','finish_reason':'stop','actual_model':'muse-spark-1.3',
         'content_chars':313,'elapsed_seconds':2.319,'task_id':'t3',
         'usage':{'prompt_tokens':1341,'completion_tokens':395,'total_tokens':1736}},
    ]
    return report


def test_decision_steps_interleave_meta_turns_with_recorded_tool_calls(tmp_path):
    """The division of labour is the product claim, so both actors must be on screen."""
    view=load_run_view(write(tmp_path,saved_report_with_full_trace()))
    steps=view['decision_steps']
    assert [step['kind'] for step in steps]==['meta_response','mcp_tool','meta_response',
                                              'mcp_tool','meta_response']
    assert [step['step'] for step in steps]==[1,2,3,4,5]
    assert [step['label'] for step in steps[1::2]]==['validate_target_context','score_positions']
    assert steps[0]['finish_reason']=='tool_calls'
    assert steps[4]['finish_reason']=='stop'
    assert steps[0]['actor']!=steps[1]['actor']
    assert steps[1]['reason_brief']=='Validate the registered target'


def test_meta_turns_expose_public_metadata_only(tmp_path):
    """content_chars is a length, never the text; reasoning must never reach the view."""
    view=load_run_view(write(tmp_path,saved_report_with_full_trace()))
    steps=view['decision_steps']
    assert 'secret-marker' not in json.dumps(steps)
    meta=[step for step in steps if step['kind']=='meta_response']
    assert len(meta)==3
    assert meta[0]['usage']=={'completion_tokens':313,'prompt_tokens':1136,'total_tokens':1449}
    assert meta[0]['content_chars']==84
    assert meta[0]['label']=='muse-spark-1.3'
    for step in meta:
        assert 'content' not in step
        assert 'private_reasoning' not in step


def test_tool_events_stay_tool_only_so_recorded_step_numbers_do_not_shift(tmp_path):
    """Regression: the existing tool timeline and its numbering are unchanged."""
    view=load_run_view(write(tmp_path,saved_report_with_full_trace()))
    assert [event['tool'] for event in view['tool_events']]==['validate_target_context',
                                                              'score_positions']
    assert [event['step'] for event in view['tool_events']]==[1,2]
    assert view['tool_calls']==['validate_target_context','score_positions']


def test_uploaded_files_are_checked_locally_and_never_leave_the_machine(tmp_path,monkeypatch):
    """The file-check view lives in the read-only program, so it cannot transmit."""
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    path=write(tmp_path,saved_report())
    monkeypatch.setattr('sys.argv',['viewer.py','--artifact',str(path)])
    app=AppTest.from_file(str(VIEWER_APP),default_timeout=60).run()
    at_view(app,'Input & Diagnostics')
    assert not app.exception
    captions=' '.join(str(c.value) for c in app.caption)
    assert 'Analysed in memory on this machine' in captions
    assert 'is sent to a provider, a GPU or any network service' in captions
    assert 'they predict nothing' in captions
    headings=' '.join(str(m.value) for m in app.markdown)
    assert 'Is this the registered protein?' in headings
    assert 'Does your numbering join to your coordinates?' in headings


def test_the_read_only_program_points_at_the_separate_live_program(tmp_path,monkeypatch):
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    path=write(tmp_path,saved_report())
    monkeypatch.setattr('sys.argv',['viewer.py','--artifact',str(path),
                                    '--session-url','http://127.0.0.1:9999'])
    app=AppTest.from_file(str(VIEWER_APP),default_timeout=60).run()
    assert not app.exception
    text=' '.join(str(c.value) for c in app.html)
    assert 'http://127.0.0.1:9999' in text
    assert 'New Review' in text
