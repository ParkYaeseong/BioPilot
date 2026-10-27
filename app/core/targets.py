"""Product registry gate, preserving the supplied v2 exact-map/WT algorithms.

Only sequence correspondence is verified. No evaluator imports or geometry guesses.
Reuse provenance: checks/science_contracts.py, supplied v2/v3 preparation package.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from app.core.capabilities import objective_capability

AMINO_ACIDS = frozenset('ACDEFGHIKLMNPQRSTVWY')
REFERENCE_ID = 'ESTA_BACSU_Nutschel_2020'
REFERENCE_SHA256 = '8a9ea05c5d2953b5b143b591bea6014aec631be96a4842b274fb3e91ee4907d7'
MATURE_SHA256 = '90914bba8255e2e85de3277fe0d5ffdfdeb8e5b741ff593dde001f73c413a065'
FRAME = 'full_reference_1based'
PROTECTED = ((77, 108, 'S'), (133, 164, 'D'), (156, 187, 'H'))

@dataclass(frozen=True)
class ValidatedTarget:
    reference_id: str
    reference_sequence: str
    reference_sha256: str
    objective_id: str
    claim_level: str
    protected_positions: tuple[int, ...] = (108, 164, 187)
    reference_numbering: str = FRAME
    sequence_context: str = 'full_212'
    phenotype_calibrated: bool = False
    coordinate_mapping_verified: bool = False

    def summary(self):
        return {key: getattr(self, key) for key in (
            'reference_id', 'reference_sha256', 'objective_id', 'claim_level',
            'protected_positions', 'reference_numbering', 'sequence_context',
            'phenotype_calibrated', 'coordinate_mapping_verified')}

@dataclass(frozen=True)
class Variant:
    candidate_id: str
    full_position: int
    mature_position: int
    wild_type: str
    mutant: str
    pdb_auth_seq_id: str | None = None
    pdb_label_seq_id: int | None = None
    coordinate_observed: bool | None = None

def registered_profile() -> dict[str, Any]:
    """Read only the provisioned public registry, never a caller-selected file."""
    path = Path(__file__).resolve().parents[2] / 'reference' / 'target_profile.json'
    return json.loads(path.read_text(encoding='utf-8'))

def normalize_sequence(text: str) -> str:
    if not isinstance(text, str):
        raise ValueError('Sequence must be text')
    lines = text.strip().splitlines()
    if lines and lines[0].startswith('>'):
        lines = lines[1:]
    sequence = ''.join(''.join(lines).split()).upper()
    if not sequence or len(sequence) > 512 or not set(sequence) <= AMINO_ACIDS:
        raise ValueError('Expected one canonical sequence of 1..512 residues; no crop or ambiguous residues')
    return sequence

def _frame(reference_numbering):
    if reference_numbering != FRAME:
        raise ValueError('Explicit full_reference_1based frame required; numbering is never auto-corrected')

def validate_target(profile: Mapping[str, Any], objective_id: str, *, reference_numbering=FRAME) -> ValidatedTarget:
    _frame(reference_numbering)
    capability = objective_capability(objective_id)
    try:
        full, mature = profile['reference_sequence'], profile['mature_sequence']
        if (profile['profile_id'] != 'lipase_bs_a_v2' or profile['reference_id'] != REFERENCE_ID
                or profile['reference_indexing'] != FRAME
                or profile['baseline']['inference_context'] != 'full_212_reference'
                or profile['baseline']['score_type'] != 'masked_marginal_log_likelihood_ratio'
                or profile['baseline']['phenotype_calibrated'] is not False):
            raise ValueError('Profile differs from registered target policy')
        for sequence, expected, length, hash_key, length_key in (
                (full, REFERENCE_SHA256, 212, 'reference_sha256', 'reference_length'),
                (mature, MATURE_SHA256, 181, 'mature_sha256', 'mature_length')):
            if (not isinstance(sequence, str) or not set(sequence) <= AMINO_ACIDS
                    or len(sequence) != length or profile[length_key] != length
                    or profile[hash_key] != expected
                    or hashlib.sha256(sequence.encode('ascii')).hexdigest() != expected):
                raise ValueError('Sequence does not match registered reference hash and length')
        starts = [i for i in range(len(full)-len(mature)+1) if full.startswith(mature, i)]
        if starts != [31] or profile['mature_region_full_1based'] != {'start': 32, 'end': 212}:
            raise ValueError('Registered exact sequence correspondence mismatch')
        sites = tuple(sorted((s['mature_position'], s['full_position'], s['residue'])
                             for s in profile['protected_sites']))
        if sites != PROTECTED or any(full[fp-1] != aa or mature[mp-1] != aa for mp, fp, aa in sites):
            raise ValueError('Registered catalytic protection cannot be removed or changed')
        structure = profile['structure']
        if (structure['coordinate_file_sha256'] is not None
                or structure['author_numbering_verified'] is not False
                or structure['coordinate_status'] != 'not_downloaded_or_verified'):
            raise ValueError('Unverified coordinates cannot be enabled by a profile')
    except (KeyError, TypeError, UnicodeError) as error:
        raise ValueError('Invalid registered target profile') from error
    return ValidatedTarget(REFERENCE_ID, full, REFERENCE_SHA256, objective_id, capability['claim_level'])

def validate_variant(profile, variant: str, *, reference_numbering=FRAME) -> Variant:
    _frame(reference_numbering)
    if isinstance(profile, ValidatedTarget):
        target = validate_target(registered_profile(), profile.objective_id)
        if profile != target:
            raise ValueError('Target differs from registered context')
    else:
        target = validate_target(profile, 'sequence_plausibility_review')
    match = re.fullmatch(r'([ACDEFGHIKLMNPQRSTVWY])([1-9][0-9]*)([ACDEFGHIKLMNPQRSTVWY])', variant) if isinstance(variant, str) else None
    if match is None:
        raise ValueError('Expected one substitution in full-reference coordinates')
    wt, pos, alt = match.group(1), int(match.group(2)), match.group(3)
    if not 32 <= pos <= 212:
        raise ValueError('Position outside registered mature region')
    if target.reference_sequence[pos-1] != wt:
        raise ValueError('WT residue mismatch; numbering is not auto-corrected')
    if wt == alt:
        raise ValueError('Synonymous substitution is not a candidate')
    if pos in target.protected_positions:
        raise ValueError('Protected catalytic site')
    return Variant(variant, pos, pos-31, wt, alt)

def require_coordinates(target, positions):
    raise ValueError('Atom coordinates and author/label correspondence are not verified')
