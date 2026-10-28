"""Synthetic provider responses exercise isolation and durable dispatch only."""
from dataclasses import replace
from copy import deepcopy
import json
import pytest

from app.core.runs import RunService
from app.core.targets import REFERENCE_ID, REFERENCE_SHA256, registered_profile, validate_target
from app.core.tool_executor import SessionContext, ToolExecutor
from app.science.esm_engine import ESMEngine
from app.science.providers import (InferenceRequest, Submission, LocalESMProvider,
    ModalESMProvider, RunPodESMProvider, UnconfiguredBackendError, canonical_digest, ProviderError)
from app.science.inference_service import InferenceService, validate_score_artifact

AA = 'ACDEFGHIKLMNPQRSTVWY'

def request(**changes):
    data = dict(reference_id=REFERENCE_ID, reference_sha256=REFERENCE_SHA256,
        reference_numbering='full_reference_1based', sequence_context='full_212',
        positions=(32,), model_key='esm150', expected_weights_sha256='a'*64,
        expected_tokenizer_sha256='b'*64)
    return InferenceRequest(**{**data, **changes})

class SyntheticBackend:
    mask_token_id = 22
    provenance = {'checkpoint':'esm2_t30_150M_UR50D', 'weights_sha256':'a'*64,
        'tokenizer_sha256':'b'*64, 'implementation':'fixture', 'precision':'float32',
        'source_mode':'synthetic_fixture'}
    def tokenize(self, sequence):
        return [0] + [self.token_id(aa) for aa in sequence] + [21]
    def token_id(self, aa):
        return AA.index(aa)+1
    def forward(self, tokens):
        return [[float(i) for i in range(23)] for _ in tokens]

def artifact():
    return ESMEngine(SyntheticBackend()).score_positions(
        validate_target(registered_profile(), 'sequence_plausibility_review'), [32])

class FakeTransport:
    def __init__(self):
        self.submits = []
        self.polls = []
        self.pending = True
    def spawn(self, app_name, function_name, environment, payload):
        self.submits.append((app_name, function_name, environment, payload))
        return 'fc-fixture-1'
    def get(self, job_id, timeout_seconds):
        self.polls.append((job_id, timeout_seconds))
        if self.pending:
            raise TimeoutError()
        return artifact()

CONFIG = {'ESM_BACKEND':'modal', 'MODAL_APP_NAME':'fixture-app',
    'MODAL_FUNCTION_NAME':'score_positions', 'MODAL_ENVIRONMENT':'test',
    'MODAL_COMPATIBILITY_VERIFIED':True}
PINS = {'esm150':{'expected_weights_sha256':'a'*64,'expected_tokenizer_sha256':'b'*64}}

def setup_run(tmp_path, *, approved=True, **input_changes):
    path = tmp_path / 'runs.sqlite'
    service = RunService(path)
    data = {'reference_id':REFERENCE_ID, 'reference_numbering':'full_reference_1based',
        'objective_profile_id':'sequence_plausibility_review', 'protected_positions':[108,164,187],
        'allowed_region':{'start_1based':32, 'end_1based':212},
        'consent_to_external_sequence_upload':True,
        'requested_budget':{'usd_micros':1000, 'max_meta_requests':2, 'max_gpu_seconds':2700}}
    run_id = service.create({**data, **input_changes}, 'owner')
    context = SessionContext(path, run_id, 'owner')
    if approved:
        run = service.get(run_id, 'owner')
        service.approve(run_id, run['plan_digest'], run['budget_version'], 'owner')
    return service, context

def test_payload_is_bounded_label_free_and_roundtrips():
    req = request()
    payload = req.to_payload()
    assert InferenceRequest.from_payload(payload) == req
    assert set(payload) == {'reference_id','reference_sha256','reference_numbering','sequence_context',
        'positions','model_key','expected_weights_sha256','expected_tokenizer_sha256'}
    assert 'sequence' not in payload
    with pytest.raises(ValueError):
        InferenceRequest.from_payload({**payload,'api_key':'do-not-forward'})
    with pytest.raises(ValueError):
        InferenceRequest.from_payload({**payload,'positions':[[32]]})
    assert request(positions=(33,32)).digest() == request(positions=(32,33)).digest()

@pytest.mark.parametrize('changes', [{'positions':(108,)}, {'positions':(32,32)},
    {'model_key':'esm8'}, {'sequence_context':'mature_181'}, {'expected_weights_sha256':None}])
