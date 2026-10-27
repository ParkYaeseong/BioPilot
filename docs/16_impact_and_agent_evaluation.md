# 16. Impact and agent evaluation: prove the right benefit

## Three questions, not one inflated score

1. Does the fixed ESM score rank this assay's measured outcomes usefully? Apply docs/04 unchanged.
2. Does Meta help a user complete a review under changing constraints and failures?
3. Can a judge inspect the same results, evidence and cost record without trusting narration?

Same candidates + same frozen ESM rank policy can yield identical ranking with and without the
agent. That is expected. Do not report biological improvement from better explanations or more tools.

## Strong comparison arms

A: operator runs the same deterministic tools/commands, with clear instructions.
B: fixed orchestrator with the same guards, caches, candidates and resource ceilings.
C: Meta-driven MCP host over the same tools/guards.
D, optional: plain chat/narration baseline, clearly weaker and not the only comparator.

Do not give C extra candidate labels, a larger GPU budget or warm caches while others are cold.
Preserve failures and incomplete outputs in denominators. Separate operator time, model latency,
GPU latency, source retrieval time and total wall time. The easiest task may not need an agent;
report null/negative utility rather than designing the baseline to fail.

## Proposed scenario suite (targets, not measured results)

Ten cases: valid request; ambiguous full/mature positions; WT-residue mismatch; protected mutation;
unsupported goal; unavailable Atlas; constrained optional budget; provider timeout; cancellation and
resume; source prompt injection. Repeat selected nondeterministic cases with prespecified seeds
and a fixed model/prompt version. A 20-run target is a development target, not an existing sample.

Primary workflow metrics: task completion with a reviewable artifact; constraint-violation count;
evidence coverage; human interventions; unnecessary expensive calls; wall/operator time; model/GPU
cost, with unmeasured fields null. Define a successful task as the correct outcome, including a
proper refusal/clarification/partial result when complete execution is invalid.

## Attribution to Meta

Log the short model decision, exact tool call, server decision and result. Show a valid request where
the model changes its next permitted action in response to a real tool result. Also demonstrate that
the server would reject unsafe calls from any host. Do not call deterministic validation an LLM invention.
Do not force a bad LLM action to make the guard look useful; label deliberate adverse-input tests.

## Biological results and leakage

Prepare data in a separate process. Freeze candidate IDs, prompt/policy, scoring context and metrics
before evaluation. Join predictions to labels only in the evaluator. Never expose the numerical
cutoff, outcome-bearing paper sections, or aggregate held-out metrics to the prediction session.
Retrospective public benchmark results are not wet-lab validation and may be affected by pretraining
memorization. Site-aware split and uncertainty requirements in docs/04 remain authoritative.

## Reporting

Use blank templates under submission/ and demo/. A result line needs an artifact/run hash, cohort,
measurement conditions and comparison scope. Use 'not measured' instead of 0 or an attractive guess.
Claims such as 'saves X minutes' require measured comparable trials; guard tests alone support only
the guard behavior tested. End with the actual next decision supported by the work, not a new-enzyme claim.
