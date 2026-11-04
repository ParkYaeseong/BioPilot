# Examples and saved results

The workbench opens the saved results in `artifacts/` without new inference:

- `artifacts/sequence_review.replay.json`: recorded Meta/MCP/ESM-2 review.
- `artifacts/unified_review_20261029.replay.json`: saved uploaded-input review.
- `artifacts/structures/esmfold2_WT/`: stored ESMFold2 reference prediction and receipt.
- `artifacts/structures/esm3_A32V/`: separate stored ESM3 variant prediction and receipt.

Prediction files are checked against the original run hashes and full-reference
sequence. The model registry is in
[optional_science_runtime_20261028.json](../validation/optional_science_runtime_20261028.json).
Other request/schema examples in this folder are illustrative fixtures, rather than
additional scientific executions.

Historical receipts can refer to `demo/artifacts/`. Those files were relocated to
`examples/artifacts/` byte-for-byte; original scientific records and hashes were
preserved. Submission drafts, filming scripts and publication handoffs stay local.

See [installation](../docs/INSTALLATION_KO.md) and the [documentation index](../docs/README.md)
to run the workbench and configure new execution.
