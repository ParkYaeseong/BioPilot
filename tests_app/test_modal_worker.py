"""Offline Modal-definition fixtures; no SDK, GPU, upload or remote calls."""
from copy import deepcopy
import importlib
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.targets import FRAME, REFERENCE_ID, REFERENCE_SHA256, registered_profile, validate_target
from app.science.esm_engine import ESMEngine
from app.science.modal_worker import create_modal_app, execute_request, worker_source_files
from app.science.models import get_model_spec
from app.science.providers import InferenceRequest


ROOT = Path(__file__).resolve().parents[1]
AA = "ACDEFGHIKLMNPQRSTVWY"
WEIGHTS, TOKENIZER = "a" * 64, "b" * 64


class SyntheticBackend:
    mask_token_id = 0

    def __init__(self, key="esm150"):
        spec = get_model_spec(key)
        self.provenance = {"checkpoint": spec.checkpoint, "model_key": key,
                           "rank_policy": spec.rank_policy, "weights_sha256": WEIGHTS,
                           "tokenizer_sha256": TOKENIZER, "implementation": "synthetic-modal-worker-test",
                           "precision": "float32", "source_mode": "synthetic_fixture"}

    def token_id(self, residue):
        return AA.index(residue) + 1

    def tokenize(self, sequence):
        return [21] + [self.token_id(aa) for aa in sequence] + [22]

    def forward(self, token_ids):
        return [[index / 10. for index in range(23)] for _ in token_ids]


def request(key="esm150"):
    return InferenceRequest(REFERENCE_ID, REFERENCE_SHA256, FRAME, "full_212", (32,), key, WEIGHTS, TOKENIZER)


def manifest(key="esm150"):
    return {key: {"checkpoint_dir": f"/models/{key}/pinned-revision",
                  "expected_weights_sha256": WEIGHTS, "expected_tokenizer_sha256": TOKENIZER}}


@pytest.mark.parametrize("key", ["esm35", "esm150", "esm650"])
def test_worker_fixture_matches_same_local_masked_scoring(key):
    calls = []
    def factory(checkpoint_dir, **kwargs):
        calls.append((checkpoint_dir, kwargs))
        return SyntheticBackend(key)
    artifact = execute_request(request(key).to_payload(), manifest(key), backend_factory=factory)
    target = validate_target(registered_profile(), "sequence_plausibility_review")
    local_artifact = ESMEngine(SyntheticBackend(key)).score_positions(target, [32], key)
    assert artifact == local_artifact
    assert artifact["source_mode"] == "synthetic_fixture"
    assert calls == [(f"/models/{key}/pinned-revision", {
        "checkpoint_key": key, "device": "cuda", "expected_weights_sha256": WEIGHTS,
        "expected_tokenizer_sha256": TOKENIZER})]


@pytest.mark.parametrize("extra", [{"sequence": "UNAPPROVED"}, {"api_key": "never-serialize-secrets"},
                                  {"checkpoint_dir": "/other/path"}, {"env": {"MODEL_API_KEY": "forbidden"}}])
def test_worker_rejects_extra_payload_data_before_backend(extra):
    payload = {**request().to_payload(), **extra}
    calls = []
    with pytest.raises(ValueError):
        execute_request(payload, manifest(), backend_factory=lambda *a, **k: calls.append(1))
    assert calls == []


@pytest.mark.parametrize("change", [{"positions": [108]}, {"positions": [32, 32]},
                                   {"reference_sha256": "0" * 64}, {"reference_numbering": "mature_1based"},
                                   {"model_key": "unknown"}, {"positions": []}])
def test_worker_revalidates_target_frame_and_position_guards(change):
    calls = []
    with pytest.raises(ValueError):
        execute_request({**request().to_payload(), **change}, manifest(),
                        backend_factory=lambda *a, **k: calls.append(1))
    assert calls == []


def test_manifest_pin_mismatch_and_unprovisioned_model_never_fallback():
    calls = []
    bad = manifest()
    bad["esm150"]["expected_weights_sha256"] = "c" * 64
    for provisioned in [bad, manifest("esm35")]:
        with pytest.raises(ValueError):
            execute_request(request().to_payload(), provisioned, backend_factory=lambda *a, **k: calls.append(1))
    assert calls == []


def test_backend_cannot_ignore_the_manifest_pins():
    bad = SyntheticBackend()
    bad.provenance["weights_sha256"] = "f" * 64
    with pytest.raises(ValueError):
        execute_request(request().to_payload(), manifest(), backend_factory=lambda *a, **k: bad)


def test_manifest_cannot_include_credentials_or_unreviewed_settings():
    provisioned = manifest()
    provisioned["esm150"]["MODEL_API_KEY"] = "forbidden-fixture-value"
    with pytest.raises(ValueError):
        execute_request(request().to_payload(), provisioned, backend_factory=lambda *a, **k: SyntheticBackend())


