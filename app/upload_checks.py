"""Diagnostics over operator-supplied files. Local, in-memory, and claim-free.

Nothing here predicts anything. The two questions answered are "is this the protein
this tool is registered for" and "does your numbering actually join to your
coordinates" — the second being the class of silent error that makes a sequence-index
viewer highlight the wrong residue and present it as evidence.

Uploaded bytes stay on this machine. No provider, GPU, network or subprocess is
reachable from this module, so `external_sequence_upload_enabled` stays false and
remains true as a statement about the product.

Unlike the registered importer, which fails closed, these functions report a verdict
instead of raising: for a diagnostic tool, "your sequence does not match your
structure" is the answer, not an error.
"""
import hashlib

from app.core.coordinate_join import derive_coordinate_join, parse_mmcif_loops
from app.core.targets import (AMINO_ACIDS, MATURE_SHA256, REFERENCE_SHA256,
                              normalize_sequence)

MAX_SEQUENCE_BYTES = 64 * 1024
MAX_STRUCTURE_BYTES = 8 * 1024 * 1024

_NOT_REVIEWABLE = (
    'This tool is registered for one public reference. Its numbering frame, protected '
    'catalytic sites and coordinate join are specific to that entry, so another protein '
    'cannot be reviewed here without registering it as a new target.')


def _digest(sequence):
    return hashlib.sha256(sequence.encode('ascii')).hexdigest()


def check_sequence(text):
    """Identify an uploaded sequence against the registered target. No claim is made."""
    if not isinstance(text, str):
        return {'verdict': 'unreadable', 'reviewable': False, 'length': 0,
                'sha256': None, 'detail': 'Expected text.'}
    if len(text.encode('utf-8', 'ignore')) > MAX_SEQUENCE_BYTES:
        return {'verdict': 'too_large', 'reviewable': False, 'length': 0, 'sha256': None,
                'detail': f'Sequence input is limited to {MAX_SEQUENCE_BYTES} bytes.'}
    try:
        sequence = normalize_sequence(text)
    except ValueError as error:
        return {'verdict': 'unreadable', 'reviewable': False, 'length': 0, 'sha256': None,
                'detail': f'{error}. Expected one FASTA record over {"".join(sorted(AMINO_ACIDS))}.'}
    digest = _digest(sequence)
    common = {'length': len(sequence), 'sha256': digest}
    if digest == REFERENCE_SHA256:
        return {**common, 'verdict': 'registered_reference', 'reviewable': True,
                'detail': 'This is the registered full reference. Positions are full-reference '
                          '1-based, and the protected catalytic sites apply.'}
    if digest == MATURE_SHA256:
        return {**common, 'verdict': 'registered_mature_sequence', 'reviewable': False,
                'detail': 'This is the registered 181-residue deposited mature sequence, not the '
                          'full reference. Reviews use the full-reference frame, which is 31 '
                          'residues longer; supply the full sequence to avoid an offset error.'}
    return {**common, 'verdict': 'not_the_registered_target', 'reviewable': False,
            'detail': _NOT_REVIEWABLE}


def check_structure(cif_text, sequence_text, chain='A'):
    """Report whether a sequence joins to a structure's author numbering.

    Works for any mmCIF, not only the registered entry: the join is derived from the
    file rather than assumed from an offset.
    """
    base = {'chain': chain, 'deposited_residue_count': None, 'modelled_residue_count': None,
            'unmodelled_positions': [], 'auth_minus_label_offsets': [],
            'insertion_codes': [], 'identity_mismatches': []}
    if not isinstance(cif_text, str) or not isinstance(sequence_text, str):
        return {**base, 'verdict': 'unreadable', 'detail': 'Expected text for both inputs.'}
    if len(cif_text.encode('utf-8', 'ignore')) > MAX_STRUCTURE_BYTES:
        return {**base, 'verdict': 'too_large',
                'detail': f'Structure input is limited to {MAX_STRUCTURE_BYTES} bytes.'}
    try:
        sequence = normalize_sequence(sequence_text)
    except ValueError as error:
        return {**base, 'verdict': 'unreadable', 'detail': str(error)}
    try:
        loops = parse_mmcif_loops(cif_text)
    except Exception:  # noqa: BLE001 - any parse failure is a verdict, not a crash
        return {**base, 'verdict': 'not_mmcif',
                'detail': 'This does not parse as mmCIF. PDB-format files are not read here.'}
    if '_pdbx_poly_seq_scheme' not in loops:
        return {**base, 'verdict': 'not_mmcif',
                'detail': 'No _pdbx_poly_seq_scheme loop, so no polymer numbering can be joined.'}
    try:
        join = derive_coordinate_join(cif_text, sequence, chain=chain)
    except ValueError as error:
        message = str(error)
        if 'No _pdbx_poly_seq_scheme rows' in message:
            verdict = 'chain_not_found'
        elif 'length' in message:
            verdict = 'length_disagreement'
        else:
            verdict = 'identity_disagreement'
        return {**base, 'verdict': verdict, 'detail': message}
    return {'chain': chain, 'verdict': 'join_verified',
            'deposited_residue_count': join['deposited_residue_count'],
            'modelled_residue_count': join['modelled_residue_count'],
            'unmodelled_positions': join['unmodelled_deposited_positions'],
            'auth_minus_label_offsets': join['auth_minus_label_offsets'],
            'insertion_codes': join['insertion_codes'],
            'identity_mismatches': join['residue_identity_mismatches'],
            'detail': _join_detail(join)}


def _join_detail(join):
    offsets = join['auth_minus_label_offsets']
    parts = []
    if offsets == [0]:
        parts.append('Author numbering equals label numbering, so a residue index can be used '
                     'directly as a selector for this chain.')
    else:
        parts.append(f'Author numbering differs from label numbering by {offsets}. Selecting by '
                     'sequence index would address the wrong residue.')
    missing = join['unmodelled_deposited_positions']
    if missing:
        parts.append(f'{len(missing)} deposited residue(s) carry no atoms: {missing}. Those '
                     'positions cannot be shown or measured, and a neighbour is not a substitute.')
    else:
        parts.append('Every deposited residue carries atoms.')
    if join['insertion_codes']:
        parts.append(f"Insertion codes are present: {join['insertion_codes']}. A bare residue "
                     'number is ambiguous here.')
    return ' '.join(parts)
