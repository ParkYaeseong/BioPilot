# Hackathon contribution scope

Prepared November 3, 2026. Event window supplied by the participant: October 26–November 4, 2026.
Solo entrant: **Yaeseong Park**. Codex and Claude provided substantial development
assistance; they are disclosed as tools, not additional human team members.

## Features presented as this entry's event implementation

| Contribution | Implementation and evidence | What is new here |
|---|---|---|
| Controlled Meta → MCP protein-review workflow | `app/host/`, `app/mcp_server.py`, `app/core/`; implementation commit `c0cb60f` on October 27 | Product host, permitted-tool integration and bounded execution; not the Meta model or MCP protocol |
| Enforced scientific and execution guards | `app/core/`, `app/bench_intake.py`, `app/bench_store.py`, `app/bench_execution.py` | Product-side enforcement of full-reference identity/numbering, protected sites, permissions, call limits and durable execution state; underlying scientific contracts/helpers are reused and disclosed below |
| Unified file/request → approval → execution → result workbench | `app/bench.py`; commit `ed666f2` on October 29 | Local Streamlit workflow, saved review navigation, recent reviews and explicit failure/partial/completed states |
| Inspectable numerical results and provenance | `app/viewer_data.py`, `app/viewer_render.py`, `app/review_checks.py`, `app/viewer.py` | Artifact-derived tables, common ranking policy, comparison controls, public tool trace and local checksum inspection; not experimental enzyme improvement |
| Candidate-linked reference structure review | `app/viewer_structure.py`, `app/core/coordinate_join.py`; commit `2d2617c` on October 29 | Local integration, reference/author numbering checks, missing-atom refusal and selected-candidate highlighting; not a new 3D renderer or a newly solved structure |
| Guided onboarding and responsive visual refinement | `app/guided_tour.py`, `app/new_review_tour.py`, `app/tour_spotlight.*`, viewer styles and brand | Original integration of the acting tours and workbench presentation; interaction patterns inspired by public interfaces |
| Reproduction package, tests and demo production | `checks/`, `tests_app/`, `requirements/`, `demo/`, `submission/`, `validation/` | Credential-free offline reproduction checks, execution receipts, documentation and a 180-second edited real-application demo |

The authoritative paths are the files in this repository. Evidence dates describe
records and do not independently prove authorship or organizer acceptance. Some
changes were committed after implementation; commit dates have not been backdated.

## Reused material: not claimed as new event inventions

| Material | Reuse boundary |
|---|---|
| Supplied v2/v3 planning, target contracts and guard algorithms | The v2 material is recorded as October 26 and the supplied v3 package was preserved October 27 in `5898a2f`. These pre-existed this implementation and are conservatively disclosed as reused material, even where a date falls within the stated event window. Original design is not relabeled as newly written application code. |
| Meta `muse-spark-1.3` | Existing provider model. This entry builds the bounded scientific tool workflow around it. |
| ESM-2, ESM3, ESMFold2 and Atlas | Existing scientific models/services/data sources. Adapters and evidence views are integration work; model architectures, training, database and scientific predictive validity are not our contributions. Optional GPU outputs are separate from the default sequence-review run. |
| Public Lipase A reference and PDB 1ISP | Existing public scientific inputs. Residue correspondence and visualization integration are checked locally; this entry did not determine the experimental structure. |
| Streamlit, MCP SDK, PyTorch, Transformers and other dependencies | Existing libraries installed from pinned requirements. |
| Vendored 3Dmol.js | Existing BSD-licensed renderer with retained upstream notices; not original event code. |
| RAPID and public UI references; AionUi GIF | Interaction/editing inspiration only. No RAPID/AionUi code or reference GIF frames are included in the demo. |

See [third-party notices](THIRD_PARTY_NOTICES.md), [development history](DEVELOPMENT_HISTORY.md),
[originality ledger](originality_ledger.csv) and [AI-development disclosure](AI_DEVELOPMENT.md).
Historical ledger wording is retained; the exact coding-start time and any blanket
reuse ruling are not invented. Owner-reported participant eligibility confirmation
does not independently establish every rights or reuse question.

## Demo scope

The demo presents the event-built file intake, validation/approval workflow, actual
Meta/MCP/CPU ESM execution, candidate review, reference-structure integration, trace
and evidence views. The opening chapter identifies the event-built workflow.
Public models and biological inputs are supporting dependencies, not new discoveries.
Candidate/reference illustrations may be reused between actual runs only after
checking identical candidate and score-artifact objects. Camera movement, highlights
and time compression are editing effects; no UI state or model progress is fabricated.

ESM sequence preferences do not establish T50, activity, stability, solubility or
retained function. This is a sequence evidence assistant, not a validated enzyme optimizer.

## License scope

The repository's original project code and documentation are offered under the
[MIT License](../LICENSE). Third-party code, reference data, model weights/services
and separately governed assets retain their respective terms; MIT does not relicense
them or grant model/API access. Model weights and owner credentials are not bundled.
