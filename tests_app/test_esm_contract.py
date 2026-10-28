"""Synthetic logits test arithmetic and boundaries, not ESM biological performance."""
from dataclasses import dataclass, replace
from hashlib import sha256
import json
import sys
from types import SimpleNamespace

import pytest

from app.science.esm_engine import ESMEngine, LocalHFBackend
from app.science.ranking import rank_candidates
from app.science.models import MODEL_REGISTRY, get_model_spec


AA = 'ACDEFGHIKLMNPQRSTVWY'
PROFILE = json.loads((__import__('pathlib').Path(__file__).resolve().parents[1] / 'reference/target_profile.json').read_text())


@dataclass(frozen=True)
class Target:
    reference_sequence: str = PROFILE['reference_sequence']
    reference_sha256: str = PROFILE['reference_sha256']
    sequence_context: str = 'full_212'
    protected_positions: tuple = (108, 164, 187)
    reference_id: str = PROFILE['reference_id']
    reference_numbering: str = 'full_reference_1based'


class SyntheticBackend:
    """Deterministic artificial vocabulary; deliberately not real inference."""
    mask_token_id = 22
    provenance = {
        'checkpoint': 'esm2_t30_150M_UR50D',
        'weights_sha256': 'a' * 64,
        'tokenizer_sha256': 'b' * 64,
        'implementation': 'synthetic_fixture_v1',
        'precision': 'float32',
        'source_mode': 'synthetic_fixture',
    }

    def __init__(self):
        self.calls = []
        self.provenance = dict(self.provenance)

    def token_id(self, residue):
        return AA.index(residue) + 1

    def tokenize(self, sequence):
        return [0] + [self.token_id(aa) for aa in sequence] + [21]

    def forward(self, tokens):
        self.calls.append(list(tokens))
        # Log-softmax differences equal these logit differences.
        return [[float(v) for v in range(23)] for _ in tokens]


def test_mask_alignment_sign_wt_and_all_nineteen_alternatives():
    backend = SyntheticBackend()
    result = ESMEngine(backend).score_positions(Target(), [32])
    assert backend.calls[0][32] == backend.mask_token_id
    assert backend.calls[0][0] == 0 and backend.calls[0][-1] == 21
    assert len(backend.calls) == 1
    assert len(result['rows']) == 19
    row = next(r for r in result['rows'] if r['candidate_id'] == 'A32V')
    assert row['wild_type'] == 'A'
    assert row['score'] == pytest.approx(backend.token_id('V') - backend.token_id('A'))
    assert result['source_mode'] == 'synthetic_fixture'
    assert len(result['artifact_sha256']) == 64
    assert result['phenotype_calibrated'] is False


def test_distribution_reused_by_position_and_persisted_with_exact_identity(tmp_path):
    backend = SyntheticBackend()
    engine = ESMEngine(backend, tmp_path)
    a = engine.score_positions(Target(), [32])
    b = engine.score_positions(Target(), [32])
    assert a['rows'] == b['rows']
    assert len(backend.calls) == 1
    other = SyntheticBackend()
    ESMEngine(other, tmp_path).score_positions(Target(), [32])
    assert len(other.calls) == 0
    changed = SyntheticBackend()
    changed.provenance['weights_sha256'] = 'c' * 64
    ESMEngine(changed, tmp_path).score_positions(Target(), [32])
    assert len(changed.calls) == 1
    changed_tokenizer = SyntheticBackend()
    changed_tokenizer.provenance['tokenizer_sha256'] = 'd' * 64
    ESMEngine(changed_tokenizer, tmp_path).score_positions(Target(), [32])
    assert len(changed_tokenizer.calls) == 1


@pytest.mark.parametrize('positions', [[], [32, 32], [0], [1], [213], [True], [108], [164], [187], [32.0]])
def test_invalid_or_protected_positions_rejected_before_inference(positions):
    backend = SyntheticBackend()
    with pytest.raises(ValueError):
        ESMEngine(backend).score_positions(Target(), positions)
    assert backend.calls == []


def test_mature_context_or_wrong_hash_rejected_before_inference():
    backend = SyntheticBackend()
    for target in [replace(Target(), sequence_context='mature_181'), replace(Target(), reference_sha256='0' * 64)]:
        with pytest.raises(ValueError):
            ESMEngine(backend).score_positions(target, [32])
    assert not backend.calls


