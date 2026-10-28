"""Trusted launcher settings. Configuration never serializes provider credentials.

Approval flags belong to the operator/launcher; they are not MCP tool arguments.
Default Modal selection does not enable remote work or create a deployment.
"""
import os
import re
from pathlib import Path
from app.science.models import get_model_spec

DEFAULTS={
    'ESM_BACKEND':'modal','ESM_MODEL_KEY':'esm150','ESM_DEVICE':'cpu',
    'ESM_LOCAL_CHECKPOINT_DIR':None,'ESM_WEIGHTS_SHA256':None,'ESM_TOKENIZER_SHA256':None,
    'ESM_REMOTE_EXECUTION_APPROVED':False,'ESM_REMOTE_ESTIMATE_MICROS':0,
    'ESM_REMOTE_TIMEOUT_SECONDS':900,'ESM_PROVIDER_BINDING':None,
    # Optional second checkpoint. Absent by default: a verifier is extra evidence,
    # never a reranker, and it must carry its own trusted pins.
    'ESM_VERIFIER_MODEL_KEY':None,'ESM_VERIFIER_CHECKPOINT_DIR':None,
    'ESM_VERIFIER_WEIGHTS_SHA256':None,'ESM_VERIFIER_TOKENIZER_SHA256':None,
    'MODAL_APP_NAME':None,'MODAL_FUNCTION_NAME':None,'MODAL_ENVIRONMENT':None,
    'MODAL_SDK_VERSION':None,'MODAL_COMPATIBILITY_VERIFIED':False,
}

def _boolean(value):
    if type(value) is bool: return value
    if value in ('true','false'): return value=='true'
    raise ValueError('Boolean ESM settings must be exactly true or false')

def load_esm_settings(env_file=None, environ=None):
    selected=dict(DEFAULTS)
    if env_file is not None:
        from dotenv import dotenv_values
        values=dotenv_values(env_file,interpolate=False)
        selected.update({key:values[key] for key in DEFAULTS if values.get(key) not in (None,'')})
        values=None
    source=os.environ if environ is None else environ
    selected.update({key:source[key] for key in DEFAULTS if source.get(key) not in (None,'')})
    if selected['ESM_BACKEND'] not in {'local','modal','runpod'}:
        raise ValueError('Unknown ESM_BACKEND; no fallback')
    if selected['ESM_DEVICE'] not in {'cpu','cuda'}:
        raise ValueError('ESM_DEVICE must explicitly select cpu or cuda')
    get_model_spec(selected['ESM_MODEL_KEY'])
    verifier=selected['ESM_VERIFIER_MODEL_KEY']
    if verifier is not None:
        get_model_spec(verifier)
        if verifier==selected['ESM_MODEL_KEY']:
            raise ValueError('The verifier checkpoint must differ from the baseline model')
    for key in ('ESM_REMOTE_EXECUTION_APPROVED','MODAL_COMPATIBILITY_VERIFIED'):
        selected[key]=_boolean(selected[key])
    for key in ('ESM_REMOTE_TIMEOUT_SECONDS','ESM_REMOTE_ESTIMATE_MICROS'):
        value=selected[key]
        if type(value) is bool or not str(value).isdigit():
            raise ValueError('ESM time and money settings require nonnegative integers')
        selected[key]=int(value)
    if not 1<=selected['ESM_REMOTE_TIMEOUT_SECONDS']<=900:
        raise ValueError('Remote job timeout must be 1..900 seconds')
    return selected

class RoutingLocalProvider:
    """Dispatch to the local provider that owns the requested checkpoint.

    Each wrapped provider still verifies its own pins and checkpoint identity, so
    routing cannot smuggle one checkpoint's weights under another model key.
    """

    def __init__(self, providers):
        self._providers=dict(providers)
        self._routes={}

    def ensure_ready(self):
        for provider in self._providers.values():
            provider.ensure_ready()

    def _for(self, model_key):
        provider=self._providers.get(model_key)
        if provider is None:
            from app.science.providers import UnconfiguredBackendError
            raise UnconfiguredBackendError('No configured local checkpoint for the requested model')
        return provider

    def submit(self, request):
        provider=self._for(request.model_key)
        submission=provider.submit(request)
        self._routes[submission.job_id]=request.model_key
        return submission

    def poll(self, job_id, timeout_seconds):
        model_key=self._routes.get(job_id)
        if model_key is None:
            from app.science.providers import ProviderError
            raise ProviderError('Unknown local job for this provider')
        return self._providers[model_key].poll(job_id, timeout_seconds)


