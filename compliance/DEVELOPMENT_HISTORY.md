# Development history and evidence

## November 3 submission update

See [event contribution boundaries](EVENT_CONTRIBUTIONS.md) for the current new/reused
feature mapping. The owner reports that organizer confirmation of participation was
received; [status and evidence scope](ELIGIBILITY_STATUS_20261103.md). Earlier pending
wording below describes the historical record and is preserved. No separate blanket
reuse ruling or unseen correspondence is invented. The event window supplied by the
participant is October26–November4; existing preparation remains disclosed as reused
relative to this implementation even where dated within that window.

This document was prepared on **2026-10-29** from existing Git and artifact records.
It does not retroactively create dated development commits.

| Date recorded | Material | Evidence and qualification |
|---|---|---|
| 2026-10-26 | v2 preparation and scientific guard helpers | [Originality ledger](originality_ledger.csv); exact eligibility/reuse ruling remains pending |
| 2026-10-27 | Supplied v3 design package preserved | Actual commit `5898a2f` (`chore: preserve supplied v3 design package before implementation`) |
| 2026-10-27 | Guarded MCP core, controlled host and ESM providers | Actual commit `c0cb60f` (`feat: implement guarded MCP review core and explicit ESM providers`) |
| 2026-10-27 | Actual Meta → MCP → ESM2 execution | [Recorded receipt](../validation/integration_success_20261027.json); requested/returned `muse-spark-1.3`, three requests, nineteen candidates |
| 2026-10-28 | Viewer/session, coordinate join, verifier, spotlight and validation refinements | [Milestone log](../docs/STATUS.md), [decisions](../docs/DECISIONS.md), tests and versioned records; much of this was not committed individually |
| 2026-10-28 | Exact-WT Atlas acquisition and two actual optional GPU predictions | [Atlas receipt](../validation/atlas_registered_reference_20261028.json), [GPU receipt](../validation/optional_science_runtime_20261028.json); separate from the older Meta trace |
| 2026-10-29 | Repository publication preparation | Current-date commits, hygiene checks and documentation; not a claim of work performed on an earlier date |

Git timestamps and local artifact dates are useful provenance, not cryptographic
proof of creation time or eligibility. Earlier design/helper reuse is disclosed;
we do not claim that all repository content was newly made during the hackathon.
The exact new contributions are described in the source, milestone log and ledger.

No history is squashed or rewritten to conceal the planning package. Published
snapshots preserve the original two commit IDs and their real metadata. Repository
creation/upload date and implementation dates are different events.
