"""Local-only inference implementation and an opt-in Modal deployment definition.

Importing this module does not import the Modal SDK, authenticate, allocate a GPU,
download weights, build an image or deploy. ``execute_request`` is the same bounded
callable used in worker fixture tests. The deployment factory is deliberately
blocked until separate deployment and existing-volume approvals are supplied.

SDK API references and installed 1.6.2 signatures/docstrings were inspected on
2026-10-27. Actual SDK factory construction, authentication, deployed limits and
inference remain unverified and require separate operational approval.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import importlib
from importlib import metadata
import inspect
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping

from app.core.targets import registered_profile, validate_target
from app.science.esm_engine import ESMEngine, LocalHFBackend
from app.science.models import get_model_spec
from app.science.providers import InferenceRequest, canonical_digest


WORKER_SOURCE_ALLOWLIST = (
    "app/__init__.py",
    "app/core/__init__.py",
    "app/core/capabilities.py",
    "app/core/targets.py",
    "app/science/__init__.py",
    "app/science/models.py",
    "app/science/esm_engine.py",
    "app/science/providers.py",
    "app/science/modal_worker.py",
    "reference/target_profile.json",
)
WORKER_ROOT = "/opt/biopilot"
MODEL_MOUNT = "/models"
IMAGE_PACKAGES = ("torch==2.9.1", "transformers==5.2.0", "safetensors==0.7.0")
MANIFEST_FIELDS = frozenset({"checkpoint_dir", "expected_weights_sha256", "expected_tokenizer_sha256"})
WORKER_EXECUTION_CEILING_SECONDS = 900
WORKER_STARTUP_TIMEOUT_SECONDS = 120
WORKER_SCALEDOWN_SECONDS = 2
WORKER_CPU_BOUNDS = (1.0, 1.0)
WORKER_MEMORY_MIB_BOUNDS = (4096, 4096)


def remote_reservation_components():
    """Offline definition bounds; no claim that a deployed worker was inspected."""
    return {"execution_seconds": WORKER_EXECUTION_CEILING_SECONDS,
            "startup_seconds": WORKER_STARTUP_TIMEOUT_SECONDS,
            "idle_seconds": WORKER_SCALEDOWN_SECONDS}


def _models_manifest(models_manifest):
    if not isinstance(models_manifest, Mapping) or not models_manifest:
        raise ValueError("A trusted, nonempty preprovisioned model manifest is required")
    checked = {}
    for key, entry in models_manifest.items():
        get_model_spec(key)
        if not isinstance(entry, Mapping) or set(entry) != MANIFEST_FIELDS:
            raise ValueError("Worker manifest must contain only pinned checkpoint locations")
        directory = entry["checkpoint_dir"]
        if (not isinstance(directory, str) or not directory
                or not (Path(directory).is_absolute() or PurePosixPath(directory).is_absolute())
                or any(part in {"..", ".env"} for part in directory.replace("\\", "/").split("/"))):
            raise ValueError("Worker checkpoint path must be an absolute trusted local location")
        for name in ("expected_weights_sha256", "expected_tokenizer_sha256"):
            if not isinstance(entry[name], str) or re.fullmatch("[0-9a-f]{64}", entry[name]) is None:
                raise ValueError("Worker checkpoint and tokenizer need trusted SHA256 pins")
        checked[key] = dict(entry)
    return checked


def execute_request(payload, models_manifest, *, backend_factory=None):
    """Run one strict, pin-matched request without downloads, retries or fallback.

    The request contains only a public reference identity and bounded positions.
    The full reference sequence and local model path are selected inside the
    worker from its provisioned registry and trusted manifest. ``backend_factory``
    is a dependency-injection seam for offline fixtures, never a request field.
    """
    request = InferenceRequest.from_payload(payload)
    provisioned = _models_manifest(models_manifest)
    if request.model_key not in provisioned:
        raise ValueError("Requested worker model is not provisioned; fallback is disabled")
    model = provisioned[request.model_key]
    if (request.expected_weights_sha256 != model["expected_weights_sha256"]
            or request.expected_tokenizer_sha256 != model["expected_tokenizer_sha256"]):
        raise ValueError("Request checkpoint pins differ from the trusted worker manifest")
    target = validate_target(registered_profile(), "sequence_plausibility_review",
                             reference_numbering=request.reference_numbering)
    if target.reference_id != request.reference_id or target.reference_sha256 != request.reference_sha256:
        raise ValueError("Worker registry differs from the requested public reference")
    factory = LocalHFBackend if backend_factory is None else backend_factory
    backend = factory(model["checkpoint_dir"], checkpoint_key=request.model_key, device="cuda",
                      expected_weights_sha256=model["expected_weights_sha256"],
                      expected_tokenizer_sha256=model["expected_tokenizer_sha256"])
    provenance = backend.provenance
    if (provenance.get("checkpoint") != get_model_spec(request.model_key).checkpoint
            or provenance.get("weights_sha256") != request.expected_weights_sha256
            or provenance.get("tokenizer_sha256") != request.expected_tokenizer_sha256):
        raise ValueError("Worker backend did not load the exact requested checkpoint pins")
    # No persistent score cache is written into the read-only model volume.
    return ESMEngine(backend).score_positions(target, list(request.positions), request.model_key)


def worker_source_files(project_root):
    """Return content hashes for fixed reviewed code/public-data files only."""
    root = Path(project_root).resolve(strict=True)
    sources = {}
    for relative in WORKER_SOURCE_ALLOWLIST:
        path = root / relative
        resolved = path.resolve(strict=True)
        if resolved != path or path.is_symlink() or not resolved.is_file():
            raise ValueError("Worker source must be a regular allowlisted file without symlink redirection")
        if resolved.stat().st_size > 256 * 1024:
            raise ValueError("Worker source exceeds the reviewed 256 KiB per-file limit")
        sources[relative] = hashlib.sha256(resolved.read_bytes()).hexdigest()
    return sources


def _verify_worker_sources(expected, project_root):
    if worker_source_files(project_root) != expected:
        raise ValueError("Provisioned worker source hashes differ from the reviewed deployment definition")


def _supports_keywords(function, names):
    parameters = inspect.signature(function).parameters
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in parameters.values()):
        return
    if not set(names) <= set(parameters):
        raise RuntimeError("Installed Modal SDK lacks required definition parameters; compatibility remains unverified")


@dataclass(frozen=True)
class ModalWorkerDefinition:
    app: Any
    function: Any
    sdk_version: str
    source_manifest_sha256: str
    compatibility_status: str = "definition_only_not_deployed"
    execution_timeout_seconds: int = WORKER_EXECUTION_CEILING_SECONDS

    @property
    def resource_bounds(self):
        return {"cpu_request": WORKER_CPU_BOUNDS[0], "cpu_limit": WORKER_CPU_BOUNDS[1],
                "memory_request_mib": WORKER_MEMORY_MIB_BOUNDS[0],
                "memory_limit_mib": WORKER_MEMORY_MIB_BOUNDS[1],
                "execution_timeout_seconds": self.execution_timeout_seconds,
                "startup_timeout_seconds": WORKER_STARTUP_TIMEOUT_SECONDS,
                "scaledown_window_seconds": WORKER_SCALEDOWN_SECONDS,
                "reservation_components": remote_reservation_components(),
                "deployment_verified": False}


def create_modal_app(models_manifest, *, project_root, expected_sdk_version,
                     deployment_approved=False, existing_volume_name=None,
                     volume_approved=False, gpu="T4", timeout_seconds=900):
    """Construct, never run/deploy, a single-container zero-retry worker definition.

    ``deployment_approved`` and ``volume_approved`` are trusted administrator
    controls. They must not be populated from an LLM or inference payload. This
    factory supplies neither credentials nor a public web endpoint. Weights must
    already exist in the explicitly approved named volume at manifest paths.
    """
    if deployment_approved is not True:
        raise PermissionError("Explicit Modal deployment approval is required before loading the SDK")
    if volume_approved is not True:
        raise PermissionError("Explicit approval to mount the existing model volume is required")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 900:
        raise ValueError("Worker timeout must be an explicit integer from 1 to 900 seconds")
    if gpu not in {"T4", "L4"}:
        raise ValueError("Choose one explicit supported worker GPU; fallback lists are disabled")
    if not isinstance(existing_volume_name, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,62}", existing_volume_name) is None:
        raise ValueError("An existing explicitly approved model volume name is required")
    frozen_manifest = _models_manifest(models_manifest)
    for entry in frozen_manifest.values():
        path = PurePosixPath(entry["checkpoint_dir"])
        if not path.is_absolute() or PurePosixPath(MODEL_MOUNT) not in path.parents:
            raise ValueError("Deployed worker models must already exist under the read-only /models volume")
    if not isinstance(expected_sdk_version, str) or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", expected_sdk_version) is None:
        raise ValueError("Pin the exact installed stable Modal SDK version before constructing a definition")
    try:
        actual_sdk_version = metadata.version("modal")
    except metadata.PackageNotFoundError as error:
        raise RuntimeError("Modal SDK is not installed; deployment compatibility is unverified") from error
    if actual_sdk_version != expected_sdk_version:
        raise RuntimeError("Installed Modal SDK differs from the explicit version pin")
    modal = importlib.import_module("modal")
    _supports_keywords(modal.App, {"include_source"})
    _supports_keywords(modal.Image.debian_slim, {"python_version"})
    _supports_keywords(modal.Volume.from_name, {"create_if_missing"})
    source_hashes = worker_source_files(project_root)
    image = modal.Image.debian_slim(python_version="3.12").pip_install(*IMAGE_PACKAGES)
    image = image.env({"PYTHONPATH": WORKER_ROOT, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    _supports_keywords(image.add_local_file, {"copy"})
    root = Path(project_root).resolve(strict=True)
    for relative in WORKER_SOURCE_ALLOWLIST:
        image = image.add_local_file(str(root / relative), f"{WORKER_ROOT}/{relative}", copy=True)
    volume = modal.Volume.from_name(existing_volume_name, create_if_missing=False)
    _supports_keywords(volume.with_mount_options, {"read_only"})
    volume = volume.with_mount_options(read_only=True)
    app = modal.App("biopilot-bench-worker", include_source=False)
    options = {"image": image, "gpu": gpu, "max_containers": 1, "min_containers": 0,
               "buffer_containers": 0, "cpu": WORKER_CPU_BOUNDS,
               "memory": WORKER_MEMORY_MIB_BOUNDS,
               "startup_timeout": WORKER_STARTUP_TIMEOUT_SECONDS,
               "scaledown_window": WORKER_SCALEDOWN_SECONDS,
               "retries": 0, "timeout": timeout_seconds, "volumes": {MODEL_MOUNT: volume},
               "secrets": [], "include_source": False, "serialized": True, "block_network": True}
    _supports_keywords(app.function, options)

    @app.function(**options)
    def infer_positions(payload):
        # This closure contains only reviewed source digests and model-location
        # metadata. No environment mapping, token, .env or host object is captured.
        _verify_worker_sources(source_hashes, WORKER_ROOT)
        return execute_request(payload, frozen_manifest)

    return ModalWorkerDefinition(app, infer_positions, actual_sdk_version, canonical_digest(source_hashes),
                                 execution_timeout_seconds=timeout_seconds)
