# BioPilot Bench — unified workflow, current 180-second script

One app: upload → request → local validation → explicit execution → results → recent reviews. English narration: 304 words. The included actual execution used3 Meta requests and45.48 seconds. This is a recording/edit plan, not an exported video. Opening the stored result sends no new request.

Actual evidence: `validation/unified_review_execution_20261029.json`; portable playback: `demo/artifacts/unified_review_20261029.replay.json`.

| Time | Screen | Purpose |
|---|---|---|
| 0:00–0:15 | New review / Input | One workspace |
| 0:15–0:35 | New review / Upload FASTA | Upload and check a constraint |
| 0:35–0:55 | New review / Confirm this review | Validate before approving execution |
| 0:55–1:15 | Recent reviews / completed uploaded-input run | Show the real execution record |
| 1:15–1:40 | Review Results / Candidates | Compare the returned candidates |
| 1:40–2:05 | Review Results / Structure | Inspect supported structural positions |
| 2:05–2:25 | Review Results / Agent Trace | Inspect what Meta requested |
| 2:25–2:45 | Review Results / Evidence | Connect input to evidence |
| 2:45–3:00 | Recent reviews / completed result | Reopen without rerunning |

## 0:00–0:15 | One workspace

BioPilot Bench connects a protein file, a review request, and traceable results in one workspace. This demonstration uses the registered public Lipase A reference.

## 0:15–0:35 | Upload and check a constraint

Upload the full-reference FASTA and describe the variant. A request for S108A is refused by the local protection guard. No model request is sent, and the file is never silently replaced with another protein.

## 0:35–0:55 | Validate before approving execution

A32V passes local validation. The confirmation connects the uploaded file hash to position thirty-two and the pinned ESM checkpoint. Execution requires separate permission and cost acknowledgment. Call limits are enforced; actual provider billing remains unverified.

## 0:55–1:15 | Show the real execution record

Here is the recorded execution of that uploaded input. Muse Spark made three Meta requests, using MCP validation and local ESM scoring. The run completed in about forty-five seconds; waiting is omitted from this edited demonstration.

## 1:15–1:40 | Compare the returned candidates

The result contains nineteen alternatives at the approved position, ranked by one common code policy. Compare candidates without changing their saved scores or ranks. Select A32V and carry the same selection into Structure.

## 1:40–2:05 | Inspect supported structural positions

The public experimental reference has no atoms for A32, so no location is invented. S108 maps to author residue seventy-seven and can be highlighted. The protected catalytic sites have distinct colors; this reference view does not establish a mutation effect.

## 2:05–2:25 | Inspect what Meta requested

Agent Trace shows Meta’s actual validation and scoring requests, with bounded arguments and public evidence. Meta selects the permitted tools and explains the result. Code owns the constraints, computation, and ranking.

## 2:25–2:45 | Connect input to evidence

Evidence connects the uploaded input receipt to the saved report and score artifact. Structure sources, chain, and residue correspondence remain inspectable. These local checks support traceability; they do not prove stability, activity, or retained function.

## 2:45–3:00 | Reopen without rerunning

Recent reviews reopen the same evidence without another model call. New input, deliberate execution, and saved results now share one workflow. ESM preference remains sequence evidence, not experimental heat tolerance or proof of biological improvement.

## Recording scope

- Use one URL: http://127.0.0.1:8522/. The8523 bookmark only links to it.
- The default edit shows current local intake checks and the separately recorded actual uploaded-input execution. Label that transition “Recorded execution ·45.48s elapsed · waiting omitted”.
- The corrected live run was invoked through the same execution backend after browser control became unavailable, then reopened in the actual UI. Do not claim an uninterrupted end-to-end browser recording exists.
- Do not animate a fabricated Execute click, progress or completion. A new recording of fresh paid execution requires corresponding approval and its own real receipt.
- The first precondition failure is preserved. It made zero Meta reservations and is not the completed run. No test fixture is scientific evidence.
- New Review has a five-step local tutorial; results have the existing nine-step replay tutorial. Both are separate optional walkthroughs. Do not run both in full inside this timed main demo.
- Both guided buttons use the same neutral/teal secondary style. The new guide never changes the draft, creates a review or arms execution.
- Only the registered public full_212 FASTA is executable; optional structure upload must match the pinned public mmCIF. Arbitrary proteins/PDB conversion are unsupported.
- ESM preference is not T50, activity, solubility, Tm or experimental validation. Provider billing is unknown. New video duration/audio/caption sync must be checked after export.
