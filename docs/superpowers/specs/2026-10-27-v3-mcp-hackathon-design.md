# BioPilot Atlas v3 design: MCP product, evidence and short demo

## Approved direction and scope

The user requested the existing complete ZIP be updated using the discussed themes, judging criteria
and MCP-oriented product approach. This is a **package revision**, not authorization to build/deploy
or submit a live product. The next implementation must preserve the biological restrictions from v2.

## Approaches

Large web app: flexible but unnecessary for a solo scientific demonstration.
MCP only: reusable but harder for non-specialist judges to understand.
MCP with an existing/controlled Meta host and optional thin result viewer: selected package default
based on the user's MCP preference and the prior discussion. Streamlit is a proposed minimal viewer,
not a mandatory contest format or an irrevocable choice.

## Components and trust

One scientific core enforces source/target/score rules. An MCP server exposes a small catalog. One
Meta host controls the conversation and approved calls. Durable worker/ledger manages inference.
An optional viewer consumes the same artifacts. An isolated evaluator joins labels after prediction.

## Judge-facing contribution

Show actual scientific tool use, correct target/numbering handling, useful constrained decisions,
and inspectable evidence/cost output. Measure workflow utility separately from ESM rank quality.
Do not overclaim an enzyme improvement, research breakthrough, calibrated uncertainty or validation.

## Global constraints

No labels in the host/MCP environment. No secret or institutional data disclosure. No arbitrary
execution tools. No paid/public/external action without permission. Retain prior-work provenance.
Current rule snapshot is source-captured from this conversation; fresh browser access is unavailable.

## Builder review

Self-review performed against v2 and the conversation; no independent subagent was available.
The main risks are host filesystem leakage, API/MCP version mismatch, confusing model vs host,
and treating a 180-second plan as a tested video. Each is assigned a specific implementation task
and release check. No claim of live application verification is made.
