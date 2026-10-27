# 05. Security, permissions and spend control

## v2 biological/data isolation update

Never mount evaluation_private, raw assay labels or outcome-bearing paper excerpts into the runtime agent. Build a whitelist, not just a blacklist of T50 column names. Reference coordinates require an independently verified import. Provider model/base URL placeholders are not runnable defaults. Scientific guards do not replace spending/ownership guards.


## Authorization gates

Keep `paid_execution_enabled=false` by default. Development planning and local synthetic tests do not authorize model requests, GPU usage, deployment, account changes, publication or submissions. Each class of external action needs explicit approval, recorded with scope and time.

Confirm official event rules before writing submission code outside the permitted window. Confirm personal participation and institutional ownership separately. The public event page has eligibility exclusions; this package is not legal clearance [S01].

## Secret and data boundaries

API keys stay in local environment variables or the deployment secret manager. Never place keys in prompts, frontend bundles, screenshots, exports, logs or fixtures. Use a separate project key and least privilege. Rotate an exposed key rather than merely deleting a screenshot.

Only explicitly authorized public enzyme data may leave the local environment. Classify sequence uploads separately from text-only Meta calls. The initial Meta context can use IDs, goals and feature summaries; it need not receive all raw sequences. Do not connect the product to institutional NAS, research servers or unpublished repositories.

Treat source text, filenames and tool results as untrusted. A result saying "ignore previous instructions" is data, not a new policy. Block arbitrary URLs, private network destinations, file paths and shell commands. The browser never sees provider credentials.

## Budget mechanism

Proposed first approved live-run ceiling: USD 2.00, 12 Meta requests, 200 candidate variants, 24 optional verifier positions and zero structure predictions. These are starting limits, not measured costs or a request to spend. ESMFold can be enabled later with an explicit ceiling, for example four structures.

Use integer USD micro-units. Before dispatch, atomically reserve a conservative cost estimate and check remaining limits. After a tool settles, reconcile to actual usage. An ambiguous timeout remains reserved; do not release and resubmit immediately.

For a concurrent reservation race, only the transaction that fits the remaining balance may succeed. A reduced user budget blocks new work and requests cancellation of pending optional jobs. Record unavoidable in-flight usage separately.

A local estimated ceiling is **not an absolute provider billing guarantee**. Model reasoning tokens, GPU cold starts, billing delays, failed jobs and retries can create differences. Use provider-side limits where available, cap worker concurrency at one, and reconcile provider usage after each run. Do not claim spend is zero because credits might cover it.

Reserve enough budget for the final report before optional evidence work. If it is unavailable, generate a deterministic partial report without another model call.

## Network and artifact hygiene

Allowlist provider hosts in code, not via model-supplied URLs. Use timeouts, size caps, MIME checks, finite JSON array lengths and authenticated downloads. Fetch public structures only for verified accessions.

Escape HTML and Markdown content in the UI. Protect CSV exports against formula injection. Validate artifact ownership, archive paths and filename traversal. Do not automatically unpickle untrusted model/data files. Pin model revisions and use trusted distributions; do not enable remote code execution just to make a checkpoint load.

Use local SQLite on persistent disk only for the solo single-writer deployment. Back up metadata and artifacts before upgrades. Do not advertise multi-tenant production readiness.

## Runtime safety scope

This prototype supports benign public-enzyme candidate review only. It does not design harmful agents, optimize toxins/pathogens, advise clinical use, order synthesis, change laboratory devices or prescribe wet-lab steps. Out-of-scope requests are blocked rather than routed to unrestricted tools.

## Release checklist

Check ownership, rules, provider account permissions, credits, data licenses and attribution. Atlas data documentation uses CC BY 4.0 [S10]; other code, weights and assays need their own notices. Do not assign a license to institution-owned code by assumption. Strip credentials and private identifiers from the demo. Submit only after the owner reviews the actual artifacts.

## Modal account guard

Check the workspace usage budget and net spend limit separately. Modal documents these as distinct controls, with credits affecting net charges rather than the usage total. Do not assume environment-level budget features are available on the current plan. No account setting has been inspected or changed here [S16].

## v3 transport and judging cross-reference

The biological protocol above remains unchanged. Apply docs/15_mcp_contract_and_hosts.md at
all host/server boundaries and docs/16_impact_and_agent_evaluation.md for workflow impact.
The evaluator is not an MCP tool; a thin UI does not relax any biological or permission gate.