def test_disabled_checkpoint_cannot_be_scored_or_mislabeled():
    backend = SyntheticBackend()
    with pytest.raises(ValueError):
        ESMEngine(backend).score_positions(Target(), [32], 'esm650')
    backend.provenance['checkpoint'] = 'esm2_t33_650M_UR50D'
    with pytest.raises(ValueError):
        ESMEngine(backend).score_positions(Target(), [32])


def test_bad_tokenizer_alignment_blocked_before_forward():
    backend = SyntheticBackend()
    backend.tokenize = lambda sequence: [backend.token_id(a) for a in sequence]
    with pytest.raises(ValueError, match='token'):
        ESMEngine(backend).score_positions(Target(), [32])
    assert backend.calls == []


def test_nonfinite_logits_fail_instead_of_creating_an_artifact():
    backend = SyntheticBackend()
    backend.forward = lambda tokens: [[float('nan')] * 23 for _ in tokens]
    with pytest.raises(ValueError):
        ESMEngine(backend).score_positions(Target(), [32])


def test_rank_ignores_optional_annotations_and_ties_use_candidate_id():
    rows = ESMEngine(SyntheticBackend()).score_positions(Target(), [32])['rows']
    rows[0]['score'] = rows[1]['score'] = 100.0
    rows[0]['atlas_bonus'] = -100000
    rows[1]['esm650_score'] = 100000
    expected = sorted([rows[0]['candidate_id'], rows[1]['candidate_id']])
    ranked = rank_candidates(rows)
    assert [r['candidate_id'] for r in ranked[:2]] == expected


@pytest.mark.parametrize('key,value', [('checkpoint', 'esm2_t33_650M_UR50D'), ('sequence_context', 'mature_181'), ('weights_sha256', '0' * 64), ('tokenizer_sha256', '0' * 64), ('reference_sha256', '0' * 64)])
def test_mixed_provenance_rank_is_blocked(key, value):
    rows = ESMEngine(SyntheticBackend()).score_positions(Target(), [32])['rows']
    rows[-1][key] = value
    with pytest.raises(ValueError):
        rank_candidates(rows)


def test_unknown_policy_duplicate_ids_and_nonfinite_rank_blocked():
    rows = ESMEngine(SyntheticBackend()).score_positions(Target(), [32])['rows']
    with pytest.raises(ValueError):
        rank_candidates(rows, 'T50_prediction')
    with pytest.raises(ValueError):
        rank_candidates([rows[0], rows[0]])
    rows[0]['score'] = float('inf')
    with pytest.raises(ValueError):
        rank_candidates(rows)


def test_cache_tamper_is_rejected(tmp_path):
    engine = ESMEngine(SyntheticBackend(), tmp_path)
    engine.score_positions(Target(), [32])
    cache_file = next(tmp_path.glob('*.json'))
    document = json.loads(cache_file.read_text())
    document['payload']['scores']['V'] = 10000
    cache_file.write_text(json.dumps(document))
    with pytest.raises(ValueError, match='cache'):
        ESMEngine(SyntheticBackend(), tmp_path).score_positions(Target(), [32])


def test_missing_real_local_checkpoint_stays_unavailable_without_download(tmp_path):
    with pytest.raises(ValueError, match='checkpoint'):
        LocalHFBackend(tmp_path)


def test_altered_frame_or_missing_protection_is_rejected():
    for target in [replace(Target(), protected_positions=()), replace(Target(), reference_numbering='mature_1based')]:
        with pytest.raises(ValueError):
            ESMEngine(SyntheticBackend()).score_positions(target, [32])


def test_user_extra_protection_cannot_be_scored():
    target = replace(Target(), protected_positions=(32, 108, 164, 187))
    with pytest.raises(ValueError):
        ESMEngine(SyntheticBackend()).score_positions(target, [32])


def test_local_backend_requires_trusted_pins_before_model_load(tmp_path):
    (tmp_path / 'config.json').write_text(json.dumps({
        'model_type': 'esm', 'num_hidden_layers': 30, 'hidden_size': 640, 'num_attention_heads': 20,
    }))
    (tmp_path / 'vocab.txt').write_text('synthetic fixture, never a real model')
    (tmp_path / 'model.safetensors').write_bytes(b'synthetic fixture, never load')
    with pytest.raises(ValueError, match='trusted'):
        LocalHFBackend(tmp_path)
    with pytest.raises(ValueError, match='hash'):
        LocalHFBackend(tmp_path, expected_weights_sha256='0' * 64, expected_tokenizer_sha256='1' * 64)


