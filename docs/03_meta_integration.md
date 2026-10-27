# 03. Meta integration: separate models, hosts, development and billing

## Roles

Muse Spark (or another verified eligible Meta model) is the product's runtime decision maker.
Muse Code is a coding agent and can also be an MCP host. ESM-2 is a separate scientific model.
Atlas is an evidence source, not a selectable chat model. Using Muse Code merely to write code
is not by itself evidence that the submitted product uses a Meta model meaningfully [S21-S23].

## Choose one working path

**Path A, reference:** Python host -> Meta API -> native function call -> guarded MCP client/server.
**Path B, compatibility:** verified Muse Code runtime -> BioPilot MCP server, with the actual Meta
model identified in a sanitized run record. Do not assume Spark is the default or supported model.
Use one path for the primary demo. Do not spend the event maintaining two full frontends.

Muse Code's official changelog describes MCP configuration/tool discovery [S23], but exact version,
permissions, protocol and account billing must be tested locally. A current MCP documentation page
may describe a different protocol from an installed host. Pin SDK and negotiated protocol after
checking compatibility; use the SDK lifecycle rather than hand-coding a guessed handshake [S22].

## Proposed Meta API contract, still requiring verification

Keep base_url/model null and live access disabled in shipped config. Confirm the actual model ID,
provider domain, roles, JSON Schema subset, function schema, tool-choice values, token parameter,
error shapes and data-use terms. Inherited candidates are not newly authenticated.
Proposed examples use Chat Completions, developer instructions, tool_choice=auto,
parallel_tool_calls=false and max_completion_tokens. They are not promises of current acceptance.
Do not mix Chat and Responses parameter names or silently degrade strictness.

## Three stages and MCP bridge

Plan: no tools; schema-bound plan, supported goal only, human approval required for execution.
Execute: resolve the policy-filtered MCP catalog, convert schemas to native function definitions,
keep exact call IDs, validate arguments and route through MCP. Return bounded structured outputs.
Report: no tools; schema-bound explanation over stored outputs. Code renders all numerical tables.
A pending job is not a completed result. Do not extract private chain of thought as a demo artifact.

The offline `checks/hackathon_contracts.py` catalog conversion demonstrates mapping only. It is
not a network client/server. The application must implement and test the actual MCP round trip.

## Scientific and label context

Only send approved objective/reference summaries, protected full positions, capability state and
permitted tool outputs. Never send measured T50 labels, benchmark cutoff, evaluator results,
full paper outcomes, this entire ZIP or a broad project memory to the prediction agent.
A model's prior knowledge of public benchmarks remains a limitation even with filesystem isolation.

## Controlled live readiness

After explicit approval, record installed host/SDK versions, verify a harmless status call, test one
schema plan, a tool/result round trip and a no-tool report. Then perform a tiny ESM-backed trace.
Record actual provider/model, prompt and catalog hashes, tool arguments/results, latency and usage
without credentials or private reasoning. Disclose when a model response is cached or simulated.

Codex/Claude Code can assist development if their use meets event rules; no unrestricted official
permission is inferred from silence. Their subscription/API usage is separate from Meta credits.
No fallback to a non-Meta runtime may be hidden in the final demo.

## Cost accounting

Treat hosted Meta API, Muse Code subscription/allowance, scientific GPU, partner inference and
storage as separate budgets. Do not promise the $150 Meta API grant funds a Muse Code subscription,
ESM on Modal or a third-party model. Confirm eligible usage and actual credits in each account.
