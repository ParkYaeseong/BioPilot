# 12. Biological readiness gates — current review 2026-10-28

| Gate | Required artifact | Current status | What it enables |
|---|---|---|---|
| B0a | Exact full/mature sequence match, hash and triad identities | Verified locally | Registered sequence-only review |
| B0b | Endpoint definition and units; supported objective profile | Definition supplied; no calibrated predictor | T50 framed as a hypothesis |
| B0c | Coordinate file, numbering/atom join | Index join verified 2026-10-28; geometry not validated | Numbering is registered; geometry stays unavailable |
| B0d | Raw/curated reconciliation, actual eligible IDs, transformation audit | Partial retrospective subset evaluated; full-library reconciliation and WT audit unverified | No full-cohort or WT-improvement claim |
| B1a | Real ESM checkpoint/tokenizer smoke test | Real pinned ESM-2 150M CPU computation and integrated MCP run saved | Actual sequence scores with provenance |
| B1b | Development-only ESM baseline with site-aware uncertainty | Retrospective subset: 117 measured variants at 9 sites; 95% bootstrap interval includes zero | Keep unvalidated sequence-evidence scope |
| B2 | Frozen independent evaluation and workflow comparison | Prediction freeze recorded for retrospective subset; independent prospective validation and workflow comparison not performed | No general accuracy, time-saving or agent rank-gain claim |
| B3 | Independent wet-lab validation under relevant conditions | Not performed; outside this prototype | No experimental efficacy claim |

B1a evidence: [real integrated run](../validation/integration_success_20261027.json), checkpoint
`esm2_t30_150M_UR50D`, revision `a695f6045e2e32885fa60af20c13cb35398ce30c`, `full_212`,
CPU/float32, `esm150_masked_v1`. The original run recomputed scores; displaying the saved artifact
now is replay. No new model inference was needed for this documentation review.

The [evaluator-only summary](../validation/site_bootstrap_summary.json) records Spearman 0.288,
95% site-bootstrap interval [-0.058, 0.536], 2000 resamples, and 9 measured sites. The interval
includes zero. The 190-variant frozen subset has 117 measured complete cases and 73 missing
measurements. This is not a full-library, prospective or wet-lab result. Recall@20 was not separately
bootstrapped. It does not establish T50 ranking utility or general performance, and is not a calibrated
temperature predictor. The scope remains `unvalidated_sequence_evidence_assistant`.

B0c is optional for sequence review but mandatory for coordinate-derived statements. Unknown
coordinate fields remain null. Keeping S108/D164/H187 unchanged does not establish retained function.
B0d/B1b do not become complete merely because model scores or unit tests exist. Preserve negative,
null and incomplete results; never replace them with a claim of improved biology.

Local tests verify guards, computation contracts and package consistency. They are not experimental
validation. Evaluation labels, outcome-bearing papers and final metrics remain outside the prediction
agent, MCP catalog/resources, allowlisted host workspace and GPU worker.

## Source and permission gates

Contest eligibility, prior-work reuse, ownership, provider permissions, data/weight terms, credits and
pricing require their own evidence. No biology or package test settles them. Shipped default provider
values stay blocked until verified for the actual execution context; a saved successful run does not
authorize a new call, download, upload, GPU job, publication, deployment or submission.

## Historical snapshot

The original 2026-10-27 design package marked B1a and B1b not performed. Those entries described the
package before the later local inference and retrospective subset analysis. Original source/history
and unfavorable results are preserved. This current table records what the saved evidence now supports.

Apply [the MCP boundary](15_mcp_contract_and_hosts.md) and
[workflow evaluation limits](16_impact_and_agent_evaluation.md) at every host/server boundary.
The evaluator never becomes an MCP tool.