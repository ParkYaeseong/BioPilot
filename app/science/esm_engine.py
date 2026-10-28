"""Bounded local ESM masked marginals; no downloads or sequence uploads.

Injected backends must identify synthetic fixtures explicitly. Only local, verified
safetensors are accepted by LocalHFBackend. Scores have no temperature unit.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile

from app.science.models import get_model_spec


AA = 'ACDEFGHIKLMNPQRSTVWY'
CHECKPOINT = 'esm2_t30_150M_UR50D'
SCORE_KIND = 'masked_marginal_log_likelihood_ratio'
REFERENCE_ID = 'ESTA_BACSU_Nutschel_2020'
REFERENCE_SHA256 = '8a9ea05c5d2953b5b143b591bea6014aec631be96a4842b274fb3e91ee4907d7'


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('ESM logits and scores must be finite numbers')
    return float(value)


class ESMEngine:
    """One full-reference masked forward pass per requested, permitted position.

The backend must expose tokenize, token_id, mask_token_id, forward, provenance.
The backend source_mode is live or synthetic_fixture; persisted live results are
returned as replay. The cache contains no experimental outcomes.
"""

    def __init__(self, backend, cache_dir=None):
        self.backend = backend
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None
        self._cache = {}

    def score_positions(self, target, positions, checkpoint_key='esm150'):
        spec = get_model_spec(checkpoint_key)
        sequence = target.reference_sequence
        if (target.sequence_context != 'full_212'
                or target.reference_numbering != 'full_reference_1based'
                or target.reference_id != REFERENCE_ID
                or target.reference_sha256 != REFERENCE_SHA256
                or hashlib.sha256(sequence.encode('ascii')).hexdigest() != target.reference_sha256
                or len(sequence) != 212 or not set(sequence) <= set(AA)):
            raise ValueError('Only the registered full_212 reference scoring context is enabled')
        protected = tuple(target.protected_positions)
        if not {108, 164, 187} <= set(protected):
            raise ValueError('Registered protected residues cannot be removed')
        if (not isinstance(positions, list) or not positions or len(positions) > 10
                or any(type(p) is not int or not 32 <= p <= 212 or p in protected for p in positions)
                or len(set(positions)) != len(positions)):
            raise ValueError('Positions must be unique eligible full-reference sites; at most 200 candidates')
        provenance = dict(self.backend.provenance)
        if (provenance.get('checkpoint') != spec.checkpoint
                or provenance.get('model_key', checkpoint_key) != checkpoint_key
                or provenance.get('rank_policy', spec.rank_policy) != spec.rank_policy):
            raise ValueError('Backend checkpoint does not match the explicitly requested registered model')
        for key in ('weights_sha256', 'tokenizer_sha256'):
            if not isinstance(provenance.get(key), str) or re.fullmatch('[0-9a-f]{64}', provenance[key]) is None:
                raise ValueError('Backend requires exact weight and tokenizer hashes')
        if (provenance.get('source_mode') not in {'live', 'synthetic_fixture'}
                or not provenance.get('implementation') or not provenance.get('precision')):
            raise ValueError('Missing backend implementation, precision or source mode')
        token_ids = list(self.backend.tokenize(sequence))
        amino_ids = {aa: self.backend.token_id(aa) for aa in AA}
        if (len(token_ids) != len(sequence) + 2 or len(set(amino_ids.values())) != 20
                or token_ids[1:-1] != [amino_ids[aa] for aa in sequence]
                or self.backend.mask_token_id in amino_ids.values()):
            raise ValueError('Unverified token alignment: expected BOS, 212 residues, EOS')
        common = {
            **provenance, 'reference_id': target.reference_id,
            'reference_sha256': target.reference_sha256,
            'sequence_context': 'full_212', 'score_kind': SCORE_KIND,
            'model_key': checkpoint_key, 'rank_policy': spec.rank_policy,
        }
        rows = []
        cached_positions = []
        for position in sorted(positions):
            identity = {**common, 'full_position': position}
            key = _digest(identity)
            payload = self._read_cache(key, identity)
            cached = payload is not None
            if payload is None:
                masked = list(token_ids)
                masked[position] = self.backend.mask_token_id
                all_logits = self.backend.forward(masked)
                if len(all_logits) != len(masked):
                    raise ValueError('ESM logits do not match the token sequence')
                logits = all_logits[position]
                # log_softmax(a) - log_softmax(w) = logit(a) - logit(w).
                # This exact cancellation avoids a redundant softmax operation.
                values = {aa: _finite(logits[token]) for aa, token in amino_ids.items()}
                wild_type = sequence[position - 1]
                scores = {aa: _finite(value - values[wild_type]) for aa, value in values.items() if aa != wild_type}
                payload = {'identity': identity, 'scores': scores}
                self._write_cache(key, payload)
            wild_type = sequence[position - 1]
            scores = payload['scores']
            if set(scores) != set(AA) - {wild_type}:
                raise ValueError('Invalid score cache amino-acid distribution')
            row_mode = 'replay' if cached and common['source_mode'] == 'live' else common['source_mode']
            for mutant in sorted(scores):
                rows.append({
                    **common, 'candidate_id': f'{wild_type}{position}{mutant}',
                    'full_position': position, 'wild_type': wild_type, 'mutant': mutant,
                    'score': _finite(scores[mutant]), 'source_mode': row_mode,
                })
            if cached:
                cached_positions.append(position)
        source_mode = common['source_mode']
        if source_mode == 'live' and len(cached_positions) == len(positions):
            source_mode = 'replay'
        artifact = {
            'rows': rows, 'provenance': common, 'source_mode': source_mode,
            'cached_positions_1based': cached_positions,
            'phenotype_calibrated': False, 'score_units': 'dimensionless',
            'rank_policy': spec.rank_policy,
            'limitations': 'ESM sequence preference; T50, activity and retained function are unknown.',
        }
        artifact['artifact_sha256'] = _digest(artifact)
        return artifact

    def _read_cache(self, key, identity):
        document = self._cache.get(key)
        path = self.cache_dir / f'{key}.json' if self.cache_dir is not None else None
        if document is None and path is not None and path.exists():
            try:
                document = json.loads(path.read_text(encoding='utf-8'))
            except (ValueError, OSError) as error:
                raise ValueError('Invalid score cache document') from error
        if document is None:
            return None
        try:
            if document['payload_sha256'] != _digest(document['payload']) or document['payload']['identity'] != identity:
                raise ValueError('Invalid score cache identity or content hash')
        except (KeyError, TypeError) as error:
            raise ValueError('Invalid score cache envelope') from error
        self._cache[key] = deepcopy(document)
        return deepcopy(document['payload'])

    def _write_cache(self, key, payload):
        document = {'payload': payload, 'payload_sha256': _digest(payload)}
        self._cache[key] = deepcopy(document)
        if self.cache_dir is None:
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.cache_dir, delete=False) as file:
            json.dump(document, file, sort_keys=True, allow_nan=False)
            temporary = Path(file.name)
        try:
            os.replace(temporary, self.cache_dir / f'{key}.json')
        finally:
            temporary.unlink(missing_ok=True)


def _file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _verified_legacy_buffers(config, weight_paths, loading_info):
    """Recognize only the deterministic buffer made nonpersistent in Transformers.

    Installed EsmEmbeddings registers position_ids with persistent=False. The
    older official rotary checkpoint stored this arange; it is not a learned
    parameter. Every other loading discrepancy remains a hard failure.
    """
    failure='Local checkpoint is incomplete or incompatible; randomly initialized weights are not ESM baseline evidence'
    if any(loading_info.get(key) for key in ('missing_keys','mismatched_keys','error_msgs','conversion_errors')):
        raise ValueError(failure)
    unexpected=loading_info.get('unexpected_keys') or ()
    if not unexpected:
        return []
    buffer_name='esm.embeddings.position_ids'
    if (not isinstance(unexpected,(list,tuple,set,frozenset))
            or len(unexpected)!=1 or buffer_name not in unexpected
            or config.get('position_embedding_type')!='rotary'
            or type(config.get('max_position_embeddings')) is not int
            or config['max_position_embeddings']!=1026):
        raise ValueError(failure)
    from safetensors import SafetensorError, safe_open
    found=0
    try:
        for path in weight_paths:
            with safe_open(path,framework='numpy') as tensors:
                if buffer_name not in tensors.keys():
                    continue
                found+=1
                view=tensors.get_slice(buffer_name)
                if (view.get_dtype()!='I64' or view.get_shape()!=[1,1026]
                        or tensors.get_tensor(buffer_name).tolist()!=[list(range(1026))]):
                    raise ValueError(failure)
    except (SafetensorError,OSError,KeyError) as error:
        raise ValueError(failure) from error
    if found!=1:
        raise ValueError(failure)
    return [buffer_name]


class LocalHFBackend:
    """Explicitly installed local ESM-2 safetensors and explicit CPU/CUDA device.

