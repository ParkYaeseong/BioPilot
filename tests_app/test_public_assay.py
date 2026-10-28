"""Synthetic CSV reconciliation only; no real assay outcomes or models."""
from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from evaluation.prepare import REFERENCE_SHA256, digest, freeze_predictions, prepare_cohort
from evaluation.public_assay import evaluate_public_assay, write_public_report


PUBLIC_SEQUENCE = "MKFVKRRIIALVTILMLSVTSLFALQPSAKAAEHNPVVMVHGIGGASFNFAGIKSYLVSQGWSRDKLYAVDFWDKTGTNYNNGPVLSRFVQKVLDETGAKKVDIVAHSMGGANTLYYIKNLDGGNKVANVVTLGGANRLTTGKALPGTDPNQKILYTSIYSSADMIVMNYLSRLDGARNVQIHGVGHIGLLYSSQVNSLIKEGLNGGGQNTN"
IDS = ["A32V", "E33A", "H34A", "N35A"]


def frozen(ids=None, k=2):
    ids = IDS if ids is None else ids
    sites = {str(int(cid[1:-1])): "development" for cid in ids}
    protocol = {
        "source_mode": "synthetic_fixture", "analysis_scope": "development_only",
        "reference_id": "ESTA_BACSU_Nutschel_2020", "reference_sha256": REFERENCE_SHA256,
        "checkpoint": "esm2_t30_150M_UR50D", "weights_sha256": "b" * 64,
        "tokenizer_sha256": "c" * 64, "sequence_context": "full_212",
        "score_kind": "masked_marginal_log_likelihood_ratio", "rank_policy": "esm150_masked_v1",
        "protected_positions": [108, 164, 187], "top_k": k,
        "tie_rule": "candidate_id_ascending", "seed": 42, "site_splits": sites,
        "prompt_sha256": "d" * 64, "budget_sha256": "e" * 64, "code_sha256": "f" * 64,
    }
    cohort = prepare_cohort(ids, protocol)
    records = [{"candidate_id": cid, "score": float(len(ids) - index), "source_mode": "synthetic_fixture"}
               for index, cid in enumerate(ids)]
    return freeze_predictions(records, cohort)


def synthetic_csv(tmp_path, rows, name="synthetic.csv", fields=("mutant", "DMS_score")):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    payload = stream.getvalue().encode("utf-8")
    path = tmp_path / name
    path.write_bytes(payload)
    source = {"source_url": "synthetic://public-assay-fixture", "source_version": "synthetic-fixture-v1",
              "source_sha256": hashlib.sha256(payload).hexdigest(), "source_mode": "synthetic_fixture"}
    return path, source


def rows():
    return [{"mutant": cid, "DMS_score": str(value)} for cid, value in zip(IDS, [1., 2., 3., 4.])]


def evaluate(bundle, path, source, **kwargs):
    return evaluate_public_assay(bundle, path, bundle["freeze_sha256"], source, **kwargs)


def test_freeze_verified_before_any_csv_file_is_opened(tmp_path, monkeypatch):
    bundle = frozen()
    def forbidden(*args, **kwargs):
        raise AssertionError("CSV opening occurred before freeze verification")
    monkeypatch.setattr(Path, "open", forbidden)
    with pytest.raises(ValueError, match="freeze|checksum"):
        evaluate_public_assay(bundle, tmp_path / "not-present.csv", "0" * 64, {})


def test_missing_prediction_refused_before_label_read_even_with_rehashed_bundle(tmp_path, monkeypatch):
    bundle = frozen()
    bundle["records"].pop()
    bundle["freeze_sha256"] = digest({key: value for key, value in bundle.items() if key != "freeze_sha256"})
    def forbidden(*args, **kwargs):
        raise AssertionError("Incomplete predictions must be rejected before label access")
    monkeypatch.setattr(Path, "open", forbidden)
    with pytest.raises(ValueError):
        evaluate(bundle, tmp_path / "not-present.csv", {})


