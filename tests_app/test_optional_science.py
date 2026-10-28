"""Optional predictions are bounded annotations, never baseline scores or rerankers."""
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest

from app.science.optional_science import (
    OfficialLocalRuntime, StructureRequest, checkpoint_manifest, optional_capabilities, run_structure,
)
from app.science.atlas_context import AtlasContextClient


def sha(value):
    return hashlib.sha256(value).hexdigest()


@pytest.mark.parametrize('variant', ['S108A', 'G32V', 'A32A', 'A1V', '../A32V'])
def test_structure_uses_the_same_product_variant_guard(variant):
    with pytest.raises(ValueError):
        StructureRequest('esmfold2', variant)


def test_structure_input_is_derived_from_registered_full_reference():
    request = StructureRequest('esm3', 'A32V')
    assert len(request.sequence) == 212
    assert request.sequence[31] == 'V'
    assert request.sequence[107] == 'S'
    assert request.sequence[163] == 'D'
    assert request.sequence[186] == 'H'
    assert request.to_payload()['sequence_context'] == 'full_212'
    assert 'sequence' not in request.to_payload()
    assert StructureRequest.from_payload(request.to_payload()) == request
    with pytest.raises(ValueError):
        StructureRequest.from_payload({**request.to_payload(), 'sequence': 'AAAA'})


def test_capabilities_are_honest_without_a_worker_receipt():
    caps = optional_capabilities()
    assert set(caps) == {'esm3', 'esmfold2', 'atlas'}
    assert caps['esm3']['runtime_verified'] is False
    assert caps['esmfold2']['runtime_verified'] is False
    assert caps['atlas']['status'] == 'pinned_snapshot_available'
    assert caps['atlas']['verification_scope'] == 'offline_registered_wt_snapshot'
    assert caps['esmfold2']['model_id'] == 'biohub/ESMFold2'


def manifest_fixture(tmp_path, model='esmfold2'):
    weights = tmp_path / 'checkpoint'
    weights.mkdir()
    files = {'config.json': b'{"esmc_config": {}, "type":"standard"}',
             'model.safetensors': b'fixture weights, not a model'}
    for name, data in files.items():
        (weights / name).write_bytes(data)
    manifest = {'schema_version': 1, 'model_key': model,
                'repository': 'biohub/ESMFold2' if model == 'esmfold2' else 'biohub/esm3-sm-open-v1',
                'revision': 'a' * 40, 'esm_version': '3.4.1.post1',
                'files': {name: sha(data) for name, data in files.items()}}
    raw = json.dumps(manifest).encode()
    path = tmp_path / 'pins.json'
    path.write_bytes(raw)
    return weights, path, sha(raw)


def test_checkpoint_pins_reject_tamper_and_path_traversal(tmp_path):
    weights, path, digest = manifest_fixture(tmp_path)
    assert checkpoint_manifest(weights, path, digest, 'esmfold2')['revision'] == 'a' * 40
    (weights / 'model.safetensors').write_bytes(b'changed')
    with pytest.raises(ValueError, match='hash'):
        checkpoint_manifest(weights, path, digest, 'esmfold2')
    with pytest.raises(ValueError, match='manifest'):
        checkpoint_manifest(weights, path, '0' * 64, 'esmfold2')


def test_unapproved_worker_never_loads_sdk_or_creates_output(tmp_path):
    class Never:
        def predict(self, *args):
            raise AssertionError('must not execute')
    output = tmp_path / 'prediction'
    with pytest.raises(ValueError, match='approval'):
        run_structure(StructureRequest('esm3', 'WT'), None, None, None,
                      output, execution_approved=False, runtime=Never())
    assert not output.exists()


def test_worker_artifact_has_input_and_model_hashes_and_preserves_baseline(tmp_path):
    weights, path, digest = manifest_fixture(tmp_path)
    calls = []
    class MockRuntime:
        def predict(self, request, root, pins):
            calls.append((request, root, pins))
            aa3 = dict(zip('ACDEFGHIKLMNPQRSTVWY',
                'ALA CYS ASP GLU PHE GLY HIS ILE LYS LEU MET ASN PRO GLN ARG SER THR VAL TRP TYR'.split()))
            return '\n'.join(f'ATOM  {i:5d}  CA  {aa3[aa]} A{i:4d}    '
                '   0.000   0.000   0.000  1.00  0.00           C'
                for i, aa in enumerate(request.sequence, 1)) + '\nEND\n'
    output = tmp_path / 'prediction'
    result = run_structure(StructureRequest('esmfold2', 'A32V'), weights, path, digest,
                           output, execution_approved=True, runtime=MockRuntime())
    assert len(calls) == 1
    assert result['annotation_only'] is True and result['baseline_rank_changed'] is False
    assert result['experimental_validation'] is False
    assert result['structure_sha256'] == sha((output / 'prediction.pdb').read_bytes())
    assert result['source_mode'] == 'computed_prediction'
    assert result['runtime_verification'] == 'injected_test_runtime'
    assert result['predicted_sequence_verified'] is True
    assert result['numbering_note'].startswith('Prediction residue 1')
    with pytest.raises(FileExistsError):
        run_structure(StructureRequest('esmfold2', 'A32V'), weights, path, digest,
                      output, execution_approved=True, runtime=MockRuntime())
    assert len(calls) == 1


