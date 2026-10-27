# BioPilot Atlas v3 MCP Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans when available to implement task by task.
> The user's existing environment and instructions take precedence; never require unavailable tools.

**Goal:** Build one reproducible, bounded Meta-driven MCP protein-review workflow and a clear three-minute demo.
**Architecture:** MCP scientific server over deterministic services, one durable worker and one Meta host.
A local Streamlit viewer is optional. The biological evaluator and labels are completely separate.
**Tech Stack:** Python, pinned MCP SDK, ESM/PyTorch in an isolated environment, SQLite, optional Streamlit.
**Spec:** `../specs/2026-10-27-v3-mcp-hackathon-design.md` and `../../01_product_spec.md`.

## Current package status

Only design files, schemas, prompts and offline guard examples exist in this ZIP. All `app/`, `apps/`,
`tests_app/` paths below are **planned implementation files**, not existing working modules.
Existing v2 guards must be integrated explicitly; they are not proof of API/MCP enforcement.

## Global Constraints

- Indie Developer / Push the Frontier; captured weights 30/25/20/25; planned video 180 seconds.
- Supported goal IDs: sequence_plausibility_review and lipase_T50_hypothesis_review.
- full_reference_1based frame, full_212 score context, interactive protected S108/D164/H187.
- ESM score is not T50/activity; optional annotations do not silently alter the common rank.
- Labels and evaluator outputs are inaccessible through host, MCP, filesystem, worker and retrieval.
- No paid/provider/GPU/public action without recorded authorization. Never hide a non-Meta fallback.
- Local stdio first; verify and pin the actually compatible host/SDK/protocol.
- Keep null provider/model values until verified. No fabricated accessions/results/commands.
- Preserve prior preparation and helper provenance; no backdating or deceptive history rewriting.

## Review Focus

- Native host broad file/shell permissions: prove the evaluation workspace is isolated (C4).
- Streamlit reruns and provider timeouts: no duplicate paid jobs (C1/C5).
- Different residue frames: no silent correction or guessed atom correspondence (B0/C2).
- No-op agent over the same rank: separate workflow benefit from biological gain (B1/E1).
- Replay/unknown results: do not show cached inference as live or absent cost as zero (C5/S1).

## Order

H0 -> B0 -> C1 -> C2 -> B1 -> C3 -> C4 -> C5 -> E1 -> S1.
Keep one coherent path working; do not build two hosts and a full web platform at once.

## H0. Rules, ownership and permitted work

**Files:** `compliance/rules_snapshot.json`, `compliance/originality_ledger.csv`, `docs/STATUS.md`.

**Interfaces:** Inputs: captured guide and actual project history. Output: recorded permissions and unresolved gates.

- [ ] Before code reuse/publication, record which materials predate the event, review current rules and exact submission fields, and record the eligibility response if available. Do not send another inquiry automatically.
- [ ] Run the package checks. Record that no external account or rule status was verified by them. Resolve only true permission blockers; do not ask again for information already in this conversation.
- [ ] Record actual changed files, test outcomes and remaining gates in docs/STATUS.md. Commit only in an authorized development repository, preserving provenance.

## B0. Registered biological context

**Files:** `app/core/targets.py`, `app/core/capabilities.py`, `tests_app/test_target_gate.py`.

**Interfaces:** validate_target(profile: Mapping[str, Any], objective_id: str) -> ValidatedTarget; validate_variant(profile, variant: str) -> Variant.

- [ ] First test that a mature-frame request cannot silently pass the full-reference interface, that S108A is rejected interactively, and unknown atom coordinates cannot support distance claims. Integrate the v2 helpers and define typed outputs.
- [ ] Observe the targeted failure before implementing the minimal change; do not count an import typo as a behavioral test.
- [ ] Run python -m pytest tests_app/test_target_gate.py -v. Then run the full application tests. Exact-sequence tests do not complete atom mapping or validate phenotype.
- [ ] Record actual changed files, test outcomes and remaining gates in docs/STATUS.md. Commit only in an authorized development repository, preserving provenance.

## C1. Durable run state, approval and spend controls

