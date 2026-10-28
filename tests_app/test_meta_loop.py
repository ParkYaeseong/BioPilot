import asyncio
import json
import pytest
from app.core.runs import RunService
from app.core.targets import registered_profile, validate_target
from app.host.meta_client import MetaClient, MetaHost

class Bridge:
    def __init__(self): self.calls=[]
    async def list_allowed(self):
        return [{'name':'validate_target_context','description':'Validate registered context',
                 'inputSchema':{'type':'object','properties':{'reference_id':{'const':'ESTA_BACSU_Nutschel_2020'},
                 'reason_brief':{'type':'string'}},'required':['reference_id','reason_brief'],'additionalProperties':False}}]
    async def call(self, name, arguments):
        self.calls.append((name,arguments))
        return {'status':'ok','coordinate_mapping_verified':False,'phenotype_calibrated':False}

class Client:
    source_mode='synthetic_fixture'
    def __init__(self, responses): self.responses=iter(responses); self.payloads=[]
    def complete(self,payload):
        self.payloads.append(payload)
        response=next(self.responses)
        if isinstance(response,Exception): raise response
        return response

def response(*, call=None, text=None, model='muse-spark-1.3'):
    message={'role':'assistant','content':text}
    if call is not None: message['tool_calls']=call
    return {'id':'fixture-response','model':model,'choices':[{'message':message,
        'finish_reason':'tool_calls' if call else 'stop'}],
        'usage':{'prompt_tokens':10,'completion_tokens':5,'total_tokens':15}}

def tool(name='validate_target_context',id='call-1',args=None):
    return {'id':id,'type':'function','function':{'name':name,'arguments':json.dumps(args or {
        'reference_id':'ESTA_BACSU_Nutschel_2020','reason_brief':'Check registered full frame'})}}

def setup(tmp_path,client,bridge=None):
    runs=RunService(tmp_path/'runs.sqlite')
    target=validate_target(registered_profile(),'sequence_plausibility_review')
    rid=runs.create({**target.summary(),'objective_profile_id':target.objective_id,
        'requested_budget':{'usd_micros':100000,'max_meta_requests':2}},'local')
    state=runs.get(rid,'local');runs.approve(rid,state['plan_digest'],1,'local')
    bridge=bridge or Bridge()
    return MetaHost(client,bridge,runs,rid,'local'),runs,rid,bridge

def test_exact_call_ids_and_no_tool_final_report(tmp_path):
    client=Client([response(call=[tool()]),response(text='Sequence mapping verified; ESM unavailable.')])
    host,runs,rid,bridge=setup(tmp_path,client)
    report=asyncio.run(host.run())
    assert report['source_mode']=='synthetic_fixture'
    assert report['actual_model']=='muse-spark-1.3'
    assert report['meta_request_attempts']==2
    assert report['actual_cost_micros'] is None
    assert len(bridge.calls)==1
    messages=client.payloads[1]['messages']
    assert messages[-1]['tool_call_id']=='call-1'
    assert client.payloads[1].get('tools') is None
    assert report['biological_efficacy_established'] is False

@pytest.mark.parametrize('calls',[[tool(name='read_file')],[tool(args={'owner_id':'foreign'})],
                                  [tool(),tool(id='call-1')]])
def test_unknown_schema_or_duplicate_call_rejected(tmp_path,calls):
    client=Client([response(call=calls)])
    host,runs,rid,bridge=setup(tmp_path,client)
    report=asyncio.run(host.run())
    assert report['status']=='partial'
    assert bridge.calls==[]
    assert len(client.payloads)==1

def test_timeout_is_not_retried_or_redispatched_after_restart(tmp_path):
    client=Client([TimeoutError('private provider details')])
    host,runs,rid,bridge=setup(tmp_path,client)
    first=asyncio.run(host.run())
    second=asyncio.run(host.run())
    assert first['status']==second['status']=='partial'
    assert len(client.payloads)==1
    assert runs.get(rid,'local')['tasks'][0]['status']=='UNKNOWN'
    assert 'private provider details' not in json.dumps(first)