def test_invalid_request_never_reaches_provider(changes):
    with pytest.raises(ValueError):
        request(**changes)

def test_local_provider_uses_same_engine_contract():
    provider = LocalESMProvider(ESMEngine(SyntheticBackend()))
    done = provider.submit(request())
    assert done.status == 'completed'
    assert done.result['source_mode'] == 'synthetic_fixture'
    assert len(done.result['rows']) == 19
    assert provider.poll(done.job_id).result == done.result

def test_local_provider_rejects_pin_mismatch_before_forward():
    provider = LocalESMProvider(ESMEngine(SyntheticBackend()))
    with pytest.raises(ValueError):
        provider.submit(request(expected_weights_sha256='c'*64))

@pytest.mark.parametrize('config,approved', [({},False), (CONFIG,False),
    ({**CONFIG,'MODAL_COMPATIBILITY_VERIFIED':False},True)])
def test_modal_is_blocked_before_transport_without_recorded_gates(config, approved):
    transport = FakeTransport()
    provider = ModalESMProvider(config, transport=transport, execution_approved=approved)
    with pytest.raises(UnconfiguredBackendError):
        provider.submit(request())
    assert transport.submits == []

def test_runpod_is_explicitly_unconfigured():
    with pytest.raises(UnconfiguredBackendError):
        RunPodESMProvider().submit(request())

def test_modal_timeout_is_pending_without_resubmission():
    transport = FakeTransport()
    provider = ModalESMProvider(CONFIG, transport=transport, execution_approved=True)
    started = provider.submit(request())
    assert started.status == 'pending'
    assert provider.poll(started.job_id, 0).status == 'pending'
    transport.pending = False
    assert provider.poll(started.job_id, 0).status == 'completed'
    assert len(transport.submits) == 1
    assert transport.submits[0][-1] == request().to_payload()

def test_service_persists_job_and_duplicate_request_never_dispatches_twice(tmp_path):
    runs, context = setup_run(tmp_path)
    transport = FakeTransport()
    provider = ModalESMProvider(CONFIG, transport=transport, execution_approved=True)
    service = InferenceService(context.db_path, provider, 'modal', 'fixture-deployment', estimate_micros=100, job_timeout_seconds=60,model_pins=PINS)
    a = service.submit(context, request())
    b = service.submit(context, request())
    assert a['task_id'] == b['task_id']
    assert a['provider_job_id'] == 'fc-fixture-1'
    assert len(transport.submits) == 1
    assert service.status(context, a['task_id'])['status'] == 'pending'
    assert transport.polls == []
    resumed = InferenceService(context.db_path, provider, 'modal', 'fixture-deployment', estimate_micros=100, job_timeout_seconds=60,model_pins=PINS)
    assert resumed.poll(context, a['task_id'], 0)['status'] == 'pending'
    transport.pending = False
    done = resumed.poll(context, a['task_id'], 0)
    assert done['status'] == 'completed'
    assert done['artifact']['source_mode'] == 'synthetic_fixture'
    assert done['cost_micros'] is None
    assert done['elapsed_seconds'] is None
    assert len(transport.submits) == 1
    assert runs.get(context.run_id, 'owner')['committed_micros'] == 100

def test_service_does_not_submit_unapproved_or_unconsented_work(tmp_path):
    _, context = setup_run(tmp_path, approved=False)
    transport = FakeTransport()
    service = InferenceService(context.db_path,
        ModalESMProvider(CONFIG,transport=transport,execution_approved=True), 'modal','fixture',
        model_pins=PINS,estimate_micros=100,job_timeout_seconds=60)
    with pytest.raises(ValueError,match='approval'):
        service.submit(context, request())
    assert transport.submits == []

def test_service_unknown_submission_retains_reservation_and_never_retries(tmp_path):
    _, context = setup_run(tmp_path)
    class UnknownProvider:
        calls = 0
        def ensure_ready(self): pass
        def submit(self, req):
            self.calls += 1
            raise TimeoutError()
    provider = UnknownProvider()
    service = InferenceService(context.db_path, provider, 'modal','fixture', estimate_micros=100, job_timeout_seconds=60,model_pins=PINS)
    first = service.submit(context, request())
    assert first['status'] == 'unknown'
    assert service.submit(context, request())['task_id'] == first['task_id']
    assert provider.calls == 1