def test_full_cohort_and_outside_rows_reconcile_without_outcome_exports(tmp_path):
    source_rows = rows() + [{"mutant": "P36A", "DMS_score": "100.0123456789"}]
    path, source = synthetic_csv(tmp_path, source_rows)
    report = evaluate(frozen(), path, source)
    assert report["original_cohort_size"] == 4
    assert report["prediction_completeness"] == 1.
    assert report["source_row_count"] == 5
    assert report["outside_cohort_row_count"] == 1
    assert report["matched_label_count"] == 4
    assert report["missing_label_count"] == 0
    assert report["primary_metrics"]["spearman"] == pytest.approx(-1.)
    assert report["source_manifest"] == source
    assert report["evaluator_only"] is True
    assert report["scientific_evidence"] is False
    assert report["calibrated_T50"] is False
    assert report["wt_improvement"] is None
    exported = json.dumps(report)
    assert "100.0123456789" not in exported
    assert '"outcome"' not in exported and '"DMS_score"' not in exported


def test_missing_measurements_keep_original_denominator_and_primary_null(tmp_path):
    path, source = synthetic_csv(tmp_path, rows()[:-1])
    report = evaluate(frozen(), path, source)
    assert report["original_cohort_size"] == 4
    assert report["matched_label_count"] == 3
    assert report["missing_label_ids"] == ["N35A"]
    assert report["primary_metrics"]["spearman"] is None
    assert report["primary_metrics"]["recall_at_k"] is None
    secondary = report["secondary_complete_case"]
    assert secondary["status"] == "conditional_on_valid_unique_measurements"
    assert secondary["cohort_size"] == 3 and secondary["top_k"] == 2
    assert secondary["spearman"] == pytest.approx(-1.)
    assert secondary["recall_at_k"] == .5
    assert report["prediction_freeze_sha256"] == frozen()["freeze_sha256"]


def test_duplicate_measurements_exclude_every_copy_without_aggregation(tmp_path):
    path, source = synthetic_csv(tmp_path, rows() + [{"mutant": "A32V", "DMS_score": "999.9912345"}])
    report = evaluate(frozen(), path, source)
    assert report["duplicate_row_count"] == 1
    assert report["duplicate_candidate_count"] == 1
    assert report["matched_label_count"] == 3
    assert report["missing_label_ids"] == ["A32V"]
    assert report["row_exclusion_counts"]["duplicate_measurement"] == 2
    assert "999.9912345" not in json.dumps(report)


@pytest.mark.parametrize("outcome,reason", [("nan", "nonfinite_outcome"), ("inf", "nonfinite_outcome"),
                                            ("", "missing_outcome"), ("unavailable", "nonnumeric_outcome")])
def test_missing_nonfinite_and_nonnumeric_are_not_zero(tmp_path, outcome, reason):
    data = rows()
    data[0]["DMS_score"] = outcome
    path, source = synthetic_csv(tmp_path, data)
    report = evaluate(frozen(), path, source)
    assert report["matched_label_count"] == 3
    assert report["row_exclusion_counts"][reason] == 1
    assert report["missing_label_ids"] == ["A32V"]
    assert report["primary_metrics"]["recall_at_k"] is None


def test_outside_cohort_nonfinite_rows_remain_in_source_diagnostics(tmp_path):
    path, source = synthetic_csv(tmp_path, rows() + [{"mutant": "P36A", "DMS_score": "nan"}])
    report = evaluate(frozen(), path, source)
    assert report["source_row_count"] == 5
    assert report["outside_cohort_row_count"] == 1
    assert report["nonfinite_row_count"] == 1
    assert report["source_outcome_diagnostics"]["nonfinite_outcome"] == 1
    assert report["matched_label_count"] == 4
    assert report["row_exclusion_counts"]["outside_frozen_cohort"] == 1
    assert report["row_exclusion_counts"]["nonfinite_outcome"] == 0