def test_no_alternate_model_fallback(tmp_path):
    client=Client([response(text='hello',model='another-model')])
    host,runs,rid,bridge=setup(tmp_path,client)
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    assert len(client.payloads)==1

def test_live_client_blocks_before_secret_or_network():
    with pytest.raises(ValueError,match='approval|live'):
        MetaClient(live=False).complete({})

def test_meta_key_alias_is_read_locally_without_env_forwarding(tmp_path,monkeypatch):
    from app.host import meta_client
    monkeypatch.delenv('MODEL_API_KEY',raising=False)
    monkeypatch.delenv('META_API_KEY',raising=False)
    path=tmp_path/'.env';path.write_text('META_API_KEY=synthetic-fixture-key\nESM_BACKEND=modal\n')
    class Reply:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self,limit): return json.dumps(response(text='ready')).encode()
    class Opener:
        def open(self,request,timeout):
            assert request.get_header('Authorization')=='Bearer synthetic-fixture-key'
            assert 'synthetic-fixture-key' not in request.data.decode()
            assert 'ESM_BACKEND' not in request.data.decode()
            return Reply()
    monkeypatch.setattr(meta_client,'build_opener',lambda *args:Opener())
    result=MetaClient(env_file=path,live=True).complete({'model':'muse-spark-1.3','messages':[],
            'stream':False,'max_completion_tokens':128})
    assert result['model']=='muse-spark-1.3'

def test_product_context_has_no_labels_paths_or_raw_sequence(tmp_path):
    client=Client([response(text='No scores available.')])
    host,runs,rid,bridge=setup(tmp_path,client)
    asyncio.run(host.run())
    encoded=json.dumps(client.payloads)
    for forbidden in ['evaluation_private','DMS_score','assay_protocol.json',registered_profile()['reference_sequence']]:
        assert forbidden not in encoded

def test_final_tool_attempt_is_not_dispatched(tmp_path):
    client=Client([response(call=[tool()]),response(call=[tool(id='call-2')])])
    host,runs,rid,bridge=setup(tmp_path,client)
    result=asyncio.run(host.run())
    assert len(bridge.calls)==1
    assert result['status']=='partial'

def test_report_reserve_is_preserved_when_budget_allows_only_one_request(tmp_path):
    client=Client([response(call=[tool()])])
    host,runs,rid,bridge=setup(tmp_path,client)
    runs.set_budget(rid,'local',usd_micros=100000,max_meta_requests=1)
    state=runs.get(rid,'local');runs.approve(rid,state['plan_digest'],state['budget_version'],'local')
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    assert result['stop_reason']=='budget_or_approval_blocked'
    assert len(client.payloads)==0

def test_missing_usage_is_unknown_without_crash(tmp_path):
    value=response(text='Validation incomplete.');value['usage']=None
    host,runs,rid,bridge=setup(tmp_path,Client([value]))
    result=asyncio.run(host.run())
    assert result['usage'][0]['total_tokens'] is None

def test_rejected_tool_does_not_become_completed_validation(tmp_path):
    class BlockedBridge(Bridge):
        async def call(self,name,arguments):
            return {'status':'blocked','code':'invalid_session_or_target'}
    client=Client([response(call=[tool()]),response(text='All validated.')])
    host,runs,rid,bridge=setup(tmp_path,client,BlockedBridge())
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    assert result['stop_reason']=='server_rejected_tool'
    assert len(client.payloads)==1


def synthetic_score_artifact(model_key='esm150'):
    from app.science.esm_engine import ESMEngine
    from app.science.models import get_model_spec
    alphabet='ACDEFGHIKLMNPQRSTVWY'
    class Backend:
        mask_token_id=22
        provenance={'checkpoint':get_model_spec(model_key).checkpoint,
                    'weights_sha256':'a'*64,'tokenizer_sha256':'b'*64,
                    'implementation':'synthetic_fixture_v1','precision':'float32',
                    'source_mode':'synthetic_fixture'}
        def token_id(self, aa): return alphabet.index(aa)+1
        def tokenize(self, sequence): return [0]+[self.token_id(aa) for aa in sequence]+[21]
        def forward(self, tokens): return [[float(v) for v in range(23)] for _ in tokens]
    target=validate_target(registered_profile(),'sequence_plausibility_review')
    return ESMEngine(Backend()).score_positions(target,[32],model_key)


