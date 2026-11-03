# Current status

## Supporting-document layout cleanup — 2026-11-03

Reviewed repository directory roles after owner questioned clutter. Kept checks/
(9small validation/reproduction scripts) and demo/artifacts/ because the package
checks,offline viewer,prediction view and tests use them. Moved14superseded demo
scripts/subtitles/recording guides into docs/archive/demo/ and2Mermaid diagrams
into docs/diagrams/,removing the standalone diagrams directory from current root.
All16moved file hashes are identical. Original manifests/receipts remain unchanged;
docs/archive/demo/archive_paths.json resolves original paths to current locations.
Updated active pointers and added a compact README directory map. Historical
preparation,source history,biological artifacts and runtime paths are preserved.

Validation:82package tests passed with12subtests;fresh-environment offline AppTest
passed5views,19candidates,S108A blocked,A32V accepted,execution disabled without
configuration. Package check2,221passed,0failures. Moved Markdown links and16hashes
checked. No app code change,new model/GPU calls or contest submission.

## README feature walkthrough GIFs — 2026-11-03

Owner requested a richer README with per-feature GIFs. Replaced the long overview
GIF in the README with five focused clips:inline validation and guards,approval/
recorded execution/completion,candidate comparison,reference structure review,
and actual tool/input provenance. Added short captions above each clip and kept
YouTube as the full demo link. Quickstart,scope,contribution and license links remain.

Created docs/images/biopilot-{input,execution,candidates,structure,evidence}.gif
from actual stored captures. Each is840×472,6.8–7.38seconds,under1.7MB;total7,811,064bytes.
The structure clip uses actual rotation frames. Existing fast push-in,rounded box,
dimming and mode-label style retained. No synthetic UI/progress or new provider/GPU
calls. Old overview GIF retained for historical receipt integrity,not duplicated
in the current README. Generation receipt:submission/readme_feature_gifs_20261103.json.

Checked every GIF frame for decoding,infinite looping and changing content;verified
46source screenshot hashes and reviewed15decoded sample frames across all5clips.
README local links15passed;no stale Release link. Product code is unchanged,so the
earlier785-pass app suite is historical;package/source checks run for this media edit.

## YouTube is the primary demo; obsolete GitHub Release retired — 2026-11-03

Owner supplied YouTube video V7jWi7q1ggU after manual upload and requested README
link replacement,Release cleanup and final submission answers. README now links
only to https://www.youtube.com/watch?v=V7jWi7q1ggU in its demo section; removed
Release/MP4/SRT download links. Updated current guides,submission metadata and
field-by-field final answers. Personal survey scores remain owner choices; no
publicity consent or form submission is presumed.

Verified local size/SHA backups of all10Release assets before deleting only the
demo-2026-11-02 Release and its attachments. API now returns404 for that Release;
its Git tag/source object is unchanged. Retained local media and historical upload
receipts. Receipt:submission/demo_release_retirement_20261103.json.

YouTube URL is owner-reported; no independent playback/caption-track verification
is claimed. Current metadata no longer treats the deleted Release as a download
destination. No source history rewrite,new provider/GPU calls or contest submission.
The owner will enter the final answers directly in the form.

## YouTube thumbnail generated and made remotely downloadable — 2026-11-03

Created an illustrative promotional cover with built-in image_gen,referencing the
actual public-reference structure screenshot. Text:BioPilot Bench / Protein Variant
Review / Meta × MCP × ESM /3-MIN DEMO. This AI-generated cover is not an evidence
screenshot or new scientific result. Saved the project asset locally and uploaded
BioPilot_Bench_YouTube_Thumbnail.png to the existing public Release for the owner
to download from another device. PNG1672×941,1,549,229bytes,under2MiB. Remote size/SHA
and anonymous PNG download passed. Full prompt and reference hash retained in
submission/youtube_thumbnail_20261103.json. No YouTube browser access,channel action,
YouTube upload,thumbnail setting,Meta/GPU inference or contest submission occurred.

## YouTube upload kit added to public GitHub Release — 2026-11-03

Owner is away from the recording PC and needs remote downloads. The prior
YouTube-ready MP4/captions/description were local-only; now uploaded five explicit
assets to existing public demo-2026-11-02 Release:YouTube-ready MP4,EN SRT,KO SRT,
English description and a ZIP containing those files plus upload instructions.
Original burned-caption demo assets preserved; no binary added to Git history.
All remote asset sizes and GitHub SHA256 digests match local bytes. Anonymous
HTTP access verified for all5files,including MP4 ftyp and ZIP PK signatures.
ZIP15,982,002bytes;MP4 remains16,425,920bytes/SHA256f4a006d9...69b1b.
Receipt:submission/youtube_kit_release_20261103.json. This is GitHub hosting only;
no YouTube account/channel/upload/watch URL or hackathon submission is claimed.
No new Meta/GPU calls. README's current working demo link remains until a real
YouTube URL is available.

## YouTube upload package prepared; browser permission blocked — 2026-11-03

Owner authorized a project YouTube channel or existing Google account,English
description,selectable Korean captions and replacing the README video link. Browser
access to https://www.youtube.com was denied at the origin approval gate. No
alternate route,account creation,upload,legal acceptance or invented watch URL.
Requested site permission; prepared all independent local media work meanwhile.

Created local_artifacts/youtube_upload_20261103 with180s1080p30MP4,English narration,
no burned dialogue captions,matched27-cue EN/KO SRTs,English description with9chapters,
credits and GitHub links. Original zoom/highlight style and narration retained.
Verified5400frames,whole-file decode,identical decoded audio,7sample frames and
caption source bytes. Current source SHA256f4a006d9e582985e8087e99f10e7d049fd6229dd362a35e213a42d736e169b1b,
16,425,920bytes. No new Meta/GPU calls. Existing Release/video files unchanged.
README link intentionally remains the working Release until an actual YouTube URL
is uploaded and verified. Local metadata/receipt status:prepared_not_uploaded.
Next:restore YouTube browser permission,inspect channel and upload with EN/KO tracks.

## README simplified and actual form answers prepared — 2026-11-03

Rewrote README from207to85lines around the product,demo,features,quickstart,workflow,
scientific scope and contribution/license links. Removed stale private-repository
and unassigned-license statements plus editorial/upload/verification narration.
Detailed provenance,media receipts and contribution disclosures remain in linked
documents. Followed a public Streamlit README structure without copying its text.
Added submission/FORM_ANSWERS_20261103.md for actual field names supplied by owner;
subjective survey choices are suggestions,not fabricated user opinions. Muse Code
usage and partner deployment are not invented; publicity consent remains owner choice.
Verified11README local links,0broken. No product code,model calls,GPU or submission.

## Repository made public and anonymous media access verified — 2026-11-03

Committed/pushed contribution disclosure,MIT license,owner-reported eligibility,
quality/contribution-labelled video receipts and form draft in624568d. Source-only
staging audit:457files,6,688,991bytes,largest2,434,346-byte README GIF;exact inventory
and staged blob bytes matched. Package check2,179passed,0failures; no product code
change. Repository had0Actions runs and0issues/PRs before visibility change.

Under the owner's submission authorization,changed ParkYaeseong/BioPilot from
private to public. GitHub identifies MIT. Anonymous HTTP checks:repository200,
README200,LICENSE200,contribution disclosure200,MP4 Range206 with valid ftyp header.
Remote uploaded size and SHA256 match current9babd85a...899ab9 MP4,16,972,362bytes.
No credentials used for anonymous checks. Receipt:validation/public_access_20261103.json.
Updated README/demo/current manifest to remove obsolete sign-in-only guidance.

Submission itself is NOT completed:the saved browser site policy denies
cerebralvalley.ai. Owner was asked to clear that saved block; no workaround,
alternative browser route,form POST or legal acceptance was attempted.
Prepared truthful source-backed answers in submission/FORM_DRAFT_20261103.md.
Next permitted action:inspect the actual form after browser site permission is
restored. No invented submission receipt or newly measured efficacy.

## Event contribution disclosure and authorized public submission preparation — 2026-11-03

Owner reported organizer participation confirmation and requested contribution
disclosure and submission. Added compliance/EVENT_CONTRIBUTIONS.md separating
event-built Meta/MCP/workbench/guard/visualization integration from existing planning,
helper algorithms,models,data,libraries and UI inspirations. Original history and
historical pending records preserved. Eligibility is recorded as owner-reported;
no unseen written ruling or blanket reuse approval is invented.

Added MIT LICENSE for original project code/docs,with third-party terms retained;
updated README/disclosures/current submission metadata and prepared truthful form
answers in submission/FORM_DRAFT_20261103.md. Opening demo chapter identifies the
event-built MCP review/workbench; camera style,source capture quality,voice and
timing are retained. No new Meta/GPU calls. Verified37local links with0broken.

All reachable Git history was scanned for common private-key/provider/GitHub/AWS
token signatures and sensitive paths:680blobs,15,064,619bytes,0findings. This is
pattern-based and not a complete security proof. Models,credentials,runtime journals,
private conversations and raw captures remain excluded from Git.

The Cerebral Valley submit URL is blocked by a saved browser origin permission.
Requested that owner clear it; no alternate surface or HTTP submission is used.
Contribution-label media export verified:180s,1080p30,5400frames,27measured
subtitle cues,whole-file decode,24sample frames and12targeted45–75s quality samples.
Release MP4/EN/KO/checksum uploaded and digest-matched; current MP4
16972362bytes,SHA2569babd85a6556e43afbaea66e1fa3b6c03937c0322cb6d5f4cffd5f4af8899ab9.
Public repository/media verification and final source upload are recorded separately
after completion. No form submission or acceptance of legal terms is claimed.

## Quality-corrected demo Release assets replaced — 2026-11-03

User explicitly requested replacing the video and providing its link. Uploaded exactly
the corrected MP4,EN SRT,KO SRT and SHA256SUMS to existing demo-2026-11-02 Release,
replacing same-name attachments. MP4 asset705148740,size16,973,584bytes,SHA256
ba3f25083e156f33c915a1f6ff8688e82cac2de7cbf1e72cd2963db933f2d00b.
GitHub uploaded states,sizes and SHA256 digest fields match all four local files.
Updated Release description/title to identify actual execution and sharp recapture.
Existing tag/source history unchanged; repository remains private. No visibility
change,new inference,source commit/push or contest submission. Receipt:
submission/demo_release_quality_20261103.json. Next:owner video review and approved
judge access/publication path. No anonymous-access claim.

## Approval and RUNNING source blur repaired — 2026-11-03

User identified degraded quality from45seconds. Root cause: the52_execute_ready and
54_execution_running IAB source screenshots already lacked text detail despite their
1280×720 pixel dimensions. Their enlargement amplified the defect. Earlier media
checks verified encoding and bounds, but missed source legibility.

User explicitly approved one additional execution,Meta cap4,local CPU only,no GPU.
Created a separately bounded one-run filming journal .runtime/film_quality_20261103;
the existing main journal remained3claims and all original records were preserved.
Actual Chrome approval/RUNNING/completion sources are crisp; same text-crop Laplacian
variance188.29→6662.98(35.39×),a relative diagnostic,not a perceptual guarantee.
No AI upscaling or fake UI. Fast target zooms,highlight styling and narration stay.

New review093ed33a29154e76a0d43fdf52a8267b / run1a614cadfe604b36999ad33c316f2dfd completed with3Meta
requests,muse-spark-1.3,2MCP calls,CPU ESM150,19candidates,no GPU. Candidate and score
artifact objects exactly equal the prior execution. New trace,receipt and reopening
captures identify this run. Across the two November3 filming executions,6Meta requests.
Current-pass journal0→1; main journal3→3. Receipt:validation/video_quality_recapture_20261103.json.

