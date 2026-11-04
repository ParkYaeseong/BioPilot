"""Read only the two recorded optional predictions; no model/backend imports."""
import hashlib
import json
from pathlib import Path

from app.core.targets import REFERENCE_SHA256, registered_profile, validate_target, validate_variant

ROOT=Path(__file__).resolve().parents[1]
PAIRS=(('esmfold2','WT'),('esm3','A32V'))
AMINO=dict(zip('ALA CYS ASP GLU PHE GLY HIS ILE LYS LEU MET ASN PRO GLN ARG SER THR VAL TRP TYR'.split(),
               'ACDEFGHIKLMNPQRSTVWY'))


def load_predictions(root=None):
    root=Path(root) if root is not None else ROOT
    evidence=root/'validation/optional_science_runtime_20261028.json'
    if not evidence.is_file():
        return []
    registry=json.loads(evidence.read_bytes())
    pins={(r['model'],r['variant']):r for r in registry['models']}
    target=validate_target(registered_profile(),'sequence_plausibility_review')
    results=[]
    for model,variant in PAIRS:
        folder=root/'examples/artifacts/structures'/f'{model}_{variant}'
        if not folder.is_dir():
            continue
        pin=pins[(model,variant)]
        raw=(folder/'receipt.json').read_bytes()
        pdb_raw=(folder/'prediction.pdb').read_bytes()
        if (hashlib.sha256(raw).hexdigest()!=pin['receipt_sha256'] or
                hashlib.sha256(pdb_raw).hexdigest()!=pin['structure_sha256']):
            raise ValueError('Prediction checksum mismatch: '+model)
        receipt=json.loads(raw)
        if (receipt['runtime_verification']!='official_sdk_execution' or receipt['status']!='completed'
                or receipt['request']['model_key']!=model or receipt['request']['variant']!=variant
                or receipt['request']['reference_sha256']!=REFERENCE_SHA256
                or receipt['request']['sequence_context']!='full_212'
                or receipt['source_mode']!='computed_prediction'
                or receipt['experimental_validation'] is not False
                or receipt['baseline_rank_changed'] is not False):
            raise ValueError('Prediction scope mismatch: '+model)
        expected=target.reference_sequence
        if variant!='WT':
            checked=validate_variant(target,variant)
            expected=expected[:checked.full_position-1]+checked.mutant+expected[checked.full_position:]
        pdb=pdb_raw.decode('utf-8')
        atoms=[line for line in pdb.splitlines() if line.startswith('ATOM  ') and line[12:16].strip()=='CA']
        try:
            sequence=''.join(AMINO[line[17:20]] for line in atoms)
            if (len(atoms)!=212 or any(line[21]!='A' for line in atoms)
                    or [int(line[22:26]) for line in atoms]!=list(range(1,213))
                    or sequence!=expected
                    or hashlib.sha256(sequence.encode()).hexdigest()!=receipt['candidate_sequence_sha256']):
                raise ValueError('Prediction sequence mismatch: '+model)
        except (KeyError,IndexError) as error:
            raise ValueError('Prediction sequence mismatch: '+model) from error
        results.append({'id':model+'_'+variant,'model':model,'variant':variant,'pdb':pdb,
                        'label':f'{"ESMFold2" if model=="esmfold2" else "ESM3"} · {variant} · full_212 predicted structure. '
                        'Actual GPU computation; stored result. Not an experimental structure or phenotype validation.',
                        'sequence_verified':True,'experimental_validation':False,
                        'elapsed_seconds':receipt['elapsed_seconds'],
                        'structure_sha256':receipt['structure_sha256']})
    return results
