# Attribution and rights review — 2026-10-28

This inventory records dependencies and provenance. Rights clearance remains
pending; it does not grant redistribution rights or assign a project license.

| Material | Source / local record | Use and review still required |
|---|---|---|
| v2 design and scientific guards | `originality_ledger.csv`, `original_package_manifest.sha256`, original Git history | Preserve earlier authorship/dates; organizer reuse and ownership ruling pending |
| ESM-2 model/code | https://github.com/facebookresearch/esm | Identify exact model weight and code terms separately before distribution; weights are not bundled |
| Transformers, PyTorch, safetensors | `requirements-science.txt`, saved inference provenance | Retain upstream notices and review exact installed versions; no repackaged dependencies |
| MCP Python SDK | https://github.com/modelcontextprotocol/python-sdk/tree/v1.25.0 | Preserve upstream license/notice if redistributed |
| Streamlit | `requirements-viewer.txt` | Local viewer dependency; review upstream notices for distribution |
| Other Python dependencies | `requirements-dev.txt`, `requirements-checks.txt`, `requirements-modal.txt` | Pinned direct dependencies; clean setup/transitive lock and distribution review pending |
| Lipase reference and 1ISP sequence metadata | `reference/source_snapshot.json`, `sources.json` | Preserve each source/capture limitation; sequence correspondence is not atom geometry |
| 1ISP coordinate file (`reference/1ISP.cif`) | https://files.rcsb.org/download/1ISP.cif retrieved 2026-10-28, sha256 `7ab626e5…cc10` | RCSB states PDB archive data files are under **CC0 1.0 Universal Public Domain Dedication**, so redistribution is permitted; attribution to the original structure authors is requested, not required. Verified at https://www.rcsb.org/pages/usage-policy. Coordinates describe the wild-type reference, never a mutant |
| 3Dmol.js 2.5.2 (`app/vendor/3Dmol-min.js`) | https://cdn.jsdelivr.net/npm/3dmol@2.5.2/build/3Dmol-min.js retrieved 2026-10-28, sha256 `7b26bfd8…ce9a` | **BSD-3-Clause**; binary redistribution permitted while reproducing the copyright notice, conditions and disclaimer. Upstream notice retained verbatim at `app/vendor/3Dmol-min.js.LICENSE.txt`. Vendored deliberately so the viewer fetches no remote asset. Bundle incorporates GLmol/Three.js/jQuery-derived code under their own terms |
| Public assay / ProteinGym metadata | `sources.json`, evaluator provenance | Keep outcome data and evaluator material out of product runtime; confirm source-specific redistribution rights |
| Meta Model API | saved integration receipt / actual returned model | API output receipt does not establish account credit, billing or contest eligibility |
| Biohub ESM SDK v3.4.1.post1 | https://github.com/Biohub/esm/tree/v3.4.1.post1; isolated GPU environment receipts | Used as an installed dependency; SDK and large weights are not bundled. Retain upstream license/third-party notices when redistributing dependencies |
| ESM3 open and ESMFold2 | https://huggingface.co/biohub/esm3-sm-open-v1 ; https://huggingface.co/biohub/ESMFold2 ; pinned revision/file hashes under validation/ | Official metadata/model cards identified MIT; weights stay outside this repository. Small computed PDB outputs are separately labeled predictions; model output is not experimental validation |
| Biohub ESM Atlas | https://docs.biohub.ai/api/protein/atlas/proteins/get ; reference/atlas_registered_reference_20261028.json | Only a sanitized exact-WT identity/confidence snapshot is included. No general database redistribution, text corpus, homology search or structure-on-miss route |
| Development assistance | Codex and owner-reported Claude updates; AI_DEVELOPMENT.md | Substantial implementation assistance is disclosed separately from the product Meta runtime |

The original package names Yaeseong Park as owner. Confirm all contributors and
whether any institutional rights apply before publication. An unverified rights
field must remain pending. This file does not assert that third-party material
or earlier code was authored during the event.