Previous video and edit are preserved under before_quality_repair_20261103.
Rendered to a pending MP4;12encoded samples at45.8–73s were checked before
replacing the local deliverable. Matching47s text-crop Laplacian variance improved
22.36× in the decoded export. Visually checked47s and63s at full resolution.
`.venv/Scripts/python.exe .cache/verify_quality_candidate.py` passed duration180s,
5400frames,full decode and the relative text-detail check before promotion.
`.venv/Scripts/python.exe local_artifacts/final_demo_20261102/verify_video.py` passed
1080p30,H.264/AAC,9chapters,27measured subtitle cues,24encoded samples,source hashes
and highlight crop bounds. File16,973,584bytes,SHA256ba3f25083e156f33c915a1f6ff8688e82cac2de7cbf1e72cd2963db933f2d00b.
Updated current receipt/manifest/checksums; private Release still contains the old cut.
No product code changes,Release upload,visibility change or contest submission.
Full human listening review remains pending. Earlier application regression is
historical and is not claimed as rerun for media-only changes.

## Actual execution added to local demo — 2026-11-03

User requested an update of the existing local MP4 while retaining fast targeted
zooms and accurate rounded highlight boxes. Preserved the previous local cut in
local_artifacts/final_demo_20261102/before_execution_edit_20261103/. Kept the camera,
halo/dimming and no same-source dissolve behavior; replaced the execution sequence
with real permission checks, Execute, RUNNING, COMPLETED and result captures.

Executed the existing November 2 frozen public uploaded-input draft once via the
real browser. Review27ad1367776e47d18948632e44413946 / run622ddd9cc74a43528e470c50f51d46dc
completed with muse-spark-1.3,3Meta requests,2MCP calls,local CPU ESM150 and19candidates.
Allowance consumed2→3,remaining0; no reset/retry/GPU. Old records preserved.
New candidates and score_artifacts exactly equal the earlier run, so invariant
candidate and public reference-structure illustrations are reused. New trace,
input receipt and reopening are captured from the new run. Waiting is shortened;
the input and execution captures are from separate dates, not a continuous take.
Only public narration group4 is regenerated with the existing Edge TTS voice.

Changed files: README.md,demo/FINAL_VIDEO_20261102_KO.md,validation/video_execution_20261103.json,
current video receipt/manifest and local-only edit/media files. Product/MCP/science
code and original artifacts are unchanged. Release remains the previous version;
no upload, visibility change or contest submission. Technical verification:180.000s,1920×1080,30fps,5400frames,H.264/AAC,
9chapters,27nonoverlapping measured EN/KO cues,whole-file decode with no errors,
24encoded sample frames,source hashes and highlight crop bounds passed.
New file17,025,247bytes,SHA256a26d5076cfd60c78a8e8e7f877b7dcfe26a1dcaae522476778563cd498dd761b.
Commands: `.venv/Scripts/python.exe local_artifacts/final_demo_20261102/verify_video.py`
passed; `.venv/Scripts/python.exe checks/validate_package.py` passed2,153checks,0failures.
Full human listening review remains pending. No product code changes, so the earlier
785-pass application regression is historical and was not rerun for this media edit.

## Private video 404 diagnosis and README entry correction — 2026-11-03

User reported Not Found on the direct Release MP4 URL. Reproduced anonymous404;
authenticated GitHub asset Range request returned206/1,024bytes with valid MP4 ftyp
signature. The asset exists; original uploaded size/SHA remain recorded. The user's
browser cookie/account was not inspected, so do not assert their precise login state.
A separate full CLI download stalled at zero bytes and was stopped; full re-download
is not claimed. Existing local MP4 and original remote SHA verification are preserved.

README preview/primary link now opens the Release page and instructs authorized
GitHub sign-in → Assets → MP4. Direct download remains an explicitly labeled
after-sign-in option. Added the same guidance to the Korean video guide. No public
visibility change, re-upload, new Meta/GPU call or submission. Evidence:
validation/release_access_20261103.json. Final package check:2,135passed,0failures;
README24local links resolve; git diff --check clean.

## README demo entry and private media Release — 2026-11-03

README now leads with the purpose, clickable video preview, actual Release download
links, credential-free offline quickstart, user flow, Meta/code roles and evidence.
The current45.48s run is separated from the historical40s integration. README
explicitly distinguishes Git sources, Release assets and local-only material.

Uploaded exactly4assets to private prerelease demo-2026-11-02: MP4(41,628,046bytes),
EN SRT, KO SRT and SHA256SUMS. Remote uploaded sizes and GitHub SHA256 digests match
the local files. Tag pins the already-pushed b3719a2 source snapshot. MP4 is not
committed to Git. No repository visibility change, public judge-access claim,
new Meta/GPU call or contest submission. Receipt:submission/demo_release_20261102.json.
Only README/docs/current metadata and the small upload receipt change in source.
Final checks:2,131package checks passed; README24local links resolve and4media
links match uploaded assets; fresh isolated-venv AppTest passed all5views,19saved
candidates,S108A refusal/A32V acceptance and execution disabled without config.
Command:`.cache/submission_repro_20261102/Scripts/python.exe checks/check_reproduction.py`.
Next:owner video review and an explicitly
authorized public/judge-access route before submission.

## Current-UI narrated video exported locally — 2026-11-02

User requested the actual video with English AI narration, zoom/pan and animated
boxes inspired by the AionUi reference GIF. Exported local_artifacts/final_demo_20261102/
BioPilot_Bench_180s_EN.mp4:180.000s,1920x1080,30fps,5,400frames,H.264/AAC,41,628,046bytes.
Current file SHA256:535495e5bbbf1df45ec11cf1a5ae8eb145e1ff98351e7e2628488103fc5a79bf.
Actual144CUA screenshots include direct FASTA upload, S108A refusal, A32V validation,
candidate comparison/selection, real reference rotation, trace/evidence inspection
and completed-result reopening. This is sampled browser capture with edited camera
and pacing, not a continuous OS screencast. No synthesized UI or execution progress.

English voice:en-US-AndrewNeural via edge-tts7.3.1/Microsoft Edge online speech;
only the public304-word narration was sent. No product Meta/GPU calls were made.
Nine audio segments/27measured sentence cues, burned English captions, separate EN/KO
SRTs,9video chapters. Soft subtitle tracks were omitted to prevent automatic double
captions over burned English. Actual recorded scientific run remains labeled REPLAY
and45.48s waiting omitted. No reference GIF footage was included.

Verification:whole-file decode passed; ffprobe confirmed180s/1080p/30fps/9chapters;
audio mean-16.9dBFS/peak-1.4dBFS;27timed sentence cues have no overlaps; source-frame
hashes matched;24encoded frames inspected. Corrected the initial reopening highlight
to enclose only COMPLETED, then re-encoded and repeated media verification. Original
scientific scores/ranks/traces and product code are unchanged. Journal execution
claims stayed2before/after;1local validated draft was added and never executed.
Human full listening review is not claimed. Public links/submission remain pending.

Final source package consistency:2,127checks passed,0failures; planned bilingual
script validation also passed. No product code changed, so the prior785-test
application regression is not represented as a new video-specific test run.
Guide:demo/FINAL_VIDEO_20261102_KO.md. Receipt:submission/video_current_ui_20261102_receipt.json.
Video/raw captures/audio/GIF stay excluded from Git. Small documentation, receipt and
encoded preview are the source handoff. Next allowed action:final user playback and
approved video publication/judge-access checks; no automatic public release or submit.

## Submission handoff and isolated offline reproduction — 2026-11-02

Submission entry now points to app/bench.py, the uploaded-input actual execution
receipt and current bilingual script. Historical video/trace records are preserved.
Added submission/REPRODUCE_KO.md and demo/FINAL_RECORDING_CHECKLIST_KO.md; no final
video, source visibility change, publication or submission was performed.

Fresh Python3.14 Windows venv with system-site-packages=false and a separate source
copy exposed a genuine missing dependency: installing requirements-viewer.txt alone
made New Review fail with ModuleNotFoundError:dotenv. Added requirements-workbench.txt
with python-dotenv1.2.1 and a complete tested Windows/Python3.14 version snapshot.
Product execution, MCP, biological data and rank code are unchanged.

New checks/check_reproduction.py passed after installation: five rendered AppTest
views,19saved candidates with locally consistent integrity, S108A refused, A32V
accepted, Execute disabled without model configuration. The check uses a temporary
journal and blocks execution boundaries; it cannot spend or use the owner's journal.
pip check found no broken requirements. Same-PC isolated installation is verified;
other machines/OSes, browser WebGL and fresh live-runtime installation are not.
Manual browser also opened saved Overview and New Review without credentials or
weights. Evidence:validation/clean_workbench_reproduction_20261102.json.

During edits a regression run returned784passed/1failed/2skipped: the sole failure
was stale generated MANIFEST hashes while documentation was being changed. The
manifest was regenerated. Final full regression:785passed,2Windows symlink skips,
2existing Modal deprecation warnings,12subtests passed in66.48s. Command:
`.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider --basetemp=.cache/submission_finish_final_20261102 --tb=short`.
Bilingual180s plan/caption validation also passed. Final package check follows the
last metadata update:2,117checks passed,0failures. Receipt:
validation/submission_readiness_20261102.json.
No new Meta/GPU calls. Repository remains private by owner decision. Final video,
unauthenticated judge access, current final form/rules and reuse/rights decisions
remain open. Next allowed work: rehearse/record current UI and inspect the export;
do not fabricate an uninterrupted live browser execution or reset execution caps.

## Unified executable workbench and New Review guide — 2026-10-29

One canonical app8522: New review / Recent reviews; full-reference FASTA or registered
example → request → local validation → explicit permission/cost acknowledgment →
Meta/MCP/local CPU ESM → same five result views.8523is a read-only compatibility link.
Legacy viewer remains independently read-only. New input hashes and report hashes
are journal-owned and inspected under Evidence. Unsupported/mature inputs and an
unverified optional mmCIF fail before execution; no hidden reference substitution.

New files:bench.py,bench_intake.py,bench_store.py,bench_execution.py,compat.py,
new_review_tour.py and two offline test modules. Extracted viewer.render_workbench
without adding execution imports. SQLite atomically claims each frozen review once,
retains a conservative global local cap and preserves interrupted/running/partial/
failed records. Input edits revoke confirmation. A separate new request requires
new approval. Scientific review launch caps are3–4Meta requests, checked before claim.

Actual browser uploaded the registered FASTA, refusedS108A and validated/approved
A32V. The first attempt stopped before Meta with0reservations: an approved optional
Atlas catalog entry was rejected by the previous strict baseline host. Preserved
that partial record. An offline MCP catalog probe reproduced it. A failing test
preceded the minimal fix: known optional Atlas may exist, but only the original
baseline tools are offered to Meta; unknown/duplicate tools are still refused.

Actual new execution:run14014be81e934c0ab4236268d013ad19, modelmuse-spark-1.3,
3Meta requests, local CPU ESM150,19candidates,45.48s,0GPU calls. Corrected execution
used the same approved journal record through the explicit backend entry after
browser control became unavailable; do not claim a continuous browser-click E2E
recording. Actual browser reopened completed results and the input receipt in the
same app. Receipt:validation/unified_review_execution_20261029.json; unchanged-byte
score replay:demo/artifacts/unified_review_20261029.replay.json. No automatic retry.

User steering added a five-step New Review spotlight guide: actual local guard and
valid preview, no draft overwrite, durable review creation, model call or approval
grant. Results keep the nine-step replay guide. Actual step images captured. Both
Start guided demo buttons changed from black primary fill to neutral/teal secondary.
Actual browser stepped through input guide and confirmed disabled execution/Finish.

Focused checks:initial4intake/store tests failed then passed;3AppTests failed then
passed; Atlas catalog regression failed then passed. Latest focused88tests passed
in11.92s before the final budget/guide polish; final12intake/UI tests passed in7.91s.
Full regression/package/browser final receipts follow below. Existing135scientific
evidence files unchanged. Actual vs mocked cases are distinct; fixtures are not
used as execution evidence. No new remote GPU, deployment or public visibility.

