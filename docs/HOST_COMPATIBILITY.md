# Actual compatibility receipt — 2026-10-27

| Component | Observed state |
|---|---|
| Python | Windows 3.14.0, .venv reuses installed packages; clean setup unverified |
| MCP | SDK 1.25.0, actual spawned stdio succeeded, negotiated protocol 2025-11-25 |
| Product host | Controlled Python; no native Muse Code compatibility claim |
| Meta | Requested muse-spark-1.3, official API contract read; prior OK/120 tokens user-reported |
| New live Meta/MCP proof | Pending, first partial attempt/key-alias diagnosis preserved; no retry |
| ESM | Pinned loader + fixture conformance; no real weights or inference |
| Modal | SDK 1.6.2 installed in .venv; offline public API signatures checked; no authentication/deployment/live call |
| RunPod | Explicit unconfigured adapter, no endpoint/Pod created |
| Isolation | Allowlisted workspace/no generic tools; OS ACL sandbox unverified |

Implementation references checked:
[MCP SDK v1.25.0](https://github.com/modelcontextprotocol/python-sdk/tree/v1.25.0),
[Meta tool calling](https://dev.meta.ai/docs/tool-calling),
[Chat Completions](https://dev.meta.ai/docs/protocols/chat-completions),
[Modal Function](https://modal.com/docs/reference/modal.Function),
[FunctionCall](https://modal.com/docs/reference/modal.FunctionCall).
Reading documentation is not a live account/SDK/cloud receipt.
