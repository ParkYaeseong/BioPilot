# BioPilot Bench

**From a protein-variant request to an inspectable scientific review.**

BioPilot Bench brings file validation, Meta-directed scientific tools and candidate
review into one local workspace. Meta selects permitted MCP tools and explains the
evidence; code enforces scientific constraints, execution limits and ranking.

[Demo](#demo) · [Quickstart](#quickstart) · [Event contributions](compliance/EVENT_CONTRIBUTIONS.md) · [MIT License](LICENSE)

## Demo

![BioPilot Bench: input validation, candidate review and reference structure inspection](docs/images/biopilot-demo.gif)

Upload a public Lipase A FASTA, approve a review, then inspect candidates, structure and evidence.

**[Three-minute demo](https://github.com/ParkYaeseong/BioPilot/releases/tag/demo-2026-11-02)**
· [Download MP4](https://github.com/ParkYaeseong/BioPilot/releases/download/demo-2026-11-02/BioPilot_Bench_180s_EN.mp4)
· [English subtitles](https://github.com/ParkYaeseong/BioPilot/releases/download/demo-2026-11-02/BioPilot_Bench_180s_EN.srt)
· [한국어 자막](https://github.com/ParkYaeseong/BioPilot/releases/download/demo-2026-11-02/BioPilot_Bench_180s_KO.srt)

## Features

- **Guarded input:** validate reference identity, full-reference numbering and protected catalytic sites before execution.
- **Meta + MCP:** run an explicitly approved, bounded review through `muse-spark-1.3` and registered scientific tools.
- **Candidate comparison:** inspect all 19 non-WT alternatives at an approved position under one ranking policy.
- **Interactive structure:** inspect candidate positions in the public reference structure with verified residue correspondence and missing-atom handling.
- **Traceable results:** review recorded tool calls, source hashes and saved results, with guided onboarding.

## Quickstart

Windows · Python 3.14. From a fresh checkout:

```powershell
py -3.14 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements/workbench-win-py314.lock.txt
.venv/Scripts/python.exe -m streamlit run app/bench.py --server.address 127.0.0.1 --server.port 8522 -- --state-dir .runtime/judge-review --artifact demo/artifacts/unified_review_20261029.replay.json
```

Open **http://127.0.0.1:8522/** to explore saved results or start **New review**.
Try `A32V` for a valid input or `S108A` to see the catalytic-site guard.

Saved results and input checks run offline. New execution requires your own Meta
credentials, pinned local ESM weights and explicit approval.
[Installation and reproduction](submission/REPRODUCE_KO.md) · [Execution setup](docs/IMPLEMENTATION_KO.md)

## Workflow

**Input & Validation → Agent Execution → Review Results**

Results are organized into **Overview / Candidates / Structure / Agent Trace / Evidence**.
Candidates and Structure share the inspected candidate. Reopening a saved review
reads its recorded results without starting another model call.

| Component | Role |
|---|---|
| Meta `muse-spark-1.3` | Select permitted tools and explain evidence |
| MCP server and Python core | Enforce guards, approvals and execution budgets |
| Local ESM-2 150M | Compute sequence preferences |
| Review workbench | Compare candidates and inspect structure, trace and provenance |

## Scope

The executable target is currently the registered public Lipase A full 212-residue
reference. ESM scores are sequence preferences, not experimental T50, activity,
stability or proof of retained function. Structure views distinguish the reference
from stored predictions and leave missing atom coordinates unmarked.

## Development and contributions

Built for the Meta Global AI Developer Hackathon by **Yaeseong Park**, with substantial
Codex and Claude development assistance. Event work includes the guarded Meta/MCP
workflow, unified workbench, evidence views and guided onboarding. Existing planning,
helper algorithms, public models, data and libraries are disclosed separately.

[Contribution breakdown](compliance/EVENT_CONTRIBUTIONS.md)
· [Development history](compliance/DEVELOPMENT_HISTORY.md)
· [AI assistance](compliance/AI_DEVELOPMENT.md)
· [Execution and validation records](docs/STATUS.md)

## License

Original project code and documentation: **[MIT](LICENSE)**.
Third-party components, models and data retain their own terms.
[Third-party notices](compliance/THIRD_PARTY_NOTICES.md).