def test_service_rechecks_user_protection_region_and_backend_binding(tmp_path):
    _, context = setup_run(tmp_path, protected_positions=[32,108,164,187])
    provider = LocalESMProvider(ESMEngine(SyntheticBackend()))
    service = InferenceService(context.db_path,provider,'local','fixture')
    with pytest.raises(ValueError):
        service.submit(context,request())

def test_mcp_scoring_service_keeps_canonical_tool_and_status_readonly(tmp_path):
    _, context = setup_run(tmp_path)
    transport = FakeTransport()
    service = InferenceService(context.db_path,
        ModalESMProvider(CONFIG,transport=transport,execution_approved=True), 'modal','fixture', estimate_micros=100,
        job_timeout_seconds=60,model_pins={'esm150':{'expected_weights_sha256':'a'*64,'expected_tokenizer_sha256':'b'*64}})
    executor = ToolExecutor(context, inference_service=service)
    assert {t['name'] for t in executor.list_tools()} == {'validate_target_context','get_run_status','score_positions','retrieve_atlas_evidence'}
    args = {'reference_id':REFERENCE_ID,'model_key':'esm150','positions_1based':[32],'reason_brief':'Review sequence preference'}
    result = executor.dispatch('score_positions',args)
    assert result['status'] == 'pending'
    executor.dispatch('get_run_status',{})
    assert len(transport.submits) == 1
    assert transport.polls == []

def test_remote_gpu_time_limit_blocks_before_spend_reservation(tmp_path):
    runs,context = setup_run(tmp_path, requested_budget={'usd_micros':1000,'max_meta_requests':2,'max_gpu_seconds':30})
    transport = FakeTransport()
    service = InferenceService(context.db_path,
        ModalESMProvider(CONFIG,transport=transport,execution_approved=True),'modal','fixture',
        estimate_micros=100,job_timeout_seconds=60,model_pins=PINS)
    with pytest.raises(ValueError,match='GPU-seconds'):
        service.submit(context,request())
    assert transport.submits == []
    assert runs.get(context.run_id,'owner')['committed_micros'] == 0

def test_remote_requires_positive_explicit_reservations_and_sequence_consent(tmp_path):
    _,context = setup_run(tmp_path,consent_to_external_sequence_upload=False)
    transport = FakeTransport()
    provider = ModalESMProvider(CONFIG,transport=transport,execution_approved=True)
    service = InferenceService(context.db_path,provider,'modal','fixture',estimate_micros=100,job_timeout_seconds=60,model_pins=PINS)
    with pytest.raises(ValueError,match='consent'):
        service.submit(context,request())
    assert transport.submits == []

def test_malformed_worker_artifact_is_not_exposed_or_retried(tmp_path):
    runs,context = setup_run(tmp_path)
    class InvalidTransport(FakeTransport):
        def get(self,job_id,timeout_seconds):
            return {**artifact(),'experimental_labels':[1,2,3]}
    transport = InvalidTransport()
    service = InferenceService(context.db_path,
        ModalESMProvider(CONFIG,transport=transport,execution_approved=True),'modal','fixture',
        estimate_micros=100,job_timeout_seconds=60,model_pins=PINS)
    started = service.submit(context,request())
    result = service.poll(context,started['task_id'])
    assert result['status'] == 'unknown'
    assert 'artifact' not in result
    assert len(transport.submits) == 1
    assert runs.get(context.run_id,'owner')['committed_micros'] == 100

def test_foreign_run_and_changed_backend_cannot_poll_existing_job(tmp_path):
    _,context = setup_run(tmp_path)
    transport = FakeTransport()
    provider = ModalESMProvider(CONFIG,transport=transport,execution_approved=True)
    service = InferenceService(context.db_path,provider,'modal','fixture',estimate_micros=100,job_timeout_seconds=60,model_pins=PINS)
    started = service.submit(context,request())
    foreign = replace(context,owner_id='intruder')
    with pytest.raises(PermissionError):
        service.poll(foreign,started['task_id'])
    other = InferenceService(context.db_path,provider,'modal','other-deployment',estimate_micros=100,job_timeout_seconds=60,model_pins=PINS)
    with pytest.raises(ValueError):
        other.poll(context,started['task_id'])
    assert transport.polls == []

