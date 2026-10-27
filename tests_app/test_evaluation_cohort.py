"""Synthetic evaluator checks only; these values are not biological evidence."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from evaluation.baseline import evaluate_predictions, spearman
from evaluation.prepare import assert_evaluator_path, digest, freeze_predictions, freeze_score_artifact, prepare_cohort, validate_frozen_predictions


IDS = ["A32V", "E33A", "H34A", "N35A"]


def protocol(**changes):
    result = {
        "source_mode": "synthetic_fixture", "analysis_scope": "development_only",
        "reference_id": "ESTA_BACSU_Nutschel_2020", "reference_sha256": "a" * 64,
        "checkpoint": "esm2_t30_150M_UR50D", "weights_sha256": "b" * 64,
        "tokenizer_sha256": "c" * 64, "sequence_context": "full_212",
        "score_kind": "masked_marginal_log_likelihood_ratio", "rank_policy": "esm150_masked_v1",
        "protected_positions": [108, 164, 187], "top_k": 2,
        "tie_rule": "candidate_id_ascending", "seed": 42,
        "site_splits": {"32": "development", "33": "development", "34": "development", "35": "development"},
        "prompt_sha256": "d" * 64, "budget_sha256": "e" * 64,
        "code_sha256": "f" * 64,
    }
    result.update(changes)
    return result


def records():
    return [{"candidate_id": cid, "score": score, "source_mode": "synthetic_fixture"}
            for cid, score in zip(IDS, [4., 3., 2., 1.])]


def frozen():
    return freeze_predictions(records(), prepare_cohort(IDS, protocol()))


def labels(values=(1., 2., 3., 4.)):
    return {"source_mode": "synthetic_fixture", "records": [
        {"candidate_id": cid, "outcome": value} for cid, value in zip(IDS, values)]}


def evaluate(bundle, label_records=None):
    return evaluate_predictions(bundle, labels() if label_records is None else label_records,
                                expected_freeze_sha256=bundle["freeze_sha256"])


def test_spearman_average_ties_and_undefined_vectors():
    assert spearman([1, 1, 3], [1, 2, 3]) == pytest.approx(0.8660254037844387)
    assert spearman([1, 2, 3], [3, 2, 1]) == pytest.approx(-1)
    assert spearman([1, 1], [2, 3]) is None
    assert spearman([1], [2]) is None
    with pytest.raises(ValueError):
        spearman([1, float("nan")], [1, 2])


def test_frozen_prediction_hash_is_independent_and_immutable():
    bundle = frozen()
    assert len(bundle["freeze_sha256"]) == 64
    validate_frozen_predictions(bundle, bundle["freeze_sha256"])
    changed = deepcopy(bundle)
    changed["records"][0]["score"] = 1000
    with pytest.raises(ValueError, match="hash|checksum"):
        validate_frozen_predictions(changed, bundle["freeze_sha256"])
    with pytest.raises(ValueError):
        validate_frozen_predictions(bundle, "0" * 64)


@pytest.mark.parametrize("bad", [records()[:-1], records() + [records()[0]], records() + [{"candidate_id": "V36A", "score": 1., "source_mode": "synthetic_fixture"}]])
def test_missing_duplicate_and_unexpected_predictions_refused(bad):
    with pytest.raises(ValueError):
        freeze_predictions(bad, prepare_cohort(IDS, protocol()))


def test_cohort_duplicate_and_invalid_k_refused():
    with pytest.raises(ValueError):
        prepare_cohort(IDS + [IDS[0]], protocol())
    for k in [0, 5, True]:
        with pytest.raises(ValueError):
            prepare_cohort(IDS, protocol(top_k=k))


def test_site_grouping_and_protocol_frozen_before_labels():
    cohort = prepare_cohort(["A32V", "A32L"], protocol(top_k=1, site_splits={"32": "development"}))
    assert cohort["candidate_sites"] == {"A32L": 32, "A32V": 32}
    with pytest.raises(ValueError):
        prepare_cohort(IDS, protocol(site_splits={"32": "development"}))
    with pytest.raises(ValueError):
        prepare_cohort(IDS, protocol(labels=[1, 2, 3, 4]))


def test_metrics_preserve_cohort_and_do_not_claim_wt_or_temperature():
    result = evaluate(frozen())
    assert result["cohort_size"] == 4
    assert result["completeness"] == 1.0
    assert result["spearman"] == pytest.approx(-1)
    assert result["recall_at_k"] == 0
    assert result["random_expected_recall_at_k"] == .5
    assert result["wt_improvement"] is None
    assert result["calibrated_T50"] is False
    assert result["source_mode"] == "synthetic_fixture"
    assert result["scientific_evidence"] is False


def test_recall_top_k_ties_use_candidate_id_ascending():
    source = records()
    for row in source:
        row["score"] = 1.
    bundle = freeze_predictions(list(reversed(source)), prepare_cohort(IDS, protocol()))
    result = evaluate(bundle, labels([1., 1., 1., 1.]))
    assert result["predicted_top_k"] == ["A32V", "E33A"]
    assert result["observed_top_k"] == ["A32V", "E33A"]
    assert result["recall_at_k"] == 1.
    assert result["spearman"] is None


@pytest.mark.parametrize("mutate", [
    lambda d: d["records"].pop(),
    lambda d: d["records"].append(d["records"][0]),
    lambda d: d["records"][0].update(outcome=None),
    lambda d: d["records"][0].update(outcome=float("inf")),
])
def test_missing_duplicate_or_nonfinite_labels_never_shrink_cohort(mutate):
    data = labels()
    mutate(data)
    with pytest.raises(ValueError):
        evaluate(frozen(), data)


def test_fixture_and_real_evaluation_cannot_be_mixed():
    data = labels()
    data["source_mode"] = "imported_snapshot"
    with pytest.raises(ValueError):
        evaluate(frozen(), data)


@pytest.mark.parametrize("checkpoint,rank_policy", [
    ("esm2_t12_35M_UR50D", "esm35_masked_v1"),
    ("esm2_t33_650M_UR50D", "esm650_masked_v1"),
])
def test_alternate_checkpoint_requires_explicit_matching_frozen_policy(checkpoint, rank_policy):
    selected = protocol(checkpoint=checkpoint, rank_policy=rank_policy)
    cohort = prepare_cohort(IDS, selected)
    bundle = freeze_predictions(records(), cohort)
    assert bundle["cohort"]["protocol"]["rank_policy"] == rank_policy
    assert evaluate(bundle)["cohort_size"] == len(IDS)
    # The original default remains esm150; an explicit checkpoint alone cannot
    # silently change the common ranking policy or promote a 650M annotation.
    with pytest.raises(ValueError):
        prepare_cohort(IDS, protocol(checkpoint=checkpoint))


@pytest.mark.parametrize("checkpoint,rank_policy", [
    ("esm2_t12_35M_UR50D", "esm35_masked_v1"),
    ("esm2_t30_150M_UR50D", "esm150_masked_v1"),
    ("esm2_t33_650M_UR50D", "esm650_masked_v1"),
])
def test_mixed_checkpoint_or_policy_rows_cannot_enter_frozen_rank(checkpoint, rank_policy):
    cohort = prepare_cohort(IDS, protocol(checkpoint=checkpoint, rank_policy=rank_policy))
    mixed = records()
    for row in mixed:
        row["checkpoint"] = checkpoint
    mixed[-1]["checkpoint"] = "esm2_t30_150M_UR50D" if checkpoint != "esm2_t30_150M_UR50D" else "esm2_t33_650M_UR50D"
    with pytest.raises(ValueError):
        freeze_predictions(mixed, cohort)
    wrong_policy = "esm650_masked_v1" if rank_policy != "esm650_masked_v1" else "esm35_masked_v1"
    with pytest.raises(ValueError):
        prepare_cohort(IDS, protocol(checkpoint=checkpoint, rank_policy=wrong_policy))


def engine_artifact_fixture(model_key="esm150"):
    # Only the test imports the product engine. Evaluation preparation itself
    # remains pure stdlib code, and the product never imports the evaluator.
    from app.core.targets import registered_profile, validate_target
    from app.science.esm_engine import ESMEngine
    from app.science.models import get_model_spec
    amino_acids = "ACDEFGHIKLMNPQRSTVWY"
    spec = get_model_spec(model_key)
    class SyntheticBackend:
        mask_token_id = 0
        provenance = {"checkpoint": spec.checkpoint, "model_key": model_key,
                      "rank_policy": spec.rank_policy, "weights_sha256": "b" * 64,
                      "tokenizer_sha256": "c" * 64, "config_sha256": "1" * 64,
                      "weight_file_hashes": {"fixture.safetensors": "2" * 64},
                      "implementation": "synthetic-evaluator-artifact-test", "precision": "float32",
                      "source_mode": "synthetic_fixture", "device": "fixture",
                      "checkpoint_revision": None, "upstream_authenticity": "synthetic_fixture"}
        def token_id(self, amino_acid):
            return amino_acids.index(amino_acid) + 1
        def tokenize(self, sequence):
            return [21] + [self.token_id(aa) for aa in sequence] + [22]
        def forward(self, token_ids):
            return [[index / 10. for index in range(23)] for _ in token_ids]
    target = validate_target(registered_profile(), "sequence_plausibility_review")
    artifact = ESMEngine(SyntheticBackend()).score_positions(target, [32], model_key)
    cohort = prepare_cohort([row["candidate_id"] for row in artifact["rows"]], protocol(
        reference_sha256=target.reference_sha256, checkpoint=spec.checkpoint,
        rank_policy=spec.rank_policy, site_splits={"32": "development"}))
    return artifact, cohort


@pytest.mark.parametrize("model_key", ["esm35", "esm150", "esm650"])
def test_actual_engine_artifact_projects_complete_numeric_predictions(model_key):
    artifact, cohort = engine_artifact_fixture(model_key)
    original = deepcopy(artifact)
    bundle = freeze_score_artifact(artifact, cohort)
    assert artifact == original
    assert len(bundle["records"]) == 19
    assert {r["candidate_id"]: r["score"] for r in bundle["records"]} == {
        r["candidate_id"]: r["score"] for r in artifact["rows"]}
    assert bundle["source_artifact_sha256"] == artifact["artifact_sha256"]
    assert bundle["source_mode"] == "synthetic_fixture"
    assert all(set(row) == {"candidate_id", "score", "source_mode"} for row in bundle["records"])
    validate_frozen_predictions(bundle, bundle["freeze_sha256"])


def test_corrupt_numeric_artifact_rejected_before_projection():
    artifact, cohort = engine_artifact_fixture()
    artifact["rows"][0]["score"] += 1000
    with pytest.raises(ValueError, match="hash|checksum"):
        freeze_score_artifact(artifact, cohort)


@pytest.mark.parametrize("change", [
    {"checkpoint": "esm2_t33_650M_UR50D"},
    {"model_key": "esm650"},
    {"rank_policy": "esm650_masked_v1"},
    {"source_mode": "live"},
    {"weights_sha256": "0" * 64},
])
def test_mixed_score_artifact_metadata_refused_even_with_recomputed_hash(change):
    artifact, cohort = engine_artifact_fixture()
    artifact["rows"][-1].update(change)
    artifact["artifact_sha256"] = digest({k: v for k, v in artifact.items() if k != "artifact_sha256"})
    with pytest.raises(ValueError):
        freeze_score_artifact(artifact, cohort)


def test_artifact_freeze_requires_complete_prespecified_cohort():
    artifact, cohort = engine_artifact_fixture()
    artifact["rows"].pop()
    artifact["artifact_sha256"] = digest({k: v for k, v in artifact.items() if k != "artifact_sha256"})
    with pytest.raises(ValueError):
        freeze_score_artifact(artifact, cohort)


def test_runtime_paths_and_symlink_escapes_refused(tmp_path):
    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    inside = runtime / "labels.json"
    inside.write_text("[]")
    with pytest.raises(ValueError):
        assert_evaluator_path(inside, runtime)
    with pytest.raises(ValueError):
        assert_evaluator_path(runtime / "report.json", runtime, must_exist=False)
    outside = tmp_path / "external.json"
    outside.write_text("[]")
    assert assert_evaluator_path(outside, runtime) == outside.resolve()
    alias = tmp_path / "linked.json"
    try:
        alias.symlink_to(inside)
    except OSError:
        pytest.skip("Windows account lacks symlink creation rights")
    with pytest.raises(ValueError):
        assert_evaluator_path(alias, runtime)


def test_cli_freeze_is_checked_before_label_file_is_opened(tmp_path):
    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    pred = tmp_path / "predictions.json"
    bundle = frozen()
    pred.write_text(json.dumps(bundle))
    output = tmp_path / "report.json"
    command = [sys.executable, "-m", "evaluation.baseline", "--predictions", str(pred),
               "--expected-freeze-sha256", "0" * 64, "--labels", str(tmp_path / "missing-labels.json"),
               "--output", str(output), "--runtime-root", str(runtime)]
    process = subprocess.run(command, capture_output=True, text=True, timeout=20)
    assert process.returncode == 2
    assert "freeze" in process.stderr.lower() or "checksum" in process.stderr.lower()
    assert not output.exists()


def test_cli_separate_process_only_writes_evaluator_report(tmp_path):
    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    bundle = frozen()
    pred = tmp_path / "predictions.json"
    pred.write_text(json.dumps(bundle))
    label_file = tmp_path / "synthetic-labels.json"
    label_file.write_text(json.dumps(labels()))
    output = tmp_path / "report.json"
    command = [sys.executable, "-m", "evaluation.baseline", "--predictions", str(pred),
               "--expected-freeze-sha256", bundle["freeze_sha256"], "--labels", str(label_file),
               "--output", str(output), "--runtime-root", str(runtime)]
    process = subprocess.run(command, capture_output=True, text=True, timeout=20)
    assert process.returncode == 0, process.stderr
    report = json.loads(output.read_text())
    assert report["evaluator_only"] is True
    assert report["scientific_evidence"] is False
    assert not list(runtime.iterdir())
