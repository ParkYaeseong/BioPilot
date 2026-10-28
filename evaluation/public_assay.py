"""Evaluator-only public-assay reconciliation after prediction freeze.

No network, environment access, product imports, model calls, unit conversion or
phenotype calibration. Source outcome values remain in the isolated CSV; exported
reports contain counts and explicitly scoped aggregate metrics only.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from random import Random
import re
from urllib.parse import urlsplit

from evaluation.baseline import spearman
from evaluation.prepare import REFERENCE_SHA256, digest, validate_frozen_predictions


REFERENCE_ID = "ESTA_BACSU_Nutschel_2020"
# Public registered sequence snapshot, independently checked against its fixed
# hash below. It is used only for WT/full-position correspondence, never labels.
PUBLIC_REFERENCE_SEQUENCE = "MKFVKRRIIALVTILMLSVTSLFALQPSAKAAEHNPVVMVHGIGGASFNFAGIKSYLVSQGWSRDKLYAVDFWDKTGTNYNNGPVLSRFVQKVLDETGAKKVDIVAHSMGGANTLYYIKNLDGGNKVANVVTLGGANRLTTGKALPGTDPNQKILYTSIYSSADMIVMNYLSRLDGARNVQIHGVGHIGLLYSSQVNSLIKEGLNGGGQNTN"
PUBLIC_MATURE_SEQUENCE = "AEHNPVVMVHGIGGASFNFAGIKSYLVSQGWSRDKLYAVDFWDKTGTNYNNGPVLSRFVQKVLDETGAKKVDIVAHSMGGANTLYYIKNLDGGNKVANVVTLGGANRLTTGKALPGTDPNQKILYTSIYSSADMIVMNYLSRLDGARNVQIHGVGHIGLLYSSQVNSLIKEGLNGGGQNTN"
MATURE_SHA256 = "90914bba8255e2e85de3277fe0d5ffdfdeb8e5b741ff593dde001f73c413a065"
MAX_CSV_BYTES = 5 * 1024 * 1024
REQUIRED_MANIFEST = {"source_url", "source_version", "source_sha256", "source_mode"}
OPTIONAL_MANIFEST = {"assay_id", "archive_member", "content_length", "retrieved_at_utc"}
EXCLUSION_REASONS = (
    "invalid_variant_id", "wild_type_or_position_mismatch", "mutated_sequence_mismatch",
    "outside_frozen_cohort", "duplicate_measurement", "missing_outcome", "nonnumeric_outcome", "nonfinite_outcome",
)


def _outside_runtime(path, runtime_root=None, *, must_exist=True):
    raw = Path(path).absolute()
    boundary = (Path(__file__).resolve().parents[1] / ".runtime" if runtime_root is None else Path(runtime_root)).resolve()
    resolved = raw.resolve(strict=must_exist)
    for candidate in (raw, resolved):
        if (".runtime" in {part.casefold() for part in candidate.parts}
                or candidate == boundary or boundary in candidate.parents):
            raise ValueError("Evaluator inputs and reports must remain outside the product runtime")
    if must_exist and not resolved.is_file():
        raise ValueError("Evaluator source must be a regular local file")
    if not must_exist and not resolved.parent.is_dir():
        raise ValueError("Evaluator report parent must already exist")
    return resolved


def _manifest(source_manifest, fixture):
    if (not isinstance(source_manifest, dict) or not REQUIRED_MANIFEST <= set(source_manifest)
            or not set(source_manifest) <= REQUIRED_MANIFEST | OPTIONAL_MANIFEST):
        raise ValueError("Source manifest must contain explicit label-free provenance fields")
    result = deepcopy(source_manifest)
    if result["source_mode"] != ("synthetic_fixture" if fixture else "imported_snapshot"):
        raise ValueError("Synthetic fixtures and real public source modes cannot be mixed")
    for key in ("source_url", "source_version"):
        if not isinstance(result[key], str) or not result[key].strip() or len(result[key]) > 2000:
            raise ValueError("Source URL and release must be explicit bounded text")
    url = urlsplit(result["source_url"])
    if (fixture and url.scheme != "synthetic") or (not fixture and (url.scheme != "https" or not url.hostname)):
        raise ValueError("Real source provenance needs a public HTTPS URL; fixtures need a synthetic URL")
    if url.username is not None or url.password is not None or url.query:
        raise ValueError("Source provenance URL must not contain credentials or query secrets")
    if not isinstance(result["source_sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", result["source_sha256"]) is None:
        raise ValueError("Source manifest needs the exact downloaded CSV SHA256")
    if result.get("assay_id", REFERENCE_ID) != REFERENCE_ID:
        raise ValueError("Source assay does not match the registered target")
    if "content_length" in result and (type(result["content_length"]) is not int or result["content_length"] < 0):
        raise ValueError("Manifest content_length must be a nonnegative integer")
    for key in ("archive_member", "retrieved_at_utc"):
        if key in result and (not isinstance(result[key], str) or len(result[key]) > 1000):
            raise ValueError("Optional source provenance must be bounded text")
    return result


def _load_csv(path, source_manifest, fixture, runtime_root, *, outcome_required, variant_column="mutant"):
    manifest = _manifest(source_manifest, fixture)
    source_path = _outside_runtime(path, runtime_root)
    if source_path.stat().st_size > MAX_CSV_BYTES:
        raise ValueError("Assay CSV exceeds the evaluator 5 MiB size bound")
    payload = source_path.read_bytes()
    if len(payload) > MAX_CSV_BYTES:
        raise ValueError("Assay CSV exceeds the evaluator 5 MiB size bound")
    if hashlib.sha256(payload).hexdigest() != manifest["source_sha256"]:
        raise ValueError("Assay CSV checksum differs from the frozen source manifest")
    if "content_length" in manifest and manifest["content_length"] != len(payload):
        raise ValueError("Assay CSV length differs from its source manifest")
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig"), newline=""))
        if not isinstance(variant_column, str) or not variant_column or len(variant_column) > 256:
            raise ValueError("An explicit bounded raw variant-column name is required")
        if outcome_required and variant_column != "mutant":
            raise ValueError("Curated outcome imports require the standard mutant column")
        required = {"mutant", "DMS_score"} if outcome_required else {variant_column}
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)) or not required <= set(reader.fieldnames):
            raise ValueError("Assay CSV lacks unique required column names; no column semantics are guessed")
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError("Assay CSV row shape differs from its header")
    except (UnicodeError, csv.Error) as error:
        raise ValueError("Assay CSV must be well-formed UTF-8 CSV") from error
    if not outcome_required:
        # Raw outcome columns are deliberately discarded. An explicit header
        # mapping does not establish which experimental column was transformed.
        rows = [{"mutant": row[variant_column]} for row in rows]
    return rows, manifest


def _variant_reason(candidate_id):
    if not isinstance(candidate_id, str) or not 3 <= len(candidate_id) <= 5:
        return "invalid_variant_id"
    match = re.fullmatch(r"([ACDEFGHIKLMNPQRSTVWY])([1-9][0-9]*)([ACDEFGHIKLMNPQRSTVWY])", candidate_id)
    if match is None or match[1] == match[3]:
        return "invalid_variant_id"
    position = int(match[2])
    if not 1 <= position <= len(PUBLIC_REFERENCE_SEQUENCE) or PUBLIC_REFERENCE_SEQUENCE[position-1] != match[1]:
        return "wild_type_or_position_mismatch"
    return None


def _mutated_sequence(candidate_id):
    position = int(candidate_id[1:-1])
    return PUBLIC_REFERENCE_SEQUENCE[:position-1] + candidate_id[-1] + PUBLIC_REFERENCE_SEQUENCE[position:]


def _valid_source_ids(rows):
    return {row["mutant"].strip() for row in rows if _variant_reason(row["mutant"].strip()) is None}


def _outcome_value(text):
    text = text.strip()
    if not text:
        return "missing_outcome", None
    try:
        value = float(text)
    except ValueError:
        return "nonnumeric_outcome", None
    if not math.isfinite(value):
        return "nonfinite_outcome", None
    return None, value


BOOTSTRAP_SEED = 20261027
BOOTSTRAP_RESAMPLES = 2000


def site_bootstrap_spearman(predicted, observed, candidate_ids, *, resamples=BOOTSTRAP_RESAMPLES,
                            seed=BOOTSTRAP_SEED, confidence=0.95):
    """Percentile interval for Spearman, resampling sites rather than variants.

    Alternatives at one position share a residue environment, so variant-level
    resampling would understate uncertainty. Sites are drawn with replacement and
    every drawn site contributes all of its measured variants. Degenerate draws
    (constant ranks, fewer than two points) are counted, never silently dropped.
    """
    if not isinstance(resamples, int) or resamples < 1:
        raise ValueError("Bootstrap resamples must be a positive integer")
    if not isinstance(seed, int):
        raise ValueError("A bootstrap interval requires an explicit integer seed")
    if not 0 < confidence < 1:
        raise ValueError("Confidence must lie strictly between 0 and 1")
    sites = {}
    for cid in candidate_ids:
        sites.setdefault(int(cid[1:-1]), []).append(cid)
    ordered = sorted(sites)
    point = spearman([predicted[cid] for cid in candidate_ids], [observed[cid] for cid in candidate_ids])
    result = {"method": "percentile_bootstrap", "resampling_unit": "site", "seed": seed,
              "resamples": resamples, "confidence": confidence, "site_count": len(ordered),
              "measured_variant_count": len(candidate_ids), "point_estimate": point,
              "ci_low": None, "ci_high": None, "excludes_zero": None,
              "usable_resamples": 0, "degenerate_resamples": 0,
              "calibrated_T50": False, "establishes_general_performance": False,
              "status": "ok"}
    if len(ordered) < 2:
        result["status"] = "insufficient_sites_for_a_site_bootstrap"
        result["degenerate_resamples"] = resamples
        return result
    random = Random(seed)
    values = []
    for _ in range(resamples):
        drawn = [ordered[random.randrange(len(ordered))] for _ in ordered]
        picked = [cid for site in drawn for cid in sites[site]]
        value = spearman([predicted[cid] for cid in picked], [observed[cid] for cid in picked])
        if value is None:
            result["degenerate_resamples"] += 1
        else:
            values.append(value)
    result["usable_resamples"] = len(values)
    if not values:
        result["status"] = "all_resamples_degenerate"
        return result
    values.sort()
    tail = (1 - confidence) / 2
    result["ci_low"] = _percentile(values, tail)
    result["ci_high"] = _percentile(values, 1 - tail)
    result["excludes_zero"] = result["ci_low"] > 0 or result["ci_high"] < 0
    return result


def _percentile(sorted_values, fraction):
    """Linear interpolation between order statistics."""
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = fraction * (len(sorted_values) - 1)
    lower = int(math.floor(position))
    upper = min(lower + 1, len(sorted_values) - 1)
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (position - lower)


def _metrics(predicted, observed, candidate_ids, top_k):
    predicted_top = sorted(candidate_ids, key=lambda cid: (-predicted[cid], cid))[:top_k]
    observed_top = sorted(candidate_ids, key=lambda cid: (-observed[cid], cid))[:top_k]
    return {"spearman": spearman([predicted[cid] for cid in candidate_ids], [observed[cid] for cid in candidate_ids]),
            "recall_at_k": len(set(predicted_top) & set(observed_top)) / top_k}


def _unique_sequence_start(reference, mature):
    canonical = set("ACDEFGHIKLMNPQRSTVWY")
    if (not isinstance(reference, str) or not isinstance(mature, str) or not reference or not mature
            or not set(reference) <= canonical or not set(mature) <= canonical):
        raise ValueError("Exact sequence correspondence requires canonical sequences")
    starts = [i for i in range(len(reference)-len(mature)+1) if reference.startswith(mature, i)]
    if len(starts) != 1:
        raise ValueError("Mature sequence correspondence is absent or ambiguous; a unique match is required")
    return starts[0]


def _normalize_raw_ids(rows, variant_column, numbering):
    if numbering not in {"full_reference_1based", "mature_1based"}:
        raise ValueError("Raw numbering must be explicitly full_reference_1based or mature_1based; no auto-detection")
    mapping = {"variant_column": variant_column, "input_numbering": numbering,
               "output_numbering": "full_reference_1based", "reference_sha256": REFERENCE_SHA256,
               "mapping_method": "identity_registered_full_reference_1based"}
    start = 0
    if numbering == "mature_1based":
        if hashlib.sha256(PUBLIC_MATURE_SEQUENCE.encode("ascii")).hexdigest() != MATURE_SHA256:
            raise ValueError("Registered mature sequence hash mismatch")
        start = _unique_sequence_start(PUBLIC_REFERENCE_SEQUENCE, PUBLIC_MATURE_SEQUENCE)
        mapping.update(mapping_method="unique_exact_sequence_match", mature_sha256=MATURE_SHA256,
                       mature_start_full_1based=start+1)
    normalized = []
    for row in rows:
        cid = row["mutant"].strip()
        if numbering == "mature_1based":
            match = re.fullmatch(r"([ACDEFGHIKLMNPQRSTVWY])([1-9][0-9]{0,2})([ACDEFGHIKLMNPQRSTVWY])", cid)
            if (match is None or match[1] == match[3] or not 1 <= int(match[2]) <= len(PUBLIC_MATURE_SEQUENCE)
                    or PUBLIC_MATURE_SEQUENCE[int(match[2])-1] != match[1]):
                raise ValueError("Raw variant IDs do not all match the explicitly declared mature frame")
            cid = f"{match[1]}{start+int(match[2])}{match[3]}"
        if _variant_reason(cid) is not None:
            raise ValueError("Raw variant IDs do not all match the explicitly declared full-reference frame")
        normalized.append({"mutant": cid})
    return normalized, mapping


def evaluate_public_assay(frozen_bundle, csv_path, expected_freeze_sha256, source_manifest, *,
                          runtime_root=None, raw_csv_path=None, raw_source_manifest=None,
                          raw_variant_column="mutant", raw_numbering="full_reference_1based"):
    """Reconcile a complete frozen prediction cohort with possibly missing labels.

    Full-cohort primary metrics are null if any valid unique measurement is absent.
    Secondary complete-case metrics keep the original K and are computed only when
    the explicitly reported measured subset has at least K members. Every duplicate
    expected candidate is excluded in full; no aggregation or favorable copy is
    selected. No candidate is removed from or added to the prediction freeze.
    """
    # This must happen before source-path resolution or any assay-file read.
    bundle = validate_frozen_predictions(frozen_bundle, expected_freeze_sha256)
    protocol = bundle["cohort"]["protocol"]
    if (protocol["reference_id"] != REFERENCE_ID or protocol["reference_sha256"] != REFERENCE_SHA256
            or hashlib.sha256(PUBLIC_REFERENCE_SEQUENCE.encode("ascii")).hexdigest() != REFERENCE_SHA256):
        raise ValueError("Public assay requires the exact registered reference identity")
    ids = bundle["cohort"]["candidate_ids"]
    if any(_variant_reason(cid) is not None for cid in ids):
        raise ValueError("Frozen candidate WT/full-reference correspondence is invalid")
    fixture = bundle["source_mode"] == "synthetic_fixture"
    source_rows, manifest = _load_csv(csv_path, source_manifest, fixture, runtime_root, outcome_required=True)
    expected = set(ids)
    counts = Counter(row["mutant"].strip() for row in source_rows if row["mutant"].strip())
    duplicate_ids = {cid for cid, count in counts.items() if count > 1}
    duplicate_expected = duplicate_ids & expected
    excluded = {reason: 0 for reason in EXCLUSION_REASONS}
    source_outcome_diagnostics = {reason: 0 for reason in ("missing_outcome", "nonnumeric_outcome", "nonfinite_outcome")}
    for row in source_rows:
        outcome_reason, _ = _outcome_value(row["DMS_score"])
        if outcome_reason is not None:
            source_outcome_diagnostics[outcome_reason] += 1
    observed = {}
    for row in source_rows:
        cid = row["mutant"].strip()
        reason = _variant_reason(cid)
        if reason is None and "mutated_sequence" in row:
            normalized = "".join(row["mutated_sequence"].split()).upper()
            if normalized != _mutated_sequence(cid):
                reason = "mutated_sequence_mismatch"
        if reason is None and cid not in expected:
            reason = "outside_frozen_cohort"
        if reason is None and cid in duplicate_expected:
            reason = "duplicate_measurement"
        value = None
        if reason is None:
            reason, value = _outcome_value(row["DMS_score"])
        if reason is not None:
            excluded[reason] += 1
        else:
            observed[cid] = value
    missing = sorted(expected - set(observed))
    predicted = {row["candidate_id"]: row["score"] for row in bundle["records"]}
    n, m, k = len(ids), len(observed), protocol["top_k"]
    primary = {"status": "complete_labeled_cohort" if not missing else "incomplete_measurements",
               "cohort_size": n, "top_k": k, "spearman": None, "recall_at_k": None}
    if not missing:
        primary.update(_metrics(predicted, observed, ids, k))
    secondary = {"status": "conditional_on_valid_unique_measurements" if m >= k else "insufficient_measurements_for_frozen_k",
                 "cohort_size": m, "missing_from_original_cohort": n-m, "top_k": k,
                 "spearman": None, "recall_at_k": None,
                 "random_expected_recall_at_k": k/m if m >= k else None}
    if m >= k:
        secondary.update(_metrics(predicted, observed, sorted(observed), k))
    raw_comparison = {"status": "not_supplied", "missingness_cause": "not_inferred"}
    if (raw_csv_path is None) != (raw_source_manifest is None):
        raise ValueError("Optional raw CSV and its explicit source manifest must be supplied together")
    if raw_csv_path is not None:
        raw_rows, raw_manifest = _load_csv(raw_csv_path, raw_source_manifest, fixture, runtime_root,
                                           outcome_required=False, variant_column=raw_variant_column)
        raw_rows, raw_mapping = _normalize_raw_ids(raw_rows, raw_variant_column, raw_numbering)
        raw_manifest = {**raw_manifest, "import_mapping": raw_mapping}
        raw_ids, curated_ids = _valid_source_ids(raw_rows), _valid_source_ids(source_rows)
        raw_counts = Counter(row["mutant"].strip() for row in raw_rows if row["mutant"].strip())
        raw_comparison = {"status": "compared_variant_ids_only", "raw_source_manifest": raw_manifest,
                          "raw_row_count": len(raw_rows), "curated_row_count": len(source_rows),
                          "raw_unique_valid_variant_count": len(raw_ids), "curated_unique_valid_variant_count": len(curated_ids),
                          "raw_duplicate_row_count": sum(count-1 for count in raw_counts.values() if count > 1),
                          "raw_only_variant_count": len(raw_ids-curated_ids), "curated_only_variant_count": len(curated_ids-raw_ids),
                          "shared_variant_count": len(raw_ids & curated_ids), "missingness_cause": "not_inferred",
                          "outcome_transformation_verified": False}
    report = {
        "format": "biopilot-public-assay-evaluation-v1", "evaluator_only": True,
        "source_mode": "synthetic_fixture" if fixture else "retrospective_public_evaluation",
        "scientific_evidence": not fixture, "prediction_freeze_sha256": expected_freeze_sha256,
        "cohort_sha256": bundle["cohort"]["cohort_sha256"], "source_manifest": manifest,
        "original_cohort_size": n, "predictions_present": len(predicted), "prediction_completeness": len(predicted)/n,
        "source_row_count": len(source_rows),
        "outside_cohort_row_count": sum(row["mutant"].strip() not in expected for row in source_rows),
        "matched_label_count": m, "missing_label_count": len(missing), "missing_label_ids": missing,
        "absent_from_source_candidate_count": len(expected-set(counts)),
        "duplicate_row_count": sum(count-1 for count in counts.values() if count > 1),
        "duplicate_candidate_count": len(duplicate_ids), "duplicate_expected_candidate_ids": sorted(duplicate_expected),
        "nonfinite_row_count": source_outcome_diagnostics["nonfinite_outcome"],
        "source_outcome_diagnostics": source_outcome_diagnostics, "row_exclusion_counts": excluded,
        "row_exclusions_are_mutually_exclusive": True,
        "frozen_top_k": k, "primary_metrics": primary, "secondary_complete_case": secondary,
        "random_full_cohort_expected_recall_at_k": k/n,
        "random_reference_kind": "mathematical_expectation_not_measured_trial",
        "raw_comparison": raw_comparison, "calibrated_T50": False, "wt_improvement": None,
        "raw_T50_units_verified": False,
        # Complete-case interval only: it inherits every caveat of the complete-case metric.
        "site_bootstrap_interval": site_bootstrap_spearman(predicted, observed, sorted(observed)) if observed else None,
        "limitations": ["Outcome values are used as recorded source scores without a Celsius interpretation",
                        "Missing measurements do not imply inactivity or zero outcome",
                        "Complete-case metrics are conditional on measurement availability",
                        "No WT-relative, wet-lab, retained-function or prospective validation",
                        "No site-bootstrap uncertainty interval; a small site subset cannot establish general performance",
                        "Raw/curated outcome transformation and per-assay redistribution terms remain unverified"],
    }
    if m + sum(excluded.values()) != len(source_rows):
        raise ValueError("Assay reconciliation counts do not preserve the source-row denominator")
    report["report_sha256"] = digest(report)
    return report


def write_public_report(report, output_path, *, runtime_root=None):
    """Create a new evaluator-only JSON report outside the product runtime."""
    if (not isinstance(report, dict) or report.get("evaluator_only") is not True
            or report.get("format") != "biopilot-public-assay-evaluation-v1"
            or report.get("report_sha256") != digest({k: v for k, v in report.items() if k != "report_sha256"})):
        raise ValueError("Expected an intact evaluator-only reconciliation report")
    path = _outside_runtime(output_path, runtime_root, must_exist=False)
    with path.open("x", encoding="utf-8") as file:
        json.dump(report, file, indent=2, sort_keys=True, allow_nan=False)
        file.write("\n")
    return path