def test_reserved_second_job_is_claimed_once_after_first_completes(tmp_path):
    _,context = setup_run(tmp_path)
    class QueuedProvider:
        def __init__(self):
            self.submissions = []
        def ensure_ready(self): pass
        def submit(self,req):
            self.submissions.append(req)
            return Submission(f'fixture-{len(self.submissions)}','pending')
        def poll(self,job_id,timeout_seconds):
            req = self.submissions[int(job_id.split('-')[-1])-1]
            result = ESMEngine(SyntheticBackend()).score_positions(
                validate_target(registered_profile(),'sequence_plausibility_review'),list(req.positions))
            return Submission(job_id,'completed',result)
    provider = QueuedProvider()
    service = InferenceService(context.db_path,provider,'modal','fixture',estimate_micros=100,
        job_timeout_seconds=60,model_pins=PINS)
    first = service.submit(context,request())
    queued = service.submit(context,request(positions=(33,)))
    assert queued['status']=='reserved'
    assert len(provider.submissions)==1
    assert service.poll(context,first['task_id'])['status']=='completed'
    started = service.submit(context,request(positions=(33,)))
    assert started['task_id']==queued['task_id']
    assert started['status']=='pending'
    assert len(provider.submissions)==2
    assert service.submit(context,request(positions=(33,)))['task_id']==queued['task_id']
    assert len(provider.submissions)==2

def _rehash(value):
    value['artifact_sha256']=canonical_digest({key:item for key,item in value.items() if key!='artifact_sha256'})
    return value

@pytest.mark.parametrize('mutation', ['envelope_live','common_missing_mode','common_unknown_mode',
    'row_missing_mode','row_unknown_mode','missing_implementation','missing_precision','row_different_precision',
    'row_different_implementation','fixture_cache_as_live'])
def test_source_mode_and_core_provenance_cannot_be_relabelled(mutation):
    result = deepcopy(artifact())
    if mutation=='envelope_live': result['source_mode']='live'
    elif mutation=='common_missing_mode': result['provenance'].pop('source_mode')
    elif mutation=='common_unknown_mode': result['provenance']['source_mode']='unknown'
    elif mutation=='row_missing_mode': result['rows'][0].pop('source_mode')
    elif mutation=='row_unknown_mode': result['rows'][0]['source_mode']='unknown'
    elif mutation=='missing_implementation': result['provenance'].pop('implementation')
    elif mutation=='missing_precision': result['provenance'].pop('precision')
    elif mutation=='row_different_precision': result['rows'][0]['precision']='float16'
    elif mutation=='row_different_implementation': result['rows'][0]['implementation']='different'
    else:
        result['source_mode']='replay'
        result['cached_positions_1based']=[32]
    with pytest.raises(ProviderError):
        validate_score_artifact(_rehash(result),request())

@pytest.mark.parametrize('changes', [
    {'positions_1based':[33]}, {'esm_model_key':'esm35'},
    {'model_pins':{'esm150':{'expected_weights_sha256':'c'*64,'expected_tokenizer_sha256':'b'*64}}},
])
def test_immutable_run_selection_blocks_model_chosen_escape(tmp_path,changes):
    runs,context = setup_run(tmp_path,**changes)
    transport = FakeTransport()
    service = InferenceService(context.db_path,
        ModalESMProvider(CONFIG,transport=transport,execution_approved=True),'modal','fixture',
        estimate_micros=100,job_timeout_seconds=60,model_pins=PINS)
    with pytest.raises(ValueError):
        service.submit(context,request())
    assert transport.submits==[]
    assert runs.get(context.run_id,'owner')['committed_micros']==0

@pytest.mark.parametrize('changes', [{'expected_weights_sha256':'c'*64},
    {'expected_tokenizer_sha256':'c'*64},{'model_key':'esm35'}])
def test_direct_service_submit_cannot_escape_provider_model_pins(tmp_path,changes):
    runs,context = setup_run(tmp_path)
    transport = FakeTransport()
    service = InferenceService(context.db_path,
        ModalESMProvider(CONFIG,transport=transport,execution_approved=True),'modal','fixture',
        estimate_micros=100,job_timeout_seconds=60,model_pins=PINS)
    with pytest.raises(ValueError):
        service.submit(context,request(**changes))
    assert transport.submits==[]
    assert runs.get(context.run_id,'owner')['committed_micros']==0

def test_remote_reserves_worker_ceiling_even_when_client_timeout_is_short(tmp_path):
    _,context = setup_run(tmp_path)
    transport = FakeTransport()
    service = InferenceService(context.db_path,
        ModalESMProvider(CONFIG,transport=transport,execution_approved=True),'modal','fixture',
        estimate_micros=100,job_timeout_seconds=60,model_pins=PINS)
    result=service.submit(context,request())
    assert result['reserved_gpu_seconds']==1022
    assert result['reservation_components']=={'execution_seconds':900,'startup_seconds':120,'idle_seconds':2}
    assert result['cost_scope']['image_build']=='unknown'
    assert result['cost_scope']['storage']=='unknown'