def test_unknown_rank_source_mode_is_rejected():
    rows = ESMEngine(SyntheticBackend()).score_positions(Target(), [32])['rows']
    for row in rows:
        row.pop('source_mode')
    with pytest.raises(ValueError):
        rank_candidates(rows)


def test_incomplete_checkpoint_cannot_be_randomly_initialized_as_real(tmp_path, monkeypatch):
    from app.science.esm_engine import _digest, _file_hash
    (tmp_path / 'config.json').write_text(json.dumps({
        'model_type': 'esm', 'num_hidden_layers': 30, 'hidden_size': 640, 'num_attention_heads': 20,
    }))
    (tmp_path / 'vocab.txt').write_text('synthetic loader contract fixture')
    (tmp_path / 'model.safetensors').write_bytes(b'synthetic loader contract fixture')
    weights = _digest({'model.safetensors': _file_hash(tmp_path / 'model.safetensors')})
    tokenizer = _digest({name: _file_hash(tmp_path / name) for name in ('config.json', 'vocab.txt')})
    fake_model = SimpleNamespace(to=lambda **kw: SimpleNamespace(eval=lambda: SimpleNamespace()))

    def load_model(*args, **kwargs):
        if kwargs.get('output_loading_info'):
            return fake_model, {'missing_keys': ['encoder.layer.0.weight'], 'unexpected_keys': [], 'mismatched_keys': [], 'error_msgs': []}
        return fake_model

    fake_transformers = SimpleNamespace(
        AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a, **kw: SimpleNamespace(mask_token_id=22)),
        AutoModelForMaskedLM=SimpleNamespace(from_pretrained=load_model),
    )
    monkeypatch.setitem(sys.modules, 'transformers', fake_transformers)
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(float32='float32'))
    with pytest.raises(ValueError, match='incomplete'):
        LocalHFBackend(tmp_path, expected_weights_sha256=weights, expected_tokenizer_sha256=tokenizer)


@pytest.mark.parametrize('key,checkpoint,layers,width,heads', [
    ('esm35', 'esm2_t12_35M_UR50D', 12, 480, 20),
    ('esm150', 'esm2_t30_150M_UR50D', 30, 640, 20),
    ('esm650', 'esm2_t33_650M_UR50D', 33, 1280, 20),
])
def test_model_registry_is_explicit_and_immutable(key, checkpoint, layers, width, heads):
    spec = get_model_spec(key)
    assert (spec.checkpoint, spec.num_hidden_layers, spec.hidden_size, spec.num_attention_heads) == (checkpoint, layers, width, heads)
    assert spec.rank_policy == f'{key}_masked_v1'
    with pytest.raises((AttributeError, TypeError)):
        spec.hidden_size = 1
    with pytest.raises(TypeError):
        MODEL_REGISTRY['arbitrary'] = spec


@pytest.mark.parametrize('key', ['esm35', 'esm150', 'esm650'])
def test_explicit_checkpoint_has_its_own_scores_cache_and_rank_policy(key, tmp_path):
    spec = get_model_spec(key)
    backend = SyntheticBackend()
    backend.provenance['checkpoint'] = spec.checkpoint
    artifact = ESMEngine(backend, tmp_path).score_positions(Target(), [32], key)
    assert artifact['rank_policy'] == spec.rank_policy
    assert artifact['provenance']['model_key'] == key
    assert all(row['checkpoint'] == spec.checkpoint for row in artifact['rows'])
    assert len(rank_candidates(artifact['rows'], spec.rank_policy)) == 19
    if key != 'esm150':
        with pytest.raises(ValueError):
            rank_candidates(artifact['rows'])
        with pytest.raises(ValueError):
            ESMEngine(backend, tmp_path).score_positions(Target(), [32])


def test_no_model_key_or_rank_policy_fallback():
    for key in ('esm3', None, '', 'facebook/esm2_t30_150M_UR50D'):
        with pytest.raises(ValueError):
            get_model_spec(key)
        with pytest.raises(ValueError):
            ESMEngine(SyntheticBackend()).score_positions(Target(), [32], key)


