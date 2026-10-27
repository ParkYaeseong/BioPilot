"""Isolated offline metrics; not a product tool or a calibrated T50 predictor."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

from evaluation.prepare import assert_evaluator_path, digest, finite, validate_frozen_predictions


def _average_ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + 1 + end) / 2.
        for i in order[start:end]:
            ranks[i] = rank
        start = end
    return ranks


def spearman(scores, outcomes):
    """Pearson correlation of average tie ranks; undefined values stay null."""
    if len(scores) != len(outcomes):
        raise ValueError("Metric vectors must cover the same frozen cohort")
    x, y = [finite(v) for v in scores], [finite(v) for v in outcomes]
    if len(x) < 2:
        return None
    rx, ry = _average_ranks(x), _average_ranks(y)
    mean = (len(x) + 1) / 2.
    dx, dy = [v - mean for v in rx], [v - mean for v in ry]
    variance_x = math.fsum(v * v for v in dx)
    variance_y = math.fsum(v * v for v in dy)
    if variance_x == 0 or variance_y == 0:
        return None
    return math.fsum(a * b for a, b in zip(dx, dy)) / math.sqrt(variance_x * variance_y)


def evaluate_predictions(frozen_predictions, labels, *, expected_freeze_sha256):
    """Join exact complete cohorts only; no WT metric or temperature interpretation.

    Experimental transformations, raw/curated reconciliation and site bootstrap
    intervals are not implemented here. A numeric result is retrospective only.
    """
    bundle = validate_frozen_predictions(frozen_predictions, expected_freeze_sha256)
    if not isinstance(labels, dict) or set(labels) != {"source_mode", "records"}:
        raise ValueError("Expected isolated label records with explicit source mode")
    fixture = bundle["source_mode"] == "synthetic_fixture"
    if labels["source_mode"] != ("synthetic_fixture" if fixture else "imported_snapshot"):
        raise ValueError("Synthetic and real evaluation sources cannot be mixed")
    observed = {}
    if not isinstance(labels["records"], list):
        raise ValueError("Expected label records")
    for row in labels["records"]:
        if not isinstance(row, dict) or set(row) != {"candidate_id", "outcome"}:
            raise ValueError("Labels require exactly candidate_id and outcome")
        cid = row["candidate_id"]
        if not isinstance(cid, str) or cid in observed:
            raise ValueError("Duplicate or invalid label ID")
        observed[cid] = finite(row["outcome"])
    ids = bundle["cohort"]["candidate_ids"]
    if set(observed) != set(ids):
        raise ValueError("Missing or unexpected labels: do not shrink the frozen cohort")
    predicted = {r["candidate_id"]: r["score"] for r in bundle["records"]}
    k = bundle["cohort"]["protocol"]["top_k"]
    predicted_top = sorted(ids, key=lambda cid: (-predicted[cid], cid))[:k]
    observed_top = sorted(ids, key=lambda cid: (-observed[cid], cid))[:k]
    report = {
        "format": "biopilot-evaluation-report-v1", "evaluator_only": True,
        "source_mode": "synthetic_fixture" if fixture else "retrospective_evaluation",
        "scientific_evidence": not fixture,
        "analysis_scope": bundle["cohort"]["protocol"]["analysis_scope"],
        "prediction_freeze_sha256": expected_freeze_sha256, "labels_sha256": digest(labels),
        "cohort_size": len(ids), "predictions_present": len(predicted), "labels_present": len(observed),
        "completeness": 1.0, "spearman": spearman([predicted[cid] for cid in ids], [observed[cid] for cid in ids]),
        "top_k": k, "predicted_top_k": predicted_top, "observed_top_k": observed_top,
        "recall_at_k": len(set(predicted_top) & set(observed_top)) / k,
        "random_expected_recall_at_k": k / len(ids),
        "random_reference_kind": "mathematical_expectation_not_measured_trial",
        "tie_rule": "candidate_id_ascending", "wt_improvement": None, "calibrated_T50": False,
        "site_bootstrap_interval": None,
        "limitations": ["No wet-lab or retained-function validation", "No raw T50 unit or transformation audit",
                        "No site-bootstrap uncertainty interval", "Public benchmark pretraining memorization not excluded"],
    }
    report["report_sha256"] = digest(report)
    return report


def _load_json(path):
    if path.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("Evaluator JSON exceeds the local 5 MiB bound")
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--expected-freeze-sha256", required=True)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runtime-root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        prediction_path = assert_evaluator_path(args.predictions, args.runtime_root)
        # The independent freeze digest is checked before label existence/read.
        bundle = validate_frozen_predictions(_load_json(prediction_path), args.expected_freeze_sha256)
        label_path = assert_evaluator_path(args.labels, args.runtime_root)
        output_path = assert_evaluator_path(args.output, args.runtime_root, must_exist=False)
        if output_path in {prediction_path, label_path}:
            raise ValueError("Evaluator report cannot overwrite input artifacts")
        report = evaluate_predictions(bundle, _load_json(label_path), expected_freeze_sha256=args.expected_freeze_sha256)
        # Exclusive creation protects old reports and source files.
        with output_path.open("x", encoding="utf-8") as file:
            json.dump(report, file, sort_keys=True, indent=2, allow_nan=False)
            file.write("\n")
        print(json.dumps({"status": "evaluated", "evaluator_only": True, "report_sha256": report["report_sha256"],
                          "source_mode": report["source_mode"]}))
        return 0
    except (ValueError, OSError, TypeError) as error:
        # No outcomes, input body or private exception internals are printed.
        message = str(error) if isinstance(error, ValueError) else "Evaluator file operation failed"
        print(message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
