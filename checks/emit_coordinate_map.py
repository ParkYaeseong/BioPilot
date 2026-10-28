"""Emit the verified coordinate map from an approved local mmCIF (docs/11 step 6).

Deliberately explicit and manual: the coordinate file is never fetched here, only
read from a path the operator passes in. The emitted map carries the source file's
sha256 so the registered contract pins the exact bytes the join came from.

The index join (deposited position <-> author numbering <-> observed flag) is a
separate fact from atom geometry. This script registers the first and leaves the
second false; nothing here validates geometry, side-chain completeness or function.

Usage:
  .venv/Scripts/python.exe checks/emit_coordinate_map.py <path-to-1ISP.cif>
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.coordinate_join import derive_coordinate_join  # noqa: E402

MATURE_REGION_START = 32  # full position of deposited position 1


def _fasta(path):
    return path.read_text(encoding='utf-8').split('\n', 1)[1].replace('\n', '')


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    cif_path = Path(sys.argv[1])
    cif_bytes = cif_path.read_bytes()
    source_sha256 = hashlib.sha256(cif_bytes).hexdigest()

    deposited = _fasta(ROOT / 'reference/1ISP_A_deposited_181.fasta')
    join = derive_coordinate_join(cif_bytes.decode('utf-8'), deposited, chain='A')

    map_path = ROOT / 'reference/residue_map.json'
    current = json.loads(map_path.read_text(encoding='utf-8'))
    by_deposited = {row['deposited_position']: row for row in join['rows']}

    rows = []
    for entry in current['mapping']:
        row = dict(entry)
        deposited_position = row.get('deposited_sequence_position')
        joined = by_deposited.get(deposited_position) if deposited_position else None
        if joined is None:
            # Positions 1-31 are not part of the deposited construct. Unknown stays null.
            row['pdb_label_seq_id'] = None
            row['pdb_auth_seq_id'] = None
            row['pdb_insertion_code'] = None
            row['coordinate_observed'] = None
        else:
            if joined['residue'] != row['residue']:
                raise SystemExit(
                    f"Residue identity disagreement at full {row['full_position']}: "
                    f"map {row['residue']} vs structure {joined['residue']}")
            row['pdb_label_seq_id'] = joined['pdb_label_seq_id']
            row['pdb_auth_seq_id'] = joined['pdb_auth_seq_id']
            row['pdb_insertion_code'] = joined['pdb_insertion_code']
            row['coordinate_observed'] = joined['coordinate_observed']
        rows.append(row)

    missing_full = [row['full_position'] for row in rows if row['coordinate_observed'] is False]
    emitted = {
        'status': 'index_join_verified_geometry_unvalidated',
        'reference_sha256': current['reference_sha256'],
        'mature_sha256': current['mature_sha256'],
        'coordinate_source': {
            'pdb_id': '1ISP',
            'chain': 'A',
            'sha256': source_sha256,
            'format': 'mmCIF',
            'join_method': '_pdbx_poly_seq_scheme x _atom_site on chain/label_seq_id',
            'auth_minus_label_offsets': join['auth_minus_label_offsets'],
            'insertion_codes': join['insertion_codes'],
            'deposited_residue_count': join['deposited_residue_count'],
            'modelled_residue_count': join['modelled_residue_count'],
            'unmodelled_full_positions': missing_full,
            'residue_identity_mismatches': join['residue_identity_mismatches'],
        },
        'mapping': rows,
        'coordinate_index_join_verified': True,
        'geometry_validated': False,
        'limits': ('Verified correspondence of sequence index to PDB author numbering and to '
                   'the presence of atoms. This is not validated atom geometry, not side-chain '
                   'completeness, and not evidence about any mutant or about retained function.'),
    }
    map_path.write_text(json.dumps(emitted, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'Emitted verified coordinate map from {cif_path.name} ({source_sha256[:12]}…)')
    print(f'  deposited {join["deposited_residue_count"]}, modelled {join["modelled_residue_count"]}, '
          f'unmodelled full positions {missing_full}')
    print(f'  auth-label offsets {join["auth_minus_label_offsets"]}, '
          f'insertion codes {join["insertion_codes"] or "none"}')


if __name__ == '__main__':
    main()