def test_cross_model_cache_cannot_supply_another_model(tmp_path):
    small = SyntheticBackend()
    small.provenance['checkpoint'] = 'esm2_t12_35M_UR50D'
    large = SyntheticBackend()
    large.provenance['checkpoint'] = 'esm2_t33_650M_UR50D'
    ESMEngine(small, tmp_path).score_positions(Target(), [32], 'esm35')
    ESMEngine(large, tmp_path).score_positions(Target(), [32], 'esm650')
    assert len(small.calls) == len(large.calls) == 1
    assert len(list(tmp_path.glob('*.json'))) == 2


def test_explicit_large_policy_rejects_partial_small_score_replacement():
    large = SyntheticBackend()
    large.provenance['checkpoint'] = 'esm2_t33_650M_UR50D'
    artifact = ESMEngine(large).score_positions(Target(), [32], 'esm650')
    artifact['rows'][0]['checkpoint'] = 'esm2_t30_150M_UR50D'
    with pytest.raises(ValueError):
        rank_candidates(artifact['rows'], 'esm650_masked_v1')


def _synthetic_local_checkpoint(tmp_path, config):
    from app.science.esm_engine import _digest, _file_hash
    (tmp_path / 'config.json').write_text(json.dumps(config))
    (tmp_path / 'vocab.txt').write_text('synthetic loader contract fixture')
    (tmp_path / 'model.safetensors').write_bytes(b'synthetic loader contract fixture')
    weights = _digest({'model.safetensors': _file_hash(tmp_path / 'model.safetensors')})
    tokenizer = _digest({name: _file_hash(tmp_path / name) for name in ('config.json', 'vocab.txt')})
    return dict(expected_weights_sha256=weights, expected_tokenizer_sha256=tokenizer)


@pytest.mark.parametrize('key,layers,width', [('esm35', 12, 480), ('esm150', 30, 640), ('esm650', 33, 1280)])
def test_local_model_architecture_is_matched_to_requested_key(key, layers, width, tmp_path, monkeypatch):
    pins = _synthetic_local_checkpoint(tmp_path, {
        'model_type': 'esm', 'num_hidden_layers': layers, 'hidden_size': width, 'num_attention_heads': 20,
    })
    placed = []
    fake_model = SimpleNamespace(to=lambda **kw: (placed.append(kw) or SimpleNamespace(eval=lambda: SimpleNamespace())))
    fake_transformers = SimpleNamespace(
        AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a, **kw: SimpleNamespace(mask_token_id=22)),
        AutoModelForMaskedLM=SimpleNamespace(from_pretrained=lambda *a, **kw: (fake_model, {})),
    )
    monkeypatch.setitem(sys.modules, 'transformers', fake_transformers)
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(float32='float32'))
    backend = LocalHFBackend(tmp_path, **pins, checkpoint_key=key, device='cpu')
    assert backend.provenance['checkpoint'] == get_model_spec(key).checkpoint
    assert backend.provenance['model_key'] == key
    assert backend.provenance['device'] == 'cpu'
    assert placed == [{'device': 'cpu', 'dtype': 'float32'}]
    other_key = 'esm35' if key != 'esm35' else 'esm650'
    with pytest.raises(ValueError, match='architecture'):
        LocalHFBackend(tmp_path, **pins, checkpoint_key=other_key, device='cpu')


def test_cuda_unavailable_blocks_without_falling_back_to_cpu(tmp_path, monkeypatch):
    pins = _synthetic_local_checkpoint(tmp_path, {
        'model_type': 'esm', 'num_hidden_layers': 30, 'hidden_size': 640, 'num_attention_heads': 20,
    })
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(float32='float32', cuda=SimpleNamespace(is_available=lambda: False)))
    monkeypatch.setitem(sys.modules, 'transformers', SimpleNamespace())
    with pytest.raises(ValueError, match='CUDA'):
        LocalHFBackend(tmp_path, **pins, device='cuda')


@pytest.mark.parametrize('device', ['auto', 'cuda:1', 'mps', '', None])
def test_local_device_is_explicit_with_no_fallback(device, tmp_path):
    with pytest.raises(ValueError, match='device'):
        LocalHFBackend(tmp_path, device=device)