**Files:** `app/core/runs.py`, `app/core/budget.py`, `app/core/artifacts.py`, `tests_app/test_run_policy.py`.

**Interfaces:** RunService.create(validated_input, owner_id) -> str; approve(run_id, plan_digest, budget_version, owner_id) -> Approval; reserve(run_id, job_digest, estimate_micros: int) -> Reservation.

- [ ] Write failures for cross-owner access, invalid plan digest, duplicate job reservation, lowered limit with in-flight work, and unknown provider completion. Implement transactional state and idempotency before inference adapters.
- [ ] Observe the targeted failure before implementing the minimal change; do not count an import typo as a behavioral test.
- [ ] Run python -m pytest tests_app/test_run_policy.py -v. Verify a restart preserves pending IDs and no second dispatch occurs merely after a timeout. Test future-call blocking without claiming perfect provider billing enforcement.
- [ ] Record actual changed files, test outcomes and remaining gates in docs/STATUS.md. Commit only in an authorized development repository, preserving provenance.

## C2. Real ESM baseline with a common score policy

**Files:** `app/science/esm_engine.py`, `app/science/ranking.py`, `tests_app/test_esm_contract.py`.

**Interfaces:** score_positions(reference: ValidatedTarget, positions: list[int], checkpoint_key: str) -> ScoreArtifact; rank_candidates(records, rank_policy: str) -> list[Candidate].

- [ ] First test mask/BOS alignment, WT identity, score sign, position-level reuse, exact cache identity, and rejection of mixed checkpoint/context ranks. Use small deterministic fixtures for tests, then one explicitly authorized tiny real ESM run.
- [ ] Observe the targeted failure before implementing the minimal change; do not count an import typo as a behavioral test.
- [ ] Run python -m pytest tests_app/test_esm_contract.py -v. Save checkpoint/tokenizer hashes and actual output. Without real inference, mark C2 integration pending, never relabel fixtures.
- [ ] Record actual changed files, test outcomes and remaining gates in docs/STATUS.md. Commit only in an authorized development repository, preserving provenance.

## B1. Development biological baseline and claim scope

**Files:** `evaluation/prepare.py`, `evaluation/baseline.py`, `tests_app/test_evaluation_cohort.py`.

**Interfaces:** prepare_cohort(source_paths, frozen_protocol) -> CohortManifest; evaluate_predictions(predictions, private_labels, protocol) -> EvaluationReport.

- [ ] First test missing/duplicate predictions and leakage-prone paths. Reconcile the actual raw/curated rows in a separate environment, freeze site-aware splits and verify a development-only baseline. Keep held-out outcomes unavailable during product work.
- [ ] Observe the targeted failure before implementing the minimal change; do not count an import typo as a behavioral test.
- [ ] Run python -m pytest tests_app/test_evaluation_cohort.py -v. Report real/null/negative results. If unavailable, continue only with an explicitly unvalidated evidence-assistant claim, not a numerical T50 claim.
- [ ] Record actual changed files, test outcomes and remaining gates in docs/STATUS.md. Commit only in an authorized development repository, preserving provenance.

## C3. Evidence adapters and actual MCP server

**Files:** `app/science/evidence.py`, `app/mcp_server.py`, `app/core/tool_executor.py`, `tests_app/test_mcp_roundtrip.py`.

**Interfaces:** ToolExecutor.dispatch(session_context, tool_name: str, arguments: dict, call_id: str) -> ToolResult; MCP exposes the six canonical tools with capability filtering.

- [ ] Write tests for discovery/call, empty/duplicate/out-of-range positions, unauthorized references, disabled fold/verifier, evaluator-tool rejection, pending task and prompt-injected source text. Use the official SDK matched to the selected host; implement stdio and trusted run binding.
- [ ] Observe the targeted failure before implementing the minimal change; do not count an import typo as a behavioral test.
- [ ] Run python -m pytest tests_app/test_mcp_roundtrip.py -v against a spawned real local server. HTTP fixtures do not prove Atlas live access. Return unavailable when no real snapshot/endpoint exists; do not fabricate hits.
- [ ] Record actual changed files, test outcomes and remaining gates in docs/STATUS.md. Commit only in an authorized development repository, preserving provenance.