def test_remote_120_second_budget_cannot_authorize_900_second_worker(tmp_path):
    runs,context = setup_run(tmp_path,requested_budget={'usd_micros':1000,'max_meta_requests':2,'max_gpu_seconds':120})
    transport = FakeTransport()
    service = InferenceService(context.db_path,
        ModalESMProvider(CONFIG,transport=transport,execution_approved=True),'modal','fixture',
        estimate_micros=100,job_timeout_seconds=60,model_pins=PINS)
    with pytest.raises(ValueError,match='GPU-seconds'):
        service.submit(context,request())
    assert transport.submits==[]
    assert runs.get(context.run_id,'owner')['committed_micros']==0

def test_remote_900_second_budget_omits_startup_and_idle_and_is_rejected(tmp_path):
    runs,context=setup_run(tmp_path,requested_budget={'usd_micros':1000,'max_meta_requests':2,'max_gpu_seconds':900})
    transport=FakeTransport()
    service=InferenceService(context.db_path,
        ModalESMProvider(CONFIG,transport=transport,execution_approved=True),'modal','fixture',
        estimate_micros=100,job_timeout_seconds=60,model_pins=PINS)
    with pytest.raises(ValueError,match='GPU-seconds'):
        service.submit(context,request())
    assert transport.submits==[]
    assert runs.get(context.run_id,'owner')['committed_micros']==0

def test_remote_1022_second_budget_covers_full_bound_once(tmp_path):
    runs,context=setup_run(tmp_path,requested_budget={'usd_micros':1000,'max_meta_requests':2,'max_gpu_seconds':1022})
    transport=FakeTransport()
    service=InferenceService(context.db_path,
        ModalESMProvider(CONFIG,transport=transport,execution_approved=True),'modal','fixture',
        estimate_micros=100,job_timeout_seconds=60,model_pins=PINS)
    first=service.submit(context,request())
    assert first['reserved_gpu_seconds']==1022
    with pytest.raises(ValueError,match='GPU-seconds'):
        service.submit(context,request(positions=(33,)))
    assert len(transport.submits)==1
    assert runs.get(context.run_id,'owner')['committed_micros']==100

def test_verified_legacy_nonpersistent_buffer_provenance_is_retained():
    value=deepcopy(artifact())
    ignored=['esm.embeddings.position_ids']
    value['provenance']['ignored_nonpersistent_buffers']=ignored
    for row in value['rows']:
        row['ignored_nonpersistent_buffers']=list(ignored)
    verified=validate_score_artifact(_rehash(value),request())
    assert verified['provenance']['ignored_nonpersistent_buffers']==ignored
    assert all(row['ignored_nonpersistent_buffers']==ignored for row in verified['rows'])

@pytest.mark.parametrize('ignored',[None,[],['esm.encoder.layer.0.weight'],
    ['esm.embeddings.position_ids','lm_head.weight'],'esm.embeddings.position_ids'])
def test_nonpersistent_buffer_provenance_cannot_exempt_unknown_weights(ignored):
    value=deepcopy(artifact())
    value['provenance']['ignored_nonpersistent_buffers']=ignored
    for row in value['rows']:
        row['ignored_nonpersistent_buffers']=ignored
    with pytest.raises(ProviderError):
        validate_score_artifact(_rehash(value),request())

def test_nonpersistent_buffer_row_and_common_provenance_must_match():
    value=deepcopy(artifact())
    value['provenance']['ignored_nonpersistent_buffers']=['esm.embeddings.position_ids']
    with pytest.raises(ProviderError):
        validate_score_artifact(_rehash(value),request())
    value=deepcopy(artifact())
    value['rows'][0]['ignored_nonpersistent_buffers']=['esm.embeddings.position_ids']
    with pytest.raises(ProviderError):
        validate_score_artifact(_rehash(value),request())


PINS_BOTH = {'esm150':{'expected_weights_sha256':'a'*64,'expected_tokenizer_sha256':'b'*64},
             'esm650':{'expected_weights_sha256':'c'*64,'expected_tokenizer_sha256':'d'*64}}


class Synthetic650Backend(SyntheticBackend):
    provenance = {'checkpoint':'esm2_t33_650M_UR50D','weights_sha256':'c'*64,
        'tokenizer_sha256':'d'*64,'implementation':'fixture','precision':'float32',
        'source_mode':'synthetic_fixture'}


