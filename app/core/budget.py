"""Money and approval types for the local, single-user run ledger."""
from __future__ import annotations

from dataclasses import dataclass


class PolicyError(ValueError):
    """A trusted-host operation failed its run policy."""


class OwnershipError(PermissionError):
    """The supplied owner does not own this run."""


class BudgetError(PolicyError):
    """A new job cannot fit the currently approved budget."""


def nonnegative_int(value: int, name: str) -> int:
    if type(value) is not int or value < 0:
        raise PolicyError(f"{name} must be a nonnegative integer")
    return value


@dataclass(frozen=True)
class Approval:
    run_id: str
    plan_digest: str
    budget_version: int


@dataclass(frozen=True)
class Reservation:
    task_id: str
    run_id: str
    job_digest: str
    estimate_micros: int
    status: str
    provider_job_id: str | None
    is_new: bool
