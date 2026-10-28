"""Launcher entry point for the opt-in one-call final report. No network here."""
import json
from pathlib import Path
import subprocess
import sys

from app.core.artifacts import ArtifactStore
from app.core.runs import RunService
from app.core.targets import registered_profile, validate_target
from app.host.meta_client import MODEL
from app.science.ranking import rank_candidates
from tests_app.test_meta_loop import synthetic_score_artifact

ROOT=Path(__file__).resolve().parents[1]

def run(*args):
    return subprocess.run([sys.executable,'-m','app.cli',*map(str,args)],cwd=ROOT,
                          capture_output=True,text=True,timeout=60)

def workspace_with_partial_review(tmp_path):
    """Build an owned partial sequence review exactly as the launcher would find it."""
    workspace=tmp_path/'continuation'
    (workspace/'state').mkdir(parents=True)
    runs=RunService(workspace/'state/runs.sqlite')
    target=validate_target(registered_profile(),'sequence_plausibility_review')
    source_run=runs.create({**target.summary(),'objective_profile_id':target.objective_id,
        'esm_model_key':'esm150','positions_1based':[32],
        'model_pins':{'esm150':{'expected_weights_sha256':'a'*64,'expected_tokenizer_sha256':'b'*64}},
        'requested_budget':{'usd_micros':150000,'max_meta_requests':3}},'local')
    artifact=synthetic_score_artifact()
    content={'run_id':source_run,'workflow':'sequence_review','status':'partial',
        'actual_model':MODEL,'source_mode':'synthetic_fixture',
        'scientific_scope':'unvalidated_sequence_evidence_assistant','biological_efficacy_established':False,
        'score_artifacts':[artifact],'candidates':rank_candidates(artifact['rows']),
        'trace':[{'event':'mcp_tool','tool':'validate_target_context','call_id':'validate-original',
                  'result':{'status':'ok'}},
                 {'event':'mcp_tool','tool':'score_positions','call_id':'score-original',
                  'result':{'status':'completed','artifact_sha256':artifact['artifact_sha256']}}]}
    path=ArtifactStore(workspace/'artifacts',runs).save(source_run,'local',content)
    (workspace/'launcher.json').write_text(json.dumps({'status':'prepared','run_id':source_run,
        'owner_id':'local','reference_id':target.reference_id,'bundle_sha256':'c'*64,
        'os_sandbox_verified':False,'external_request_attempts':0},indent=2),encoding='utf-8')
    return workspace,path.stem,artifact


def test_prepare_writes_reviewable_plan_receipt_without_any_request(tmp_path):
    workspace,source_artifact_id,artifact=workspace_with_partial_review(tmp_path)
    result=run('final-report','--workspace',workspace,'--source-artifact-id',source_artifact_id,'--prepare')
    assert result.returncode==0,result.stderr
    output=json.loads(result.stdout)
    assert output['status']=='awaiting_approval'
    assert output['external_request_attempts']==0
    assert output['max_meta_requests']==1
    assert output['usd_micros']==50000
    assert output['max_completion_tokens']==1024
    assert output['source_artifact_id']==source_artifact_id
    assert output['source_score_artifact_sha256']==artifact['artifact_sha256']
    assert 0<output['request_body_bytes']<=16384
    assert 'payload' not in output
    receipt=json.loads((workspace/'final_report_plan.json').read_text(encoding='utf-8'))
    assert receipt['request_sha256']==output['request_sha256']
    assert receipt['continuation_run_id']==output['continuation_run_id']


def test_prepare_refuses_to_overwrite_an_existing_plan_receipt(tmp_path):
    workspace,source_artifact_id,_=workspace_with_partial_review(tmp_path)
    first=run('final-report','--workspace',workspace,'--source-artifact-id',source_artifact_id,'--prepare')
    assert first.returncode==0,first.stderr
    original=(workspace/'final_report_plan.json').read_bytes()
    second=run('final-report','--workspace',workspace,'--source-artifact-id',source_artifact_id,'--prepare')
    assert second.returncode==2
    assert json.loads(second.stdout)['status']=='blocked'
    assert (workspace/'final_report_plan.json').read_bytes()==original


def test_execution_is_blocked_without_both_explicit_single_report_flags(tmp_path):
    workspace,source_artifact_id,_=workspace_with_partial_review(tmp_path)
    prepared=run('final-report','--workspace',workspace,'--source-artifact-id',source_artifact_id,'--prepare')
    continuation=json.loads(prepared.stdout)['continuation_run_id']
    for flags in ([], ['--live'], ['--ack-single-report']):
        result=run('final-report','--workspace',workspace,'--continuation-run-id',continuation,*flags)
        assert result.returncode==2
        output=json.loads(result.stdout)
        assert output['status']=='blocked'
        assert 'approval' in output['reason']
        state=RunService(workspace/'state/runs.sqlite').get(continuation,'local')
        assert state['tasks']==[]


def test_unknown_continuation_run_is_refused_before_any_credential_or_request(tmp_path):
    workspace,source_artifact_id,_=workspace_with_partial_review(tmp_path)
    run('final-report','--workspace',workspace,'--source-artifact-id',source_artifact_id,'--prepare')
    result=run('final-report','--workspace',workspace,'--continuation-run-id','0'*32,
               '--live','--ack-single-report')
    assert result.returncode==2
    assert json.loads(result.stdout)['status']=='blocked'
