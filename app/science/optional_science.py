"""Optional structure workers: registered public inputs, pinned local models, no ranking.

This module is safe to import for readiness display. Only OfficialLocalRuntime imports
the optional GPU SDK. Download and remote dispatch are deliberately absent.
Official SDK contract inspected at Biohub/esm tag v3.4.1.post1, 2026-10-28.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys
import time

from app.core.targets import FRAME, REFERENCE_SHA256, registered_profile, validate_target, validate_variant

ESM_SDK_VERSION = '3.4.1.post1'
MODELS = {'esm3': 'biohub/esm3-sm-open-v1', 'esmfold2': 'biohub/ESMFold2'}
SOURCES = {
    'esm3': 'https://github.com/Biohub/esm/blob/v3.4.1.post1/_assets/ESM3_README.md',
    'esmfold2': 'https://github.com/Biohub/esm/tree/v3.4.1.post1/esm/models/esmfold2',
    'atlas': 'https://docs.biohub.ai/api/protein/atlas/proteins/get',
}


def optional_capabilities():
    """Implementation availability is distinct from installed/runtime verification."""
    atlas = {'model_id': None, 'adapter_implemented': True, 'runtime_verified': False,
             'status': 'snapshot_unavailable', 'annotation_only': True,
             'live_runtime_enabled': False, 'source_url': SOURCES['atlas']}
    try:
        from app.core.atlas_snapshot import load_registered_atlas_snapshot
        load_registered_atlas_snapshot()
        atlas.update(status='pinned_snapshot_available', runtime_verified=True,
                     verification_scope='offline_registered_wt_snapshot',
                     upstream_authenticity_verified=False)
    except (ValueError, OSError, TypeError, KeyError):
        pass
    return {key: {'model_id': model, 'adapter_implemented': True,
                  'runtime_verified': False, 'status': 'requires_pinned_worker',
                  'annotation_only': True, 'source_url': SOURCES[key]}
            for key, model in MODELS.items()} | {'atlas': atlas}


def _digest(data):
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class StructureRequest:
    model_key: str
    variant: str = 'WT'

    def __post_init__(self):
        if not isinstance(self.model_key, str) or self.model_key not in MODELS:
            raise ValueError('Only registered optional structure models are supported')
        target = validate_target(registered_profile(), 'sequence_plausibility_review')
        if self.variant != 'WT':
            validate_variant(target, self.variant, reference_numbering=FRAME)

    @property
    def sequence(self):
        target = validate_target(registered_profile(), 'sequence_plausibility_review')
        sequence = target.reference_sequence
        if self.variant == 'WT':
            return sequence
        checked = validate_variant(target, self.variant)
        return sequence[:checked.full_position-1] + checked.mutant + sequence[checked.full_position:]

    def to_payload(self):
        return {'schema_version': 1, 'model_key': self.model_key, 'variant': self.variant,
                'reference_sha256': REFERENCE_SHA256, 'reference_numbering': FRAME,
                'sequence_context': 'full_212'}

    @classmethod
    def from_payload(cls, value):
        if (not isinstance(value, dict) or set(value) != {
                'schema_version', 'model_key', 'variant', 'reference_sha256',
                'reference_numbering', 'sequence_context'}
                or type(value['schema_version']) is not int or value['schema_version'] != 1
                or value['reference_sha256'] != REFERENCE_SHA256
                or value['reference_numbering'] != FRAME or value['sequence_context'] != 'full_212'):
            raise ValueError('Invalid optional request; free sequences and extra fields are forbidden')
        return cls(value['model_key'], value['variant'])


def checkpoint_manifest(directory, manifest_path, expected_sha256, model_key):
    """Trusted operator pins; never accept a caller-selected URL or floating revision."""
    root = Path(directory).resolve()
    raw = Path(manifest_path).read_bytes()
    if not isinstance(expected_sha256, str) or _digest(raw) != expected_sha256:
        raise ValueError('Checkpoint manifest hash mismatch')
    pins = json.loads(raw)
    if (not isinstance(pins, dict) or set(pins) != {'schema_version', 'model_key', 'repository', 'revision', 'esm_version', 'files'}
            or pins['schema_version'] != 1 or pins['model_key'] != model_key
            or pins['repository'] != MODELS.get(model_key)
            or pins['esm_version'] != ESM_SDK_VERSION
            or re.fullmatch('[0-9a-f]{40}', pins['revision']) is None
            or not isinstance(pins['files'], dict) or not pins['files']):
        raise ValueError('Invalid checkpoint manifest identity or SDK pin')
    for name, digest in pins['files'].items():
        rel = PurePosixPath(name)
        if (rel.is_absolute() or '..' in rel.parts or '\\' in name or ':' in name
                or re.fullmatch('[0-9a-f]{64}', digest) is None):
            raise ValueError('Invalid checkpoint manifest file path/hash')
        if _digest((root / name).read_bytes()) != digest:
            raise ValueError('Checkpoint file hash mismatch: ' + name)
    # All files, including auxiliary decoders/configs, are pinned. A model loader may
    # otherwise discover an unlisted shard or execute a changing remote helper.
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != set(pins['files']):
        raise ValueError('Checkpoint manifest inventory mismatch')
    if model_key == 'esmfold2':
        config = json.loads((root / 'config.json').read_text(encoding='utf-8'))
        if config.get('esmc_config') is None or config.get('type') == 'experimental':
            raise ValueError('Only the standard bundled-backbone ESMFold2 checkpoint is enabled')
    return pins


def _verify_prediction_sequence(pdb, sequence):
    """Check output CA identities and full-reference numbering, without geometry claims."""
    amino = dict(zip('ALA CYS ASP GLU PHE GLY HIS ILE LYS LEU MET ASN PRO GLN ARG SER THR VAL TRP TYR'.split(),
                     'ACDEFGHIKLMNPQRSTVWY'))
    residues = {}
    try:
        for line in pdb.splitlines():
            if not line.startswith('ATOM  ') or line[12:16].strip() != 'CA':
                continue
            position = int(line[22:26])
            if (line[21] != 'A' or line[26:27].strip() or line[16:17].strip()
                    or position in residues or line[17:20] not in amino
                    or not all(math.isfinite(float(line[start:start+8])) for start in (30, 38, 46))):
                raise ValueError('Prediction sequence identity/numbering mismatch')
            residues[position] = amino[line[17:20]]
    except (IndexError, ValueError) as error:
        raise ValueError('Prediction sequence identity/numbering mismatch') from error
    if residues != dict(enumerate(sequence, 1)):
        raise ValueError('Prediction sequence is incomplete or differs from the exact full_212 input')


class OfficialLocalRuntime:
    """Exact official SDK call paths; network-disabled fresh worker process only."""
    def predict(self, request, root, pins):
        if importlib.metadata.version('esm') != ESM_SDK_VERSION:
            raise ValueError('Installed esm SDK differs from the verified version')
        if 'huggingface_hub.constants' in sys.modules:
            raise ValueError('Use a fresh worker process so offline cache settings apply before SDK import')
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['HF_DATASETS_OFFLINE'] = '1'
        if request.model_key == 'esm3':
            # SDK ESM3 loader has no local-path argument. Its dedicated offline HF
            # cache must resolve main to this exact verified snapshot revision.
            if (root.name != pins['revision'] or root.parent.name != 'snapshots'
                    or root.parent.parent.name != 'models--biohub--esm3-sm-open-v1'):
                raise ValueError('ESM3 needs its isolated pinned Hugging Face snapshot directory')
            ref = root.parent.parent / 'refs' / 'main'
            if ref.read_text().strip() != pins['revision']:
                raise ValueError('ESM3 offline main ref differs from the pinned revision')
            os.environ['HF_HUB_CACHE'] = str(root.parent.parent.parent)
        import torch
        if not torch.cuda.is_available():
            raise ValueError('Optional structure execution requires a verified CUDA worker')
        # Bound this worker's PyTorch allocator on the one selected visible GPU.
        # CUDA context/non-PyTorch allocations are outside this allocator bound.
        torch.cuda.set_per_process_memory_fraction(0.80, 0)
        torch.cuda.reset_peak_memory_stats(0)
        self.provenance = {'esm': importlib.metadata.version('esm'),
                           'torch': importlib.metadata.version('torch'),
                           'transformers': importlib.metadata.version('transformers'),
                           'cuda_runtime': str(getattr(getattr(torch, 'version', None), 'cuda', None)),
                           'gpu_name': torch.cuda.get_device_name(0),
                           'pytorch_memory_fraction': 0.80}
        torch.manual_seed(0)
        torch.cuda.manual_seed_all(0)
        with torch.inference_mode():
            if request.model_key == 'esm3':
                from esm.models.esm3 import ESM3
                from esm.sdk.api import ESMProtein, GenerationConfig
                model = ESM3.from_pretrained('esm3-sm-open-v1').to('cuda').eval()
                result = model.generate(ESMProtein(sequence=request.sequence),
                                        GenerationConfig(track='structure', num_steps=8))
                if not isinstance(result, ESMProtein) or result.sequence != request.sequence:
                    raise ValueError('ESM3 structure generation did not preserve the exact candidate')
                pdb = result.to_pdb_string()
                self.provenance['peak_pytorch_allocated_bytes'] = torch.cuda.max_memory_allocated(0)
                return pdb
            from esm.models.esmfold2 import EsmFold2Model
            model = EsmFold2Model.from_pretrained(str(root), device='cuda',
                local_files_only=True, esmc_precision='bf16').eval()
            model.set_chunk_size(64)
            pdb = model.infer_protein_as_pdb(request.sequence, num_loops=3,
                                            num_sampling_steps=32, num_diffusion_samples=1)
            self.provenance['peak_pytorch_allocated_bytes'] = torch.cuda.max_memory_allocated(0)
            return pdb


def run_structure(request, checkpoint_dir, manifest_path, manifest_sha256, output_dir,
                  *, execution_approved=False, runtime=None):
    """Run one annotation. CLI supervises this process with a hard wall timeout."""
    if execution_approved is not True:
        raise ValueError('Explicit structure execution approval is required')
    if not isinstance(request, StructureRequest):
        raise ValueError('Expected a validated structure request')
    # Revalidate even a manually constructed dataclass, before pins/imports or writes.
    request = StructureRequest.from_payload(request.to_payload())
    output = Path(output_dir)
    if output.exists():
        raise FileExistsError('Prediction output already exists; prior artifacts are preserved')
    root = Path(checkpoint_dir).resolve()
    pins = checkpoint_manifest(root, manifest_path, manifest_sha256, request.model_key)
    output.mkdir(parents=False)
    started = time.monotonic()
    try:
        selected_runtime = runtime or OfficialLocalRuntime()
        pdb = selected_runtime.predict(request, root, pins)
        if (not isinstance(pdb, str) or not pdb.startswith(('ATOM', 'HEADER', 'REMARK', 'MODEL'))
                or '\nATOM ' not in '\n' + pdb or len(pdb.encode()) > 5 * 1024 * 1024):
            raise ValueError('Model returned an invalid or oversized PDB structure')
        _verify_prediction_sequence(pdb, request.sequence)
        data = pdb.encode('utf-8')
        with (output / 'prediction.pdb').open('xb') as stream:
            stream.write(data)
        receipt = {'schema_version': 1, 'status': 'completed',
            'source_mode': 'computed_prediction', 'request': request.to_payload(),
            'candidate_sequence_sha256': _digest(request.sequence.encode('ascii')),
            'checkpoint_manifest_sha256': manifest_sha256,
            'model_repository': pins['repository'], 'checkpoint_revision': pins['revision'],
            'esm_version': ESM_SDK_VERSION, 'device': 'cuda', 'seed': 0,
            'runtime_provenance': getattr(selected_runtime, 'provenance', None),
            'runtime_verification': 'official_sdk_execution' if runtime is None else 'injected_test_runtime',
            'structure_sha256': _digest(data), 'structure_path': 'prediction.pdb',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'elapsed_seconds': round(time.monotonic()-started, 3),
            'annotation_only': True, 'baseline_rank_changed': False,
            'experimental_validation': False, 'atom_geometry_validated': False,
            'predicted_sequence_verified': True,
            'sampling': {'track': 'structure', 'num_steps': 8} if request.model_key == 'esm3'
                else {'num_loops': 3, 'num_sampling_steps': 32, 'num_diffusion_samples': 1,
                      'chunk_size': 64, 'esmc_precision': 'bf16'},
            'numbering_note': 'Prediction residue 1 corresponds to full-reference position 1; '
                              'this is the full_212 prediction, not the mature 1ISP construct.',
            'confidence_metrics': None, 'phenotype_claim': None}
        (output / 'receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False), encoding='utf-8')
        return receipt
    except Exception:
        (output / 'failure.json').write_text(json.dumps({'status': 'failed',
            'request': request.to_payload(), 'scientific_evidence': False,
            'elapsed_seconds': round(time.monotonic()-started, 3)}), encoding='utf-8')
        raise
