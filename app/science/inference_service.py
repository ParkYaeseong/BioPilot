"""Durable provider dispatch. Status reads never dispatch or poll a provider.

Unknown submissions retain reservations; they cannot be retried automatically.
"""
from contextlib import contextmanager
from copy import deepcopy
import json
import math
from pathlib import Path
import sqlite3

from app.core.budget import nonnegative_int
from app.core.runs import RunService
from app.core.targets import registered_profile, validate_target
from app.science.models import get_model_spec
from app.science.providers import (InferenceRequest, Submission, UnconfiguredBackendError,
    ProviderError, canonical_digest)

AA = 'ACDEFGHIKLMNPQRSTVWY'
COMMON_KEYS = frozenset({'checkpoint','model_key','rank_policy','weights_sha256','tokenizer_sha256',
    'config_sha256','weight_file_hashes','implementation','precision','source_mode','device',
    'checkpoint_revision','upstream_authenticity','reference_id','reference_sha256',
    'sequence_context','score_kind'})

def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

class InferenceService:
    def __init__(self, db_path, provider, backend_key, provider_binding, *, estimate_micros=0,
                 model_pins=None, job_timeout_seconds=None):
        self.db_path = Path(db_path).resolve()
        self.provider = provider
        if backend_key not in {'local','modal','runpod'}:
            raise ValueError('Unknown backend; fallback is forbidden')
        if not isinstance(provider_binding,str) or not 1 <= len(provider_binding) <= 200:
            raise ValueError('An explicit provider deployment/checkpoint binding is required')
        self.backend_key = backend_key
        self.provider_binding = provider_binding
        self.estimate_micros = nonnegative_int(estimate_micros,'estimate_micros')
        self.job_timeout_seconds = job_timeout_seconds
        self.model_pins = deepcopy(dict(model_pins or {}))
        if not self.model_pins and backend_key == 'local' and getattr(provider,'engine',None) is not None:
            provenance = provider.engine.backend.provenance
            from app.science.models import MODEL_REGISTRY
            matching = [key for key,spec in MODEL_REGISTRY.items() if spec.checkpoint == provenance.get('checkpoint')]
            if matching:
                self.model_pins[matching[0]] = {key:provenance.get(name) for key,name in (
                    ('expected_weights_sha256','weights_sha256'),('expected_tokenizer_sha256','tokenizer_sha256'))}
        self.runs = RunService(self.db_path)
        with self._transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS inference_jobs (
                task_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, request_json TEXT NOT NULL,
                job_digest TEXT NOT NULL, backend TEXT NOT NULL, provider_binding TEXT NOT NULL,
                status TEXT NOT NULL, provider_job_id TEXT, artifact_json TEXT,
                cost_micros INTEGER, elapsed_seconds REAL, reserved_gpu_seconds INTEGER NOT NULL,
                UNIQUE(run_id,job_digest))''')

    @contextmanager
    def _transaction(self):
        db = sqlite3.connect(self.db_path,timeout=10,isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('BEGIN IMMEDIATE')
        try:
            yield db
        except BaseException:
            db.rollback()
            raise
        else:
            db.commit()
        finally:
            db.close()

    def ensure_ready(self):
        self.provider.ensure_ready()
        # A configured catalog must not advertise a model with missing/invalid pins.
        if self.model_pins:
            target = validate_target(registered_profile(),'sequence_plausibility_review')
            for model_key in self.model_pins:
                try:
                    self.request_for(target,[32],model_key)
                except (ValueError,TypeError,KeyError) as error:
                    raise UnconfiguredBackendError('Trusted ESM model/tokenizer pins are incomplete or invalid') from error
        if self.backend_key != 'local':
            if self.estimate_micros <= 0:
                raise UnconfiguredBackendError('Remote inference needs a positive conservative cost reservation')
            if type(self.job_timeout_seconds) is not int or not 1 <= self.job_timeout_seconds <= 900:
                raise UnconfiguredBackendError('Remote inference needs an explicit bounded per-job GPU timeout')

    def request_for(self,target,positions,model_key):
        pins = self.model_pins.get(model_key)
        if not isinstance(pins,dict):
            raise UnconfiguredBackendError('Requested ESM model has no trusted checkpoint/tokenizer pins')
        return InferenceRequest(target.reference_id,target.reference_sha256,target.reference_numbering,
            target.sequence_context,tuple(positions),model_key,pins.get('expected_weights_sha256'),
            pins.get('expected_tokenizer_sha256'))

    def _run(self,context):
        if Path(context.db_path).resolve() != self.db_path:
            raise ValueError('Session database does not match this inference service')
        return self.runs.get(context.run_id,context.owner_id)

    def _validate(self,context,request):
        if not isinstance(request,InferenceRequest):
            raise ValueError('Expected a validated inference request')
        configured = self.model_pins.get(request.model_key)
        if (not isinstance(configured,dict)
                or configured.get('expected_weights_sha256')!=request.expected_weights_sha256
                or configured.get('expected_tokenizer_sha256')!=request.expected_tokenizer_sha256):
            raise ValueError('Request model/checkpoint pins differ from the configured provider')
        run = self._run(context)
        data = run['input']
        target = validate_target(registered_profile(), data.get('objective_profile_id',data.get('objective_id')),
            reference_numbering=data.get('reference_numbering'))
        if request.reference_id != data.get('reference_id') or request.reference_sha256 != target.reference_sha256:
            raise ValueError('Inference reference does not match the immutable run')
        protected = data.get('protected_positions', [108,164,187])
        if (not isinstance(protected,list) or any(type(p) is not int or not 1 <= p <= 212 for p in protected)
                or not {108,164,187} <= set(protected)):
            raise ValueError('Invalid immutable protected-site policy')
        region = data.get('allowed_region',{'start_1based':32,'end_1based':212})
        start,end = region.get('start_1based'),region.get('end_1based')
        if type(start) is not int or type(end) is not int or not 32 <= start <= end <= 212:
            raise ValueError('Invalid immutable full-reference region')
        if any(p in protected or not start <= p <= end for p in request.positions):
            raise ValueError('Request violates the immutable allowed region/protected sites')
        selected = data.get('esm_model_key',data.get('model_key'))
        if 'esm_model_key' in data or 'model_key' in data:
            get_model_spec(selected)
        if selected is not None and request.model_key != selected:
            raise ValueError('Request model differs from the immutable selected model')
        if 'positions_1based' in data:
            selected_positions = data['positions_1based']
            if (not isinstance(selected_positions,list) or not 1 <= len(selected_positions) <= 10
                    or any(type(p) is not int or not start<=p<=end or p in protected for p in selected_positions)
                    or len(set(selected_positions))!=len(selected_positions)
                    or not set(request.positions)<=set(selected_positions)):
                raise ValueError('Request positions differ from the immutable approved review positions')
        if 'model_pins' in data:
            approved_pins = data['model_pins']
            if not isinstance(approved_pins,dict) or not isinstance(approved_pins.get(request.model_key),dict):
                raise ValueError('Immutable approved model pins are missing or invalid')
            approved = approved_pins[request.model_key]
            if (approved.get('expected_weights_sha256')!=request.expected_weights_sha256
                    or approved.get('expected_tokenizer_sha256')!=request.expected_tokenizer_sha256):
                raise ValueError('Request checkpoint pins differ from the immutable approved review pins')
        if self.backend_key != 'local' and data.get('consent_to_external_sequence_upload') is not True:
            raise ValueError('Remote public-reference computation requires recorded sequence-upload consent')
        return run

    def submit(self,context,request):
        run = self._validate(context,request)
        digest = canonical_digest({'request':request.to_payload(),'backend':self.backend_key,
                                   'provider_binding':self.provider_binding})
        with self._transaction() as db:
            existing = db.execute('SELECT task_id FROM inference_jobs WHERE run_id=? AND job_digest=?',
                                  (context.run_id,digest)).fetchone()
        if existing:
            return self._dispatch_if_reserved(context,request,existing['task_id'])
        self.ensure_ready()
        # Until a verified deployment attestation binds a smaller worker timeout,
        # reserve the configured worker factory's entire 900-second ceiling.
        seconds = 0 if self.backend_key == 'local' else 900
        with self._transaction() as db:
            rows = list(db.execute('SELECT * FROM inference_jobs WHERE run_id=?',(context.run_id,)))
            self._check_limits(rows,run,request,seconds)
        reservation = self.runs.reserve(context.run_id,digest,self.estimate_micros,context.owner_id)
        with self._transaction() as db:
            rows = list(db.execute('SELECT * FROM inference_jobs WHERE run_id=?',(context.run_id,)))
            existing = next((row for row in rows if row['job_digest']==digest),None)
            if existing is None:
                self._check_limits(rows,run,request,seconds)
                db.execute('INSERT INTO inference_jobs VALUES (?,?,?,?,?,?,?,NULL,NULL,NULL,NULL,?)',
                    (reservation.task_id,context.run_id,_json(request.to_payload()),digest,
                     self.backend_key,self.provider_binding,'reserved',seconds))
        return self._dispatch_if_reserved(context,request,reservation.task_id)

    def _dispatch_if_reserved(self,context,request,task_id):
        # A queued task can recover only while it has never been dispatched.
        # claim remains atomic; DISPATCHED/UNKNOWN tasks can only be reconciled.
        row,task = self._job(context,task_id)
        if row['status']!='reserved' or task['status']!='RESERVED':
            return self.status(context,task_id)
        self.ensure_ready()
        if self.backend_key!='local' and row['reserved_gpu_seconds']<900:
            raise ValueError('Queued remote reservation does not cover the verified worker ceiling')
        if self.runs.claim(context.run_id,task_id,context.owner_id):
            self._update(task_id,status='dispatching')
            try:
                submission = self.provider.submit(request)
                if not isinstance(submission,Submission) or not submission.job_id:
                    raise ProviderError('Provider did not return a persistent job identity')
                self.runs.attach_provider_job(context.run_id,task_id,context.owner_id,submission.job_id)
                self._update(task_id,status='pending',provider_job_id=submission.job_id)
                if submission.status == 'completed':
                    self._complete(context,task_id,request,submission)
                elif submission.status != 'pending':
                    raise ProviderError('Invalid provider submission state')
            except Exception:
                self.runs.mark_unknown(context.run_id,task_id,context.owner_id)
                self._update(task_id,status='unknown')
        return self.status(context,task_id)

    def _check_limits(self,rows,run,request,seconds):
        if len(rows) >= 12:
            raise ValueError('At most twelve scientific jobs are supported per run')
        positions = set(request.positions)
        for row in rows:
            previous = InferenceRequest.from_payload(json.loads(row['request_json']))
            if (row['backend'] != self.backend_key or row['provider_binding'] != self.provider_binding
                    or previous.model_key != request.model_key
                    or previous.expected_weights_sha256 != request.expected_weights_sha256
                    or previous.expected_tokenizer_sha256 != request.expected_tokenizer_sha256):
                raise ValueError('One run must retain the same backend/model/checkpoint rank policy')
            positions.update(previous.positions)
        if len(positions)*19 > 200:
            raise ValueError('Run exceeds the frozen 200-candidate ceiling')
        max_seconds = run['input'].get('requested_budget',{}).get('max_gpu_seconds',0)
        if seconds and (type(max_seconds) is not int or max_seconds <= 0
                or sum(row['reserved_gpu_seconds'] for row in rows)+seconds > max_seconds):
            raise ValueError('Remote job exceeds the approved cumulative GPU-seconds ceiling')

    def _update(self,task_id,**fields):
        allowed = {'status','provider_job_id','artifact_json','cost_micros','elapsed_seconds'}
        if not set(fields)<=allowed:
            raise ValueError('Invalid inference state fields')
        with self._transaction() as db:
            db.execute('UPDATE inference_jobs SET '+','.join(key+'=?' for key in fields)+' WHERE task_id=?',
                       (*fields.values(),task_id))

    def _job(self,context,task_id):
        run = self._run(context)
        with self._transaction() as db:
            row = db.execute('SELECT * FROM inference_jobs WHERE task_id=? AND run_id=?',
                             (task_id,context.run_id)).fetchone()
        if row is None or row['backend'] != self.backend_key or row['provider_binding'] != self.provider_binding:
            raise ValueError('Inference job is unavailable to this bound service/run')
        task = next((task for task in run['tasks'] if task['task_id']==task_id),None)
        if task is None:
            raise ValueError('Inference job has no durable reservation')
        return dict(row),task

    def status(self,context,task_id):
        row,task = self._job(context,task_id)
        req = InferenceRequest.from_payload(json.loads(row['request_json']))
        state = row['status']
        if state in {'reserved','dispatching'} and task['status'] in {'DISPATCHED','UNKNOWN'}:
            state = 'unknown'
        result = {'status':state,'task_id':task_id,'provider_job_id':row['provider_job_id'] or task['provider_job_id'],
            'backend':self.backend_key,'provider_binding':self.provider_binding,'model_key':req.model_key,
            'request_sha256':req.digest(),'cost_micros':row['cost_micros'],
            'cost_status':'unknown' if row['cost_micros'] is None else 'actual',
            'elapsed_seconds':row['elapsed_seconds'],'reserved_gpu_seconds':row['reserved_gpu_seconds']}
        if row['artifact_json'] is not None:
            result['artifact'] = json.loads(row['artifact_json'])
            result['artifact_sha256'] = result['artifact']['artifact_sha256']
        return result

    def list_status(self,context):
        """Bound run artifact state only; no polling, cost reservation or dispatch."""
        self._run(context)
        with self._transaction() as db:
            tasks = [row['task_id'] for row in db.execute(
                'SELECT task_id FROM inference_jobs WHERE run_id=? ORDER BY rowid LIMIT 12',(context.run_id,))]
        return [self.status(context,task_id) for task_id in tasks]

    def poll(self,context,task_id,timeout_seconds=0):
        """Trusted worker reconciliation only. MCP status tools do not call this."""
        if type(timeout_seconds) not in (int,float) or not 0 <= timeout_seconds <= 5:
            raise ValueError('Poll timeout must be 0..5 seconds')
        row,task = self._job(context,task_id)
        if row['artifact_json'] is not None:
            return self.status(context,task_id)
        job_id = row['provider_job_id'] or task['provider_job_id']
        if job_id is None:
            return self.status(context,task_id)
        self.ensure_ready()
        request = InferenceRequest.from_payload(json.loads(row['request_json']))
        try:
            submission = self.provider.poll(job_id,timeout_seconds)
            if not isinstance(submission,Submission) or submission.job_id != job_id:
                raise ProviderError('Provider job identity changed during reconciliation')
            if submission.status == 'completed':
                self._complete(context,task_id,request,submission)
            elif submission.status == 'pending':
                self._update(task_id,status='pending',provider_job_id=job_id)
            else:
                raise ProviderError('Invalid provider poll state')
        except Exception:
            self.runs.mark_unknown(context.run_id,task_id,context.owner_id)
            self._update(task_id,status='unknown')
        return self.status(context,task_id)

    def _complete(self,context,task_id,request,submission):
        artifact = validate_score_artifact(submission.result,request)
        cost,elapsed = submission.cost_micros,submission.elapsed_seconds
        if cost is not None:
            nonnegative_int(cost,'provider actual cost')
        if elapsed is not None and (type(elapsed) not in (int,float) or not math.isfinite(elapsed) or elapsed<0):
            raise ProviderError('Invalid provider elapsed time')
        self._update(task_id,status='completed',artifact_json=_json(artifact),cost_micros=cost,elapsed_seconds=elapsed)
        self.runs.settle(context.run_id,task_id,context.owner_id,actual_micros=cost)

def validate_score_artifact(artifact,request):
    """Reject unexpected worker fields and verify the exact numerical artifact."""
    if not isinstance(artifact,dict) or len(_json(artifact).encode()) > 1_000_000:
        raise ProviderError('Invalid or oversized ESM artifact')
    allowed = {'rows','provenance','source_mode','cached_positions_1based','phenotype_calibrated',
               'score_units','rank_policy','limitations','artifact_sha256'}
    if set(artifact)-allowed or artifact.get('artifact_sha256') != canonical_digest(
            {key:value for key,value in artifact.items() if key!='artifact_sha256'}):
        raise ProviderError('ESM artifact hash/fields are invalid')
    spec = get_model_spec(request.model_key)
    if artifact.get('phenotype_calibrated') is not False or artifact.get('score_units')!='dimensionless' or artifact.get('rank_policy')!=spec.rank_policy:
        raise ProviderError('ESM artifact claims or rank policy do not match sequence preference')
    common = artifact.get('provenance')
    if not isinstance(common,dict) or set(common)-COMMON_KEYS:
        raise ProviderError('Unexpected ESM provenance fields')
    expected = {'reference_id':request.reference_id,'reference_sha256':request.reference_sha256,
        'sequence_context':'full_212','checkpoint':spec.checkpoint,'model_key':request.model_key,
        'weights_sha256':request.expected_weights_sha256,'tokenizer_sha256':request.expected_tokenizer_sha256,
        'score_kind':'masked_marginal_log_likelihood_ratio'}
    if any(common.get(key)!=value for key,value in expected.items()):
        raise ProviderError('ESM provenance differs from the frozen request')
    if (not isinstance(common.get('implementation'),str) or not common['implementation'].strip()
            or len(common['implementation'])>200
            or common.get('precision') not in {'float16','bfloat16','float32','float64'}
            or common.get('rank_policy')!=spec.rank_policy):
        raise ProviderError('ESM implementation, precision or rank provenance is incomplete')
    cached = artifact.get('cached_positions_1based')
    if (not isinstance(cached,list) or any(type(p) is not int or p not in request.positions for p in cached)
            or len(set(cached))!=len(cached)):
        raise ProviderError('ESM cache-position provenance is invalid')
    common_mode = common.get('source_mode')
    if common_mode=='synthetic_fixture':
        expected_envelope_mode = 'synthetic_fixture'
    elif common_mode=='live':
        expected_envelope_mode = 'replay' if set(cached)==set(request.positions) else 'live'
    else:
        raise ProviderError('ESM provenance source mode is missing or unsupported')
    if artifact.get('source_mode')!=expected_envelope_mode:
        raise ProviderError('ESM envelope source mode conflicts with provenance/cache identity')
    sequence = registered_profile()['reference_sequence']
    candidates = {f'{sequence[p-1]}{p}{aa}' for p in request.positions for aa in AA if aa!=sequence[p-1]}
    rows = artifact.get('rows')
    if not isinstance(rows,list) or len(rows)!=len(candidates):
        raise ProviderError('ESM candidate cohort is incomplete')
    seen = set()
    for row in rows:
        if not isinstance(row,dict) or set(row)-(COMMON_KEYS|{'candidate_id','full_position','wild_type','mutant','score'}):
            raise ProviderError('Unexpected ESM row fields')
        cid = row.get('candidate_id')
        pos = row.get('full_position')
        if (cid not in candidates or cid in seen or pos not in request.positions
                or row.get('wild_type')!=sequence[pos-1] or row.get('mutant') not in AA
                or cid!=f'{sequence[pos-1]}{pos}{row["mutant"]}'
                or any(row.get(key)!=value for key,value in expected.items())
                or row.get('implementation')!=common['implementation']
                or row.get('precision')!=common['precision']
                or row.get('rank_policy')!=spec.rank_policy
                or row.get('source_mode')!=('synthetic_fixture' if common_mode=='synthetic_fixture'
                    else 'replay' if pos in cached else 'live')
                or type(row.get('score')) not in (int,float) or not math.isfinite(row['score'])):
            raise ProviderError('ESM row identity, provenance or score is invalid')
        seen.add(cid)
    return artifact
