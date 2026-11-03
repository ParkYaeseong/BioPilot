# BioPilot Bench — submission answers

Prepared November 3, 2026. These are source-backed draft answers, not an inspected
copy of the live form and not a submission receipt. Adjust field lengths to the
actual form. Do not automatically accept legal declarations.

## Project

**Name:** BioPilot Bench

**Track:** Indie Developer

**Theme:** Push the Frontier

**Team:** Solo — Yaeseong Park (GitHub: ParkYaeseong)

**Repository:** https://github.com/ParkYaeseong/BioPilot

**Three-minute demo:** https://www.youtube.com/watch?v=V7jWi7q1ggU

**Final field-by-field answers:** [FORM_ANSWERS_20261103.md](FORM_ANSWERS_20261103.md)

**Reproduction instructions:** https://github.com/ParkYaeseong/BioPilot/blob/main/submission/REPRODUCE_KO.md

**Contribution disclosure:** https://github.com/ParkYaeseong/BioPilot/blob/main/compliance/EVENT_CONTRIBUTIONS.md

## One-line description

A guarded Meta/MCP workbench that turns a public protein-variant request into an inspectable scientific review.

## Problem and solution

Protein-variant review spans file identity, residue numbering, model execution,
candidate comparison and evidence tracing. Misnumbered inputs and unsupported
biological claims can make an otherwise plausible analysis misleading. BioPilot
Bench connects these tasks in one local workbench: upload the registered public
Lipase A FASTA, describe a variant, validate the input, explicitly approve a bounded
run, and inspect the resulting candidates, reference structure, tool trace and provenance.

## How Meta is used

The product uses the Meta Model API with the actual returned model muse-spark-1.3.
Meta selects permitted MCP tools for target validation and scoring, then provides
a bounded evidence explanation. Registered code enforces reference identity,
full-reference 1-based numbering, protected catalytic sites, approvals and budgets;
local CPU ESM-2 150M computes sequence preferences. Code ranks all 19 non-WT
alternatives at the approved position using one common policy. Meta, development
assistants and scientific models are explicitly distinguished in the records.

## What was built during the event

The event implementation includes the controlled Meta/MCP workflow, guarded product
services, provider adapters, durable single-use execution state, unified local file
and request workbench, candidate comparison, reference-structure integration,
inspectable trace/provenance views, guided tours, tests and reproduction package.
Existing planning and guard algorithms, public models/libraries and public scientific
references are disclosed separately. They are not claimed as new model inventions,
newly solved structures or newly authored event dependencies. Original history is retained.

## Evidence and limits

The current demo is exactly 180 seconds and includes actual approved execution.
Its scientific run used 3 Meta requests, 2 MCP calls, local CPU ESM and 19 candidates.
Actual captures are edited with zooms and highlights; waiting is shortened and
saved-result navigation is REPLAY. The narration is AI-generated English, with
English captions and separate English/Korean SRT files.

The executable target is currently the registered public full-length Lipase A
reference, not arbitrary uploaded proteins. S108/D164/H187 are protected for
interactive review. ESM preference is not T50, activity, solubility, stability or
experimental validation. Missing atom coordinates remain absent. No prospective
wet-lab gain or general predictive-performance improvement is claimed.

## Deployment and reproduction

This is a local Streamlit/MCP project, not a hosted public inference endpoint.
The repository provides saved real results and a credential-free offline UI/input
validation route. Real execution requires the entrant's own Meta credentials and
verified local checkpoint configuration. No owner API key or model weights are
distributed. An isolated Windows/Python 3.14 environment on the same PC passed
offline reproduction; another machine and a fresh full live setup remain unverified.

## Development assistance and credits

Yaeseong Park provided the domain goal, scientific constraints, product direction,
review and execution/publication decisions. Codex and Claude substantially assisted
implementation, debugging, testing, documentation and demonstration production.
Dependencies, scientific inputs and licenses are identified in the repository.

## Fields requiring the owner or actual form

Use the authenticated participant identity for contact/Discord/team invitations.
Do not invent missing contact fields, age/residency declarations, contributor rights,
organizer correspondence or mandatory terms. The owner reports that participation
was confirmed; no private correspondence is attached publicly. A required deployed
URL must not be filled with localhost or represented as an available hosted service.
