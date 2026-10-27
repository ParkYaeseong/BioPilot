# Current status

## Implementation update — 2026-10-27

The first local product implementation now exists on branch
`implementation/mcp-core-20261027`. The original package was preserved in the
initial local Git commit; no push/publication was performed. The supplied status
below remains a historical package receipt, not the current implementation claim.

- H0: inspected the package, helper provenance and captured rules. Original run:
  68/69 unittest checks passed; validator failed `manifest complete` because local
  additions were not part of the distribution. Local credentials/environments/helper
  files are now pruned from source inventory. Original manifest is preserved at
  `compliance/original_package_manifest.sha256`.
- B0 implemented: `app/core/targets.py`, `capabilities.py`; typed immutable registry,
  explicit full-reference frame, exact hashes, S108/D164/H187 policy, variant/FASTA
  checks, geometry blocked. `tests_app/test_target_gate.py`: 32 passed after 32 RED failures.
- C1 implemented slice: `app/core/runs.py`, `budget.py`; SQLite approval/version,
  atomic reservation/claim, ownership, timeout/unknown-cost and cancellation guards.
  `tests_app/test_run_policy.py`: 20 passed. Not a provider billing guarantee.
- C2 adapter/math implemented; real integration pending. Local-only pinned safetensors
  loading, masked marginals/cache/common-model ranking tested with synthetic logits.
  No weights downloaded and no real ESM score exists yet.
- C3 transport implemented slice: `app/mcp_server.py`, `tool_executor.py`,
  `runtime_bundle.py`; actual spawned stdio MCP validation/status calls succeeded.
  SDK 1.25.0 negotiated protocol 2025-11-25. Evaluator/secret/docs/tests excluded from
  the provisioned workspace. OS ACL isolation and native Muse Code are unverified.
- C4 controlled validation smoke code exists: `app/host/`, `app/cli.py`,
  `app/core/artifacts.py`. Mocked loop tests distinguish fixtures and live results.
  The first live attempt has a partial receipt under `.runtime/live_validation_20261027`;
  no actual provider/model response was verified by that attempt; no retry occurred.
  User-reported earlier Meta smoke (OK, 120 tokens) remains separate evidence.
- B1 evaluator code is separate in `evaluation/`; tests are synthetic only. Real raw/
  curated reconciliation, held-out evaluation and biological baseline remain unperformed.
- C5 UI, E1 real workflow comparison and S1 recording/submission remain unimplemented.

User steering is implemented at the local code/test level: shared provider interface,
LocalESMProvider, ModalESMProvider and explicit unconfigured RunPodESMProvider; default
ESM_BACKEND=modal, explicit 35M/150M/650M model policies, shared MCP score_positions,
durable submit/poll/status, worker source allowlist and guarded deployment definition.
Actual model/GPU integration remains pending. This does not approve GPU allocation,
paid remote work, model downloads, deployment or RunPod creation.
No live ESM/GPU/Atlas, raw label lookup, external sequence upload, publication,
GitHub push or contest submission has occurred. Test counts above are stage receipts.
The final combined receipt is in validation/implementation_final_tests.txt.
Final command: `.venv/Scripts/python.exe -m pytest tests tests_app -q -rs --basetemp .cache/pytest_final_installed_sdk`.
Observed result: **339 passed, 2 skipped, 2 warnings, 12 subtests passed** (59.59 s).
Both skips are Windows symlink privilege tests. Complete changed-file inventory and
integration modes are in validation/implementation_summary.json; Korean launch
instructions are in docs/IMPLEMENTATION_KO.md.

Modal SDK 1.6.2 was installed into .venv only (requirements-modal.txt), and required
public API signatures were checked without authentication or cloud operations.
Live compatibility and execution remain false. See validation/modal_sdk_offline.json.
The SDK emits two Python 3.16 deprecation warnings on Python 3.14; current tests pass.
The .env secret values were compared locally against the source inventory without
printing them; no matching source files were found. The real .env remains ignored.

The sequence_review host now reserves its final request before tools and validates
saved numerical artifacts before deterministic ranking. Pending inference stops with
a partial report. Only mocked provider responses/fixtures tested this full review loop.
The evaluator can freeze an ESM artifact directly without manual row renumbering.
Independent review fixes cover queued-task resume, source-mode consistency, configured
model pins/positions and conservative 900-second remote reservations. Windows UTF-8
source reading and source-manifest inventory were also repaired with failing tests.

Next permission-dependent action: review exact model download, existing volume,
T4/L4 choice, 900-second conservative ceiling and approved cost, then separately
authorize one remote integration. No such action has been authorized or performed.
UI remains omitted while the real biological baseline/claim scope is unvalidated.

## Supplied package status (preserved)

Package revision v3 is prepared for implementation. It is not a running application.
The preserved scientific guards and new offline catalog/rubric/recording helpers are tested separately
from any product integration. See VALIDATION.md for actual test receipts and exact scope.

No Meta API, MCP transport, ESM GPU, Atlas live service, UI rendering, biological evaluation, video,
publication or submission was executed by this package revision.

Next implementation task: read-only environment/repo inspection and H0/B0 under the user's actual
permissions, then follow the v3 plan. Do not restart earlier completed user work if a real repo exists.
