# BioPilot Atlas v3 verification receipt

Revision: 2026-10-27. Scope: the complete design/prompt/configuration pack and its offline helpers.
**This is not a working application, a live MCP compatibility test, or evidence of protein improvement.**

## Executed checks

`python -m unittest discover -s tests -v` passed **69 tests**:
- 39 preserved v2 scientific-contract tests.
- 25 v3 offline tests for MCP catalogs/capability filtering, provider schema conversion,
  evidence-mode labels, runtime source-path isolation, weighted self-review scores and video timing.
- 5 real subprocess checks of the package validator on the intact package and deliberately changed
  copies (catalog drift, wrong rubric, evaluator exposure, and an overlong recording plan).

`python checks/validate_package.py` passed before packaging. It checks syntax, schemas/examples,
canonical prompt consistency, source-reference IDs, offline permissions, sequence/mapping guards,
MCP/native catalog agreement, captured rubric, timezone conversion, prize arithmetic, prompt inventory,
recording-plan duration and unverified-submission flags. After MANIFEST.sha256 is written, it also
checks file hashes, path safety and manifest completeness. Its assertion count varies with file count;
it is not a count of scientific experiments or validated capabilities.

The sequence/reference artifacts, target profile, residue map, isolated assay metadata, biological
correction documents and scientific helper/tests were byte-compared with v2. Exact hashes and results
are in `validation/preserved_v2_science.json`. Their preservation does not independently reconfirm
any outside source, atom coordinates, assay measurement or biological result.

The new helper tests and validator regression tests were first run against the old/missing behavior
and failed. Actual red and green outputs are retained under `validation/`. The earlier v2 receipts are
under `validation/history_v2/`; they describe only that historical version.

## What these checks do NOT establish

No live Meta API call, actual Muse Code host connection, MCP protocol session, ESM inference,
GPU creation, live Atlas retrieval, PDB atom mapping, row-level assay reconciliation, biological
benchmark, website rendering, audio recording, video duration inspection, repository publication,
credit/card verification, eligibility decision or submission was performed in this revision.

The offline catalog adapter is not an MCP transport. Runtime source-path checks are not a sandbox:
a future application must also restrict real filesystem permissions, resolve symlinks safely and
inspect source content. No model-output resistance to prompt injection has been measured here.

The 180-second storyboard is arithmetically checked; the actual future recording can still exceed it.
The 30/25/20/25 rubric is a captured official-guide requirement, not a prediction of judge scores.
All proposed outcome and workflow measurements remain unset until actually performed.

## Source freshness

The official hackathon guide was directly read earlier in this conversation. The current Browser
connection failed and the guide could not be freshly retrieved here. The rule snapshot explicitly
records that limitation. MCP architecture was checked from official web documentation; Muse Code
support was checked from an official changelog search excerpt, not the installed application.
Scientific references are inherited from v2 without a new biological source audit. Confirm the final
rules/form, real model IDs, provider billing and installed SDK/host compatibility before use.

## Reproduce after extraction

Install `requirements-checks.txt` only in an authorized environment if its dependencies are absent.
Then run from the extracted package root:

```bash
python -m unittest discover -s tests -v
python checks/validate_package.py
```

The checks do not require API keys or paid network calls. The subprocess regression tests create
and remove isolated temporary copies. Ignore generated __pycache__ files when repackaging.

Read `OPEN_ISSUES.md` before making any scientific, compatibility or competition-compliance claim.
