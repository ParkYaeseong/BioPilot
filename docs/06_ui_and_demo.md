# 06. Thin demo interface, not a new web platform

## Required evidence, optional interface

The captured guide requires a public repository, a working project and a three-minute demo [S21].
It does not explicitly mandate a hosted website or an installer. Confirm the final form before
assuming a local-only deliverable satisfies all judging access expectations.

Primary experience: a Meta-backed conversation invokes real BioPilot MCP tools. Optional support:
a local Streamlit viewer opens the corresponding run ID and explains results to non-specialists.
No Next.js rewrite, login system or multi-tenant SaaS is needed for this MVP.

## One page, four visible areas

1. **Goal and constraints:** registered target, supported goal, coordinate frame, protected sites and approvals.
2. **Execution trace:** actual provider/model, concise decision, MCP tool, result status, elapsed time and provenance badge.
3. **Candidate review:** deterministic ESM score/rank, model revision, evidence and explicitly unknown phenotype status.
4. **Evidence and exports:** sources, cost actual/estimated/unknown, run hashes, CSV/FASTA/JSON and limitations.

Native Muse-host mode uses the viewer read-only. Controlled-host mode may add input/approve/cancel
controls backed by the same services. Streamlit reruns must not duplicate a paid job; use durable
server-owned state and idempotency, not page memory alone.

## Three-minute proof

The current UI recording plan is `demo/review_flows_180s.json`, with English narration
in `demo/REVIEW_FLOWS_180S_EN.md` and Korean screen actions in `demo/REVIEW_FLOWS_180S_KO.md`.
It plans exactly 180 seconds of the unified file/request workflow and a labeled recorded
uploaded-input execution (3 Meta requests,45.48 seconds), followed by its actual result views.
Tutorials remain separate local/replay walkthroughs and never invoke execution.
The original `demo/storyboard.json` and `demo/NARRATION_EN.md` remain historical plans.
Show a real request, actual Meta-to-MCP execution, one concrete failure or constraint branch and a
reviewable result. Explain the measured workflow benefit, not a fictional biological improvement.
A clear output is more useful than scrolling through large logs or a wall of architecture slides.

Screen badges distinguish LIVE, IMPORTED SNAPSHOT, REPLAY and SYNTHETIC FIXTURE. A replay is a
truthful backup only. Do not claim replay duration is inference latency. Preserve actual wall-clock
runtime separately and label any edited waiting interval. Never present fixtures as scientific results.

## Recording and access

Prepare English narration or subtitles for judges and Korean notes for the presenter. This is a
communication recommendation, not a newly discovered mandatory language rule. Read the final
language/access requirements. Test the real exported video duration, audio and legibility; validating
a storyboard is not validating a video. Check links without your own login. No faces are required by
this plan; do not assert the event forbids or requires them without a source.

Sensitive screens: never expose API keys, billing details, account identifiers or institutional files.
A publicly hosted demo must be read-only unless authenticated/authorized; it must not spend from the
owner's account for anonymous visitors. Neither public code nor a video authorizes arbitrary remote compute.
