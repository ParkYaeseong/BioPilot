# 04. Scientific computation and evaluation protocol - v2 authority

## 1. Registered question and capability

The initial case is `ESTA_BACSU_Nutschel_2020`, a Bacillus subtilis Lipase A assay [S11, S17].
The product returns ESM-ranked single-substitution hypotheses, evidence and unknowns. It does
not claim to produce a thermostable, active, soluble or industrially validated enzyme.

Two goal profiles are supported: `sequence_plausibility_review` and
`lipase_T50_hypothesis_review`. Both use the same generic ESM sequence score in P0. The second
names the intended retrospective endpoint; it does not create a T50 predictor. Reject other
optimization objectives or explicitly narrow them to an approved profile before execution.
A prose goal must never silently enable a new scientific predictor.

## 2. Target and numbering

Use `reference/target_profile.json`. The ProteinGym reference is 212 aa. The RCSB 1ISP chain-A
deposited sequence is 181 aa and uniquely matches full-reference positions 32-212 [S11, S19].
The sequence identity and correspondence were independently checked locally. This is not a
claim about cleavage mechanism, author residue numbering or modeled atom availability.

The source catalytic triad S77/D133/H156 in mature-sequence numbering maps to S108/D164/H187
in the full reference [S17]. Protect these positions by default in **interactive mode**, plus
user constraints. Preserving them is a conservative constraint, not proof of retained function.
Fail if the registered amino acids or reference hash change.

Use full-reference 1-based numbering for variant IDs and product inputs. Keep explicit mature,
deposited-sequence, label_seq_id, auth_seq_id, insertion-code and observed-coordinate fields.
Only the first two sequence mappings are presently verified. Unknown coordinate values remain
null, never zero, false-without-evidence, or an assumed offset. No coordinate-dependent feature
may run until an exact mmCIF join is verified. 1ISP metadata says 181 deposited and 179 modeled
residues, but it does not identify the missing positions for us [S18].

Updated 2026-10-28: the join was verified from the pinned mmCIF (sha256 `7ab626e5…cc10`) by
`app/core/coordinate_join.py`, so the label_seq_id, auth_seq_id, insertion-code and
observed-coordinate fields are now registered rather than null. The metadata still does not
name the missing positions; the coordinate file does, and they are full 32 (auth 1 ALA) and
full 212 (auth 181 ASN). This verifies index correspondence only. Atom geometry stays
unvalidated, `coordinate_mapping_verified` stays false, and the sentence above continues to
govern every geometry-dependent feature.

The curated metadata range 32-205 is not the mature domain boundary. Do not exclude 206-212
from biological design solely because of that metadata. Conversely, do not add unmeasured
variants to a benchmark denominator. Audit the actual data rows before establishing a cohort.

## 3. Phenotype and units

The endpoint is the reported residual-activity T50 after a 20-minute heat challenge. It is a
curve-derived, assay-specific quantity, not a melting temperature Tm, folding free energy,
specific activity or industrial lifetime [S17]. Keep the assay protocol ID and units with every
experimental value. The model score has no temperature unit.

The source metadata records raw direction +1. Inspect the actual raw-to-DMS transformation;
never assume `DMS_score` is raw degrees Celsius. A positive normalized score is not a positive
WT-relative change. The ProteinGym binary cutoff is a cohort median, not WT. Its numeric value
and the WT-comparison protocol are kept in `evaluation_private/assay_protocol.json`, not runtime
context [S11].

For a WT-relative claim require matched WT and variant conditions, units, reference identity,
measurement provenance and a pre-registered uncertainty rule. Until then report WT improvement
as **unknown**, not false, zero or inferred from the median. The paper's threshold convention is
not automatically a formal p<0.05 test [S17]. Do not invent replicate counts or error estimates.

## 4. Sequence and scoring contract

Accept one FASTA record or one sequence. Normalize whitespace/case, then reject gaps, empty
input, ambiguous residues and characters outside the 20 canonical amino acids in v2. Verify
length and hash; no silent crop or truncation. Product length limit 512 is an engineering limit.
Validate each single substitution against its WT residue. Reject duplicates, synonyms,
multiple substitutions, protected sites and out-of-scope positions in interactive mode.

Baseline checkpoint family: `esm2_t30_150M_UR50D`. Pin implementation and weight checksums before
real inference. Inference context is the **entire 212-aa reference**, with mutations expressed
in that frame. A mature-only 181-aa sensitivity run is a different scoring context and cache key;
it must not replace selected baseline rows or be chosen after observing the held-out labels.

For substitution w->a at full-reference position i:

`s_i(a) = log P(a | x with i masked) - log P(w | x with i masked)`

This is the official masked-marginal construction [S09], used here as an uncalibrated sequence
preference. One masked position supplies all 19 alternatives, so reuse its distribution. Check
BOS/EOS/padding offsets against the actual tokenizer. Use the correct residue-token logits.
WT marginals, pseudo-likelihood, different checkpoints and different sequence contexts are
separate score families, not interchangeable rows. A larger checkpoint is not assumed better.

## 5. Candidate universe and ranking

Distinguish three universes:

