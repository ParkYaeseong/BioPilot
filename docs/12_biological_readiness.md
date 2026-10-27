# 12. Biological readiness gates

| Gate | Required artifact | Current status | What it enables |
|---|---|---|---|
| B0a | Exact full/mature sequence match, hash and triad identities | Verified locally | Registered sequence-only review |
| B0b | Endpoint definition and units; supported objective profile | Definition supplied | T50 framed as a hypothesis, not prediction |
| B0c | Coordinate file, numbering/atom join | Not acquired | Geometry stays unavailable |
| B0d | Raw/curated reconciliation, actual eligible IDs, transformation audit | Not performed | Quantitative benchmark stays pending |
| B1a | Real ESM checkpoint/tokenizer smoke test | Not performed | Real sequence scores, not fixtures |
| B1b | Development-only ESM baseline versus random with site-aware uncertainty | Not performed | Evidence for or against T50 ranking utility |
| B2 | Frozen independent evaluation and workflow comparison | Not performed | Scoped retrospective claims |
| B3 | Independent wet-lab validation under relevant conditions | Out of this hackathon pack | Specific experimental claims only |

B0c is optional for an ESM-only sequence review but mandatory for coordinate-derived statements.
B0d/B1b are mandatory before quantitative T50-performance claims. B1a is mandatory before
presenting any score as actual ESM output. A failed B1b does not justify deleting unfavorable
results: ship an honestly scoped evidence assistant or explicitly narrow the claim.

The local tests are executable guards and package-consistency checks, not any B1/B2/B3 result.
The runnable checks perform no model inference or network requests.

## Source and permission gates are separate

Confirm contest rules, ownership, API capability, upload permission, pricing and credits before
the corresponding action. None is settled by a biology test. API docs that were not readable during
this revision remain provisional; never authenticate from a placeholder or claim inherited values
were reverified.

## v3 transport and judging cross-reference

The biological protocol above remains unchanged. Apply docs/15_mcp_contract_and_hosts.md at
all host/server boundaries and docs/16_impact_and_agent_evaluation.md for workflow impact.
The evaluator is not an MCP tool; a thin UI does not relax any biological or permission gate.
