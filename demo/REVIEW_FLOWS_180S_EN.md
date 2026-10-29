# BioPilot Bench — current 180-second demo script

Prepared 2026-10-29 (Asia/Seoul). This is the current script for the five-view Saved Review and three-stage New Review UI.

**Recording plan, not a newly exported video.** Show actual saved Meta/MCP evidence and actual unarmed input checks. No new provider or GPU call is needed.

English narration: **291 words**, approximately **97 words/minute** averaged over the three-minute timeline. This is a planning estimate, not measured speech.

Use `review_flows_180s.json` as the timeline and `REVIEW_FLOWS_180S_EN.srt` for planned captions. Korean actions and narration are in `REVIEW_FLOWS_180S_KO.md`.

| Time | Actual screen | Purpose |
|---|---|---|
| 0:00–0:15 | Saved Review / Overview | The review problem |
| 0:15–0:35 | Saved Review / Agent Trace | What Meta actually did |
| 0:35–0:55 | Saved Review / Candidates | Compare and inspect candidates |
| 0:55–1:20 | Saved Review / Structure | Locate only what the structure supports |
| 1:20–1:40 | Saved Review / Evidence | Inspect provenance |
| 1:40–1:55 | New Review / INPUT | Switch to a new review |
| 1:55–2:15 | New Review / local validation refused | Show a real local refusal |
| 2:15–2:45 | New Review / VALIDATED, UNARMED | Prepare a valid request and inspect execution gates |
| 2:45–3:00 | New Review confirmation / closing | State the contribution and limits |

## 0:00–0:15 | The review problem

BioPilot Bench helps researchers review protein variants with traceable evidence. Here are nineteen saved Lipase A candidates and their ESM sequence preferences. These are recorded results, not a new model run.

## 0:15–0:35 | What Meta actually did

The saved trace shows what Meta actually requested through MCP. It first requested target validation, then sequence scoring. Code enforces constraints and ranking; ESM supplies sequence preferences. Opening these records sends no new request.

## 0:35–0:55 | Compare and inspect candidates

Compare the leading candidates without changing their original scores or ranks. Select A32V and open Structure. The same candidate selection carries across views, keeping the table and visualization connected.

## 0:55–1:20 | Locate only what the structure supports

This is the public experimental reference, not a predicted mutant. A32 has no atoms here, so BioPilot shows sequence context without inventing a location. Selecting S108 highlights author residue seventy-seven. The three protected catalytic sites have distinct colors.

## 1:20–1:40 | Inspect provenance

Evidence records the structure source, chain, checksums, and residue correspondence. Run provenance connects the displayed candidates to saved computation. These checks support traceability, not validated stability, activity, or binding changes.

## 1:40–1:55 | Switch to a new review

New Review is a separate execution workflow. It has three stages: input validation, agent execution, and results. Unlike Saved Review, this surface can execute an explicitly approved request.

## 1:55–2:15 | Show a real local refusal

First, request S108A. The local guard refuses this protected-site substitution before sending any model request. This is an actual input check, not a new Meta decision. Protection itself does not prove retained function.

## 2:15–2:45 | Prepare a valid request and inspect execution gates

Now enter A32V. Local validation prepares a review without executing it. Confirmation shows full-reference positions, the checkpoint, request limits, and unverified provider cost. A new run requires arming, cost acknowledgment, and Execute. We stop before execution in this recording.

## 2:45–3:00 | State the contribution and limits

Saved evidence and new execution remain clearly separated. ESM preference is not experimental heat tolerance or proof of biological improvement. BioPilot makes candidate review inspectable while preserving human judgment.

## Recording boundaries

- Saved Review is REPLAY of real stored evidence. New Review demonstrates local validation and preflight only in this version.
- Keep the source/mode badges and unknown cost visible. Call caps are not a verified currency ceiling.
- Use the recorded provider/model shown in Agent Trace. Do not relabel the model or invent a Meta rationale.
- Show the experimental 1ISP reference. A32 has no atoms; do not use ESM3/ESMFold2 predictions to fill that gap or imply a measured variant effect.
- Full-reference one-based numbering and full_212 scoring remain fixed. S108/D164/H187 are protected; that is not a function guarantee.
- The guided tutorial is a separate optional walkthrough. For this timed recording, navigate the real controls manually; do not run the full guide and then repeat it.
- Record genuine cursor movement, selection, panel opening and two seconds of 3D rotation. Use short cuts between screens; do not animate a static image as if it were a running job.
- This script makes no workflow-speed, biological-gain, competition-eligibility, or final-submission claim.

## If actual new execution is added later

Treat it as a different recording version. Obtain the corresponding live-call approval, verify the actual run/model/score artifacts, and replace the final preflight segment with that real recording. Label any removed waiting time. Show the returned running/failed/partial/completed state as it actually occurred; do not promise completion or reuse test fixtures. Replace “We stop before execution” and regenerate captions only after that evidence exists.

Before delivery, measure the exported file duration, narration, captions and legibility. A 180-second timeline is not a verified 180-second MP4.