Bilingual180s script/captions now follow input → request → labeled recorded actual
execution → candidates/structure/trace/evidence → reopening.304English words;
timeline180s; EN39/KO33cues, max2lines, minimum2286ms, no gaps/overlaps. These are
planned captions, not measured voice or a new exported movie. Guide walkthroughs
remain separate from the timed main recording. Command:checks/validate_review_flow_demo.py.

Final full regression:785passed,2skipped,2warnings,12subtests in83.96s.
Command:`.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider --basetemp=.cache/unified_bench_final_regression --tb=short`.
After the final mobile card positioning and teardown fixes, focused affected suite:
83passed in9.03s. Actual390x844 viewport:pageWidth390; cardbottom602.6875; overlay
absent after Finish. Guide/reopening/restarts left exactly the original partial
and new completed records,1remaining allowance,3actual Meta requests unchanged.
Independent review:60offline tests, no remaining substantive issue after fixing
the minimum cap and analogous legacy validation-smoke optional-tool filtering.
Final UI/coverage/screenshot receipt:validation/unified_workbench_ui_20261029.json.
Package/source verification:2,091checks passed,0failures; git diff --check clean.
Next: existing private repository sync; no public deployment or submission.

## Bilingual 180-second demo with New Review — 2026-10-29

Current recording entry point is demo/REVIEW_FLOWS_180S_EN.md and its Korean
counterpart. Updated nine-shot timeline: saved Overview/Meta trace/candidates/
Structure/Evidence for0–100s, New Review stages/refusal/valid preflight for100–165s,
then scope/contribution through180s. English narration291words; average97wpm is a
planning estimate, not measured speech. The default stops before paid execution.

Added EN/KO planned SRT captions, demo/review_flows_180s.json, current guide links
in README.md/demo/README_KO.md/docs06, and checks/validate_review_flow_demo.py.
Original storyboards, narratives, videos and scientific artifacts remain historical
records. Recent New Review test fixtures are not used as live evidence. Actual new
execution would require its own approval, verified recording and revised narration.

Verification command: `.venv/Scripts/python.exe checks/validate_review_flow_demo.py`.
Timeline exactly180s,9segments; EN44/KO32cues; each starts0/ends180000ms, no gaps or
overlaps, maximum2lines, shortest1818ms. Captions exactly match the corresponding
narration. Offline checks confirm the current five views, A32V acceptance, S108A
refusal,19saved candidates, recorded actual model, A32missing atoms/S108author77.
Receipt:validation/review_flow_demo_script_20261029.json. Documentation-only change;
Package consistency after manifest refresh:2,029checks passed,0failures.
no application code change or new provider/GPU call. Previous full UI regression
remains769passed/2skipped; it was not rerun for this documentation milestone.
No new voice, video export, video-duration check, publication or submission.
Next: rehearse actual screen actions, record narration/screens, then measure the
real exported file and caption sync before any final video or submission claim.

## Primary Structure review restored — 2026-10-29

Saved Review: Overview / Candidates / Structure / Agent Trace / Evidence, all
unnumbered. New Review execution remains separate. Structure and Candidates share
focused_candidate; protected-site inspection does not overwrite the candidate.
Comparison selection remains a separate three-candidate set, preserving ranks.

viewer_structure.py rechecks pinned mmCIF bytes, the registered full_212 sequence,
unique exact deposited-sequence match, polymer/atom join, residue identities,
author numbering, chain and model policy, and finite coordinates. It verifies
index correspondence, not geometry, side-chain completeness or variant effects.
1ISP chain A has179 observed residues; full32 and212 have no atoms; full1–31 are
outside the deposited construct. A32X candidates show sequence context without a
fake atom marker. S108/D164/H187 are distinct colours. Fit/Rotate/Focus residue
are presentation-only controls. Default camera shows the whole reference.

Evidence / Structure provenance contains source URL, checksum, chain and mapping
states. Existing saved ESM3/ESMFold2 predictions remain clearly separated under
Additional evidence; no prediction or optional annotation reranks candidates.
The nine-step English guide opens Structure for steps6–7 and restores prior state.
Actual structure thumbnails refreshed from CUA screenshots. 390px mobile has no
page overflow; controls stack and embedded controls wrap. Viewer frame leaves
room for the complete limitations text. Actual browser Fit/Focus/Rotate verified.

Changed viewer.py, viewer_structure.py, guided_tour.py, tour_spotlight.py/js, two tour
images/capture metadata, related tests, demo plan and milestone docs. MCP/Meta,
New Review execution, raw scientific artifacts, scores and ranks are unchanged.
Initial navigation and verification tests failed before implementation. Focused
structure/tour/view regression:41passed before the final refusal test was added.
Full regression:769passed,2skipped,2warnings,12subtests in87.71s. Command:
`.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider --basetemp=.cache/structure_release_final --tb=short`.
After the final thumbnail contain/style change, focused structure/tour regression:
37passed in7.41s, including explicit candidate inspection after a protected-site
view. Actual screenshot confirms the whole preview is visible. Package:2,009
checks passed,0failures.
Scientific baseline:135unchanged,0changed,0missing. Full results and screenshot
hashes:validation/structure_review_20261029.json.
No new provider/GPU call, sequence upload, visibility change, deployment or submission.
Next allowed action: finish source verification and sync the existing private repo.

## Separate execution from saved exploration — 2026-10-29

Saved Review has four unnumbered views and no Previous/Continue workflow controls.
Diagnostics and reference mapping are Evidence subviews. New Review alone has
Input & Validation, Agent Execution and Review Results numbered stages. Input
submission only validates; Arm, cost acknowledgment and Execute are required.
Edits reset acknowledgment. Pending requests are consumed before dispatch and
refresh cannot retry them. Running/failed/partial/completed are distinct; partial
reports survive nonzero exits. Currency cost stays unknown; call caps are not bills.

Changed viewer.py/css, viewer_render.py, session.py, new review_flow.py, tour/copy
and related tests. Existing MCP/Meta adapters and session_exec unchanged. Initial
navigation test failed; focused viewer/tour29passed; New Review tests16passed.
Actual IAB tutorial9steps navigated and restored Overview. Execution status tests
use explicit mocks; New Review browser inspection remains unarmed. Full regression:764passed,2skipped,2warnings,12subtests in75.85s.
Exact command: `.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider --basetemp=.cache/separated_review_regression --tb=short`.
Evidence:validation/separated_review_flows_20261029.json. Actual unarmed browser
preparation and9-step guided screenshots are saved in local_artifacts/review_flows_20261029.
Scientific baseline135files unchanged. Package check2,005passed,0failures. No new
provider/GPU call, visibility change or submission. See current180s demo plan
in demo/REVIEW_FLOWS_180S_EN.md. Next: finish verification and private source sync.

## Workspace switch correction — 2026-10-29

Owner clarified the two sidebar links themselves were the issue. Changed only
viewer.css: two equal horizontal segments, common neutral label colour, selected
surface, no left bracket/inset accent. Navigation URLs and capability isolation
are unchanged. Actual IAB sidebar screenshot checked; both labels fit. Focused
brand/workspace/contrast regression:16 passed in2.83s. Command:
`.venv/Scripts/python.exe -m pytest tests_app/test_brand_presentation.py tests_app/test_workspace_flow.py tests_app/test_viewer_contrast.py -q -p no:cacheprovider --basetemp=.cache/workspace_switch_final --tb=short`.
No model/GPU calls or scientific file changes. Auto stays default. Source remains
private; next action is owner review of the corrected two-item switch.

## Responsive shell and Auto appearance — 2026-10-29

Resumed the interrupted Overview QA in the in-app browser. Actual Overview image
is captured; the missing-thumbnail test passes. Fixed header/button overlap,
mobile columns and long labels. Replaced boxed B with original ribbon SVG/favicon.
Simplified workspace navigation to flat links after owner rejected the card menu;
kept replay/live capability isolation. Appearance defaults to Auto via system media
queries, with explicit Light/Dark options. Tour and structure documents support Auto.

Changed viewer.py/css, viewer_render.py, viewer_structure.py, session.py, brand.py,
local brand assets, tour rendering, screenshots and related tests. Browser checks:
50 main-view width/theme combinations passed at320/390/599/1280/1920;10 unarmed
session checks;9-step desktop/mobile guide checks and Finish restoration passed.
135 original science/reference/receipt hashes unchanged. New provider/GPU calls0.
These are browser viewport checks, not physical-phone or biological validation.
The latest navigation/Auto refinement has30focused tests passing; final regression
passed:759 tests,2 skipped,2 warnings,12 subtests in71.80s.
Command:`.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider --basetemp=.cache/responsive_auto_final --tb=short`.
Receipt:validation/responsive_chrome_20261029.json. Package checks:1,989passed.
New video not exported. Repository stays private.

## Overview-first implementation; visual QA interrupted — 2026-10-29

Implemented the owner's five-view order: Overview, Candidates, Agent Trace,
Evidence, Input & Diagnostics. The landing overview now reads the saved candidate
and Meta artifacts for purpose/context, top scores, recorded handoffs and limits.
The absent original objective remains absent. Candidates retains the complete
cohort, original order, comparison and CSV. Reference mapping & saved structures
is an Evidence subview; FASTA/mmCIF diagnostics are confined to the final view.

Changed app/viewer.py, viewer.css, guided_tour.py, tour_spotlight.py/js; updated
viewer, demo replay, workspace and tour behavior tests; added
tests_app/test_overview_priority.py. Nine English guided steps move actual view
and selection state, then restore it. Local replay controls still cannot dispatch
provider/GPU work. Existing scientific/reference/verification files: 135 of 135
hashes unchanged, no missing files. No new integration calls or scientific result.

Failing landing tests: 5 failures before implementation, then 5 passed. Combined
overview/workspace/tour tests: 19 passed in 6.59s; existing viewer files: 49 passed
in 11.52s. Initial full run: 748 passed, 3 failed, 2 skipped, 12 subtests in 67.16s.
Two failures were a stale source manifest and the old five-row landing assumption;
both are corrected. The remaining Overview thumbnail test is deliberately not
weakened: a verified actual screenshot is still missing.
Final full regression: 750 passed, 1 failed (the missing thumbnail), 2 skipped,
2 warnings and 12 subtests passed in 66.47s. Package check: 1,967 passed,
0 failures; manifest regenerated after documentation updates.

Before desktop/mobile and after desktop diagnostic captures are preserved under
local_artifacts/overview_refinement_20261029. The after capture has browser clipping
and duplicate rendering and is not a visual-completion proof. CUA then stopped
because it could not confidently determine the current Windows browser URL.
No further UI automation or alternate capture path was used. Full size/theme
validation and the new overview.png remain pending; the eight original thumbnails
and earlier recordings are preserved. The temporary viewport override could not
be reset after the tool disabled browser control.

See docs/OVERVIEW_REFINEMENT_KO.md and demo/OVERVIEW_DEMO_180S_EN.md. This change
does not export a new video. Final offline test/package results are recorded in
validation/overview_refinement_20261029.json. Repository stays private; source
update is not pushed while the required thumbnail test remains failing. Next
allowed action: resume browser QA when available, capture the actual Overview,
reset the viewport, and complete the same test/manifest checks before private push.
Public release, eligibility/reuse, contributor/rights, final form, video review
and final contest submission gates remain unchanged.

## Owner choice: keep repository private — 2026-10-29

Owner explicitly chose to keep ParkYaeseong/BioPilot private for now. Connected
GitHub metadata confirms private visibility; no visibility-setting action was
performed. Updated submission/manifest.current.json and docs/DECISIONS.md to
replace the pending choice with this decision. Historical upload receipts retain
their original meaning. Code, saved scientific results and prior test receipts
are unchanged. Verification: GitHub metadata read and offline package checker
(1,947 checks passed, 0 failures);
exact checker command is `.venv/Scripts/python.exe checks/validate_package.py`.
The published-guide requirement for an eventual public submission is deferred
by the owner, not permission to change sharing now. No new provider/GPU calls or
contest submission. Next allowed work: local/private preparation; public release
requires a later explicit owner instruction.