def score_tool(*, id='score-1', model_key='esm150', positions=None):
    return tool('score_positions',id,{'reference_id':'ESTA_BACSU_Nutschel_2020',
        'model_key':model_key,'positions_1based':[32] if positions is None else positions,
        'reason_brief':'Review registered sequence preferences with the approved model'})


class ReviewBridge(Bridge):
    def __init__(self, score_result=None):
        super().__init__()
        self.score_result=score_result or {'status':'completed','artifact':synthetic_score_artifact(),
                                         'cost_micros':None,'cost_status':'unknown'}
    async def list_allowed(self):
        tools=await super().list_allowed()
        tools.append({'name':'score_positions','description':'Score approved full-reference positions',
            'inputSchema':{'type':'object','properties':{
                'reference_id':{'type':'string'},'model_key':{'enum':['esm35','esm150','esm650']},
                'positions_1based':{'type':'array','items':{'type':'integer'},'minItems':1,'maxItems':10,'uniqueItems':True},
                'reason_brief':{'type':'string','minLength':1,'maxLength':400}},
                'required':['reference_id','model_key','positions_1based','reason_brief'],'additionalProperties':False}})
        return tools
    async def call(self,name,arguments):
        self.calls.append((name,arguments))
        if name=='score_positions': return self.score_result
        return {'status':'ok','coordinate_mapping_verified':False,'phenotype_calibrated':False}


def setup_review(tmp_path,client,bridge=None,*,max_requests=4,micros=250000,model_key='esm150',positions=None,
                 final_report_tokens=None):
    runs=RunService(tmp_path/'review.sqlite')
    target=validate_target(registered_profile(),'sequence_plausibility_review')
    rid=runs.create({**target.summary(),'objective_profile_id':target.objective_id,
        'esm_model_key':model_key,'positions_1based':[32] if positions is None else positions,
        'model_pins':{model_key:{'expected_weights_sha256':'a'*64,'expected_tokenizer_sha256':'b'*64}},
        'requested_budget':{'usd_micros':micros,'max_meta_requests':max_requests}},'local')
    state=runs.get(rid,'local');runs.approve(rid,state['plan_digest'],1,'local')
    bridge=bridge or ReviewBridge()
    extra={} if final_report_tokens is None else {'final_report_tokens':final_report_tokens}
    host=MetaHost(client,bridge,runs,rid,'local',workflow='sequence_review',**extra)
    return host,runs,rid,bridge


def test_sequence_review_three_turns_code_ranks_artifact_and_final_has_no_tools(tmp_path):
    client=Client([response(call=[tool()]),response(call=[score_tool()]),
                   response(text='Sequence preferences only; T50 and activity remain unknown.')])
    host,runs,rid,bridge=setup_review(tmp_path,client)
    result=asyncio.run(host.run())
    assert result['status']=='sequence_review_complete'
    assert result['source_mode']=='synthetic_fixture'
    assert result['scientific_scope']=='unvalidated_sequence_evidence_assistant'
    assert result['biological_efficacy_established'] is False
    assert result['actual_cost_micros'] is None
    assert result['meta_request_attempts']==3
    assert len(result['score_artifacts'])==1
    assert len(result['candidates'])==19
    assert result['candidates'][0]['score']>=result['candidates'][-1]['score']
    assert [name for name,args in bridge.calls]==['validate_target_context','score_positions']
    assert client.payloads[2].get('tools') is None
    # The score result must still reach the final turn, which now ends with its own
    # report instruction rather than the tool message.
    assert [m for m in client.payloads[2]['messages'] if m.get('role')=='tool'][-1]['tool_call_id']=='score-1'
    assert client.payloads[2]['messages'][-1]['role']=='developer'
    assert client.payloads[1]['messages'][-1]['tool_call_id']=='call-1'
    assert 'model_narrative' in result
    assert result['ranking_scope']=='esm150_masked_v1'
    for forbidden in ('evaluation_private','DMS_score',registered_profile()['reference_sequence'],'ESM_BACKEND','MODEL_API_KEY'):
        assert forbidden not in json.dumps(client.payloads)