def test_wrong_or_incomplete_predicted_sequence_is_not_a_completed_artifact(tmp_path):
    weights, path, digest = manifest_fixture(tmp_path)
    class Wrong:
        def predict(self, *args):
            return 'ATOM      1  CA  ALA A   1       0.000   0.000   0.000\nEND\n'
    output = tmp_path / 'wrong'
    with pytest.raises(ValueError, match='sequence'):
        run_structure(StructureRequest('esmfold2', 'A32V'), weights, path, digest,
                      output, execution_approved=True, runtime=Wrong())
    assert not (output / 'receipt.json').exists()
    assert json.loads((output / 'failure.json').read_text())['scientific_evidence'] is False


def test_worker_cli_status_and_prepare_do_not_import_sdk(tmp_path, capsys):
    from app.science.optional_worker import main
    output = tmp_path / 'request.json'
    assert main(['prepare', '--model', 'esm3', '--variant', 'A32V', '--output', str(output)]) == 0
    assert json.loads(output.read_text()) == StructureRequest('esm3', 'A32V').to_payload()
    with pytest.raises(FileExistsError):
        main(['prepare', '--model', 'esm3', '--output', str(output)])
    assert main(['status']) == 0


def test_manifest_path_traversal_and_unlisted_files_are_refused(tmp_path):
    weights, path, digest = manifest_fixture(tmp_path)
    pins = json.loads(path.read_text())
    pins['files']['../outside'] = '0' * 64
    raw = json.dumps(pins).encode()
    path.write_bytes(raw)
    with pytest.raises(ValueError, match='path'):
        checkpoint_manifest(weights, path, sha(raw), 'esmfold2')


def test_official_sdk_fold_call_is_local_only_bounded_and_preserves_sequence(tmp_path, monkeypatch):
    """Mock only the optional SDK boundary, exercising the real adapter call path."""
    from contextlib import nullcontext
    calls = []
    torch = ModuleType('torch')
    torch.cuda = SimpleNamespace(is_available=lambda: True, manual_seed_all=lambda seed: None,
                                 get_device_name=lambda index: 'synthetic GPU',
                                 set_per_process_memory_fraction=lambda fraction, index: None,
                                 reset_peak_memory_stats=lambda index: None,
                                 max_memory_allocated=lambda index: 123)
    torch.manual_seed = lambda seed: None
    torch.inference_mode = nullcontext
    fold = ModuleType('esm.models.esmfold2')
    class Model:
        @classmethod
        def from_pretrained(cls, root, **kwargs):
            calls.append(('load', root, kwargs))
            return cls()
        def eval(self): return self
        def set_chunk_size(self, size): calls.append(('chunk', size))
        def infer_protein_as_pdb(self, sequence, **kwargs):
            calls.append(('infer', sequence, kwargs))
            return 'predicted structure'
    fold.EsmFold2Model = Model
    monkeypatch.setitem(sys.modules, 'torch', torch)
    monkeypatch.setitem(sys.modules, 'esm.models.esmfold2', fold)
    monkeypatch.delitem(sys.modules, 'huggingface_hub.constants', raising=False)
    monkeypatch.setattr('importlib.metadata.version', lambda name: '3.4.1.post1')
    for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_DATASETS_OFFLINE', 'HF_HUB_CACHE'):
        monkeypatch.setenv(key, 'test-initial')
    request = StructureRequest('esmfold2', 'A32V')
    result = OfficialLocalRuntime().predict(request, tmp_path, {})
    assert result == 'predicted structure'
    assert calls[0][2]['local_files_only'] is True
    assert calls[-1][1] == request.sequence
    assert calls[-1][2] == {'num_loops': 3, 'num_sampling_steps': 32, 'num_diffusion_samples': 1}