## C4. One real Meta host and isolated workspace

**Files:** `app/host/meta_client.py`, `app/host/mcp_bridge.py`, `app/cli.py`, `tests_app/test_meta_loop.py`, `docs/HOST_COMPATIBILITY.md`.

**Interfaces:** MCPBridge.list_allowed(session) -> list[Tool]; call(session, tool_call) -> ToolResult; MetaHost.run(run_id) -> ReviewBundle.

- [ ] First test exact call-ID correlation, prompt/schema output validation, token/call ceilings, no-tool reporting, server rejection, no label/file escape and no hidden alternate-model fallback. Choose controlled API host or practically verified Muse Code; do not implement both by default.
- [ ] Observe the targeted failure before implementing the minimal change; do not count an import typo as a behavioral test.
- [ ] Run python -m pytest tests_app/test_meta_loop.py -v. After explicit spend approval, test one harmless real call and one real ESM-backed flow. Record model/provider, protocol, host version and usage without secrets. If native cost/isolation controls are insufficient, use the controlled host.
- [ ] Record actual changed files, test outcomes and remaining gates in docs/STATUS.md. Commit only in an authorized development repository, preserving provenance.

## C5. Thin local result viewer, optional

**Files:** `apps/streamlit_app.py`, `app/core/reports.py`, `tests_app/test_viewer_contract.py`.

**Interfaces:** load_run_view(run_id, owner_id) -> RunView; render_review(run_id) -> ReviewBundle. Viewer must consume the same events/artifacts as the host.

- [ ] First test repeated UI rendering does not dispatch work, unknown values remain unknown, replay badges persist, foreign-run access fails, CSV/HTML content is escaped, and numeric scores come from saved artifacts. Add four panels, not a multi-page SaaS.
- [ ] Observe the targeted failure before implementing the minimal change; do not count an import typo as a behavioral test.
- [ ] Run python -m pytest tests_app/test_viewer_contract.py -v and inspect the rendered local page. If a host/CLI already makes the demo clear, omit this stage and document the alternative. No deploy authorization is implied.
- [ ] Record actual changed files, test outcomes and remaining gates in docs/STATUS.md. Commit only in an authorized development repository, preserving provenance.

## E1. Frozen workflow and biological evaluation

**Files:** `evaluation/workflow_suite.py`, `submission/evidence_matrix.json`, `tests_app/test_metrics.py`.

**Interfaces:** evaluate_workflows(traces, frozen_scenarios, resource_caps) -> WorkflowReport, separately from EvaluationReport.

- [ ] First test consistent task denominators, failed tasks, unknown cost and cold/warm cache labels. Compare manual/fixed/Meta workflows on the same constraints and score policy. Freeze protocol before final outcomes; report equal biological ranks honestly.
- [ ] Observe the targeted failure before implementing the minimal change; do not count an import typo as a behavioral test.
- [ ] Run python -m pytest tests_app/test_metrics.py -v and execute only the authorized trials. Fill the evidence matrix with actual artifacts and limitations. No result placeholders may become claimed metrics.
- [ ] Record actual changed files, test outcomes and remaining gates in docs/STATUS.md. Commit only in an authorized development repository, preserving provenance.

## S1. Three-minute demo and submission preparation

**Files:** `demo/storyboard.json`, `demo/NARRATION_EN.md`, `submission/README.template.md`, `submission/manifest.template.json`, `compliance/originality_ledger.csv`.

**Interfaces:** Output: actual video, accessible permitted links, exact dependency/launch instructions and source/attribution records after implementation.

- [ ] Replace narration result slots only with measured evidence. Record true LIVE/REPLAY modes, demonstrate a meaningful branch, identify event-created work and clarify unverified science. Review final form for hosted access, duration/language and all contributor requirements.
- [ ] Run all application and package tests; inspect actual video metadata/audio and link access. No website/installer is added solely by assumption. Leave status not_submitted until an explicit authorized submit action returns a real receipt.
- [ ] Record actual changed files, test outcomes and remaining gates in docs/STATUS.md. Commit only in an authorized development repository, preserving provenance.
