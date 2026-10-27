# 10. Biological correction ledger

This document and docs/04, docs/11 and docs/12 supersede the v1 scientific assumptions.

| ID | Risk | Implemented correction | Remaining evidence |
|---|---|---|---|
| BIO-01 | ESM preference called thermostability | Objective profiles, no calibration claim, fixed score type, report contract | Real inference and held-out evaluation |
| BIO-02 | T50 confused with Tm/activity | Registered assay endpoint and evaluator-only WT rule | Raw data units/transformations and matched WT |
| BIO-03 | Mature/full/PDB numbering mixed | Exact sequence mapping; S108/D164/H187 guards | mmCIF author/label/atom join |
| BIO-04 | Predicted structure used as experimental validation | 1ISP reference evidence distinguished from predicted candidate evidence | Coordinate download and geometry review |
| BIO-05 | 3,439 and 2,172 treated as same cohort | Reconciliation record; denominator/failure rules | Row-level raw/curated audit |
| BIO-06 | Agent credited for fixed ESM ranking | Separate workflow and rank metrics | Controlled run artifacts |
| BIO-07 | Meta Atlas and Biohub Atlas conflated | Provider IDs and optional independent adapters | Live endpoint, license and account verification |
| BIO-08 | Formal tests called biology validation | New validation report separating guards from efficacy | No experimental validation performed |

## What is positively verified here

The two supplied public sequences match exactly in a unique 181-aa interval; the corresponding
three residues have the stated identities. Public source metadata/definitions were inspected.
Offline guards check the intended failure behavior. These are distinct checks, not one accuracy score.

## What is deliberately blocked

No geometry from sequence-only mappings; no WT hit-rate from a median label; no calibrated
T50 forecast from ESM logits; no mixed model/context ranking; no biological superiority from an
unchanged score policy; no deployment/API authentication claim from a design template.

## Source acquisition limits

Container downloads failed for raw mmCIF, full assay metadata and the paper PDF. The web tool
could read the RCSB deposited FASTA, PDB summary, ProteinGym reference row and the paper text.
PDF screenshot attempts failed, so no claim is made about figures/table layout. The package
contains transcribed sequence/metadata facts with their URLs, not fabricated raw file hashes.

The RCSB structure-citation abstract also uses a His155 label while the assay paper uses H156
in mature-sequence numbering. Do not settle atom numbering by choosing one prose label:
join the exact mmCIF author/label sequence scheme and verify residue identity first [S17-S19].