## English tutorial correction — 2026-10-29

The user identified Korean copy in the otherwise English submission UI. The
spotlight overlay had its own Korean text despite the English base walkthrough.
Translated all eight descriptions, tips, controls, screen captions and accessible
labels; declared the dialog language as English. Manual playback now says to use
Next, with the seven-second cadence shown only during autoplay.

Changed app/tour_spotlight.py, app/tour_spotlight.js, app/viewer.py and the existing
spotlight regression test. Replaced the comparison thumbnail and README screenshot
with actual English local UI captures; retained the other seven source images.
Updated the capture manifest and validation/english_tutorial_20261029.json.

The English requirement first failed against the Korean overlay (1 failed, 2
passed), then focused tests passed (15). Related viewer, tutorial, structure and
provenance regression: 104 passed in 12.42s. CUA verified all eight English steps,
actual Next navigation, Finish dismissal and restoration to the prior view. The
8522 saved-result preview was restarted because imported Python copy was cached.
Package verification: 1,947 checks passed, 0 failures. Exact commands and
screenshot hashes are in the verification receipt. No new
Meta/GPU calls, scientific results, visibility changes or contest submission.

The Oct28 video is preserved as a historical draft and still shows the earlier
tutorial language. A final English recording, full human review, public visibility
approval, rights/contributors, final form and eligibility/reuse ruling remain
open. Next allowed action: record/review the corrected English demo and resolve
the remaining submission gates with the owner.

## GitHub main upload verified — 2026-10-29

Source uploaded to https://github.com/ParkYaeseong/BioPilot, main commit 457890b0e6bbf0cfba8c050024847a23a017ce41.
Connected GitHub read and git ls-remote confirm the uploaded commit. Repository
remains private pending the owner's explicit public-visibility choice. Original
Oct27 commits are ancestors; no history rewriting, force push or invented dates.
Initial source inventory:392 files,3,534,877bytes,max524,222bytes. Raw chats,
credentials, weights, environments and videos excluded. AI assistance and actual
Meta use are disclosed; no new provider/GPU execution or contest submission.

Fresh regression:744passed,2skipped,2warnings,12subtests in63.36s. A fresh local
Git clone of the exact pushed commit passes1939package checks with0failures,
including artifact hashes after checkout. Remote clone was interrupted by a
connection reset/stall; this check uses the existing dependencies and does not
establish a clean installation on another machine. The uploaded disclosure was
also independently read through the GitHub connector.

Changed publication records:compliance/AI_DEVELOPMENT.md,DEVELOPMENT_HISTORY.md,
META_RUNTIME_EVIDENCE.md,HACKATHON_READINESS_KO.md,rules_recheck_20261029.json,
publication_hygiene_20261029.json;README/screenshots/notices;Git attributes;
validation/github_publication_20261029.json;submission/manifest.current.json;
originality ledger. Removed one trailing blank line in a test; behavior unchanged.
Follow-up documentation package check:1943passed,0failures; source whitespace
check passed. Exact commands and limits are in the publication receipt. Public visibility,
eligibility/reuse ruling, rights/contributors, final form, final video/public link
and explicit contest submission remain open. Next action: respond to the owner's
visibility choice and finish source verification records.

## GitHub publication preparation and fresh guide check — 2026-10-29

User explicitly requested upload to ParkYaeseong/BioPilot. The destination was
verified empty and private; publication upload is authorized, visibility change is
a separate choice. Original two Oct27 commits remain intact. New publication-time
commits are dated when actually created, not reconstructed as earlier daily work.

Added AI_DEVELOPMENT, DEVELOPMENT_HISTORY, META_RUNTIME_EVIDENCE, fresh Participant
Guide review and relative README screenshots. Corrected stale Atlas/GPU status;
redacted one old external-address diagnostic while preserving its historical fact.
No full private assistant conversations, credentials, model weights, raw capture
directories or runtime databases enter the source inventory. Third-party notices
updated; a project-wide license is not invented. Source-only size and existing
history credential-pattern audit are recorded separately from eligibility/reuse.

Added Git attributes: LF source checkout, byte-preserved JSON/evidence/upstream
assets. This prevents Windows autocrlf changing replay or checkpoint receipt hashes.
Only non-evidence UTF-8 source text is normalized before regenerating the manifest.
The two original label-free evaluator scaffolds are explicitly included; actual
evaluation runs remain excluded. Staged blob bytes are checked against the intended
inventory before commit. Fresh package/regression results and actual remote upload
will be recorded after verification. No contest submission or new model call.

## Updated three-minute spotlight demo exported — 2026-10-28

New local video: local_artifacts/spotlight_demo_20261028/BioPilot_Bench_Spotlight_180s_LOCAL_DRAFT.mp4.
180.000s,1920×1080,H.264/AAC,26 burned and embedded English captions, offline Zira
voice.802 actual CUA viewport samples,median154ms; actual tutorial/selection/rotation
and free local chat refusal. Not continuous OS capture; timing edits disclosed.
No new provider/GPU inference during capture. Actual GPU source results are replayed.
Technical checks: no detected black interval,mean-18.1dBFS/peak-1.1dBFS. Seven decoded
frames/contact sheet inspected. Full human audio/video review remains pending.
Old movies and source receipts preserved. No publication or submission.

Final application regression:744 passed,2 skipped,2 warnings,12 subtests,58.65s.
Exact command and final package check are in validation/spotlight_verification_20261028.json.
Current submission metadata now references the real new movie and runtime receipts.
Source archive excludes secrets, model weights, runtime caches and actual evaluator
run data. Clean installation on another machine and final rights/rules/public links
remain unverified. Next allowed work: human review and explicitly authorized public
release/submission preparation; no automatic publication.

## RAPID-style spotlight tutorial and two actual GPU predictions — 2026-10-28

User clarified the tutorial with a RAPID screenshot: dim the rest of the screen,
focus the current region, show a floating explanation with per-step pictures and
move actual views with Next. Replaced the explanation-strip presentation with a
local spotlight overlay. Manual progression is the default; optional autoplay
retains the disclosed seven-second presentation cadence.

New/changed UI files: app/tour_spotlight.py, tour_spotlight.js, assets/tour/ (eight
actual CUA target-region PNGs and capture manifest), guided_tour.py, viewer.py,
viewer.css, viewer_structure.py, prediction_view.py, session.py; related behavior
tests. The overlay tracks scroll/resize, blocks outside pointer actions, supports
Back/Next/Skip/Close/Escape and keyboard focus, and returns original control state.
Native Streamlit callbacks still own all transitions. It cannot activate live runs.

Actual scientific work: after the user's explicit BOP account, GPU and concrete
public-reference/11-file egress approvals, used an isolated unprivileged worker.
Original keys, SSH configuration, existing processes and environments preserved.
No evaluator/label/private data or credentials entered the worker. Official
revision/LFS-or-git-blob checks precede immutable checkpoint manifests.

- ESMFold2 WT full_212: official esm3.4.1.post1, torch2.11.0, transformers4.57.6,
  CUDA13.0, NVIDIA L40S;44.776s recorded model-load/inference interval after pin
  verification; peak PyTorch allocation26,654,082,048bytes.
- ESM3 A32V full_212: same isolated SDK environment;6.478s recorded interval;
  peak PyTorch allocation5,450,721,792bytes. Seed0;structure track8steps.
- Fixed PyTorch allocation fraction0.80 on one visible GPU, one job at a time,
 900s supervisor ceiling. Official unfused PyTorch paths were used because
 optional fused kernels were absent; this was not a model/provider fallback.
- Both outputs passed exact chainA CA identity/numbering1..212 checks and local
  PDB/receipt/manifest checksum checks. Receipts and small computed PDBs are under
  demo/artifacts/structures/; sanitized summary validation/optional_science_runtime_20261028.json.
  Different models AND inputs: no variant-effect/model-accuracy comparison,
  geometry validation, phenotype claim or ESM2 reranking follows.
- Structure's Additional evidence panel shows these stored predictions separately
  from experimental1ISP and later-acquired Atlas context. Viewing them does not
  run a GPU job. The Meta product runtime remains muse-spark-1.3; no new Meta
  call was made here. Automatic remote folding in product MCP remains disabled;
  actual GPU execution is the explicitly approved bounded operator-worker route.

Also repaired two existing live-chat intake defects found during review: a UUID
workspace prevents collisions across fresh browser sessions; WT mismatch and
explicit mature numbering are refused before dispatch; preparation/timeout errors
are rendered without losing the conversation. These paths have offline behavioral
tests and did not spend provider credit during verification.

Focused UI/science-render tests:69 passed before final documentation checks.
Full regression and package results are in validation/spotlight_verification_20261028.json.
Browser proof: local_artifacts/refinement_20261028/tutorial_spotlight_light.png.
Eligibility/reuse/rights, public links, final refreshed video and actual submission
remain separate unfinished gates. No publication/deployment/submission occurred.

## Workspace refined; optional evidence connected — 2026-10-28

User requested repairs after their latest Claude changes. Inspected both real
8520/8521 surfaces before editing. Preserved those processes; current source is
served at loopback 8522 (replay) and 8523 (live session), with linked navigation.
Existing processes use fileWatcherType=none and retain old compiled scripts until
restarted. No old work, traces, videos or original manifests were overwritten.

Changed: app/viewer.py, viewer.css, viewer_render.py, viewer_structure.py, session.py;
new guided_tour.py and behavior tests; app/core/atlas_snapshot.py, tool_executor.py,
runtime_bundle.py, config/runtime_bundle.allowlist.json, development.yaml, both
tool schemas; new science/optional_science.py, optional_worker.py, atlas_context.py;
pinned reference Atlas snapshot/policy, tests and local/official-source guides.

- Light now covers actual installed React Aria controls, descendant text, caption
  opacity, native vector stroke, switch/checkbox, semantic tables, chat and iframe.
  Actual scoped Light body contrast17.85:1; caption/icon/placeholder7.58:1.
  Dark sampled text7.47:1 or better. Not a full accessibility conformance audit.
- Compact header, ordered Input/Candidates/Structure/Meta trace/Evidence; files
  live in Input. Saved review and live session share presentation/navigation while
  the replay import graph still cannot reach a provider or subprocess.
- An eight-step acting walkthrough performs actual local guards and changes
  candidate/structure/trace widgets every7s; pause/back/next/restart/exit restore.
  It is REPLAY with presentation timing, never simulated new model inference.
- Reference structure has matching Light background, real Rotate/Fit controls,
  full-reference selected label and explicit unmodelled full32 behavior.
- Actual Biohub Atlas GET returned the exact registered WT. fold_on_miss=false,
  no new folding; sanitized snapshot hash pinned in code/policy/runtime bundle.
  retrieve_atlas_evidence works through real stdio MCP without a runtime network
  dependency. Its original acquisition was HTTP; current use is imported_snapshot.
  pTM/pLDDT null. Original Meta replay has not been extended with a fictitious call.
- ESM3/ESMFold2 official SDK adapters and bounded operator worker implemented;
  mock-boundary tests are distinct from actual GPU execution. User approved BOP
  GPU use and the concrete11-file public-reference/worker transfer. Existing
  pipeline SSH access was verified, separate SDK environment provisioned; model
  weights and actual inference are being verified and are not marked complete.

Tests: `.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider
--basetemp=.cache/workspace_all_final_1750 --tb=short` → **733 passed,2 skipped,
2 warnings,12 subtests**,62.09s. Skips: Windows symlink privileges. Warnings:
installed Modal async deprecations. Final SVG-stroke CSS correction separately
covered by8 passing contrast tests and actual browser vector-ink inspection.
Package inventory is refreshed after milestone/evidence updates.

Real vs mocked: local checks, browser actions, actual Atlas HTTP and stdio MCP,
and operator SSH/environment are real. Saved Meta/ESM remain replay. New optional
model GPU results remain pending. No new Meta request, RunPod allocation, account
change, publication, deployment, submission or new biological efficacy claim.
Eligibility/reuse/rights and final public links remain unresolved. Next: finish
bounded BOP model verification, import only validated prediction artifacts, then
update final package and re-record the demo after the feature surface is stable.

