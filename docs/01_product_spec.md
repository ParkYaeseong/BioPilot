# 01. Product specification: verifiable variant review through MCP

## Positioning

**Track:** Indie Developer. **Primary theme:** Push the Frontier. **Alternative:** Build for Your World.
The themes are problem statements, not the Indie/Startup competition tracks. No theme-specific
prize pool or easier theme is established by the captured guide [S21].

BioPilot gives a Meta model bounded access to scientific computation, with human-approved constraints
and inspectable evidence. This targets research-workflow acceleration, not an assertion that a new
protein model or improved enzyme has been discovered. If only a convenient wrapper is achieved,
frame the work as domain workflow assistance rather than claiming a research breakthrough.

## User and output

A researcher reviews single substitutions of a benign public Lipase A reference. Input includes
an explicit coordinate frame, protected positions, top K and approved optional-work limits.
Output includes actual ESM sequence scores, a deterministic shortlist, registered reference evidence,
unknowns, model/source hashes, cost status and exports. No synthesis, clinical or autonomous wet-lab action.

## Core experience

1. User opens a prepared run context in a controlled Meta host or verified Muse Code session.
2. The app validates the target and coordinate frame. Ambiguity causes a correction request, not a guessed offset.
3. Meta chooses a permitted analysis action and gives a short evidence-linked reason.
4. The server enforces constraints, permissions and budgets; ESM computes real scores.
5. Meta requests useful optional evidence or finishes when that evidence is unavailable or over budget.
6. Code ranks candidates and renders numbers; Meta explains what is and is not supported.
7. The user inspects results in the host/CLI and optionally a small local viewer.

## P0 and non-goals

P0: target validation, actual ESM computation, one actual Meta-driven MCP tool round trip, persistent
run ledger, guarded operations, deterministic exports, and a reproducible demo with clear limitations.
An offline evaluation protocol is required; numerical biological claims require actual reconciled data
and executed evaluation. If unavailable, report that gap rather than inventing a benchmark.

P1: verified Atlas retrieval, 650M annotations, one optional exact-candidate structure prediction,
3D rendering, hosted read-only demo, and alternative open-weight runtime. None may block the core.

Excluded: mandatory Next.js/FastAPI web platform, installers, multi-agent swarms, whole-Atlas indexing,
new foundation-model training, routine wet-lab procedures, automatic synthesis, patient advice,
institutional integrations and open public billed endpoints.

## Approaches and decision

A new website maximizes UI control but consumes solo development time. MCP-only offers reusability
but may obscure value in a short video. The selected package default is **MCP first, one real Meta host,
optional thin Streamlit results viewer**. A controlled host is the reference path for strong budget and
label isolation; existing Muse Code is a compatible-host option after practical verification [S22-S23].

## Scientific contract and success

Preserve docs/04 and docs/10-12. Both supported goals use generic ESM preference in P0, not a phenotype
predictor. The target, scoring context, checkpoint and candidate cohort must be explicit.
Success means a real, auditable review with safe failure behavior. Quantified time savings, biological
gain and higher accuracy are empirical questions, not pre-filled pitch claims.

## Evidence for the rubric

Impact: a concrete research job and measured orchestration/inspection effort.
Meta tooling: decisions leading to actual MCP calls and a changed plan under constraints.
Technical execution: numbering, artifact lineage, recovery, budget and data isolation.
Demo: three understandable minutes of real input, execution and output.
Use docs/16 and submission/evidence_matrix.json; never award this prototype a fictitious judge score.
