"""Derive the deposited-sequence to atom-coordinate join from a real mmCIF.

docs/11 fixes the procedure: join `_pdbx_poly_seq_scheme` with `_atom_site` on
entity/chain/label_seq_id, keep auth_seq_id, insertion code, model number and
alternate conformers as distinct fields, verify residue identities rather than
counts, and identify missing residues explicitly. Nothing here assumes an offset,
and the scientific source sequence is never mutated to force a match.

Pure stdlib and pure computation: no network, no file I/O, no credentials. The
caller supplies the mmCIF text, so an approval boundary stays outside this module.
"""

_ABSENT = ('?', '.', '', None)

_THREE_TO_ONE = {
    'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D', 'CYS': 'C', 'GLN': 'Q',
    'GLU': 'E', 'GLY': 'G', 'HIS': 'H', 'ILE': 'I', 'LEU': 'L', 'LYS': 'K',
    'MET': 'M', 'PHE': 'F', 'PRO': 'P', 'SER': 'S', 'THR': 'T', 'TRP': 'W',
    'TYR': 'Y', 'VAL': 'V',
}


def _tokenize(line):
    """Split one mmCIF data line, honouring ' and " quoting."""
    tokens, index, end = [], 0, len(line)
    while index < end:
        char = line[index]
        if char in ' \t':
            index += 1
            continue
        if char in "'\"":
            quote = char
            index += 1
            start = index
            while index < end:
                if line[index] == quote and (index + 1 >= end or line[index + 1] in ' \t'):
                    break
                index += 1
            tokens.append(line[start:index])
            index += 1
        else:
            start = index
            while index < end and line[index] not in ' \t':
                index += 1
            tokens.append(line[start:index])
    return tokens


def parse_mmcif_loops(text):
    """Return {category: [row dicts]} for every loop_ block, folding ;multi-line; values."""
    folded, raw, index = [], text.splitlines(), 0
    while index < len(raw):
        line = raw[index]
        if line.startswith(';'):
            chunk = [line[1:]]
            index += 1
            while index < len(raw) and not raw[index].startswith(';'):
                chunk.append(raw[index])
                index += 1
            index += 1
            folded.append(('VALUE', '\n'.join(chunk)))
        else:
            folded.append(('LINE', line))
            index += 1

    loops, index = {}, 0
    while index < len(folded):
        kind, line = folded[index]
        if kind != 'LINE' or line.strip() != 'loop_':
            index += 1
            continue
        index += 1
        names = []
        while (index < len(folded) and folded[index][0] == 'LINE'
               and folded[index][1].lstrip().startswith('_')):
            names.append(folded[index][1].strip())
            index += 1
        if not names:
            continue
        category = names[0].split('.')[0]
        keys = [name.split('.', 1)[1] for name in names]
        rows, buffer = [], []
        while index < len(folded):
            kind, line = folded[index]
            if kind == 'VALUE':
                buffer.append(line)
                index += 1
            else:
                stripped = line.strip()
                if stripped == '#' or stripped == 'loop_' or stripped.startswith('_'):
                    break
                if stripped:
                    buffer.extend(_tokenize(stripped))
                index += 1
            while len(buffer) >= len(keys):
                rows.append(dict(zip(keys, buffer[:len(keys)])))
                buffer = buffer[len(keys):]
        loops[category] = rows
    return loops


def _clean(value):
    return None if value in _ABSENT else value


def derive_coordinate_join(cif_text, deposited_sequence, *, chain='A'):
    """Join the deposited polymer sequence to observed atoms for one author chain.

    Raises ValueError when the structure disagrees with the supplied sequence, so a
    mismatch can never be absorbed into a silently shifted mapping.
    """
    loops = parse_mmcif_loops(cif_text)
    scheme = [row for row in loops.get('_pdbx_poly_seq_scheme', [])
              if row.get('pdb_strand_id') == chain]
    if not scheme:
        raise ValueError(f'No _pdbx_poly_seq_scheme rows for chain {chain}')
    if len(scheme) != len(deposited_sequence):
        raise ValueError(
            f'Deposited sequence length {len(deposited_sequence)} does not match '
            f'{len(scheme)} polymer rows for chain {chain}')

    atoms = [row for row in loops.get('_atom_site', [])
             if row.get('group_PDB') == 'ATOM' and row.get('label_asym_id')]
    observed = {}
    for atom in atoms:
        try:
            key = (atom['label_asym_id'], int(atom['label_seq_id']))
        except (KeyError, TypeError, ValueError):
            continue
        entry = observed.setdefault(key, {'atoms': 0, 'models': set(), 'alts': set()})
        entry['atoms'] += 1
        model = _clean(atom.get('pdbx_PDB_model_num'))
        if model is not None:
            entry['models'].add(model)
        alt = _clean(atom.get('label_alt_id'))
        if alt is not None:
            entry['alts'].add(alt)

    rows, mismatches, offsets, insertions = [], [], set(), set()
    for position, row in enumerate(scheme, start=1):
        label_seq_id = int(row['seq_id'])
        mon_id = row.get('mon_id') or ''
        one_letter = _THREE_TO_ONE.get(mon_id, 'X')
        expected = deposited_sequence[position - 1]
        if one_letter != expected:
            mismatches.append({'deposited_position': position,
                               'sequence_residue': expected,
                               'structure_residue': one_letter,
                               'mon_id': mon_id})
        auth_seq_id = _clean(row.get('pdb_seq_num'))
        insertion = _clean(row.get('pdb_ins_code'))
        if insertion is not None:
            insertions.add(insertion)
        if auth_seq_id is not None:
            try:
                offsets.add(int(auth_seq_id) - label_seq_id)
            except ValueError:
                pass
        found = observed.get((row.get('asym_id'), label_seq_id), {})
        rows.append({
            'deposited_position': position,
            'residue': one_letter,
            'mon_id': mon_id,
            'pdb_label_seq_id': label_seq_id,
            'pdb_auth_seq_id': auth_seq_id,
            'pdb_insertion_code': insertion,
            'coordinate_observed': bool(found.get('atoms')),
            'modelled_atom_count': found.get('atoms', 0),
            'model_numbers': sorted(found.get('models', ())),
            'alt_conformer_ids': sorted(found.get('alts', ())),
        })

    if mismatches:
        raise ValueError(
            f'Residue identity disagreement at {len(mismatches)} position(s); the source '
            f'sequence is never altered to force a match. First: {mismatches[0]}')

    declared_unobserved = sorted(
        {_clean(row.get('auth_seq_id')) for row in
         loops.get('_pdbx_unobs_or_zero_occ_residues', [])
         if row.get('auth_asym_id') == chain} - {None})
    return {
        'chain': chain,
        'rows': rows,
        'unmodelled_deposited_positions': [row['deposited_position'] for row in rows
                                           if not row['coordinate_observed']],
        'declared_unobserved_auth_seq_ids': declared_unobserved,
        'residue_identity_mismatches': mismatches,
        'auth_minus_label_offsets': sorted(offsets),
        'insertion_codes': sorted(insertions),
        'modelled_residue_count': sum(1 for row in rows if row['coordinate_observed']),
        'deposited_residue_count': len(rows),
    }