def test_deployment_default_blocks_before_optional_sdk_import(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Optional Modal SDK must not be imported before approval")
    monkeypatch.setattr(importlib, "import_module", forbidden)
    with pytest.raises(PermissionError):
        create_modal_app(manifest(), project_root=ROOT, expected_sdk_version="1.4.1")


def test_existing_volume_requires_its_explicit_approval():
    with pytest.raises(PermissionError):
        create_modal_app(manifest(), project_root=ROOT, expected_sdk_version="1.4.1",
                         deployment_approved=True, existing_volume_name="existing-models")


def test_source_allowlist_omits_host_evaluator_and_secrets():
    sources = worker_source_files(ROOT)
    assert "app/science/modal_worker.py" in sources
    assert "reference/target_profile.json" in sources
    assert "app/science/providers.py" in sources
    forbidden = {"host", "evaluation", "evaluation_private", "tests", "tests_app", "docs", ".env"}
    for relative, digest in sources.items():
        assert not set(Path(relative).parts) & forbidden
        assert len(digest) == 64


class FakeImage:
    def __init__(self):
        self.files, self.environ, self.packages = [], {}, []
    def pip_install(self, *packages):
        self.packages.extend(packages)
        return self
    def env(self, env):
        self.environ.update(env)
        return self
    def add_local_file(self, local_path, remote_path, *, copy=False):
        self.files.append((str(local_path), remote_path, copy))
        return self


def fake_sdk():
    image = FakeImage()
    events = []
    class Volume:
        @staticmethod
        def from_name(name, *, create_if_missing=False):
            events.append(("volume", name, create_if_missing))
            return Volume()
        def with_mount_options(self, *, read_only=False):
            events.append(("mount", read_only))
            return self
    class App:
        def __init__(self, name, *, include_source=True):
            self.name, self.include_source = name, include_source
            self.options = None
        def function(self, **options):
            self.options = options
            return lambda function: function
    return SimpleNamespace(Image=SimpleNamespace(debian_slim=lambda **kwargs: image), Volume=Volume,
                           App=App), image, events


def test_approved_factory_definition_is_bounded_and_uses_only_file_allowlist(monkeypatch):
    from importlib import metadata
    sdk, image, events = fake_sdk()
    monkeypatch.setattr(metadata, "version", lambda name: "1.4.1")
    monkeypatch.setattr(importlib, "import_module", lambda name: sdk)
    definition = create_modal_app(manifest(), project_root=ROOT, expected_sdk_version="1.4.1",
                                  deployment_approved=True, volume_approved=True,
                                  existing_volume_name="existing-models", timeout_seconds=120)
    options = definition.app.options
    assert definition.sdk_version == "1.4.1"
    assert definition.compatibility_status == "definition_only_not_deployed"
    assert options["gpu"] == "T4"
    assert options["max_containers"] == 1 and options["min_containers"] == 0
    assert options["retries"] == 0 and options["timeout"] == 120
    assert options["secrets"] == [] and options["include_source"] is False
    assert options["block_network"] is True
    assert definition.app.include_source is False
    assert events == [("volume", "existing-models", False), ("mount", True)]
    assert len(image.files) == len(worker_source_files(ROOT))
    assert all(remote.startswith("/opt/biopilot/") for _, remote, _ in image.files)
    assert all("==" in package for package in image.packages)
    assert not set(image.environ) & {"MODEL_API_KEY", "MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"}
    captured = inspect.getclosurevars(definition.function).nonlocals
    assert not any("key" in name or "token" in name for name in captured)


def test_sdk_version_must_match_before_any_definition(monkeypatch):
    from importlib import metadata
    monkeypatch.setattr(metadata, "version", lambda name: "1.2.3")
    with pytest.raises(RuntimeError):
        create_modal_app(manifest(), project_root=ROOT, expected_sdk_version="1.4.1",
                         deployment_approved=True, volume_approved=True, existing_volume_name="existing-models")


def test_definition_freezes_manifest_without_capturing_host_environment(monkeypatch):
    from importlib import metadata
    import app.science.modal_worker as worker
    sdk, _, _ = fake_sdk()
    monkeypatch.setattr(metadata, "version", lambda name: "1.4.1")
    monkeypatch.setattr(importlib, "import_module", lambda name: sdk)
    provisioned = manifest()
    definition = create_modal_app(provisioned, project_root=ROOT, expected_sdk_version="1.4.1",
                                  deployment_approved=True, volume_approved=True,
                                  existing_volume_name="existing-models")
    provisioned["esm150"]["checkpoint_dir"] = "/models/tampered"
    captured = []
    monkeypatch.setattr(worker, "_verify_worker_sources", lambda *a: None)
    monkeypatch.setattr(worker, "execute_request", lambda payload, models: captured.append(models))
    definition.function(request().to_payload())
    assert captured[0]["esm150"]["checkpoint_dir"] == "/models/esm150/pinned-revision"


def test_source_manifest_detects_changes_without_reading_unlisted_files(monkeypatch):
    import app.science.modal_worker as worker
    expected = worker_source_files(ROOT)
    altered = dict(expected)
    altered["app/science/esm_engine.py"] = "0" * 64
    monkeypatch.setattr(worker, "worker_source_files", lambda root: altered)
    with pytest.raises(ValueError):
        worker._verify_worker_sources(expected, ROOT)


@pytest.mark.parametrize("timeout", [0, 901, True])
def test_timeout_above_approved_max_or_invalid_is_refused(timeout):
    with pytest.raises(ValueError):
        create_modal_app(manifest(), project_root=ROOT, expected_sdk_version="1.4.1",
                         deployment_approved=True, volume_approved=True,
                         existing_volume_name="existing-models", timeout_seconds=timeout)