@pytest.mark.parametrize('status',['pending','unknown','reserved'])
def test_sequence_pending_returns_partial_without_model_poll_or_duplicate_dispatch(tmp_path,status):
    bridge=ReviewBridge({'status':status,'task_id':'fixture-job','cost_micros':None})
    client=Client([response(call=[tool()]),response(call=[score_tool()])])
    host,runs,rid,bridge=setup_review(tmp_path,client,bridge)
    first=asyncio.run(host.run())
    second=asyncio.run(host.run())
    assert first['status']==second['status']=='partial'
    assert first['stop_reason']==f'esm_{status}'
    assert len(client.payloads)==2
    assert len(bridge.calls)==2
    assert first['candidates']==[]


@pytest.mark.parametrize('max_requests,micros',[(2,250000),(3,100000)])
def test_sequence_review_preserves_report_request_and_cost_reserve(tmp_path,max_requests,micros):
    client=Client([])
    host,runs,rid,bridge=setup_review(tmp_path,client,max_requests=max_requests,micros=micros)
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    assert result['stop_reason']=='budget_or_approval_blocked'
    assert client.payloads==[] and bridge.calls==[]


def test_score_cannot_run_before_validation(tmp_path):
    client=Client([response(call=[score_tool()])])
    host,runs,rid,bridge=setup_review(tmp_path,client)
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    assert bridge.calls==[]


@pytest.mark.parametrize('call',[score_tool(model_key='esm650'),score_tool(positions=[33]),score_tool(id='call-1')])
def test_sequence_model_cannot_change_frozen_model_cohort_or_reuse_call_id(tmp_path,call):
    client=Client([response(call=[tool()]),response(call=[call])])
    host,runs,rid,bridge=setup_review(tmp_path,client)
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    assert len(bridge.calls)==1


@pytest.mark.parametrize('corruption',['hash','mixed_checkpoint','incomplete'])
def test_sequence_review_rejects_invalid_or_mixed_artifact_before_final_model(tmp_path,corruption):
    from app.host.meta_client import _hash
    artifact=synthetic_score_artifact()
    if corruption=='hash': artifact['artifact_sha256']='0'*64
    else:
        if corruption=='mixed_checkpoint': artifact['rows'][0]['checkpoint']='esm2_t33_650M_UR50D'
        else: artifact['rows'].pop()
        artifact['artifact_sha256']=_hash({k:v for k,v in artifact.items() if k!='artifact_sha256'})
    client=Client([response(call=[tool()]),response(call=[score_tool()])])
    host,runs,rid,bridge=setup_review(tmp_path,client,ReviewBridge({'status':'completed','artifact':artifact}))
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    assert result['candidates']==[]
    assert len(client.payloads)==2


def test_sequence_final_tool_call_is_not_dispatched(tmp_path):
    client=Client([response(call=[tool()]),response(call=[score_tool()]),response(call=[tool(id='last')])])
    host,runs,rid,bridge=setup_review(tmp_path,client)
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    assert len(bridge.calls)==2


def test_no_tool_sequence_narrative_cannot_become_complete(tmp_path):
    client=Client([response(text='Everything is complete.')])
    host,runs,rid,bridge=setup_review(tmp_path,client)
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    assert not result['candidates']
    assert len(client.payloads)==1


def test_unknown_workflow_is_rejected(tmp_path):
    host,runs,rid,bridge=setup(tmp_path,Client([]))
    with pytest.raises(ValueError,match='workflow'):
        MetaHost(host.client,bridge,runs,rid,'local',workflow='arbitrary_agent')


