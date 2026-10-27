# ESM provider backend implementation addendum

User-requested implementation scope, 2026-10-27. The existing v3 scientific plan
remains authoritative except for the user's explicit multi-backend/model extension.
No cloud operation, model download or public action is authorized by this plan.

1. Preserve B0/C1 and the actual local MCP transport. Select backend only through
   trusted launcher settings. Default Modal is blocked until configured and approved.
2. Define one immutable public-reference inference request and provider protocol.
   The payload contains reference identity, full positions, model identity and trusted
   pins; it contains no Meta key, full environment, raw sequence or evaluator data.
3. Implement local provider over the same pinned scoring engine; explicit CPU/CUDA.
   Implement Modal submit/poll with durable job IDs. RunPod stays unconfigured.
4. Enforce approval, cap, position/variant limits and idempotency before dispatch.
   Unknown submission does not retry; status reads do not submit or poll jobs.
5. Use explicit esm35, esm150 or esm650 model and matching common rank policy.
   Main independent evaluation may freeze650; baseline150 is preserved. A different
   model/precision/context is different provenance and cannot silently replace rows.
6. Ship a worker callable and guarded deployment factory, no execution on import.
   Worker image includes only reviewed product/science code and public reference;
   preprovisioned pinned weights only, no automatic download or whole-repo upload.
7. RED/GREEN local conformance tests compare fixture-backed local/remote score shapes,
   token mapping, score sign, hashes, failure, timeout and duplicate request handling.
   Injected transports are fixtures, not real Modal integration evidence.
8. Finish regression/package validation, dependency/runtime instructions and status
   ledger. After separate GPU/download/deployment approval, verify the installed SDK,
   provision exact weights and perform one bounded integration test. That test is pending.

Score at full position i: log P(mutant | full reference masked at i) minus
log P(WT | same mask). The shared log-softmax normalizer cancels, giving the
logit difference. Scores are dimensionless sequence preferences, not experimental T50.

Test receipts: validation/implementation_c2_models_*, implementation_esm_providers_*,
implementation_provider_config_*, implementation_modal_worker_* and final regression.
