# Actual compatibility receipt — updated 2026-10-28

The rows below distinguish installed local components and saved live execution from unverified
remote integrations. They do not claim a new provider call on 2026-10-28.

| Component | Observed state |
|---|---|
| Python | Windows 3.14.0; `.venv` reuses installed packages; clean setup on another machine unverified |
| MCP | SDK 1.25.0; actual spawned local stdio succeeded; negotiated protocol `2025-11-25` |
| Product host | Controlled Python host; no native Muse Code compatibility claim |
| Meta | Saved integration requested and returned `muse-spark-1.3`; three requests completed validation, scoring and final explanation |
| Real Meta/MCP proof | Run `5b7c92bc2d364680809713bf8c332f66`, 2026-10-27, `sequence_review_complete`; 40 s wall; saved receipt linked below |
| ESM | Real local `esm2_t30_150M_UR50D`, revision `a695f6045e2e32885fa60af20c13cb35398ce30c`; CPU/float32; Transformers 5.2.0 / PyTorch 2.9.1; pinned weights/tokenizer; `full_212` |
| Viewer | Streamlit 1.66.1; local read-only saved-artifact renderer; localhost binding; replay is labelled separately from original inference |
| Modal | SDK 1.6.2 installed; offline public API/bounds checked; no verified remote deployment/GPU integration; current remote readiness remains pending |
| RunPod | Explicit unconfigured adapter; no endpoint/Pod created |
| Atlas / folding | No verified live integration; no geometry or efficacy claim |
| Isolation | Allowlisted product workspace and no generic tools; OS ACL sandbox unverified |
| Cost | Actual Meta invoice remains `null`/`unknown`; local reservation is not a bill |

Installed Python/MCP/PyTorch/Transformers/Streamlit versions were rechecked with local package
metadata on 2026-10-28. The actual execution evidence is the preserved
[integration receipt](../validation/integration_success_20261027.json), with checkpoint/tokenizer,
reference, bundle and score-artifact hashes. Prior failures remain in `validation/`.
Viewing its portable artifact is **REPLAY**, not a fresh integration test.

Historical implementation references consulted during the implementation:
[MCP SDK v1.25.0](https://github.com/modelcontextprotocol/python-sdk/tree/v1.25.0),
[Meta tool calling](https://dev.meta.ai/docs/tool-calling),
[Chat Completions](https://dev.meta.ai/docs/protocols/chat-completions),
[Modal Function](https://modal.com/docs/reference/modal.Function),
[FunctionCall](https://modal.com/docs/reference/modal.FunctionCall).
These links are not a claim that account state, current pricing, current API behavior or remote
compatibility was freshly checked on this documentation update.