# BioPilot Bench v3 project instructions

Read START_HERE_KO.md, docs/01-06, docs/10-18 and the 2026-10-27 implementation plan.
This is a design/prompt package, not an existing application. Inspect any real repo before editing it.

## Mission

Build a reusable MCP-based protein-variant review tool for a solo hackathon.
Meta selects permitted tools and explains evidence; code enforces numbering, constraints, budgets,
computation and ranking. A simple local Streamlit viewer is optional; a large Next.js service is out of scope.

## Non-negotiable boundaries

- Preserve the v2 biological contract: full-reference 1-based coordinates; registered full_212 scoring
  context; protect S108/D164/H187 for interactive review; never claim this guarantees retained function.
- ESM scores are sequence preferences, not T50, activity, solubility, Tm or experimental validation.
- Supported goals: sequence_plausibility_review and lipase_T50_hypothesis_review only.
- PDB sequence correspondence is not verified atom geometry. Unknown coordinates stay null.
- Keep the rank policy common across candidates; optional 650M/structure/Atlas annotations do not silently rerank.
- Benchmark labels, raw outcomes, result-bearing papers, evaluator metadata and final metrics stay out of
  the prediction agent, MCP catalog/resources, host workspace and GPU worker. Prompt secrecy alone is inadequate.
- Never expose ProteinGym evaluation or label lookup as an agent tool. Offline evaluation happens after predictions freeze.
- A product MCP server must enforce guards itself even when called from Muse Code, CLI or Streamlit.
  Host-side filtering is an additional control, not the sole control.
- No arbitrary shell, arbitrary URL, file read, SQL, spending or synthesis-ordering tools in the product catalog.
- No clinical advice, pathogen/toxin optimization, institutional/private data or unauthorized resources.
- No live provider calls, GPU allocation, external sequence upload, publication, deployment or submission
  without the corresponding explicit approval. A package update does not grant those permissions.
- No hidden fallback from Meta to another model. Development assistants may differ from the product model;
  final traces must identify the actual provider/model and the newly built functionality.
- API/model/protocol settings and exact Muse Code configuration must be verified against the installed version.
  Never invent working commands or endpoints. Keep null/default-blocked values until verified.
- Cached real results must retain source/run hashes; label replay and synthetic fixtures clearly.
  Render numerical tables from artifacts, not model-written prose. Do not expose private chain of thought.
- Preserve pre-event planning and helper provenance. Do not rewrite dates/history or present this package
  as code newly authored during the event. Record reuse and seek the required organizer ruling.

## Workflow

H0 -> B0 -> C1 -> C2 -> B1 -> C3 -> C4 -> C5 -> E1 -> S1.
Write a failing test, implement a small unit, then run focused and regression tests. Keep actual,
mocked, replayed and unverified integrations separate. No UI expansion before the baseline claim
scope is reviewed. A failed T50 baseline permits a narrower evidence assistant, not fabricated gain.

Existing Muse Code may host the agent when its tool restrictions, runtime workspace and actual
Meta model can be verified. Otherwise use the controlled Python host. Do not implement both hosts
fully or add cloud infrastructure merely to obtain a bonus prize.

At each milestone update docs/STATUS.md and docs/DECISIONS.md with changed files, exact tests,
remaining permission gates, real versus mocked integrations and the next allowed action.
The rule snapshot is not a guarantee of eligibility or a freshly checked final legal rulebook.
