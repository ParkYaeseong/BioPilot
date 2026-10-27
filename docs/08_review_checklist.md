# 08. Release review checklist

## Scientific integrity

- [ ] Exact reference/checkpoint/scoring-context hashes are pinned and actual outputs exist.
- [ ] Full/mature/PDB coordinate frames remain distinct; protected-site checks are enforced server-side.
- [ ] ESM preference, T50 endpoint, Tm, activity, pLDDT and experimental results are not conflated.
- [ ] No unsupported efficacy, calibration, WT-improvement or independent-validation claim.
- [ ] Evaluation cohort, missing outputs, costs and negative results are disclosed.

## MCP and Meta evidence

- [ ] Installed host/SDK/protocol and actual provider/model are recorded.
- [ ] MCP discovery and a real tool/result call are observed; conversion-only tests are not called integration tests.
- [ ] Server rechecks every call; unavailable tools are hidden and forbidden direct calls also fail.
- [ ] No outcome tool/resource or label-bearing host filesystem is available to the agent.
- [ ] No hidden non-Meta fallback; cached model responses are identified.
- [ ] Async tasks, idempotency, changing budgets and cancellation do not duplicate billed work.

## Product and demonstration

- [ ] A valid task produces a reviewable shortlist with real numerical provenance.
- [ ] A numbering/constraint error shows a meaningful correction path, not a fabricated success.
- [ ] A budget/service failure yields a truthful partial report with unknowns.
- [ ] UI and host share records; rerendering does not launch new computation.
- [ ] Video is actually around/within the official three-minute constraint, audible and readable.
- [ ] English delivery is understandable; Korean notes are not accidentally shown as missing narration.
- [ ] Replay, imported snapshots and fixtures are visibly different.

## Submission and rights

- [ ] Current rules/eligibility and pre-event-work interpretation are resolved and documented.
- [ ] Originality ledger distinguishes new code, earlier preparation and dependencies.
- [ ] Public repo, video and judge access work outside the author's session.
- [ ] Third-party code/weight/data terms and required attribution are recorded separately.
- [ ] Secrets, account identifiers, institution-owned assets and evaluator mounts are excluded.
- [ ] Submit only with explicit user authorization; do not treat checklist files as a submission receipt.