## Live session surface added; live path re-verified — 2026-10-28

Tests: **660 passed, 12 subtests, 0 failed**; `checks/validate_package.py` **PASS, 1741 checks**.

- First paid Meta run since the refactor completed: 3 requests, 4,733 tokens, 19 candidates,
  `muse-spark-1.3` requested and returned. **Score artifact sha256 identical to the saved
  replay**, so the rename, prompt edit and tool-description change did not alter computation.
  Billing stays `unknown` — token counts are known, no invoice was read.
- `app/session.py` is a **separate program** from the replay viewer. The viewer still cannot
  reach a provider and that assertion now also covers `app/viewer_render.py`. The live surface
  opens unarmed, states that it can spend, shows a code-owned run cap it cannot raise, and
  refuses protected sites and out-of-region positions locally at zero cost.
- `app/session_exec.py` keeps command construction separate from execution, so "unarmed builds no
  live flags" and "protected positions never reach a process" are unit-tested without spending.

Remaining: demo assets still carry the old product name and need re-recording (deferred by the
user to last). Public repository URL and video URL are still absent. Atlas stays unintegrated.

Next allowed action: re-record demo assets, or publish the repository. Neither is started.


## Verifier wired, renamed to BioPilot Bench, guided tour added — 2026-10-28

Exact tests: `.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider`
→ **636 passed, 12 subtests, 0 failed**; `checks/validate_package.py` → **PASS, 1717 checks, 0 failures**.

- **esm650 verifier provisioned.** `facebook/esm2_t33_650M_UR50D` revision `08e4846e…`, 2.61 GB,
  every file verified against official LFS/git-blob hashes. The installer's aggregate-digest step
  failed on `sys.path`, so the receipt was finalised after re-hashing all five files on disk and
  matching them to the download record. Local run: 16.8 s load, 1.2 s per position.
  **Finding: the checkpoints disagree at rank 1** — esm150 ranks A32E first, esm650 ranks A32S
  first. That is exactly why optional evidence must not rerank.
- **Multi-checkpoint support.** `ESM_VERIFIER_*` settings (absent by default), pins for both
  checkpoints, `RoutingLocalProvider` dispatching by `model_key`, and runs may approve a model
  set (`esm_model_keys`). Pin validation now runs **before** any backend is built.
- **Fixed a fail-open.** An unrecognised run-input key made `_validate` skip the model
  restriction entirely, so any pinned model would have been accepted. Now validated.
- **Did not weaken the no-mixing guard.** `inference_service.py` still refuses two checkpoints in
  one run; the verifier is a separate run. The tool description now states this, and
  `app/core/tool_executor.py` derives the offered `model_key` enum from configured pins, so an
  unprovisioned checkpoint is never offered. `verifier_enabled: true` is now declared in config.
- **Renamed to BioPilot Bench** across 23 product-surface files. Deliberately preserved: recorded
  narration scripts and SRTs, video receipts, pre-event plans/specs, `compliance/` original-package
  records, and every reference to the `BioPilot_Atlas_Local_Start` directory and the repo folder.
  `BIOPILOT_ATLAS_KO.md` keeps its filename because `compliance/original_package_manifest.sha256`
  records it. MCP server id is now `biopilot-bench`, which differs from the saved receipts.
- **Guided tour** added to the viewer: four dismissible steps naming the next action in each tab.
  Note the explanation-block count is unchanged at 46 — a path was added, density was not reduced.

Real vs mocked: the verifier weights, hashes and the rank-1 disagreement are real; routing is
covered by synthetic-backend tests. No Meta API call was made in this work.

Remaining gates: recorded demo assets are now stale (old product name in audio) and need
re-recording. Atlas stays unintegrated by decision. Public repository URL and video URL are still
absent, so the entry is not submittable. No live Meta session has been run.

Next allowed action: re-record demo assets under the new name, or start the live session work
(budget-capped) with explicit approval before the first paid call.

## Coordinate join derived and Meta handoffs surfaced — 2026-10-28

Changed files: `app/core/coordinate_join.py` (new), `checks/emit_coordinate_map.py` (new),
`app/core/targets.py`, `checks/validate_package.py`, `reference/residue_map.json`,
`reference/target_profile.json`, `evaluation/workflow_suite.py`, `app/viewer_data.py`,
`app/viewer.py`, `app/viewer.css`, `docs/04`, `docs/11`, `docs/12`, `OPEN_ISSUES.md`,
`docs/DECISIONS.md`, `MANIFEST.sha256`; tests: `tests_app/test_coordinate_join.py` (new),
`tests_app/test_target_gate.py`, `tests_app/test_viewer.py`, `tests_app/test_viewer_polish.py`.

Exact tests run: `.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider`
→ **609 passed, 12 subtests, 0 failed**; `.venv/Scripts/python.exe checks/validate_package.py`
→ **PASS, 1702 checks, 0 failures** (up from 1483; the per-residue join rows are now checked).
`.venv/Scripts/python.exe -m app.cli validate --variant A32V` accepted and `--variant S108A`
blocked, unchanged.

- One approved read-only fetch of the official 1ISP mmCIF into gitignored `local_artifacts/`.
  Receipt (URL, HTTP 200, server date, 196038 bytes, sha256 `7ab626e5…cc10`) is in
  `local_artifacts/1isp_quarantine_20261028/fetch_provenance.json`. No provider call, no GPU,
  no upload, no sequence sent anywhere. The file was not vendored into the tracked tree.
- `app/core/coordinate_join.py` derives the join by the docs/11 procedure and is covered by a
  synthetic-fixture test plus a real-file integration test that skips when the local copy is
  absent. Chain A: 181 rows, 0 residue-identity disagreements, `auth − label` offset 0, no
  insertion codes, modelled 179/181. **Unmodelled: deposited 1 and 181 = full 32 and 212.**
  docs/04 records those positions as unidentified; they are now identified.
- 3D structure panel: still not built, now on evidence. All 19 saved candidates are A32X and
  full 32 has no modelled atoms, so selection-linked highlighting shows nothing for the whole
  cohort; a naive index selection resolves to auth 32 SER = full 63. No 3D library or JS
  component was added.
- Decision trace now shows the full recorded alternation (3 Meta turns, 2 MCP calls) above the
  unchanged tool timeline. Model turns carry finish reason, model, token usage, elapsed and
  reply length only — never reply text or reasoning.

- **docs/11 step 6 completed** on the user's explicit ruling to separate the two axes.
  `checks/emit_coordinate_map.py` emitted `reference/residue_map.json` with the source sha256
  pinned; re-running it is byte-identical. The profile was versioned `lipase_bs_a_v2` →
  `lipase_bs_a_v3`. `app/core/targets.py` no longer merely forbids coordinates — it now **pins**
  the verified state (exact source hash, `author_numbering_verified: true`,
  `geometry_validated: false`, unmodelled positions exactly `(32, 212)`) and refuses any drift.
  That is a tightening, not a loosening: six parametrised drift cases are rejected.
- Kept apart deliberately: `author_numbering_verified` (**true**, index join) versus
  `geometry_validated` / `coordinate_mapping_verified` (**false**, atom geometry). Every product
  output still reports geometry as unverified, `require_coordinates` still fails closed, and
  `coordinate_features_enabled` stays false.
- Found and fixed a latent coupling: `evaluation/workflow_suite.py` classified the geometry guard
  by matching its message text, so rewording silently reclassified the scenario as
  `unexpected_guard_error`. The needle was corrected and the coupling is now pinned by
  `test_require_coordinates_message_keeps_the_classified_fragment`.

Real vs mocked: the join, the emitted map and the fetch receipt are real; the handoff ladder
replays a saved real run. Nothing was recomputed and no new model call was made.

Remaining permission gates: the RCSB coordinate file is **not** vendored or redistributed —
redistribution rights were never established, so the map pins its hash instead and the
integration test skips where the file is absent. Atom geometry, side-chain completeness and
conformer policy remain unvalidated. Demo assets are not yet re-recorded. No 3D panel exists.

Next allowed action: re-record the demo assets to show the handoff ladder, or stop here. Any
geometry-dependent feature still requires a separate geometry review that has not been started.

## User-implemented work reviewed and polished — 2026-10-28

Inspected the user's actual http://127.0.0.1:8520/ viewer. Kept that process
running and opened a separate loopback preview at http://127.0.0.1:8521/.
The newer user implementation, existing real Meta intake records and all previous
failed runs/videos are preserved. No provider, ESM inference, GPU, upload,
publication or submission was initiated in this polish task.

Changed application files: `.streamlit/config.toml`, `app/viewer.py`,
`app/viewer.css`, `app/viewer_data.py`; tests: `tests_app/test_viewer.py`,
`tests_app/test_viewer_polish.py`, `tests_app/test_provenance_integrity.py`.
The baseline scientific claim remains reviewed and narrowed to unvalidated
sequence evidence; no phenotype or time-saving improvement is inferred.

- Fixed inherited dark text on dark surfaces and mismatched native widget/table
  colors. Actual browser-computed sidebar/primary metric contrast was 15.89:1
  in Light and 15.86:1 in Dark. This is a scoped check, not a full WCAG audit.
  Desktop 1440×900 and narrow sidebar collapse/expand were inspected. Theme controls,
  selection chips and focus remain readable. Motion respects reduced-motion.
- Added actual local example buttons A32V/S108A/G32V, explicit last-checked input,
  top-three comparison/clear, and previous/next saved trace navigation. These
  interactions do not dispatch models or alter saved results. Examples deliberately
  set the full-reference frame and sequence-preference goal; direct input is never
  silently renumbered. CSV download was exercised; its final selected two rows
  match the saved scores/ranks. An attempted browser selection of A32V did not
  commit, and no rank6 CSV result is claimed.
- Repaired provenance overclaim with behavioral tests: compute the score payload
  hash, compare displayed candidates/order to committed rows, and match the actual
  scoring-tool digest. Source-file/export hashes without source bytes stay recorded
  only; opened-file identity is computed locally, not an upstream authentication.
  Corrupt envelopes and candidate/score/rank changes are detected; Overview warns
  on mismatches. Replay bytes remain SHA256 cf02b139fe0866483ebb069903e5e0c2ce65a03e9460697c5ffecef805c273f8.
- New video: `local_artifacts/polish_demo_20261028/BioPilot_Bench_Polished_180s_LOCAL_DRAFT.mp4`.
  180.000s, 1920×1080 H.264/AAC, 34 English captions, non-silent offline Zira voice,
  zero detected black intervals. Uses 278 of 340 actual CUA browser samples,
  approximately 2Hz sampling; camera/timing edits and original timestamps are
  disclosed. It is not a continuous OS screencast or fresh Meta/ESM execution.
  Actual input refusals, tab/trace navigation, candidate selection and CSV controls
  appear. Contact sheet reviewed; full human audio/video review remains pending.
  Sources/hash/disclosures: `submission/video_polished_receipt.json`.
- Updated `docs/POLISHED_REVIEW_KO.md`, `docs/WORKFLOW_MEASUREMENT_KO.md`, current
  submission evidence/manifest, guides and provenance ledger. `python -m streamlit`
  is the documented launcher. The user's pasted score-local example had a truncated
  tokenizer pin and missing positions; a complete verified CLI example is supplied
  without executing inference.

Exact regression:
`.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider --basetemp=.cache/polished_full_20261028`
→ **588 passed, 2 skipped, 2 warnings, 12 subtests passed**, 47.51s, exit0.
Skips remain Windows symlink permissions; warnings are installed Modal asyncio
policy deprecations. Root UI RED had 4 expected behavior failures; related GREEN
had 92 passes. New integrity tests had 14 initial expected failures and 18 final
passes including later source-classification cases. Full receipt:
`validation/polished_verification_20261028.json`.
Final package checker: `.venv/Scripts/python.exe checks/validate_package.py` →
PASS, **1475 checks / 0 failures**. Source diff whitespace check also passed.

