# 02. MCP-first system design

## Topology

User -> controlled Meta host OR verified Muse Code host -> BioPilot MCP server -> deterministic
science/policy core -> ESM worker and approved evidence adapters -> SQLite/artifact store.
A thin Streamlit viewer reads the same run events and outputs. The offline evaluator is a separate
process with private labels, outside every host, MCP resource and model context.

| Layer | Implementation proposal | Responsibility |
|---|---|---|
| Reference host | Small Python Meta API loop plus MCP client | Planner/executor/report stages and bounded model requests |
| Existing host option | Muse Code with one BioPilot MCP server | Convenient conversation; version/account/isolation gate first |
| MCP server | Official Python SDK, local stdio first | Tool discovery/calls and untrusted input boundary |
| Core | Typed Python services and v2 science guards | Target validation, plan authorization, ranking, evidence and budget |
| Worker | One durable process, async job IDs | ESM inference, retry/reconciliation and persisted state |
| State | SQLite WAL + persistent artifact directory | Immutable runs, events, tasks, hashes and budget ledger |
| Optional UI | Streamlit, loopback by default | Request/approval in controlled-host mode, trace and result inspection |
| Evaluator | Separate offline command/environment | Join frozen predictions to labels and compute evaluation |

The Meta model is not an MCP client by itself. Either an existing host or our adapter performs
protocol operations and maps model tool calls to MCP tools [S22]. Do not assume Meta's REST API
accepts an arbitrary MCP URL or that Muse Code uses a particular model/account by default.

## Interfaces planned for the application

`TargetRegistry.validate(reference_id, objective_profile_id, frame) -> ValidatedTarget`
`RunService.create(validated_input, owner_id) -> run_id`
`RunService.approve(run_id, plan_digest, budget_version, owner_id) -> Approval`
`ToolExecutor.dispatch(session_context, tool_name, arguments, call_id) -> ToolResult`
`ArtifactStore.get_owned(run_id, artifact_id, owner_id) -> Artifact`
`ReportService.render(run_id) -> ReviewBundle`

These are design interfaces, not shipped implementations. `checks/` contains reference guards only.
An optional FastAPI surface can call these services later; it is not required for the local submission.

## Host-independent enforcement

The server obtains a trusted session/run binding from the application launcher, not a model-selected
owner ID. For stdio, use a dedicated process/configured run context or a trusted host association.
A run ID alone is never authorization. For remote HTTP, require authentication, authorization,
origin/host checks and TLS before exposing compute. Remote mode is disabled in P0.

Every MCP call rechecks the canonical schema, ownership, target/variant validity, state, capability,
plan digest, budget version and idempotency. The same checks apply to direct/CLI invocations.
Model-supplied descriptions cannot grant permissions or change objective capability.

## Durable execution

States: DRAFT -> VALIDATED -> PLANNED -> AWAITING_APPROVAL -> QUEUED -> RUNNING -> REPORTING
-> COMPLETED. Alternative outcomes: BLOCKED, PARTIAL, FAILED, CANCELLED.
Tasks and reservations are committed before dispatch. Store provider job IDs immediately. After a
network timeout, reconcile that job before resubmission. An unknown charge remains unknown.

A lower budget affects future jobs, not already incurred costs. If a newly approved cap is below
committed usage, report the conflict, stop new dispatches and report in-flight work honestly.
Long ESM jobs return a persistent task ID. The worker waits/polls; do not waste model calls polling.
Use application-level job IDs unless a mutually supported MCP task extension is actually verified.

## Tool and resource inventory

Canonical catalog: `schemas/tools.mcp.json`. Six designed tools: validate_target_context,
score_positions, retrieve_atlas_evidence, fetch_atlas_structure, predict_structure, get_run_status.
Filter optional tools by verified backend capability. Registered immutable exports can be delivered
by the host/core; no general file-reader tool is needed. See docs/15 for argument and transport rules.

No evaluation/ProteinGym-label tool, arbitrary shell, URL-fetch, SQL, secret read or budget-increase tool.
PDB/Atlas/ESM artifacts have different subject and evidence levels. A reference structure is not the
structure of a new mutant. ESMFold and coordinate-derived claims remain disabled until their own gates pass.

## Storage and cache identity

Keep references, runs, candidates, tasks, scores, evidence, ledger, events and artifacts as in v2.
Persist score provenance: sequence hash/context, checkpoint revision, tokenizer/scoring method,
mask position and numerical precision. Mutations at one position share a forward pass only under
the registered masked-marginal definition. Do not mix 150M and 650M values in one rank column.

## UI boundary

The viewer is not an additional agent. It reads event/artifact IDs from the same services and marks
LIVE, IMPORTED SNAPSHOT, REPLAY or SYNTHETIC FIXTURE. Native-host mode can use a read-only viewer.
Controlled-host mode may add request/approval controls. Do not duplicate approvals in both hosts.
Local demo access and remote judge access are separate readiness questions; recheck the submission form.

## Runtime isolation

Build an explicitly reviewed allowlisted workspace; do not mount the whole design repository.
Exclude evaluator files, tests, scientific outcome text, caches containing labels, shell tools and
broad knowledge search. Muse Code filesystem reach must be restricted by environment/permissions,
not only a prompt. If that cannot be verified, the reference controlled host is the evaluation path.