def test_sequence_holds_final_reserve_before_scoring_dispatch(tmp_path):
    client=Client([response(call=[tool()]),response(call=[score_tool()]),response(text='Unknown phenotype.')])
    host,runs,rid,bridge=setup_review(tmp_path,client)
    original=bridge.call
    async def inspect_reserve(name,arguments):
        if name=='score_positions':
            state=runs.get(rid,'local')
            pending=[task for task in state['tasks'] if task['status']=='RESERVED']
            assert len(pending)==1
            assert pending[0]['estimate_micros']==50000
            assert pending[0]['kind']=='meta'
        return await original(name,arguments)
    bridge.call=inspect_reserve
    assert asyncio.run(host.run())['status']=='sequence_review_complete'


def test_sequence_ceiling_keeps_last_request_tool_free(tmp_path):
    class StatusBridge(ReviewBridge):
        async def list_allowed(self):
            return await super().list_allowed()+[{'name':'get_run_status','description':'Bound run status',
                'inputSchema':{'type':'object','properties':{},'required':[],'additionalProperties':False}}]
    def status_call(cid):
        return {'id':cid,'type':'function','function':{'name':'get_run_status','arguments':'{}'}}
    client=Client([response(call=[tool()]),response(call=[status_call('status-1')]),
                   response(call=[status_call('status-2')]),response(text='Scores are unavailable.')])
    host,runs,rid,bridge=setup_review(tmp_path,client,StatusBridge(),max_requests=4)
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    assert result['meta_request_attempts']==4
    assert client.payloads[-1].get('tools') is None
    assert len(bridge.calls)==3


def test_sequence_narrative_does_not_write_numerical_candidates(tmp_path):
    client=Client([response(call=[tool()]),response(call=[score_tool()]),
                   response(text='Unverified narrative number: 999999.')])
    host,runs,rid,bridge=setup_review(tmp_path,client)
    result=asyncio.run(host.run())
    assert result['status']=='sequence_review_complete'
    assert all(row['score']!=999999 for row in result['candidates'])
    assert result['candidates']==sorted(result['score_artifacts'][0]['rows'],key=lambda r:(-r['score'],r['candidate_id']))


def test_sequence_timeout_and_model_mismatch_never_fall_back(tmp_path):
    client=Client([TimeoutError('private details')])
    host,runs,rid,bridge=setup_review(tmp_path,client)
    first=asyncio.run(host.run());second=asyncio.run(host.run())
    assert first['status']==second['status']=='partial'
    assert len(client.payloads)==1
    assert 'private details' not in json.dumps(first)
    assert any(task['status']=='UNKNOWN' for task in runs.get(rid,'local')['tasks'])


def test_sequence_rejects_raw_environment_or_backend_arguments(tmp_path):
    call=score_tool()
    arguments=json.loads(call['function']['arguments']);arguments['backend']='runpod'
    call['function']['arguments']=json.dumps(arguments)
    client=Client([response(call=[tool()]),response(call=[call])])
    host,runs,rid,bridge=setup_review(tmp_path,client)
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    assert len(bridge.calls)==1


@pytest.mark.parametrize('pins',[None,[],{'esm150':None}])
def test_invalid_review_pins_fail_before_provider_or_tool_calls(tmp_path,pins):
    client=Client([])
    host,runs,rid,bridge=setup_review(tmp_path,client)
    original=runs.get
    def altered(run_id,owner_id):
        state=original(run_id,owner_id)
        state['input']['model_pins']=pins
        return state
    runs.get=altered
    with pytest.raises(ValueError):
        asyncio.run(host.run())
    assert client.payloads==[] and bridge.calls==[]


def test_oversized_meta_request_is_blocked_before_secret_or_network(monkeypatch):
    from app.host import meta_client
    accessed=[]
    def forbidden_secret(*args,**kwargs):
        accessed.append('secret')
        raise AssertionError('Secrets must not be read for an oversized body')
    def forbidden_network(*args,**kwargs):
        accessed.append('network')
        raise AssertionError('Network must not be accessed for an oversized body')
    monkeypatch.setattr(meta_client.os.environ,'get',forbidden_secret)
    monkeypatch.setattr(meta_client,'build_opener',forbidden_network)
    payload={'model':'muse-spark-1.3','stream':False,'max_completion_tokens':512,
             'messages':[{'role':'user','content':'A'*20000}]}
    with pytest.raises(ValueError,match='body|byte|size'):
        MetaClient(live=True).complete(payload)
    assert accessed==[]


