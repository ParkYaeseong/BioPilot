"""Explicit bounded ESM execution providers. No default network execution."""
from dataclasses import dataclass, asdict
import importlib
import importlib.util
from importlib.metadata import version
import hashlib
import json
import re
import uuid
from typing import Any, Mapping, Protocol

from app.core.targets import REFERENCE_ID, REFERENCE_SHA256, FRAME
from app.science.models import get_model_spec

class UnconfiguredBackendError(ValueError):
    pass

class ProviderError(RuntimeError):
    pass

def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class InferenceRequest:
    reference_id: str
    reference_sha256: str
    reference_numbering: str
    sequence_context: str
    positions: tuple[int, ...]
    model_key: str
    expected_weights_sha256: str
    expected_tokenizer_sha256: str

    def __post_init__(self):
        if (self.reference_id != REFERENCE_ID or self.reference_sha256 != REFERENCE_SHA256
                or self.reference_numbering != FRAME or self.sequence_context != 'full_212'):
            raise ValueError('Only the registered full_212 public reference is enabled')
        if (type(self.positions) is not tuple or not 1 <= len(self.positions) <= 10
                or any(type(p) is not int or not 32 <= p <= 212 or p in (108,164,187) for p in self.positions)
                or len(set(self.positions)) != len(self.positions)):
            raise ValueError('Expected 1..10 unique eligible full-reference positions')
        object.__setattr__(self,'positions',tuple(sorted(self.positions)))
        get_model_spec(self.model_key)
        for pin in (self.expected_weights_sha256, self.expected_tokenizer_sha256):
            if not isinstance(pin, str) or re.fullmatch('[0-9a-f]{64}', pin) is None:
                raise ValueError('Explicit trusted checkpoint and tokenizer SHA256 pins are required')

    def to_payload(self):
        value = asdict(self)
        value['positions'] = list(self.positions)
        return value

    def digest(self):
        return canonical_digest(self.to_payload())

    @classmethod
    def from_payload(cls, payload):
        expected = set(cls.__dataclass_fields__)
        if not isinstance(payload, dict) or set(payload) != expected or type(payload['positions']) is not list:
            raise ValueError('Invalid inference payload fields; extra data is forbidden')
        return cls(**{**payload, 'positions': tuple(payload['positions'])})

@dataclass(frozen=True)
class Submission:
    job_id: str
    status: str
    result: dict | None = None
    cost_micros: int | None = None
    elapsed_seconds: float | None = None

class ESMInferenceProvider(Protocol):
    def ensure_ready(self) -> None: ...
    def submit(self, request: InferenceRequest) -> Submission: ...
    def poll(self, job_id: str, timeout_seconds: float = 0) -> Submission: ...

class LocalESMProvider:
    def __init__(self, engine):
        self.engine = engine
        self._results = {}
    def ensure_ready(self):
        if self.engine is None or not hasattr(self.engine, 'score_positions'):
            raise UnconfiguredBackendError('Local ESM checkpoint is not configured')
    def submit(self, request):
        if not isinstance(request,InferenceRequest):
            raise ValueError('Expected a validated bounded inference request')
        self.ensure_ready()
        provenance = self.engine.backend.provenance
        if (provenance.get('weights_sha256') != request.expected_weights_sha256
                or provenance.get('tokenizer_sha256') != request.expected_tokenizer_sha256
                or provenance.get('checkpoint') != get_model_spec(request.model_key).checkpoint):
            raise ValueError('Local checkpoint does not match the explicit request pins/model')
        from app.core.targets import registered_profile, validate_target
        target = validate_target(registered_profile(), 'sequence_plausibility_review')
        result = self.engine.score_positions(target, list(request.positions), request.model_key)
        job_id = 'local-' + uuid.uuid4().hex
        done = Submission(job_id, 'completed', result)
        self._results[job_id] = done
        return done
    def poll(self, job_id, timeout_seconds=0):
        _poll_timeout(timeout_seconds)
        if job_id not in self._results:
            raise ProviderError('Local result is not in memory; read its persisted service artifact')
        return self._results[job_id]

BACKEND_CONFIG_KEYS = frozenset({'ESM_BACKEND', 'MODAL_APP_NAME', 'MODAL_FUNCTION_NAME',
    'MODAL_ENVIRONMENT', 'MODAL_COMPATIBILITY_VERIFIED', 'MODAL_SDK_VERSION'})