def make_inference_service(context, settings):
    from app.science.providers import LocalESMProvider, ModalESMProvider, UnconfiguredBackendError, canonical_digest
    from app.science.inference_service import InferenceService
    backend_key=settings['ESM_BACKEND']
    if backend_key=='runpod':
        raise UnconfiguredBackendError('RunPod is explicitly unconfigured')
    baseline_key=settings['ESM_MODEL_KEY']
    verifier_key=settings['ESM_VERIFIER_MODEL_KEY']
    pins={baseline_key:{'expected_weights_sha256':settings['ESM_WEIGHTS_SHA256'],
                        'expected_tokenizer_sha256':settings['ESM_TOKENIZER_SHA256']}}
    if verifier_key is not None:
        pins[verifier_key]={'expected_weights_sha256':settings['ESM_VERIFIER_WEIGHTS_SHA256'],
                            'expected_tokenizer_sha256':settings['ESM_VERIFIER_TOKENIZER_SHA256']}
    # Validate every pin before a checkpoint is touched: a malformed pin must never
    # reach the point of loading weights.
    if any(not isinstance(value,str) or re.fullmatch('[0-9a-f]{64}',value) is None
           for entry in pins.values() for value in entry.values()):
        raise UnconfiguredBackendError('Trusted checkpoint/tokenizer pins are required before exposing ESM capability')
    if verifier_key is not None:
        if backend_key!='local':
            raise UnconfiguredBackendError('The optional verifier checkpoint is only wired for the local backend')
        if not settings['ESM_VERIFIER_CHECKPOINT_DIR']:
            raise UnconfiguredBackendError('Verifier checkpoint directory is not configured; downloads are disabled')
    if backend_key=='local':
        from app.science.esm_engine import ESMEngine,LocalHFBackend
        if not settings['ESM_LOCAL_CHECKPOINT_DIR']:
            raise UnconfiguredBackendError('Local checkpoint is not configured; downloads are disabled')
        cache=Path(context.db_path).parent/'esm_cache'
        def _local(directory,key,weights,tokenizer):
            return LocalESMProvider(ESMEngine(LocalHFBackend(directory,
                expected_weights_sha256=weights,expected_tokenizer_sha256=tokenizer,
                checkpoint_key=key,device=settings['ESM_DEVICE']),cache))
        provider=_local(settings['ESM_LOCAL_CHECKPOINT_DIR'],baseline_key,
            settings['ESM_WEIGHTS_SHA256'],settings['ESM_TOKENIZER_SHA256'])
        if verifier_key is not None:
            provider=RoutingLocalProvider({baseline_key:provider,
                verifier_key:_local(settings['ESM_VERIFIER_CHECKPOINT_DIR'],verifier_key,
                    settings['ESM_VERIFIER_WEIGHTS_SHA256'],settings['ESM_VERIFIER_TOKENIZER_SHA256'])})
        estimate=0
    else:
        config={key:settings[key] for key in ('ESM_BACKEND','MODAL_APP_NAME','MODAL_FUNCTION_NAME',
                'MODAL_ENVIRONMENT','MODAL_SDK_VERSION','MODAL_COMPATIBILITY_VERIFIED')}
        provider=ModalESMProvider(config,execution_approved=settings['ESM_REMOTE_EXECUTION_APPROVED'])
        provider.ensure_ready()
        estimate=settings['ESM_REMOTE_ESTIMATE_MICROS']
        if estimate<=0:
            raise UnconfiguredBackendError('Remote work needs an approved conservative cost estimate')
    binding=settings['ESM_PROVIDER_BINDING'] or canonical_digest({k:v for k,v in settings.items()
        if k not in {'ESM_LOCAL_CHECKPOINT_DIR','ESM_REMOTE_EXECUTION_APPROVED'}})
    return InferenceService(context.db_path,provider,backend_key,binding,estimate_micros=estimate,
                            model_pins=pins,job_timeout_seconds=900 if backend_key!='local' else None)