def test_original_k_is_never_lowered_for_incomplete_measurements(tmp_path):
    path, source = synthetic_csv(tmp_path, rows()[:2])
    report = evaluate(frozen(k=3), path, source)
    assert report["frozen_top_k"] == 3
    assert report["secondary_complete_case"]["cohort_size"] == 2
    assert report["secondary_complete_case"]["spearman"] is None
    assert report["secondary_complete_case"]["recall_at_k"] is None
    assert report["secondary_complete_case"]["status"] == "insufficient_measurements_for_frozen_k"


def test_constant_outcomes_return_undefined_correlation(tmp_path):
    data = rows()
    for row in data:
        row["DMS_score"] = "7.123456789"
    path, source = synthetic_csv(tmp_path, data)
    report = evaluate(frozen(), path, source)
    assert report["primary_metrics"]["spearman"] is None
    assert report["primary_metrics"]["recall_at_k"] == 1.
    assert "7.123456789" not in json.dumps(report)


def test_mutated_sequence_and_wt_correspondence_are_checked(tmp_path):
    data = []
    for item in rows():
        cid = item["mutant"]
        pos = int(cid[1:-1])
        sequence = PUBLIC_SEQUENCE[:pos-1] + cid[-1] + PUBLIC_SEQUENCE[pos:]
        data.append({**item, "mutated_sequence": sequence})
    data[0]["mutated_sequence"] = PUBLIC_SEQUENCE
    data.append({"mutant": "A33V", "DMS_score": "2", "mutated_sequence": PUBLIC_SEQUENCE})
    path, source = synthetic_csv(tmp_path, data, fields=("mutant", "DMS_score", "mutated_sequence"))
    report = evaluate(frozen(), path, source)
    assert report["row_exclusion_counts"]["mutated_sequence_mismatch"] == 1
    assert report["row_exclusion_counts"]["wild_type_or_position_mismatch"] == 1
    assert report["matched_label_count"] == 3


def test_source_bytes_hash_must_match_manifest(tmp_path):
    path, source = synthetic_csv(tmp_path, rows())
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="checksum|hash"):
        evaluate(frozen(), path, source)


def test_runtime_paths_and_existing_report_overwrite_are_blocked(tmp_path):
    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    path, source = synthetic_csv(runtime, rows())
    with pytest.raises(ValueError):
        evaluate(frozen(), path, source, runtime_root=runtime)
    safe_path, safe_source = synthetic_csv(tmp_path, rows())
    report = evaluate(frozen(), safe_path, safe_source, runtime_root=runtime)
    with pytest.raises(ValueError):
        write_public_report(report, runtime / "report.json", runtime_root=runtime)
    output = tmp_path / "report.json"
    write_public_report(report, output, runtime_root=runtime)
    assert json.loads(output.read_text())["evaluator_only"] is True
    with pytest.raises(FileExistsError):
        write_public_report(report, output, runtime_root=runtime)


def test_exact_190_theoretical_predictions_preserved_with_partial_measurement_fixture(tmp_path):
    positions = [32, 50, 70, 90, 110, 130, 150, 170, 190, 205]
    aa = "ACDEFGHIKLMNPQRSTVWY"
    ids = [f"{PUBLIC_SEQUENCE[pos-1]}{pos}{alt}" for pos in positions for alt in aa if alt != PUBLIC_SEQUENCE[pos-1]]
    bundle = frozen(ids, k=20)
    path, source = synthetic_csv(tmp_path, [{"mutant": cid, "DMS_score": str(index)} for index, cid in enumerate(ids[:50])])
    report = evaluate(bundle, path, source)
    assert report["original_cohort_size"] == 190
    assert report["predictions_present"] == 190
    assert report["matched_label_count"] == 50
    assert report["missing_label_count"] == 140
    assert report["primary_metrics"]["spearman"] is None
    assert report["secondary_complete_case"]["cohort_size"] == 50
    assert report["secondary_complete_case"]["top_k"] == 20
    assert report["prediction_freeze_sha256"] == bundle["freeze_sha256"]


