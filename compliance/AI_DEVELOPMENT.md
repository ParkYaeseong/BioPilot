# AI-assisted development disclosure

## November 3 submission update

See [event contribution boundaries](EVENT_CONTRIBUTIONS.md) for the current new/reused
feature mapping. The owner reports that organizer confirmation of participation was
received; [status and evidence scope](ELIGIBILITY_STATUS_20261103.md). Earlier pending
wording below describes the historical record and is preserved. No separate blanket
reuse ruling or unseen correspondence is invented. The event window supplied by the
participant is October26–November4; existing preparation remains disclosed as reused
relative to this implementation even where dated within that window.

Prepared for repository publication on **2026-10-29**. This is a disclosure written
now from existing records, not a contemporaneous chat transcript or an organizer ruling.

## Product model and development assistants

| Role | Actual use | Evidence |
|---|---|---|
| Product runtime | Meta Model API, requested and returned `muse-spark-1.3`; bounded MCP tool selection and public explanations | [Actual integration receipt](../validation/integration_success_20261027.json), [saved replay](../demo/artifacts/sequence_review.replay.json) |
| Development assistance | Codex helped implement, debug, test, document and prepare demonstrations | Source, tests, [decision log](../docs/DECISIONS.md), [originality ledger](originality_ledger.csv) |
| Additional development assistance | The owner reports local updates made with Claude, including session, structure and tutorial work subsequently reviewed and refined | Owner's development disclosure; not an independently exported Claude transcript |
| Scientific models | ESM2 scoring; separate ESM3/ESMFold2 GPU predictions | [GPU execution records](../validation/optional_science_runtime_20261028.json) |

Codex and Claude are development assistants. They are not hidden substitutes for
the product's Meta runtime. ESM3/ESMFold2/Atlas are separately identified tools or
evidence sources; their use is not presented as additional Muse/Meta API calls.

## Work assisted by AI

Assistance covered the controlled Python host, guarded MCP services, ESM provider
adapters, artifact/provenance checks, failure tests, local Streamlit workbench,
light/dark styles, guided spotlight, local file diagnostics, optional scientific
workers, documentation and edited demonstration. The owner provided the domain
goal, scientific constraints, UI corrections and explicit execution/publication
directions. AI assistance is substantial; this project does not claim exclusive
manual authorship or that every line was independently reviewed by the owner.

Verification consists of recorded automated tests, actual Meta/MCP/scientific
executions and browser inspection, with limits stated in the receipts. It is not
wet-lab validation, a complete security audit, or an eligibility determination.

## Earlier material and new contributions

The v2 preparation and guard helpers are recorded as **2026-10-26** material.
The supplied v3 design package was preserved in commit `5898a2f` on **2026-10-27**.
Implementation commit `c0cb60f` is also from **2026-10-27**. Later work includes the
viewer/session, revised intake guards, real replay, coordinate joins, optional
GPU workers and outputs, Atlas snapshot, UI/tutorial and demonstrations.

Some later work remained uncommitted until publication preparation. New commits
therefore carry their actual publication-time dates. No retrospective daily Git
history, backdated commit, or claim that prior preparation was event-authored is
created. See [development history](DEVELOPMENT_HISTORY.md) and the detailed ledger.
Prior-work allowance and the owner's eligibility remain subject to organizer rules
and any required written ruling.

## What is shared

The repository contains product prompts, code, tests, sanitized execution records,
scientific artifact hashes and this development summary. Private full assistant
conversations, credentials, SSH material, account/billing screens, model weights
and local runtime databases are not included. No full chat export is asserted to
be a mandatory submission item without a verified requirement.

If organizers specifically request development sessions or prompts, the owner can
prepare a separately reviewed, redacted export. A summary is supporting disclosure,
not proof of sole authorship or a substitute for the final submission form.
