# Unified review workbench implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline to implement task-by-task. Do not start new user chats.

**Goal:** One Streamlit app from approved file/example input through explicit real execution to the existing five result views and recent records.

**Architecture:** Add app/bench.py as the composition root; retain the independently read-only viewer and original Meta/MCP host. A local host-side SQLite journal freezes validated inputs and atomically claims execution once, independently of browser state. It indexes only its own reports and the registered public replay, never scans runtime/evaluator directories.

**Tech stack:** Existing Python/Streamlit/SQLite, existing controlled Meta host, local pinned ESM CPU provider and vendored3Dmol. No new web framework or cloud service.

**Spec:** Owner's approved unified flow in the preceding conversation: input/example, request, validation, explicit permissions/limits, execution, same result views, recent reviews. Actual execution requested in the current message.

## Global constraints

- Only registered public full_212 Lipase A input is executable. Exact matching uploaded full-reference FASTA is accepted; mature/unregistered input is rejected before dispatch.
- Optional uploaded mmCIF must match the pinned public1ISP bytes to become executable context; do not silently use an unverified upload as a coordinate source.
- Full-reference1-based numbering, protectedS108/D164/H187, common ranking, supported claim scope, label isolation and no invented geometry stay unchanged.
- Unknown provider billing remains unknown. One verification run, at most4Meta requests, local CPU ESM; no remote GPU/allocation/upload is required.
- Preparation, browsing recent records, page refresh and tutorial actions never dispatch execution. Explicit execution consumes the validated review atomically before subprocess launch.
- No automatic retry of failed/partial/unknown/running records. New deliberate requests require new validation/approval. Preserve raw run reports and input receipts.
- UI language English, appearance Auto by default; desktop/mobile layouts reuse established palette and responsive styles.

## Review focus

- Uploaded sequence differs/mature: refuse, no fallback to a different sequence, no provider call.
- Changed file/request/approval: clear pending confirmation, never execute stale frozen input.
- Refresh, two browser sessions or interrupted host: durable single claim and global configured run cap prevent duplicate dispatch.
- Actual partial/failed result: preserve evidence and truthful status, no synthetic completion or implicit retry.
- Recent records: only journal-owned paths plus bundled example; reject traversal, integrity mismatch and fabricated imported completion.

## Task1 — frozen intake and durable execution journal

- [x] Add failing tests for file/example parity, unsupported uploads, protected requests, atomic duplicate claims and durable caps.
- [x] Implement app/bench_intake.py and app/bench_store.py; bind input hashes, explicit goal and runtime path to a frozen local record.
- [x] Verify focused tests without provider or GPU calls.

## Task2 — one app and reusable result renderer

- [x] Add failing AppTests for New review / Recent reviews, upload controls, no two-surface switch and no dispatch on navigation.
- [x] Extract the existing viewer presentation into render_workbench while retaining legacy viewer.main behavior and import purity.
- [x] Implement app/bench.py and app/bench_execution.py. Only the explicit approval submit claims then invokes original run_session; completed records open the same five result views.
- [x] Exercise mocked completed/partial/failed paths, file edits, review reopening and reruns; mocks remain labeled.

## Task3 — actual bounded run and browser evidence

- [x] Verify local ESM pins/config and Meta credential availability without displaying credentials.
- [x] Start canonical app at8522; retain8523 as a compatibility link to the same app.
- [x] Execute one approved registered example/FASTA request through the new journal/bridge, maximum4Meta requests. Record actual status, model, report and score hashes; do not manufacture completion.
- [x] Inspect real browser file/example intake, validation, approval, recent records, result views, guided tutorial and mobile layout; save screenshots.

## Task4 — current demonstration and verification

Final regression/browser/review results are recorded in STATUS and the final UI receipt; source sync follows verification.

- [x] Update bilingual180s script/captions to the unified flow and actual recorded outcome, explicitly label any recorded execution and edited waiting.
- [x] Run focused then full regression, source package and unchanged scientific-evidence checks. Update STATUS/DECISIONS and receipts.
- [ ] Review the full change, then sync the existing private repo preserving history. No public deployment/submission.