- Theoretical mature single-substitution library: 181 x 19 = 3,439 [S17].
- Published curated assay: metadata reports 2,172 variants; actual rows not yet imported [S11].
- Interactive protected subset: at most 200 label-blind eligible variants from a registered
  region, chosen by a deterministic policy and frozen seed.

The 1,267-count difference has no verified row-level explanation in this package. It must not
be labeled 'all inactive variants'. Reconcile raw IDs, numbering, duplicates, missing values,
unmeasurable entries, nonactivity and actual exclusions. Missing activity/T50 is not numerical zero.

Policy `esm150_masked_v1` sorts a common valid baseline score descending, then candidate ID.
All methods use the same eligible cohort and diversity constraints. Do not merge partial 650M
scores into a 150M ranking. Optional evidence cannot silently alter the rank. A mode reproducing
an unrestricted published benchmark must remain separate from the protected interactive cohort;
report the retained counts and exclusions for each. Do not call a restricted run 'all 2,172'.

## 6. Evidence hierarchy and provider identity

Use registered experimental reference structure 1ISP first for reference context [S18]. It is
not a mutant structure and does not validate mutant activity. Its ligand or crystal environment
must not automatically become a biological design constraint.

Atlas is optional comparative evidence, not a required source of reference geometry. Retain
provider, source release, returned accession, query hash, retrieval time, subject identity,
prediction model and source mode. `meta_esm_atlas_2023` and `biohub_esm_atlas` are separate
providers [S10, S20]. Verify each provider's API, IDs, terms and output before enabling it.
Do not call Biohub models Meta models just because they share the ESM name.

If no verified search endpoint is available, use a real provenance-preserving export or return
an explicitly partial ESM-only review. No invented hits or paths. Avoid full-Atlas downloads.
Do not equate sequence/structural similarity with the same function. Any homolog use requires
alignment coverage, redundancy/paralogy checks and a preserved reference-position mapping;
a whole-protein exact-match map cannot substitute for a gapped homolog alignment.

ESMFold remains optional. pLDDT is structural confidence, not thermostability. Folding a homolog
is not folding the mutant. ESM-derived predictions are not independent experimental validation
of ESM-derived ranks. Model-size disagreement is not calibrated biological uncertainty.

## 7. Development and evaluation separation

B0 registers target and endpoint before GPU inference. B1 performs an approved development-only
baseline study before UI expansion. This study can fail to support useful T50 prioritization;
retain the negative result and keep the sequence-review product scope. Do not change targets or
metrics post hoc and advertise an untouched test.

Only an offline evaluator reads labels. Do not mount `evaluation_private/`, source-paper results,
raw assay files, held-out aggregates or review narratives in the product agent. Source metadata
must be whitelisted. No runtime arbitrary browsing of the assay paper. Filesystem isolation does
not establish that a public benchmark was absent from LLM/ESM pretraining.

For any development/tuning of rank, prompts or optional-selection policy, group splits by residue
position and freeze a split manifest before looking at held-out outcomes. Predictive observations
at one site are not independent variants for uncertainty intervals. For a fixed no-tuning baseline,
a retrospective full-cohort evaluation is allowed but must be named as such, not prospective validation.

## 8. Metrics and failure accounting

Define the eligible, labeled cohort before prediction and use it across random, baseline, fixed
workflow and Meta workflow conditions. Optional structure availability must not filter the cohort.
Preserve failed/missing predictions; report completeness. Any complete-case correlation is
secondary and explicitly conditional, not a silent deletion from the primary cohort.

Spearman compares scores and recorded outcomes with average ranks for ties; report undefined
for constant vectors or insufficient observations. Recall@K is overlap with an evaluator-defined
Top-K set divided by K, with a pre-registered deterministic tie rule and cohort-specific K.
Pre-register K <= eligible count. A random size-K list has expected Recall@K K/N in that cohort;
this is a mathematical reference, not an experimental result.

Top-K mean/median raw T50 can be reported only after checking units/transformations. A WT
improvement hit rate is disabled until the WT rule is valid. A median-bin hit rate may be
reported under its correct name but is not WT improvement. Bootstrap by residue site for
intervals; repeated LLM runs are workflow replicates, not independent biological samples.

## 9. Agent contribution and freeze

With the same cohort and `esm150_masked_v1`, fixed and adaptive workflows can return identical
ranks. Evaluate Meta on objective/constraint handling, valid arguments, provenance, failure
recovery, optional computation, latency and cost. Do not attribute biological rank gain to the
agent when no rank-changing method exists. Atlas-on/off under identical ranking tests evidence
utility, not biological accuracy. A new ranking method needs its own development and frozen test.

Freeze target/reference hashes, eligible IDs, mode, protected positions, score definition,
checkpoint, context, prompts, source providers, budget, split, metric/tie rules and script version.
Keep cold/warm cache timings and coding costs separate. Report known and unknown costs honestly.
No performance result is supplied in this package. Single-enzyme findings do not generalize by default.

## v3 transport and judging cross-reference

The biological protocol above remains unchanged. Apply docs/15_mcp_contract_and_hosts.md at
all host/server boundaries and docs/16_impact_and_agent_evaluation.md for workflow impact.
The evaluator is not an MCP tool; a thin UI does not relax any biological or permission gate.
