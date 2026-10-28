"""Behavioral policy-intake tests; no assay labels or scientific inference."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from evaluation import workflow_suite as suite


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "evaluation" / "workflow_protocol.json"


@pytest.fixture
def protocol():
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def test_protocol_hash_is_canonical_and_tampering_blocks_execution(protocol):
    unsigned = {key: value for key, value in protocol.items() if key != "protocol_sha256"}
    expected = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":"),
                                        ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    assert suite.protocol_digest(protocol) == expected == protocol["protocol_sha256"]
    reordered = dict(reversed(list(protocol.items())))
    assert suite.protocol_digest(reordered) == expected
    changed = deepcopy(protocol)
    changed["scenarios"][0]["request"]["variant"] = "S108A"
    with pytest.raises(ValueError, match="hash|freeze"):
        suite.run_fixed_policy_suite(changed)


def test_missing_manual_and_meta_stay_in_common_denominator(protocol):
    report = suite.evaluate_workflows(protocol, [])
    assert (report["scenario_denominator"], report["planned_cells"],
            report["observed_cells"], report["missing_cells"]) == (6, 18, 0, 18)
    assert len(report["observations"]) == 18
    for method in ("manual", "fixed", "meta"):
        summary = report["methods"][method]
        assert summary["status"] == "not_run"
        assert summary["task_denominator"] == 6
        assert summary["missing_count"] == 6
        assert summary["correct_count"] == 0
        assert summary["observed_correct_fraction"] is None
        for measure in ("wall_seconds", "operator_seconds", "human_interventions", "cost_usd"):
            assert summary[measure] is None
    assert report["matched_scenario_count"] == 0
    assert report["workflow_gain_supported"] is False
    assert report["scientific_review_completed"] is False
    assert report["meta_benefit"] is None
    assert report["operator_time_savings_seconds"] is None


def test_fixed_arm_executes_guards_and_preserves_unknown_measures(protocol):
    report = suite.run_fixed_policy_suite(protocol)
    fixed = [row for row in report["observations"] if row["method_id"] == "fixed"]
    observed = [(row["scenario_id"], row["outcome"]["status"], row["outcome"]["guard_code"])
                for row in fixed]
    assert observed == [
        ("validA32V", "accepted", "validated"),
        ("matureframeA1V", "rejected", "frame_required"),
        ("protectedS108A", "rejected", "protected_site"),
        ("WTmismatchG32V", "rejected", "wt_mismatch"),
        ("unsupportedactivityobjective", "rejected", "unsupported_objective"),
        ("unavailableatomgeometry", "unavailable", "coordinates_unverified"),
    ]
    assert report["observed_cells"] == 6
    assert report["missing_cells"] == 12
    assert report["methods"]["fixed"]["correct_count"] == 6
    assert report["methods"]["fixed"]["task_denominator"] == 6
    assert report["methods"]["manual"]["status"] == "not_run"
    assert report["methods"]["meta"]["status"] == "not_run"
    assert report["workflow_gain_supported"] is False
    assert report["scientific_evidence"] is False
    assert report["protocol_sha256"] == protocol["protocol_sha256"]
    assert report["run"]["protocol_frozen_before_run"] is True
    assert report["run"]["started_at_utc"] > protocol["frozen_at_utc"]
    assert report["run"]["wall_seconds"] > 0
    sources = report["run"]["source_sha256"]
    for relative in ("evaluation/workflow_suite.py", "app/core/targets.py",
                     "app/core/capabilities.py", "reference/target_profile.json"):
        assert sources[relative] == hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    accepted = fixed[0]["outcome"]["variant_context"]
    assert accepted["full_position"] == 32
    assert accepted["mature_position"] == 1
    assert accepted["coordinate_observed"] is None
    assert accepted["pdb_auth_seq_id"] is None
    for row in fixed:
        assert row["execution_status"] == "completed"
        assert row["source_mode"] == "actual_local_policy"
        assert row["wall_seconds"] >= 0
        assert row["operator_seconds"] is None
        assert row["human_interventions"] is None
        assert row["cost_usd"] is None
        assert row["cost_status"] == "unknown"
    for row in fixed[1:]:
        assert row["outcome"]["guard_error"]


def fixed_observation(protocol):
    """A labeled test fixture, not an actual execution record."""
    return {
        "scenario_id": "validA32V", "method_id": "fixed",
        "protocol_sha256": protocol["protocol_sha256"],
        "request": deepcopy(protocol["scenarios"][0]["request"]),
        "execution_status": "completed", "source_mode": "synthetic_fixture",
        "outcome": {"status": "accepted", "guard_code": "validated",
                    "guard_error": None, "variant_context": None},
        "wall_seconds": 0.125, "operator_seconds": None,
        "human_interventions": None, "cost_usd": None, "cost_status": "unknown",
    }


def test_failed_and_incorrect_cells_do_not_shrink_denominator(protocol):
    incorrect = fixed_observation(protocol)
    incorrect["outcome"].update(status="rejected", guard_code="unexpected_guard_error",
                                guard_error="Unexpected local refusal")
    failed = fixed_observation(protocol)
    failed.update(scenario_id="protectedS108A", request=deepcopy(protocol["scenarios"][2]["request"]),
                  execution_status="failed", outcome=None)
    report = suite.evaluate_workflows(protocol, [incorrect, failed])
    summary = report["methods"]["fixed"]
    assert summary["task_denominator"] == 6
    assert summary["observed_count"] == 2
    assert summary["correct_count"] == 0
    assert summary["incorrect_count"] == 1
    assert summary["failed_count"] == 1
    assert summary["missing_count"] == 4
    assert report["planned_cells"] == 18
    assert report["missing_cells"] == 16
    assert report["failed_cells"] == 1


@pytest.mark.parametrize("mutation", [
    {"method_id": "unregistered"}, {"scenario_id": "unregistered"},
    {"protocol_sha256": "0" * 64}, {"extra": "not_schema"},
    {"request": {"variant": "S108A"}},
    {"execution_status": "not_run"},
    {"wall_seconds": float("nan")}, {"wall_seconds": float("inf")},
    {"operator_seconds": -1}, {"operator_seconds": True},
    {"human_interventions": 0.5}, {"human_interventions": -1},
    {"cost_usd": 0}, {"cost_status": "actual"},
])
def test_invalid_or_wrong_identity_observation_rejected(protocol, mutation):
    row = fixed_observation(protocol)
    row.update(mutation)
    with pytest.raises(ValueError):
        suite.evaluate_workflows(protocol, [row])


def test_duplicate_observation_rejected(protocol):
    row = fixed_observation(protocol)
    with pytest.raises(ValueError, match="Duplicate"):
        suite.evaluate_workflows(protocol, [row, deepcopy(row)])


def test_synthetic_and_actual_observations_cannot_be_pooled(protocol):
    fixture = fixed_observation(protocol)
    actual = fixed_observation(protocol)
    actual.update(scenario_id="protectedS108A", source_mode="actual_local_policy",
                  request=deepcopy(protocol["scenarios"][2]["request"]))
    with pytest.raises(ValueError, match="Synthetic|synthetic"):
        suite.evaluate_workflows(protocol, [fixture, actual])


def test_fixture_coverage_retains_missing_and_failed_task_denominator(protocol):
    correct = fixed_observation(protocol)
    failed = fixed_observation(protocol)
    failed.update(scenario_id="protectedS108A", execution_status="failed", outcome=None,
                  request=deepcopy(protocol["scenarios"][2]["request"]))
    report = suite.evaluate_workflows(protocol, [correct, failed])
    assert report["source_mode"] == "synthetic_fixture"
    fixed = report["methods"]["fixed"]
    assert fixed["correct_outcome_coverage_fraction"] == 1 / 6
    assert fixed["observed_correct_fraction"] == 0.5
    assert fixed["missing_count"] == 4


def test_oversized_measure_is_a_validation_error(protocol):
    row = fixed_observation(protocol)
    row["operator_seconds"] = 10 ** 400
    with pytest.raises(ValueError, match="finite"):
        suite.evaluate_workflows(protocol, [row])


@pytest.mark.parametrize("mutation", [
    {"methods": ["fixed", "meta"]}, {"methods": ["manual", "fixed", "fixed"]},
    {"protected_positions": []}, {"scenarios": []}, {"task_scope": "scientific_review"},
])
def test_resigned_but_unregistered_protocol_cannot_expand_scope(protocol, mutation):
    protocol.update(mutation)
    protocol["protocol_sha256"] = suite.protocol_digest(protocol)
    with pytest.raises(ValueError):
        suite.run_fixed_policy_suite(protocol)


def test_cli_refuses_overwrite_before_running(tmp_path):
    output = tmp_path / "prior.json"
    output.write_text("preserved", encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "evaluation.workflow_suite",
                             "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 2
    assert "exists" in result.stderr.lower()
    assert output.read_text(encoding="utf-8") == "preserved"


def test_cli_writes_local_fixed_report_with_no_model(tmp_path):
    output = tmp_path / "new.json"
    result = subprocess.run([sys.executable, "-m", "evaluation.workflow_suite",
                             "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["observed_cells"] == 6
    assert report["missing_cells"] == 12
    assert report["run"]["provider_calls"] == 0
    assert report["run"]["gpu_jobs"] == 0
    assert report["methods"]["meta"]["wall_seconds"] is None


# --- Meta arm (protocol v2, provider calls permitted) ---------------------------


@pytest.fixture
def meta_protocol():
    return json.loads(suite.META_PROTOCOL_PATH.read_text(encoding="utf-8"))


class _FakeClient:
    """Records payloads instead of sending them. Never contacts a provider."""

    source_mode = "live"
    max_output_tokens = 512

    def __init__(self, replies):
        self.replies, self.payloads = list(replies), []
        self.live = True

    def complete(self, payload):
        self.payloads.append(deepcopy(payload))
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def _decision_reply(status, reason_code):
    return {
        "id": "resp_fake", "model": "muse-spark-1.3",
        "choices": [{"finish_reason": "tool_calls", "message": {"content": None, "tool_calls": [
            {"id": "call_1", "type": "function", "function": {
                "name": "report_intake_decision",
                "arguments": json.dumps({"status": status, "reason_code": reason_code,
                                         "explanation": "bounded reason"})}}]}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


def _expected_codes(protocol):
    return [s["expected"]["guard_code"] for s in protocol["scenarios"]]


def _all_correct_replies(protocol):
    """Replies that match each frozen expectation, status and code together."""
    return [_decision_reply(s["expected"]["status"], s["expected"]["guard_code"])
            for s in protocol["scenarios"]]


def test_meta_arm_requires_a_protocol_that_permits_provider_calls(protocol, meta_protocol):
    assert protocol["resource_policy"]["provider_calls_permitted"] is False
    assert meta_protocol["resource_policy"]["provider_calls_permitted"] is True
    client = _FakeClient([_decision_reply("accepted", "validated")] * 6)
    with pytest.raises(ValueError, match="hash|freeze|permit"):
        suite.run_meta_policy_suite(protocol, client)


def test_meta_payload_never_contains_expected_outcomes(meta_protocol):
    # The enumerated vocabulary is inherently present; what must never leak is which
    # member applies to this scenario, so the task text names no reason code at all
    # and the offered closed set is never narrowed toward the frozen answer.
    for scenario in meta_protocol["scenarios"]:
        payload = suite.build_meta_request(meta_protocol, scenario)
        blob = json.dumps(payload, sort_keys=True)
        assert json.dumps(scenario["expected"], sort_keys=True) not in blob
        assert "expected" not in blob
        task = payload["messages"][1]["content"]
        assert not any(code in task for code in suite.META_DECISION_CODES)
        offered = payload["tools"][0]["function"]["parameters"]["properties"]
        assert offered["reason_code"]["enum"] == list(suite.META_DECISION_CODES)
        assert offered["status"]["enum"] == list(suite.META_DECISION_STATUSES)
        assert payload["model"] == "muse-spark-1.3"
        assert payload["stream"] is False
        assert payload["reasoning_effort"] == suite.META_EFFORT
        assert payload["parallel_tool_calls"] is False
        assert scenario["request"]["variant"] in blob


def test_meta_arm_records_model_decision_separately_from_guard_verdict(meta_protocol):
    codes = _expected_codes(meta_protocol)
    client = _FakeClient(_all_correct_replies(meta_protocol))
    report = suite.run_meta_policy_suite(meta_protocol, client)
    assert len(client.payloads) == 6
    meta = report["methods"]["meta"]
    assert meta["status"] == "observed" and meta["observed_count"] == 6
    assert meta["correct_count"] == 6 and meta["source_modes"] == ["actual_meta"]
    for row in [r for r in report["observations"] if r["method_id"] == "meta"]:
        outcome = row["outcome"]
        assert outcome["model_decision"]["reason_code"] in codes
        assert outcome["deterministic_guard"]["guard_code"] in codes
        assert outcome["decided_by"] == "meta_model"
    assert report["workflow_gain_supported"] is False


def test_meta_arm_disagreement_is_recorded_as_incorrect_not_overwritten(meta_protocol):
    # The model answers 'validated' everywhere; the guard still blocks the unsafe cases.
    client = _FakeClient([_decision_reply("accepted", "validated")] * 6)
    report = suite.run_meta_policy_suite(meta_protocol, client)
    meta = report["methods"]["meta"]
    assert meta["correct_count"] == 1 and meta["incorrect_count"] == 5
    blocked = [r for r in report["observations"]
               if r["method_id"] == "meta" and r["scenario_id"] == "protectedS108A"][0]
    assert blocked["outcome"]["model_decision"]["reason_code"] == "validated"
    assert blocked["outcome"]["deterministic_guard"]["guard_code"] == "protected_site"
    assert blocked["outcome"]["agreement"] is False


def test_meta_provider_failure_is_a_failed_cell_not_a_dropped_task(meta_protocol):
    client = _FakeClient([_decision_reply("accepted", "validated"), RuntimeError("provider down")]
                         + [_decision_reply("rejected", "protected_site")] * 4)
    report = suite.run_meta_policy_suite(meta_protocol, client)
    meta = report["methods"]["meta"]
    assert meta["task_denominator"] == 6
    assert meta["failed_count"] == 1
    assert meta["observed_count"] + meta["missing_count"] == 6
    failed = [r for r in report["observations"]
              if r["method_id"] == "meta" and r["execution_status"] == "failed"]
    assert len(failed) == 1 and "provider" in failed[0]["failure_error"].lower()


def test_meta_arm_refuses_a_client_without_live_approval(meta_protocol):
    class _Offline(_FakeClient):
        source_mode = "synthetic_fixture"
    with pytest.raises(ValueError, match="live|provenance|approval"):
        suite.run_meta_policy_suite(meta_protocol, _Offline([]))


def test_meta_arm_enforces_an_explicit_request_ceiling(meta_protocol):
    client = _FakeClient([_decision_reply("accepted", "validated")] * 6)
    with pytest.raises(ValueError, match="ceiling|budget|requests"):
        suite.run_meta_policy_suite(meta_protocol, client, max_requests=3)


def test_meta_report_records_reservation_and_unknown_actual_cost(meta_protocol):
    client = _FakeClient(_all_correct_replies(meta_protocol))
    report = suite.run_meta_policy_suite(meta_protocol, client)
    run = report["run"]
    assert run["provider_calls"] == 6
    assert run["gpu_jobs"] == 0 and run["esm_inference_calls"] == 0
    assert run["reserved_micros"] == 6 * suite.META_RESERVED_MICROS_PER_CALL
    assert run["actual_cost_micros"] is None
    assert report["methods"]["meta"]["cost_status"] == "unknown"
    assert run["closed_set_choice"] is True


def _length_stop_reply():
    """A real failure shape: reasoning consumed the completion budget, no tool call."""
    return {"id": "resp_len", "model": "muse-spark-1.3",
            "choices": [{"finish_reason": "length", "message": {"content": None}}],
            "usage": {"prompt_tokens": 1900, "completion_tokens": 512, "total_tokens": 2412}}


def test_failed_meta_cell_records_provider_finish_reason_and_usage(meta_protocol):
    client = _FakeClient([_length_stop_reply()] * 6)
    report = suite.run_meta_policy_suite(meta_protocol, client)
    meta = report["methods"]["meta"]
    assert meta["failed_count"] == 6 and meta["correct_count"] == 0
    rows = [r for r in report["observations"] if r["method_id"] == "meta"]
    assert all("length" in r["failure_error"] for r in rows)
    diagnostics = report["run"]["failure_diagnostics"]
    assert len(diagnostics) == 6
    assert {d["finish_reason"] for d in diagnostics} == {"length"}
    assert all(d["completion_tokens"] == 512 for d in diagnostics)
    assert all(d["public_content_chars"] == 0 for d in diagnostics)
    assert report["run"]["usable_decisions"] == 0


def test_transport_failure_records_diagnostics_without_a_provider_response(meta_protocol):
    client = _FakeClient([RuntimeError("socket closed")] * 6)
    report = suite.run_meta_policy_suite(meta_protocol, client)
    diagnostics = report["run"]["failure_diagnostics"]
    assert len(diagnostics) == 6
    assert all(d["finish_reason"] is None and d["completion_tokens"] is None for d in diagnostics)
    assert report["methods"]["meta"]["failed_count"] == 6


def test_meta_probe_runs_one_scenario_and_stays_partial(meta_protocol):
    first = meta_protocol["scenarios"][0]
    client = _FakeClient([_decision_reply(first["expected"]["status"],
                                          first["expected"]["guard_code"])])
    report = suite.run_meta_policy_suite(meta_protocol, client, max_requests=1,
                                         scenario_ids=[first["scenario_id"]])
    assert len(client.payloads) == 1
    meta = report["methods"]["meta"]
    assert meta["status"] == "partial"
    assert meta["observed_count"] == 1 and meta["missing_count"] == 5
    assert meta["task_denominator"] == 6
    assert meta["correct_count"] == 1
    assert meta["correct_outcome_coverage_fraction"] == 1 / 6
    assert report["run"]["provider_calls"] == 1
    assert report["run"]["reserved_micros"] == suite.META_RESERVED_MICROS_PER_CALL


def test_meta_request_shape_is_explicit_and_recorded(meta_protocol):
    first = meta_protocol["scenarios"][0]
    payload = suite.build_meta_request(meta_protocol, first, effort="low",
                                       max_completion_tokens=1024)
    assert payload["reasoning_effort"] == "low"
    assert payload["max_completion_tokens"] == 1024
    client = _FakeClient([_decision_reply(first["expected"]["status"],
                                          first["expected"]["guard_code"])])
    client.max_output_tokens = 1024
    report = suite.run_meta_policy_suite(meta_protocol, client, max_requests=1,
                                         scenario_ids=[first["scenario_id"]],
                                         effort="low", max_completion_tokens=1024)
    assert report["run"]["reasoning_effort"] == "low"
    assert report["run"]["max_completion_tokens"] == 1024
    assert client.payloads[0]["max_completion_tokens"] == 1024


def test_meta_runner_refuses_a_cap_the_client_cannot_send(meta_protocol):
    client = _FakeClient([])  # max_output_tokens stays 512
    with pytest.raises(ValueError, match="client|cap|cannot"):
        suite.run_meta_policy_suite(meta_protocol, client, max_completion_tokens=1024)


def test_unregistered_scenario_id_cannot_be_probed(meta_protocol):
    client = _FakeClient([])
    with pytest.raises(ValueError, match="scenario|Unregistered"):
        suite.run_meta_policy_suite(meta_protocol, client, max_requests=1,
                                    scenario_ids=["not_a_registered_scenario"])


def test_separate_probe_and_remainder_runs_merge_into_one_arm(meta_protocol):
    scenarios = meta_protocol["scenarios"]
    probe = suite.run_meta_policy_suite(
        meta_protocol, _FakeClient([_decision_reply(scenarios[0]["expected"]["status"],
                                                    scenarios[0]["expected"]["guard_code"])]),
        max_requests=1, scenario_ids=[scenarios[0]["scenario_id"]])
    rest = suite.run_meta_policy_suite(
        meta_protocol, _FakeClient(_all_correct_replies(meta_protocol)[1:]),
        max_requests=5, scenario_ids=[s["scenario_id"] for s in scenarios[1:]])
    observed = [r for r in probe["observations"] + rest["observations"]
                if r["method_id"] == "meta" and r["execution_status"] != "not_run"]
    assert len(observed) == 6
    merged = suite.evaluate_workflows(meta_protocol, observed)
    assert merged["methods"]["meta"]["status"] == "observed"
    assert merged["methods"]["meta"]["correct_count"] == 6
    assert merged["observed_cells"] == 6


def test_fixed_arm_runs_under_any_registered_protocol_without_provider_calls(meta_protocol):
    # The provider-permitting protocol must not turn the local guard arm into a caller.
    report = suite.run_fixed_policy_suite(meta_protocol)
    assert report["run"]["provider_calls"] == 0
    assert report["protocol_sha256"] == meta_protocol["protocol_sha256"]
    assert report["methods"]["fixed"]["correct_count"] == 6
    assert report["methods"]["meta"]["status"] == "not_run"


def test_fixed_and_meta_arms_merge_under_one_protocol(meta_protocol):
    fixed = suite.run_fixed_policy_suite(meta_protocol)
    meta = suite.run_meta_policy_suite(meta_protocol, _FakeClient(_all_correct_replies(meta_protocol)))
    observed = [r for r in fixed["observations"] + meta["observations"]
                if r["execution_status"] != "not_run"]
    merged = suite.evaluate_workflows(meta_protocol, observed)
    assert merged["observed_cells"] == 12 and merged["missing_cells"] == 6
    assert merged["methods"]["fixed"]["status"] == "observed"
    assert merged["methods"]["meta"]["status"] == "observed"
    assert merged["methods"]["manual"]["status"] == "not_run"
    assert merged["matched_scenario_count"] == 0  # manual never ran, so no scenario is complete
    assert merged["workflow_gain_supported"] is False


def test_cli_merge_combines_saved_meta_reports_with_a_fresh_fixed_arm(tmp_path, meta_protocol):
    saved = tmp_path / "meta_part.json"
    meta = suite.run_meta_policy_suite(meta_protocol, _FakeClient(_all_correct_replies(meta_protocol)))
    saved.write_text(json.dumps(meta, sort_keys=True, indent=2), encoding="utf-8")
    output = tmp_path / "combined.json"
    result = subprocess.run([sys.executable, "-m", "evaluation.workflow_suite", "--arm", "combined",
                             "--merge", str(saved), "--output", str(output)],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["observed_cells"] == 12 and report["missing_cells"] == 6
    assert report["methods"]["fixed"]["status"] == "observed"
    assert report["methods"]["meta"]["status"] == "observed"
    assert report["methods"]["manual"]["status"] == "not_run"
    assert report["run"]["provider_calls"] == 0  # merging re-sends nothing
    assert report["run"]["merged_sources"][0]["path"].endswith("meta_part.json")
    assert report["workflow_gain_supported"] is False


def test_cli_merge_rejects_a_report_from_a_different_protocol(tmp_path, protocol):
    saved = tmp_path / "v1_fixed.json"
    saved.write_text(json.dumps(suite.run_fixed_policy_suite(protocol), sort_keys=True, indent=2),
                     encoding="utf-8")
    output = tmp_path / "combined.json"
    result = subprocess.run([sys.executable, "-m", "evaluation.workflow_suite", "--arm", "combined",
                             "--merge", str(saved), "--output", str(output)],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 2
    assert not output.exists()


def test_executed_meta_arm_warns_that_wall_times_are_not_comparable(meta_protocol):
    """A side-by-side table invites a speed reading; the artifact must refuse it."""
    fixed = suite.run_fixed_policy_suite(meta_protocol)
    meta = suite.run_meta_policy_suite(meta_protocol, _FakeClient(_all_correct_replies(meta_protocol)))
    merged = suite.evaluate_workflows(meta_protocol, [r for r in fixed["observations"] + meta["observations"]
                                                      if r["execution_status"] != "not_run"])
    joined = " ".join(merged["limitations"]).lower()
    assert "not comparable" in joined and "ratio is not a speed result" in joined
    # The unexecuted arm must never acquire a timing number.
    assert merged["methods"]["manual"]["wall_seconds"] is None
    # And the warning only appears once an arm actually ran.
    assert not any("not comparable" in line.lower()
                   for line in suite.run_fixed_policy_suite(json.loads(
                       suite.PROTOCOL_PATH.read_text(encoding="utf-8")))["limitations"])
