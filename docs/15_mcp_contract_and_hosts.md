# 15. MCP contract, hosts and model boundaries

## MCP is the reusable tool interface

MCP connects a host/client to tools/resources; it is not a model, a GPU, an execution policy or a
scientific evaluation method [S22]. Our server wraps deterministic biological services. Meta is the
runtime model in the host. Muse Code may provide that host, or a small Python adapter may do so.

## Six designed tools

| Tool | Input | Result and limits |
|---|---|---|
| validate_target_context | registered reference ID, short reason | Hash/frame/objective/protected-site check; cannot edit policy |
| score_positions | reference ID, allowed checkpoint key, unique full positions, reason | Actual masked marginals or persisted pending job; no outcome prediction |
| retrieve_atlas_evidence | registered reference ID, bounded hit count, reason | Provenanced real hits/snapshot or unavailable; no made-up accessions |
| fetch_atlas_structure | verified legacy Atlas accession, reason | Predicted reference/homolog structure, not exact mutant proof |
| predict_structure | existing candidate ID, reason | Optional exact-candidate prediction; disabled by default |
| get_run_status | no model-selected owner/run ID | Bound run state, current limits, artifacts and unresolved costs |

The full catalog is in schemas/tools.mcp.json. The model sees only the subset that can actually run.
Unknown tools are rejected. A disabled verifier also narrows model_key to esm150; rejecting the
server call is still required. Meta/Biohub Atlas schemas and accessions must not be silently mixed.

## Not tools

Approval, owner identity, plan digest, limits, run creation and export permissions are trusted-host
operations, not LLM-editable authority. Ranking and report-number rendering are deterministic core
operations. ProteinGym labels and evaluation are **never** MCP tools/resources or source context.
A script running experiments is not an MCP integration until an actual protocol call succeeds.

## Transport and compatibility

Start with local stdio and one trusted session/run binding. Pin the tested Python MCP SDK and actual
host. Do not force a protocol version from a newer web page onto an older client: current official
MCP docs and Muse Code changelog mention different-version lifecycle details [S22-S23]. Let the
chosen SDK/host negotiate and record the working version. SDK initialization must be verified in
its matching official documentation. No arbitrary user commands in the server launch config.

A verified HTTP implementation is optional later; it needs authentication, origin/host checks,
permissions, TLS when remote, rate limits and persistent state. Do not expose localhost through a
public tunnel just to make a demo link.

## Job result lifecycle

Guard and reserve before dispatch. Return pending plus task_id for long computation. Persist the
provider job ID and reconcile before retries. A model-requested repeated status call does not cause
new inference. Backend timers handle waiting. Respect the approved Meta request cap and final-report
reserve. Terminate gracefully with a deterministic partial report on budget/provider failure.

## Native host versus controlled host

Muse Code can offer an existing UI and MCP tool list [S23]. Verify the actual Meta provider/model,
tool permissions, workspace, model budget and account charging; never assume a particular model
or that hackathon API credits fund its subscription. Native generic file/shell tools must not reach
outcomes. Restrict them at the host/environment layer. Use a separate runtime workspace, not the
repository containing evaluation_private or paper results.

If global Meta-call limits cannot be enforced in the native host, say so; use the controlled API host
for the strict budget/evaluation demonstration. Server-owned scientific limits still apply to all hosts.
Do not claim native-host compatibility until actually tested with the installed version.

## Proposed configuration and tests

The Muse config file is a placeholder shape only, not an installed or verified configuration.
Required tests: tool discovery/call, schema parity, unknown tool, disabled backend, cross-run ID,
pending task, repeated call, version mismatch, host restart, injected source instructions and label-isolation
attempt. `checks/hackathon_contracts.py` verifies offline portions only; it is not live transport proof.