Real/mocked/replayed distinctions: UI guards and browser interactions are actual
local actions; stored Meta/ESM scientific output is replay; unit provider/logit
fixtures remain synthetic. The existing six-case fixed/Meta intake records are
separate: 6/6 and5/6, respectively, closed-set/rules supplied, manual unrun. They
support neither biological skill nor a measured workflow benefit. Evaluation
artifacts were not imported into the viewer or prediction runtime; the video
annotation reads them outside the product.

Next allowed action: inspect the new UI/video and review exact public materials.
Remaining gates: full human video/audio review, clean reproduction, rights and
contributor review, organizer eligibility/reuse ruling, current final form,
unauthenticated public links and explicit publication/submission authorization.
A new versioned private source ZIP is prepared after source/manifest validation;
prior ZIPs and videos remain preserved. No new external action is authorized.

## Local submission preparation — 2026-10-28

**Core MVP and local replay are demonstrable; final submission remains incomplete.**
No new Meta/ESM inference, GPU allocation, sequence upload, publication, deployment,
organizer message or contest submission was performed during this preparation.
The original 2026-10-27 implementation and earlier failed integration receipts remain intact.

- Current-facing guides now describe the actual saved Meta → MCP → local ESM run,
  the localhost read-only viewer and the narrowed scientific scope. Changed:
  `README.md`, `START_HERE_KO.md`, `VALIDATION.md`, `docs/IMPLEMENTATION_KO.md`,
  `docs/HOST_COMPATIBILITY.md`, `docs/12_biological_readiness.md`.
- `checks/export_demo_replay.py`, `tests_app/test_demo_replay.py` and
  `demo/artifacts/sequence_review.replay.json` provide a portable real-result replay.
  Source raw SHA256 `d396dd4eb8f75976e5fc61f38e1ffcf0c922397a7cbefc9ee8529cf32ffdb785`
  and original score SHA256 `63a1c3752407d96a54f33b735d72e700839e4b0e9363894597738f6e8531157f`
  are preserved. The nested score artifact is unchanged. The exporter rejects
  unknown/synthetic/conflicting provenance and altered ranks before writing;
  top-level display modes are REPLAY and the original run hash stays visible.
- Fixed `app/viewer_data.py`, `app/viewer.py`, `tests_app/test_viewer.py`: a live
  Meta validation with no ESM artifact previously displayed ESM LIVE. It now shows
  UNAVAILABLE. Every saved view explicitly says SAVED ARTIFACT PLAYBACK; original
  computation and current replay are distinct. Actual local browser inspection
  confirmed REPLAY, unknown cost, the recorded model and artifact-rendered ranks.
- `submission/README.md`, `manifest.current.json`, `evidence.current.json` and
  `FINAL_CHECKLIST_KO.md` connect actual evidence to claims and unresolved gates.
  Original blank templates remain preserved. Rights/reuse notices and a dated
  local-preparation row were added under `compliance/`; no license or organizer
  permission was invented. Rules were retried read-only via web and browser;
  both returned Loading... without final guide/form content. See
  `compliance/rules_recheck_20261028.json`.
- Local recording draft: `local_artifacts/demo/BioPilot_Bench_180s_LOCAL_DRAFT.mp4`,
  180.000 seconds, 1280×720 H.264/AAC, non-silent offline synthetic English narration
  and embedded/burned captions. Edited real UI stills and receipt-rendered cards are
  persistently labeled REPLAY / SAVED REAL RUN and LOCAL DRAFT. The encoded contact
  sheet was visually inspected; human full audio/video review and public access stay
  false. Changed: `demo/NARRATION_EN.md`, `demo/NARRATION_EN.srt`, `demo/README_KO.md`,
  `submission/video_draft_receipt.json`. Technical sources/hashes are in that receipt.
- Final packaging hardening: `checks/package_files.py`, `checks/update_manifest.py`,
  `tests/test_package_inventory.py`. Only the two original label-free evaluator
  scaffold files remain in source inventory; actual local evaluator subdirectories
  are pruned before descent. Model weights and SQLite/DB files are excluded everywhere.
  Manifest output is LF on Windows. The local source ZIP is
  `local_artifacts/BioPilot_Bench_submission_source_20261028.zip`; its unpacked
  package check is recorded outside source inventory to avoid self-hash recursion.
  The video is a separate local artifact, not silently placed in the source ZIP.
- An actual new local stdio MCP validation and valid/protected variant checks ran
  without external requests: `validation/submission_local_smoke_20261028.json`.
  A32V returned 0/ok; S108A returned 2/blocked. MCP negotiated 2025-11-25.
- Source credential-value comparison found no exact matching local long secret
  value in source inventory; values were never printed. This is a scoped
  comparison, not a comprehensive secret audit. Receipt:
  `validation/submission_source_hygiene_20261028.json`.

Exact final regression after inventory hardening:
`.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider --basetemp=.cache/submission_inventory_final_20261028`
→ **488 passed, 2 skipped, 2 warnings, 12 subtests passed**, 40.76 seconds, exit 0.
The preceding application/replay regression passed 477 tests before the 11 inventory regressions were added.
The skips are Windows symlink privileges; warnings are installed Modal SDK
asyncio deprecations. Before this turn: 449 passed / 1 manifest failure / 2 skipped.
The current source manifest is regenerated for this local preparation; the
original package manifest and historical receipts are preserved. Existing CRLF-only
noise in `tests_app/test_meta_loop.py` was normalized without changing its Python text.

Behavioral tests were run RED then GREEN: viewer 4 expected failures → 18 passed;
initial export 3 expected failures → 27 combined passes; export provenance review
13 expected failures → 44 focused passes / 1 Windows skip. Packaging inventory
11 expected failures → 14 focused passes / 1 Windows skip. See
`validation/submission_preparation_20261028.json` for exact scope and commands.

Real / mocked / replayed: the new local protocol/guard checks are actual; current
screens display the saved actual 2026-10-27 scientific run as replay. Unit-provider
responses and logits remain synthetic fixtures. No science result was recomputed.
The retrospective interval still includes zero; workflow comparison is unmeasured;
actual billing and atom geometry remain unknown. Keep the unvalidated sequence
review claim. Do not claim T50 improvement, calibrated prediction or time savings.

Remaining gates: clean setup on another environment, human review and permitted
public video/repo access, final form/rules, contributor/rights review, organizer
eligibility/reuse ruling and explicit final submission authorization. Optional
remote Modal is unavailable: CLI permits at most 900 GPU seconds while the current
conservative remote reservation needs 1022; do not advertise a runnable remote path.
This limitation does not affect the completed local ESM reference path.

Next allowed action: inspect the local replay, evidence-linked submission draft and
recording materials; review exact public materials and organizer requirements.
Do not launch new remote/provider work merely because this package was updated.

## Site bootstrap interval and local viewer — 2026-10-27

### The headline correlation does not survive its own confidence interval

`site_bootstrap_interval` was hardcoded `None`. It is now computed, and the result
changes what may be claimed:

- Complete-case Spearman **0.288**, 95% site-bootstrap interval **[-0.058, 0.536]**,
  `excludes_zero: false`. The correlation is **not statistically distinguishable from
  zero**.
- 117 measured variants across **9** sites, not 10: every `G110` label is missing.
- 2000 percentile resamples, seed 20261027, 0 degenerate resamples.
- `recall_at_k` 0.35 against a 0.171 random expectation carries the same uncertainty
  and was not separately bootstrapped.

Sites are the resampling unit because alternatives at one position share a residue
environment; resampling individual variants would understate uncertainty and would have
produced a falsely narrow interval. The existing limitation "a small site subset cannot
establish general performance" is now backed by a number.

Originals are preserved: `evaluation_report.json` and `evaluation_curated_report.json`
are untouched. The new output is `evaluation_curated_report_with_ci.json` plus
`site_bootstrap_summary.json`, mirrored at `validation/site_bootstrap_summary.json`.

- Changed file: `evaluation/public_assay.py` (`site_bootstrap_spearman`, `_percentile`,
  and the report field). New test file `tests_app/test_site_bootstrap.py`: 8 tests
  covering determinism under a fixed seed, perfect and inverted agreement, too-few-sites
  returning a null interval with a reason, counted degenerate resamples, and the
  refusal to claim calibration or general performance.

### Local read-only viewer (C5, deliberately minimal)

`app/viewer_data.py` is a pure read model over one saved artifact; `app/viewer.py` is a
thin Streamlit layer. The read model imports only `json` and `pathlib`, asserted by an
AST test, so it cannot reach a provider, GPU, credential or database.

- It renders numbers from the stored artifact, never from model prose, and labels
  `LIVE` / `REPLAY` / `SYNTHETIC_FIXTURE` distinctly. An unsettled cost shows as
  `unknown (not verified)`, never `$0`. A partial run is shown as not complete.
- **Security fix during this work:** the first launch advertised
  `External URL: [redacted non-loopback address]`, meaning the viewer was bound to every
  interface and reachable off-machine. `.streamlit/config.toml` now pins
  `server.address = "localhost"`. Verified by relaunch: the banner no longer advertises
  a Network or External URL and `netstat` shows `TCP 127.0.0.1:8502 LISTENING` only.
- Verified by actually running the app, not just unit tests: `streamlit.testing.v1.AppTest`
  executes the script and asserts no exception, the scope warning, the status metric, the
  model metric, the unverified-cost metric, the missing-artifact error path and the
  partial-run error path. An HTTP 200 on the shell page would not have proved this,
  because Streamlit runs the script only on websocket connect.
- `streamlit==1.66.1` installed into `.venv` only and pinned in `requirements-viewer.txt`.
  Installing it authorizes nothing.
- New test file `tests_app/test_viewer.py`: 14 tests.

### Machine capacity check

Measured on this machine: Core Ultra 5 245K, 14 cores, 31.4 GB RAM (12.5 GB free),
123.5 GB free disk, **Intel integrated graphics with no CUDA**. Local capacity is
sufficient for everything currently in scope — ESM 150M CPU inference already runs in
24 s, and the viewer and bootstrap are trivial. No external compute host is needed. The
only thing this machine cannot do is CUDA GPU work, which is stage 3 Modal and is remote
by design and still unauthorized.

### Current suite

`.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider`
→ **449 passed, 1 failed, 2 skipped, 12 subtests passed**. The one failure remains the
pre-existing `MANIFEST.sha256` drift. Both skips are the Windows symlink privilege tests.

## Stage 2 integration verified in one execution — 2026-10-27

`sequence_review` now completes Meta tool calling, MCP execution, real local ESM,
code-computed ranking and the final grounded explanation **within a single run**.

Receipt: `.runtime/real_integration3_20261027/attempt3.{execution,stdout}.json`, mirrored
at `validation/integration_success_20261027.json`. Run `5b7c92bc2d364680809713bf8c332f66`,
40 s wall, returncode 0, `status=sequence_review_complete`.

Evidence chain inside that one execution:

1. Meta response, `finish_reason=tool_calls`, 313 completion tokens
2. MCP `validate_target_context` → `ok`
3. Meta response, `finish_reason=tool_calls`, 214 completion tokens
4. MCP `score_positions` → `completed`, artifact `63a1c375…`
5. Meta response, `finish_reason=stop`, 395 completion tokens, 313 characters

- Model: `muse-spark-1.3` requested and returned. MCP protocol `2025-11-25`.
- ESM really ran in this execution: `cached_positions_1based` is empty, the fresh
  workspace wrote 1 cache file, `esm_source_mode=live`. Provenance: `esm2_t30_150M_UR50D`
  rev `a695f604…`, cpu, float32, `full_212`, transformers-5.2.0/torch-2.9.1, weights
  `377f67e2…`, tokenizer `28bae4e8…`.
- The artifact sha256 is identical across three independent fresh workspaces, which
  shows deterministic computation rather than cache reuse.