def test_request_guard_measures_serialized_utf8_body_and_uses_it_once(monkeypatch):
    from app.host import meta_client
    monkeypatch.setenv('MODEL_API_KEY','synthetic-fixture-key')
    sent=[]
    class Reply:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self,limit): return json.dumps(response(text='ready')).encode()
    class Opener:
        def open(self,request,timeout):
            sent.append(request.data)
            return Reply()
    monkeypatch.setattr(meta_client,'build_opener',lambda *args:Opener())
    payload={'model':'muse-spark-1.3','stream':False,'max_completion_tokens':512,
             'messages':[{'role':'user','content':'public Korean text: 확인'}]}
    MetaClient(live=True).complete(payload)
    assert len(sent)==1
    assert json.loads(sent[0])==payload
    assert len(sent[0])<=meta_client.MAX_REQUEST_BYTES
    payload['messages'][0]['content']='가'*10000
    with pytest.raises(ValueError,match='body|byte|size'):
        MetaClient(live=True).complete(payload)
    assert len(sent)==1


@pytest.mark.parametrize('review',[False,True])
def test_model_tool_call_extra_metadata_is_not_replayed_or_persisted(tmp_path,review):
    first=tool()
    first['reasoning_content']='private-extra-metadata'
    first['unrecognized']={'opaque':'private-extra-metadata'}
    first['function']['reasoning_content']='private-extra-metadata'
    if review:
        client=Client([response(call=[first]),response(call=[score_tool()]),response(text='Unknown phenotype.')])
        host,runs,rid,bridge=setup_review(tmp_path,client)
    else:
        client=Client([response(call=[first]),response(text='Unknown phenotype.')])
        host,runs,rid,bridge=setup(tmp_path,client)
    report=asyncio.run(host.run())
    assert 'private-extra-metadata' not in json.dumps(client.payloads)
    assert 'private-extra-metadata' not in json.dumps(report)
    replayed=client.payloads[1]['messages'][-2]['tool_calls'][0]
    assert set(replayed)=={'id','type','function'}
    assert set(replayed['function'])=={'name','arguments'}
    assert replayed['id']=='call-1'
    assert client.payloads[1]['messages'][-1]['tool_call_id']=='call-1'


@pytest.mark.parametrize('review',[False,True])
def test_local_body_rejection_is_not_an_unknown_provider_charge(tmp_path,review):
    from app.host.meta_client import RequestBodyLimitError
    client=Client([RequestBodyLimitError('local oversized body')])
    host,runs,rid,bridge=setup_review(tmp_path,client) if review else setup(tmp_path,client)
    result=asyncio.run(host.run())
    assert result['status']=='partial'
    assert result['stop_reason']=='local_request_body_limit_no_network'
    assert result['meta_request_attempts']==0
    tasks=runs.get(rid,'local')['tasks']
    assert not any(task['status']=='UNKNOWN' for task in tasks)
    settled=[task for task in tasks if task['status']=='SETTLED']
    assert len(settled)==1 and settled[0]['actual_micros']==0
    assert bridge.calls==[]


@pytest.mark.parametrize('review',[False,True])
def test_future_meta_trace_keeps_public_finish_reason_on_invalid_final_output(tmp_path,review):
    final=response(text=None)
    final['choices'][0]['finish_reason']='length'
    final['choices'][0]['message']['reasoning_content']='private never record'
    replies=[response(call=[tool()])]
    if review: replies.append(response(call=[score_tool()]))
    replies.append(final)
    client=Client(replies)
    host,runs,rid,bridge=setup_review(tmp_path,client) if review else setup(tmp_path,client)
    report=asyncio.run(host.run())
    assert report['status']=='partial'
    events=[event for event in report['trace'] if event['event']=='meta_response']
    assert events[-1]['finish_reason']=='length'
    assert 'private never record' not in json.dumps(report)