def verifier_request(**changes):
    return request(model_key='esm650', expected_weights_sha256='c'*64,
                   expected_tokenizer_sha256='d'*64, **changes)


def routed_provider():
    from app.science.provider_config import RoutingLocalProvider
    return RoutingLocalProvider({'esm150':LocalESMProvider(ESMEngine(SyntheticBackend())),
                                 'esm650':LocalESMProvider(ESMEngine(Synthetic650Backend()))})


def test_a_run_approving_only_the_baseline_still_refuses_the_verifier(tmp_path):
    """Configuring a second checkpoint must not widen an already frozen run."""
    runs, context = setup_run(tmp_path, esm_model_key='esm150')
    service = InferenceService(context.db_path, routed_provider(), 'local', 'fixture',
                               model_pins=PINS_BOTH)
    with pytest.raises(ValueError, match='immutable selected model'):
        service.submit(context, verifier_request())


def test_one_run_never_mixes_checkpoints_even_when_both_are_approved(tmp_path):
    """Approving a model set must not let a single run mix two rank policies.

    The verifier is separate evidence, not a second opinion blended into one ranking.
    """
    runs, context = setup_run(tmp_path, esm_model_keys=['esm150','esm650'])
    service = InferenceService(context.db_path, routed_provider(), 'local', 'fixture',
                               model_pins=PINS_BOTH)
    baseline = service.submit(context, request())
    assert baseline['status'] == 'completed'
    assert baseline['model_key'] == 'esm150'
    assert baseline['artifact']['provenance']['checkpoint'] == 'esm2_t30_150M_UR50D'
    with pytest.raises(ValueError, match='same backend/model/checkpoint rank policy'):
        service.submit(context, verifier_request())


def test_the_verifier_checkpoint_serves_its_own_run(tmp_path):
    """Routing works end to end when a run is frozen on the verifier checkpoint."""
    runs, context = setup_run(tmp_path, esm_model_keys=['esm650'])
    service = InferenceService(context.db_path, routed_provider(), 'local', 'fixture',
                               model_pins=PINS_BOTH)
    done = service.submit(context, verifier_request())
    assert done['status'] == 'completed'
    assert done['model_key'] == 'esm650'
    assert done['artifact']['provenance']['checkpoint'] == 'esm2_t33_650M_UR50D'
    assert done['artifact']['provenance']['rank_policy'] == 'esm650_masked_v1'


def test_an_approved_model_set_still_rejects_a_model_outside_it(tmp_path):
    runs, context = setup_run(tmp_path, esm_model_keys=['esm150'])
    service = InferenceService(context.db_path, routed_provider(), 'local', 'fixture',
                               model_pins=PINS_BOTH)
    with pytest.raises(ValueError, match='immutable selected model'):
        service.submit(context, verifier_request())


def test_the_verifier_cannot_borrow_the_baseline_pins(tmp_path):
    """Routing must not let one checkpoint be served under another model key."""
    runs, context = setup_run(tmp_path, esm_model_keys=['esm150','esm650'])
    service = InferenceService(context.db_path, routed_provider(), 'local', 'fixture',
                               model_pins=PINS_BOTH)
    with pytest.raises(ValueError):
        service.submit(context, request(model_key='esm650'))


def test_the_offered_model_choice_follows_the_configured_pins(tmp_path):
    """Meta sees exactly the checkpoints that are actually provisioned, never more."""
    _, context = setup_run(tmp_path)
    baseline_only = InferenceService(context.db_path, LocalESMProvider(ESMEngine(SyntheticBackend())),
        'local', 'fixture', model_pins={'esm150':PINS_BOTH['esm150']})
    offered = ToolExecutor(context, inference_service=baseline_only).list_tools()
    enum = [t for t in offered if t['name']=='score_positions'][0]['inputSchema']['properties']['model_key']['enum']
    assert enum == ['esm150']

    with_verifier = InferenceService(context.db_path, routed_provider(), 'local', 'fixture',
                                     model_pins=PINS_BOTH)
    offered = ToolExecutor(context, inference_service=with_verifier).list_tools()
    enum = [t for t in offered if t['name']=='score_positions'][0]['inputSchema']['properties']['model_key']['enum']
    assert enum == ['esm150','esm650']
    # esm35 is registered in the model registry but was never provisioned, so it must
    # not be offered merely because the catalog lists it.
    assert 'esm35' not in enum
