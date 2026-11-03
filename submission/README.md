# BioPilot Bench — local submission draft

## November 3 final preparation

[Ready-to-copy form answers](FORM_DRAFT_20261103.md),
[new versus reused contributions](../compliance/EVENT_CONTRIBUTIONS.md),
[owner-reported participation confirmation](../compliance/ELIGIBILITY_STATUS_20261103.md),
and [current quality-corrected media upload](demo_release_quality_20261103.json)
supersede the corresponding earlier preparation status below.
The live submission form is not yet inspected: browser access is blocked by a saved
site permission. No submission or acceptance of legal terms is claimed.

## Current submission entry — 2026-11-02

The current-UI **180-second English-narrated MP4** has now been exported locally.
See [video guide and scope](../demo/FINAL_VIDEO_20261102_KO.md) and
[technical video receipt](video_current_ui_20261102_receipt.json). It uses actual
browser captures, edited zoom/pan/highlights and synthetic narration, with recorded
scientific execution clearly labeled. The MP4 and EN/KO SRTs are now available as
[private Release assets](https://github.com/ParkYaeseong/BioPilot/releases/tag/demo-2026-11-02),
separate from Git source history. [Remote upload verification](demo_release_20261102.json).
Raw captures stay local. Public release, full human listening review and unauthenticated
video access remain pending.

Use the **unified workbench** in `app/bench.py`, not the historical separate
viewer/session launch commands below. New review → FASTA/request → validation →
explicit execution approval → results → Recent reviews is one local app.
Results use Overview / Candidates / Structure / Agent Trace / Evidence.

- [Judge reproduction instructions](REPRODUCE_KO.md): fresh isolated Windows
  Python 3.14 environment and separate source copy passed all five rendered views,
  S108A refusal and A32V validation. No credentials or weights were copied. This is
  offline UI/intake verification on the same PC, not new live execution or a second PC.
- [Current actual execution receipt](../validation/unified_review_execution_20261029.json):
  `muse-spark-1.3`, 3 Meta requests, local CPU ESM-2 150M, 19 candidates, 45.48 seconds.
- [Current portable replay](../demo/artifacts/unified_review_20261029.replay.json)
  preserves the score/trace and original report provenance. Opening it is REPLAY.
- [Current bilingual 180-second script](../demo/REVIEW_FLOWS_180S_KO.md) and
  [final recording checklist](../demo/FINAL_RECORDING_CHECKLIST_KO.md). Earlier MP4s
  below remain historical drafts; use the current-UI export and receipt above.

```powershell
.venv/Scripts/python.exe -m streamlit run app/bench.py --server.address 127.0.0.1 --server.port 8522 -- --state-dir .runtime/bench --max-runs 3 --max-requests 4
```

This working-environment command can expose approved execution only when the
owner's trusted Meta and pinned local ESM configuration is present. Judges use
the separate offline installation route above and receive no owner credentials.
Current source: [ParkYaeseong/BioPilot](https://github.com/ParkYaeseong/BioPilot),
private by the owner's decision. Public/judge access, final rules/form, prior-work
eligibility, contributor/rights confirmation, final video review and submission
receipt remain open. Do not infer completion from source upload or tests.

## Preserved earlier preparation and video records

Prepared on 2026-10-28 (Asia/Seoul). **Not published or submitted.**
Track/theme remain the planning choices Indie Developer / Push the Frontier;
final eligibility, reuse permission and submission requirements need organizer confirmation.

BioPilot is a reusable MCP tool for reviewing single substitutions of a public
Lipase A reference. Meta chooses bounded tools and explains evidence. Python
checks coordinates, protected sites, approvals and budgets, computes ESM sequence
preferences and produces a deterministic shortlist. The current claim is an
**unvalidated sequence evidence assistant**. It is not a validated enzyme optimizer.

## Inspect the working evidence

The saved integration receipt is [integration_success_20261027.json](../validation/integration_success_20261027.json).
It records one actual Meta → MCP → local ESM → final explanation execution, using
`muse-spark-1.3`, the controlled Python host, MCP SDK 1.25.0 / protocol 2025-11-25,
and `esm2_t30_150M_UR50D` on CPU in the registered `full_212` context.
The measured fields, source hashes and limitations are collected directly from
artifacts in [evidence.current.json](evidence.current.json).

The portable [saved review](../demo/artifacts/sequence_review.replay.json) contains
the actual ranked candidates, score artifact, provenance, tool trace and model
explanation. Its original computation was live; opening this copy is **REPLAY**.
The export records the original report hash and retains the original score hash.
No model request, model download, GPU job or sequence upload is needed to inspect it.
Actual provider billing remains unknown; a local reservation is not an invoice.

From the project root in the existing Windows environment:

```powershell
.venv/Scripts/python.exe -m app.cli validate --variant A32V
.venv/Scripts/python.exe -m app.cli validate --variant S108A
.venv/Scripts/python.exe -m streamlit run app/viewer.py -- --artifact demo/artifacts/sequence_review.replay.json
```

The second command must exit 2 with `status: blocked`: the catalytic residue is
protected. The viewer is bound to localhost and only reads saved artifacts.
For an actual fresh local MCP round trip and the full verification commands, see
[IMPLEMENTATION_KO.md](../docs/IMPLEMENTATION_KO.md) and [the recording guide](../demo/README_KO.md).
Tested dependency pins are in `requirements/dev.txt`, `requirements/science.txt`
and `requirements/viewer.txt`. The current `.venv` reuses system packages;
**installation into a clean environment has not been verified**.

Fresh Meta execution is a separate approved action. `MODEL_API_KEY` or
`META_API_KEY` stays in the owner's local environment; judges receive no owner
credentials. Do not run `meta-review`, `meta-smoke`, `esm-score`, `score-local`,
remote GPU or deployment commands merely to inspect the replay. Native Muse Code,
RunPod and a deployed Modal worker are unverified. Atlas has a pinned exact-WT snapshot,
and separate ESM3/ESMFold2 operator-worker executions are recorded in
[the actual GPU receipt](../validation/optional_science_runtime_20261028.json).
Automatic remote folding through the product MCP remains disabled.
The current remote GPU budget bounds also need reconciliation before any Modal run.

## Scientific and impact limits

Inputs and substitutions use full-reference 1-based coordinates. Interactive
review protects S108/D164/H187. Keeping those residues does not guarantee retained
function. Scores use one common `esm150_masked_v1` rank policy; optional evidence
does not silently rerank candidates. Scores are unitless sequence preferences,
not T50, Tm, activity, solubility or experimental validation. Unknown atom
correspondence stays null; geometry remains disabled.

The evaluator-only [retrospective summary](../validation/site_bootstrap_summary.json)
reports a site-bootstrap interval that includes zero. It does not establish T50
ranking utility or general predictive performance. Missing measurements are not
inactivity. This small public retrospective analysis is not a prospective,
independent wet-lab or full-assay validation. Never mount this summary, evaluator
code, labels or outcome-bearing papers in the product host or GPU worker.

Manual/fixed/Meta workflow time savings have **not been measured**. Meta did not
improve the biological ranking: numerical ranks are computed by the same fixed
policy. The demonstrated contribution is bounded tool coordination and an
inspectable evidence chain. Public-data pretraining contamination remains possible.

## Contribution, rights and final access

The original design package, v2 helpers and source dates are preserved in Git and
`compliance/original_package_manifest.sha256`. Implementation under `app/` began
on 2026-10-27; local submission preparation on 2026-10-28 adds the portable replay,
corrected playback labels and evidence-linked documentation. Do not equate these
dates with an organizer ruling on event originality or eligible reuse.

The original package names Yaeseong Park as owner. Confirm the final contributor
list before submission and disclose Codex assistance. See
[originality_ledger.csv](../compliance/originality_ledger.csv) and
[THIRD_PARTY_NOTICES.md](../compliance/THIRD_PARTY_NOTICES.md).
No new blanket code/data license is assigned here.

[manifest.current.json](manifest.current.json) lists the real artifacts and open
gates. Public repository, video/product links, unauthenticated judge access,
final form, rights and organizer eligibility/reuse decisions remain pending until
actual evidence is recorded. A local draft video or replay is not a public-access
verification or a completed submission. Status stays `not_submitted`.

## Local recording draft

[The 180-second MP4 draft](../local_artifacts/demo/BioPilot_Bench_180s_LOCAL_DRAFT.mp4)
uses edited captures of the actual replay viewer and cards rendered from recorded
local guard results. It has disclosed offline synthetic English narration and
matching captions. It is not a continuous screen recording or a fresh Meta run.
[Technical receipt](video_draft_receipt.json): actual duration, video/audio streams,
source hashes and non-silent audio were checked. The encoded frame inspection sheet
was reviewed locally. Human review of the full audio/video and final contest
requirements remains pending. The video is stored outside the source inventory;
no upload or public-access check was performed.

## Updated interaction video and UI inspection

The newer [180-second 1080p draft](../local_artifacts/polish_demo_20261028/BioPilot_Bench_Polished_180s_LOCAL_DRAFT.mp4)
includes actual sampled browser clicks, local refusals, saved trace navigation and
candidate selection, with disclosed camera/timing edits and offline voice. It is
not a continuous OS screencast or new scientific execution. Technical receipt:
[video_polished_receipt.json](video_polished_receipt.json). Full human review and
public access remain pending. Earlier draft videos/receipts stay preserved.

[The revised local guide](../docs/POLISHED_REVIEW_KO.md) documents the inspected
UI, current launch command and integrity scopes. The verified full regression is
588 passed /2 Windows skips. Hash presence alone no longer appears as authentication;
only available local checks are shown as matched. The separate existing six-case
policy record is fixed6/6, Meta5/6, manual notrun; this is closed-set rule application,
not evidence of research time savings, biological skill or a superior rank policy.


## Latest local review material — 2026-10-28

Use demo/RECORD_SPOTLIGHT_KO.md and submission/video_spotlight_receipt.json for the
new180s spotlight/rotation video. New UI previews are loopback8522/8523; see
docs/WORKSPACE_REFINEMENT_KO.md. Both optional GPU models have actual recorded
results in validation/optional_science_runtime_20261028.json. These remain separate
annotations and do not establish phenotype improvement. Final rules/rights/reuse,
clean-install and public-link gates are unchanged; not_submitted remains correct.