def backend_config(mapping):
    """Accept only a selected config mapping, never an entire secret environment."""
    if not isinstance(mapping, Mapping) or not set(mapping) <= BACKEND_CONFIG_KEYS:
        raise ValueError('Only selected ESM backend configuration fields are accepted')
    data = dict(mapping)
    data.setdefault('ESM_BACKEND', 'modal')
    if data['ESM_BACKEND'] not in {'local', 'modal', 'runpod'}:
        raise ValueError('Unknown ESM backend; fallback is forbidden')
    return data

def _poll_timeout(value):
    if type(value) not in (int, float) or not 0 <= value <= 5:
        raise ValueError('Poll timeout must be 0..5 seconds')

def _job_id(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 300 or not value.isascii() or any(c.isspace() for c in value):
        raise ProviderError('Provider did not return a valid job identity')
    return value

class OfficialModalTransport:
    """SDK API checked against Modal Function/FunctionCall docs; no deployment here."""
    def spawn(self, app_name, function_name, environment, payload):
        modal = importlib.import_module('modal')
        function = modal.Function.from_name(app_name, function_name, environment_name=environment)
        return function.spawn(payload).object_id

    def get(self, job_id, timeout_seconds):
        modal = importlib.import_module('modal')
        return modal.FunctionCall.from_id(job_id).get(timeout=timeout_seconds)

class ModalESMProvider:
    def __init__(self, config, *, transport=None, execution_approved=False):
        self.config = backend_config(config)
        self.transport = transport
        self.execution_approved = execution_approved
    def ensure_ready(self):
        if (self.config['ESM_BACKEND'] != 'modal' or self.execution_approved is not True
                or self.config.get('MODAL_COMPATIBILITY_VERIFIED') is not True):
            raise UnconfiguredBackendError('Modal execution and installed SDK compatibility are not approved/verified')
        for key in ('MODAL_APP_NAME', 'MODAL_FUNCTION_NAME'):
            if not isinstance(self.config.get(key), str) or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,100}', self.config[key]) is None:
                raise UnconfiguredBackendError('Modal deployment/function is not configured')
        environment = self.config.get('MODAL_ENVIRONMENT')
        if environment is not None and (not isinstance(environment, str) or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,100}', environment) is None):
            raise UnconfiguredBackendError('Invalid Modal environment configuration')
        if self.transport is None and importlib.util.find_spec('modal') is None:
            raise UnconfiguredBackendError('Modal SDK is not installed; remote inference remains blocked')
        if self.transport is None and (not self.config.get('MODAL_SDK_VERSION')
                or version('modal') != self.config['MODAL_SDK_VERSION']):
            raise UnconfiguredBackendError('Installed Modal SDK version does not match its verified configuration')
    def submit(self, request):
        if not isinstance(request,InferenceRequest):
            raise ValueError('Expected a validated bounded inference request')
        self.ensure_ready()
        transport = self.transport or OfficialModalTransport()
        job = transport.spawn(self.config['MODAL_APP_NAME'], self.config['MODAL_FUNCTION_NAME'],
                              self.config.get('MODAL_ENVIRONMENT'), request.to_payload())
        return Submission(_job_id(job), 'pending')
    def poll(self, job_id, timeout_seconds=0):
        self.ensure_ready()
        _poll_timeout(timeout_seconds)
        _job_id(job_id)
        try:
            result = (self.transport or OfficialModalTransport()).get(job_id, timeout_seconds)
        except TimeoutError:
            return Submission(job_id, 'pending')
        if not isinstance(result, dict):
            raise ProviderError('Modal worker returned an invalid result envelope')
        return Submission(job_id, 'completed', result)

class RunPodESMProvider:
    def ensure_ready(self):
        raise UnconfiguredBackendError('RunPod is explicitly unconfigured; no fallback provider is enabled')
    def submit(self, request):
        self.ensure_ready()
    def poll(self, job_id, timeout_seconds=0):
        self.ensure_ready()

def provider_from_config(config, *, local_engine=None, transport=None, execution_approved=False):
    data = backend_config(config)
    if data['ESM_BACKEND'] == 'local':
        return LocalESMProvider(local_engine)
    if data['ESM_BACKEND'] == 'modal':
        return ModalESMProvider(data, transport=transport, execution_approved=execution_approved)
    return RunPodESMProvider()