def test_optional_raw_comparison_uses_only_ids_and_preserves_counts(tmp_path):
    curated_path, curated_source = synthetic_csv(tmp_path, rows(), name="curated.csv")
    raw_path, raw_source = synthetic_csv(tmp_path, [{"mutant": cid} for cid in IDS + ["P36A"]], name="raw.csv", fields=("mutant",))
    report = evaluate(frozen(), curated_path, curated_source, raw_csv_path=raw_path, raw_source_manifest=raw_source)
    raw = report["raw_comparison"]
    assert raw["raw_row_count"] == 5 and raw["curated_row_count"] == 4
    assert raw["raw_only_variant_count"] == 1 and raw["curated_only_variant_count"] == 0
    assert raw["missingness_cause"] == "not_inferred"


def test_raw_alternate_header_requires_explicit_column_mapping(tmp_path):
    curated_path, curated_source = synthetic_csv(tmp_path, rows(), name="curated.csv")
    raw_rows = [{"Variants of BsLipA": cid, "T50": "do-not-interpret", "T50.1": "also-uninterpreted"} for cid in IDS]
    raw_path, raw_source = synthetic_csv(tmp_path, raw_rows, name="raw-alternate.csv", fields=("Variants of BsLipA", "T50", "T50.1"))
    with pytest.raises(ValueError):
        evaluate(frozen(), curated_path, curated_source, raw_csv_path=raw_path, raw_source_manifest=raw_source)
    report = evaluate(frozen(), curated_path, curated_source, raw_csv_path=raw_path, raw_source_manifest=raw_source,
                      raw_variant_column="Variants of BsLipA", raw_numbering="full_reference_1based")
    comparison = report["raw_comparison"]
    assert comparison["shared_variant_count"] == 4
    assert comparison["outcome_transformation_verified"] is False
    mapping = comparison["raw_source_manifest"]["import_mapping"]
    assert mapping["variant_column"] == "Variants of BsLipA"
    assert mapping["input_numbering"] == "full_reference_1based"
    assert "do-not-interpret" not in json.dumps(report)
    assert "also-uninterpreted" not in json.dumps(report)


def test_explicit_mature_frame_uses_unique_sequence_correspondence(tmp_path):
    curated_path, curated_source = synthetic_csv(tmp_path, rows(), name="curated.csv")
    mature_ids = [f"{cid[0]}{int(cid[1:-1])-31}{cid[-1]}" for cid in IDS]
    raw_path, raw_source = synthetic_csv(tmp_path, [{"variant": cid} for cid in mature_ids], name="raw-mature.csv", fields=("variant",))
    with pytest.raises(ValueError):
        evaluate(frozen(), curated_path, curated_source, raw_csv_path=raw_path, raw_source_manifest=raw_source,
                 raw_variant_column="variant", raw_numbering="full_reference_1based")
    report = evaluate(frozen(), curated_path, curated_source, raw_csv_path=raw_path, raw_source_manifest=raw_source,
                      raw_variant_column="variant", raw_numbering="mature_1based")
    comparison = report["raw_comparison"]
    assert comparison["shared_variant_count"] == 4
    assert comparison["raw_only_variant_count"] == 0
    mapping = comparison["raw_source_manifest"]["import_mapping"]
    assert mapping["mapping_method"] == "unique_exact_sequence_match"
    assert mapping["mature_start_full_1based"] == 32


def test_ambiguous_mature_sequence_mapping_is_rejected():
    from evaluation.public_assay import _unique_sequence_start
    with pytest.raises(ValueError, match="ambiguous|unique"):
        _unique_sequence_start("ACAC", "AC")
    with pytest.raises(ValueError):
        _unique_sequence_start("ACDE", "WW")


def test_raw_auto_frame_and_unknown_column_are_rejected(tmp_path):
    curated_path, curated_source = synthetic_csv(tmp_path, rows(), name="curated.csv")
    raw_path, raw_source = synthetic_csv(tmp_path, [{"mutant": cid} for cid in IDS], name="raw.csv", fields=("mutant",))
    for settings in ({"raw_numbering": "auto"}, {"raw_variant_column": "unknown-column"}):
        with pytest.raises(ValueError):
            evaluate(frozen(), curated_path, curated_source, raw_csv_path=raw_path, raw_source_manifest=raw_source, **settings)