- 19 candidates ranked by `esm150_masked_v1`; the ranks are rendered by code, and the
  model narrative contains no numbers.
- `scientific_scope` stays `unvalidated_sequence_evidence_assistant` and
  `biological_efficacy_established` stays false.
- Cost: 3 requests, 150000 micros reserved and committed for this attempt.
  **`actual_cost_micros` is null and `cost_status` is `unknown`.** Across the three
  attempts 450000 micros ($0.45) were reserved locally; the invoiced amount is unverified.

Two earlier attempts failed and are preserved, not overwritten:

- Attempt 1 (`real_integration_20261027`, run `75704247…`): raising the reserved report
  cap from 512 to 1024 was not sufficient. `finish_reason=length` at exactly 1024.
- Attempt 2 (`real_integration2_20261027`, run `86b60d59…`): adding an explicit length
  instruction was also not sufficient; `prompt_tokens` rose 1237→1325 proving the
  instruction was sent, yet the response again filled 1024 and returned no content.

Root cause, found only on the third diagnosis: `_run_sequence_review` sent **no
`reasoning_effort` field at all**, so reasoning tokens consumed the whole completion
budget. The package's own `examples/meta_execute_request.json` specifies `medium` and
`examples/meta_report_request.json` specifies `low`, and `app/host/final_report.py`
already set `low` and had completed live in 575 tokens. The implementation simply did
not follow the design. Setting `tool_stage=medium` and `final_report=low` fixed it:
the final response used 395 of 1024 tokens.

- Changed files: `app/host/meta_client.py` (`REPORT_TOKEN_CAP`, `EXECUTE_EFFORT`,
  `REPORT_EFFORT`, `FINAL_REPORT_INSTRUCTION`, `MetaHost(final_report_tokens=…)` with no
  silent downgrade, `_public_content_chars` trace diagnostic), `app/host/runner.py`
  (wires 1024 and the efforts for `sequence_review` only), `app/host/final_report.py`
  (single-sources `REPORT_TOKEN_CAP`), `tests_app/test_meta_loop.py` (one positional
  assertion updated to assert intent after the final turn gained its own instruction).
- New test file `tests_app/test_review_report_cap.py`: 15 tests. The validation smoke
  512-token contract cannot be widened, and a still-truncated report stays `partial`
  rather than being reported as success.
- `content_chars` is now recorded per response so a future `length` failure can be
  diagnosed as empty-vs-truncated without spending another live request.
- Exact tests: `.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider`
  → **427 passed, 1 failed, 2 skipped, 12 subtests passed**. The one failure is the
  pre-existing `MANIFEST.sha256` drift described below. Both skips are the Windows
  symlink privilege tests.

## Final report continuation — 2026-10-27

The partial sequence review `b7a1e675000f4c10b53fcb137fd2bcf2` is now explained by a
separate saved report. Its own artifact was not modified.

Why the earlier 3-request run stopped: `_run_sequence_review` sends every request,
including its reserved final no-tool report, with `MAX_OUTPUT_TOKENS=512`. The third
response used exactly 512 completion tokens, so `finish_reason` was `length`, the
"No complete public narrative" check rejected it and `stop_reason` became
`invalid_or_forbidden_model_output`. Tool calling and real ESM scoring had already
succeeded; only the closing narrative was truncated. That 512-token sequence-review
contract is unchanged.

- Changed file: `app/cli.py` (new `final-report` subcommand). New test file:
  `tests_app/test_final_report_cli.py`.
- Gap closed: `app/host/final_report.py` and its 13 tests already existed and
  `app/core/runtime_bundle.py` already allowlisted the module, but no CLI or runner
  command could reach it; `runner.py` still accepts only
  `--workflow {validation_smoke,sequence_review}` and was not extended.
- `--prepare` builds the one-call plan and writes `final_report_plan.json` without
  sending anything, refuses to overwrite an existing receipt, and requires the exact
  source artifact id. Execution requires both `--live --ack-single-report`, checked
  before a key-reading client is constructed.
- Exact tests: `tests_app/test_final_report_cli.py` 4 failed (RED, argparse rejected
  the unknown command) then 4 passed; combined with `tests_app/test_final_report.py`
  17 passed. Receipts: `validation/phase3_final_report_cli_red.txt`,
  `validation/phase3_final_report_cli_green.txt`.
- Full suite `.venv/Scripts/python.exe -m pytest tests tests_app -q -rs`:
  **412 passed, 1 failed, 2 skipped, 12 subtests passed**, matching the pre-change
  baseline exactly. The single failure is `tests/test_package_validator_v3.py`
  manifest drift, which already failed before this work: 11 source files were modified
  and several untracked beforehand. `MANIFEST.sha256` is now additionally stale for
  `app/cli.py`, `docs/STATUS.md` and `docs/DECISIONS.md`, with `manifest complete`
  flagging the new test and receipt files. The manifest was deliberately not
  regenerated here. Both skips remain the Windows symlink privilege tests.
- One self-inflicted regression was found and fixed during this work. The first
  `validation/phase3_final_report_cli_green.txt` was captured by shell redirection, so
  a cp949-encoded Windows warning string landed in it. `checks/validate_package.py`
  reads inventory files as strict UTF-8 and crashed with `UnicodeDecodeError`, turning
  1 validator failure into 7. The receipt was regenerated with `PYTHONIOENCODING=utf-8`
  and `-p no:cacheprovider`; capture pytest receipts that way on this machine.
- Live execution: one request, `muse-spark-1.3` requested and returned, no tools, no
  retry, no GPU, no new ESM inference. `finish_reason=stop`,
  usage 446 prompt / 575 completion / 1021 total, 2.86 s. 575 completion tokens sits
  under the 1024 cap, confirming 512 was the binding constraint.
- Budget: continuation run `2ff6d7ee66234d58823d518525af1b4b` reserved and committed
  50000 micros ($0.05 local reservation) for 1/1 permitted request. The task is
  `COMPLETED_UNKNOWN_COST` with provider job `chatcmpl-01a17c07-7d47-750e-b9ab-010f39d18ca9`.
  **`actual_cost_micros` is null and `cost_status` is `unknown`; the real invoiced
  amount is still unverified.** The source run stays at its own 150000/150000 micros.
- Preservation check: the source artifact reloads with a matching checksum and still
  reads `partial` / `invalid_or_forbidden_model_output` / 3 attempts. The new report
  `d430e93a6f385ff15e4ed4bcf99064934c2ef5290a1a2017f1ac6e8bb2ee3962` was written under
  the separate continuation run directory.
- Scientific scope is unchanged: `scores_reused_from_saved_artifact` is true,
  `esm_source_mode` is `replay`, `biological_efficacy_established` is false and the
  scope stays `unvalidated_sequence_evidence_assistant`. No T50, activity, solubility,
  Tm, geometry or retained-function claim follows from this report.
- Receipts: `.runtime/real_meta_esm150_20261027/phase3.execution.json` and
  `phase3.stdout.json`, mirrored at `validation/meta_final_report_execution.json`.
- `.runtime/meta_final_report_20261027/` holds only an abandoned `product/` bundle with
  no `launcher.json` or `state/`; the continuation correctly lives in the source
  workspace database instead. It was left in place, not deleted.

Next permission-dependent action is unchanged: no remote GPU, model download,
deployment, publication, push or submission is authorized. Regenerating
`MANIFEST.sha256` is a separate decision that has not been taken.

## Implementation update — 2026-10-27

The first local product implementation now exists on branch
`implementation/mcp-core-20261027`. The original package was preserved in the
initial local Git commit; no push/publication was performed. The supplied status
below remains a historical package receipt, not the current implementation claim.

- H0: inspected the package, helper provenance and captured rules. Original run:
  68/69 unittest checks passed; validator failed `manifest complete` because local
  additions were not part of the distribution. Local credentials/environments/helper
  files are now pruned from source inventory. Original manifest is preserved at
  `compliance/original_package_manifest.sha256`.
- B0 implemented: `app/core/targets.py`, `capabilities.py`; typed immutable registry,
  explicit full-reference frame, exact hashes, S108/D164/H187 policy, variant/FASTA
  checks, geometry blocked. `tests_app/test_target_gate.py`: 32 passed after 32 RED failures.
- C1 implemented slice: `app/core/runs.py`, `budget.py`; SQLite approval/version,
  atomic reservation/claim, ownership, timeout/unknown-cost and cancellation guards.
  `tests_app/test_run_policy.py`: 20 passed. Not a provider billing guarantee.
- C2 adapter/math implemented; real integration pending. Local-only pinned safetensors
  loading, masked marginals/cache/common-model ranking tested with synthetic logits.
  No weights downloaded and no real ESM score exists yet.
- C3 transport implemented slice: `app/mcp_server.py`, `tool_executor.py`,
  `runtime_bundle.py`; actual spawned stdio MCP validation/status calls succeeded.
  SDK 1.25.0 negotiated protocol 2025-11-25. Evaluator/secret/docs/tests excluded from
  the provisioned workspace. OS ACL isolation and native Muse Code are unverified.
- C4 controlled validation smoke code exists: `app/host/`, `app/cli.py`,
  `app/core/artifacts.py`. Mocked loop tests distinguish fixtures and live results.
  The first live attempt has a partial receipt under `.runtime/live_validation_20261027`;
  no actual provider/model response was verified by that attempt; no retry occurred.
  User-reported earlier Meta smoke (OK, 120 tokens) remains separate evidence.
- B1 evaluator code is separate in `evaluation/`; tests are synthetic only. Real raw/
  curated reconciliation, held-out evaluation and biological baseline remain unperformed.
- C5 UI, E1 real workflow comparison and S1 recording/submission remain unimplemented.

User steering is implemented at the local code/test level: shared provider interface,
LocalESMProvider, ModalESMProvider and explicit unconfigured RunPodESMProvider; default
ESM_BACKEND=modal, explicit 35M/150M/650M model policies, shared MCP score_positions,
durable submit/poll/status, worker source allowlist and guarded deployment definition.
Actual model/GPU integration remains pending. This does not approve GPU allocation,
paid remote work, model downloads, deployment or RunPod creation.
No live ESM/GPU/Atlas, raw label lookup, external sequence upload, publication,
GitHub push or contest submission has occurred. Test counts above are stage receipts.
The final combined receipt is in validation/implementation_final_tests.txt.
Final command: `.venv/Scripts/python.exe -m pytest tests tests_app -q -rs --basetemp .cache/pytest_final_installed_sdk`.
Observed result: **339 passed, 2 skipped, 2 warnings, 12 subtests passed** (59.59 s).
Both skips are Windows symlink privilege tests. Complete changed-file inventory and
integration modes are in validation/implementation_summary.json; Korean launch
instructions are in docs/IMPLEMENTATION_KO.md.

Modal SDK 1.6.2 was installed into .venv only (requirements-modal.txt), and required
public API signatures were checked without authentication or cloud operations.
Live compatibility and execution remain false. See validation/modal_sdk_offline.json.
The SDK emits two Python 3.16 deprecation warnings on Python 3.14; current tests pass.
The .env secret values were compared locally against the source inventory without
printing them; no matching source files were found. The real .env remains ignored.

The sequence_review host now reserves its final request before tools and validates
saved numerical artifacts before deterministic ranking. Pending inference stops with
a partial report. Only mocked provider responses/fixtures tested this full review loop.
The evaluator can freeze an ESM artifact directly without manual row renumbering.
Independent review fixes cover queued-task resume, source-mode consistency, configured
model pins/positions and conservative 900-second remote reservations. Windows UTF-8
source reading and source-manifest inventory were also repaired with failing tests.

Next permission-dependent action: review exact model download, existing volume,
T4/L4 choice, 900-second conservative ceiling and approved cost, then separately
authorize one remote integration. No such action has been authorized or performed.
UI remains omitted while the real biological baseline/claim scope is unvalidated.

## Supplied package status (preserved)