def _legacy_buffer_checkpoint(tmp_path, monkeypatch, *, config_changes=None,
                              tensor_change=None, loading_changes=None):
    """Tiny safetensors buffer and mocked model loader; never real ESM weights."""
    import numpy as np
    from safetensors.numpy import save_file
    from app.science.esm_engine import _digest, _file_hash
    key='esm.embeddings.position_ids'
    config={'model_type':'esm','num_hidden_layers':30,'hidden_size':640,
            'num_attention_heads':20,'position_embedding_type':'rotary',
            'max_position_embeddings':1026,**(config_changes or {})}
    (tmp_path/'config.json').write_text(json.dumps(config))
    (tmp_path/'vocab.txt').write_text('synthetic loader fixture')
    tensors={key:np.arange(1026,dtype=np.int64).reshape(1,1026)}
    if tensor_change:
        tensors=tensor_change(tensors)
    save_file(tensors,str(tmp_path/'model.safetensors'))
    pins={'expected_weights_sha256':_digest({'model.safetensors':_file_hash(tmp_path/'model.safetensors')}),
          'expected_tokenizer_sha256':_digest({name:_file_hash(tmp_path/name) for name in ('config.json','vocab.txt')})}
    placed=[]
    fake_model=SimpleNamespace(to=lambda **kwargs:(placed.append(kwargs) or SimpleNamespace(eval=lambda:SimpleNamespace())))
    loading={'unexpected_keys':{key},'missing_keys':set(),'mismatched_keys':set(),
             'error_msgs':[],**(loading_changes or {})}
    monkeypatch.setitem(sys.modules,'transformers',SimpleNamespace(
        AutoTokenizer=SimpleNamespace(from_pretrained=lambda *args,**kwargs:SimpleNamespace(mask_token_id=22)),
        AutoModelForMaskedLM=SimpleNamespace(from_pretrained=lambda *args,**kwargs:(fake_model,loading))))
    monkeypatch.setitem(sys.modules,'torch',SimpleNamespace(float32='float32'))
    return pins,placed


@pytest.mark.parametrize('reported_keys',[{'esm.embeddings.position_ids'},['esm.embeddings.position_ids']])
def test_exact_legacy_nonpersistent_position_buffer_is_recorded(tmp_path,monkeypatch,reported_keys):
    pins,placed=_legacy_buffer_checkpoint(tmp_path,monkeypatch,loading_changes={'unexpected_keys':reported_keys})
    backend=LocalHFBackend(tmp_path,**pins)
    assert placed==[{'device':'cpu','dtype':'float32'}]
    assert backend.provenance['ignored_nonpersistent_buffers']==['esm.embeddings.position_ids']
    assert backend.provenance['weights_sha256']==pins['expected_weights_sha256']


@pytest.mark.parametrize('change',[
    {'position_embedding_type':'absolute'}, {'max_position_embeddings':1025},
    {'max_position_embeddings':True},
])
def test_legacy_position_buffer_requires_exact_rotary_configuration(tmp_path,monkeypatch,change):
    pins,placed=_legacy_buffer_checkpoint(tmp_path,monkeypatch,config_changes=change)
    with pytest.raises(ValueError):
        LocalHFBackend(tmp_path,**pins)
    assert placed==[]


@pytest.mark.parametrize('kind',['wrong_dtype','wrong_shape','wrong_values','missing_tensor'])
def test_legacy_position_buffer_contents_are_verified_before_acceptance(tmp_path,monkeypatch,kind):
    import numpy as np
    key='esm.embeddings.position_ids'
    def change(tensors):
        if kind=='wrong_dtype':tensors[key]=tensors[key].astype(np.int32)
        elif kind=='wrong_shape':tensors[key]=tensors[key].reshape(1026)
        elif kind=='wrong_values':tensors[key][0,-1]=0
        else:tensors={'unrelated.fixture':np.zeros((1,),dtype=np.int64)}
        return tensors
    pins,placed=_legacy_buffer_checkpoint(tmp_path,monkeypatch,tensor_change=change)
    with pytest.raises(ValueError):
        LocalHFBackend(tmp_path,**pins)
    assert placed==[]


@pytest.mark.parametrize('change',[
    {'unexpected_keys':{'esm.embeddings.position_ids','esm.encoder.layer.0.fake_weight'}},
    {'missing_keys':{'esm.encoder.layer.0.weight'}},
    {'mismatched_keys':{'esm.encoder.layer.0.weight'}},
    {'error_msgs':['synthetic loader failure']},
])
def test_legacy_buffer_exception_does_not_relax_learned_weight_guards(tmp_path,monkeypatch,change):
    pins,placed=_legacy_buffer_checkpoint(tmp_path,monkeypatch,loading_changes=change)
    with pytest.raises(ValueError):
        LocalHFBackend(tmp_path,**pins)
    assert placed==[]
