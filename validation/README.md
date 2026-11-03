# Verification evidence

This directory keeps compact scientific execution receipts, checkpoint/source hashes,
and major integration/reproduction checks. Records describe the run at their recorded
date; they do not imply that every integration is currently configured.

- `integration_success_20261027.json`: actual Meta -> MCP -> local ESM execution.
- `optional_science_runtime_20261028.json`: stored ESM3 / ESMFold2 GPU execution and
  prediction hashes. The read-only structure viewer uses this file.
- `atlas_registered_reference_20261028.json`: exact registered-reference Atlas lookup.
- `real_esm150_position32_*.json`: actual scoring inputs, scores and review receipts.
- `unified_review_execution_20261029.json`: unified uploaded-input review execution.
- `clean_workbench_reproduction_20261102.json`: isolated offline reproduction.
- `video_quality_recapture_20261103.json`: actual execution used in the edited demo.
- `history_v2/`: preserved original label-free provenance and version-two checks.

Individual root-level pytest output logs are local development output. They were
preserved byte-for-byte under ignored `local_artifacts/repository_cleanup_20261104/`
and removed from the current source tree. Earlier Git commits retain their history.
New logs belong in `.cache/` or `local_artifacts/`, rather than this public folder.

Run the current tests and package checker yourself; stored receipts are historical
evidence, not a substitute for fresh verification. See [reproduction instructions](../submission/REPRODUCE_KO.md).