Package revision v3 is prepared for implementation. It is not a running application.
The preserved scientific guards and new offline catalog/rubric/recording helpers are tested separately
from any product integration. See VALIDATION.md for actual test receipts and exact scope.

No Meta API, MCP transport, ESM GPU, Atlas live service, UI rendering, biological evaluation, video,
publication or submission was executed by this package revision.

Next implementation task: read-only environment/repo inspection and H0/B0 under the user's actual
permissions, then follow the v3 plan. Do not restart earlier completed user work if a real repo exists.

## 2026-10-28 Meta contribution arm, viewer provenance and demo recut

E1 workflow measurement is now partly executed rather than only specified.
`evaluation/workflow_protocol.json` (v1, provider calls forbidden) produced the fixed local
guard arm: 6/6 correct in 11.1 ms, zero provider calls — `validation/workflow_policy_baseline_20261028.json`.
`evaluation/workflow_protocol_meta_v2.json` (frozen 2026-10-28T02:10:28Z, provider calls
permitted; ESM inference, GPU, upload and labels still forbidden) produced the Meta arm.

Observed arms, common six-scenario denominator:
- fixed: 6 observed, 6 correct, source_mode actual_local_policy
- meta: 6 observed, 5 correct, source_mode actual_meta
- manual: not_run, 6 cells missing (the user declined to perform the human arm)
Combined artifact: `validation/workflow_comparison_20261028.json`. `workflow_gain_supported`
remains false in every report.

Twelve live provider requests were made in total, $0.60 reserved locally. Every response again
returned a null invoiced amount, so cost_status stays unknown and no spend is asserted.
Attempt 1 (effort=medium, 512-token cap) failed all six cells with finish_reason=length and is
preserved in `validation/workflow_meta_arm_20261028.json` with
`validation/workflow_meta_arm_attempt1_length_failure.json`. Attempts 2 and 3 (effort=low,
1024-token cap) are `workflow_meta_probe_20261028.json` and `workflow_meta_remainder_20261028.json`,
summarised in `workflow_meta_arm_success_20261028.json`.

Meta's one incorrect cell is WTmismatchG32V: it answered accepted/validated while the
deterministic guard answered wt_mismatch, because it never checked the reference residue
identity at position 32. Both verdicts are stored in the same cell. This measures rule
application inside a closed set of six reason codes with the registered rules supplied in
context; it does not establish rule discovery, scientific skill, time saving or cost benefit,
and no manual arm exists to compare against.

Viewer: `app/viewer_data.provenance_chain` is a pure read-model function (imports stay within
the asserted json/pathlib/csv/io/hashlib/math set) that walks reference and pinned model
digests to the score artifact, the MCP tool result, the replay export and the rendered bytes,
verifying each stored commitment and marking mismatches or absent stages. The Evidence tab
renders it with the scope line stating it is not signed, anchored or tamper-proof. A 3D
structure viewer was declined against the unverified coordinate mapping. A real ordering defect
was found and fixed: the sidebar painted before the palette was injected, measuring ~105 peak
glyph brightness against 255 after the fix.

Demo: six screenshots of the actually running local workbench were captured over loopback with
the installed browser (`local_artifacts/workbench_demo_20261028/capture_ui.py`, viewport only,
no desktop content, zero provider calls). Narration segment 6 previously stated that the Meta
arm had not been run and is now factually wrong; it was rewritten and re-synthesised to the
measured 6/6 and 5/6 result, and segment 7 was shortened to fit its 15-second budget. The
earlier `local_artifacts/demo/BioPilot_Bench_180s_LOCAL_DRAFT.mp4` draft and its receipts are
preserved unchanged.

Tests: `tests_app/test_workflow_suite.py` 48 passed; `tests_app/test_viewer.py` 36 passed.
Full regression after the Meta arm work was 548 passed with the single known MANIFEST.sha256
inventory drift, which is regenerated at packaging time.

Still not done and still not authorised: no GitHub publication, no external deployment, no
contest submission, no manual arm, no GPU or Modal work, no biological efficacy claim.

## 2026-11-03 — demo camera rebuild and README GIF

Changed files: `local_artifacts/final_demo_20261102/build_video.py`,
`local_artifacts/final_demo_20261102/verify_video.py`,
`local_artifacts/final_demo_20261102/build_readme_gif.py` (new),
`docs/images/biopilot-demo.gif` (new), `submission/readme_gif_receipt.json` (new),
`submission/video_current_ui_20261102_receipt.json`, `README.md`,
`demo/FINAL_VIDEO_20261102_KO.md`, `docs/DECISIONS.md`, `MANIFEST.sha256`.

The published cut drifted its zoom across whole shots, highlighted most of the page,
and crossfaded consecutive shots that shared one screenshot, which double-exposed the
UI text: the encoded frame at 68 s had doubled headings. The camera is now one fast
ease-out push-in per shot followed by a static hold, the zoom is solved from the
emphasis target so a highlight cannot be cropped by its own shot, and same-screenshot
reframes are cut rather than dissolved. Highlights are a rounded stroke with a halo
over dimmed surroundings and appear only after the camera settles.

Re-encode verified locally: 180 s, 1920x1080, 30 fps, 5400 frames, 9 chapters, 27
measured caption cues, no whole-file decode error, mean -16.9 dBFS and peak -1.4 dBFS.
Output is 17.6 MB against the previous 41.6 MB because static holds compress far better
than continuous drift. `verify_video.py` now also asserts that every emphasis target
stays inside its own shot's crop from the moment the highlight appears, and that no
same-source reframe is dissolved; both guards pass over all 25 highlighted shots.

A 14-second silent looping README GIF was added at `docs/images/biopilot-demo.gif`
(760x428, 177 frames, 2.4 MB) covering the guard refusal, local validation, the recorded
run's counters, the ranked candidates and the missing-atom notice. It reuses the existing
capture hashes; no new screenshot, Meta request or GPU work. Captions move above the
highlight when the target sits low so they never cover it.

Still not done and still not authorised: the private demo Release still carries the
2026-11-02 asset and the re-encoded MP4 has not been uploaded; no GitHub publication,
no external deployment, no contest submission, no GPU or Modal work, no biological
efficacy claim. Full human listening review of the audio remains pending.

## 2026-11-03 — repository root flattened

Changed files: seven `requirements-*.txt` moved to `requirements/*.txt`;
`BIOPILOT_ATLAS_KO.md`, `OPEN_ISSUES.md`, `SOURCES.md`, `VALIDATION.md` moved to `docs/`;
references updated in `README.md`, `docs/VALIDATION.md`, `docs/BIOPILOT_ATLAS_KO.md`,
`docs/IMPLEMENTATION_KO.md`, `checks/check_reproduction.py`, `checks/validate_package.py`,
`compliance/THIRD_PARTY_NOTICES.md`, `prompts/coding/00_bootstrap_ko.txt`,
`submission/README.md`, `submission/REPRODUCE_KO.md`, `requirements/workbench.txt`;
plus `MANIFEST.sha256`, `docs/DECISIONS.md`.

Root entries went from 40 to 30. A sweep confirms no `requirements-` reference and no
root-relative link to a moved document survives outside the frozen historical records,
which keep the old paths on purpose. The `-r` include in the workbench pin resolves.

Tests: package validator 2149 checks, 0 failures; `pytest -q` 785 passed, 2 skipped,
12 subtests passed. The GIF was also re-delivered at 760x428 and 2.4 MB so the README
image loads quickly; the bytes on GitHub match the local blob exactly.

Still not done and still not authorised: the repository stays private until the owner
publishes it at the end; the demo Release still carries the 2026-11-02 video and the
re-encoded cut has not replaced it; no external deployment, contest submission, GPU or
Modal work, and no biological efficacy claim.


## 2026-11-03 — clarify installed model capabilities

Changed README.md to distinguish saved ESM-2 results, the experimental 1ISP reference,
and stored real ESMFold2 WT / ESM3 A32V predictions. Added the exact Structure expander
and selector labels, linked the existing GPU operator guide, and stated that New review
does not launch optional folding or provision RunPod. The current video omits those
prediction views. No application, model, score, rank or original receipt changed.

Verification: load_predictions returned both stored predictions with sequence_verified=True;
pytest tests_app/test_prediction_view.py tests_app/test_optional_science.py
tests_app/test_viewer_structure.py -q -p no:cacheprovider
--basetemp=.cache/model_docs_check_20261103 --tb=short: 44 passed.
No new Meta call, GPU job, external sequence transfer or video edit. Fresh third-party
GPU installation and automatic remote execution remain unverified/unimplemented respectively.
Next allowed action: inspect stored prediction views; new GPU execution requires its own approval.


## 2026-11-03 — structure and Atlas demo edit

Changed README.md, submission/FORM_ANSWERS_20261103.md, compliance/EVENT_CONTRIBUTIONS.md,
demo/FINAL_VIDEO_20261102_KO.md; added two measured EN/KO subtitle files, two README GIFs,
submission/readme_structure_gifs_20261103.json and submission/structure_atlas_video_20261103.json.
Final videos remain in local_artifacts/structure_demo_20261103, outside the Git source inventory.
The original cut and YouTube URL are preserved; the owner has not uploaded this revised cut.

The new 180-second flow preserves the original input/approved execution/candidates and adds
1ISP reference -> stored ESMFold2 WT -> stored ESM3 A32V -> exact-WT Atlas snapshot -> actual
Meta trace -> input/report evidence. The repetitive closing limitation narration was replaced
with the product value, while model/input/replay labels and scientific limits remain accurate.
No API, GPU, new Atlas lookup, deployment or submission occurred; no scientific artifacts changed.

Tests: 44 prediction/optional-science/reference-view tests passed. Both final videos are
180.000 seconds, 1920x1080, 30 fps, 5400 frames, nine chapters, with full decode errors zero.
The clean video contains EN/KO optional subtitle tracks; separate SRTs contain 25 measured cues.
Sampled 45.8-86s frames retain 50.9-53.7 dB PSNR against the original clean cut. Reviewed final
encoded full-size structure, Atlas, evidence and caption samples; corrected Atlas highlight and
caption/model-label overlap. Full human audio listening and revised YouTube playback are not verified.
Next allowed action: owner reviews the new local cut and uploads it; update the README URL only
when the replacement URL is available. Fresh model/GPU work still requires separate approval.

Package validation after the media/documentation additions: 2237 checks, 0 failures.
Added README/guide links, both GIF loops and all 25 EN/KO subtitle intervals also passed.
Publication follow-up: normalized the two public SRT files to LF so the Git blobs and MANIFEST hashes agree; local MP4/SRT delivery files are preserved.


## 2026-11-04 — simplify hardware wording in the demo

Changed the structure narration to describe full-reference prediction and interactive
inspection, and changed the editorial labels to ESMFold2 WT / ESM3 A32V saved prediction.
The README feature copy and structure GIF captions now emphasize these functions rather
than the GPU model. Actual scientific receipts and hardware/reproduction records remain
unchanged. Source UI captures are preserved; this removes hardware emphasis from the edit,
not provenance from the original application evidence.

The previous local videos, narration, subtitle timing and verification receipt are preserved
in local_artifacts/structure_demo_20261103/before_hardware_wording_edit. Updated files use the
same delivery paths. The new wording requires no product Meta call, GPU job or Atlas lookup;
only the public demo narration is regenerated with the existing speech service. Existing
YouTube URL still identifies the older owner-uploaded cut.

Media verification: both outputs are 180.000 seconds, 1920x1080, 30 fps, 5400 frames, nine chapters; full decode errors zero. Measured subtitle cues remain aligned and ordered.
Package validation after the wording revision: 2237 checks, 0 failures.


## 2026-11-04 — align README introduction with the demo wording

Changed README.md to describe stored structure predictions and interactive inspection, without foregrounding GPU hardware. Existing GIFs, actual model/input labels, execution guides and scientific records remain intact. Documentation-only change; no new model calls or GPU jobs.
Validation: .venv/Scripts/python.exe checks/validate_package.py — 2237 checks, 0 failures. Next action: view the updated public README; no new execution approval required.
