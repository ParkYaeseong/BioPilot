# Review workbench and policy-workflow evidence

Date: 2026-10-28 KST. User authorized the recommended UI/workflow improvement,
then requested GitHub co-science references and Vercel-like styling. This records
implementation choices within that authorization; no repeated approval gate is added.

## Intent and claim

Make a scientist's task, actual Meta tool decisions and artifact-derived candidates
understandable during a three-minute demonstration. Retain Streamlit and the
controlled Python host. The baseline claim review already narrowed the product to
an unvalidated sequence evidence assistant; no phenotype or time-saving gain follows.

## Approaches

1. Polish the saved JSON viewer: least work, but little task context or interaction.
2. **Selected: one Streamlit review workbench**, with task context, recorded trace,
   candidate comparison/export and actual offline input checks. Reuses the existing
   runtime boundary and is suitable for screen recording.
3. New React/Next.js service or a co-scientist fork: unnecessary framework/provider
   expansion for this project's agreed local scope. No deployment is authorized.

The user's instruction to proceed covers option 2. Styling is a developer choice
in response to their Vercel/co-science steering, not a claim of a new provider host.

## References and reuse

- https://github.com/K-Dense-AI/k-dense-byok — task workspace and artifact inspection;
  repository LICENSE was inspected as MIT. No implementation or assets are copied.
- https://github.com/K-Dense-AI/scientific-agent-skills — procedural scientific skills,
  not a ready-made UI; do not import its broad tools into this product.
- https://vercel.com/geist/stack and https://vercel.com/geist/typography — monochrome
  hierarchy, borders, compact status badges, readable tables and disclosure panels.
  Use original local CSS and system fonts; no font/asset download or brand copying.

## Screen and interaction contract

Desktop-first, usable at 1280x720 and 1440x900, responsive narrow layout. Use a
neutral dark default with system-font typography, high-contrast text, thin borders,
small teal/amber semantic accents, visible focus and native accessible controls.
Offer light/dark appearance using local CSS/tokens. Do not claim a full WCAG audit.

First view: a task-oriented title, compact REPLAY/source/model/cost information,
registered target/goal/full-reference numbering/protected positions, and the first
five candidates. Keep raw IDs, hashes, full JSON and repeated per-row provenance
inside named disclosure panels. The science limit remains concise and always visible.

Three sibling views may be used: Overview, Decision trace, Evidence. Candidate
inspection stays reachable from the overview. Every playback view says saved run;
no fake progress, countdown, simulated new decisions or new-compute button.

- Display recorded tool names, short `reason_brief`, bounded arguments, outcomes
  and exact order. Only public trace fields; no private reasoning. Step navigation
  changes the selected saved event and never dispatches work.
- Render candidates/ranks/scores directly from the saved artifact. Default top five,
  optional full cohort, choose up to three for side-by-side inspection. Preserve
  original ranks and one common score policy. No recalculation or silent reranking.
- Download CSV generated from displayed artifact rows with formula-injection
  protection for strings; numerical negative scores remain numerical values.
- A clearly separate **Offline input check** accepts a variant and declared frame,
  calls the same registered target/variant guards, and returns a plain explanation
  for WT mismatch, protected residue, invalid frame or unsupported goal. It makes
  no model call, does not modify the saved run and never implies Meta chose a response.
- Original LIVE provenance, current REPLAY mode and synthetic fixtures remain distinct.
  Unknown cost, geometry and efficacy stay unknown/false as specified.

## Workflow evidence contract

Freeze a six-scenario **policy intake** protocol before running the local fixed arm:
valid A32V; mature numbering; protected S108A; WT mismatch G32V; unsupported activity
objective; unavailable atom geometry. Outcome correctness includes proper refusal
or limited scope. These are intake tasks, not completed ESM reviews.

Record actual local fixed-guard outcomes and wall times. Manual and Meta arms have
not been run under these matched conditions: retain their missing cells, null times,
null interventions/cost, and common denominators. Prior scientific Meta integration
may be linked as separate evidence, never pooled as a matched arm or workflow gain.
No labels, assay outcomes, evaluation metadata or final metrics are provided to the
prediction host/MCP/worker. No human-effort or biological advantage is fabricated.

## Non-goals and permission boundary

No new provider call, GPU, ESM inference/download, external sequence upload, cloud
service, publication or submission. A future matched Meta run needs a concrete
bounded plan and corresponding explicit approval. No broad file/shell/URL tools.
Keep original source/run hashes and pre-event provenance. Preserve old video/ZIP;
create versioned local artifacts after inspection. A recording of replay is labeled.

## Verification and handoff

Write behavioral failures before code. Verify actual Streamlit interactions with
AppTest and browser screenshots, pure read-model isolation, guard refusal, selection
and CSV ordering/safety, honest trace modes and missing-arm reporting. Run the full
suite and package validator. Update STATUS/DECISIONS and current submission evidence;
regenerate source manifest and a new private source ZIP after all source edits.
