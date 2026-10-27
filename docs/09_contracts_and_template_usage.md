# 09. Contracts, examples and templates

The JSON files are proposed application contracts, not live provider responses. Examples are
synthetic protocol fixtures unless their provenance explicitly states otherwise.

| File | Meaning |
|---|---|
| run_input.schema.json | Supported goal, frame, target and limits |
| plan.schema.json | Structured plan and scientific scope |
| evidence.schema.json | Provider, subject, evidence level and provenance |
| tool_result.schema.json | Success/pending/error/blocked, artifacts and usage |
| report_narrative.schema.json | Evidence-linked explanation; no claimed biological efficacy |
| tools.mcp.json | Canonical designed MCP inventory and input schemas, not a JSON-RPC response |
| tools.chat_completions.json | Equivalent full function catalog generated from the MCP catalog |

The server filters the canonical inventory by state, ownership, enabled backends and budget.
`score_positions` has nonempty unique positions. With the 650M verifier disabled, the advertised
model_key enum is restricted to esm150. Structures stay unavailable unless their feature gates pass.
`validate_target_context` checks registered context; it cannot edit the reference, grant approvals or change goals.

The full designed catalog is not what every model call receives. Execute examples deliberately
advertise only get_run_status, a harmless synthetic round trip. A disabled or unknown tool must also
be rejected if invoked directly. MCP annotations are hints, never authorization.

Plan and report examples embed the canonical runtime prompt and schema. Regenerate them after a
prompt/schema edit. Keep exact assistant tool-call/result IDs. No provider call is made by these files.
No tool evaluates experimental labels or reads evaluation_private. Final evaluation output may be
shown to human judges only after predictions freeze, not fed back into that prediction session.

For template rendering, bind each required slot using controlled serialized data. Reject missing or
unresolved slots. Do not let user/source text choose template paths or override policy fields.
Placeholder IDs/model/base URL must never be sent to a live provider.

`templates/muse_mcp.example.json` is a **non-runnable configuration shape**. Confirm supported
configuration location/keys and replace values only after the application exists. It is not an
instruction to copy unknown flags into Muse Code. `config/runtime_bundle.allowlist.json` lists the
reviewed runtime source files; an actual bundler must check content, symlinks and destination isolation.
