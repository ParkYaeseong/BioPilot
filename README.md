# BioPilot Atlas v3 | MCP-first hackathon design and prompt pack

**Version:** 3.0 / 2026-10-27. **Owner:** Yaeseong Park.

**A verifiable protein-variant review agent, not a validated enzyme optimizer.**
A Meta model requests bounded scientific tools through MCP. Deterministic code checks biological
constraints, runs ESM, records provenance and ranks candidates. A thin local result viewer is optional.

This ZIP is a **complete replacement for v2**. It includes design documents, prompts, proposed
contracts, source-traceable reference metadata and runnable **offline guard examples**.
It does **not** contain a working MCP server, a production host, a completed UI, live API integration,
measured ESM performance, a demo video or a submitted contest entry.

## Start

1. Read `START_HERE_KO.md`, `docs/14_hackathon_rules_and_strategy.md` and `docs/15_mcp_contract_and_hosts.md`.
2. Run `python -m unittest discover -s tests -v` and `python checks/validate_package.py`.
3. Pass `prompts/coding/00_bootstrap_ko.txt` to WORK, Muse Code, Codex or Claude Code in this folder.
4. Follow `docs/superpowers/plans/2026-10-27-v3-mcp-hackathon.md`.
5. Use the application implementation only after its own tests and permission gates pass.

## Product decisions

| Decision | v3 default |
|---|---|
| Track / theme | Indie Developer / Push the Frontier; Build for Your World is an honest fallback positioning |
| Core product | Reusable guarded MCP tools + one Meta-driven host |
| Reliable reference host | Small Python host with Meta API and an MCP client; no arbitrary shell or label access |
| Existing host option | Muse Code calling BioPilot MCP, only after actual compatibility, permissions and isolation checks |
| Demo interface | Optional Streamlit viewer of the same events/artifacts; no Next.js platform or installer required by this plan |
| Scientific scope | Public Lipase A, single substitutions, ESM-ranked hypotheses; no calibrated T50 prediction |
| Evidence for judges | Real Meta tool calls, real ESM results, constraint handling, source lineage and honest workflow comparison |
| Recording | Planned 180-second demo, English narration/subtitle draft and Korean guide |

A hosted website/desktop installer is **not specified as mandatory in the participant-guide snapshot
available in this conversation**. This is not an official exemption: recheck the final submission
form, demo access requirements and any later rules. A replay is a fallback, not a working-product substitute.

## Latest rule basis and limits

The directly-read official participant guide in the conversation lists Impact 30%, Meta tooling 25%,
Technical execution 20%, Demo 25%; public repository; three-minute video; and the November 4, 21:00
America/New_York deadline (November 5, 11:00 Asia/Seoul). This revision could not reopen the
connected browser or retrieve the event detail page. These facts are marked **conversation-captured
primary-source text**, not freshly authenticated rules. See `compliance/rules_snapshot.json`.

## Preserved scientific safeguards

The exact full-212/mature-181 sequence correspondence and protected full S108/D164/H187 remain.
Sequence mapping is not PDB atom mapping. ESM preference is not thermal stability; pLDDT is not
fitness; median-bin labels are not WT improvements. Dataset/WT audit and actual model evaluation
remain pending. `checks/science_contracts.py`, its 39 original tests, and source reference/evaluator
files are preserved byte-for-byte. No labels may be exposed as MCP tools, resources or files.

## Key folders

- `docs/`: product, architecture, biology, rules, MCP, evidence, budget and submission plan.
- `prompts/`: coding, runtime, review and bilingual recording/host instructions.
- `reference/`: public sequences and conservative target registry, no actual candidate labels.
- `evaluation_private/`: evaluator-only protocol metadata; excluded from every runtime bundle.
- `schemas/`, `examples/`, `config/`, `templates/`: proposed contracts and clearly labeled scaffolding.
- `demo/`, `submission/`, `compliance/`: storyboard, blank evidence records and rule/provenance ledgers.
- `checks/`, `tests/`, `validation/`: runnable offline checks and actual verification receipts.

Do not give the prediction agent this whole repository. A coding assistant can work on development
files, but a scientific evaluation session must use a separate allowlisted workspace with no outcome
material. Never publish this design package unchanged as proof of in-event implementation.
