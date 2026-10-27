"""Offline scientific guards, not a predictor or a working BioPilot app.

No external services, model weights, or experimental efficacy checks are used.
Downstream code must explicitly integrate these guards; a prompt is not enforcement.
"""
from __future__ import annotations
import hashlib
import math
import re
from typing import Any, Iterable, Mapping

AMINO_ACIDS = frozenset('ACDEFGHIKLMNPQRSTVWY')

def _sequence(value: str) -> str:
    if not isinstance(value, str) or not value or not set(value) <= AMINO_ACIDS:
        raise ValueError('Expected a nonempty canonical uppercase amino-acid sequence')
    return value

def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    return float(value)

def exact_sequence_map(reference: str, mature: str) -> dict[int, int]:
    """Map mature to full 1-based positions only for a unique exact match.

    This proves a sequence correspondence, not a cleavage site or atom mapping.
    General proteins requiring gapped alignments must use a reviewed alignment.
    """
    _sequence(reference); _sequence(mature)
    starts = [i for i in range(len(reference)-len(mature)+1) if reference.startswith(mature, i)]
    if len(starts) != 1:
        raise ValueError('Sequence mapping is absent or ambiguous; no offset may be assumed')
    return {i+1: starts[0]+i+1 for i in range(len(mature))}

def verify_target(profile: Mapping[str, Any]) -> dict[str, Any]:
    full = _sequence(profile['reference_sequence'])
    mature = _sequence(profile['mature_sequence'])
    for seq, key, length_key in [(full,'reference_sha256','reference_length'),(mature,'mature_sha256','mature_length')]:
        if hashlib.sha256(seq.encode('ascii')).hexdigest()!=profile[key] or len(seq)!=profile[length_key]:
            raise ValueError('Target sequence hash or length mismatch')
    mapping = exact_sequence_map(full, mature)
    region = profile['mature_region_full_1based']
    if region != {'start': mapping[1], 'end':mapping[len(mature)]}:
        raise ValueError('Registered mature region disagrees with the actual sequences')
    protected=[]
    for site in profile['protected_sites']:
        mp,fp,aa=site['mature_position'],site['full_position'],site['residue']
        if mp not in mapping or mapping[mp]!=fp or full[fp-1]!=aa or mature[mp-1]!=aa:
            raise ValueError('Protected site has incompatible numbering or residue identity')
        if fp in protected:raise ValueError('Duplicate protected site')
        protected.append(fp)
    # Even verified sequence correspondence does not establish an atom-level join.
    return {'protected_full_positions':sorted(protected),'mature_to_full':mapping,'coordinate_mapping_verified':False}

def validate_variant(profile: Mapping[str, Any], variant: str) -> dict[str, Any]:
    """Apply the protected interactive policy, not an unrestricted benchmark policy."""
    checked=verify_target(profile)
    match=re.fullmatch(r'([ACDEFGHIKLMNPQRSTVWY])([1-9][0-9]*)([ACDEFGHIKLMNPQRSTVWY])',variant)
    if match is None:raise ValueError('Expected one substitution in full-reference 1-based coordinates')
    wt,pos,alt=match.group(1),int(match.group(2)),match.group(3)
    full=profile['reference_sequence'];region=profile['mature_region_full_1based']
    if not region['start']<=pos<=region['end']:raise ValueError('Position outside registered mature region')
    if full[pos-1]!=wt:raise ValueError('WT residue mismatch; numbering is not auto-corrected')
    if wt==alt:raise ValueError('Synonymous substitution is not a candidate')
    if pos in checked['protected_full_positions']:raise ValueError('Protected catalytic site')
    reverse={f:m for m,f in checked['mature_to_full'].items()}
    return {'full_position':pos,'mature_position':reverse[pos],'wild_type':wt,'mutant':alt}

def objective_capability(profile_id: str) -> dict[str, Any]:
    profiles={
        'sequence_plausibility_review':{'claim_level':'sequence_model_preference','phenotype_calibrated':False},
        'lipase_T50_hypothesis_review':{'claim_level':'hypothesis','phenotype_calibrated':False},
    }
    if profile_id not in profiles:raise ValueError('Unsupported scientific objective: no registered predictor')
    return dict(profiles[profile_id])

def binary_label_meaning(label: int, method: str) -> str:
    if type(label) is not int or label not in (0,1) or method!='median':
        raise ValueError('Only the documented median-bin interpretation is supported')
    return ('upper' if label else 'lower')+'_median_group_not_WT_improvement'

def classify_t50(value: float|None, wt: float|None, margin: float|None,
                 conditions_match: bool, rule_verified: bool) -> str:
    """Evaluator-only interpretation. Never convert an ESM score with this helper.

    The margin must come from a pre-registered, justified uncertainty rule.
    A returned class is not a statistical significance claim or validation of function.
    """
    for number,name in [(value,'T50'),(wt,'WT_T50'),(margin,'uncertainty_margin')]:
        if number is not None:_finite(number,name)
    if margin is not None and margin<0:raise ValueError('Uncertainty margin cannot be negative')
    if any(x is None for x in (value,wt,margin)) or not conditions_match or not rule_verified:return 'unknown'
    return 'above_WT_under_registered_rule' if value-wt>margin else 'not_above_WT_under_registered_rule'

def rank_baseline(records: Iterable[Mapping[str, Any]], *, checkpoint: str, score_kind: str,
                  reference_sha256: str, sequence_context: str) -> list[dict[str, Any]]:
    """A common-score ranking. Optional annotations cannot change its ordering."""
    rows=[];seen=set()
    expected={'checkpoint':checkpoint,'score_kind':score_kind,'reference_sha256':reference_sha256,'sequence_context':sequence_context}
    for record in records:
        r=dict(record);cid=r.get('candidate_id')
        if not isinstance(cid,str) or not cid or cid in seen:raise ValueError('Missing or duplicate candidate ID')
        if any(r.get(k)!=v for k,v in expected.items()):raise ValueError('Incompatible scoring provenance')
        _finite(r.get('score'),'score');seen.add(cid);rows.append(r)
    return sorted(rows,key=lambda r:(-r['score'],r['candidate_id']))

def require_coordinate_row(row: Mapping[str, Any]) -> None:
    """Fail closed for missing atom correspondence; no sequence-index substitution."""
    if row.get('coordinate_observed') is not True:
        raise ValueError('Atom coordinates are not verified for this residue')
    if row.get('pdb_auth_seq_id') in (None,'','?','.') or row.get('pdb_label_seq_id') is None:
        raise ValueError('PDB author/label numbering join is incomplete')

def validate_prediction_cohort(prediction_ids: Iterable[str], expected_ids: Iterable[str]) -> None:
    predicted=list(prediction_ids);expected=list(expected_ids)
    if len(set(predicted))!=len(predicted) or len(set(expected))!=len(expected):
        raise ValueError('Duplicate IDs in prediction or expected cohort')
    if set(predicted)!=set(expected):
        raise ValueError('Missing or unexpected predictions: disclose failures, do not shrink the cohort')
