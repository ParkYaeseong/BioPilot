# Overview-first review implementation plan

**Goal:** Make the saved review understandable before asking a viewer to inspect
candidate details or enter diagnostic data.

**Architecture:** Keep the current Streamlit program, artifact read model, guarded
local diagnostics and separate live session. Add a small overview renderer and
reuse the existing candidate, trace, provenance and structure renderers.

**Tech stack:** Existing Python/Streamlit and local CSS/JavaScript; no new dependency.

**Spec:** The owner's ten-point request on 2026-10-29. This is an implementation
record for that explicit direction, not a new scientific objective.

## Decisions and constraints

- Five views, in order: Overview, Candidates, Agent Trace, Evidence, Input & Diagnostics.
- Overview describes the current review purpose; the missing original objective
  stays missing. Numerical rows, counts, provenance and trace come from the artifact.
- Reference mapping & saved structures is an Evidence subview. The registered
  join and actual saved predictions remain distinct from geometry/biology validation.
- FASTA/mmCIF and advanced numbering checks remain local and appear only in diagnostics.
- Nine English spotlight steps traverse real views and preserve/restore selections.
- No provider, GPU, new retrieval, public-release or contest-submission action.
- Preserve all existing scientific artifact bytes, original source hashes and common rank.

## Tasks and verification

- [x] Capture the old screen at desktop and mobile sizes before editing its renderer.
- [x] Add failing behavioral tests for a summary landing view and five-view navigation.
- [x] Split the existing shortlist into Candidates; add Overview and nested Evidence.
- [x] Update tour states and tests for actual navigation/selection/restoration.
- [ ] Add responsive containment and inspect 1280, 599 and 390 pixel widths in light/dark.
- [ ] Capture actual updated screens, refresh tour thumbnails and document a 180s demo path.
- [ ] Run focused tests, full regression, package checks and compare the 135 baseline hashes.
- [ ] Update STATUS/DECISIONS, source manifest and the authorized private GitHub repository.

## Review focus

Incomplete/synthetic/tampered runs must retain their existing warnings. Missing
recorded objectives must not become invented requests. Old navigation session
values must resolve safely. Structure steps must select the right Evidence
subview. Small screens must keep controls reachable and contain wide tables.
Screenshots and an edited-demo plan do not count as a new inference or video export.