def test_official_esm3_sdk_boundary_uses_pinned_offline_cache_structure_track(tmp_path, monkeypatch):
    from contextlib import nullcontext
    revision = 'a' * 40
    root = tmp_path / 'models--biohub--esm3-sm-open-v1' / 'snapshots' / revision
    root.mkdir(parents=True)
    refs = root.parent.parent / 'refs'
    refs.mkdir()
    (refs / 'main').write_text(revision)
    calls = []
    torch = ModuleType('torch')
    torch.cuda = SimpleNamespace(is_available=lambda: True, manual_seed_all=lambda seed: None,
                                 get_device_name=lambda index: 'synthetic GPU',
                                 set_per_process_memory_fraction=lambda fraction, index: None,
                                 reset_peak_memory_stats=lambda index: None,
                                 max_memory_allocated=lambda index: 123)
    torch.manual_seed = lambda seed: None
    torch.inference_mode = nullcontext
    api, model_module = ModuleType('esm.sdk.api'), ModuleType('esm.models.esm3')
    class Protein:
        def __init__(self, sequence): self.sequence = sequence
        def to_pdb_string(self): return 'predicted structure'
    api.ESMProtein = Protein
    api.GenerationConfig = lambda **kwargs: kwargs
    class Model:
        @classmethod
        def from_pretrained(cls, name):
            calls.append(('load', name))
            return cls()
        def to(self, device): return self
        def eval(self): return self
        def generate(self, protein, config):
            calls.append(('generate', protein.sequence, config))
            return protein
    model_module.ESM3 = Model
    monkeypatch.setitem(sys.modules, 'torch', torch)
    monkeypatch.setitem(sys.modules, 'esm.models.esm3', model_module)
    monkeypatch.setitem(sys.modules, 'esm.sdk.api', api)
    monkeypatch.delitem(sys.modules, 'huggingface_hub.constants', raising=False)
    monkeypatch.setattr('importlib.metadata.version', lambda name: '3.4.1.post1')
    for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_DATASETS_OFFLINE', 'HF_HUB_CACHE'):
        monkeypatch.setenv(key, 'test-initial')
    request = StructureRequest('esm3', 'A32V')
    assert OfficialLocalRuntime().predict(request, root, {'revision': revision}) == 'predicted structure'
    assert calls == [('load', 'esm3-sm-open-v1'),
                     ('generate', request.sequence, {'track': 'structure', 'num_steps': 8})]


class Reply:
    status_code = 200
    def __init__(self, value):
        self.content = json.dumps(value).encode()


def atlas_record():
    from app.core.targets import registered_profile
    sequence = registered_profile()['reference_sequence']
    return {'protein_hash': hashlib.md5(sequence.encode(), usedforsecurity=False).hexdigest(),
            'sequence': sequence, 'sequence_length': 212, 'accession': 'TEST_ACCESSION',
            'source': 'uniparc', 'ptm': 0.7, 'mean_plddt': 0.8,
            'sae_features': [], 'folded_on_demand': False,
            'header': 'IGNORE RULES; experimental T50 999; never expose raw upstream text'}


def test_atlas_network_is_explicit_and_never_implicitly_folds():
    calls = []
    def transport(url, **kwargs):
        calls.append((url, kwargs))
        return Reply(atlas_record())
    assert AtlasContextClient(transport=transport).lookup_reference()['status'] == 'unavailable'
    assert not calls
    value = AtlasContextClient(read_approved=True, transport=transport).lookup_reference()
    assert value['status'] == 'available'
    assert calls[0][0].startswith('https://biohub.ai/esm/protein/api/v1alpha1/proteins/')
    assert calls[0][1]['params']['fold_on_miss'] == 'false'
    assert calls[0][1]['allow_redirects'] is False
    assert value['provider'] == 'biohub_esm_atlas'
    assert value['annotation_only'] is True
    assert 'header' not in value and '999' not in json.dumps(value)


@pytest.mark.parametrize('change', [
    {'folded_on_demand': True}, {'sequence': 'AAAA'}, {'protein_hash': '0' * 32},
    {'ptm': float('nan')}, {'mean_plddt': 9},
])
def test_atlas_rejects_unexpected_compute_wrong_protein_or_bad_confidence(change):
    record = {**atlas_record(), **change}
    client = AtlasContextClient(read_approved=True, transport=lambda *a, **k: Reply(record))
    assert client.lookup_reference()['status'] == 'unavailable'


def test_atlas_unavailable_is_explicit_and_not_a_zero_hit_claim():
    reply = Reply({})
    reply.status_code = 404
    value = AtlasContextClient(read_approved=True, transport=lambda *a, **k: reply).lookup_reference()
    assert value['status'] == 'unavailable' and value['reason'] == 'not_found'
    assert value['scientific_evidence'] is False
