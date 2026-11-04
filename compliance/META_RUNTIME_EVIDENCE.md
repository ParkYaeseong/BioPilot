# Actual Meta runtime evidence

BioPilot uses **Meta Model API `muse-spark-1.3`** in its controlled Python host.
The development assistants and scientific models have separate roles.

The [actual integration receipt](../validation/integration_success_20261027.json)
records the requested and returned model, three Meta requests, a completed
nineteen-candidate review and local ESM2 computation. Its [portable saved record](../examples/artifacts/sequence_review.replay.json)
retains the tool trace, numerical artifact and original source hashes.

The recorded sequence is:

1. Meta requests `validate_target_context`.
2. Registered MCP code checks the approved reference and scope.
3. Meta requests `score_positions`.
4. ESM2 computes sequence preferences; code applies the common rank policy.
5. Meta returns a public explanation of the evidence and limits.

This is actual product-runtime use, not merely coding with an AI assistant or
branding an ESM-only script as a Meta-agent application. The stored viewer is
explicitly **REPLAY**. It does not claim a fresh API call on each click.

No provider API keys, authorization headers, private reasoning, or full account
exports are required to inspect these sanitized records. Billing is unverified.
The ESM3/ESMFold2 runs and later Atlas snapshot are separate, accurately labeled
evidence and are not inserted into the original Meta execution history.

These records support the stated implementation. They do not guarantee the
organizers' judgment of meaningful model use, novelty, impact or eligibility.
