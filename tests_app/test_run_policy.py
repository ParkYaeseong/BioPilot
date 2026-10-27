"""Behavioral C1 tests: no network, credentials, or experimental labels."""
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.core.budget import BudgetError, OwnershipError, PolicyError
from app.core.runs import RunService


def run_input(limit=100, requests=2):
    return {"reference_id": "ESTA_BACSU_Nutschel_2020", "reference_numbering": "full_reference_1based",
            "requested_budget": {"usd_micros": limit, "max_meta_requests": requests}}


@pytest.fixture
def ledger(tmp_path):
    service = RunService(tmp_path / "runs.sqlite")
    rid = service.create(run_input(), "alice")
    return service, rid


def approve(service, rid):
    run = service.get(rid, "alice")
    return service.approve(rid, run["plan_digest"], run["budget_version"], "alice")


def test_cross_owner_cannot_read_or_approve(ledger):
    service, rid = ledger
    run = service.get(rid, "alice")
    with pytest.raises(OwnershipError):
        service.get(rid, "mallory")
    with pytest.raises(OwnershipError):
        service.approve(rid, run["plan_digest"], 1, "mallory")


def test_wrong_plan_and_budget_version_cannot_approve(ledger):
    service, rid = ledger
    run = service.get(rid, "alice")
    with pytest.raises(PolicyError):
        service.approve(rid, "0" * 64, 1, "alice")
    with pytest.raises(PolicyError):
        service.approve(rid, run["plan_digest"], 2, "alice")


def test_caller_mutation_does_not_change_plan(ledger):
    service, rid = ledger
    first = service.get(rid, "alice")
    first["input"]["requested_budget"]["usd_micros"] = 999999
    assert service.get(rid, "alice")["input"] == run_input()


def test_no_dispatch_without_approval(ledger):
    service, rid = ledger
    with pytest.raises(PolicyError):
        service.reserve(rid, "job-one", 10, "alice")


def test_duplicate_job_reuses_task_and_only_one_claim(ledger):
    service, rid = ledger
    approve(service, rid)
    first = service.reserve(rid, "job-one", 60, "alice")
    second = service.reserve(rid, "job-one", 60, "alice")
    assert first.task_id == second.task_id
    assert first.is_new and not second.is_new
    assert service.claim(rid, first.task_id, "alice") is True
    assert service.claim(rid, first.task_id, "alice") is False
    assert service.get(rid, "alice")["committed_micros"] == 60
    with pytest.raises(PolicyError):
        service.reserve(rid, "job-one", 1, "alice")


def test_restart_preserves_unknown_outcome_without_redispatch(ledger):
    service, rid = ledger
    approve(service, rid)
    task = service.reserve(rid, "job-one", 60, "alice")
    assert service.claim(rid, task.task_id, "alice")
    service.attach_provider_job(rid, task.task_id, "alice", "provider-42")
    service.mark_unknown(rid, task.task_id, "alice")
    restarted = RunService(service.db_path)
    again = restarted.reserve(rid, "job-one", 60, "alice")
    assert again.task_id == task.task_id
    assert again.status == "UNKNOWN"
    assert again.provider_job_id == "provider-42"
    assert not restarted.claim(rid, task.task_id, "alice")
    view = restarted.get(rid, "alice")
    assert view["committed_micros"] == 60
    assert view["actual_cost_micros"] is None
    assert view["cost_status"] == "unknown"


def test_lower_limit_blocks_future_work_and_keeps_inflight(ledger):
    service, rid = ledger
    approve(service, rid)
    task = service.reserve(rid, "job-one", 60, "alice")
    service.claim(rid, task.task_id, "alice")
    service.set_budget(rid, "alice", 30)
    run = service.get(rid, "alice")
    assert run["budget_conflict"] is True
    assert run["committed_micros"] == 60
    assert run["budget_version"] == 2
    assert run["cancellation_requested"] is True
    with pytest.raises(PolicyError):
        service.reserve(rid, "job-two", 0, "alice")
    with pytest.raises(BudgetError):
        approve(service, rid)


def test_new_budget_requires_fresh_approval(ledger):
    service, rid = ledger
    old = approve(service, rid)
    service.set_budget(rid, "alice", 200)
    with pytest.raises(PolicyError):
        service.reserve(rid, "job-one", 1, "alice")
    with pytest.raises(PolicyError):
        service.approve(rid, old.plan_digest, old.budget_version, "alice")
    approve(service, rid)
    assert service.reserve(rid, "job-one", 101, "alice").is_new


