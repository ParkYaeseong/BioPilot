# Decision log

2026-10-27: Update the full v2 pack with the user's discussed MCP-first direction and optional thin UI.
Keep biological safeguards. Use one controlled Meta host by default, with Muse Code compatibility
as a verified option. Retain strict source-state and evaluator isolation.

Captured rubric is 30/25/20/25, not equal quarters. Track and theme are separate. Design a 180-second
recording plan but do not claim a finished video. Preserve rule-source retrieval limits and prior-work provenance.

No switch to a different theme, new biological predictor, paid fallback or cloud deployment is authorized here.

2026-10-27 implementation H0/B0: user explicitly requested actual Python/MCP code.
No Git repository existed, so preserve the supplied source in a local baseline commit
and work on `implementation/mcp-core-20261027`; preserve the original manifest and
preparation ledger. Exclude .env, private evaluator files, helper folder, venv and
runtime artifacts from Git. Use .venv with installed site packages for this machine;
clean-environment installation is not yet verified. Initial checker failure was source
inventory drift; prune local credentials/environments before inspecting package text.

B0 uses hard registered sequence/hash/frame/protection anchors. Existing v2 pure
sequence/WT algorithms are reused with attribution rather than importing the evaluator
helpers into runtime. Geometry stays blocked; phenotype calibration stays false.
RED/GREEN receipt: validation/implementation_b0_red.txt, 32 target tests passed.

C1 reserves before dispatch and records unknown provider outcomes without automatic
retry. A transactional claim permits one dispatcher. Cost and provider usage are
separate; unknown prices stay null. Twenty policy tests passed.

C2 uses full_212 masked-marginal log ratios, one forward per position, at most ten
positions/190 alternatives. Synthetic logits are fixtures, never real model evidence.
Weights/tokenizer pins and checkpoint architecture are required for local real loading.
Latest user steering permits explicit 35M/150M/650M contexts; each has its own common
rank policy and cannot silently replace/mix the registered 150M baseline.

C3 chooses controlled Python host plus real local stdio MCP. Native Muse Code is
unverified; do not build a second host. Catalog initially publishes validation/status
only. Optional compute is unavailable until backend configuration and authorization.
Runtime allowlist separation is verified; OS ACL isolation is not claimed.

C4 validation smoke is capped at two provider requests, 512 completion tokens each,
with no-tool final response and no retries/fallback. Actual ESM orchestration remains
pending. Reviewer findings for budget exhaustion, malformed usage and rejected-tool
completion were reproduced RED and fixed GREEN; receipts are under validation/.
The first live attempt produced no verified provider response and remains a partial
artifact; the earlier user-reported 120-token smoke was not overwritten or reclassified.

B1 evaluator reads labels only after an independently supplied prediction freeze hash,
outside runtime. Synthetic tests do not establish biological utility. Raw reconciliation,
site bootstrap intervals and real outcomes remain unperformed. Keep the product claim
at an unvalidated sequence evidence assistant until those gates are met.

Backend steering: default Modal, alternate local CPU/CUDA, RunPod explicit unconfigured.
Use one provider protocol and the same MCP score tool; never forward the Meta key or
the whole .env to a scientific worker. No GPU/download/deployment action is authorized
by adding adapter source. Modal SDK/live compatibility will remain unverified unless
tested against an installed version. See the follow-up implementation plan and receipts.

2026-10-27 backend implementation closeout: providers.py defines an exact public-reference
request with no sequence, credentials or evaluator fields. Local and Modal use the same
masked-marginal artifact; RunPod always reports unconfigured. Default Modal does not
grant execution. Factory settings/worker pinning are trusted-launcher operations.
Actual scientific runs require current run approval, cost/GPU budgets and transfer consent.

Reviewer Important findings were fixed with RED/GREEN tests: a never-dispatched RESERVED
job may resume once through the existing claim; UNKNOWN/DISPATCHED never auto-resubmit;
artifact/common/row source modes and provenance must agree; model/pin/position scope is
frozen; remote jobs reserve the supported 900-second worker ceiling until actual deployed
timeout evidence exists. This conservative choice can block a small remote budget; it
prevents pretending a short client wait bounds a longer billed GPU job.

Sequence-review Meta mode is opt-in, keeps the validation smoke unchanged, reserves one
no-tool final response, and renders scores only from verified saved artifacts. Full
review tests are synthetic; no claim of actual Meta+ESM integration follows from them.
freeze_score_artifact projects the verified numeric artifact into the separate frozen
evaluation protocol without exposing labels or evaluator outputs to runtime.

Installed Modal SDK 1.6.2 in the project .venv after local tests passed. Only offline
public API signatures were inspected; no setup/login/lookup/remote/GPU/deploy was called.
The installed SDK matches the optional requirements pin; live compatibility remains false.
Two upstream Python 3.16 deprecation warnings remain informational on Python 3.14.

The package checker now prunes local credentials/environments/helpers before source
reads and uses explicit UTF-8 on Windows. Original distribution manifest and history
remain preserved; the current source manifest is intentionally regenerated for changed
source. Final test receipt and next gates are in STATUS.md and IMPLEMENTATION_KO.md.
