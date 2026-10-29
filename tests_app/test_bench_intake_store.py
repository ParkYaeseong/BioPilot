from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import pytest

ROOT=Path(__file__).resolve().parents[1]


def full_fasta():
    from app.core.targets import registered_profile
    return ('>public_Lipase_A\n'+registered_profile()['reference_sequence']+'\n').encode()


def test_uploaded_reference_binds_the_same_executable_target_as_example():
    from app.bench_intake import freeze_input
    example=freeze_input('Review A32V', input_kind='example')
    uploaded=freeze_input('Review A32V', input_kind='upload', fasta=full_fasta(), filename='reference.fasta')
    assert uploaded['reference_sha256']==example['reference_sha256']
    assert uploaded['positions']==[32]
    assert uploaded['input_kind']=='upload' and uploaded['fasta_sha256']
    assert uploaded['filename']=='reference.fasta'


def test_unsupported_input_or_structure_never_falls_back():
    from app.bench_intake import freeze_input
    for kwargs in ({'input_kind':'upload'}, {'input_kind':'upload','fasta':b'>other\nAAAA'},
                   {'input_kind':'example','cif':b'data_unknown'}):
        with pytest.raises(ValueError):
            freeze_input('Review A32V',**kwargs)
    with pytest.raises(ValueError,match='Protected'):
        freeze_input('Review S108A',input_kind='example')


def test_durable_atomic_claim_and_cap_survive_a_second_store(tmp_path):
    from app.bench_intake import freeze_input
    from app.bench_store import ReviewStore
    store=ReviewStore(tmp_path,max_runs=1)
    review=store.create(freeze_input('Review A32V',input_kind='example'))
    def claim(_):
        try:
            ReviewStore(tmp_path,max_runs=1).claim(review['id'], approved=True)
            return True
        except ValueError:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(claim,range(2)))==[False,True]
    assert ReviewStore(tmp_path,max_runs=1).get(review['id'])['status']=='running'
    other=store.create(freeze_input('Review position 45',input_kind='example'))
    with pytest.raises(ValueError,match='cap'):
        store.claim(other['id'],approved=True)
    assert store.remaining_runs==0


def test_no_claim_without_approval_and_no_arbitrary_record_path(tmp_path):
    from app.bench_intake import freeze_input
    from app.bench_store import ReviewStore
    store=ReviewStore(tmp_path)
    row=store.create(freeze_input('Review A32V',input_kind='example'))
    with pytest.raises(ValueError): store.claim(row['id'],approved=False)
    assert store.get(row['id'])['status']=='validated'
    with pytest.raises(ValueError): store.get('../../elsewhere')


def test_source_hash_mature_sequence_and_report_integrity_are_not_silent_fallbacks(tmp_path):
    from app.core.targets import registered_profile
    from app.bench_intake import freeze_input
    from app.bench_store import ReviewStore
    mature=('>mature\n'+registered_profile()['mature_sequence']).encode()
    with pytest.raises(ValueError,match='full reference|full-reference|full sequence'):
        freeze_input('Review A32V',input_kind='upload',fasta=mature)
    request=freeze_input('Review A32V',input_kind='upload',fasta=full_fasta())
    store=ReviewStore(tmp_path)
    row=store.create(request)
    store.claim(row['id'],approved=True)
    raw=b'{"status":"partial","stop_reason":"fixture"}'
    store.finish(row['id'],status='partial',report=raw)
    path=store.report_path(row['id'])
    path.write_bytes(raw+b' ')
    with pytest.raises(ValueError,match='checksum'):
        store.report_path(row['id'])


def test_uploaded_mmcif_is_accepted_only_as_the_pinned_public_reference():
    from app.bench_intake import freeze_input
    result=freeze_input('Review A32V',input_kind='upload',fasta=full_fasta(),cif=(ROOT/'reference/1ISP.cif').read_bytes())
    assert result['structure_sha256']


@pytest.mark.parametrize('request_cap',[1,2])
def test_insufficient_scientific_request_cap_is_refused_before_claim(tmp_path,monkeypatch,request_cap):
    from app.bench_intake import freeze_input
    from app.bench_store import ReviewStore
    from app.bench_execution import execute_review
    store=ReviewStore(tmp_path)
    row=store.create(freeze_input('Review A32V',input_kind='example'))
    with pytest.raises(ValueError,match='3|three'):
        execute_review(store,row['id'],root=ROOT,esm_env=tmp_path/'unused.env',approved=True,max_requests=request_cap)
    assert store.get(row['id'])['status']=='validated'
    assert store.remaining_runs==3
