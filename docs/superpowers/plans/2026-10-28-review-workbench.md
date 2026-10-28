# Review workbench implementation plan

Spec: `../specs/2026-10-28-review-workbench-design.md`. User authorized execution.
Use the existing dirty checkout; preserve earlier work and do not commit unrelated
changes. Independent owners implement tasks 1 and 2 in parallel, then root verifies.

## Review focus

- An apparently LIVE saved run must still be playback; mode/unknown cost remain visible.
- A user input check must not mutate the saved report or silently convert numbering.
- Candidate subset/CSV must preserve stored scores and original rank; text cannot inject formulas.
- Trace reasons are untrusted text, escaped and short; private reasoning fields are omitted.
- Missing manual/Meta observations must not turn into successes, zeros or measured impact.

## Task 1 — Streamlit workbench

Own `app/viewer.py`, `app/viewer_data.py`, new `app/review_checks.py`,
`tests_app/test_viewer.py`, `tests_app/test_review_checks.py`, `tests_app/test_demo_replay.py`
only where its existing UI assertions need the intended new UI. Optional original CSS
may be `app/viewer.css`. Do not change runtime catalog/allowlist or provider modules.

Interfaces: retain `load_run_view(path)`, `format_candidate_rows(rows)` and
`claim_banner()`. Add pure view helpers for task context, public trace events,
candidate subset/comparison and safe CSV. `check_review_input(variant, frame,
objective) -> dict` in `review_checks.py` calls registered product guards only.
Viewer imports this guard module; pure viewer_data imports stdlib only, no providers,
runtime state or evaluator. Extend its import-isolation assertion for necessary stdlib.

1. Write failing behavioral tests: trace public reasons/order/private-field omission;
   top-five/original-rank comparison/CSV; unchanged saved file across input checks;
   protected/WT/frame/goal refusals; AppTest top-level context and actual selection.
2. Run focused tests and record expected behavioral failures, not only import errors.
3. Implement the spec's one-page neutral workbench with native controls and original
   local styling. Keep old helpers compatible where useful; update assertions to
   actual behavior when presentation changes. No fake Run button or new paid work.
4. Run `.venv/Scripts/python.exe -m pytest tests_app/test_viewer.py tests_app/test_review_checks.py tests_app/test_demo_replay.py -q -p no:cacheprovider --basetemp=.cache/workbench_ui`.
   Expect pass, including real Streamlit AppTest.

## Task 2 — Frozen policy-intake comparison

Own `evaluation/workflow_protocol.json`, `evaluation/workflow_suite.py`,
`tests_app/test_workflow_suite.py`, `validation/workflow_policy_baseline_20261028.json`.
No edits to app UI, STATUS/DECISIONS, submission evidence or source manifest.

Interfaces: `run_fixed_policy_suite(protocol) -> dict` returns measured local policy
observations, explicitly incomplete manual/Meta arms and no workflow-gain claim.
`evaluate_workflows(protocol, observations) -> dict` validates exact scenario/method
identity, denominators and finite optional measures; failed and missing tasks remain.
CLI only runs this fixed local policy arm and writes a fresh non-overwritten report.

1. Freeze six cases, methods and expected outcomes from the spec in protocol JSON.
2. Write failing tests for missing-arm denominators, wrong/duplicate/unregistered
   observations, null human time/unknown cost, no matched-gain claim, deterministic
   protocol hash and actual guard outcomes. Observe behavioral failures.
3. Implement actual guarded intake checks with no scores/inference/network. Retain
   per-case input/status/guard errors and timing; distinguish from scientific reviews.
4. Run focused pytest, execute the offline suite once, preserve protocol/source hashes.
   Expect six fixed observations and twelve missing manual/Meta observations; no
   fabricated human interventions or provider costs.

## Task 3 — Integrate, inspect and record

Root reviews diffs and focused results, asks a fresh reviewer for isolation/claim
checks, and resolves concrete defects with RED/GREEN. Inspect the actual local page
through CUA at desktop size, exercise candidate selection, trace and local refusal.
Capture screenshots of the final workbench. Keep the prior video and source ZIP;
prepare a versioned local recording with honest replay and actual local interactions
where possible. No new calls or artificial Meta response in the recording.

Update docs/STATUS.md, docs/DECISIONS.md, current guides/submission files and reuse
ledger with exact commands, real/mocked/replayed modes, source hashes and open gates.
Regenerate MANIFEST.sha256, run full pytest and package validator, create a new
private source ZIP and verify its unpacked package. Final report links the actual UI,
recording material and comparison limits; actual matched Meta/human study remains pending.
