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


BASE_LOCAL = {'ESM_BACKEND':'local','ESM_MODEL_KEY':'esm150',
    'ESM_LOCAL_CHECKPOINT_DIR':'/nonexistent','ESM_WEIGHTS_SHA256':'a'*64,
    'ESM_TOKENIZER_SHA256':'b'*64}
WITH_VERIFIER = {**BASE_LOCAL,'ESM_VERIFIER_MODEL_KEY':'esm650',
    'ESM_VERIFIER_CHECKPOINT_DIR':'/nonexistent-verifier',
    'ESM_VERIFIER_WEIGHTS_SHA256':'c'*64,'ESM_VERIFIER_TOKENIZER_SHA256':'d'*64}


def test_verifier_is_absent_by_default():
    assert load_esm_settings(environ={})['ESM_VERIFIER_MODEL_KEY'] is None


def test_verifier_must_be_a_different_registered_model():
    with pytest.raises(ValueError):
        load_esm_settings(environ={**WITH_VERIFIER,'ESM_VERIFIER_MODEL_KEY':'esm150'})
    with pytest.raises(ValueError):
        load_esm_settings(environ={**WITH_VERIFIER,'ESM_VERIFIER_MODEL_KEY':'esm8'})


@pytest.mark.parametrize('field', ['ESM_VERIFIER_WEIGHTS_SHA256','ESM_VERIFIER_TOKENIZER_SHA256'])
def test_verifier_without_its_own_trusted_pins_is_refused_before_any_checkpoint_load(field):
    """Pins are validated before a backend is built, so a bad pin never loads weights."""
    settings = load_esm_settings(environ={**WITH_VERIFIER, field:'not-a-pin'})
    with pytest.raises(ValueError, match='pins'):
        make_inference_service(None, settings)


def test_verifier_without_a_checkpoint_directory_is_refused():
    settings = load_esm_settings(environ=WITH_VERIFIER)
    settings['ESM_VERIFIER_CHECKPOINT_DIR'] = None
    with pytest.raises(ValueError, match='[Vv]erifier checkpoint directory'):
        make_inference_service(None, settings)


def test_a_verifier_is_not_wired_for_remote_backends():
    settings = load_esm_settings(environ={**WITH_VERIFIER,'ESM_BACKEND':'modal'})
    with pytest.raises(ValueError, match='local backend'):
        make_inference_service(None, settings)