def test_concurrent_reservations_never_oversubscribe(ledger):
    service, rid = ledger
    approve(service, rid)
    def reserve(digest):
        try:
            return service.reserve(rid, digest, 60, "alice")
        except BudgetError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, ["a", "b"]))
    assert sum(item is not None for item in results) == 1
    assert service.get(rid, "alice")["committed_micros"] == 60


def test_unknown_actual_is_not_released_as_zero(ledger):
    service, rid = ledger
    approve(service, rid)
    task = service.reserve(rid, "a", 60, "alice")
    service.claim(rid, task.task_id, "alice")
    service.settle(rid, task.task_id, "alice", actual_micros=None)
    assert service.get(rid, "alice")["committed_micros"] == 60
    assert service.get(rid, "alice")["actual_cost_micros"] is None
    with pytest.raises(BudgetError):
        service.reserve(rid, "b", 50, "alice")


def test_settle_actual_cost_and_late_overrun(ledger):
    service, rid = ledger
    approve(service, rid)
    task = service.reserve(rid, "a", 60, "alice")
    service.claim(rid, task.task_id, "alice")
    service.settle(rid, task.task_id, "alice", actual_micros=120)
    view = service.get(rid, "alice")
    assert view["committed_micros"] == 120
    assert view["actual_cost_micros"] == 120
    assert view["cost_status"] == "actual"
    assert view["budget_conflict"] is True
    with pytest.raises(BudgetError):
        service.reserve(rid, "b", 0, "alice")


def test_request_ceiling_is_not_a_money_estimate(ledger):
    service, rid = ledger
    approve(service, rid)
    for i in range(2):
        task = service.reserve(rid, f"meta-{i}", 0, "alice", kind="meta")
        assert service.claim(rid, task.task_id, "alice")
        service.settle(rid, task.task_id, "alice", actual_micros=0)
    with pytest.raises(BudgetError):
        service.reserve(rid, "meta-2", 0, "alice", kind="meta")


@pytest.mark.parametrize("value", [-1, True, 1.5])
def test_invalid_money_never_reserved(ledger, value):
    service, rid = ledger
    approve(service, rid)
    with pytest.raises(PolicyError):
        service.reserve(rid, "job-one", value, "alice")


def test_foreign_task_and_cancel_are_rejected(ledger):
    service, rid = ledger
    other = service.create(run_input(), "alice")
    approve(service, rid)
    task = service.reserve(rid, "one", 10, "alice")
    with pytest.raises(PolicyError):
        service.claim(other, task.task_id, "alice")
    with pytest.raises(OwnershipError):
        service.claim(rid, task.task_id, "mallory")
    service.cancel(rid, "alice")
    assert not service.claim(rid, task.task_id, "alice")
    with pytest.raises(PolicyError):
        service.reserve(rid, "two", 1, "alice")


def test_lower_request_ceiling_blocks_already_queued_future_dispatches(ledger):
    service, rid = ledger
    approve(service, rid)
    first = service.reserve(rid, "meta-one", 0, "alice", kind="meta")
    service.reserve(rid, "meta-two", 0, "alice", kind="meta")
    service.set_budget(rid, "alice", 100, max_meta_requests=1)
    assert service.get(rid, "alice")["budget_conflict"] is True
    with pytest.raises(BudgetError):
        approve(service, rid)
    with pytest.raises(PolicyError):
        service.claim(rid, first.task_id, "alice")


def test_unknown_running_task_blocks_concurrent_dispatch(ledger):
    service, rid = ledger
    approve(service, rid)
    first = service.reserve(rid, "one", 10, "alice")
    second = service.reserve(rid, "two", 10, "alice")
    assert service.claim(rid, first.task_id, "alice")
    service.mark_unknown(rid, first.task_id, "alice")
    assert not service.claim(rid, second.task_id, "alice")
    service.settle(rid, first.task_id, "alice", actual_micros=10)
    assert service.claim(rid, second.task_id, "alice")


def test_provider_identity_cannot_be_replaced(ledger):
    service, rid = ledger
    approve(service, rid)
    task = service.reserve(rid, "one", 10, "alice")
    service.claim(rid, task.task_id, "alice")
    service.attach_provider_job(rid, task.task_id, "alice", "provider-1")
    with pytest.raises(PolicyError):
        service.attach_provider_job(rid, task.task_id, "alice", "provider-2")


def test_events_and_tasks_are_owner_bound(ledger):
    service, rid = ledger
    with pytest.raises(OwnershipError):
        service.events(rid, "mallory")
    assert service.events(rid, "alice")[0]["kind"] == "created"
    approve(service, rid)
    task = service.reserve(rid, "one", 10, "alice")
    with pytest.raises(OwnershipError):
        service.mark_unknown(rid, task.task_id, "mallory")
