"""The explicit execution boundary for the unified local workbench."""
import json
from pathlib import Path

from app import session_exec
from app.review_flow import result_phase
from app.science.provider_config import load_esm_settings


def local_configuration(esm_env):
    """Inspect public local configuration only. Never load a model or call a provider."""
    settings=load_esm_settings(esm_env)
    if settings['ESM_BACKEND']!='local' or settings['ESM_DEVICE']!='cpu':
        raise ValueError('This launch enables local CPU ESM only. Remote GPU requires a separate approved configuration.')
    if settings['ESM_MODEL_KEY'] not in ('esm150','esm650'):
        raise ValueError('The unified review requires a registered 150M or 650M checkpoint.')
    checkpoint=settings['ESM_LOCAL_CHECKPOINT_DIR']
    if not checkpoint or not Path(checkpoint).is_dir() or not settings['ESM_WEIGHTS_SHA256'] or not settings['ESM_TOKENIZER_SHA256']:
        raise ValueError('Pinned local checkpoint settings are missing. No execution is available.')
    return {'backend':'local','device':'cpu','model_key':settings['ESM_MODEL_KEY'],
            'pins_checked_during_execution':True,'provider_cost':'unknown / unverified'}


def execute_review(store, review_id, *, root, esm_env, approved=False, max_requests=4):
    if type(max_requests) is not int or not 3<=max_requests<=4:
        raise ValueError('Scientific review requires a cap of 3–4 Meta requests before execution can be claimed.')
    if approved is not True:
        raise ValueError('Explicit approval is required before claiming a review.')
    config=local_configuration(esm_env)
    frozen=store.get(review_id)['request']
    if frozen['model_key']!=config['model_key']:
        raise ValueError('Checkpoint configuration changed. Validate a fresh review.')
    row=store.claim(review_id,approved=True)
    workspace=store.workspace(review_id)
    workspace.parent.mkdir(exist_ok=True)
    try:
        result=session_exec.run_session(root, workspace, positions=frozen['positions'],
            model_key=frozen['model_key'],esm_env=esm_env,
            budget=session_exec.SessionBudget(max_runs=1,max_requests_per_run=max_requests),
            armed=True,goal_text=frozen['message'])
        # Preserve the exact report bytes returned by the existing controlled host.
        raw=result.get('stdout','').encode('utf-8')
        try:
            report=json.loads(raw)
        except (ValueError,TypeError):
            report={}
        if isinstance(report,dict) and 'status' in report:
            return store.finish(review_id,status=result_phase(report['status']),report=raw,
                error=None if result.get('returncode')==0 else 'Execution returned a partial or failed result; inspect the saved stop reason.')
        return store.finish(review_id,status='failed',
            error=f"Controlled {result.get('stage','execution')} returned no valid report (exit {result.get('returncode')}). No automatic retry.")
    except Exception as error:
        # The claim is never released, including on timeout/unknown provider outcome.
        return store.finish(review_id,status='failed',
            error=f'{type(error).__name__}: execution stopped. Inspect the local run record before any deliberate new request. No automatic retry.')
