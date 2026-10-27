import pytest
from app.core.artifacts import ArtifactStore
from app.core.runs import RunService

def test_owned_artifact_identity_and_corruption(tmp_path):
    runs=RunService(tmp_path/'runs.sqlite');rid=runs.create({},'local')
    store=ArtifactStore(tmp_path/'artifacts',runs)
    content={'score':None,'source_mode':'synthetic_fixture'}
    path=store.save(rid,'local',content)
    assert store.load(rid,'local',path.stem)==content
    with pytest.raises(PermissionError): store.load(rid,'other',path.stem)
    with pytest.raises(ValueError): store.load(rid,'local','../../.env')
    path.write_text('{"run_id":"wrong","content":{}}')
    with pytest.raises(ValueError): store.load(rid,'local',path.stem)

def test_malformed_artifact_is_reported_as_invalid(tmp_path):
    runs=RunService(tmp_path/'runs.sqlite');rid=runs.create({},'local')
    store=ArtifactStore(tmp_path/'artifacts',runs)
    path=store.save(rid,'local',{'source_mode':'synthetic_fixture'})
    path.write_text('{}')
    with pytest.raises(ValueError): store.load(rid,'local',path.stem)
