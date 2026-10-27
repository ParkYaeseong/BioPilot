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

def make_inference_service(context, settings):
    from app.science.providers import LocalESMProvider, ModalESMProvider, UnconfiguredBackendError, canonical_digest
    from app.science.inference_service import InferenceService
    backend_key=settings['ESM_BACKEND']
    if backend_key=='runpod':
        raise UnconfiguredBackendError('RunPod is explicitly unconfigured')
    pins={settings['ESM_MODEL_KEY']:{'expected_weights_sha256':settings['ESM_WEIGHTS_SHA256'],
                                  'expected_tokenizer_sha256':settings['ESM_TOKENIZER_SHA256']}}
    if backend_key=='local':
        from app.science.esm_engine import ESMEngine,LocalHFBackend
        if not settings['ESM_LOCAL_CHECKPOINT_DIR']:
            raise UnconfiguredBackendError('Local checkpoint is not configured; downloads are disabled')
        backend=LocalHFBackend(settings['ESM_LOCAL_CHECKPOINT_DIR'],
            expected_weights_sha256=settings['ESM_WEIGHTS_SHA256'],expected_tokenizer_sha256=settings['ESM_TOKENIZER_SHA256'],
            checkpoint_key=settings['ESM_MODEL_KEY'],device=settings['ESM_DEVICE'])
        provider=LocalESMProvider(ESMEngine(backend,Path(context.db_path).parent/'esm_cache'))
        estimate=0
    else:
        config={key:settings[key] for key in ('ESM_BACKEND','MODAL_APP_NAME','MODAL_FUNCTION_NAME',
                'MODAL_ENVIRONMENT','MODAL_SDK_VERSION','MODAL_COMPATIBILITY_VERIFIED')}
        provider=ModalESMProvider(config,execution_approved=settings['ESM_REMOTE_EXECUTION_APPROVED'])
        provider.ensure_ready()
        estimate=settings['ESM_REMOTE_ESTIMATE_MICROS']
        if estimate<=0:
            raise UnconfiguredBackendError('Remote work needs an approved conservative cost estimate')
    if any(not isinstance(value,str) or re.fullmatch('[0-9a-f]{64}',value) is None
           for value in pins[settings['ESM_MODEL_KEY']].values()):
        raise UnconfiguredBackendError('Trusted checkpoint/tokenizer pins are required before exposing ESM capability')
    binding=settings['ESM_PROVIDER_BINDING'] or canonical_digest({k:v for k,v in settings.items()
        if k not in {'ESM_LOCAL_CHECKPOINT_DIR','ESM_REMOTE_EXECUTION_APPROVED'}})
    return InferenceService(context.db_path,provider,backend_key,binding,estimate_micros=estimate,
                            model_pins=pins,job_timeout_seconds=900 if backend_key!='local' else None)
