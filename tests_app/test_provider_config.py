import pytest
from app.science.provider_config import load_esm_settings, make_inference_service

def test_default_modal_is_blocked_not_silent_local_fallback():
    settings=load_esm_settings(environ={})
    assert settings['ESM_BACKEND']=='modal'
    assert settings['ESM_REMOTE_EXECUTION_APPROVED'] is False
    assert settings['MODAL_COMPATIBILITY_VERIFIED'] is False
    with pytest.raises(ValueError):
        make_inference_service(None,settings)

def test_env_whitelist_and_precedence_without_meta_key(tmp_path):
    path=tmp_path/'.env';path.write_text('ESM_BACKEND=local\nMETA_API_KEY=fixture\nMODEL_API_KEY=fixture\n')
    settings=load_esm_settings(path,environ={'ESM_BACKEND':'runpod','MODAL_TOKEN_SECRET':'fixture-secret'})
    assert settings['ESM_BACKEND']=='runpod'
    assert not any('API_KEY' in k or 'TOKEN_SECRET' in k for k in settings)
    assert 'fixture' not in str(settings)

@pytest.mark.parametrize('settings',[{'ESM_BACKEND':'arbitrary'}, {'ESM_DEVICE':'auto'},
    {'ESM_REMOTE_TIMEOUT_SECONDS':'0'}, {'ESM_REMOTE_TIMEOUT_SECONDS':'901'},
    {'ESM_REMOTE_EXECUTION_APPROVED':'yes'}, {'ESM_MODEL_KEY':'esm8'}])
def test_unknown_or_ambiguous_configuration_blocked(settings):
    with pytest.raises(ValueError): load_esm_settings(environ=settings)

def test_runpod_is_explicitly_unconfigured():
    settings=load_esm_settings(environ={'ESM_BACKEND':'runpod'})
    with pytest.raises(ValueError,match='RunPod|runpod'):
        make_inference_service(None,settings)
