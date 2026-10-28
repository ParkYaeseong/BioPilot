import shutil
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


def test_real_gpu_predictions_remain_separate_and_have_matching_local_hashes():
    from app.prediction_view import load_predictions
    rows=load_predictions()
    assert [(r['model'],r['variant']) for r in rows]==[('esmfold2','WT'),('esm3','A32V')]
    assert all(r['sequence_verified'] and not r['experimental_validation'] for r in rows)
    assert all('ATOM  ' in r['pdb'] for r in rows)


def test_changed_predicted_coordinates_are_not_silently_rendered(tmp_path):
    from app.prediction_view import load_predictions
    shutil.copytree(ROOT/'demo/artifacts/structures',tmp_path/'demo/artifacts/structures')
    (tmp_path/'validation').mkdir()
    shutil.copyfile(ROOT/'validation/optional_science_runtime_20261028.json',
                    tmp_path/'validation/optional_science_runtime_20261028.json')
    pdb=tmp_path/'demo/artifacts/structures/esmfold2_WT/prediction.pdb'
    pdb.write_text(pdb.read_text()+'REMARK modified\n')
    with pytest.raises(ValueError,match='checksum'):
        load_predictions(tmp_path)


def test_missing_optional_prediction_files_do_not_prevent_reference_view(tmp_path):
    from app.prediction_view import load_predictions
    assert load_predictions(tmp_path)==[]
