# 11. Target, sequence and structure registration

## Supplied data

`reference/lipase_full_212.fasta` is the ProteinGym reference sequence [S11].
`reference/1ISP_A_deposited_181.fasta` is the deposited RCSB entity sequence [S19].
The local hashes in `target_profile.json` identify these sequence strings; they are not an upstream
release commit or mmCIF checksum. `source_snapshot.json` records the capture method and limitations.

`checks/science_contracts.py::exact_sequence_map` verifies a unique exact substring, giving
mature 1 -> full 32 and mature 181 -> full 212. Generic gapped/ambiguous mappings are rejected,
not approximated. Catalytic-source annotations are mapped through this verified correspondence:
S77 -> S108; D133 -> D164; H156 -> H187 [S17].

## Sequence-only is not coordinate-complete

Every row in `residue_map.json` carries full and mature indices. All atom-numbering and observed
coordinate fields are null. Do not infer the two unmodeled residue identities from the total count.
The mature numbering in this pack means the 181-aa deposited sequence index, not an asserted PDB
author numbering scheme. The reference prefix outside positions 32-212 is excluded from this
interactive mature-enzyme scope; that is not a general rule for all secretion biology.

## Required coordinate import in WORK/development

1. Download official 1ISP mmCIF only through an approved read-only source fetch; record URL,
   retrieval time, exact file hash and entry revision. Do not use an HTML error page as mmCIF.
2. Read the entity polymer sequence and require equality with the registered 181-aa sequence.
3. Join `_pdbx_poly_seq_scheme` with `_atom_site` using entity/chain/label_seq_id. Preserve
   auth_seq_id, insertion code, model number and alternate conformers as distinct fields.
4. Verify actual residue identities, not only counts. Identify missing atoms/residues explicitly;
   CA-only availability is not enough for side-chain geometry. Record chosen conformer policy.
5. Compare full -> mature -> structure numbering at every mapped site, including the triad.
6. Only then emit a new verified coordinate map with the source-file hash. Never mutate the
   scientific source sequence to force a match. Changes require a new target profile version.

The supplied `require_coordinate_row` guard blocks null/absent mappings; it does not itself parse
or validate mmCIF. A production importer and its real-coordinate integration test are still to build.

## Inference context

Use the full 212-aa sequence for the initial masked-marginal baseline and log that choice.
The mature 181-aa sequence is a biologically motivated alternative context, but its scores may
differ. Register it as a separate ablation before observing evaluation labels. Do not mix contexts,
silently crop, or use mature numbering with a full-reference tokenizer.

## Protection is not functional proof

The triad is a minimal known functional constraint, not a complete function-preservation model.
Substrate specificity, catalytic efficiency, folding, expression and secretion can change at other
positions. Do not promise preserved activity because three positions were left unchanged.