Constructing this adapter performs no model download or remote-code execution.
It verifies architecture and local file hashes. Upstream weight authenticity must
be established by the trusted installer; local hashes alone prove file identity.
"""

    def __init__(self, checkpoint_dir, *, expected_weights_sha256=None, expected_tokenizer_sha256=None,
                 checkpoint_key='esm150', device='cpu'):
        spec = get_model_spec(checkpoint_key)
        if device not in ('cpu', 'cuda'):
            raise ValueError('Explicit local device must be cpu or cuda; automatic fallback is disabled')
        self.device = device
        directory = Path(checkpoint_dir).resolve()
        config_path = directory / 'config.json'
        weight_paths = sorted(directory.glob('*.safetensors'))
        if not config_path.is_file() or not weight_paths or not (directory / 'vocab.txt').is_file():
            raise ValueError('A complete local checkpoint with safetensors and vocab.txt is required; downloads are disabled')
        if (not isinstance(expected_weights_sha256, str) or re.fullmatch('[0-9a-f]{64}', expected_weights_sha256) is None
                or not isinstance(expected_tokenizer_sha256, str) or re.fullmatch('[0-9a-f]{64}', expected_tokenizer_sha256) is None):
            raise ValueError('Explicit trusted weight and tokenizer SHA256 pins are required before live checkpoint load')
        config = json.loads(config_path.read_text(encoding='utf-8'))
        if (config.get('model_type') != 'esm' or config.get('num_hidden_layers') != spec.num_hidden_layers
                or config.get('hidden_size') != spec.hidden_size or config.get('num_attention_heads') != spec.num_attention_heads):
            raise ValueError(f'Local checkpoint architecture is not {spec.checkpoint}')
        tokenizer_paths = [p for p in sorted(directory.iterdir()) if p.is_file() and p.name in {
            'vocab.txt', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'config.json',
        }]
        weight_hashes = {p.name: _file_hash(p) for p in weight_paths}
        tokenizer_hashes = {p.name: _file_hash(p) for p in tokenizer_paths}
        if _digest(weight_hashes) != expected_weights_sha256 or _digest(tokenizer_hashes) != expected_tokenizer_sha256:
            raise ValueError('Local checkpoint hash differs from the trusted installation pins')
        from importlib.metadata import version
        import torch
        if device == 'cuda' and not torch.cuda.is_available():
            raise ValueError('CUDA device requested but unavailable; CPU fallback is disabled')
        from transformers import AutoModelForMaskedLM, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(str(directory), local_files_only=True, trust_remote_code=False)
        model, loading_info = AutoModelForMaskedLM.from_pretrained(
            str(directory), local_files_only=True, trust_remote_code=False, use_safetensors=True,
            output_loading_info=True,
        )
        ignored_buffers=_verified_legacy_buffers(config,weight_paths,loading_info)
        self.model = model.to(device=device, dtype=torch.float32).eval()
        self.mask_token_id = self.tokenizer.mask_token_id
        if self.mask_token_id is None:
            raise ValueError('Local checkpoint tokenizer has no mask token')
        self.provenance = {
            'checkpoint': spec.checkpoint, 'model_key': checkpoint_key, 'rank_policy': spec.rank_policy,
            'weights_sha256': expected_weights_sha256,
            'tokenizer_sha256': expected_tokenizer_sha256,
            'config_sha256': _file_hash(config_path),
            'weight_file_hashes': weight_hashes,
            'implementation': f'transformers-{version("transformers")}/torch-{version("torch")}',
            'precision': 'float32', 'source_mode': 'live', 'device': device,
            'checkpoint_revision': directory.name if re.fullmatch('[0-9a-f]{40}', directory.name) else None,
            'upstream_authenticity': 'trusted_launcher_supplied_pins',
        }
        if ignored_buffers:
            self.provenance['ignored_nonpersistent_buffers']=ignored_buffers

    def token_id(self, residue):
        token = self.tokenizer.convert_tokens_to_ids(residue)
        if token is None or token == self.tokenizer.unk_token_id:
            raise ValueError('Canonical residue is absent from the checkpoint tokenizer')
        return token

    def tokenize(self, sequence):
        return self.tokenizer(sequence, add_special_tokens=True, truncation=False)['input_ids']

    def forward(self, token_ids):
        import torch
        inputs = torch.tensor([token_ids], dtype=torch.long, device=self.device)
        with torch.inference_mode():
            logits = self.model(input_ids=inputs, attention_mask=torch.ones_like(inputs)).logits
        return logits[0].float().cpu().tolist()
