"""The coordinate join is derived from a real mmCIF, never from an assumed offset.

docs/11 requires the join to come from _pdbx_poly_seq_scheme x _atom_site on
entity/chain/label_seq_id, with auth numbering, insertion codes and missing
residues kept as distinct facts. These tests pin that derivation. The synthetic
fixture runs everywhere; the integration test runs only where the approved local
1ISP copy exists, and is reported as skipped otherwise.
"""
from pathlib import Path

import pytest

from app.core.coordinate_join import derive_coordinate_join, parse_mmcif_loops

ROOT = Path(__file__).resolve().parents[1]
LOCAL_1ISP = ROOT / 'local_artifacts/1isp_quarantine_20261028/1ISP.cif'

# Four deposited residues on chain A. Residue 1 is deposited but unmodelled, so
# it carries a scheme row and no atoms - the exact shape that must not silently
# become "present" or shift every downstream number by one.
FIXTURE = """data_TEST
#
loop_
_pdbx_poly_seq_scheme.asym_id
_pdbx_poly_seq_scheme.entity_id
_pdbx_poly_seq_scheme.seq_id
_pdbx_poly_seq_scheme.mon_id
_pdbx_poly_seq_scheme.pdb_seq_num
_pdbx_poly_seq_scheme.auth_seq_num
_pdbx_poly_seq_scheme.pdb_mon_id
_pdbx_poly_seq_scheme.auth_mon_id
_pdbx_poly_seq_scheme.pdb_strand_id
_pdbx_poly_seq_scheme.pdb_ins_code
A 1 1 ALA 1 ?  ?   ?   A .
A 1 2 GLU 2 2  GLU GLU A .
A 1 3 HIS 3 3  HIS HIS A .
A 1 4 SER 4 4  SER SER A .
#
loop_
_pdbx_unobs_or_zero_occ_residues.id
_pdbx_unobs_or_zero_occ_residues.auth_asym_id
_pdbx_unobs_or_zero_occ_residues.auth_seq_id
_pdbx_unobs_or_zero_occ_residues.auth_comp_id
1 A 1 ALA
#
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.label_atom_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_seq_id
_atom_site.auth_seq_id
_atom_site.auth_asym_id
_atom_site.pdbx_PDB_model_num
ATOM 1 CA GLU A 2 2 A 1
ATOM 2 CB GLU A 2 2 A 1
ATOM 3 CA HIS A 3 3 A 1
ATOM 4 CA SER A 4 4 A 1
#
"""


def test_loop_parser_reads_the_categories_the_join_depends_on():
    loops = parse_mmcif_loops(FIXTURE)
    assert len(loops['_pdbx_poly_seq_scheme']) == 4
    assert len(loops['_atom_site']) == 4
    assert loops['_pdbx_poly_seq_scheme'][0]['mon_id'] == 'ALA'
    assert loops['_pdbx_poly_seq_scheme'][0]['pdb_mon_id'] == '?'


def test_join_marks_a_deposited_but_unmodelled_residue_as_not_observed():
    join = derive_coordinate_join(FIXTURE, 'AEHS', chain='A')
    rows = join['rows']
    assert [row['deposited_position'] for row in rows] == [1, 2, 3, 4]
    assert [row['residue'] for row in rows] == ['A', 'E', 'H', 'S']
    assert [row['coordinate_observed'] for row in rows] == [False, True, True, True]
    assert rows[0]['pdb_auth_seq_id'] == '1'
    assert rows[0]['pdb_label_seq_id'] == 1
    assert join['unmodelled_deposited_positions'] == [1]
    assert join['residue_identity_mismatches'] == []
    assert join['auth_minus_label_offsets'] == [0]
    assert join['insertion_codes'] == []


def test_join_refuses_a_sequence_that_does_not_match_the_structure():
    """Never mutate the scientific source sequence to force a match (docs/11)."""
    with pytest.raises(ValueError, match='identity'):
        derive_coordinate_join(FIXTURE, 'AEHW', chain='A')


def test_join_refuses_a_length_disagreement():
    with pytest.raises(ValueError, match='length'):
        derive_coordinate_join(FIXTURE, 'AEH', chain='A')


@pytest.mark.skipif(not LOCAL_1ISP.is_file(),
                    reason='approved local 1ISP copy is absent; join cannot be re-derived here')
def test_real_1isp_join_matches_the_registered_rule():
    """The product's numbering rule must come from the real file, not an assumption."""
    deposited = (ROOT / 'reference/1ISP_A_deposited_181.fasta').read_text(
        encoding='utf-8').split('\n', 1)[1].replace('\n', '')
    join = derive_coordinate_join(LOCAL_1ISP.read_text(encoding='utf-8'), deposited, chain='A')
    assert len(join['rows']) == 181
    assert join['residue_identity_mismatches'] == []
    assert join['auth_minus_label_offsets'] == [0]
    assert join['insertion_codes'] == []
    # Deposited 1 and 181 are deposited but carry no atoms. docs/04 records that
    # 1ISP metadata does not identify these two positions; this derivation does.
    assert join['unmodelled_deposited_positions'] == [1, 181]
    observed = {row['deposited_position']: row['coordinate_observed'] for row in join['rows']}
    assert observed[1] is False and observed[181] is False
    # The catalytic triad (full 108/164/187 -> deposited 77/133/156) is modelled.
    for deposited_position, expected in ((77, 'S'), (133, 'D'), (156, 'H')):
        row = join['rows'][deposited_position - 1]
        assert row['residue'] == expected
        assert row['coordinate_observed'] is True
        assert row['pdb_auth_seq_id'] == str(deposited_position)


def test_registered_residue_map_matches_the_verified_join_rule():
    """The shipped map must carry the derived join exactly, with its source pinned."""
    import json
    mapping = json.loads((ROOT / 'reference/residue_map.json').read_text(encoding='utf-8'))
    assert mapping['coordinate_index_join_verified'] is True
    assert mapping['geometry_validated'] is False
    source = mapping['coordinate_source']
    assert source['pdb_id'] == '1ISP' and source['chain'] == 'A'
    assert source['sha256'] == (
        '7ab626e5c5c1bec8ed8acdd4675f105939ef982542a559084860d16e4b07cc10')
    rows = mapping['mapping']
    assert len(rows) == 212
    for row in rows:
        full = row['full_position']
        if full < 32:
            assert row['pdb_label_seq_id'] is None
            assert row['pdb_auth_seq_id'] is None
            assert row['coordinate_observed'] is None
        else:
            assert row['pdb_label_seq_id'] == full - 31
            assert row['pdb_auth_seq_id'] == str(full - 31)
            assert row['pdb_insertion_code'] is None
            assert row['coordinate_observed'] is (full not in (32, 212))


def test_catalytic_triad_is_modelled_and_the_demo_position_is_not():
    """All 19 saved candidates are A32X, and full 32 carries no atoms. Say so."""
    import json
    rows = json.loads((ROOT / 'reference/residue_map.json').read_text(
        encoding='utf-8'))['mapping']
    for full, residue in ((108, 'S'), (164, 'D'), (187, 'H')):
        assert rows[full - 1]['residue'] == residue
        assert rows[full - 1]['coordinate_observed'] is True
        assert rows[full - 1]['protected'] is True
    assert rows[31]['full_position'] == 32 and rows[31]['residue'] == 'A'
    assert rows[31]['coordinate_observed'] is False
    assert rows[211]['full_position'] == 212 and rows[211]['coordinate_observed'] is False
