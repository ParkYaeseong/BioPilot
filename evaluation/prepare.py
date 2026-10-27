"""Freeze a label-free cohort and predictions before any evaluator label join."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re


AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
REFERENCE_SHA256 = "8a9ea05c5d2953b5b143b591bea6014aec631be96a4842b274fb3e91ee4907d7"
# A larger checkpoint is not an optional per-row rank override. It can be the
# primary baseline only when its matching policy is explicitly frozen for the
# whole cohort before the independent label join.
CHECKPOINT_POLICIES = {
    "esm2_t12_35M_UR50D": "esm35_masked_v1",
    "esm2_t30_150M_UR50D": "esm150_masked_v1",
    "esm2_t33_650M_UR50D": "esm650_masked_v1",
}
CHECKPOINT_MODEL_KEYS = {
    "esm2_t12_35M_UR50D": "esm35",
    "esm2_t30_150M_UR50D": "esm150",
    "esm2_t33_650M_UR50D": "esm650",
}
PROTOCOL_FIELDS = frozenset({
    "source_mode", "analysis_scope", "reference_id", "reference_sha256", "checkpoint",
    "weights_sha256", "tokenizer_sha256", "sequence_context", "score_kind", "rank_policy",
    "protected_positions", "top_k", "tie_rule", "seed", "site_splits", "prompt_sha256",
    "budget_sha256", "code_sha256",
})
ROW_PROVENANCE = ("reference_id", "reference_sha256", "checkpoint", "weights_sha256", "tokenizer_sha256",
                  "sequence_context", "score_kind")
ROW_FIELDS = frozenset({"candidate_id", "score", "source_mode", "full_position", "wild_type", "mutant",
                        "implementation", "precision", *ROW_PROVENANCE})


def digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Scores and outcomes must be finite numbers")
    return float(value)


def candidate_site(candidate_id):
    if not isinstance(candidate_id, str):
        raise ValueError("Expected full-reference single-substitution candidate ID")
    match = re.fullmatch(r"([ACDEFGHIKLMNPQRSTVWY])([1-9][0-9]*)([ACDEFGHIKLMNPQRSTVWY])", candidate_id)
    if match is None or match[1] == match[3] or not 32 <= int(match[2]) <= 212:
        raise ValueError("Expected eligible full-reference single-substitution candidate ID")
    return int(match[2])


def _ids(values):
    if not isinstance(values, (list, tuple)) or not values or len(values) > 200:
        raise ValueError("Expected a nonempty frozen cohort of at most 200 protected interactive candidates")
    sites = {cid: candidate_site(cid) for cid in values}
    if len(sites) != len(values):
        raise ValueError("Duplicate candidate IDs in frozen cohort")
    return sites


def prepare_cohort(candidate_ids, frozen_protocol):
    """Build a label-free protected-cohort manifest with one split per residue site.

    This minimal interface does not reconcile raw/curated datasets or establish an
    unrestricted published benchmark. Those remain separate scientific tasks.
    """
    sites = _ids(candidate_ids)
    if not isinstance(frozen_protocol, dict) or set(frozen_protocol) != PROTOCOL_FIELDS:
        raise ValueError("Frozen protocol fields must match the label-free allowlist")
    protocol = deepcopy(frozen_protocol)
    mode = protocol["source_mode"]
    if mode not in {"synthetic_fixture", "live", "replay"}:
        raise ValueError("Unknown prediction source mode")
    if protocol["analysis_scope"] not in {"development_only", "retrospective_fixed_no_tuning"}:
        raise ValueError("Unsupported prespecified evaluation scope")
    for key in ("reference_sha256", "weights_sha256", "tokenizer_sha256", "prompt_sha256", "budget_sha256", "code_sha256"):
        if not isinstance(protocol[key], str) or re.fullmatch(r"[0-9a-f]{64}", protocol[key]) is None:
            raise ValueError(f"Expected exact {key}")
    if (protocol["reference_id"] != "ESTA_BACSU_Nutschel_2020"
            or protocol["checkpoint"] not in CHECKPOINT_POLICIES
            or protocol["sequence_context"] != "full_212"
            or protocol["score_kind"] != "masked_marginal_log_likelihood_ratio"
            or protocol["rank_policy"] != CHECKPOINT_POLICIES.get(protocol["checkpoint"])
            or protocol["tie_rule"] != "candidate_id_ascending"):
        raise ValueError("Protocol must explicitly freeze one matching common checkpoint and rank policy")
    if mode != "synthetic_fixture" and protocol["reference_sha256"] != REFERENCE_SHA256:
        raise ValueError("Real evaluation requires the registered reference sequence hash")
    protected = protocol["protected_positions"]
    if (not isinstance(protected, list) or len(set(protected)) != len(protected)
            or any(type(p) is not int or not 32 <= p <= 212 for p in protected)
            or not {108, 164, 187} <= set(protected)
            or set(sites.values()) & set(protected)):
        raise ValueError("Interactive cohort must preserve the registered protected positions")
    k = protocol["top_k"]
    if type(k) is not int or not 1 <= k <= len(sites):
        raise ValueError("Pre-register top_k within the complete frozen cohort")
    if type(protocol["seed"]) is not int:
        raise ValueError("Freeze an integer seed")
    splits = protocol["site_splits"]
    if (not isinstance(splits, dict) or set(splits) != {str(p) for p in sites.values()}
            or any(value not in {"development", "heldout", "retrospective"} for value in splits.values())):
        raise ValueError("Each residue site needs exactly one frozen split assignment")
    if protocol["analysis_scope"] == "development_only" and any(value != "development" for value in splits.values()):
        raise ValueError("Development-only evaluation cannot join held-out outcomes")
    if protocol["analysis_scope"] == "retrospective_fixed_no_tuning" and any(value != "retrospective" for value in splits.values()):
        raise ValueError("Retrospective fixed evaluation must be named and frozen as such")
    protocol["protected_positions"] = sorted(protected)
    manifest = {"format": "biopilot-cohort-v1", "reference_numbering": "full_reference_1based",
                "candidate_ids": sorted(sites), "candidate_sites": dict(sorted(sites.items())), "protocol": protocol}
    manifest["cohort_sha256"] = digest(manifest)
    return manifest


def _checked_cohort(manifest):
    if not isinstance(manifest, dict):
        raise ValueError("Expected frozen cohort manifest")
    try:
        rebuilt = prepare_cohort(manifest["candidate_ids"], manifest["protocol"])
    except (KeyError, TypeError) as error:
        raise ValueError("Invalid frozen cohort manifest") from error
    if rebuilt != manifest:
        raise ValueError("Cohort checksum or frozen metadata mismatch")
    return rebuilt


def freeze_predictions(records, cohort_manifest):
    """Freeze complete predictions, without labels, before the evaluator is launched."""
    cohort = _checked_cohort(cohort_manifest)
    protocol = cohort["protocol"]
    if not isinstance(records, (list, tuple)):
        raise ValueError("Expected prediction records")
    rows = []
    seen = set()
    for record in records:
        if not isinstance(record, dict) or not set(record) <= ROW_FIELDS:
            raise ValueError("Prediction records cannot carry outcomes or unreviewed fields")
        cid = record.get("candidate_id")
        site = candidate_site(cid)
        if cid in seen:
            raise ValueError("Duplicate prediction ID")
        seen.add(cid)
        if record.get("source_mode") != protocol["source_mode"]:
            raise ValueError("Prediction source mode must match the frozen protocol")
        for key in ROW_PROVENANCE:
            if key in record and record[key] != protocol[key]:
                raise ValueError("Prediction scoring provenance differs from frozen protocol")
            if protocol["source_mode"] != "synthetic_fixture" and key not in record:
                raise ValueError("Real predictions require full scoring provenance")
        if "full_position" in record and record["full_position"] != site:
            raise ValueError("Prediction position differs from its candidate ID")
        if ("wild_type" in record and record["wild_type"] != cid[0]) or ("mutant" in record and record["mutant"] != cid[-1]):
            raise ValueError("Prediction residue differs from its candidate ID")
        rows.append({"candidate_id": cid, "score": finite(record.get("score")), "source_mode": record["source_mode"]})
    expected = set(cohort["candidate_ids"])
    if seen != expected:
        raise ValueError("Missing or unexpected predictions: disclose failure; do not shrink the cohort")
    bundle = {"format": "biopilot-frozen-predictions-v1", "source_mode": protocol["source_mode"],
              "cohort": cohort, "records": sorted(rows, key=lambda row: row["candidate_id"])}
    bundle["freeze_sha256"] = digest(bundle)
    return bundle


def freeze_score_artifact(artifact, cohort_manifest):
    """Freeze an unchanged ESMEngine artifact without hand-editing score rows.

    Verify the original score hash, full common checkpoint/context/pin identity,
    source mode and exact cohort before projecting only ``ROW_FIELDS``. Additional
    checkpoint metadata stays in the original artifact, linked by its hash; it is
    not copied into evaluator prediction records. No product module is imported.
    """
    expected_fields = {"rows", "provenance", "source_mode", "cached_positions_1based",
                       "phenotype_calibrated", "score_units", "rank_policy", "limitations", "artifact_sha256"}
    if not isinstance(artifact, dict) or set(artifact) != expected_fields:
        raise ValueError("Expected a complete numeric ESM score artifact")
    source_hash = artifact["artifact_sha256"]
    if (not isinstance(source_hash, str) or re.fullmatch(r"[0-9a-f]{64}", source_hash) is None
            or digest({k: v for k, v in artifact.items() if k != "artifact_sha256"}) != source_hash):
        raise ValueError("Original score artifact checksum mismatch")
    cohort = _checked_cohort(cohort_manifest)
    protocol = cohort["protocol"]
    source_mode = artifact["source_mode"]
    common = artifact["provenance"]
    model_key = CHECKPOINT_MODEL_KEYS[protocol["checkpoint"]]
    required_common = {*ROW_PROVENANCE, "model_key", "rank_policy", "source_mode", "implementation", "precision"}
    if (not isinstance(common, dict) or not required_common <= set(common)
            or artifact["phenotype_calibrated"] is not False or artifact["score_units"] != "dimensionless"
            or source_mode != protocol["source_mode"] or artifact["rank_policy"] != protocol["rank_policy"]
            or common["model_key"] != model_key or common["rank_policy"] != protocol["rank_policy"]
            or any(common[key] != protocol[key] for key in ROW_PROVENANCE)
            or not isinstance(common["implementation"], str) or not common["implementation"]
            or not isinstance(common["precision"], str) or not common["precision"]):
        raise ValueError("Score artifact differs from the frozen common checkpoint, pins, source or context")
    # Engine provenance describes the original backend execution. An entirely
    # replayed artifact retains source_mode=live in that provenance, while its
    # artifact and every row are explicitly replay. Mixed live/replay rows are
    # refused so evaluation timing/source scope cannot silently change.
    backend_mode = "synthetic_fixture" if source_mode == "synthetic_fixture" else "live"
    if common["source_mode"] != backend_mode:
        raise ValueError("Score artifact backend source mode is inconsistent")
    rows = artifact["rows"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 200:
        raise ValueError("Expected the complete bounded ESM candidate rows")
    base_fields = {"candidate_id", "full_position", "wild_type", "mutant", "score"}
    projected = []
    positions = set()
    for row in rows:
        if (not isinstance(row, dict) or set(row) != set(common) | base_fields
                or row["source_mode"] != source_mode
                or any(key not in row or row[key] != value for key, value in common.items() if key != "source_mode")):
            raise ValueError("Mixed checkpoint, pin, source or provenance rows cannot be frozen")
        positions.add(candidate_site(row["candidate_id"]))
        projected.append({key: row[key] for key in ROW_FIELDS if key in row})
    cached = artifact["cached_positions_1based"]
    if (not isinstance(cached, list) or any(type(p) is not int for p in cached)
            or len(set(cached)) != len(cached) or not set(cached) <= positions
            or (source_mode == "live" and cached)
            or (source_mode == "replay" and set(cached) != positions)):
        raise ValueError("Score artifact cache/source metadata is inconsistent")
    bundle = freeze_predictions(projected, cohort)
    bundle["source_artifact_sha256"] = source_hash
    bundle["freeze_sha256"] = digest({key: value for key, value in bundle.items() if key != "freeze_sha256"})
    return bundle


def validate_frozen_predictions(bundle, expected_sha256):
    """Verify against a separately recorded digest, before opening any label file."""
    if not isinstance(bundle, dict) or not isinstance(expected_sha256, str):
        raise ValueError("Expected frozen predictions and independent checksum")
    allowed = {"format", "source_mode", "cohort", "records", "freeze_sha256", "source_artifact_sha256"}
    if not set(bundle) <= allowed:
        raise ValueError("Frozen predictions cannot carry outcomes or unreviewed metadata")
    if "source_artifact_sha256" in bundle and (not isinstance(bundle["source_artifact_sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", bundle["source_artifact_sha256"]) is None):
        raise ValueError("Invalid source score artifact checksum")
    checksum = bundle.get("freeze_sha256")
    if not isinstance(checksum, str) or checksum != expected_sha256:
        raise ValueError("Prediction freeze checksum differs from the recorded hash")
    payload = {key: value for key, value in bundle.items() if key != "freeze_sha256"}
    if digest(payload) != checksum:
        raise ValueError("Prediction freeze checksum mismatch")
    try:
        cohort = _checked_cohort(bundle["cohort"])
        if bundle.get("format") != "biopilot-frozen-predictions-v1" or bundle.get("source_mode") != cohort["protocol"]["source_mode"]:
            raise ValueError("Invalid prediction freeze format")
        rows = bundle["records"]
        if not isinstance(rows, list) or {r["candidate_id"] for r in rows} != set(cohort["candidate_ids"]) or len(rows) != len(cohort["candidate_ids"]):
            raise ValueError("Prediction freeze does not cover the exact cohort")
        for row in rows:
            if (set(row) != {"candidate_id", "score", "source_mode"}
                    or row["source_mode"] != bundle["source_mode"]):
                raise ValueError("Invalid frozen prediction record")
            finite(row["score"])
    except (KeyError, TypeError) as error:
        raise ValueError("Invalid prediction freeze fields") from error
    return deepcopy(bundle)


def assert_evaluator_path(path, runtime_root, *, must_exist=True):
    """Reject lexical and resolved paths into the supplied product runtime boundary."""
    raw = Path(path).absolute()
    boundary = Path(runtime_root).resolve(strict=True)
    if not boundary.is_dir():
        raise ValueError("Runtime boundary must be an existing directory")
    # Check lexical components as well: an alias inside .runtime must not be used
    # even when it points outside that directory.
    if ".runtime" in {part.casefold() for part in raw.parts} or raw == boundary or boundary in raw.parents:
        raise ValueError("Evaluator input/output cannot be inside the product runtime")
    resolved = raw.resolve(strict=must_exist)
    if ".runtime" in {part.casefold() for part in resolved.parts} or resolved == boundary or boundary in resolved.parents:
        raise ValueError("Evaluator symlink/path resolves into the product runtime")
    if must_exist and not resolved.is_file():
        raise ValueError("Evaluator input must be a file")
    if not must_exist and not resolved.parent.is_dir():
        raise ValueError("Evaluator output parent directory must already exist")
    return resolved
