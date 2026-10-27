"""Explicit ESM model identities shared by local and hosted adapters.

Architecture sources: each facebook/esm2_* repository's config.json on
Hugging Face, checked 2026-10-27. Registry membership grants no execution,
download, upload or spending permission.
"""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class ModelSpec:
    key: str
    checkpoint: str
    num_hidden_layers: int
    hidden_size: int
    num_attention_heads: int
    rank_policy: str


MODEL_REGISTRY = MappingProxyType({
    'esm35': ModelSpec('esm35', 'esm2_t12_35M_UR50D', 12, 480, 20, 'esm35_masked_v1'),
    'esm150': ModelSpec('esm150', 'esm2_t30_150M_UR50D', 30, 640, 20, 'esm150_masked_v1'),
    'esm650': ModelSpec('esm650', 'esm2_t33_650M_UR50D', 33, 1280, 20, 'esm650_masked_v1'),
})


def get_model_spec(key: str) -> ModelSpec:
    if not isinstance(key, str) or key not in MODEL_REGISTRY:
        raise ValueError('Unknown ESM model key; no checkpoint fallback is permitted')
    return MODEL_REGISTRY[key]


class ScoringBackend(Protocol):
    """Trusted local/worker adapter interface; provider-specific clients stay outside core."""
    mask_token_id: int
    provenance: Mapping[str, Any]

    def token_id(self, residue: str) -> int: ...
    def tokenize(self, sequence: str) -> list[int]: ...
    def forward(self, token_ids: list[int]) -> list[list[float]]: ...


class PositionScorer(Protocol):
    """Same scoring request/result shape for local, Modal and RunPod execution."""

    def score_positions(self, target: Any, positions: list[int], checkpoint_key: str = 'esm150') -> dict[str, Any]: ...
