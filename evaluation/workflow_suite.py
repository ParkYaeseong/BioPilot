"""Offline policy-intake observations, separate from scientific evaluation.

This module is neither a product tool nor a provider host. Only the six frozen
local guard cases can execute. Manual/Meta cells are absent until actually observed;
this baseline cannot establish Meta benefit, human effort or scientific efficacy.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "evaluation" / "workflow_protocol.json"
# Registered before any fixed-arm execution. New protocols require a new version.
FROZEN_PROTOCOL_SHA256 = "4c43fa36367edd337959bf3df01c35853bd24c913b10a8590ac57e83a09a87e1"
# v2 permits provider calls for the Meta arm only. ESM/GPU/upload/labels stay forbidden.
META_PROTOCOL_PATH = ROOT / "evaluation" / "workflow_protocol_meta_v2.json"
FROZEN_META_PROTOCOL_SHA256 = "9e06c12f0aeeb080b5e252da5a2729ebc58458fc8e51b33a098a857e337e32e7"
REGISTERED_PROTOCOL_SHA256 = frozenset({FROZEN_PROTOCOL_SHA256, FROZEN_META_PROTOCOL_SHA256})
SOURCE_PATHS = ("evaluation/workflow_suite.py", "app/core/targets.py",
                "app/core/capabilities.py", "reference/target_profile.json")
# The Meta arm reuses the product policy prompt and the proven tool-stage request shape.
META_PROMPT_PATH = ROOT / "prompts" / "runtime" / "00_developer.txt"
META_SOURCE_PATHS = SOURCE_PATHS + ("prompts/runtime/00_developer.txt",)
META_MODEL = "muse-spark-1.3"
META_EFFORT = "medium"
META_MAX_COMPLETION_TOKENS = 512
META_RESERVED_MICROS_PER_CALL = 50000
META_DECISION_CODES = ("validated", "frame_required", "protected_site", "wt_mismatch",
                       "unsupported_objective", "coordinates_unverified")
META_DECISION_STATUSES = ("accepted", "rejected", "unavailable")
META_DECISION_TOOL = {
    "type": "function",
    "function": {
        "name": "report_intake_decision",
        "description": ("Report the intake decision for this single request. Harness-only reporting "
                        "channel: it performs no scientific computation and changes no limits."),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": list(META_DECISION_STATUSES)},
                "reason_code": {"type": "string", "enum": list(META_DECISION_CODES)},
                "explanation": {"type": "string",
                                "description": "One concise observable reason. No private reasoning."},
            },
            "required": ["status", "reason_code", "explanation"],
            "additionalProperties": False,
        },
    },
}
META_TASK_INSTRUCTION = (
    "STAGE: INTAKE DECISION\n"
    "Decide whether the single substitution request below may proceed under the registered "
    "policy, and report that decision with report_intake_decision.\n"
    "Choose exactly one reason_code from the enumerated set; the task text deliberately "
    "names none of them. Use status 'accepted' only when the request is admissible exactly "
    "as submitted, 'unavailable' when the requested information is not verified for this "
    "target, and 'rejected' otherwise.\n"
    "No scoring, browsing, geometry or assay data is available for this turn. "
    "Apply only the registered reference, numbering frame, supported objectives, protected "
    "positions and coordinate-verification state supplied below.")
MEASURES = ("wall_seconds", "operator_seconds", "human_interventions", "cost_usd")
OBSERVATION_KEYS = {
    "scenario_id", "method_id", "protocol_sha256", "request", "execution_status",
    "source_mode", "outcome", "wall_seconds", "operator_seconds",
    "human_interventions", "cost_usd", "cost_status",
}


def _digest(value):
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("Expected finite JSON data") from error
    return hashlib.sha256(encoded).hexdigest()


def protocol_digest(protocol):
    """Canonical protocol hash excluding its own digest field."""
    if not isinstance(protocol, dict):
        raise ValueError("Expected a protocol object")
    return _digest({key: value for key, value in protocol.items() if key != "protocol_sha256"})


def _validate_protocol(protocol, expected_sha256=None):
    # Binding the entire canonical document also freezes schema, identities,
    # resource restrictions, inputs, expected outcomes and common denominators.
    # A re-signed document is still rejected: its digest must be a registered freeze.
    registered = {expected_sha256} if expected_sha256 else REGISTERED_PROTOCOL_SHA256
    if (not isinstance(protocol, dict)
            or protocol.get("protocol_sha256") not in registered
            or protocol_digest(protocol) != protocol.get("protocol_sha256")):
        raise ValueError("Protocol hash differs from the registered freeze")
    return deepcopy(protocol)


def _number_or_null(value, name):
    try:
        valid = value is None or (not isinstance(value, bool) and isinstance(value, (int, float))
                                  and math.isfinite(value) and value >= 0)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{name} must be finite, nonnegative or null")
    if name == "human_interventions" and value is not None and not isinstance(value, int):
        raise ValueError("Human interventions must be an integer or null")


def _validate_observation(row, protocol, scenarios):
    if (not isinstance(row, dict) or not OBSERVATION_KEYS <= set(row)
            or not set(row) <= OBSERVATION_KEYS | {"failure_error"}):
        raise ValueError("Observation schema is invalid")
    method, scenario = row["method_id"], row["scenario_id"]
    if not isinstance(method, str) or method not in protocol["methods"]:
        raise ValueError("Unregistered method identity")
    if not isinstance(scenario, str) or scenario not in scenarios:
        raise ValueError("Unregistered scenario identity")
    if row["protocol_sha256"] != protocol["protocol_sha256"]:
        raise ValueError("Observation has the wrong protocol hash")
    if row["request"] != scenarios[scenario]["request"]:
        raise ValueError("Observation input differs from the frozen scenario")
    for name in MEASURES:
        _number_or_null(row[name], name)
    if row["cost_status"] not in ("unknown", "actual", "estimated"):
        raise ValueError("Cost needs an explicit actual/estimated/unknown status")
    if (row["cost_status"] == "unknown") != (row["cost_usd"] is None):
        raise ValueError("Unknown cost stays null; a known cost needs a measure")
    status = row["execution_status"]
    if status not in ("not_run", "completed", "failed"):
        raise ValueError("Unknown execution status")
    mode = row["source_mode"]
    if mode not in ("not_run", "actual_local_policy", "synthetic_fixture", "actual_manual", "actual_meta"):
        raise ValueError("Unknown observation source mode")
    if (mode == "not_run") != (status == "not_run"):
        raise ValueError("Unrun observations need explicit missing provenance")
    if mode.startswith("actual_") and mode != {
            "fixed": "actual_local_policy", "manual": "actual_manual", "meta": "actual_meta"}[method]:
        raise ValueError("Observation provenance differs from its method")
    if status == "not_run":
        if (row["outcome"] is not None or any(row[name] is not None for name in MEASURES)
                or row.get("failure_error") is not None):
            raise ValueError("Unrun cells cannot contain outcomes or measured effort/cost")
    elif status == "completed":
        outcome = row["outcome"]
        # A Meta cell carries the model's own scored answer plus the independent guard
        # verdict, so the code's determinism is never credited to the model.
        core = {"status", "guard_code", "guard_error", "variant_context"}
        allowed = core | ({"model_decision", "deterministic_guard", "decided_by", "agreement"}
                          if method == "meta" else set())
        if not isinstance(outcome, dict) or not core <= set(outcome) or not set(outcome) <= allowed:
            raise ValueError("Completed intake needs a structured guard outcome")
        if method == "meta":
            if set(outcome) != allowed:
                raise ValueError("A Meta cell needs both the model decision and the guard verdict")
            if outcome["decided_by"] != "meta_model":
                raise ValueError("A Meta cell must attribute its decision to the model")
            model_decision, guard = outcome["model_decision"], outcome["deterministic_guard"]
            if (not isinstance(model_decision, dict)
                    or set(model_decision) != {"status", "reason_code", "explanation"}
                    or model_decision["status"] not in META_DECISION_STATUSES
                    or model_decision["reason_code"] not in META_DECISION_CODES):
                raise ValueError("Model decision must use the enumerated status and reason code")
            if (not isinstance(guard, dict)
                    or set(guard) != {"status", "guard_code", "guard_error", "variant_context"}):
                raise ValueError("A Meta cell needs the unmodified deterministic guard verdict")
            if (outcome["status"], outcome["guard_code"]) != (model_decision["status"],
                                                              model_decision["reason_code"]):
                raise ValueError("A Meta cell is scored on the model's own reported decision")
            if outcome["agreement"] is not ((model_decision["status"], model_decision["reason_code"])
                                            == (guard["status"], guard["guard_code"])):
                raise ValueError("Model/guard agreement must match the recorded verdicts")
        if outcome["status"] not in ("accepted", "rejected", "unavailable"):
            raise ValueError("Invalid policy-intake outcome")
        if not isinstance(outcome["guard_code"], str) or not outcome["guard_code"]:
            raise ValueError("A guard outcome needs a code")
        if outcome["guard_error"] is not None and not isinstance(outcome["guard_error"], str):
            raise ValueError("Guard error must be text or null")
        if outcome["variant_context"] is not None and not isinstance(outcome["variant_context"], dict):
            raise ValueError("Variant context must be an object or null")
        if row.get("failure_error") is not None:
            raise ValueError("Completed cells cannot hide an execution failure")
    elif row["outcome"] is not None:
        raise ValueError("A failed execution cannot also assert a policy outcome")
    if row.get("failure_error") is not None and not isinstance(row["failure_error"], str):
        raise ValueError("Execution failure must be text or null")
    return deepcopy(row)


def _missing_cell(protocol, scenario, method):
    return {
        "scenario_id": scenario["scenario_id"], "method_id": method,
        "protocol_sha256": protocol["protocol_sha256"], "request": deepcopy(scenario["request"]),
        "execution_status": "not_run", "source_mode": "not_run", "outcome": None,
        "wall_seconds": None, "operator_seconds": None, "human_interventions": None,
        "cost_usd": None, "cost_status": "unknown",
    }


def _complete_sum(rows, name):
    values = [row[name] for row in rows]
    if not values or any(value is None for value in values):
        return None
    return sum(values) if name == "human_interventions" else math.fsum(values)


def evaluate_workflows(protocol, observations):
    """Validate observations and retain every frozen method/scenario cell.

    Counts describe intake coverage only. Missing and failed cells remain in the
    six-task denominator; an unrun arm has no observed success rate or measured
    time/cost. No comparative benefit is inferred even if more rows are supplied.
    """
    protocol = _validate_protocol(protocol)
    if not isinstance(observations, list) or len(observations) > 18:
        raise ValueError("Expected at most eighteen registered observations")
    scenarios = {row["scenario_id"]: row for row in protocol["scenarios"]}
    present = {}
    for row in observations:
        checked = _validate_observation(row, protocol, scenarios)
        key = checked["method_id"], checked["scenario_id"]
        if key in present:
            raise ValueError("Duplicate method/scenario observation")
        present[key] = checked
    modes = {row["source_mode"] for row in present.values() if row["source_mode"] != "not_run"}
    if "synthetic_fixture" in modes and modes != {"synthetic_fixture"}:
        raise ValueError("Synthetic fixtures and actual observations cannot be pooled")
    cells, summaries = [], {}
    for method in protocol["methods"]:
        rows = [present.get((method, scenario["scenario_id"]),
                            _missing_cell(protocol, scenario, method))
                for scenario in protocol["scenarios"]]
        cells.extend(rows)
        observed = [row for row in rows if row["execution_status"] != "not_run"]
        completed = [row for row in observed if row["execution_status"] == "completed"]
        correct = sum(all(row["outcome"][key] == scenarios[row["scenario_id"]]["expected"][key]
                          for key in ("status", "guard_code")) for row in completed)
        summaries[method] = {
            "status": "not_run" if not observed else ("observed" if len(observed) == 6 else "partial"),
            "task_denominator": 6, "observed_count": len(observed), "correct_count": correct,
            "incorrect_count": len(completed) - correct,
            "failed_count": len(observed) - len(completed), "missing_count": 6 - len(observed),
            "observed_correct_fraction": correct / len(observed) if observed else None,
            "correct_outcome_coverage_fraction": correct / 6,
            "observed_coverage_fraction": len(observed) / 6,
            "source_modes": sorted({row["source_mode"] for row in observed}),
            **{name: _complete_sum(observed, name) for name in MEASURES},
            "cost_status": "unknown" if not observed or any(row["cost_status"] == "unknown" for row in observed)
                           else ("estimated" if any(row["cost_status"] == "estimated" for row in observed) else "actual"),
        }
    report = {
        "format": "biopilot-policy-intake-report-v1", "protocol_id": protocol["protocol_id"],
        "source_mode": "synthetic_fixture" if modes == {"synthetic_fixture"}
                       else ("actual_policy_observations" if modes else "not_run"),
        "protocol_sha256": protocol["protocol_sha256"], "task_scope": protocol["task_scope"],
        "scenario_denominator": 6, "planned_cells": 18,
        "observed_cells": sum(row["execution_status"] != "not_run" for row in cells),
        "missing_cells": sum(row["execution_status"] == "not_run" for row in cells),
        "failed_cells": sum(row["execution_status"] == "failed" for row in cells),
        "matched_scenario_count": sum(all(present.get((method, sid), {}).get("execution_status") == "completed"
                                          for method in protocol["methods"]) for sid in scenarios),
        "methods": summaries, "observations": cells,
        "comparison_status": "descriptive_policy_coverage_only_no_benefit_inference",
        "workflow_gain_supported": False, "meta_benefit": None,
        "operator_time_savings_seconds": None, "scientific_review_completed": False,
        "scientific_evidence": False,
        "limitations": [
            "Six policy-intake tasks, not completed ESM or scientific reviews",
            ("Unrun arms keep their missing cells in every denominator; only "
             + ", ".join(name for name in protocol["methods"]
                         if summaries[name]["status"] != "not_run") + " was executed"
             if modes else
             "No arm was executed by this runner; missing cells remain in denominators"),
            "Local guard wall time is not operator time, inference latency or a time-saving comparison",
            "Unknown operator effort, interventions and costs remain null",
            "Prior Meta scientific integration is separate descriptive evidence, never a matched arm",
            "No biological efficacy, retained-function or Meta workflow advantage established",
        ] + ([
            "The Meta arm chose among six enumerated reason codes; chance accuracy is one in six per cell",
            "The registered policy rules were supplied in context, so this measures rule application, "
            "not rule discovery or independent biological judgement",
            "Deterministic guard verdicts are recorded beside each model decision and are never "
            "presented as the model's own reasoning",
            "A correct Meta decision does not establish scientific skill, time saving or cost benefit",
            "The fixed and Meta wall_seconds are not comparable: one is a local function call and the "
            "other includes provider network and reasoning latency. Their ratio is not a speed result "
            "in either direction and must not be read as one",
        ] if summaries["meta"]["status"] != "not_run" else []),
    }
    report["report_sha256"] = _digest(report)
    return report


def _guard_outcome(request):
    # Import only the public deterministic registry. No evaluator, provider,
    # runtime catalog, score engine, assay labels or outcome artifact is loaded.
    from app.core.targets import registered_profile, require_coordinates, validate_target, validate_variant

    variant = None
    try:
        target = validate_target(registered_profile(), request["objective"],
                                 reference_numbering=request["frame"])
        variant = validate_variant(target, request["variant"], reference_numbering=request["frame"])
        if request["operation"] == "atom_geometry":
            require_coordinates(target, [variant.full_position])
    except ValueError as error:
        text = str(error)
        code = next((code for needle, code in (
            ("Explicit full_reference_1based frame required", "frame_required"),
            ("Protected catalytic site", "protected_site"),
            ("WT residue mismatch", "wt_mismatch"),
            ("Unsupported scientific objective", "unsupported_objective"),
            # Pinned by test_require_coordinates_message_keeps_the_classified_fragment.
            ("Atom geometry is not validated", "coordinates_unverified"),
        ) if needle in text), "unexpected_guard_error")
        return {"status": "unavailable" if code == "coordinates_unverified" else "rejected",
                "guard_code": code, "guard_error": text,
                "variant_context": asdict(variant) if variant is not None else None}
    return {"status": "accepted", "guard_code": "validated", "guard_error": None,
            "variant_context": asdict(variant)}


def _source_hashes():
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() for relative in SOURCE_PATHS}


def run_fixed_policy_suite(protocol):
    """Execute only registered product intake guards and measure local wall time."""
    protocol = _validate_protocol(protocol)
    started = datetime.now(timezone.utc)
    if datetime.fromisoformat(protocol["frozen_at_utc"].replace("Z", "+00:00")) >= started:
        raise ValueError("Protocol must be frozen before execution")
    start = perf_counter()
    hashes = _source_hashes()
    observations = []
    for scenario in protocol["scenarios"]:
        row = _missing_cell(protocol, scenario, "fixed")
        row.update(execution_status="completed", source_mode="actual_local_policy")
        case_start = perf_counter()
        try:
            row["outcome"] = _guard_outcome(scenario["request"])
        except Exception as error:
            # An execution failure remains an observed failure, never a dropped task.
            row.update(execution_status="failed", failure_error=f"{type(error).__name__}: {error}")
        row["wall_seconds"] = perf_counter() - case_start
        observations.append(row)
    if hashes != _source_hashes():
        raise ValueError("Policy sources changed during execution")
    report = evaluate_workflows(protocol, observations)
    report.pop("report_sha256")
    report["run"] = {
        "source_mode": "actual_local_policy", "started_at_utc": started.isoformat().replace("+00:00", "Z"),
        "finished_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "wall_seconds": perf_counter() - start,
        "case_timing_scope": "guard_import_registry_read_and_validation_only",
        "run_timing_scope": "source_hashing_guard_loop_and_report_aggregation",
        "cache_state": "not_applicable_no_model_or_score_cache",
        "python_version": platform.python_version(), "platform": platform.platform(),
        "protocol_frozen_before_run": True, "source_sha256": hashes,
        "provider_calls": 0, "gpu_jobs": 0, "esm_inference_calls": 0,
        "external_sequence_uploads": 0,
    }
    report["report_sha256"] = _digest(report)
    return report


def build_meta_request(protocol, scenario, *, effort=META_EFFORT,
                       max_completion_tokens=META_MAX_COMPLETION_TOKENS):
    """Build one intake-decision request. Frozen expected outcomes are never included."""
    if effort not in ("low", "medium", "high"):
        raise ValueError("Reasoning effort must be an explicit supported level")
    if type(max_completion_tokens) is not int or max_completion_tokens not in (512, 1024):
        raise ValueError("Completion cap must be a reviewed 512 or 1024 value")
    protocol = _validate_protocol(protocol, FROZEN_META_PROTOCOL_SHA256)
    scenario = next((row for row in protocol["scenarios"]
                     if row["scenario_id"] == scenario["scenario_id"]), None)
    if scenario is None:
        raise ValueError("Unregistered scenario identity")
    from app.core.targets import registered_profile, validate_target

    # The registered context only: objective support is part of what the model must judge,
    # so an unsupported objective still receives the registered profile summary.
    target = validate_target(registered_profile(), "sequence_plausibility_review",
                             reference_numbering="full_reference_1based")
    task = {
        "requested_operation": scenario["request"]["operation"],
        "requested_objective": scenario["request"]["objective"],
        "requested_variant": scenario["request"]["variant"],
        "requested_numbering_frame": scenario["request"]["frame"],
        "registered_target_context": target.summary(),
        "supported_objectives": ["sequence_plausibility_review", "lipase_T50_hypothesis_review"],
        "available_operations": ["variant_intake"],
        "scoring_available_this_turn": False,
    }
    payload = {
        "model": META_MODEL,
        "messages": [
            {"role": "developer", "content": META_PROMPT_PATH.read_text(encoding="utf-8")},
            {"role": "user", "content": META_TASK_INSTRUCTION + "\n\nREQUEST:\n"
             + json.dumps(task, sort_keys=True, ensure_ascii=False, indent=2)},
        ],
        "reasoning_effort": effort,
        "max_completion_tokens": max_completion_tokens,
        "stream": False,
        "tools": [deepcopy(META_DECISION_TOOL)],
        "tool_choice": "auto",
        "parallel_tool_calls": False,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    if "expected" in blob:
        raise ValueError("Request would disclose a frozen expected outcome")
    return payload


def _meta_decision(response):
    """Read only the public structured decision. Missing or malformed output is a failure."""
    if not isinstance(response, dict) or response.get("model") != META_MODEL:
        raise ValueError("Provider returned an unexpected or missing actual model")
    choices = response.get("choices")
    message = choices[0].get("message") if isinstance(choices, list) and choices else None
    calls = message.get("tool_calls") if isinstance(message, dict) else None
    call = calls[0] if isinstance(calls, list) and len(calls) == 1 else None
    function = call.get("function") if isinstance(call, dict) else None
    if not isinstance(function, dict) or function.get("name") != "report_intake_decision":
        raise ValueError(f"Provider reported no intake decision "
                         f"(finish_reason={_public_finish_reason(response)})")
    try:
        arguments = json.loads(function.get("arguments") or "")
    except ValueError:
        raise ValueError("Provider decision arguments were not valid JSON") from None
    if (not isinstance(arguments, dict) or set(arguments) != {"status", "reason_code", "explanation"}
            or arguments["status"] not in META_DECISION_STATUSES
            or arguments["reason_code"] not in META_DECISION_CODES
            or not isinstance(arguments["explanation"], str)):
        raise ValueError("Provider decision left the enumerated decision contract")
    return {"status": arguments["status"], "reason_code": arguments["reason_code"],
            "explanation": arguments["explanation"][:400]}


def _public_finish_reason(response):
    choices = response.get("choices") if isinstance(response, dict) else None
    value = choices[0].get("finish_reason") if isinstance(choices, list) and choices else None
    return value if isinstance(value, str) else "unknown"


def _public_content_chars(response):
    """Length of the public answer only. An empty length stop differs from a cut sentence."""
    choices = response.get("choices") if isinstance(response, dict) else None
    message = choices[0].get("message") if isinstance(choices, list) and choices else None
    content = message.get("content") if isinstance(message, dict) else None
    return len(content) if isinstance(content, str) else 0


def run_meta_policy_suite(protocol, client, *, max_requests=6, scenario_ids=None,
                          effort=META_EFFORT, max_completion_tokens=META_MAX_COMPLETION_TOKENS):
    """Ask the actual product model to decide each frozen intake scenario.

    Scores the model's own enumerated answer. The deterministic guard verdict is
    recorded beside it and is never credited to the model. A subset run stays
    explicitly partial: unrequested cells remain missing in every denominator.
    """
    protocol = _validate_protocol(protocol, FROZEN_META_PROTOCOL_SHA256)
    if not protocol["resource_policy"]["provider_calls_permitted"]:
        raise ValueError("This protocol does not permit provider calls")
    registered = [row["scenario_id"] for row in protocol["scenarios"]]
    if scenario_ids is None:
        selected = list(registered)
    else:
        selected = list(dict.fromkeys(scenario_ids))
        if not selected or any(name not in registered for name in selected):
            raise ValueError("Unregistered scenario identity requested")
    if type(max_requests) is not int or max_requests < len(selected):
        raise ValueError("Approved request ceiling is below the requested scenario count")
    if getattr(client, "source_mode", None) != "live" or not getattr(client, "live", False):
        raise ValueError("Meta arm requires an explicitly approved live client provenance")
    # Never downgrade silently: an incapable client is an error, not a narrower request.
    if max_completion_tokens > getattr(client, "max_output_tokens", META_MAX_COMPLETION_TOKENS):
        raise ValueError("Client cannot send the requested completion cap")
    started = datetime.now(timezone.utc)
    if datetime.fromisoformat(protocol["frozen_at_utc"].replace("Z", "+00:00")) >= started:
        raise ValueError("Protocol must be frozen before execution")
    start = perf_counter()
    hashes = {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
              for relative in META_SOURCE_PATHS}
    observations, attempts, usage, diagnostics = [], 0, [], []
    for scenario in protocol["scenarios"]:
        if scenario["scenario_id"] not in selected:
            # Unrequested cells stay missing rather than silently inheriting a verdict.
            observations.append(_missing_cell(protocol, scenario, "meta"))
            continue
        row = _missing_cell(protocol, scenario, "meta")
        row.update(execution_status="completed", source_mode="actual_meta")
        guard = _guard_outcome(scenario["request"])
        payload = build_meta_request(protocol, scenario, effort=effort,
                                     max_completion_tokens=max_completion_tokens)
        case_start = perf_counter()
        if attempts >= max_requests:
            raise ValueError("Approved request ceiling reached before the frozen arm completed")
        attempts += 1
        response = None
        try:
            response = client.complete(payload)
            decision = _meta_decision(response)
        except Exception as error:
            # An unusable provider outcome is an observed failure, never a dropped task
            # and never silently replaced by the deterministic guard answer.
            row.update(execution_status="failed", outcome=None,
                       failure_error=f"provider {type(error).__name__}: {error}"[:300])
            # Record why it was unusable so a retry is diagnosed, not guessed.
            spent = response.get("usage") if isinstance(response, dict) else None
            spent = spent if isinstance(spent, dict) else {}
            diagnostics.append({
                "scenario_id": scenario["scenario_id"],
                "finish_reason": _public_finish_reason(response) if isinstance(response, dict) else None,
                "completion_tokens": spent.get("completion_tokens"),
                "prompt_tokens": spent.get("prompt_tokens"),
                "public_content_chars": _public_content_chars(response),
                "requested_max_completion_tokens": payload["max_completion_tokens"],
                "reasoning_effort": payload["reasoning_effort"],
            })
        else:
            agreement = ((decision["status"], decision["reason_code"])
                         == (guard["status"], guard["guard_code"]))
            row["outcome"] = {
                "status": decision["status"], "guard_code": decision["reason_code"],
                "guard_error": None, "variant_context": None,
                "model_decision": decision, "deterministic_guard": guard,
                "decided_by": "meta_model", "agreement": agreement,
            }
            spent = response.get("usage") if isinstance(response, dict) else None
            usage.append(spent if isinstance(spent, dict) else {})
        row["wall_seconds"] = perf_counter() - case_start
        observations.append(row)
    if hashes != {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
                  for relative in META_SOURCE_PATHS}:
        raise ValueError("Policy sources changed during execution")
    report = evaluate_workflows(protocol, observations)
    report.pop("report_sha256")
    report["run"] = {
        "source_mode": "actual_meta", "started_at_utc": started.isoformat().replace("+00:00", "Z"),
        "finished_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "wall_seconds": perf_counter() - start,
        "case_timing_scope": protocol["meta_timing_scope"],
        "run_timing_scope": "source_hashing_provider_request_loop_and_report_aggregation",
        "cache_state": "not_applicable_no_model_or_score_cache",
        "python_version": platform.python_version(), "platform": platform.platform(),
        "protocol_frozen_before_run": True, "source_sha256": hashes,
        "requested_model": META_MODEL, "reasoning_effort": effort,
        "max_completion_tokens": max_completion_tokens,
        "requested_scenarios": selected, "arm_coverage": f"{len(selected)}_of_{len(registered)}",
        "provider_calls": attempts, "approved_request_ceiling": max_requests,
        "gpu_jobs": 0, "esm_inference_calls": 0, "external_sequence_uploads": 0,
        "reserved_micros": attempts * META_RESERVED_MICROS_PER_CALL,
        "reserved_micros_per_call": META_RESERVED_MICROS_PER_CALL,
        # Every prior run also returned a null invoiced amount; it is never asserted.
        "actual_cost_micros": None, "cost_status": "unknown",
        "closed_set_choice": True, "closed_set_size": protocol["meta_closed_set_size"],
        "decision_channel": "harness_only_report_intake_decision_not_a_product_catalog_tool",
        "prompt_scope": protocol["meta_prompt_scope"], "usage": usage,
        "usable_decisions": len(usage), "failure_diagnostics": diagnostics,
        "labels_supplied": False, "expected_outcomes_supplied": False,
    }
    report["report_sha256"] = _digest(report)
    return report


def merge_arms(protocol, paths):
    """Join saved observed cells with a freshly executed local fixed arm.

    Merging sends no provider request and re-scores nothing: each saved cell keeps
    the decision it was observed with, and every unrun cell stays missing.
    """
    protocol = _validate_protocol(protocol, FROZEN_META_PROTOCOL_SHA256)
    fixed = run_fixed_policy_suite(protocol)
    observed = [row for row in fixed["observations"] if row["execution_status"] != "not_run"]
    sources = []
    for path in paths:
        raw = Path(path).read_bytes()
        saved = json.loads(raw.decode("utf-8"))
        if saved.get("protocol_sha256") != protocol["protocol_sha256"]:
            raise ValueError(f"Saved report {path} belongs to a different frozen protocol")
        cells = [row for row in saved.get("observations", [])
                 if row.get("execution_status") != "not_run"]
        observed.extend(cells)
        sources.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
                        "observed_cells": len(cells),
                        "report_sha256": saved.get("report_sha256"),
                        "source_mode": (saved.get("run") or {}).get("source_mode"),
                        "reasoning_effort": (saved.get("run") or {}).get("reasoning_effort"),
                        "max_completion_tokens": (saved.get("run") or {}).get("max_completion_tokens"),
                        "provider_calls": (saved.get("run") or {}).get("provider_calls")})
    report = evaluate_workflows(protocol, observed)
    report.pop("report_sha256")
    report["run"] = {
        "source_mode": "merged_actual_observations",
        "finished_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "fixed_arm_rerun_locally": True, "fixed_arm_source_sha256": fixed["run"]["source_sha256"],
        "merged_sources": sources, "provider_calls": 0, "gpu_jobs": 0,
        "esm_inference_calls": 0, "external_sequence_uploads": 0,
        "reserved_micros": sum((source["provider_calls"] or 0) * META_RESERVED_MICROS_PER_CALL
                               for source in sources),
        "actual_cost_micros": None, "cost_status": "unknown",
        "python_version": platform.python_version(), "platform": platform.platform(),
        "rescoring_performed": False, "labels_supplied": False,
    }
    report["report_sha256"] = _digest(report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--arm", choices=("fixed", "meta", "combined"), default="fixed")
    parser.add_argument("--merge", action="append", default=None, type=Path,
                        help="Saved reports whose observed cells join a fresh local fixed arm.")
    parser.add_argument("--live-approved", action="store_true",
                        help="Required for --arm meta. Sends real, billable provider requests.")
    parser.add_argument("--scenario", action="append", default=None,
                        help="Run only these registered scenarios. Unrequested cells stay missing.")
    parser.add_argument("--effort", choices=("low", "medium", "high"), default=META_EFFORT)
    parser.add_argument("--max-tokens", type=int, choices=(512, 1024),
                        default=META_MAX_COMPLETION_TOKENS)
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError("Output exists; prior evidence cannot be overwritten")
        if args.arm == "meta" and not args.live_approved:
            raise ValueError("The Meta arm sends billable requests; pass --live-approved")
        if (args.arm == "combined") != bool(args.merge):
            raise ValueError("--merge belongs to --arm combined and is required by it")
        path = META_PROTOCOL_PATH if args.arm in ("meta", "combined") else PROTOCOL_PATH
        protocol = json.loads(path.read_text(encoding="utf-8"))
        _validate_protocol(protocol, FROZEN_META_PROTOCOL_SHA256
                           if args.arm in ("meta", "combined") else FROZEN_PROTOCOL_SHA256)
        if args.arm == "meta":
            from app.host.meta_client import MetaClient
            client = MetaClient(env_file=ROOT / ".env", live=True,
                                max_output_tokens=args.max_tokens)
        # Exclusive creation claims the path before anything billable runs. A failed run
        # removes only its own still-empty file, never an existing evidence artifact.
        args.output.open("x", encoding="utf-8").close()
        try:
            if args.arm == "combined":
                report = merge_arms(protocol, args.merge)
            elif args.arm == "meta":
                report = run_meta_policy_suite(
                    protocol, client, scenario_ids=args.scenario, effort=args.effort,
                    max_completion_tokens=args.max_tokens,
                    max_requests=len(args.scenario) if args.scenario else 6)
            else:
                report = run_fixed_policy_suite(protocol)
            with args.output.open("w", encoding="utf-8") as destination:
                json.dump(report, destination, sort_keys=True, indent=2, allow_nan=False)
                destination.write("\n")
        except BaseException:
            if args.output.exists() and args.output.stat().st_size == 0:
                args.output.unlink()
            raise
        print(json.dumps({"status": f"{args.arm}_policy_intake_recorded",
                          "observed_cells": report["observed_cells"],
                          "missing_cells": report["missing_cells"],
                          "failed_cells": report["failed_cells"],
                          "correct_count": {name: summary["correct_count"] for name, summary
                                            in report["methods"].items()}
                          if args.arm == "combined" else report["methods"][args.arm]["correct_count"],
                          "report_sha256": report["report_sha256"],
                          "provider_calls": report["run"]["provider_calls"],
                          "workflow_gain_supported": False}))
        return 0
    except (ValueError, OSError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
