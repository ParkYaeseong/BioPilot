"""Synthetic final-report continuation receipts, never actual Meta evidence."""
from copy import deepcopy
import json

import pytest

from app.core.artifacts import ArtifactStore
from app.core.runs import RunService
from app.core.targets import registered_profile, validate_target
from app.host.final_report import prepare_final_report, generate_final_report
from app.host.meta_client import MetaClient, MODEL
from app.science.ranking import rank_candidates
from tests_app.test_meta_loop import synthetic_score_artifact, response


class Client:
    source_mode='synthetic_fixture'
    max_output_tokens=1024
    def __init__(self, replies):
        self.replies=iter(replies)
        self.payloads=[]
    def complete(self,payload):
        self.payloads.append(deepcopy(payload))
        result=next(self.replies)
        if isinstance(result,Exception): raise result
        return result


def source(tmp_path,*,alter=None):
    runs=RunService(tmp_path/'runs.sqlite')
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
    if alter: alter(content)
    store=ArtifactStore(tmp_path/'artifacts',runs)
    path=store.save(source_run,'local',content)
    return runs,store,source_run,path.stem,path,artifact


def prepare(tmp_path):
    runs,store,source_run,source_id,path,artifact=source(tmp_path)
    plan=prepare_final_report(runs,store,source_run,source_id,'local')
    return plan,runs,store,source_run,source_id,path,artifact


def test_prepare_is_reviewable_one_call_plan_without_approval_or_network(tmp_path):
    plan,runs,store,source_run,source_id,path,artifact=prepare(tmp_path)
    assert plan['run_id']!=source_run
    assert plan['source_artifact_id']==source_id
    assert plan['source_score_artifact_sha256']==artifact['artifact_sha256']
    assert plan['max_meta_requests']==1
    assert plan['usd_micros']==50000
    assert plan['payload']['max_completion_tokens']==1024
    assert 'tools' not in plan['payload']
    assert len(json.dumps(plan['payload']).encode('utf-8'))<=16384
    assert runs.get(plan['run_id'],'local')['state']=='AWAITING_APPROVAL'
    assert runs.get(plan['run_id'],'local')['tasks']==[]


def test_default_blocked_does_not_read_client_or_dispatch(tmp_path):
    plan,runs,store,*_=prepare(tmp_path)
    client=Client([])
    result=generate_final_report(client,runs,store,plan['run_id'],'local')
    assert result['status']=='blocked'
    assert result['meta_request_attempts']==0
    assert client.payloads==[]
    assert runs.get(plan['run_id'],'local')['tasks']==[]


def test_single_final_report_preserves_original_and_links_exact_source_ids(tmp_path):
    plan,runs,store,source_run,source_id,path,artifact=prepare(tmp_path)
    original_bytes=path.read_bytes()
    reply=response(text='These are sequence preferences. T50 and activity remain unknown.')
    reply['choices'][0]['message']['reasoning_content']='private never persist'
    reply['private_metadata']='private never persist'
    client=Client([reply])
    result=generate_final_report(client,runs,store,plan['run_id'],'local',approved=True)
    assert result['status']=='final_report_complete'
    assert result['finish_reason']=='stop'
    assert result['actual_model']==MODEL
    assert result['meta_request_attempts']==1
    assert result['source_run_id']==source_run
    assert result['source_artifact_id']==source_id
    assert result['evidence_ids']==[source_id,artifact['artifact_sha256']]
    assert result['actual_cost_micros'] is None
    assert result['biological_efficacy_established'] is False
    assert result['candidates']==rank_candidates(artifact['rows'])
    assert path.read_bytes()==original_bytes
    assert client.payloads[0]['max_completion_tokens']==1024
    assert 'tools' not in client.payloads[0]
    assert 'private never persist' not in json.dumps(result)
    assert 'artifact_id' in result
    saved=store.load(plan['run_id'],'local',result['artifact_id'])
    assert saved['source_artifact_id']==source_id
    assert 'private never persist' not in json.dumps(saved)


def test_continuation_cannot_be_redispatched_after_success_or_timeout(tmp_path):
    plan,runs,store,*_=prepare(tmp_path)
    client=Client([TimeoutError('private error details')])
    first=generate_final_report(client,runs,store,plan['run_id'],'local',approved=True)
    again=generate_final_report(client,runs,store,plan['run_id'],'local',approved=True)
    assert first['status']=='partial'
    assert first['stop_reason']=='provider_outcome_unknown_no_retry'
    assert again['status']=='blocked'
    assert len(client.payloads)==1
    assert 'private error details' not in json.dumps(first)
    assert runs.get(plan['run_id'],'local')['tasks'][0]['status']=='UNKNOWN'


def test_length_reason_is_preserved_without_claiming_complete_or_retrying(tmp_path):
    plan,runs,store,*_=prepare(tmp_path)
    reply=response(text='Partial public explanation.')
    reply['choices'][0]['finish_reason']='length'
    reply['usage']={'prompt_tokens':100,'completion_tokens':1024,'total_tokens':1124}
    client=Client([reply])
    result=generate_final_report(client,runs,store,plan['run_id'],'local',approved=True)
    assert result['status']=='partial'
    assert result['finish_reason']=='length'
    assert result['usage']['completion_tokens']==1024
    assert result['model_narrative']=='Partial public explanation.'
    assert len(client.payloads)==1


@pytest.mark.parametrize('kind',['foreign','source_hash','score_hash','missing_validation','wrong_score_link','ranks'])
def test_bad_owned_source_or_scientific_provenance_blocked_before_client(tmp_path,kind):
    def alter(content):
        if kind=='score_hash': content['score_artifacts'][0]['artifact_sha256']='0'*64
        if kind=='missing_validation': content['trace']=content['trace'][1:]
        if kind=='wrong_score_link': content['trace'][-1]['result']['artifact_sha256']='0'*64
        if kind=='ranks': content['candidates'][0]['score']=999999
    runs,store,source_run,source_id,path,artifact=source(tmp_path,alter=alter)
    if kind=='source_hash':
        document=json.loads(path.read_text());document['content']['status']='changed'
        path.write_text(json.dumps(document))
    with pytest.raises((ValueError,PermissionError)):
        prepare_final_report(runs,store,source_run,source_id,'foreign' if kind=='foreign' else 'local')


def test_final_model_cannot_call_tools_or_switch_provider(tmp_path):
    plan,runs,store,*_=prepare(tmp_path)
    reply=response(text='Not accepted',model='some-other-model')
    client=Client([reply])
    result=generate_final_report(client,runs,store,plan['run_id'],'local',approved=True)
    assert result['status']=='partial'
    assert result['actual_model'] is None
    assert len(client.payloads)==1


def test_live_client_default_cap_stays512_and1024_is_explicit(monkeypatch):
    from app.host import meta_client
    reads=[]
    def forbidden(*a,**kw):
        reads.append(True)
        raise AssertionError('No real secrets/network allowed')
    monkeypatch.setattr(meta_client.os.environ,'get',forbidden)
    request={'model':MODEL,'messages':[],'stream':False,'max_completion_tokens':1024}
    with pytest.raises(ValueError,match='contract|cap'):
        MetaClient(live=True).complete(request)
    assert not reads
    assert MetaClient(max_output_tokens=1024).max_output_tokens==1024
    assert MetaClient().max_output_tokens==512
    for invalid in (True,513,2048,0):
        with pytest.raises(ValueError): MetaClient(max_output_tokens=invalid)
